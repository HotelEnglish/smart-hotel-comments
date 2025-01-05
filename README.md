# 智慧酒店评论爬虫系统

这是一个基于Flask的智慧酒店评论爬虫系统，可以自动收集来自携程、Booking.com和Agoda等网站的酒店评论。该系统提供了一个友好的Web界面，支持多站点爬取，并具有代理池和反爬虫机制。

## 功能特点

- 🌐 支持多个订房网站（携程、Booking.com、Agoda）
- 🔄 自动更新的代理池系统
- 🚀 异步爬取机制
- 📊 实时进度显示
- 🛡️ 内置反爬虫措施
- 💻 友好的Web操作界面
- ☁️ 支持Vercel部署

## 在线演示

[在线演示地址](https://your-demo-url.vercel.app)

## 本地开发

### 环境要求

- Python 3.9+
- Chrome浏览器
- Git

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/your-username/hotel-reviews-scraper.git
cd hotel-reviews-scraper
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 运行项目
```bash
python app.py
```

5. 访问网址
```
http://localhost:5000
```

### 配置说明

- `app.py`: 主应用程序文件
- `proxy_pool.py`: 代理池管理
- `hotel_reviews_scraper.py`: 爬虫核心逻辑
- `templates/index.html`: Web界面模板

## Vercel部署

1. 安装Vercel CLI
```bash
npm install -g vercel
```

2. 登录Vercel
```bash
vercel login
```

3. 部署项目
```bash
vercel
```

## 使用说明

1. 打开Web界面
2. 输入搜索关键词（如"智慧酒店"）
3. 选择要爬取的网站
4. 设置每个网站的爬取页数
5. 点击"开始爬取"
6. 等待爬取完成，查看结果

## 注意事项

- 请遵守目标网站的robots.txt规则
- 建议适当控制爬取频率
- 部分网站可能需要登录才能访问
- 免费代理可能不够稳定，建议适时更换
- Vercel环境下有一些限制（如执行时间限制）

## 项目结构

```
hotel-reviews-scraper/
├── app.py              # Flask应用主文件
├── proxy_pool.py       # 代理池管理
├── scraper_base.py     # 爬虫基类
├── hotel_reviews_scraper.py  # 爬虫实现
├── wsgi.py            # WSGI入口
├── requirements.txt    # 项目依赖
├── runtime.txt        # Python版本声明
├── vercel.json        # Vercel配置
├── .gitignore        # Git忽略文件
└── templates/         # 模板文件
    └── index.html    # Web界面
```

## 开发计划

- [ ] 添加更多网站支持
- [ ] 优化代理池性能
- [ ] 添加数据导出功能
- [ ] 实现评论情感分析
- [ ] 添加用户认证系统

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 许可证

[MIT License](LICENSE)

## 联系方式

如有问题或建议，请提交 [Issue](https://github.com/your-username/hotel-reviews-scraper/issues)

## 致谢

- [Flask](https://flask.palletsprojects.com/)
- [Selenium](https://www.selenium.dev/)
- [Vercel](https://vercel.com/)

