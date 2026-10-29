from pathlib import Path

from ...analysis import AnalysisConfig, analyze_image
from ..output import print_mapping, to_json


def register(subparsers) -> None:
    parser = subparsers.add_parser("analyze", help="Measure star quality of captured images")
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--full-size", action="store_true", help="Decode RAW files at full resolution")
    parser.add_argument("--json", action="store_true")
    parser.set_defaults(handler=analyze, needs_camera=False)


def analyze(args, controller: None) -> None:
    config = AnalysisConfig(half_size=not args.full_size)
    results = [analyze_image(path, config).to_dict() for path in args.images]
    if args.json:
        print(to_json(results))
        return
    for result in results:
        print(result.pop("source"))
        print_mapping(result, indent=2)
