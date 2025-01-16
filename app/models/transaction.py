from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
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

    user = relationship("User", back_populates="transactions")
    literature_item = relationship("LiteratureItem", back_populates="transactions")