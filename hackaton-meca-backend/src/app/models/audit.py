from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class AuditChainHead(Base):
    __tablename__ = "audit_chain_head"

    id = Column(SmallInteger, primary_key=True)
    last_hash = Column(String(64), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True)
    action = Column(String(80), nullable=False)
    entity = Column(String(80), nullable=False)
    entity_id = Column(String(50), nullable=True)
    details_json = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(300), nullable=True)
    request_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    prev_hash = Column(String(64), nullable=True)
    row_hash = Column(String(64), nullable=True)

    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_logs_user", "user_id", "created_at"),
        Index("idx_audit_logs_entity", "entity", "entity_id"),
    )
