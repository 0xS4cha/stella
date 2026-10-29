import pytest

from stella.camera import InvalidSettingValueError, ReadOnlySettingError, SettingNotFoundError


def test_list_flattens_sections(controller):
    settings = controller.config.list()
    assert {"iso", "shutterspeed", "longexpnr"} <= settings.keys()
    assert "capturesettings" not in settings


def test_apply_writes_once(controller, camera):
    applied = controller.config.apply({"iso": "1600", "longexpnr": "on", "exposurecompensation": "-1"})
    assert applied == {"iso": "1600", "longexpnr": 1, "exposurecompensation": -1.0}
    assert camera.writes == 1
    assert controller.config.get("iso").value == "1600"


def test_apply_is_atomic_on_invalid_value(controller, camera):
    with pytest.raises(InvalidSettingValueError):
        controller.config.apply({"iso": "1600", "shutterspeed": "60"})
    assert camera.writes == 0
    assert controller.config.get("iso").value == "400"


def test_unknown_setting(controller):
    with pytest.raises(SettingNotFoundError):
        controller.config.get("nope")


def test_readonly_setting(controller):
    with pytest.raises(ReadOnlySettingError):
        controller.config.set("expprogram", "A")
