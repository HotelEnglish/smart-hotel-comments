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
    'start_time': None,
    'should_stop': False,  # 控制搜索停止
    'target_count': 0,     # 目标评论数量
    'current_count': 0,    # 当前评论数量
    'date_range': {        # 日期范围
        'start': None,
        'end': None
    }
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

def search_platform(platform, keyword, target_count, date_range):
    """在特定平台上搜索"""
    try:
        search_status['platform_status'][platform] = {
            'status': 'searching',
            'review_count': 0
        }
        
        start_time = time.time()
        max_search_time = 300  # 最大搜索时间5分钟
        
        # 模拟搜索过程
        for i in range(10):  # 分批次搜索
            if search_status['should_stop'] or \
               search_status['current_count'] >= target_count or \
               time.time() - start_time > max_search_time:
                break
                
            # 模拟找到一些评论
            new_reviews = [
                {
                    'hotel_name': f'测试酒店 {i}',
                    'content': f'这是一条来自{platform}的测试评论 {i}',
                    'score': 4.5,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'timestamp': datetime.now().isoformat()  # 用于实时显示
                }
                for i in range(3)
            ]
            
            # 过滤日期范围
            if date_range['start'] and date_range['end']:
                new_reviews = [
                    review for review in new_reviews
                    if date_range['start'] <= review['date'] <= date_range['end']
                ]
            
            if platform not in search_status['results']:
                search_status['results'][platform] = []
            
            search_status['results'][platform].extend(new_reviews)
            search_status['current_count'] += len(new_reviews)
            search_status['platform_status'][platform] = {
                'status': 'searching',
                'review_count': len(search_status['results'][platform])
            }
            
            time.sleep(1)  # 模拟搜索延迟
        
        search_status['platform_status'][platform] = {
            'status': 'completed',
            'review_count': len(search_status['results'][platform])
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
        target_count = int(data.get('target_count', 100))  # 默认100条
        date_range = {
            'start': data.get('start_date'),
            'end': data.get('end_date')
        }
        
        if not keyword:
            return jsonify({'error': '关键词不能为空'}), 400
            
        if not platforms:
            return jsonify({'error': '请选择至少一个平台'}), 400
        
        # 重置搜索状态
        search_status.update({
            'is_searching': True,
            'should_stop': False,
            'platform_status': {},
            'results': {},
            'start_time': datetime.now().isoformat(),
            'target_count': target_count,
            'current_count': 0,
            'date_range': date_range
        })
        
        # 为每个平台启动搜索线程
        for platform in platforms:
            Thread(
                target=search_platform,
                args=(platform, keyword, target_count, date_range),
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

@app.route('/stop_scraping', methods=['POST'])
def stop_scraping():
    search_status['should_stop'] = True
    return jsonify({
        'status': 'success',
        'message': '正在停止搜索...'
    })

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