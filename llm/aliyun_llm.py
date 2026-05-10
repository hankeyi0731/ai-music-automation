import requests
import json
import logging
import time
from config import ALIYUN_LLM_CONFIG, MAX_RETRY, RETRY_DELAY

logger = logging.getLogger('music_agent')

class AliyunLLM:
    """阿里云大模型调用模块"""
    
    def __init__(self):
        self.api_key = ALIYUN_LLM_CONFIG['api_key']
        self.base_url = ALIYUN_LLM_CONFIG['base_url']
        self.models = ALIYUN_LLM_CONFIG['models']
        self.model_assignment = ALIYUN_LLM_CONFIG['model_assignment']
        self.timeout = ALIYUN_LLM_CONFIG['timeout']
        self.max_tokens = ALIYUN_LLM_CONFIG['max_tokens']
        self.temperature = ALIYUN_LLM_CONFIG['temperature']
    
    def _get_model_name(self, task_type):
        """根据任务类型获取模型名称"""
        assignment = self.model_assignment.get(task_type)
        if assignment:
            return self.models.get(assignment)
        return self.models['qwen_plus']  # 默认使用qwen-plus
    
    def _call_api(self, model_name, messages):
        """调用阿里云大模型API"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        payload = {
            'model': model_name,
            'messages': messages,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }
        
        for attempt in range(MAX_RETRY):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                result = response.json()
                
                if result.get('status') == 'success':
                    return result['output']['text']
                
                logger.warning(f"API返回异常: {result}")
                time.sleep(RETRY_DELAY)
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"API调用失败，第 {attempt+1}/{MAX_RETRY} 次尝试: {str(e)}")
                time.sleep(RETRY_DELAY)
        
        raise Exception(f"API调用失败，已达到最大重试次数 {MAX_RETRY}")
    
    def crawl_clean_extract(self, raw_data, task_description="提取关键信息并结构化"):
        """内容爬取、清洗、提取、结构化 - 使用 qwen-flash"""
        model_name = self._get_model_name('crawl_clean_extract')
        
        messages = [
            {
                'role': 'system',
                'content': '你是一个专业的数据清洗和信息提取助手。请对提供的数据进行清洗、提取关键信息并输出结构化结果。'
            },
            {
                'role': 'user',
                'content': f"{task_description}\n\n原始数据:\n{json.dumps(raw_data, ensure_ascii=False, indent=2)}"
            }
        ]
        
        logger.info(f"调用 {model_name} 进行数据清洗和提取")
        result = self._call_api(model_name, messages)
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {'text': result}
    
    def analyze_8dimensional(self, hotspot_data):
        """8维度深度拆解、分析、智能选组 - 使用 qwen-plus"""
        model_name = self._get_model_name('analysis_8dimensional')
        
        system_prompt = """
你是一个专业的热点分析和音乐创作顾问。请对热点内容进行8维度强制分层拆解：

1. 表层事实：提炼事件核心经过、关键人物、核心一句话摘要；
2. 情绪氛围：判定整体情绪基调、情绪层次、强弱起伏；
3. 内核立意：挖掘背后价值观、大众共情点、深层共鸣逻辑；
4. 音乐适配：匹配适合曲风、BPM区间、建议音轨数量、配器风格、编曲层次要求；
5. 适配人群：精准定位会产生共鸣的用户群体特征；
6. 内容衍生：可衍生出的文案类型、短视频脚本、语录、故事改编方向；
7. 关键词标签：提取高热度关键词、话题标签；
8. 结构分层：梳理起承转合、段落划分，适配音乐前奏/主歌/副歌结构。

请输出结构化的JSON格式结果。
        """.strip()
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"请对以下热点进行8维度分析:\n\n{json.dumps(hotspot_data, ensure_ascii=False)}"}
        ]
        
        logger.info(f"调用 {model_name} 进行8维度分析")
        result = self._call_api(model_name, messages)
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            # 如果不是JSON格式，返回原始结果
            return {
                'analysis_text': result,
                'hotspot': hotspot_data
            }
    
    def generate_prompt(self, analysis_result, song_count=3):
        """音乐提示词、标题、文案生成 - 使用 qwen-plus"""
        model_name = self._get_model_name('prompt_generation')
        
        system_prompt = """
你是一个专业的音乐创作提示词工程师。请根据热点分析结果，生成高质量的音乐创作提示词。

输出要求：
1. 生成 {song_count} 组不同风格的音乐提示词
2. 每组包含：歌曲类型（带人声AI歌曲/纯音乐BGM）、适配工具、适配平台、完整prompt
3. 格式为JSON数组
4. 参考当下国内外爆款音乐结构
        """.strip()
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"根据以下分析结果，生成 {song_count} 组音乐创作提示词:\n\n{json.dumps(analysis_result, ensure_ascii=False, indent=2)}"}
        ]
        
        logger.info(f"调用 {model_name} 生成音乐提示词")
        result = self._call_api(model_name, messages)
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return [{'prompt': result, 'song_type': '纯音乐BGM', 'tool': '豆包音乐', 'platforms': ['腾讯音乐人', '网易音乐人']}]
    
    def memory_reinforcement(self, history_data, new_analysis):
        """记忆结论、强化学习迭代 - 使用 qwen-plus"""
        model_name = self._get_model_name('memory_reinforcement')
        
        system_prompt = """
你是一个专业的数据分析和策略优化助手。请分析历史数据和新的分析结果，输出：
1. 总结最优策略和模式
2. 识别成功因素和失败模式
3. 生成可复用的优化结论
4. 为次日同类热点提供优先复用的策略建议

请输出结构化的JSON格式结果。
        """.strip()
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"""
历史数据:
{json.dumps(history_data, ensure_ascii=False, indent=2)}

新分析结果:
{json.dumps(new_analysis, ensure_ascii=False, indent=2)}

请分析并输出最优策略和可复用结论。
            """.strip()}
        ]
        
        logger.info(f"调用 {model_name} 进行记忆强化学习")
        result = self._call_api(model_name, messages)
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {'conclusion': result}
    
    def generate_title_and_copy(self, analysis_result, platform='抖音'):
        """生成标题和文案"""
        model_name = self._get_model_name('prompt_generation')
        
        platform_style = {
            '抖音': '简短、有冲击力、带话题标签',
            '微博': '稍长、有悬念、带热门话题',
            'QQ音乐': '文艺、情感化、突出音乐性',
            '网易云音乐': '感性、有故事感、引发共鸣'
        }
        
        system_prompt = f"""
你是一个专业的音乐文案策划师。请为{platform}平台生成吸引人的标题和文案。

风格要求：{platform_style.get(platform, '通用风格')}

请输出JSON格式，包含title和copy字段。
        """.strip()
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"根据以下分析结果生成标题和文案:\n\n{json.dumps(analysis_result, ensure_ascii=False, indent=2)}"}
        ]
        
        logger.info(f"调用 {model_name} 生成{platform}标题和文案")
        result = self._call_api(model_name, messages)
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {'title': '热门音乐', 'copy': result}
    
    def batch_analyze(self, hotspots):
        """批量分析多个热点"""
        results = []
        
        for hotspot in hotspots:
            try:
                analysis = self.analyze_8dimensional(hotspot)
                results.append({
                    'hotspot': hotspot,
                    'analysis': analysis
                })
            except Exception as e:
                logger.error(f"分析热点失败: {str(e)}")
                results.append({
                    'hotspot': hotspot,
                    'error': str(e)
                })
        
        return results