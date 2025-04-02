# Scrapy settings for PaperAssistant project

BOT_NAME = 'PaperAssistant'

SPIDER_MODULES = ['app.spiders']
NEWSPIDER_MODULE = 'app.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'PaperAssistant (+http://www.yourdomain.com)'
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performing to the same domain
CONCURRENT_REQUESTS = 2

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 1

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
   'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': 100,
}

# Configure item pipelines
ITEM_PIPELINES = {
   'app.spiders.pipelines.PaperPipeline': 300,
}

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
# 移除 TWISTED_REACTOR 设置，让 Scrapy 自动选择合适的反应器
# TWISTED_REACTOR = 'twisted.internet.selectreactor.SelectReactor'
FEED_EXPORT_ENCODING = 'utf-8'

# 论文下载相关配置
PAPERS_FOLDER = 'papers'  # 论文下载保存路径
DOWNLOAD_MAX_WORKERS = 2  # 下载线程池大小
DOWNLOAD_CHUNK_SIZE = 8192  # 下载块大小
DOWNLOAD_RETRY_TIMES = 3  # 下载重试次数
DOWNLOAD_RETRY_DELAY = 5  # 重试等待时间(秒)
DOWNLOAD_DELAY = 1  # 每个下载任务之间的延迟时间(秒)