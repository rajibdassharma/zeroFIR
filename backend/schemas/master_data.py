"""Public schemas for the login dropdown chain."""
from pydantic import BaseModel


class DistrictPublic(BaseModel):
    id: int
    name: str


class PoliceStationPublic(BaseModel):
    id: int
    name: str
    district_id: int


class UserOptionPublic(BaseModel):
    """One entry in the login-page User ID dropdown. Role shown inline
    so the operator knows which entry is theirs."""
    username: str
    role: str
