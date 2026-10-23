from ninja import Schema


class AircraftIn(Schema):
    registration: str
    aircraft_type: str | None = None
    airport: str | None = None
