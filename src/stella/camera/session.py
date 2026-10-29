import json
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .controller import CameraController, CaptureResult

MANIFEST_NAME = "manifest.jsonl"
TRACKED_SETTINGS = ("iso", "shutterspeed", "f-number", "imagequality", "whitebalance", "focallength")


@dataclass
class CaptureSession:
    controller: CameraController
    root: Path
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic

    @property
    def directory(self) -> Path:
        return self.root / self.started_at.strftime("%Y-%m-%dT%H-%M-%S")

    @property
    def manifest(self) -> Path:
        return self.directory / MANIFEST_NAME

    def shoot(self, metadata: dict[str, Any] | None = None) -> CaptureResult:
        settings = self._snapshot_settings()
        result = self.controller.capture(download_dir=self.directory)
        self._record(result, settings, metadata or {})
        return result

    def series(self, count: int, interval: float = 0.0, metadata: dict[str, Any] | None = None) -> Iterator[CaptureResult]:
        for index in range(count):
            started = self.clock()
            yield self.shoot({**(metadata or {}), "series_index": index})
            remaining = interval - (self.clock() - started)
            if index < count - 1 and remaining > 0:
                self.sleep(remaining)

    def _snapshot_settings(self) -> dict[str, Any]:
        available = self.controller.config.list()
        return {name: available[name].value for name in TRACKED_SETTINGS if name in available}

    def _record(self, result: CaptureResult, settings: dict[str, Any], metadata: dict[str, Any]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        entry = {
            "captured_at": result.captured_at.isoformat(),
            "files": [str(path.relative_to(self.directory)) for path in result.local_paths],
            "settings": settings,
            "metadata": metadata,
        }
        with self.manifest.open("a") as handle:
            handle.write(json.dumps(entry) + "\n")
