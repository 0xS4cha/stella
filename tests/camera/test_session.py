import json

from stella.camera import CaptureSession


def test_capture_downloads_all_files(controller, tmp_path):
    result = controller.capture(download_dir=tmp_path)
    assert [path.name for path in result.local_paths] == ["DSC_0001.JPG", "DSC_0001.NEF"]
    assert all(path.exists() for path in result.local_paths)


def test_series_writes_manifest_and_respects_interval(controller, tmp_path):
    sleeps = []
    session = CaptureSession(controller, tmp_path, sleep=sleeps.append, clock=lambda: 0.0)
    results = list(session.series(3, interval=10, metadata={"target": "milky-way"}))
    entries = [json.loads(line) for line in session.manifest.read_text().splitlines()]
    assert len(results) == 3
    assert sleeps == [10, 10]
    assert entries[0]["settings"]["iso"] == "400"
    assert entries[2]["metadata"] == {"target": "milky-way", "series_index": 2}
    assert entries[0]["files"] == ["DSC_0001.JPG", "DSC_0001.NEF"]
