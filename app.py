from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import threading
import queue
from proxy_pool import ProxyPool
import logging
import os
import json
from datetime import datetime

app = Flask(__name__)

# 全局变量
scraping_status = {
    'is_running': False,
    'progress': 0,
    'total_reviews': 0,
    'current_site': '',
    'error': None
}

result_queue = queue.Queue()

class SimpleScraper:
    def __init__(self, proxy_pool):
        self.proxy_pool = proxy_pool
        self.session = requests.Session()
    
    def get_page(self, url):
        headers = self.proxy_pool.get_headers()
        proxy = self.proxy_pool.get_proxy()
        try:
            response = self.session.get(
                url, 
                headers=headers, 
                proxies=proxy,
                timeout=10
            )
            return response.text
        except Exception as e:
            logging.error(f"获取页面失败: {str(e)}")
            return None

class CtripScraper(SimpleScraper):
    def scrape(self, keyword, pages=50):
        reviews = []
        try:
            # 使用携程API接口
            api_url = f"https://m.ctrip.com/restapi/soa2/16709/json/GetSearchResult?keyword={keyword}"
            data = self.session.post(api_url, headers=self.proxy_pool.get_headers()).json()
            
            # 解析酒店列表
            if 'hotels' in data:
                for hotel in data['hotels'][:pages]:
                    hotel_reviews = self._get_hotel_reviews(hotel['hotelId'])
                    reviews.extend(hotel_reviews)
            
            return reviews
        except Exception as e:
            logging.error(f"爬取携程失败: {str(e)}")
            return reviews
    
    def _get_hotel_reviews(self, hotel_id):
        reviews = []
        try:
            api_url = f"https://m.ctrip.com/restapi/soa2/16765/json/GetReviewList?hotelId={hotel_id}"
            data = self.session.post(api_url, headers=self.proxy_pool.get_headers()).json()
            
            if 'reviews' in data:
                for review in data['reviews']:
                    reviews.append({
                        'hotel_name': data.get('hotelName', ''),
                        'content': review.get('content', ''),
                        'date': review.get('reviewDate', '')
                    })
        except Exception as e:
            logging.error(f"获取酒店评论失败: {str(e)}")
        return reviews

def scraping_worker(keyword, sites, pages_per_site):
    """爬虫工作线程"""
    global scraping_status
    
    try:
        proxy_pool = ProxyPool()
        
        scrapers = {
            'ctrip': CtripScraper(proxy_pool),
            # 其他网站的爬虫实现...
        }
        
        total_reviews = 0
        for site in sites:
            try:
                scraping_status['current_site'] = site
                if site in scrapers:
                    scraper = scrapers[site]
                    reviews = scraper.scrape(keyword, pages_per_site)
                    total_reviews += len(reviews)
                    result_queue.put((site, reviews))
                scraping_status['progress'] = (sites.index(site) + 1) / len(sites) * 100
                
            except Exception as e:
                logging.error(f"爬取{site}时出错: {str(e)}")
                scraping_status['error'] = str(e)
                
        scraping_status['total_reviews'] = total_reviews
        
    except Exception as e:
        scraping_status['error'] = str(e)
    finally:
        scraping_status['is_running'] = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    if scraping_status['is_running']:
        return jsonify({'error': '爬虫正在运行中'})
    
    data = request.json
    keyword = data.get('keyword', '')
    sites = data.get('sites', [])
    pages_per_site = data.get('pages_per_site', 50)
    
    if not keyword or not sites:
        return jsonify({'error': '参数错误'})
    
    # 重置状态
    scraping_status.update({
        'is_running': True,
        'progress': 0,
        'total_reviews': 0,
        'current_site': '',
        'error': None
    })
    
    # 启动爬虫线程
    thread = threading.Thread(
        target=scraping_worker,
        args=(keyword, sites, pages_per_site)
    )
    thread.start()
    
    return jsonify({'message': '爬虫已启动'})

@app.route('/status')
def get_status():
    return jsonify(scraping_status)

@app.route('/results')
def get_results():
    results = {}
    while not result_queue.empty():
        site, reviews = result_queue.get()
        results[site] = reviews
    return jsonify(results)

@app.errorhandler(Exception)
def handle_error(error):
    message = str(error)
    status_code = 500
    if hasattr(error, 'code'):
        status_code = error.code
    response = {
        'error': {
            'message': message,
            'status_code': status_code
        }
    }
    return jsonify(response), status_code

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=debug) 