from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, not_null=True)
    twitter_user_id = Column(Integer, not_null=True)
    username = Column(String, not_null=True)
    
    def __repr__(self) -> str:
            return f"User(id={self.id}, twitter_user_id={self.twitter_user_id}, username={self.username})"