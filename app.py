from flask import Flask, render_template, request, jsonify
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import threading
import queue
from proxy_pool import ProxyPool
from hotel_reviews_scraper import CtripScraper, BookingScraper, AgodaScraper
import logging
import os

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

def initialize_driver(proxy_pool):
    """初始化Chrome驱动"""
    chrome_options = Options()
    
    # Vercel环境特定配置
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--single-process')
    chrome_options.add_argument(f'--user-agent={proxy_pool.get_headers()["User-Agent"]}')
    
    # 配置代理
    proxy = proxy_pool.get_proxy()
    seleniumwire_options = {
        'proxy': proxy,
        'verify_ssl': False  # 禁用SSL验证以提高性能
    }
    
    try:
        # 尝试使用 ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(
            service=service,
            options=chrome_options,
            seleniumwire_options=seleniumwire_options
        )
    except Exception as e:
        logging.error(f"使用 ChromeDriverManager 失败: {str(e)}")
        # 降级使用远程 WebDriver
        try:
            driver = webdriver.Remote(
                command_executor='http://localhost:4444/wd/hub',
                options=chrome_options
            )
        except Exception as e:
            logging.error(f"使用远程 WebDriver 失败: {str(e)}")
            raise
    
    return driver

def scraping_worker(keyword, sites, pages_per_site):
    """爬虫工作线程"""
    global scraping_status
    
    try:
        proxy_pool = ProxyPool()
        driver = initialize_driver(proxy_pool)
        
        scrapers = {
            'ctrip': CtripScraper(driver, proxy_pool),
            'booking': BookingScraper(driver, proxy_pool),
            'agoda': AgodaScraper(driver, proxy_pool)
        }
        
        total_reviews = 0
        for site in sites:
            try:
                scraping_status['current_site'] = site
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
        driver.quit()

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

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    # 根据环境变量决定是否开启debug模式
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=debug) 