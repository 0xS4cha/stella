import json

import numpy as np
import pytest
from PIL import Image

from stella.cli import build_parser, main


def test_settings_set_parses_assignments():
    args = build_parser().parse_args(["settings", "set", "iso=1600", "shutterspeed=30"])
    assert args.assignments == [("iso", "1600"), ("shutterspeed", "30")]


def test_settings_set_rejects_malformed_assignment():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["settings", "set", "iso"])


def test_profile_list_runs_without_camera(capsys):
    assert main(["profile", "list"]) == 0
    assert "astro-d60" in capsys.readouterr().out


def test_analyze_outputs_json(tmp_path, capsys):
    path = tmp_path / "frame.png"
    Image.fromarray(np.full((64, 64), 20, dtype=np.uint8)).save(path)
    assert main(["analyze", "--json", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)[0]["metrics"]["star_count"] == 0


def test_env_requires_location(monkeypatch, capsys):
    monkeypatch.delenv("STELLA_LATITUDE", raising=False)
    monkeypatch.delenv("STELLA_LONGITUDE", raising=False)
    assert main(["env", "now", "--offline"]) == 1
    assert "Location required" in capsys.readouterr().err


def test_analysis_errors_are_reported(tmp_path, capsys):
    assert main(["analyze", str(tmp_path / "missing.nef")]) == 1
    assert "Image not found" in capsys.readouterr().err
