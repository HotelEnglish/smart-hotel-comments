import requests
import random
from fake_useragent import UserAgent
import time
import json
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
        """从多个免费代理源更新代理池"""
        try:
            # 使用多个免费代理API
            apis = [
                "https://proxylist.geonode.com/api/proxy-list?limit=100&page=1&sort_by=lastChecked&protocols=http,https",
                "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
                # 可以添加更多API源
            ]
            
            new_proxies = []
            for api in apis:
                try:
                    response = self.scraper.get(api, timeout=10)
                    if response.status_code == 200:
                        if api.startswith('https://proxylist.geonode.com'):
                            data = response.json()
                            new_proxies.extend([
                                {
                                    'http': f"http://{proxy['ip']}:{proxy['port']}",
                                    'https': f"https://{proxy['ip']}:{proxy['port']}"
                                }
                                for proxy in data['data']
                            ])
                        else:
                            # 处理其他API返回的格式
                            proxies = response.text.strip().split('\n')
                            new_proxies.extend([
                                {
                                    'http': f"http://{proxy}",
                                    'https': f"https://{proxy}"
                                }
                                for proxy in proxies
                            ])
                except Exception as e:
                    logging.error(f"从API获取代理失败: {str(e)}")
                    continue
            
            self.proxies = new_proxies
            self.last_update = time.time()
            logging.info(f"代理池更新成功，当前代理数量: {len(self.proxies)}")
            
        except Exception as e:
            logging.error(f"更新代理池失败: {str(e)}")
    
    def get_proxy(self):
        """获取一个可用的代理"""
        if time.time() - self.last_update > self.update_interval or not self.proxies:
            self.update_proxies()
        
        if not self.proxies:
            return None
            
        proxy = random.choice(self.proxies)
        return proxy
    
    def get_headers(self):
        """获取随机User-Agent"""
        return {
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        } 