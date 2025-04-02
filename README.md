# PaperSpider 项目文档

## 项目概述

PaperSpider 是一个用于自动爬取和下载 arXiv 学术论文的爬虫系统。该项目可以根据指定的学术分类（如 cs.AI、cs.CL 等）定期抓取最新发布的论文信息，包括标题、作者、摘要、PDF链接等，并将这些信息存储到数据库中。同时，系统还提供了自动下载论文PDF文件的功能。

## 功能特点

- **自动爬取论文**：根据指定的 arXiv 分类自动爬取最新论文信息
- **数据存储**：将爬取的论文信息存储到 MySQL 数据库中
- **自动下载**：支持自动下载论文的 PDF 文件并按日期归档
- **定时任务**：通过 Celery 支持定时爬取任务
- **并发控制**：内置请求频率和并发数限制，避免对 arXiv 服务器造成过大压力
- **错误处理**：完善的错误处理和重试机制

## 技术架构

### 核心组件

- **Scrapy**：用于构建爬虫框架
- **SQLAlchemy**：ORM 框架，用于数据库操作
- **Celery**：分布式任务队列，用于管理定时任务
- **Redis**：作为 Celery 的消息代理
- **MySQL**：存储爬取的论文数据

### 项目结构

```
PaperSpider/
├── app/                    # 主应用目录
│   ├── __init__.py
│   ├── models/             # 数据模型
│   │   └── paper_download.py
│   ├── settings.py         # Scrapy 设置
│   ├── spiders/            # 爬虫目录
│   │   ├── __init__.py
│   │   ├── arxiv_spider.py # arXiv 爬虫
│   │   ├── items.py        # 数据项定义
│   │   └── pipelines.py    # 数据处理管道
│   └── utils/              # 工具类
│       ├── db_utils.py     # 数据库工具
│       └── downloader.py   # 论文下载器
├── papers/                 # 下载的论文存储目录
├── .env                    # 环境变量配置
├── requirements.txt        # 项目依赖
├── run_spider.py           # 爬虫启动脚本
├── scrapy.cfg              # Scrapy 配置
└── tasks.py                # Celery 任务定义
```

## 数据模型

### Paper 模型

存储爬取的论文信息：

- `id`: 主键
- `arxiv_id`: arXiv 论文 ID
- `title`: 论文标题
- `authors`: 作者列表 (JSON 格式)
- `institutions`: 机构列表 (JSON 格式)
- `abstract`: 论文摘要
- `pdf_url`: PDF 下载链接
- `published_date`: 发布日期
- `categories`: 论文分类
- `vector_id`: 向量 ID (用于向量检索)
- `created_at`: 创建时间
- `updated_at`: 更新时间

### PaperDownload 模型

存储论文下载状态：

- `id`: 主键
- `paper_id`: 关联的论文 ID
- `download_status`: 下载状态 (pending, downloading, completed, failed)
- `download_progress`: 下载进度
- `download_path`: 下载路径
- `download_error`: 错误信息
- `created_at`: 创建时间
- `updated_at`: 更新时间

## 环境配置

### 依赖安装

```bash
pip install -r requirements.txt
```

### 数据库配置

1. 创建 MySQL 数据库

```sql
CREATE DATABASE paper_assistant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. 配置 `.env` 文件

```
# 数据库配置
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=paper_assistant

# Scrapy配置
BOT_NAME=PaperAssistant
SPIDER_MODULES=['app.spiders']
NEWSPIDER_MODULE='app.spiders'

# Celery配置
CELERY_BROKER_URL='redis://localhost:6379/0'
CELERY_RESULT_BACKEND='redis://localhost:6379/0'
```

## 部署启动方式

### 直接运行爬虫

```bash
python run_spider.py
```

这将启动爬虫，根据 `run_spider.py` 中的配置爬取指定分类的论文。默认爬取 cs.CL 分类的最近 1 天发布的论文。

### 自定义爬虫参数

可以修改 `run_spider.py` 中的参数来自定义爬取行为：

```python
# 修改爬取的分类和时间范围
process.crawl('arxiv', categories='cs.AI,cs.CL', days_back=3)
```

### 使用 Celery 定时任务

1. 启动 Redis 服务

```bash
redis-server
```

2. 启动 Celery Worker

```bash
celery -A tasks worker --loglevel=info
```

3. 启动 Celery Beat (定时任务调度器)

```bash
celery -A tasks beat --loglevel=info
```

## 注意事项

1. 请遵守 arXiv 的使用政策，避免频繁请求对服务器造成压力
2. 默认配置已经设置了合理的请求频率限制和并发数
3. 下载的论文 PDF 文件会按日期存储在 `papers/` 目录下
4. 确保系统有足够的存储空间用于保存论文文件

## 扩展功能

- 可以通过修改 `arxiv_spider.py` 来爬取更多的论文信息
- 可以通过修改 `downloader.py` 来自定义下载行为
- 可以通过修改 `tasks.py` 来设置不同的定时任务