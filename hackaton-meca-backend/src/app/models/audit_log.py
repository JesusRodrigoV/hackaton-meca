from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event = Column(String(100), nullable=False, index=True)   
    log_type = Column(String(50), nullable=False, server_default="security", index=True)
    action = Column(String(160), nullable=True)
    detail = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = Column(String(120), ForeignKey("users.id"), nullable=True)
    attempted_email = Column(String(200), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)
    ip_country = Column(String(120), nullable=True)
    ip_asn = Column(Integer, nullable=True)
    ip_organization = Column(String(255), nullable=True)
    ip_guide_data = Column(JSON, nullable=True)

    user = relationship("User")
