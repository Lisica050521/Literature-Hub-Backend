from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime, timedelta
from app.db.base import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    literature_item_id = Column(Integer, ForeignKey("literature_items.id"), nullable=False)
    loan_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=14))  # срок возврата 2 недели
    return_date = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="transactions")
    literature_item = relationship("LiteratureItem", back_populates="transactions")

    @hybrid_property
    def book_id(self):
        return self.literature_item_id