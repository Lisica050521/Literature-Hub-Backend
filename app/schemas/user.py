from pydantic import BaseModel
from typing import List
from typing import Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    role: str

class UserResponse(UserBase):
    id: str

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    users: List[UserResponse]        

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None