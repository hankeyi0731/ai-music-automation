import logging
import json

logger = logging.getLogger('music_agent')

class HotspotAnalyzer:
    """8维度强制分层拆解引擎 - 全部使用阿里云qwen-plus-2025-07-28深度AI分析"""
    
    def __init__(self):
        self.llm = None
        self._init_llm()
    
    def _init_llm(self):
        """初始化阿里云大模型"""
        try:
            from llm.aliyun_llm import AliyunLLM
            self.llm = AliyunLLM()
            logger.info("已初始化阿里云qwen-plus-2025-07-28大模型")
        except Exception as e:
            logger.error(f"初始化LLM失败: {str(e)}")
            raise RuntimeError(f"无法初始化LLM: {str(e)}")
    
    def analyze_8dimensional(self, hotspot):
        """使用LLM进行8维度深度分析"""
        if not self.llm:
            raise RuntimeError("LLM未初始化")
        
        system_prompt = """
你是一位专业的热点分析和音乐创作顾问，擅长将热点事件转化为音乐创作灵感。请对以下热点内容进行8维度深度分析：

【1】表层事实
- 热点本质：事件的核心是什么
- 核心冲突：矛盾点在哪里
- 传播引爆点：为什么会火
- 一句话爆款摘要：用一句话概括

【2】情绪氛围
- 主情绪：喜/怒/哀/惧/燃/治愈/爽（选1-2个）
- 情绪强度：1-10分
- 情绪曲线：起伏节奏描述（平稳/渐升/爆发/波动）
- 适合的音乐氛围：描述适合的音乐感觉

【3】内核立意
- 大众共鸣点：什么能打动人心
- 价值观内核：背后的价值取向
- 社会情绪：反映了什么社会心态
- 能让人转发的理由：为什么人们会分享

【4】音乐适配（最关键）
- 最佳曲风：具体曲风名称（如流行、抒情、电子、国风等）
- 最佳BPM：具体数值或范围
- 配器风格：乐器搭配风格
- 编曲层次：简单/中等/复杂
- 人声/纯音乐判断：明确选择
- 爆款结构参考：参考的热门歌曲结构

【5】适配人群
- 年龄：目标年龄范围
- 性别倾向：男/女/中性
- 兴趣标签：3-5个兴趣关键词
- 行为偏好：用户行为特点
- 平台分布：主要活跃平台

【6】内容衍生
- 爆款文案方向：文案风格建议
- 短视频脚本结构：分镜建议
- 标题公式：吸睛标题模板
- 封面方向：视觉风格建议

【7】关键词标签
- 热搜词：5个核心关键词
- 音乐标签：适合的音乐风格标签
- 平台流量标签：各平台热门标签
- 可带入歌词的关键词：适合写进歌词的词

【8】结构分层
- 前奏风格：开场设计
- 主歌情绪：叙述部分感觉
- 副歌爆发点：高潮设计
- 尾句记忆点：结尾亮点
- 整首歌时长结构：各部分时长分配

请输出JSON格式，确保每个维度都有详细内容。
        """.strip()
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"请对以下热点进行8维度深度分析:\n\n{json.dumps(hotspot, ensure_ascii=False)}"}
        ]
        
        try:
            result = self.llm._call_api('qwen-plus-2025-07-28', messages)
            return json.loads(result)
        except json.JSONDecodeError:
            # 如果LLM返回非JSON格式，包装成结构化数据
            return {
                'raw_result': result,
                'analysis_source': 'llm_text'
            }
        except Exception as e:
            logger.error(f"LLM分析失败: {str(e)}")
            raise
    
    def analyze_all(self, hotspots):
        """对所有热点进行8维度分析 - 全部走LLM"""
        logger.info("开始8维度深度拆解（全部使用qwen-plus-2025-07-28）...")
        
        if not self.llm:
            raise RuntimeError("LLM未初始化，无法进行分析")
        
        results = []
        
        for hotspot in hotspots:
            try:
                logger.info(f"分析热点: {hotspot.get('title', '未知')}")
                
                # 使用LLM进行深度分析
                llm_result = self.analyze_8dimensional(hotspot)
                
                # 结构化处理LLM结果
                analysis = self._structure_analysis(hotspot, llm_result)
                results.append(analysis)
                
                logger.info(f"完成热点分析: {hotspot.get('title', '未知')}")
                
            except Exception as e:
                logger.error(f"分析热点失败: {str(e)}")
                # 添加失败记录
                results.append({
                    'hotspot': hotspot,
                    'error': str(e),
                    'analysis_source': 'error'
                })
        
        logger.info(f"完成 {len(results)} 条热点的8维度分析")
        return results
    
    def _structure_analysis(self, hotspot, llm_result):
        """结构化LLM分析结果"""
        # 标准化字段名称（支持中英文字段）
        def get_field(data, keys):
            for key in keys:
                if key in data:
                    return data[key]
            return {} if isinstance(data, dict) else ""
        
        analysis = {
            'hotspot': hotspot,
            'analysis_source': 'llm',
            'llm_model': 'qwen-plus-2025-07-28',
            
            # 【1】表层事实
            'surface_fact': {
                'hotspot_nature': get_field(llm_result, ['表层事实', 'surface_fact', '热点本质', 'nature']).get('热点本质', '') if isinstance(get_field(llm_result, ['表层事实', 'surface_fact']), dict) else '',
                'core_conflict': get_field(llm_result, ['表层事实', 'surface_fact']).get('核心冲突', '') if isinstance(get_field(llm_result, ['表层事实', 'surface_fact']), dict) else '',
                'viral_point': get_field(llm_result, ['表层事实', 'surface_fact']).get('传播引爆点', '') if isinstance(get_field(llm_result, ['表层事实', 'surface_fact']), dict) else '',
                'summary': get_field(llm_result, ['表层事实', 'surface_fact']).get('一句话爆款摘要', '') if isinstance(get_field(llm_result, ['表层事实', 'surface_fact']), dict) else ''
            },
            
            # 【2】情绪氛围
            'emotion': {
                'main_emotion': get_field(llm_result, ['情绪氛围', 'emotion']).get('主情绪', '') if isinstance(get_field(llm_result, ['情绪氛围', 'emotion']), dict) else '',
                'emotion_intensity': get_field(llm_result, ['情绪氛围', 'emotion']).get('情绪强度', 5) if isinstance(get_field(llm_result, ['情绪氛围', 'emotion']), dict) else 5,
                'emotion_curve': get_field(llm_result, ['情绪氛围', 'emotion']).get('情绪曲线', '') if isinstance(get_field(llm_result, ['情绪氛围', 'emotion']), dict) else '',
                'music_atmosphere': get_field(llm_result, ['情绪氛围', 'emotion']).get('适合的音乐氛围', '') if isinstance(get_field(llm_result, ['情绪氛围', 'emotion']), dict) else ''
            },
            
            # 【3】内核立意
            'core_meaning': {
                'empathy_points': get_field(llm_result, ['内核立意', 'core_meaning']).get('大众共鸣点', []) if isinstance(get_field(llm_result, ['内核立意', 'core_meaning']), dict) else [],
                'values_core': get_field(llm_result, ['内核立意', 'core_meaning']).get('价值观内核', '') if isinstance(get_field(llm_result, ['内核立意', 'core_meaning']), dict) else '',
                'social_emotion': get_field(llm_result, ['内核立意', 'core_meaning']).get('社会情绪', '') if isinstance(get_field(llm_result, ['内核立意', 'core_meaning']), dict) else '',
                'share_reason': get_field(llm_result, ['内核立意', 'core_meaning']).get('能让人转发的理由', '') if isinstance(get_field(llm_result, ['内核立意', 'core_meaning']), dict) else ''
            },
            
            # 【4】音乐适配
            'music_fit': {
                'best_genre': get_field(llm_result, ['音乐适配', 'music_fit']).get('最佳曲风', '') if isinstance(get_field(llm_result, ['音乐适配', 'music_fit']), dict) else '',
                'best_bpm': get_field(llm_result, ['音乐适配', 'music_fit']).get('最佳BPM', '') if isinstance(get_field(llm_result, ['音乐适配', 'music_fit']), dict) else '',
                'instrument_style': get_field(llm_result, ['音乐适配', 'music_fit']).get('配器风格', '') if isinstance(get_field(llm_result, ['音乐适配', 'music_fit']), dict) else '',
                'arrangement_level': get_field(llm_result, ['音乐适配', 'music_fit']).get('编曲层次', '') if isinstance(get_field(llm_result, ['音乐适配', 'music_fit']), dict) else '',
                'vocal_or_instrumental': get_field(llm_result, ['音乐适配', 'music_fit']).get('人声/纯音乐判断', '') if isinstance(get_field(llm_result, ['音乐适配', 'music_fit']), dict) else '',
                'hit_structure': get_field(llm_result, ['音乐适配', 'music_fit']).get('爆款结构参考', '') if isinstance(get_field(llm_result, ['音乐适配', 'music_fit']), dict) else ''
            },
            
            # 【5】适配人群
            'target_audience': {
                'age_range': get_field(llm_result, ['适配人群', 'target_audience']).get('年龄', '') if isinstance(get_field(llm_result, ['适配人群', 'target_audience']), dict) else '',
                'gender_tendency': get_field(llm_result, ['适配人群', 'target_audience']).get('性别倾向', '') if isinstance(get_field(llm_result, ['适配人群', 'target_audience']), dict) else '',
                'interest_tags': get_field(llm_result, ['适配人群', 'target_audience']).get('兴趣标签', []) if isinstance(get_field(llm_result, ['适配人群', 'target_audience']), dict) else [],
                'behavior_preferences': get_field(llm_result, ['适配人群', 'target_audience']).get('行为偏好', '') if isinstance(get_field(llm_result, ['适配人群', 'target_audience']), dict) else '',
                'platform_distribution': get_field(llm_result, ['适配人群', 'target_audience']).get('平台分布', []) if isinstance(get_field(llm_result, ['适配人群', 'target_audience']), dict) else []
            },
            
            # 【6】内容衍生
            'content_derivation': {
                'copy_direction': get_field(llm_result, ['内容衍生', 'content_derivation']).get('爆款文案方向', '') if isinstance(get_field(llm_result, ['内容衍生', 'content_derivation']), dict) else '',
                'video_structure': get_field(llm_result, ['内容衍生', 'content_derivation']).get('短视频脚本结构', '') if isinstance(get_field(llm_result, ['内容衍生', 'content_derivation']), dict) else '',
                'title_formula': get_field(llm_result, ['内容衍生', 'content_derivation']).get('标题公式', '') if isinstance(get_field(llm_result, ['内容衍生', 'content_derivation']), dict) else '',
                'cover_direction': get_field(llm_result, ['内容衍生', 'content_derivation']).get('封面方向', '') if isinstance(get_field(llm_result, ['内容衍生', 'content_derivation']), dict) else ''
            },
            
            # 【7】关键词标签
            'keywords': {
                'hot_search_words': get_field(llm_result, ['关键词标签', 'keywords']).get('热搜词', []) if isinstance(get_field(llm_result, ['关键词标签', 'keywords']), dict) else [],
                'music_tags': get_field(llm_result, ['关键词标签', 'keywords']).get('音乐标签', []) if isinstance(get_field(llm_result, ['关键词标签', 'keywords']), dict) else [],
                'platform_tags': get_field(llm_result, ['关键词标签', 'keywords']).get('平台流量标签', []) if isinstance(get_field(llm_result, ['关键词标签', 'keywords']), dict) else [],
                'lyric_keywords': get_field(llm_result, ['关键词标签', 'keywords']).get('可带入歌词的关键词', []) if isinstance(get_field(llm_result, ['关键词标签', 'keywords']), dict) else []
            },
            
            # 【8】结构分层
            'structure': {
                'intro_style': get_field(llm_result, ['结构分层', 'structure']).get('前奏风格', '') if isinstance(get_field(llm_result, ['结构分层', 'structure']), dict) else '',
                'verse_emotion': get_field(llm_result, ['结构分层', 'structure']).get('主歌情绪', '') if isinstance(get_field(llm_result, ['结构分层', 'structure']), dict) else '',
                'chorus_climax': get_field(llm_result, ['结构分层', 'structure']).get('副歌爆发点', '') if isinstance(get_field(llm_result, ['结构分层', 'structure']), dict) else '',
                'ending_memory': get_field(llm_result, ['结构分层', 'structure']).get('尾句记忆点', '') if isinstance(get_field(llm_result, ['结构分层', 'structure']), dict) else '',
                'duration_structure': get_field(llm_result, ['结构分层', 'structure']).get('整首歌时长结构', '') if isinstance(get_field(llm_result, ['结构分层', 'structure']), dict) else ''
            },
            
            # 原始LLM结果
            'raw_llm_result': llm_result
        }
        
        return analysis