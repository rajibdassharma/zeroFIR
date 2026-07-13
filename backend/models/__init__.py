"""Import every model here so Base.metadata knows about all tables.

Never remove entries. Migration authors reference Base.metadata for
schema inspection, and seed.py's Base.metadata.create_all needs all
models registered.
"""
from models.district import District
from models.police_station import PoliceStation
from models.user import User
from models.ncrp_complaint import NcrpComplaint
from models.ncrp_transaction import NcrpTransaction
from models.ncrp_suspect_mobile import NcrpSuspectMobile
from models.ncrp_efir_answer import NcrpEfirAnswer
from models.masked_application import MaskedApplication

__all__ = [
    "District",
    "PoliceStation",
    "User",
    "NcrpComplaint",
    "NcrpTransaction",
    "NcrpSuspectMobile",
    "NcrpEfirAnswer",
    "MaskedApplication",
]
