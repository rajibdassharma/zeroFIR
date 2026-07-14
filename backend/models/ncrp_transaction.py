"""NcrpTransaction — one row per victim-account debit reported to NCRP.

Parent: `ncrp_data` (FK on `acknowledgement_no`).

A single complaint typically lists multiple transactions across
different bank / wallet / UPI accounts.
"""
import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, Numeric, String, func

from database import Base


class NcrpTransaction(Base):
    __tablename__ = "ncrp_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    acknowledgement_no = Column(
        String(60),
        ForeignKey("ncrp_data.acknowledgement_no", ondelete="CASCADE"),
        nullable=False,
    )

    # NCRP dropdown values.
    sub_category = Column(String(100), nullable=True)     # "Demat/Depository Fraud"
    bank_wallet = Column(String(200), nullable=True)      # "State Bank of India"

    # Account / wallet / UPI id / merchant id — kept as free text to
    # cover every payment surface NCRP handles.
    account_id = Column(String(200), nullable=True)

    # Transaction identifier — usually 12-digit UTR but wallets emit
    # longer ones. NCRP-supplied.
    transaction_id = Column(String(100), nullable=True)

    transaction_date = Column(Date, nullable=True)
    approx_time = Column(String(20), nullable=True)       # "09:37 PM" as string
    amount = Column(Numeric(18, 2), nullable=True)
    reference_no = Column(String(200), nullable=True)     # bank ref no
    other = Column(String(500), nullable=True)            # NCRP "Other" free-text

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
