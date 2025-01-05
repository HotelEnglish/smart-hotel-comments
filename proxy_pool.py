import requests
import random
from fake_useragent import UserAgent
import time
import logging
import cloudscraper

class ProxyPool:
    def __init__(self):
        self.proxies = []
        self.user_agent = UserAgent()
        self.update_interval = 300
        self.last_update = 0
        self.scraper = cloudscraper.create_scraper()
    
    def update_proxies(self):
        """从免费代理API更新代理池"""
        try:
            response = self.scraper.get(
                'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
                timeout=10
            )
            if response.status_code == 200:
                proxies = response.text.strip().split('\n')
                self.proxies = [
                    {
                        'http': f'http://{proxy}',
                        'https': f'http://{proxy}'
                    }
                    for proxy in proxies
                ]
                self.last_update = time.time()
        except Exception as e:
            logging.error(f"更新代理池失败: {str(e)}")
    
    def get_proxy(self):
        """获取一个代理"""
        if time.time() - self.last_update > self.update_interval or not self.proxies:
            self.update_proxies()
        return random.choice(self.proxies) if self.proxies else None
    
    def get_headers(self):
        """获取随机User-Agent"""
        return {
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        } 