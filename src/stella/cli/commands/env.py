import argparse
import os
from datetime import date, datetime

from ...environment import EnvironmentService, Lens, Location, OpenMeteoProvider, SkyQuality
from ..output import print_mapping, to_json


def register(subparsers) -> None:
    parser = subparsers.add_parser("env", help="Inspect observing conditions")
    actions = parser.add_subparsers(dest="action", required=True)

    now_parser = actions.add_parser("now", help="Conditions at a given time")
    add_location_arguments(now_parser)
    now_parser.add_argument("--time", type=datetime.fromisoformat, help="ISO timestamp, defaults to now")
    sky = now_parser.add_mutually_exclusive_group()
    sky.add_argument("--bortle", type=int)
    sky.add_argument("--sqm", type=float)
    now_parser.add_argument("--focal-length", type=float, help="Lens focal length in mm")
    now_parser.add_argument("--aperture", type=float, help="Shooting f-number")
    now_parser.set_defaults(handler=now, needs_camera=False)

    night_parser = actions.add_parser("night", help="Darkness window and hourly forecast for a night")
    add_location_arguments(night_parser)
    night_parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    night_parser.set_defaults(handler=night, needs_camera=False)


def add_location_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--lat", type=float, default=_env_float("STELLA_LATITUDE"))
    parser.add_argument("--lon", type=float, default=_env_float("STELLA_LONGITUDE"))
    parser.add_argument("--elevation", type=float, default=_env_float("STELLA_ELEVATION") or 0.0)
    parser.add_argument("--offline", action="store_true", help="Skip the weather forecast")
    parser.add_argument("--json", action="store_true")


def now(args, controller: None) -> None:
    sky = SkyQuality.from_bortle(args.bortle) if args.bortle else SkyQuality.from_sqm(args.sqm) if args.sqm else None
    lens = Lens(args.focal_length, args.aperture or 3.5) if args.focal_length else None
    snapshot = _service(args).snapshot(_location(args), args.time, sky, lens, args.aperture)
    _emit(snapshot.to_dict(), args.json)


def night(args, controller: None) -> None:
    _emit(_service(args).night_plan(_location(args), args.date).to_dict(), args.json)


def _service(args) -> EnvironmentService:
    return EnvironmentService(weather=None if args.offline else OpenMeteoProvider())


def _location(args) -> Location:
    if args.lat is None or args.lon is None:
        raise ValueError("Location required: pass --lat/--lon or set STELLA_LATITUDE/STELLA_LONGITUDE")
    return Location(args.lat, args.lon, args.elevation)


def _emit(data: dict, as_json: bool) -> None:
    if as_json:
        print(to_json(data))
        return
    forecast = data.pop("forecast", None)
    print_mapping({key: value for key, value in data.items() if value not in (None, [])})
    for row in forecast or []:
        print(
            f"  {row['time'][5:16].replace('T', ' ')}  clouds {row['cloud_cover_pct']:>5}%  "
            f"humidity {row['humidity_pct']:>5}%  {row['temperature_c']:>5}°C  wind {row['wind_speed_kmh']} km/h"
        )


def _env_float(name: str) -> float | None:
    value = os.environ.get(name)
    return float(value) if value else None
