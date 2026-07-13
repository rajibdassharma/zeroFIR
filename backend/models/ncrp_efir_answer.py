"""NcrpEfirAnswer — one row per e-FIR Y/N question NCRP asked the complainant.

Screens 3–9 of KarnatakazeroFIR show the seven canonical questions
NCRP puts to a complainant during e-FIR triage. The answers are what
drive the "should this become a Zero FIR" decision downstream — kept
as rows (rather than columns on ncrp_complaints) so the question
catalogue can evolve without a schema change every time NCRP updates
the questionnaire.
"""
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, func

from database import Base


# Canonical question codes we recognise. NCRP may send others — those
# get stored verbatim with an "unknown" code so nothing gets dropped.
QUESTION_CODES = frozenset({
    "amount_10_lakh_or_above",           # slide 8
    "residing_in_state",                  # slide 9
    "occurred_in_state_jurisdiction",     # slide 10
    "bns_318_4_cheated_delivered",        # slide 11
    "bns_319_pretending_someone_else",    # slide 12
    "bns_308_taken_through_threats",      # slide 13
    "bns_340_fake_document_electronic",   # slide 14
})


class NcrpEfirAnswer(Base):
    __tablename__ = "ncrp_efir_answers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(
        String(36),
        ForeignKey("ncrp_complaints.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Slug from QUESTION_CODES, or "unknown" if NCRP added a new one.
    question_code = Column(String(60), nullable=False)
    # Full question text (English + Kannada) as NCRP asked it, so the
    # Masking App can render the exact wording the complainant saw.
    question_text = Column(Text, nullable=False)
    answer = Column(Boolean, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
