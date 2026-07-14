"""NcrpSuspectMobile — one row per suspect mobile number NCRP captured.

Parent: `ncrp_data` (FK on `acknowledgement_no`).
"""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, func

from database import Base


class NcrpSuspectMobile(Base):
    __tablename__ = "ncrp_suspect_mobiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    acknowledgement_no = Column(
        String(60),
        ForeignKey("ncrp_data.acknowledgement_no", ondelete="CASCADE"),
        nullable=False,
    )
    mobile = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
