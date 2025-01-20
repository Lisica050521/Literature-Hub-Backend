from pydantic import BaseModel
from typing import List
from typing import Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    role: str

class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    users: List[UserResponse]        

class UserUpdate(BaseModel):
    uusername: Optional[str] = None
    password: Optional[str] = None