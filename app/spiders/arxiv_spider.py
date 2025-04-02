import scrapy
import re
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode
from ..utils.db_utils import db_manager, Paper
from .items import PaperItem

class ArxivSpider(scrapy.Spider):
    name = 'arxiv'
    allowed_domains = ['arxiv.org']
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS': 2,  # 限制并发请求数
        'DOWNLOAD_DELAY': 1,       # 下载延迟，避免请求过于频繁
        'LOG_LEVEL': 'DEBUG',      # 设置日志级别为DEBUG
    }
    
    def __init__(self, categories='cs.AI,cs.CL', days_back=1, *args, **kwargs):
        super(ArxivSpider, self).__init__(*args, **kwargs)
        self.categories = categories.split(',')
        self.days_back = int(days_back)
        # 创建数据库会话
        self.db_session = db_manager.get_session()
        # 用于记录新爬取的论文ID
        self.new_paper_ids = []
        self.logger.info(f"初始化爬虫: 分类={self.categories}, 天数={self.days_back}")
    
    def closed(self, reason):
        """爬虫关闭时启动论文下载并关闭数据库会话"""
        try:
            # 获取今天的日期
            today = datetime.utcnow().date()
            # 获取今天发布的所有论文
            papers = self.db_session.query(Paper).filter(
                Paper.published_date >= today,
                Paper.published_date < today + timedelta(days=1)
            ).all()
            
            if papers:
                # 启动下载任务
                from ..utils.downloader import paper_downloader
                paper_downloader.download_papers(papers)
                self.logger.info(f"已启动{len(papers)}篇今日发布的新论文的下载任务")
            else:
                self.logger.info("今日没有新发布的论文")
        except Exception as e:
            self.logger.error(f"获取今日论文时出错: {str(e)}")
        finally:
            # 关闭数据库会话
            if hasattr(self, 'db_session'):
                self.db_session.close()
                self.logger.info("数据库会话已关闭")
    
    def start_requests(self):
        # 为每个分类创建请求
        for category in self.categories:
            # 使用网站列表页面而不是API
            url = f'https://arxiv.org/list/{category}/recent?skip=0&show=250'
            self.logger.info(f"开始请求: {url}")
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={'category': category},
                errback=self.errback_httpbin
            )
    
    def errback_httpbin(self, failure):
        """处理请求错误"""
        self.logger.error(f"请求失败: {failure}")
    
    def parse(self, response):
        self.logger.info(f"解析页面: {response.url}")
        
        # 查找包含论文列表的主要容器
        articles_containers = response.css('dl#articles')
        if not articles_containers:
            self.logger.error("未找到论文列表容器 (dl#articles)")
            return
        
        articles_container = articles_containers[0]
        
        if not articles_container:
            self.logger.error("未找到论文列表容器 (dl#articles)")
            return
        
        # 从标题中提取日期和总条目数
        date_entries_info = response.xpath('//h3[contains(text(), "entries")]/text()').get('')
        self.logger.debug(f"日期条目信息: {date_entries_info}")
        
        current_date = None
        total_entries = 0
        
        if date_entries_info:
            # 提取日期
            date_part = date_entries_info.split('(')[0].strip()
            try:
                # 将解析的日期转换为UTC时间
                current_date = datetime.strptime(date_part, '%a, %d %b %Y').replace(hour=0, minute=0, second=0)
                self.logger.debug(f"提取的日期: {current_date}")
            except ValueError as e:
                self.logger.error(f"日期解析错误: {e}")
                current_date = datetime.utcnow()
                
            # 提取总条目数
            try:
                if 'showing first' in date_entries_info:
                    entries_part = date_entries_info.split('showing first')[1]
                    if 'of' in entries_part:
                        total_entries = int(entries_part.split('of')[1].split('entries')[0].strip())
                        self.logger.debug(f"总条目数: {total_entries}")
            except (ValueError, IndexError) as e:
                self.logger.error(f"提取总条目数错误: {e}")
                total_entries = 0
        
        # 获取所有dt和dd标签对
        dt_tags = articles_container.css('dt')
        dd_tags = articles_container.css('dd')
        
        self.logger.info(f"找到 {len(dt_tags)} 个dt标签和 {len(dd_tags)} 个dd标签")
        
        # 确保dt和dd标签数量匹配
        if len(dt_tags) != len(dd_tags):
            self.logger.warning(f"dt标签数量({len(dt_tags)})与dd标签数量({len(dd_tags)})不匹配")
        
        # 处理每对dt和dd标签
        for i, (dt, dd) in enumerate(zip(dt_tags, dd_tags)):
            try:
                # 从dt标签中提取论文ID
                arxiv_id_link = dt.css('a[href*="/abs/"]::attr(href)').get('')
                if not arxiv_id_link:
                    self.logger.warning(f"条目 {i+1} 没有找到arxiv_id链接")
                    continue
                    
                # 从链接中提取ID
                arxiv_id = arxiv_id_link.split('/abs/')[1]
                if not arxiv_id:
                    self.logger.warning(f"条目 {i+1} 无法从链接提取arxiv_id")
                    continue
                
                self.logger.debug(f"处理论文 {i+1}/{len(dt_tags)}: {arxiv_id}")
                    
                # 检查论文是否已存在
                if not self._is_paper_exists(arxiv_id):
                    item = PaperItem()
                    item['arxiv_id'] = arxiv_id
                    
                    # 获取标题 - 从dt标签中的meta div获取
                    meta_div = dd.css('div.meta')
                    title_element = meta_div.css('div.list-title::text').getall()
                    title = ''.join(title_element).replace('Title:', '').strip()
                    item['title'] = title
                    
                    # 获取作者 - 从meta div中的list-authors获取
                    authors_element = meta_div.css('div.list-authors a::text').getall()
                    item['authors'] = [author.strip() for author in authors_element]
                    
                    # 机构信息在列表页面不可用
                    item['institutions'] = []
                    
                    # 获取摘要 - 从dd标签中获取
                    abstract = dd.css('p.mathjax::text').get('').strip()
                    item['abstract'] = abstract
                    
                    # PDF链接
                    item['pdf_url'] = f'https://arxiv.org/pdf/{arxiv_id}.pdf'
                    
                    # 使用从页面标题提取的日期
                    item['published_date'] = current_date if current_date else datetime.utcnow()
                    
                    categories = []
                    # 获取分类 - 从meta div中的list-subjects获取
                    prime_categories = meta_div.css('div.list-subjects span.primary-subject::text').getall()
                    if prime_categories:
                        categories.extend([cat.strip() for cat in prime_categories if cat.strip()])
                    
                    other_categories_text = meta_div.css('div.list-subjects::text').getall()
                    if other_categories_text:
                        other_cats = other_categories_text[0].strip().split(';')
                        if len(other_cats) > 1:  # 确保有分号分隔的内容
                            categories.extend([cat.strip() for cat in other_cats[1:] if cat.strip()])
                    
                    item['categories'] = categories
                    
                    self.logger.debug(f"提取论文: {arxiv_id}, 标题: {title[:30]}...")
                    # 记录新爬取的论文ID
                    self.new_paper_ids.append(arxiv_id)
                    yield item
                else:
                    self.logger.debug(f"论文已存在: {arxiv_id}")
            except Exception as e:
                self.logger.error(f"处理条目 {i+1} 时出错: {str(e)}")
        
        # 如果有更多页面需要抓取，生成下一页请求
        if total_entries > 0:
            current_skip = 0
            match = re.search(r'skip=(\d+)', response.url)
            if match:
                current_skip = int(match.group(1))
            
            # 每页显示条数，通常是50
            items_per_page = 250
            next_skip = current_skip + items_per_page
            
            # 如果还有更多条目需要抓取
            if next_skip < total_entries:
                category = response.meta.get('category')
                next_url = re.sub(r'skip=\d+', f'skip={next_skip}', response.url)
                self.logger.info(f"请求下一页: {next_url}")
                yield scrapy.Request(
                    url=next_url,
                    callback=self.parse,
                    meta={'category': category},
                    errback=self.errback_httpbin
                )
            else:
                self.logger.info(f"已到达最后一页，总条目: {total_entries}")
    
    def _is_paper_exists(self, arxiv_id):
        """检查论文是否已存在于数据库中"""
        try:
            return db_manager.paper_exists(self.db_session, arxiv_id)
        except Exception as e:
            self.logger.error(f"检查论文存在性时出错: {str(e)}")
            return False