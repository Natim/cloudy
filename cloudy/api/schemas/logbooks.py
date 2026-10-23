from ninja import Schema


class LogbookCreateIn(Schema):
    category: str
    name: str | None = None


class LogbookPatchIn(Schema):
    name: str | None = None
    time_format: int | None = None
    height_format: int | None = None
