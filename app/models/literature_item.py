from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class LiteratureItem(Base):
    __tablename__ = "literature_items"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    publication_date = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    available_copies = Column(Integer, default=0)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)

    author = relationship("Author", back_populates="literature_items")
    
    transactions = relationship("Transaction", back_populates="literature_item")