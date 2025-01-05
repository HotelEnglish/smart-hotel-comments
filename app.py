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
        start_time = time.time()
        max_search_time = 300  # 5分钟超时
        
        search_status['platform_status'][platform] = {
            'status': 'searching',
            'review_count': 0
        }
        
        # 分批次搜索，每批次检查是否需要停止
        batch_size = 3
        total_batches = (target_count + batch_size - 1) // batch_size
        
        for batch in range(total_batches):
            # 检查停止条件
            if search_status['should_stop']:
                search_status['platform_status'][platform]['status'] = 'stopped'
                logging.info(f"{platform} 搜索已停止")
                return
            
            # 检查超时
            if time.time() - start_time > max_search_time:
                search_status['platform_status'][platform]['status'] = 'timeout'
                logging.info(f"{platform} 搜索超时")
                return
            
            # 检查是否达到目标数量
            if search_status['current_count'] >= target_count:
                search_status['platform_status'][platform]['status'] = 'completed'
                return
            
            # 模拟获取一批评论
            new_reviews = [
                {
                    'hotel_name': f'测试酒店 {batch * batch_size + i}',
                    'content': f'这是一条来自{platform}的测试评论 {batch * batch_size + i}',
                    'score': 4.5,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'timestamp': datetime.now().isoformat()
                }
                for i in range(batch_size)
            ]
            
            # 过滤日期范围
            if date_range['start'] and date_range['end']:
                new_reviews = [
                    review for review in new_reviews
                    if date_range['start'] <= review['date'] <= date_range['end']
                ]
            
            # 更新结果
            if platform not in search_status['results']:
                search_status['results'][platform] = []
            
            search_status['results'][platform].extend(new_reviews)
            search_status['current_count'] += len(new_reviews)
            
            # 更新进度
            search_status['platform_status'][platform].update({
                'status': 'searching',
                'review_count': len(search_status['results'][platform]),
                'progress': min(100, (batch + 1) * 100 // total_batches)
            })
            
            time.sleep(1)  # 模拟搜索延迟
        
        search_status['platform_status'][platform]['status'] = 'completed'
        
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

@app.route('/export', methods=['POST'])
def export_results():
    try:
        data = request.get_json()
        format_type = data.get('format', 'txt')
        
        if format_type not in ['txt', 'markdown']:
            return jsonify({'error': '不支持的导出格式'}), 400
        
        content = ''
        if format_type == 'txt':
            for platform, reviews in search_status['results'].items():
                content += f"\n=== {platform} ===\n\n"
                for review in reviews:
                    content += f"酒店：{review['hotel_name']}\n"
                    content += f"评分：{review['score']}\n"
                    content += f"日期：{review['date']}\n"
                    content += f"评论：{review['content']}\n"
                    content += "-" * 50 + "\n"
        else:  # markdown
            content = "# 酒店评论搜索结果\n\n"
            for platform, reviews in search_status['results'].items():
                content += f"## {platform}\n\n"
                for review in reviews:
                    content += f"### {review['hotel_name']}\n\n"
                    content += f"- 评分：{review['score']}\n"
                    content += f"- 日期：{review['date']}\n"
                    content += f"- 评论：{review['content']}\n\n"
                    content += "---\n\n"
        
        return jsonify({
            'status': 'success',
            'content': content
        })
        
    except Exception as e:
        logging.error(f"导出结果失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 