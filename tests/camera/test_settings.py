import gphoto2 as gp
import pytest

from stella.camera import InvalidSettingValueError, Setting

from .fakes import FakeWidget


def make(widget_type, **kwargs):
    return Setting.from_widget(FakeWidget("name", widget_type, **kwargs))


@pytest.mark.parametrize("raw, expected", [("on", 1), ("FALSE", 0), (True, 1), ("1", 1)])
def test_toggle_coercion(raw, expected):
    assert make(gp.GP_WIDGET_TOGGLE, value=0).coerce(raw) == expected


def test_toggle_rejects_garbage():
    with pytest.raises(InvalidSettingValueError):
        make(gp.GP_WIDGET_TOGGLE, value=0).coerce("maybe")


def test_range_bounds():
    setting = make(gp.GP_WIDGET_RANGE, value=0.0, value_range=(-1.0, 1.0, 0.5))
    assert setting.coerce("0.5") == 0.5
    with pytest.raises(InvalidSettingValueError):
        setting.coerce("2")


def test_choice_is_case_insensitive():
    setting = make(gp.GP_WIDGET_RADIO, value="Auto", choices=["Auto", "Daylight"])
    assert setting.coerce("daylight") == "Daylight"
    with pytest.raises(InvalidSettingValueError, match="expected one of"):
        setting.coerce("Cloudy")


def test_to_dict_exposes_choices_and_range():
    data = make(gp.GP_WIDGET_RANGE, value=0.0, value_range=(-1.0, 1.0, 0.5)).to_dict()
    assert data["type"] == "range"
    assert data["range"] == {"min": -1.0, "max": 1.0, "step": 0.5}
