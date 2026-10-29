from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any

from .astronomy import Astronomy, AstronomicalConditions, DarkWindow
from .errors import WeatherUnavailableError
from .location import Location
from .optics import NIKON_D60, CameraBody, ExposureLimits, Lens, exposure_limits
from .sky import SkyQuality
from .weather import WeatherConditions, WeatherProvider, conditions_at

MOON_INTERFERENCE_WARNING = 0.3
CLOUD_COVER_WARNING = 40.0


@dataclass(frozen=True)
class EnvironmentSnapshot:
    time: datetime
    location: Location
    astronomy: AstronomicalConditions
    weather: WeatherConditions | None = None
    sky: SkyQuality | None = None
    exposure_limits: ExposureLimits | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "time": self.time.isoformat(),
            "location": self.location.to_dict(),
            "astronomy": self.astronomy.to_dict(),
            "weather": self.weather.to_dict() if self.weather else None,
            "sky": self.sky.to_dict() if self.sky else None,
            "exposure_limits": self.exposure_limits.to_dict() if self.exposure_limits else None,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class NightPlan:
    location: Location
    dark_window: DarkWindow | None
    forecast: tuple[WeatherConditions, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "location": self.location.to_dict(),
            "dark_window": self.dark_window.to_dict() if self.dark_window else None,
            "forecast": [row.to_dict() for row in self.forecast],
            "warnings": list(self.warnings),
        }


class EnvironmentService:
    def __init__(self, astronomy: Astronomy | None = None, weather: WeatherProvider | None = None, body: CameraBody = NIKON_D60):
        self.astronomy = astronomy or Astronomy()
        self.weather = weather
        self.body = body

    def snapshot(
        self,
        location: Location,
        when: datetime | None = None,
        sky: SkyQuality | None = None,
        lens: Lens | None = None,
        aperture: float | None = None,
    ) -> EnvironmentSnapshot:
        when = when or datetime.now(timezone.utc)
        astronomy = self.astronomy.conditions(location, when)
        warnings = []
        weather = None
        if self.weather is not None:
            try:
                weather = conditions_at(self.weather, location, when)
            except WeatherUnavailableError as error:
                warnings.append(str(error))
        limits = exposure_limits(self.body, lens, aperture) if lens else None
        warnings.extend(assess(astronomy, weather))
        return EnvironmentSnapshot(astronomy.time, location, astronomy, weather, sky, limits, tuple(warnings))

    def night_plan(self, location: Location, night_of: date) -> NightPlan:
        window = self.astronomy.dark_window(location, night_of)
        warnings = [] if window else ["No astronomical darkness on this night"]
        forecast: tuple[WeatherConditions, ...] = ()
        if self.weather is not None and window is not None:
            try:
                rows = self.weather.forecast(location, window.start.date(), window.end.date())
                forecast = tuple(row for row in rows if window.start - timedelta(hours=1) <= row.time <= window.end)
            except WeatherUnavailableError as error:
                warnings.append(str(error))
        return NightPlan(location, window, forecast, tuple(warnings))


def assess(astronomy: AstronomicalConditions, weather: WeatherConditions | None) -> list[str]:
    warnings = []
    if not astronomy.is_dark:
        warnings.append(f"Sky is not fully dark ({astronomy.twilight.value} twilight)")
    if astronomy.moon_interference >= MOON_INTERFERENCE_WARNING:
        warnings.append(f"Moon is bright and high ({astronomy.moon_illumination:.0%} lit, {astronomy.moon_altitude:.0f}° altitude)")
    if weather is not None:
        if weather.cloud_cover_pct is not None and weather.cloud_cover_pct >= CLOUD_COVER_WARNING:
            warnings.append(f"Cloud cover is {weather.cloud_cover_pct:.0f}%")
        if weather.dew_risk:
            warnings.append("Dew risk: temperature is close to the dew point")
    return warnings
