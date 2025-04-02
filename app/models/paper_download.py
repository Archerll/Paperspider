from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..utils.db_utils import Base

class PaperDownload(Base):
    __tablename__ = 'paper_downloads'
    
    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey('papers.id'), nullable=False)
    download_status = Column(String(20), default='pending')  # pending, downloading, completed, failed
    download_progress = Column(Float, default=0.0)
    download_path = Column(String(500))
    download_error = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 建立与Paper模型的关系
    paper = relationship('Paper', backref='downloads')