from ...camera import CameraController, apply_profile, builtin_profiles, resolve_profile
from ..output import print_mapping
from .settings import parse_assignment


def register(subparsers) -> None:
    parser = subparsers.add_parser("profile", help="Manage camera profiles")
    actions = parser.add_subparsers(dest="action", required=True)

    list_parser = actions.add_parser("list", help="List built-in profiles")
    list_parser.set_defaults(handler=list_profiles, needs_camera=False)

    apply_parser = actions.add_parser("apply", help="Apply a built-in profile or a JSON profile file")
    apply_parser.add_argument("profile")
    apply_parser.add_argument("--override", nargs="*", default=[], metavar="NAME=VALUE", type=parse_assignment)
    apply_parser.set_defaults(handler=apply)


def list_profiles(args, controller: None) -> None:
    for profile in builtin_profiles().values():
        print(f"{profile.name}  {profile.description}")


def apply(args, controller: CameraController) -> None:
    profile = resolve_profile(args.profile).merged(dict(args.override))
    print_mapping(apply_profile(controller.config, profile))
