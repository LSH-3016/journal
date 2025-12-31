from sqlalchemy import Column, Integer, String, Text, Date, BigInteger, ARRAY
from database import Base

class History(Base):
    __tablename__ = "history"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String(255), index=True, nullable=False)
    content = Column(Text, nullable=False)
    record_date = Column(Date, nullable=False)
    tags = Column(ARRAY(Text), nullable=True)
    s3_key = Column(Text, nullable=True)  # 문자열로 변경