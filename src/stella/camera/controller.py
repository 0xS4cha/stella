from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import gphoto2 as gp

from .config import CameraConfig
from .manager import CameraManager

EVENT_TIMEOUT_MS = 1500


@dataclass(frozen=True)
class CameraFile:
    folder: str
    name: str

    @property
    def path(self) -> str:
        return f"{self.folder.rstrip('/')}/{self.name}"


@dataclass(frozen=True)
class CaptureResult:
    captured_at: datetime
    files: tuple[CameraFile, ...]
    local_paths: tuple[Path, ...] = ()


class CameraController:
    def __init__(self, manager: CameraManager | None = None):
        self.manager = manager or CameraManager()
        self.config = CameraConfig(self.manager)

    def connect(self) -> None:
        self.manager.connect()

    def disconnect(self) -> None:
        self.manager.disconnect()

    def capture(self, download_dir: Path | None = None) -> CaptureResult:
        camera = self.manager.get_camera()
        captured_at = datetime.now(timezone.utc)
        primary = camera.capture(gp.GP_CAPTURE_IMAGE, self.manager.context)
        files = (CameraFile(primary.folder, primary.name), *self._collect_added_files(camera))
        local_paths = tuple(self.download(file, download_dir) for file in files) if download_dir else ()
        return CaptureResult(captured_at, files, local_paths)

    def download(self, file: CameraFile, target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / file.name
        camera_file = self.manager.get_camera().file_get(
            file.folder, file.name, gp.GP_FILE_TYPE_NORMAL, self.manager.context
        )
        camera_file.save(str(target))
        return target

    def _collect_added_files(self, camera) -> list[CameraFile]:
        files = []
        while True:
            event_type, data = camera.wait_for_event(EVENT_TIMEOUT_MS, self.manager.context)
            if event_type == gp.GP_EVENT_TIMEOUT:
                return files
            if event_type == gp.GP_EVENT_FILE_ADDED:
                files.append(CameraFile(data.folder, data.name))

    def __enter__(self) -> "CameraController":
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        self.disconnect()
