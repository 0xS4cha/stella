import json

import pytest

from stella.camera import ProfileError, apply_profile, builtin_profiles, resolve_profile


def test_builtin_astro_profile_applies(controller, camera):
    profile = builtin_profiles()["astro-d60"]
    applied = apply_profile(controller.config, profile)
    assert applied["imagequality"] == "NEF (Raw)"
    assert camera.writes == 1


def test_requirements_are_checked(controller, camera):
    camera.tree.get_child_by_name("expprogram").value = "A"
    profile = resolve_profile("astro-d60")
    with pytest.raises(ProfileError, match="requires expprogram=M"):
        apply_profile(controller.config, profile)


def test_profile_from_plain_settings_file(tmp_path):
    path = tmp_path / "night.json"
    path.write_text(json.dumps({"iso": "800"}))
    profile = resolve_profile(str(path))
    assert profile.name == "night"
    assert profile.settings == {"iso": "800"}


def test_overrides(controller):
    profile = resolve_profile("astro-d60").merged({"iso": "800"})
    assert apply_profile(controller.config, profile)["iso"] == "800"


def test_unknown_profile():
    with pytest.raises(ProfileError):
        resolve_profile("missing")
