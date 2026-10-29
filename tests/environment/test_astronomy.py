from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from platformdirs import user_cache_dir

from stella.environment import Astronomy, Location

CACHE = Path(user_cache_dir("stella")) / "skyfield"

pytestmark = pytest.mark.skipif(not (CACHE / "de421.bsp").exists(), reason="ephemeris not downloaded")


@pytest.fixture(scope="module")
def astronomy():
    return Astronomy(CACHE)


def test_midnight_in_paris_is_dark(astronomy):
    conditions = astronomy.conditions(Location(48.85, 2.35), datetime(2026, 10, 29, 23, tzinfo=timezone.utc))
    assert conditions.is_dark
    assert 0 <= conditions.moon_illumination <= 1


def test_paris_autumn_dark_window(astronomy):
    window = astronomy.dark_window(Location(48.85, 2.35), date(2026, 10, 29))
    assert window.start.hour == 18
    assert 9 < window.duration.total_seconds() / 3600 < 12


def test_arctic_summer_has_no_darkness(astronomy):
    assert astronomy.dark_window(Location(69.6, 18.9), date(2026, 6, 21)) is None
