from sqlalchemy import Column, Integer, String, Text, Date, BigInteger, ARRAY
from database import Base

class History(Base):
    __tablename__ = "history"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    username = Column(String(255), index=True, nullable=False)
    content = Column(Text, nullable=False)
    record_date = Column(Date, nullable=False)
    tags = Column(ARRAY(Text), nullable=True)