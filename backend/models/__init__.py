"""Import every model here so Base.metadata knows about all tables.

Two main outbound tables (both keyed on `acknowledgement_no`):
  - `ncrp_data`           → outbound to NCRP (APIs 2 / 5)
  - `police_it_v2_data`   → outbound to Police IT V2 for FIR creation

Plus child tables for normalization and reference lookups.
"""
from models.police_station import PoliceStation
from models.user import User

# ── NCRP outbound side ──────────────────────────────────────────
from models.ncrp_data import NcrpData
from models.ncrp_transaction import NcrpTransaction
from models.ncrp_suspect_mobile import NcrpSuspectMobile
from models.ncrp_suspect_account import NcrpSuspectAccount
from models.ncrp_efir_answer import NcrpEfirAnswer

# ── Police IT V2 outbound side ──────────────────────────────────
from models.police_it_v2_data import PoliceITV2Data
from models.police_it_v2_act import PoliceITV2Act

__all__ = [
    "PoliceStation",
    "User",
    "NcrpData",
    "NcrpTransaction",
    "NcrpSuspectMobile",
    "NcrpSuspectAccount",
    "NcrpEfirAnswer",
    "PoliceITV2Data",
    "PoliceITV2Act",
]
