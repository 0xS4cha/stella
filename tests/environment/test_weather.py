from datetime import date, datetime, timezone

import httpx
import pytest

from stella.environment import Location, OpenMeteoProvider, WeatherUnavailableError, conditions_at

PAYLOAD = {
    "hourly": {
        "time": ["2026-10-29T22:00", "2026-10-29T23:00"],
        "temperature_2m": [8.0, 6.5],
        "relative_humidity_2m": [85, 95],
        "dew_point_2m": [5.7, 5.8],
        "cloud_cover": [10, 70],
        "cloud_cover_low": [0, 60],
        "cloud_cover_mid": [10, 10],
        "cloud_cover_high": [0, None],
        "visibility": [24000, 9000],
        "wind_speed_10m": [5.0, 3.1],
    }
}


def provider(handler):
    return OpenMeteoProvider(httpx.Client(transport=httpx.MockTransport(handler)))


def test_forecast_parses_hourly_rows():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=PAYLOAD)

    rows = provider(handler).forecast(Location(48.85, 2.35), date(2026, 10, 29), date(2026, 10, 29))
    assert requests[0].url.params["start_date"] == "2026-10-29"
    assert "cloud_cover_low" in requests[0].url.params["hourly"]
    assert rows[0].time == datetime(2026, 10, 29, 22, tzinfo=timezone.utc)
    assert rows[1].cloud_cover_high_pct is None
    assert not rows[0].dew_risk
    assert rows[1].dew_risk


def test_conditions_at_picks_nearest_hour():
    weather = provider(lambda request: httpx.Response(200, json=PAYLOAD))
    row = conditions_at(weather, Location(48.85, 2.35), datetime(2026, 10, 29, 22, 40, tzinfo=timezone.utc))
    assert row.cloud_cover_pct == 70


def test_http_failure_is_wrapped():
    weather = provider(lambda request: httpx.Response(503))
    with pytest.raises(WeatherUnavailableError):
        weather.forecast(Location(0, 0), date(2026, 10, 29), date(2026, 10, 29))
