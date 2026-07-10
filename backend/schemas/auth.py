from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=200)


class LoginResponse(BaseModel):
    token: str
    role: str
    user_id: int
    full_name: str | None = None
    must_change_password: bool = False


class MeResponse(BaseModel):
    id: int
    username: str
    role: str
    full_name: str | None = None
    unit_id: int | None = None
    ps_id: int | None = None
