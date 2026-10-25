from ninja import Schema


class TokenIn(Schema):
    email: str
    password: str


class TokenOut(Schema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
