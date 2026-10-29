import argparse
import sys

from ..camera import CameraController, CameraError
from .commands import COMMANDS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stella", description="Astrophotography automation for the Nikon D60")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in COMMANDS:
        command.register(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if not getattr(args, "needs_camera", True):
            args.handler(args, None)
            return 0
        with CameraController() as controller:
            args.handler(args, controller)
    except (CameraError, OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0
