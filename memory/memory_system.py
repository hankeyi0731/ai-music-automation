import json
import os
import logging
from datetime import datetime
from config import DATA_DIR

logger = logging.getLogger('music_agent')

class MemorySystem:
    """记忆系统 - 存储和复用优化结论，支持阿里云大模型强化学习"""
    
    def __init__(self, use_llm=True):
        self.use_llm = use_llm
        self.llm = None
        
        if self.use_llm:
            try:
                from llm.aliyun_llm import AliyunLLM
                self.llm = AliyunLLM()
                logger.info("已初始化阿里云大模型用于记忆强化学习")
            except Exception as e:
                logger.warning(f"初始化LLM失败，使用本地记忆: {str(e)}")
                self.use_llm = False
        
        self.memory_file = os.path.join(DATA_DIR, 'memory.json')
        self.memory = self._load_memory()
    
    def _load_memory(self):
        """加载记忆数据"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载记忆数据失败: {str(e)}")
                return self._create_empty_memory()
        return self._create_empty_memory()
    
    def _create_empty_memory(self):
        """创建空的记忆结构"""
        return {
            'version': '1.0',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'hotspot_patterns': [],  # 热点模式
            'genre_performance': {},  # 曲风表现
            'structure_effectiveness': {},  # 结构效果
            'platform_preferences': {},  # 平台偏好
            'best_practices': [],  # 最佳实践
            'failed_patterns': []  # 失败模式
        }
    
    def update(self, conclusions):
        """根据复盘结论更新记忆 - 使用LLM进行强化学习迭代"""
        logger.info("更新记忆系统...")
        
        if not conclusions:
            return
        
        try:
            # 使用LLM进行强化学习分析（qwen-plus-2025-07-28）
            if self.use_llm and self.llm:
                try:
                    # 获取历史数据
                    history_data = {
                        'best_practices': self.memory['best_practices'],
                        'hotspot_patterns': self.memory['hotspot_patterns'],
                        'platform_preferences': self.memory['platform_preferences']
                    }
                    
                    # 调用LLM进行强化学习分析
                    llm_result = self.llm.memory_reinforcement(history_data, conclusions)
                    
                    # 解析LLM结果
                    if isinstance(llm_result, dict):
                        # 更新最佳实践
                        if 'best_practices' in llm_result:
                            for practice in llm_result['best_practices']:
                                content = practice.get('content', str(practice))
                                if content not in [p['content'] for p in self.memory['best_practices']]:
                                    self.memory['best_practices'].append({
                                        'content': content,
                                        'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        'usage_count': 0
                                    })
                        
                        # 更新策略建议
                        if 'strategy' in llm_result:
                            self.memory['optimization_strategy'] = llm_result['strategy']
                            
                        # 更新失败模式
                        if 'failed_patterns' in llm_result:
                            for pattern in llm_result['failed_patterns']:
                                if pattern not in self.memory['failed_patterns']:
                                    self.memory['failed_patterns'].append(pattern)
                    else:
                        # LLM返回文本结果，作为总结保存
                        self.memory['llm_summary'] = llm_result
                    
                    logger.info("使用LLM完成记忆强化学习")
                    
                except Exception as e:
                    logger.warning(f"LLM强化学习失败，使用本地规则: {str(e)}")
            
            # 本地规则更新（始终执行，作为LLM的补充）
            # 更新平台偏好
            if 'platform_performance' in conclusions:
                for platform, stats in conclusions['platform_performance'].items():
                    if platform not in self.memory['platform_preferences']:
                        self.memory['platform_preferences'][platform] = []
                    self.memory['platform_preferences'][platform].append({
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'avg_plays': stats.get('avg_plays', 0),
                        'avg_likes': stats.get('avg_likes', 0),
                        'avg_completion': stats.get('avg_completion', 0)
                    })
            
            # 更新最佳实践
            if 'recommendations' in conclusions:
                for rec in conclusions['recommendations']:
                    if rec not in [p['content'] for p in self.memory['best_practices']]:
                        self.memory['best_practices'].append({
                            'content': rec,
                            'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'usage_count': 0
                        })
            
            # 更新热点模式
            if 'top_performing_content' in conclusions:
                title = conclusions['top_performing_content'].get('title', '')
                self.memory['hotspot_patterns'].append({
                    'title': title,
                    'plays': conclusions['top_performing_content'].get('plays', 0),
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
            
            # 更新时间戳
            self.memory['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 保存记忆
            self._save_memory()
            
            logger.info("记忆系统更新完成")
            
        except Exception as e:
            logger.error(f"更新记忆系统失败: {str(e)}")
    
    def _save_memory(self):
        """保存记忆数据"""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存记忆数据失败: {str(e)}")
    
    def get_best_platform(self, song_type):
        """获取最佳发布平台"""
        if not self.memory['platform_preferences']:
            # 默认返回规则
            if song_type == '带人声AI歌曲':
                return '抖音音乐开放平台'
            else:
                return '腾讯音乐人'
        
        # 计算平均播放量最高的平台
        best_platform = None
        best_avg_plays = 0
        
        for platform, records in self.memory['platform_preferences'].items():
            if records:
                avg_plays = sum(r['avg_plays'] for r in records) / len(records)
                if avg_plays > best_avg_plays:
                    best_avg_plays = avg_plays
                    best_platform = platform
        
        return best_platform or ('抖音音乐开放平台' if song_type == '带人声AI歌曲' else '腾讯音乐人')
    
    def get_best_practices(self, limit=5):
        """获取最佳实践"""
        practices = sorted(
            self.memory['best_practices'],
            key=lambda x: x.get('usage_count', 0),
            reverse=True
        )
        return practices[:limit]
    
    def increment_practice_usage(self, practice_content):
        """增加最佳实践使用次数"""
        for practice in self.memory['best_practices']:
            if practice['content'] == practice_content:
                practice['usage_count'] = practice.get('usage_count', 0) + 1
                self._save_memory()
                break
    
    def get_hotspot_patterns(self, limit=10):
        """获取热点模式"""
        patterns = sorted(
            self.memory['hotspot_patterns'],
            key=lambda x: x.get('plays', 0),
            reverse=True
        )
        return patterns[:limit]
    
    def get_memory_summary(self):
        """获取记忆摘要"""
        return {
            'total_best_practices': len(self.memory['best_practices']),
            'total_hotspot_patterns': len(self.memory['hotspot_patterns']),
            'tracked_platforms': list(self.memory['platform_preferences'].keys()),
            'last_updated': self.memory['updated_at']
        }
    
    def clear_memory(self):
        """清空记忆"""
        self.memory = self._create_empty_memory()
        self._save_memory()
        logger.info("记忆已清空")