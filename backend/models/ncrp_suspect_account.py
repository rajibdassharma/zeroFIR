"""NcrpSuspectAccount — one row per suspect bank / wallet / UPI account.

Parent: `ncrp_data` (FK on `acknowledgement_no`).

Populated when the operator sets `has_suspect_account_details = True`
on the parent NcrpData (mirrors NCRP's "Do You have Suspect Account
Details?" toggle on the Transactions screen).

Distinct from `NcrpTransaction` (which records the VICTIM's account
debits) — this row is the FRAUDSTER's account where the money went.
"""
import uuid

from sqlalchemy import (
    Column, Date, DateTime, ForeignKey, Numeric, String, func,
)

from database import Base


class NcrpSuspectAccount(Base):
    __tablename__ = "ncrp_suspect_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    acknowledgement_no = Column(
        String(60),
        ForeignKey("ncrp_data.acknowledgement_no", ondelete="CASCADE"),
        nullable=False,
    )
    bank_wallet = Column(String(150), nullable=True)
    account_id = Column(String(60), nullable=True)
    ifsc_code = Column(String(20), nullable=True)
    account_holder_name = Column(String(200), nullable=True)
    amount_credited = Column(Numeric(18, 2), nullable=True)
    credited_on = Column(Date, nullable=True)
    remarks = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
