"""Public schemas for the login user dropdown + PS lookup."""
from pydantic import BaseModel


class UserOptionPublic(BaseModel):
    """One entry in the login-page User ID dropdown. Role shown inline
    so the operator can double-check they picked the right entry."""
    username: str
    role: str


class PoliceStationPublic(BaseModel):
    """Feeds the NCRP-entry Address tab's Police Station dropdown so
    the CC operator always picks a value that resolves — no free-text
    typos, no unanchored complaints."""
    id: int
    name: str
