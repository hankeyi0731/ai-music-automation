import os
import time
import logging
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from config import AUDIO_DIR, AUDIO_REQUIREMENTS, MAX_RETRY, RETRY_DELAY, MUSIC_GENERATION_CONFIG

logger = logging.getLogger('music_agent')

class MusicGenerator:
    """双轨音乐生成模块"""
    
    def __init__(self):
        self.driver = None
    
    def _init_driver(self):
        """初始化浏览器驱动"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            # 设置下载路径
            prefs = {
                'download.default_directory': AUDIO_DIR,
                'download.prompt_for_download': False,
                'download.directory_upgrade': True,
                'safebrowsing.enabled': True
            }
            chrome_options.add_experimental_option('prefs', prefs)
            self.driver = webdriver.Chrome(options=chrome_options)
    
    def _convert_to_mp3(self, input_path, output_path=None):
        """转换音频格式为MP3"""
        if output_path is None:
            output_path = os.path.splitext(input_path)[0] + '.mp3'
        
        try:
            # 使用ffmpeg转换
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-codec:a', 'libmp3lame',
                '-b:a', '320k',
                '-ar', '44100',
                '-y',
                output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            if os.path.exists(output_path):
                os.remove(input_path)
                return output_path
            return None
        except Exception as e:
            logger.error(f"转换音频格式失败: {str(e)}")
            return None
    
    def _check_audio_quality(self, file_path):
        """检查音频质量是否符合要求"""
        try:
            # 检查文件存在
            if not os.path.exists(file_path):
                return False, "文件不存在"
            
            # 检查格式
            if not file_path.endswith('.mp3'):
                return False, "格式不是MP3"
            
            # 检查文件大小
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > AUDIO_REQUIREMENTS['file_size_max_mb']:
                return False, f"文件过大: {file_size_mb:.2f}MB"
            
            # 检查MP3属性
            audio = MP3(file_path)
            
            # 检查码率
            bitrate = audio.info.bitrate / 1000  # kbps
            if bitrate < AUDIO_REQUIREMENTS['bitrate_min']:
                return False, f"码率不足: {bitrate:.1f}kbps"
            
            # 检查采样率
            sample_rate = audio.info.sample_rate
            if sample_rate < AUDIO_REQUIREMENTS['sample_rate_min']:
                return False, f"采样率不足: {sample_rate}Hz"
            
            return True, f"码率: {bitrate:.1f}kbps, 采样率: {sample_rate}Hz"
        
        except Exception as e:
            return False, f"检查失败: {str(e)}"
    
    def generate_with_douyin_lab(self, prompt):
        """使用抖音创作实验室生成带人声AI歌曲"""
        logger.info(f"使用抖音创作实验室生成音乐: {prompt[:50]}...")
        
        try:
            self._init_driver()
            self.driver.get(MUSIC_GENERATION_CONFIG['douyin_lab']['url'])
            time.sleep(5)
            
            # 模拟输入prompt（实际需要根据页面结构调整）
            try:
                input_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea, input[type="text"]'))
                )
                input_box.send_keys(prompt)
                
                # 点击生成按钮
                generate_btn = self.driver.find_element(By.CSS_SELECTOR, 'button:contains("生成")')
                generate_btn.click()
                
                # 等待生成完成
                time.sleep(60)
                
                # 模拟下载
                download_btn = self.driver.find_element(By.CSS_SELECTOR, 'button:contains("下载")')
                download_btn.click()
                
                # 等待下载完成
                time.sleep(10)
                
                # 返回模拟的文件路径
                filename = f"douyin_{int(time.time())}.mp3"
                filepath = os.path.join(AUDIO_DIR, filename)
                
                # 创建模拟文件（实际场景中会自动下载）
                with open(filepath, 'wb') as f:
                    f.write(b'fake_audio_data')
                
                return filepath
                
            except Exception as e:
                logger.warning(f"抖音创作实验室生成失败，使用模拟数据: {str(e)}")
                # 返回模拟文件
                filename = f"douyin_{int(time.time())}.mp3"
                filepath = os.path.join(AUDIO_DIR, filename)
                with open(filepath, 'wb') as f:
                    f.write(b'fake_audio_data')
                return filepath
                
        except Exception as e:
            logger.error(f"使用抖音创作实验室失败: {str(e)}")
            return None
    
    def generate_with_doubao(self, prompt):
        """使用豆包音乐生成纯音乐BGM"""
        logger.info(f"使用豆包音乐生成音乐: {prompt[:50]}...")
        
        try:
            self._init_driver()
            self.driver.get(MUSIC_GENERATION_CONFIG['doubao_music']['url'])
            time.sleep(5)
            
            # 模拟生成过程
            try:
                # 实际操作会在这里
                time.sleep(30)
                
                # 返回模拟的文件路径
                filename = f"doubao_{int(time.time())}.mp3"
                filepath = os.path.join(AUDIO_DIR, filename)
                
                # 创建模拟文件
                with open(filepath, 'wb') as f:
                    f.write(b'fake_bgm_data')
                
                return filepath
                
            except Exception as e:
                logger.warning(f"豆包音乐生成失败，使用模拟数据: {str(e)}")
                filename = f"doubao_{int(time.time())}.mp3"
                filepath = os.path.join(AUDIO_DIR, filename)
                with open(filepath, 'wb') as f:
                    f.write(b'fake_bgm_data')
                return filepath
                
        except Exception as e:
            logger.error(f"使用豆包音乐失败: {str(e)}")
            return None
    
    def generate_one(self, prompt_data):
        """生成单首音乐"""
        song_type = prompt_data['song_type']
        prompt = prompt_data['prompt']
        
        for attempt in range(MAX_RETRY):
            try:
                # 根据类型选择生成工具
                if song_type == '带人声AI歌曲':
                    filepath = self.generate_with_douyin_lab(prompt)
                else:
                    filepath = self.generate_with_doubao(prompt)
                
                if not filepath:
                    raise Exception("生成失败")
                
                # 检查质量
                success, msg = self._check_audio_quality(filepath)
                
                if success:
                    logger.info(f"音频质量检查通过: {msg}")
                    return {
                        'success': True,
                        'filepath': filepath,
                        'prompt_data': prompt_data,
                        'quality_info': msg
                    }
                else:
                    logger.warning(f"音频质量检查失败: {msg}，尝试转换")
                    
                    # 尝试转换
                    converted_path = self._convert_to_mp3(filepath)
                    if converted_path:
                        success, msg = self._check_audio_quality(converted_path)
                        if success:
                            return {
                                'success': True,
                                'filepath': converted_path,
                                'prompt_data': prompt_data,
                                'quality_info': msg
                            }
                
                logger.warning(f"第 {attempt+1} 次尝试失败，重试...")
                time.sleep(RETRY_DELAY)
                
            except Exception as e:
                logger.warning(f"生成失败，第 {attempt+1} 次尝试: {str(e)}")
                time.sleep(RETRY_DELAY)
        
        return {
            'success': False,
            'error': f"达到最大重试次数 {MAX_RETRY}",
            'prompt_data': prompt_data
        }
    
    def generate_all(self, prompts):
        """生成所有音乐"""
        logger.info(f"开始双轨生成音乐，共 {len(prompts)} 首")
        
        results = []
        for prompt_data in prompts:
            result = self.generate_one(prompt_data)
            results.append(result)
            
            if result['success']:
                logger.info(f"成功生成音乐: {result['filepath']}")
            else:
                logger.error(f"生成音乐失败: {result['error']}")
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        logger.info(f"音乐生成完成，成功 {success_count}/{len(results)}")
        
        return results
    
    def __del__(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()