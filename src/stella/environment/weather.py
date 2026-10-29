from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Protocol

import httpx

from .errors import WeatherUnavailableError
from .location import Location

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_FIELDS = {
    "temperature_2m": "temperature_c",
    "relative_humidity_2m": "humidity_pct",
    "dew_point_2m": "dew_point_c",
    "cloud_cover": "cloud_cover_pct",
    "cloud_cover_low": "cloud_cover_low_pct",
    "cloud_cover_mid": "cloud_cover_mid_pct",
    "cloud_cover_high": "cloud_cover_high_pct",
    "visibility": "visibility_m",
    "wind_speed_10m": "wind_speed_kmh",
}
DEW_RISK_MARGIN_C = 2.0


@dataclass(frozen=True)
class WeatherConditions:
    time: datetime
    temperature_c: float | None
    humidity_pct: float | None
    dew_point_c: float | None
    cloud_cover_pct: float | None
    cloud_cover_low_pct: float | None
    cloud_cover_mid_pct: float | None
    cloud_cover_high_pct: float | None
    visibility_m: float | None
    wind_speed_kmh: float | None

    @property
    def dew_risk(self) -> bool:
        if self.temperature_c is None or self.dew_point_c is None:
            return False
        return self.temperature_c - self.dew_point_c <= DEW_RISK_MARGIN_C

    def to_dict(self) -> dict[str, Any]:
        data = {name: getattr(self, name) for name in HOURLY_FIELDS.values()}
        return {"time": self.time.isoformat(), **data, "dew_risk": self.dew_risk}


class WeatherProvider(Protocol):
    def forecast(self, location: Location, start: date, end: date) -> list[WeatherConditions]: ...


class OpenMeteoProvider:
    def __init__(self, client: httpx.Client | None = None, url: str = OPEN_METEO_URL):
        self._client = client or httpx.Client(timeout=10.0)
        self._url = url

    def forecast(self, location: Location, start: date, end: date) -> list[WeatherConditions]:
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "elevation": location.elevation_m,
            "hourly": ",".join(HOURLY_FIELDS),
            "timezone": "UTC",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        try:
            response = self._client.get(self._url, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise WeatherUnavailableError(f"Open-Meteo request failed: {error}") from error
        return parse_hourly(payload)


def parse_hourly(payload: dict[str, Any]) -> list[WeatherConditions]:
    hourly = payload.get("hourly")
    if not hourly or "time" not in hourly:
        raise WeatherUnavailableError("Open-Meteo response has no hourly data")
    rows = []
    for index, stamp in enumerate(hourly["time"]):
        values = {target: _at(hourly.get(source), index) for source, target in HOURLY_FIELDS.items()}
        rows.append(WeatherConditions(time=datetime.fromisoformat(stamp).replace(tzinfo=timezone.utc), **values))
    return rows


def conditions_at(provider: WeatherProvider, location: Location, when: datetime) -> WeatherConditions:
    when = when.astimezone(timezone.utc)
    rows = provider.forecast(location, when.date(), (when + timedelta(hours=1)).date())
    if not rows:
        raise WeatherUnavailableError("No weather data for the requested time")
    return min(rows, key=lambda row: abs(row.time - when))


def _at(values: list | None, index: int) -> float | None:
    if values is None or index >= len(values) or values[index] is None:
        return None
    return float(values[index])
