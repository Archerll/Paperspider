import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from app.utils.db_utils import db_manager

def run_spider():
    # 确保数据库表已创建
    db_manager.create_tables()
    
    # 获取Scrapy设置
    settings = get_project_settings()
    
    # 创建爬虫进程
    process = CrawlerProcess(settings)
    
    # 添加爬虫cs.AI,
    process.crawl('arxiv', categories='cs.CL', days_back=1)
    
    # 启动爬虫
    process.start()

if __name__ == "__main__":
    run_spider()