from ninja import Schema


class TokenIn(Schema):
    email: str
    password: str


class TokenOut(Schema):
    api_key: str


class LogbookCreateIn(Schema):
    cat: str
    name: str | None = None


class LogbookPatchIn(Schema):
    name: str | None = None
    time_format: int | None = None
    height_format: int | None = None


class AircraftIn(Schema):
    imma: str
    type: str | None = None
    airport: str | None = None


class ErrorOut(Schema):
    detail: str
