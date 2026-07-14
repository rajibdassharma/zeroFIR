"""NcrpEfirAnswer — one row per e-FIR Y/N question NCRP asked the complainant.

Parent: `ncrp_data` (FK on `acknowledgement_no`).

The seven canonical questions drive the "should this become a Zero
FIR" decision downstream — kept as rows so the question catalogue
can evolve without a schema change.
"""
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, func

from database import Base


# Canonical question codes we recognise. NCRP may send others — those
# get stored verbatim with an "unknown" code so nothing gets dropped.
QUESTION_CODES = frozenset({
    "amount_10_lakh_or_above",
    "residing_in_state",
    "occurred_in_state_jurisdiction",
    "bns_318_4_cheated_delivered",
    "bns_319_pretending_someone_else",
    "bns_308_taken_through_threats",
    "bns_340_fake_document_electronic",
})


class NcrpEfirAnswer(Base):
    __tablename__ = "ncrp_efir_answers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    acknowledgement_no = Column(
        String(60),
        ForeignKey("ncrp_data.acknowledgement_no", ondelete="CASCADE"),
        nullable=False,
    )
    question_code = Column(String(60), nullable=False)
    question_text = Column(Text, nullable=False)
    answer = Column(Boolean, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
