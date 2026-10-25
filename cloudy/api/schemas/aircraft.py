from ninja import Schema


class AircraftIn(Schema):
    registration: str
    aircraft_type: str | None = None
    airport: str | None = None


class AircraftPatchIn(Schema):
    registration: str | None = None
    aircraft_type: str | None = None
    airport: str | None = None
