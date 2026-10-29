import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

from .config import CameraConfig
from .errors import CameraError

PRESETS_PACKAGE = "stella.camera.presets"


class ProfileError(CameraError):
    pass


@dataclass(frozen=True)
class Profile:
    name: str
    settings: dict[str, Any]
    description: str = ""
    requires: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Profile":
        if "name" not in data or "settings" not in data:
            raise ProfileError("A profile needs at least a name and settings")
        return cls(
            name=data["name"],
            settings=dict(data["settings"]),
            description=data.get("description", ""),
            requires=dict(data.get("requires", {})),
        )

    @classmethod
    def from_file(cls, path: Path) -> "Profile":
        data = json.loads(path.read_text())
        if "settings" not in data and "name" not in data:
            data = {"name": path.stem, "settings": data}
        return cls.from_dict(data)

    def merged(self, overrides: Mapping[str, Any]) -> "Profile":
        return Profile(self.name, {**self.settings, **overrides}, self.description, self.requires)


def builtin_profiles() -> dict[str, Profile]:
    profiles = {}
    for entry in resources.files(PRESETS_PACKAGE).iterdir():
        if entry.name.endswith(".json"):
            profile = Profile.from_dict(json.loads(entry.read_text()))
            profiles[profile.name] = profile
    return profiles


def resolve_profile(reference: str) -> Profile:
    path = Path(reference)
    if path.suffix == ".json" and path.exists():
        return Profile.from_file(path)
    profiles = builtin_profiles()
    if reference not in profiles:
        raise ProfileError(f"Unknown profile {reference!r}; available: {sorted(profiles)}")
    return profiles[reference]


def check_requirements(config: CameraConfig, profile: Profile) -> None:
    for name, expected in profile.requires.items():
        actual = config.get(name).value
        if str(actual).lower() != str(expected).lower():
            raise ProfileError(f"Profile {profile.name} requires {name}={expected}, camera reports {actual}")


def apply_profile(config: CameraConfig, profile: Profile) -> dict[str, Any]:
    check_requirements(config, profile)
    return config.apply(profile.settings)
