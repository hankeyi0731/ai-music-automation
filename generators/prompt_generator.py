import logging
from config import DAILY_MUSIC_LIMIT

logger = logging.getLogger('music_agent')

class PromptGenerator:
    """音乐prompt生成模块 - 支持阿里云大模型增强生成"""
    
    def __init__(self, use_llm=True):
        self.use_llm = use_llm
        self.llm = None
        
        if self.use_llm:
            try:
                from llm.aliyun_llm import AliyunLLM
                self.llm = AliyunLLM()
                logger.info("已初始化阿里云大模型用于prompt生成")
            except Exception as e:
                logger.warning(f"初始化LLM失败，使用本地生成: {str(e)}")
                self.use_llm = False
        
        # 平台分流规则
        self.platform_rules = {
            '带人声AI歌曲': {
                'primary': ['抖音音乐开放平台'],
                'secondary': []
            },
            '纯音乐BGM': {
                'primary': ['腾讯音乐人', '网易音乐人'],
                'secondary': []
            }
        }
        
        # 曲风模板
        self.genre_templates = {
            '流行': '流行风格，朗朗上口的旋律，现代电子配器',
            '抒情': '抒情风格，温暖治愈，适合情感表达',
            '民谣': '民谣风格，吉他为主，质朴自然',
            '舞曲': '舞曲风格，强烈节奏，适合舞蹈',
            '电子': '电子风格，合成器音效，未来感',
            '摇滚': '摇滚风格，电吉他，充满力量感',
            '国风': '国风风格，传统乐器，东方韵味',
            '钢琴': '钢琴独奏，优雅动人',
            '大提琴': '大提琴独奏，深沉内敛'
        }
    
    def generate_prompt(self, analysis):
        """根据分析结果生成单个prompt"""
        music_fit = analysis['music_fit']
        emotion = analysis['emotion']
        structure = analysis['structure']
        keywords = analysis['keywords']
        
        # 确定歌曲类型
        song_type = '带人声AI歌曲' if emotion['emotion_level'] >= 2 else '纯音乐BGM'
        
        # 选择工具
        tool = '抖音创作实验室' if song_type == '带人声AI歌曲' else '豆包音乐'
        
        # 构建曲风描述
        genres = music_fit['genres']
        genre_desc = '、'.join([self.genre_templates.get(g, g) for g in genres])
        
        # 构建BPM描述
        bpm_min, bpm_max = music_fit['bpm_range']
        bpm_desc = f"BPM {bpm_min}-{bpm_max}"
        
        # 构建配器描述
        instrument_desc = music_fit['instrument_style']
        
        # 构建结构描述
        structure_desc = structure['duration']
        
        # 构建情绪描述
        emotion_desc = {
            '积极': '欢快、充满活力',
            '消极': '悲伤、深情',
            '中性': '平静、舒缓'
        }[emotion['emotion_type']]
        
        # 构建完整prompt
        prompt = f"""
一首{emotion_desc}的{genres[0]}风格音乐，{genre_desc}，
{BPM描述}，{instrument_desc}，
编曲{music_fit['arrangement_requirement']}，建议{music_fit['suggested_tracks']}音轨，
时长{structure_desc}，适合作为短视频背景音乐或热门歌曲。
关键词：{','.join(keywords['hot_keywords'])}
        """.strip()
        
        return {
            'prompt': prompt,
            'song_type': song_type,
            'tool': tool,
            'platforms': self.platform_rules[song_type]['primary'],
            'analysis': analysis,
            'emotion_type': emotion['emotion_type'],
            'genre': genres[0],
            'bpm': f"{bpm_min}-{bpm_max}"
        }
    
    def generate(self, analysis_results):
        """生成3组高质量音乐prompt"""
        logger.info("开始生成音乐prompt...")
        
        prompts = []
        
        # 筛选最有潜力的热点
        sorted_results = sorted(
            analysis_results,
            key=lambda x: x['emotion'].get('emotion_level', 0) if isinstance(x['emotion'], dict) else 0,
            reverse=True
        )
        
        # 优先使用LLM生成（qwen-plus-2025-07-28）
        if self.use_llm and self.llm and sorted_results:
            try:
                # 使用LLM生成prompt
                llm_prompts = self.llm.generate_prompt(sorted_results[0], song_count=DAILY_MUSIC_LIMIT)
                
                for i, llm_prompt in enumerate(llm_prompts[:DAILY_MUSIC_LIMIT]):
                    prompt_data = {
                        'id': i + 1,
                        'prompt': llm_prompt.get('prompt', ''),
                        'song_type': llm_prompt.get('song_type', '纯音乐BGM'),
                        'tool': llm_prompt.get('tool', '豆包音乐'),
                        'platforms': llm_prompt.get('platforms', ['腾讯音乐人', '网易音乐人']),
                        'analysis': sorted_results[0],
                        'emotion_type': sorted_results[0]['emotion'].get('emotion_type', '中性') if isinstance(sorted_results[0]['emotion'], dict) else '中性',
                        'genre': '流行',
                        'bpm': '90-120',
                        'source': 'llm'
                    }
                    prompts.append(prompt_data)
                
                logger.info(f"使用LLM生成了 {len(prompts)} 组音乐prompt")
                return prompts
                
            except Exception as e:
                logger.warning(f"LLM生成prompt失败，回退到本地生成: {str(e)}")
        
        # 本地规则引擎生成
        for i, analysis in enumerate(sorted_results[:DAILY_MUSIC_LIMIT]):
            try:
                prompt_data = self.generate_prompt(analysis)
                prompt_data['id'] = i + 1
                prompt_data['source'] = 'local'
                prompts.append(prompt_data)
            except Exception as e:
                logger.error(f"生成prompt失败: {str(e)}")
        
        logger.info(f"生成了 {len(prompts)} 组音乐prompt")
        return prompts
    
    def generate_variations(self, base_prompt, count=3):
        """生成prompt变体"""
        variations = []
        
        for i in range(count):
            variation = {
                'prompt': base_prompt['prompt'] + f" 版本{i+1}",
                'song_type': base_prompt['song_type'],
                'tool': base_prompt['tool'],
                'platforms': base_prompt['platforms'],
                'variation': i + 1
            }
            variations.append(variation)
        
        return variations