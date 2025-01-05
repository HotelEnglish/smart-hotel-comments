from abc import ABC, abstractmethod
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import random
import time

class BaseScraper(ABC):
    def __init__(self, driver, proxy_pool):
        self.driver = driver
        self.proxy_pool = proxy_pool
        self.wait = WebDriverWait(driver, 10)
        
    @abstractmethod
    def scrape(self, keyword, pages):
        pass
    
    def random_sleep(self, min_seconds=1, max_seconds=3):
        """随机等待时间"""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def safe_find_element(self, by, value, timeout=10):
        """安全地查找元素"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None
    
    def handle_captcha(self):
        """处理验证码（需要根据具体网站实现）"""
        pass 