from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class TwoFactorCodes(Base):
    __tablename__ = "two_factor_codes"

    id = Column(Integer, primary_key=True, index=True)
    code_hash = Column(String(255), nullable=False) 
    is_used = Column(Boolean, default=False, nullable=False)
    user_id = Column(String(120), ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="backup_codes")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
