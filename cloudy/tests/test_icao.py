from cloudy.logbooks.icao import icao_from_place


def test_icao_from_place_strips_airport_name():
    assert icao_from_place("LFRN - Rennes Saint Jacques") == "LFRN"
    assert icao_from_place("lfrn - Rennes") == "LFRN"
    assert icao_from_place("LFRN") == "LFRN"
    assert icao_from_place("EHTE") == "EHTE"
    assert icao_from_place("") == ""
    assert icao_from_place(None) == ""
    assert icao_from_place("Rennes Saint Jacques") == "Rennes Saint Jacques"
