from cloudy.core.widgets import HorizontalRadioSelect


def test_horizontal_radio_renders_each_label_once():
    widget = HorizontalRadioSelect(choices=((0, "SE"), (1, "ME"), (-1, "Aucun")))
    html = widget.render("single_pilot_se_me", "0", attrs={"id": "id_single_pilot_se_me"})

    assert html.count("SE") == 1
    assert html.count("ME") == 1
    assert html.count("Aucun") == 1
    assert html.count("<label") == 3
    assert html.count("label-radio") == 3
    assert html.count("radio-inline") == 3
    assert 'id="id_single_pilot_se_me_0"' in html
    assert "checked" in html
