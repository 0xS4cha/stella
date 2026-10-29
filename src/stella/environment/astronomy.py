import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import Any

from platformdirs import user_cache_dir
from skyfield import almanac
from skyfield.api import Loader, wgs84

from .location import Location

EPHEMERIS = "de421.bsp"
DARK_STATE = 0


class Twilight(str, Enum):
    DAY = "day"
    CIVIL = "civil"
    NAUTICAL = "nautical"
    ASTRONOMICAL = "astronomical"
    NIGHT = "night"


def classify_twilight(sun_altitude: float) -> Twilight:
    if sun_altitude > -0.833:
        return Twilight.DAY
    if sun_altitude > -6.0:
        return Twilight.CIVIL
    if sun_altitude > -12.0:
        return Twilight.NAUTICAL
    if sun_altitude > -18.0:
        return Twilight.ASTRONOMICAL
    return Twilight.NIGHT


@dataclass(frozen=True)
class AstronomicalConditions:
    time: datetime
    sun_altitude: float
    moon_altitude: float
    moon_azimuth: float
    moon_illumination: float
    twilight: Twilight

    @property
    def moon_interference(self) -> float:
        return self.moon_illumination * max(0.0, math.sin(math.radians(self.moon_altitude)))

    @property
    def is_dark(self) -> bool:
        return self.twilight is Twilight.NIGHT

    def to_dict(self) -> dict[str, Any]:
        return {
            "time": self.time.isoformat(),
            "sun_altitude": round(self.sun_altitude, 2),
            "moon_altitude": round(self.moon_altitude, 2),
            "moon_azimuth": round(self.moon_azimuth, 2),
            "moon_illumination": round(self.moon_illumination, 3),
            "moon_interference": round(self.moon_interference, 3),
            "twilight": self.twilight.value,
            "is_dark": self.is_dark,
        }


@dataclass(frozen=True)
class DarkWindow:
    start: datetime
    end: datetime

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    def to_dict(self) -> dict[str, Any]:
        return {"start": self.start.isoformat(), "end": self.end.isoformat(), "hours": round(self.duration.total_seconds() / 3600, 2)}


class Astronomy:
    def __init__(self, cache_dir: Path | None = None):
        self._loader = Loader(str(cache_dir or Path(user_cache_dir("stella")) / "skyfield"), verbose=False)

    @cached_property
    def ephemeris(self):
        return self._loader(EPHEMERIS)

    @cached_property
    def timescale(self):
        return self._loader.timescale()

    def conditions(self, location: Location, when: datetime) -> AstronomicalConditions:
        when = _as_utc(when)
        moment = self.timescale.from_datetime(when)
        observer = self.ephemeris["earth"] + self._topos(location)
        sun_altitude, _, _ = observer.at(moment).observe(self.ephemeris["sun"]).apparent().altaz()
        moon_altitude, moon_azimuth, _ = observer.at(moment).observe(self.ephemeris["moon"]).apparent().altaz()
        illumination = almanac.fraction_illuminated(self.ephemeris, "moon", moment)
        return AstronomicalConditions(
            time=when,
            sun_altitude=float(sun_altitude.degrees),
            moon_altitude=float(moon_altitude.degrees),
            moon_azimuth=float(moon_azimuth.degrees),
            moon_illumination=float(illumination),
            twilight=classify_twilight(float(sun_altitude.degrees)),
        )

    def dark_window(self, location: Location, night_of: date) -> DarkWindow | None:
        start = datetime.combine(night_of, time(12), tzinfo=timezone.utc) - timedelta(hours=location.longitude / 15.0)
        t0 = self.timescale.from_datetime(start)
        t1 = self.timescale.from_datetime(start + timedelta(days=1))
        state = almanac.dark_twilight_day(self.ephemeris, self._topos(location))
        times, states = almanac.find_discrete(t0, t1, state)
        begin = end = None
        for moment, value in zip(times, states):
            if value == DARK_STATE and begin is None:
                begin = moment.utc_datetime()
            elif value != DARK_STATE and begin is not None:
                end = moment.utc_datetime()
                break
        if begin is None:
            return None
        return DarkWindow(begin, end or (start + timedelta(days=1)))

    @staticmethod
    def _topos(location: Location):
        return wgs84.latlon(location.latitude, location.longitude, elevation_m=location.elevation_m)


def _as_utc(when: datetime) -> datetime:
    return when.replace(tzinfo=timezone.utc) if when.tzinfo is None else when.astimezone(timezone.utc)
