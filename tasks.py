from celery import shared_task
from datetime import datetime
from spiders.arxiv_spider import ArxivSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

@shared_task
def crawl_arxiv_papers():
    """启动arXiv论文爬虫的Celery任务"""
    try:
        process = CrawlerProcess(get_project_settings())
        process.crawl(ArxivSpider)
        process.start()
        return {'status': 'success', 'timestamp': datetime.now().isoformat()}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'timestamp': datetime.now().isoformat()}