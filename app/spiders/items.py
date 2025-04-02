from scrapy import Item, Field

class PaperItem(Item):
    """论文数据项"""
    arxiv_id = Field()  # arXiv ID
    title = Field()     # 标题
    authors = Field()   # 作者列表
    institutions = Field()  # 机构列表
    abstract = Field()  # 摘要
    pdf_url = Field()   # PDF链接
    published_date = Field()  # 发布时间
    categories = Field()  # arXiv分类