from datetime import datetime
# from ..models import Paper, db
from ..utils.db_utils import db_manager

class PaperPipeline:
    def open_spider(self, spider):
        """爬虫启动时创建数据库会话"""
        self.db_session = db_manager.get_session()
        spider.logger.info("管道已创建数据库会话")
    
    def close_spider(self, spider):
        """爬虫关闭时关闭数据库会话"""
        if hasattr(self, 'db_session'):
            self.db_session.close()
            spider.logger.info("管道已关闭数据库会话")
    
    async def process_item(self, item, spider):
        """处理爬取的论文项"""
        try:
            success, message = db_manager.save_paper(self.db_session, dict(item))
            if success:
                spider.logger.info(f"保存论文成功: {item['arxiv_id']}")
            else:
                spider.logger.info(f"保存论文失败: {item['arxiv_id']} - {message}")
            return item
        except Exception as e:
            spider.logger.error(f"处理论文项时出错: {str(e)}")
            self.db_session.rollback()
            return item