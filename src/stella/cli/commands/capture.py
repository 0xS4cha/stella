from pathlib import Path

from ...camera import CameraController, CaptureSession


def register(subparsers) -> None:
    parser = subparsers.add_parser("capture", help="Capture one or more images")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--interval", type=float, default=0.0, help="Seconds between shot starts")
    parser.add_argument("--output", type=Path, default=Path("captures"))
    parser.set_defaults(handler=capture)


def capture(args, controller: CameraController) -> None:
    session = CaptureSession(controller, args.output)
    for result in session.series(args.count, args.interval):
        for path in result.local_paths:
            print(path)
    print(f"Manifest: {session.manifest}")
