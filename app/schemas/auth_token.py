from pydantic import BaseModel

class AuthToken(BaseModel):
    access_token: str
    token_type: str

class TokenMetadata(BaseModel):
    username: str | None = None