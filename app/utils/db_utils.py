import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

# 创建基类
Base = declarative_base()

# 定义Paper模型类
class Paper(Base):
    __tablename__ = 'papers'
    id = Column(Integer, primary_key=True)
    arxiv_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    authors = Column(Text, nullable=False)  # JSON格式存储
    institutions = Column(Text)  # JSON格式存储
    abstract = Column(Text, nullable=False)
    pdf_url = Column(String(200))
    published_date = Column(DateTime, nullable=False)
    categories = Column(String(200))  # 以逗号分隔的分类列表
    vector_id = Column(String(50))  # Milvus中的向量ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DBManager:
    """数据库管理器，提供独立的数据库会话"""
    
    def __init__(self):
        # 从环境变量或配置文件获取数据库连接信息
        db_user = os.environ.get('DB_USER', 'root')
        db_password = os.environ.get('DB_PASSWORD', 'root1234')
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '3306')
        db_name = os.environ.get('DB_NAME', 'paper_assistant')
        
        # 创建数据库连接
        self.engine = create_engine(
            f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}',
            pool_recycle=3600,
            echo=False
        )
        
        # 创建会话工厂
        self.Session = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """获取新的会话"""
        return self.Session()
    
    def paper_exists(self, session, arxiv_id):
        """检查论文是否已存在"""
        return session.query(Paper.id).filter_by(arxiv_id=arxiv_id).scalar() is not None
    
    def save_paper(self, session, paper_data):
        """保存论文数据"""
        try:
            # 检查论文是否已存在
            if not self.paper_exists(session, paper_data['arxiv_id']):
                # 创建新的论文记录
                paper = Paper(
                    arxiv_id=paper_data['arxiv_id'],
                    title=paper_data['title'],
                    authors=json.dumps(paper_data['authors']),
                    institutions=json.dumps(paper_data['institutions']),
                    abstract=paper_data['abstract'],
                    pdf_url=paper_data['pdf_url'],
                    published_date=paper_data['published_date'],
                    categories=','.join(paper_data['categories']) if paper_data['categories'] else ''
                )
                
                session.add(paper)
                session.commit()
                return True, "保存成功"
            else:
                return False, "论文已存在"
        except Exception as e:
            session.rollback()
            return False, str(e)

# 创建全局数据库管理器实例
db_manager = DBManager()