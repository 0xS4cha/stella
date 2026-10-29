import pytest

from stella.environment import EnvironmentDataError, SkyQuality


@pytest.mark.parametrize("sqm, bortle", [(22.0, 1), (21.8, 3), (20.8, 4), (19.0, 6), (17.0, 9)])
def test_sqm_to_bortle(sqm, bortle):
    assert SkyQuality.from_sqm(sqm).bortle == bortle


@pytest.mark.parametrize("bortle", range(1, 10))
def test_bortle_round_trip(bortle):
    assert SkyQuality.from_sqm(SkyQuality.from_bortle(bortle).sqm).bortle == bortle


def test_invalid_bortle():
    with pytest.raises(EnvironmentDataError):
        SkyQuality.from_bortle(10)
