import os
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from .db_utils import db_manager
from ..models.paper_download import PaperDownload
from ..settings import (PAPERS_FOLDER, DOWNLOAD_MAX_WORKERS, DOWNLOAD_CHUNK_SIZE,
                      DOWNLOAD_RETRY_TIMES, DOWNLOAD_RETRY_DELAY, DOWNLOAD_DELAY)

class PaperDownloader:
    def __init__(self):
        self.max_workers = DOWNLOAD_MAX_WORKERS
        self.chunk_size = DOWNLOAD_CHUNK_SIZE
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.base_dir = Path(PAPERS_FOLDER)
        self.base_dir.mkdir(exist_ok=True)
        self.download_semaphore = threading.Semaphore(self.max_workers)

    def get_download_path(self, paper):
        """根据论文创建时间生成下载路径"""
        date_dir = paper.created_at.strftime('%Y-%m-%d')
        save_dir = self.base_dir / date_dir
        save_dir.mkdir(exist_ok=True)
        return str(save_dir / f"{paper.arxiv_id}.pdf")

    def download_paper(self, paper):
        """下载单个论文"""
        if not paper.pdf_url:
            return False, "PDF URL不存在"

        session = db_manager.get_session()
        try:
            # 创建或获取下载记录
            download_record = session.query(PaperDownload).filter_by(paper_id=paper.id).first()
            if not download_record:
                download_record = PaperDownload(paper_id=paper.id)
                session.add(download_record)
            
            # 更新下载状态为downloading
            download_record.download_status = 'downloading'
            download_record.download_progress = 0
            download_record.download_path = self.get_download_path(paper)
            session.commit()

            # 使用信号量控制并发下载数量
            with self.download_semaphore:
                # 添加重试机制
                for retry in range(DOWNLOAD_RETRY_TIMES):
                    try:
                        # 发送请求获取文件大小
                        response = requests.get(paper.pdf_url, stream=True)
                        response.raise_for_status()
                        total_size = int(response.headers.get('content-length', 0))
                        break
                    except Exception as e:
                        if retry < DOWNLOAD_RETRY_TIMES - 1:
                            time.sleep(DOWNLOAD_RETRY_DELAY)
                            continue
                        raise e

            # 创建临时文件
            temp_path = download_record.download_path + '.tmp'
            downloaded_size = 0

            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            download_record.download_progress = progress
                            session.commit()

            # 下载完成后重命名文件
            os.rename(temp_path, download_record.download_path)
            download_record.download_status = 'completed'
            download_record.download_progress = 100
            session.commit()
            # 添加下载延迟
            time.sleep(DOWNLOAD_DELAY)
            return True, "下载成功"

        except Exception as e:
            download_record.download_status = 'failed'
            download_record.download_error = str(e)
            session.commit()
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False, str(e)

        finally:
            session.close()

    def download_papers(self, papers):
        """批量下载论文"""
        futures = []
        for paper in papers:
            # 直接提交下载任务，不检查download_status
            # 因为Paper模型没有download_status字段
            # download_paper方法会创建或获取PaperDownload记录并处理状态
            future = self.executor.submit(self.download_paper, paper)
            futures.append(future)
        return futures

# 创建全局下载器实例
paper_downloader = PaperDownloader()