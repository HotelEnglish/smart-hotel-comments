from flask import Flask, render_template, request, jsonify
import logging
import os

app = Flask(__name__)

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

@app.route('/api/test', methods=['GET'])
def test_api():
    """测试API是否正常工作"""
    return jsonify({
        'status': 'success',
        'message': 'API is working'
    })

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        keyword = data.get('keyword')
        if not keyword:
            return jsonify({'error': '关键词不能为空'}), 400
            
        return jsonify({
            'status': 'success',
            'message': '请求已接收',
            'data': {
                'keyword': keyword
            }
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