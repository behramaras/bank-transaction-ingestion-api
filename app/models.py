from app.databases import Base
from sqlalchemy import Float, Column, String, DateTime, Integer


class Upload(Base):
    __tablename__ = "uploads"

    created_at = Column(DateTime)
    upload_id = Column(String, primary_key=True)
    status = Column(String)
    rows_ingested = Column(Integer, default=0)
    rows_failed = Column(Integer, default=0)

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True)
    upload_id = Column(String, index=True)
    account_id = Column(String, index=True)
    user_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    amount = Column(Float)
    currency = Column(String)
    merchant_id = Column(String)
    category = Column(String)

