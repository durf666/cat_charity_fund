from pydantic import BaseModel


class User(BaseModel):
    id: int
    is_active: bool = True
    is_verified: bool = False
    is_superuser: bool = False
