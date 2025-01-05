from flask import Flask, render_template, request, jsonify
import logging
import os
from threading import Thread
import time
from datetime import datetime

app = Flask(__name__)

# 全局变量存储搜索状态
search_status = {
    'is_searching': False,
    'platform_status': {},
    'results': {},
    'start_time': None
}

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logging.error(f"渲染首页失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test')
def test_api():
    """测试API是否正常工作"""
    return jsonify({
        'status': 'success',
        'message': 'API is working'
    })

@app.route('/search_status')
def get_search_status():
    """获取搜索状态"""
    if not search_status['is_searching']:
        return jsonify({
            'status': 'completed',
            'results': search_status['results']
        })
    
    return jsonify({
        'status': 'in_progress',
        'platform_status': search_status['platform_status'],
        'start_time': search_status['start_time']
    })

def search_platform(platform, keyword):
    """模拟在特定平台上搜索"""
    try:
        search_status['platform_status'][platform] = {
            'status': 'searching',
            'review_count': 0
        }
        
        # 模拟搜索过程
        time.sleep(5)  # 实际项目中替换为真实的爬取逻辑
        
        # 模拟找到一些评论
        reviews = [
            {
                'hotel_name': f'测试酒店 {i}',
                'content': f'这是一条来自{platform}的测试评论 {i}',
                'score': 4.5,
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            for i in range(3)
        ]
        
        search_status['results'][platform] = reviews
        search_status['platform_status'][platform] = {
            'status': 'completed',
            'review_count': len(reviews)
        }
        
    except Exception as e:
        logging.error(f"{platform} 搜索失败: {str(e)}")
        search_status['platform_status'][platform] = {
            'status': 'error',
            'error': str(e)
        }

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        keyword = data.get('keyword')
        platforms = data.get('platforms', [])
        
        if not keyword:
            return jsonify({'error': '关键词不能为空'}), 400
            
        if not platforms:
            return jsonify({'error': '请选择至少一个平台'}), 400
        
        # 重置搜索状态
        search_status.update({
            'is_searching': True,
            'platform_status': {},
            'results': {},
            'start_time': datetime.now().isoformat()
        })
        
        # 为每个平台启动搜索线程
        for platform in platforms:
            Thread(
                target=search_platform,
                args=(platform, keyword),
                daemon=True
            ).start()
        
        return jsonify({
            'status': 'success',
            'message': '搜索已开始',
            'platforms': platforms
        })
        
    except Exception as e:
        logging.error(f"处理爬虫请求时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"未处理的异常: {str(e)}")
    return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 