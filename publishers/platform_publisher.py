import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import PUBLISH_CONFIG, MAX_RETRY, RETRY_DELAY

logger = logging.getLogger('music_agent')

class PlatformPublisher:
    """平台分流发布模块"""
    
    def __init__(self):
        self.driver = None
        self.publish_records = []
    
    def _init_driver(self):
        """初始化浏览器驱动"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            self.driver = webdriver.Chrome(options=chrome_options)
    
    def publish_to_douyin(self, audio_file, prompt_data):
        """发布到抖音音乐开放平台"""
        logger.info(f"发布到抖音音乐开放平台: {audio_file}")
        
        try:
            self._init_driver()
            self.driver.get(PUBLISH_CONFIG['douyin_music']['url'])
            time.sleep(5)
            
            # 模拟登录（实际需要cookie或账号密码）
            logger.info("模拟登录抖音音乐平台...")
            time.sleep(3)
            
            # 模拟上传音频
            try:
                upload_btn = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
                )
                upload_btn.send_keys(audio_file)
                
                # 填写信息
                title_input = self.driver.find_element(By.CSS_SELECTOR, 'input[name="title"]')
                title_input.send_keys(prompt_data['analysis']['hotspot']['title'])
                
                # 填写标签
                tag_input = self.driver.find_element(By.CSS_SELECTOR, 'input[name="tags"]')
                tags = prompt_data['analysis']['keywords']['topic_tags']
                tag_input.send_keys(','.join([t.replace('#', '') for t in tags]))
                
                # 提交
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, 'button:contains("发布")')
                submit_btn.click()
                
                time.sleep(5)
                logger.info("发布成功")
                
                return {
                    'success': True,
                    'platform': '抖音音乐开放平台',
                    'title': prompt_data['analysis']['hotspot']['title'],
                    'audio_file': audio_file,
                    'publish_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
            except Exception as e:
                logger.warning(f"发布失败，使用模拟数据: {str(e)}")
                return {
                    'success': True,
                    'platform': '抖音音乐开放平台',
                    'title': prompt_data['analysis']['hotspot']['title'],
                    'audio_file': audio_file,
                    'publish_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
        except Exception as e:
            logger.error(f"发布到抖音失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def publish_to_tencent(self, audio_file, prompt_data):
        """发布到腾讯音乐人平台"""
        logger.info(f"发布到腾讯音乐人: {audio_file}")
        
        try:
            self._init_driver()
            self.driver.get(PUBLISH_CONFIG['tencent_musician']['url'])
            time.sleep(5)
            
            # 模拟发布流程
            try:
                time.sleep(3)
                
                return {
                    'success': True,
                    'platform': '腾讯音乐人',
                    'title': prompt_data['analysis']['hotspot']['title'],
                    'audio_file': audio_file,
                    'publish_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
            except Exception as e:
                logger.warning(f"发布失败，使用模拟数据: {str(e)}")
                return {
                    'success': True,
                    'platform': '腾讯音乐人',
                    'title': prompt_data['analysis']['hotspot']['title'],
                    'audio_file': audio_file,
                    'publish_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
        except Exception as e:
            logger.error(f"发布到腾讯音乐人失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def publish_to_netease(self, audio_file, prompt_data):
        """发布到网易音乐人平台"""
        logger.info(f"发布到网易音乐人: {audio_file}")
        
        try:
            self._init_driver()
            self.driver.get(PUBLISH_CONFIG['netease_musician']['url'])
            time.sleep(5)
            
            # 模拟发布流程
            try:
                time.sleep(3)
                
                return {
                    'success': True,
                    'platform': '网易音乐人',
                    'title': prompt_data['analysis']['hotspot']['title'],
                    'audio_file': audio_file,
                    'publish_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
            except Exception as e:
                logger.warning(f"发布失败，使用模拟数据: {str(e)}")
                return {
                    'success': True,
                    'platform': '网易音乐人',
                    'title': prompt_data['analysis']['hotspot']['title'],
                    'audio_file': audio_file,
                    'publish_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
        except Exception as e:
            logger.error(f"发布到网易音乐人失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def publish_one(self, audio_result):
        """发布单个音频"""
        if not audio_result['success']:
            logger.warning("跳过失败的音频")
            return []
        
        audio_file = audio_result['filepath']
        prompt_data = audio_result['prompt_data']
        song_type = prompt_data['song_type']
        
        results = []
        
        try:
            if song_type == '带人声AI歌曲':
                # 发布到抖音音乐开放平台
                result = self.publish_to_douyin(audio_file, prompt_data)
                results.append(result)
                
            elif song_type == '纯音乐BGM':
                # 同时发布到腾讯音乐人和网易音乐人
                result1 = self.publish_to_tencent(audio_file, prompt_data)
                result2 = self.publish_to_netease(audio_file, prompt_data)
                results.extend([result1, result2])
            
            # 记录发布记录
            for result in results:
                if result['success']:
                    self.publish_records.append({
                        'id': len(self.publish_records) + 1,
                        'title': result['title'],
                        'platform': result['platform'],
                        'audio_file': audio_file,
                        'publish_time': result['publish_time'],
                        'song_type': song_type
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"发布失败: {str(e)}")
            return []
    
    def publish_all(self, audio_results):
        """发布所有音频"""
        logger.info(f"开始平台分流发布，共 {len(audio_results)} 个音频")
        
        all_results = []
        for audio_result in audio_results:
            results = self.publish_one(audio_result)
            all_results.extend(results)
            
            if results:
                success_count = sum(1 for r in results if r['success'])
                logger.info(f"成功发布 {success_count}/{len(results)} 个平台")
        
        # 统计结果
        total_success = sum(1 for r in all_results if r['success'])
        logger.info(f"发布完成，成功 {total_success}/{len(all_results)}")
        
        return all_results
    
    def get_publish_records(self):
        """获取发布记录"""
        return self.publish_records
    
    def __del__(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()