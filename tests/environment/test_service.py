from datetime import date, datetime, timedelta, timezone

from stella.environment import (
    AstronomicalConditions,
    DarkWindow,
    EnvironmentService,
    Lens,
    Location,
    SkyQuality,
    Twilight,
    WeatherConditions,
    WeatherUnavailableError,
    classify_twilight,
)

WHEN = datetime(2026, 10, 29, 22, tzinfo=timezone.utc)
PARIS = Location(48.85, 2.35)


class FakeAstronomy:
    def __init__(self, moon_altitude=-10.0, sun_altitude=-40.0, window=True):
        self.moon_altitude = moon_altitude
        self.sun_altitude = sun_altitude
        self.window = window

    def conditions(self, location, when):
        return AstronomicalConditions(when, self.sun_altitude, self.moon_altitude, 90.0, 0.8, classify_twilight(self.sun_altitude))

    def dark_window(self, location, night_of):
        return DarkWindow(WHEN - timedelta(hours=4), WHEN + timedelta(hours=6)) if self.window else None


def weather_row(time, clouds=0.0, temperature=10.0, dew_point=2.0):
    return WeatherConditions(time, temperature, 60.0, dew_point, clouds, 0.0, 0.0, 0.0, 30000.0, 5.0)


class FakeWeather:
    def __init__(self, clouds=0.0, fail=False):
        self.clouds = clouds
        self.fail = fail

    def forecast(self, location, start, end):
        if self.fail:
            raise WeatherUnavailableError("offline")
        return [weather_row(WHEN + timedelta(hours=offset), self.clouds) for offset in range(-6, 12)]


def test_twilight_classification():
    assert classify_twilight(10) is Twilight.DAY
    assert classify_twilight(-3) is Twilight.CIVIL
    assert classify_twilight(-15) is Twilight.ASTRONOMICAL
    assert classify_twilight(-30) is Twilight.NIGHT


def test_clear_dark_snapshot_has_no_warnings():
    service = EnvironmentService(FakeAstronomy(), FakeWeather())
    snapshot = service.snapshot(PARIS, WHEN, SkyQuality.from_bortle(4), Lens(18, 3.5))
    assert snapshot.warnings == ()
    assert snapshot.weather.time == WHEN
    assert snapshot.exposure_limits.recommended_s < 30
    assert snapshot.to_dict()["sky"]["bortle"] == 4


def test_bad_conditions_raise_warnings():
    service = EnvironmentService(FakeAstronomy(moon_altitude=50.0, sun_altitude=-10.0), FakeWeather(clouds=80.0))
    warnings = " | ".join(service.snapshot(PARIS, WHEN).warnings)
    assert "nautical" in warnings
    assert "Moon" in warnings
    assert "Cloud cover is 80%" in warnings


def test_weather_failure_degrades_gracefully():
    snapshot = EnvironmentService(FakeAstronomy(), FakeWeather(fail=True)).snapshot(PARIS, WHEN)
    assert snapshot.weather is None
    assert snapshot.warnings == ("offline",)


def test_night_plan_keeps_forecast_inside_dark_window():
    plan = EnvironmentService(FakeAstronomy(), FakeWeather()).night_plan(PARIS, date(2026, 10, 29))
    assert plan.forecast[0].time == WHEN - timedelta(hours=5)
    assert plan.forecast[-1].time == WHEN + timedelta(hours=6)


def test_night_plan_without_darkness():
    plan = EnvironmentService(FakeAstronomy(window=False), FakeWeather()).night_plan(PARIS, date(2026, 6, 21))
    assert plan.dark_window is None
    assert plan.forecast == ()
