from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, nullable=False)
    bio = Column(String, nullable=True)

    literature_items = relationship("LiteratureItem", back_populates="author")

    def __repr__(self):
        return f"<Author(id={self.id}, name={self.name})>"