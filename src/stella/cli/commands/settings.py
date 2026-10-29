import argparse
import json
from pathlib import Path

from ...camera import CameraController
from ..output import print_mapping, to_json


def register(subparsers) -> None:
    parser = subparsers.add_parser("settings", help="Inspect and change camera settings")
    actions = parser.add_subparsers(dest="action", required=True)

    list_parser = actions.add_parser("list", help="List every camera setting")
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(handler=list_settings)

    get_parser = actions.add_parser("get", help="Show a setting with its allowed values")
    get_parser.add_argument("name")
    get_parser.add_argument("--json", action="store_true")
    get_parser.set_defaults(handler=get_setting)

    set_parser = actions.add_parser("set", help="Set one or more settings in a single write")
    set_parser.add_argument("assignments", nargs="+", metavar="NAME=VALUE", type=parse_assignment)
    set_parser.set_defaults(handler=set_settings)

    load_parser = actions.add_parser("load", help="Apply settings from a JSON file")
    load_parser.add_argument("file", type=Path)
    load_parser.set_defaults(handler=load_settings)


def parse_assignment(raw: str) -> tuple[str, str]:
    name, separator, value = raw.partition("=")
    if not separator or not name:
        raise argparse.ArgumentTypeError(f"expected NAME=VALUE, got {raw!r}")
    return name, value


def list_settings(args, controller: CameraController) -> None:
    settings = controller.config.list()
    if args.json:
        print(to_json([setting.to_dict() for setting in settings.values()]))
    else:
        print_mapping({name: setting.value for name, setting in settings.items()})


def get_setting(args, controller: CameraController) -> None:
    setting = controller.config.get(args.name).to_dict()
    if args.json:
        print(to_json(setting))
    else:
        print_mapping(setting)


def set_settings(args, controller: CameraController) -> None:
    print_mapping(controller.config.apply(dict(args.assignments)))


def load_settings(args, controller: CameraController) -> None:
    print_mapping(controller.config.apply(json.loads(args.file.read_text())))
