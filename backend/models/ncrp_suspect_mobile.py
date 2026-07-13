"""NcrpSuspectMobile — one row per suspect mobile number NCRP captured.

NCRP screen 1 has an "Add" button next to Suspect Mobile No, so the
complaint can carry 0..n suspect mobiles. Kept as a separate table
(rather than a JSON array on ncrp_complaints) so future analytics can
group cases by shared suspect numbers.
"""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, func

from database import Base


class NcrpSuspectMobile(Base):
    __tablename__ = "ncrp_suspect_mobiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(
        String(36),
        ForeignKey("ncrp_complaints.id", ondelete="CASCADE"),
        nullable=False,
    )
    mobile = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
