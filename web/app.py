import json
import logging
import sys
import os
from datetime import datetime
from flask import Flask, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

HOTSPOT_DATA = []
ANALYSIS_DATA = []
CLUSTER_DATA = []

def get_current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def load_config():
    try:
        config = {
            'ALIYUN_LLM_CONFIG': {
                'api_key': 'sk-your-key',
                'base_url': 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
                'models': {
                    'qwen_flash': 'qwen-flash',
                    'qwen_plus': 'qwen-plus-2025-07-28'
                },
                'timeout': 120,
                'max_tokens': 2048,
                'temperature': 0.7
            }
        }
        return config
    except Exception as e:
        logger.warning(f"加载配置失败: {e}")
        return {}

def call_aliyun_llm(prompt, model="qwen-plus-2025-07-28", max_retries=3):
    config = load_config()
    api_key = config.get("ALIYUN_LLM_CONFIG", {}).get("api_key", "")
    
    if not api_key:
        logger.warning("未找到阿里云API密钥")
        return None
    
    try:
        import requests
        import time
        
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "input": {
                "messages": [{"role": "user", "content": prompt}]
            },
            "parameters": {"result_format": "message"}
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=120)
                
                if response.status_code != 200:
                    logger.error(f"LLM调用HTTP错误: {response.status_code}")
                    time.sleep(2 ** attempt)
                    continue
                    
                result = response.json()
                
                if result.get("error"):
                    logger.error(f"LLM API错误: {result['error'].get('message', '未知错误')}")
                    time.sleep(2 ** attempt)
                    continue
                
                if result.get("output", {}).get("text"):
                    return result["output"]["text"]
                elif result.get("output", {}).get("choices", []) and len(result["output"]["choices"]) > 0:
                    return result["output"]["choices"][0]["message"]["content"]
                else:
                    logger.error("LLM返回数据格式异常")
                    time.sleep(2 ** attempt)
                    continue
                    
            except requests.exceptions.ReadTimeout:
                logger.error(f"LLM调用超时，第 {attempt + 1}/{max_retries} 次尝试")
                time.sleep(2 ** attempt)
            except requests.exceptions.ConnectionError:
                logger.error(f"LLM连接失败，第 {attempt + 1}/{max_retries} 次尝试")
                time.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"LLM调用异常: {str(e)}")
                time.sleep(2 ** attempt)
        
        logger.error(f"LLM调用失败，已重试 {max_retries} 次")
        return None
        
    except ImportError:
        logger.error("未安装requests库")
        return None
    except Exception as e:
        logger.error(f"LLM调用初始化失败: {e}")
        return None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI音乐自动化 - 可视化面板</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 25px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }
        h1 { font-size: 32px; color: #2c3e50; margin-bottom: 8px; }
        .subtitle { color: #7f8c8d; font-size: 16px; }
        .section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 25px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
        }
        .section-title { font-size: 24px; color: #2c3e50; font-weight: 600; }
        .btn {
            padding: 14px 32px;
            border: none;
            border-radius: 30px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4); }
        .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
        .result-area { margin-top: 20px; max-height: 500px; overflow-y: auto; padding: 10px; }
        .hotspot-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }
        .hotspot-title { font-size: 18px; font-weight: 600; color: #2c3e50; margin-bottom: 10px; }
        .hotspot-meta { display: flex; gap: 15px; color: #7f8c8d; font-size: 14px; flex-wrap: wrap; }
        .hotspot-tag { background: #e0e7ff; color: #4338ca; padding: 4px 12px; border-radius: 15px; font-size: 13px; }
        .analysis-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #8bc34a;
        }
        .analysis-title { font-size: 16px; font-weight: 600; color: #2c3e50; margin-bottom: 15px; }
        .analysis-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
        .analysis-item { background: white; padding: 12px; border-radius: 8px; }
        .analysis-label { font-size: 12px; color: #7f8c8d; margin-bottom: 4px; }
        .analysis-value { font-size: 14px; color: #2c3e50; font-weight: 500; }
        .cluster-card {
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #ff9800;
        }
        .cluster-title { font-size: 20px; font-weight: 600; color: #e65100; margin-bottom: 15px; }
        .cluster-desc { font-size: 14px; color: #5d4037; margin-bottom: 10px; }
        .cluster-tags { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 15px; }
        .cluster-tag { background: #ffcc80; color: #e65100; padding: 4px 12px; border-radius: 15px; font-size: 13px; }
        .prompt-area {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 25px;
            font-family: 'Courier New', monospace;
            line-height: 1.8;
            font-size: 14px;
            color: #2c3e50;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .btn-copy {
            padding: 10px 24px;
            background: #4caf50;
            color: white;
            border: none;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 15px;
            transition: all 0.3s;
        }
        .btn-copy:hover { background: #43a047; }
        .platform-section { margin-bottom: 30px; }
        .platform-header {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 18px 25px;
            border-radius: 12px;
            margin-bottom: 20px;
            color: white;
        }
        .platform-header h3 { font-size: 20px; font-weight: 600; margin: 0; }
        .platform-header span { font-size: 24px; }
        .btn-platform {
            margin-left: auto;
            padding: 10px 24px;
            background: rgba(255,255,255,0.2);
            color: white;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-platform:hover { background: rgba(255,255,255,0.3); }
        .loading { 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            padding: 60px; 
            color: #667eea; 
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
            border-radius: 12px;
            min-height: 200px;
        }
        .spinner {
            width: 45px; 
            height: 45px; 
            border: 4px solid rgba(102, 126, 234, 0.2); 
            border-top: 4px solid #667eea;
            border-radius: 50%; 
            animation: spin 1s linear infinite; 
            margin-right: 20px;
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
        }
        @keyframes spin { 
            0% { transform: rotate(0deg); } 
            100% { transform: rotate(360deg); } 
        }
        .loading-text {
            font-size: 18px;
            font-weight: 500;
        }
        .loading-dots {
            animation: dots 1.5s infinite;
        }
        @keyframes dots {
            0%, 60%, 100% { opacity: 0.3; }
            30% { opacity: 1; }
        }
        .empty-state { text-align: center; padding: 60px; color: #7f8c8d; }
        .empty-icon { font-size: 48px; margin-bottom: 15px; }
        .empty-text { font-size: 16px; }
        .stats-bar {
            display: flex; justify-content: space-between; margin-bottom: 20px; padding: 15px;
            background: #f8f9fa; border-radius: 10px;
        }
        .stat-item { text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; color: #667eea; }
        .stat-label { font-size: 12px; color: #7f8c8d; }
        .prompt-card {
            background: #f3e5f5;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #9c27b0;
        }
        .prompt-number {
            display: inline-block; width: 30px; height: 30px;
            background: linear-gradient(135deg, #9c27b0, #7b1fa2);
            color: white; border-radius: 50%; text-align: center;
            line-height: 30px; font-weight: bold; margin-right: 10px;
        }
        .prompt-title { font-size: 18px; font-weight: 600; color: #4a148c; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎵 AI音乐自动化 - 可视化面板</h1>
            <p class="subtitle">热点爬取 → AI分析 → 智能聚类 → 提示词生成</p>
        </header>

        <div class="stats-bar">
            <div class="stat-item"><div class="stat-value" id="statHotspots">0</div><div class="stat-label">热点数量</div></div>
            <div class="stat-item"><div class="stat-value" id="statAnalysis">0</div><div class="stat-label">分析完成</div></div>
            <div class="stat-item"><div class="stat-value" id="statClusters">0</div><div class="stat-label">派系数量</div></div>
            <div class="stat-item"><div class="stat-value" id="statPrompts">0</div><div class="stat-label">提示词数量</div></div>
        </div>

        <div class="section">
            <div class="section-header">
                <span class="section-title">📡 第一块：热点爬取区</span>
                <button class="btn btn-primary" id="crawlBtn" onclick="crawlHotspots()">立刻爬取热点</button>
            </div>
            <div class="result-area" id="hotspotResult">
                <div class="empty-state">
                    <div class="empty-icon">🔥</div>
                    <div class="empty-text">点击按钮开始爬取热点数据</div>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-header">
                <span class="section-title">📊 第二块：热点分析区</span>
                <button class="btn btn-primary" id="analyzeBtn" onclick="analyzeHotspots()">一键批量8维度分析</button>
            </div>
            <div class="result-area" id="analysisResult">
                <div class="empty-state">
                    <div class="empty-icon">🧠</div>
                    <div class="empty-text">请先爬取热点，再进行AI分析</div>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-header">
                <span class="section-title">🤖 第三块：AI智能聚类</span>
                <button class="btn btn-primary" id="clusterBtn" onclick="clusterHotspots()">AI自动聚类分析</button>
            </div>
            <div class="result-area" id="clusterResult">
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <div class="empty-text">请先完成热点分析，再进行AI聚类</div>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-header">
                <span class="section-title">🎼 第四块：提示词生成区</span>
                <button class="btn btn-primary" id="promptBtn" onclick="generatePrompts()">一键聚类生成3条提示词</button>
            </div>
            <div class="result-area" id="promptResult">
                <div class="empty-state">
                    <div class="empty-icon">📝</div>
                    <div class="empty-text">请先完成AI聚类，再生成音乐提示词</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function escapeHtml(text) {
            const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
            return text.replace(/[&<>"']/g, m => map[m]);
        }

        async function crawlHotspots() {
            const btn = document.getElementById('crawlBtn');
            const result = document.getElementById('hotspotResult');
            btn.disabled = true; btn.textContent = '爬取中...';
            result.innerHTML = '<div class="loading"><div class="spinner"></div><div class="loading-text">正在爬取热点数据<span class="loading-dots">...</span></div></div>';
            
            try {
                const response = await fetch('/api/crawl', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    let html = '';
                    data.data.forEach((item, idx) => {
                        html += '<div class="hotspot-card">';
                        html += '<div class="hotspot-title">' + item.title + '</div>';
                        html += '<div class="hotspot-meta">';
                        html += '<span class="hotspot-tag">' + item.platform + '</span>';
                        html += '<span>热度: ' + item.hot_value + '</span>';
                        html += '<span>时间: ' + item.time + '</span>';
                        html += '</div></div>';
                    });
                    result.innerHTML = html;
                    document.getElementById('statHotspots').textContent = data.data.length;
                } else { result.innerHTML = '<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-text">爬取失败: ' + data.message + '</div></div>'; }
            } catch (e) { result.innerHTML = '<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-text">请求失败: ' + e.message + '</div></div>'; }
            btn.disabled = false; btn.textContent = '立刻爬取热点';
        }

        async function analyzeHotspots() {
            const btn = document.getElementById('analyzeBtn');
            const result = document.getElementById('analysisResult');
            btn.disabled = true; btn.textContent = '分析中...';
            result.innerHTML = '<div class="loading"><div class="spinner"></div><div class="loading-text">正在调用AI进行批量8维度分析<span class="loading-dots">...</span></div></div>';
            
            try {
                const response = await fetch('/api/analyze', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    let html = '';
                    data.data.forEach((item, idx) => {
                        html += '<div class="analysis-card">';
                        html += '<div class="analysis-title">📌 ' + item.title + '</div>';
                        html += '<div class="analysis-grid">';
                        html += '<div class="analysis-item"><div class="analysis-label">主题</div><div class="analysis-value">' + item.theme + '</div></div>';
                        html += '<div class="analysis-item"><div class="analysis-label">情绪</div><div class="analysis-value">' + item.emotion + '</div></div>';
                        html += '<div class="analysis-item"><div class="analysis-label">风格</div><div class="analysis-value">' + item.style + '</div></div>';
                        html += '<div class="analysis-item"><div class="analysis-label">受众</div><div class="analysis-value">' + item.audience + '</div></div>';
                        html += '<div class="analysis-item"><div class="analysis-label">场景</div><div class="analysis-value">' + item.scene + '</div></div>';
                        html += '<div class="analysis-item"><div class="analysis-label">关键词</div><div class="analysis-value">' + item.keywords + '</div></div>';
                        html += '<div class="analysis-item"><div class="analysis-label">热度</div><div class="analysis-value">' + item.popularity + '</div></div>';
                        html += '<div class="analysis-item"><div class="analysis-label">趋势</div><div class="analysis-value">' + item.trend + '</div></div>';
                        html += '</div></div>';
                    });
                    result.innerHTML = html;
                    document.getElementById('statAnalysis').textContent = data.data.length;
                } else { result.innerHTML = '<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-text">分析失败: ' + data.message + '</div></div>'; }
            } catch (e) { result.innerHTML = '<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-text">请求失败: ' + e.message + '</div></div>'; }
            btn.disabled = false; btn.textContent = '一键批量8维度分析';
        }

        async function clusterHotspots() {
            const btn = document.getElementById('clusterBtn');
            const result = document.getElementById('clusterResult');
            btn.disabled = true; btn.textContent = '聚类中...';
            result.innerHTML = '<div class="loading"><div class="spinner"></div><div class="loading-text">AI正在智能聚类分析<span class="loading-dots">...</span></div></div>';
            
            try {
                const response = await fetch('/api/cluster', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    let html = '';
                    data.data.forEach((cluster, idx) => {
                        html += '<div class="cluster-card">';
                        html += '<div class="cluster-title">🏷️ 派系' + (idx + 1) + ': ' + cluster.name + '</div>';
                        html += '<div class="cluster-desc">描述: ' + cluster.description + '</div>';
                        html += '<div class="cluster-tags">';
                        cluster.keywords.forEach(k => html += '<span class="cluster-tag">' + k + '</span>');
                        html += '</div>';
                        html += '<div style="font-size:13px; color:#795548;">包含热点: ' + cluster.count + '条</div>';
                        html += '</div>';
                    });
                    result.innerHTML = html;
                    document.getElementById('statClusters').textContent = data.data.length;
                } else { result.innerHTML = '<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-text">聚类失败: ' + data.message + '</div></div>'; }
            } catch (e) { result.innerHTML = '<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-text">请求失败: ' + e.message + '</div></div>'; }
            btn.disabled = false; btn.textContent = 'AI自动聚类分析';
        }

        async function generatePrompts() {
            const btn = document.getElementById('promptBtn');
            const result = document.getElementById('promptResult');
            btn.disabled = true; btn.textContent = '生成中...';
            result.innerHTML = '<div class="loading"><div class="spinner"></div><div class="loading-text">正在为每个派系生成专业音乐提示词<span class="loading-dots">...</span></div></div>';
            
            try {
                const response = await fetch('/api/generate', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    let html = '';
                    
                    html += '<div class="platform-section">';
                    html += '<div class="platform-header" style="background:#667eea;">';
                    html += '<span>🔵</span><h3>Suno 专用提示词</h3>';
                    html += '<button class="btn-platform" onclick="window.open(&quot;https://suno.com/create&quot;, &quot;_blank&quot;)">🌐 打开 Suno</button>';
                    html += '</div>';
                    data.data.forEach(function(cluster, idx) {
                        if (cluster.prompts.suno) {
                            html += '<div class="prompt-card">';
                            html += '<div class="prompt-title"><span class="prompt-number" style="background:#667eea;">' + (idx + 1) + '</span>派系: ' + cluster.cluster_name + '</div>';
                            html += '<div class="prompt-area">' + escapeHtml(cluster.prompts.suno) + '</div>';
                            html += '<button class="btn-copy" onclick="copyPrompt(this)">📋 复制此提示词</button>';
                            html += '</div>';
                        }
                    });
                    html += '</div>';
                    
                    html += '<div class="platform-section">';
                    html += '<div class="platform-header" style="background:#ff9800;">';
                    html += '<span>🟠</span><h3>Sodance v1.0 专用提示词</h3>';
                    html += '<button class="btn-platform" onclick="window.open(&quot;https://music.douyin.com/studio&quot;, &quot;_blank&quot;)">🌐 打开抖音创作实验室</button>';
                    html += '</div>';
                    data.data.forEach(function(cluster, idx) {
                        if (cluster.prompts.sodance) {
                            html += '<div class="prompt-card">';
                            html += '<div class="prompt-title"><span class="prompt-number" style="background:#ff9800;">' + (idx + 1) + '</span>派系: ' + cluster.cluster_name + '</div>';
                            html += '<div class="prompt-area">' + escapeHtml(cluster.prompts.sodance) + '</div>';
                            html += '<button class="btn-copy" onclick="copyPrompt(this)">📋 复制此提示词</button>';
                            html += '</div>';
                        }
                    });
                    html += '</div>';
                    
                    result.innerHTML = html;
                    document.getElementById('statPrompts').textContent = data.data.length * 2;
                } else { result.innerHTML = '<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-text">生成失败: ' + data.message + '</div></div>'; }
            } catch (e) { result.innerHTML = '<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-text">请求失败: ' + e.message + '</div></div>'; }
            btn.disabled = false; btn.textContent = '一键聚类生成3条提示词';
        }

        function copyPrompt(btn) {
            const text = btn.previousElementSibling.textContent;
            navigator.clipboard.writeText(text).then(function() { alert('提示词已复制到剪贴板！'); });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/api/crawl', methods=['POST'])
def api_crawl():
    global HOTSPOT_DATA
    try:
        from crawlers.hotspot_crawler import HotspotCrawler
        crawler = HotspotCrawler(use_llm=False)
        data = crawler.crawl_all()
        current_time = get_current_time()
        for item in data:
            item["time"] = current_time
        HOTSPOT_DATA = data
        logger.info(f"成功爬取 {len(data)} 条热点数据")
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"爬取热点失败: {e}")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    global HOTSPOT_DATA, ANALYSIS_DATA
    if not HOTSPOT_DATA:
        return jsonify({"success": False, "message": "请先爬取热点数据"})
    
    try:
        all_hotspots = HOTSPOT_DATA
        expected_count = len(all_hotspots)
        prompt = f"""请对以下所有热点进行8维度分析，返回JSON格式：
热点列表：{json.dumps(all_hotspots, ensure_ascii=False)}

要求：
1. 必须返回 {expected_count} 条分析结果，与热点数量完全一致
2. 每条分析结果必须包含以下9个字段：
   - title: 热点标题（必须与输入的热点标题完全一致）
   - theme: 主题
   - emotion: 情绪
   - style: 风格
   - audience: 受众
   - scene: 场景
   - keywords: 关键词
   - popularity: 热度
   - trend: 趋势

请严格返回JSON数组格式，不要包含任何其他文字。
"""
        
        llm_result = call_aliyun_llm(prompt)
        
        if llm_result:
            try:
                analysis_data = json.loads(llm_result)
            except:
                analysis_data = None
        else:
            analysis_data = None
        
        if not analysis_data:
            return jsonify({"success": False, "message": "AI分析失败，请重试"})
        
        if len(analysis_data) != expected_count:
            logger.error(f"分析结果数量不匹配: 期望 {expected_count} 条，实际 {len(analysis_data)} 条")
            return jsonify({"success": False, "message": f"分析结果数量不匹配: 期望 {expected_count} 条，实际 {len(analysis_data)} 条"})
        
        for i, item in enumerate(analysis_data):
            if 'title' not in item or not item['title']:
                if i < len(all_hotspots):
                    item['title'] = all_hotspots[i].get('title', f'热点{i+1}')
                else:
                    item['title'] = f'热点{i+1}'
        
        ANALYSIS_DATA = analysis_data
        logger.info(f"成功分析 {len(analysis_data)} 条热点")
        return jsonify({"success": True, "data": analysis_data})
    except Exception as e:
        logger.error(f"分析热点失败: {e}")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/cluster', methods=['POST'])
def api_cluster():
    global ANALYSIS_DATA, CLUSTER_DATA
    if not ANALYSIS_DATA:
        return jsonify({"success": False, "message": "请先完成热点分析"})
    
    try:
        total_count = len(ANALYSIS_DATA)
        prompt = f"""请对以下热点分析结果进行智能聚类：
分析结果：{json.dumps(ANALYSIS_DATA, ensure_ascii=False)}

要求：
1. 必须将所有 {total_count} 条热点全部分配到5个派系中，不能遗漏
2. 五个派系的count字段总和必须等于 {total_count}
3. 每个派系需要包含：
   - name: 派系名称（由AI自动生成，体现派系特点）
   - description: 派系描述
   - keywords: 核心关键词列表（数组格式）
   - count: 该派系包含的热点数量
4. 请按照情绪、风格、主题的相似性进行分组

请返回JSON数组格式，包含5个派系，不要有其他文字。
"""
        
        llm_result = call_aliyun_llm(prompt)
        
        if llm_result:
            try:
                cluster_data = json.loads(llm_result)
            except:
                cluster_data = None
        else:
            cluster_data = None
        
        if not cluster_data or len(cluster_data) != 5:
            return jsonify({"success": False, "message": "AI聚类失败，请重试"})
        
        CLUSTER_DATA = cluster_data
        logger.info(f"成功聚类为 {len(cluster_data)} 个派系")
        return jsonify({"success": True, "data": cluster_data})
    except Exception as e:
        logger.error(f"聚类失败: {e}")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/generate', methods=['POST'])
def api_generate():
    global CLUSTER_DATA
    if not CLUSTER_DATA:
        return jsonify({"success": False, "message": "请先完成AI聚类"})
    
    try:
        all_prompts = []
        
        for cluster in CLUSTER_DATA:
            cluster_prompts = {
                "cluster_name": cluster['name'],
                "prompts": {}
            }
# 第647行需要修改
# 从: if not cluster_data or len(cluster_data) != 3:
# 改为: if not cluster_data or len(cluster_data) != 5:# 第647行需要修改
# 从: if not cluster_data or len(cluster_data) != 3:
# 改为: if not cluster_data or len(cluster_data) != 5:# 第647行需要修改
# 从: if not cluster_data or len(cluster_data) != 3:
# 改为: if not cluster_data or len(cluster_data) != 5:# 第647行需要修改
# 从: if not cluster_data or len(cluster_data) != 3:
# 改为: if not cluster_data or len(cluster_data) != 5:# 第647行需要修改
# 从: if not cluster_data or len(cluster_data) != 3:
# 改为: if not cluster_data or len(cluster_data) != 5:            
            # 每个派系生成1条Suno提示词，总字数不超过3000字
            suno_prompt = f"""请为以下热点派系生成1条完整的音乐创作提示词：
派系名称：{cluster['name']}
派系描述：{cluster['description']}
核心关键词：{', '.join(cluster['keywords'])}

要求包含以下要素：
1. 音乐风格：明确标注具体子流派
2. BPM范围：给出精确范围（如110-115）
3. 情绪基调：描述情绪曲线
4. 配器建议：具体乐器清单和使用场景
5. 编曲结构：段落结构设计
6. 歌词方向：主题与视角，避免真实人名事件
7. 适用场景：短视频/BGM使用场景

总字数控制在3000字以内，请直接输出提示词内容。
"""
            
            suno_result = call_aliyun_llm(suno_prompt)
            if suno_result:
                if len(suno_result) > 3000:
                    suno_result = suno_result[:2997] + '...'
                cluster_prompts["prompts"]["suno"] = suno_result
            else:
                return jsonify({"success": False, "message": "生成Suno提示词失败，请重试"})
            
            sodance_prompt = f"""请根据以下热点派系，生成适配抖音Sodance v1.0的音乐创作提示词，字数控制在500字以内：
派系名称：{cluster['name']}
派系描述：{cluster['description']}
核心关键词：{', '.join(cluster['keywords'])}

要求只做氛围感、风格、情绪、短视频场景描述，**不要写BPM、轨道数量、乐器分轨、秒数结构、混音工程参数**。
内容要求：
1. 匹配本派系整体情绪气质，定精准曲风；
2. 适配抖音短视频传播调性，适合15s/30s剪辑使用；
3. 编曲层次饱满、情绪自然起伏、有前奏主歌副歌桥段完整段落感；
4. 音色干净流畅、旋律好听耐听，风格贴合热点舆论氛围；
5. 语言高级简洁，只输出可直接给Sodance v1.0使用的成品提示词。

字数严格控制在500字以内！
"""
            
            sodance_result = call_aliyun_llm(sodance_prompt)
            if sodance_result:
                if len(sodance_result) > 500:
                    sodance_result = sodance_result[:497] + '...'
                cluster_prompts["prompts"]["sodance"] = sodance_result
            else:
                return jsonify({"success": False, "message": "生成Sodance提示词失败，请重试"})
            
            all_prompts.append(cluster_prompts)
        
        logger.info(f"成功生成 {len(CLUSTER_DATA)} 个派系的提示词")
        return jsonify({"success": True, "data": all_prompts})
    except Exception as e:
        logger.error(f"生成提示词失败: {e}")
        return jsonify({"success": False, "message": str(e)})

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("AI音乐自动化 - 可视化面板")
    logger.info("=" * 60)
    logger.info("访问地址: http://localhost:5002")
    logger.info("=" * 60)
    app.run(host='0.0.0.0', port=5002, debug=False)
