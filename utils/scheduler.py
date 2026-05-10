import schedule
import time
import logging

logger = logging.getLogger('music_agent')

class Scheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self.jobs = []
    
    def add_daily_task(self, time_str, task_func):
        """添加每日定时任务"""
        job = schedule.every().day.at(time_str).do(task_func)
        self.jobs.append(job)
        logger.info(f"已添加定时任务: 每天 {time_str} 执行 {task_func.__name__}")
        return job
    
    def add_hourly_task(self, task_func):
        """添加每小时任务"""
        job = schedule.every().hour.do(task_func)
        self.jobs.append(job)
        logger.info(f"已添加定时任务: 每小时执行 {task_func.__name__}")
        return job
    
    def add_minutely_task(self, task_func):
        """添加每分钟任务"""
        job = schedule.every().minute.do(task_func)
        self.jobs.append(job)
        logger.info(f"已添加定时任务: 每分钟执行 {task_func.__name__}")
        return job
    
    def add_custom_task(self, interval, unit, task_func):
        """添加自定义间隔任务"""
        job = None
        if unit == 'seconds':
            job = schedule.every(interval).seconds.do(task_func)
        elif unit == 'minutes':
            job = schedule.every(interval).minutes.do(task_func)
        elif unit == 'hours':
            job = schedule.every(interval).hours.do(task_func)
        elif unit == 'days':
            job = schedule.every(interval).days.do(task_func)
        
        if job:
            self.jobs.append(job)
            logger.info(f"已添加定时任务: 每{interval}{unit}执行 {task_func.__name__}")
        
        return job
    
    def run_pending(self):
        """运行待执行的任务"""
        schedule.run_pending()
    
    def cancel_all(self):
        """取消所有任务"""
        schedule.clear()
        self.jobs = []
        logger.info("所有定时任务已取消")
    
    def list_jobs(self):
        """列出所有任务"""
        return schedule.get_jobs()
    
    def run_once(self, task_func):
        """立即执行一次任务"""
        logger.info(f"立即执行任务: {task_func.__name__}")
        return task_func()
    
    def run_until_complete(self):
        """持续运行直到手动停止"""
        logger.info("调度器开始持续运行...")
        while True:
            self.run_pending()
            time.sleep(1)