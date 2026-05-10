#!/usr/bin/env python3
"""
音乐爆款智能体 - 主入口
实现完整自动化闭环：热点爬取→分层拆解→prompt生成→音乐生成→平台发布→数据爬取→复盘分析
"""

import os
import sys
import time
import logging
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import LOG_DIR, LOG_CONFIG, DAILY_CRAWL_TIME, DAILY_PUBLISH_TIME, DAILY_ANALYZE_TIME
from crawlers.hotspot_crawler import HotspotCrawler
from analyzers.hotspot_analyzer import HotspotAnalyzer
from generators.prompt_generator import PromptGenerator
from generators.music_generator import MusicGenerator
from publishers.platform_publisher import PlatformPublisher
from analyzers.data_analyzer import DataAnalyzer
from memory.memory_system import MemorySystem
from utils.scheduler import Scheduler

# 初始化日志
def init_logging():
    log_file = os.path.join(LOG_DIR, LOG_CONFIG['file_name'])
    logging.basicConfig(
        level=getattr(logging, LOG_CONFIG['level']),
        format=LOG_CONFIG['format'],
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('music_agent')

def daily_workflow():
    """每日自动化工作流"""
    logger = init_logging()
    logger.info("========== 开始每日自动化工作流 ==========")
    
    try:
        # 1. 爬取热点
        logger.info("步骤1: 爬取热点数据")
        crawler = HotspotCrawler()
        hotspots = crawler.crawl_all()
        
        # 2. 分层拆解
        logger.info("步骤2: 8维度分层拆解")
        analyzer = HotspotAnalyzer()
        analysis_results = analyzer.analyze_all(hotspots)
        
        # 3. 生成prompt
        logger.info("步骤3: 生成音乐prompt")
        prompt_gen = PromptGenerator()
        prompts = prompt_gen.generate(analysis_results)
        
        # 4. 生成音乐
        logger.info("步骤4: 双轨生成音乐")
        music_gen = MusicGenerator()
        audio_files = music_gen.generate_all(prompts)
        
        # 5. 平台发布
        logger.info("步骤5: 平台分流发布")
        publisher = PlatformPublisher()
        publish_results = publisher.publish_all(audio_files)
        
        logger.info("========== 每日自动化工作流完成 ==========")
        return True
        
    except Exception as e:
        logger.error(f"每日工作流执行失败: {str(e)}", exc_info=True)
        return False

def analyze_publish_data():
    """分析发布数据（24小时后执行）"""
    logger = init_logging()
    logger.info("========== 开始发布数据复盘分析 ==========")
    
    try:
        # 爬取发布数据
        logger.info("步骤1: 爬取各平台数据")
        crawler = HotspotCrawler()
        publish_data = crawler.crawl_publish_data()
        
        # 复盘分析
        logger.info("步骤2: 复盘分析")
        analyzer = DataAnalyzer()
        conclusions = analyzer.analyze(publish_data)
        
        # 更新记忆系统
        logger.info("步骤3: 更新记忆系统")
        memory = MemorySystem()
        memory.update(conclusions)
        
        logger.info("========== 复盘分析完成 ==========")
        return conclusions
        
    except Exception as e:
        logger.error(f"复盘分析执行失败: {str(e)}", exc_info=True)
        return None

def main():
    """主函数"""
    logger = init_logging()
    logger.info("音乐爆款智能体启动")
    
    # 创建调度器
    scheduler = Scheduler()
    
    # 每日定时爬取和生成
    scheduler.add_daily_task(DAILY_CRAWL_TIME, daily_workflow)
    
    # 每日定时发布
    scheduler.add_daily_task(DAILY_PUBLISH_TIME, daily_workflow)
    
    # 每日定时分析（24小时后）
    scheduler.add_daily_task(DAILY_ANALYZE_TIME, analyze_publish_data)
    
    # 如果是首次运行，立即执行一次
    logger.info("首次运行，立即执行一次工作流")
    daily_workflow()
    
    # 启动调度循环
    logger.info("启动定时任务调度器")
    while True:
        scheduler.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()