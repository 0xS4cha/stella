import gphoto2 as gp

from .errors import CameraConnectionError

MACOS_HINT = "on macOS, quit any app using the camera or run `killall PTPCamera`"


class CameraManager:
    def __init__(self, backend=gp):
        self._backend = backend
        self._camera = None
        self.context = backend.Context()

    @property
    def connected(self) -> bool:
        return self._camera is not None

    def connect(self) -> None:
        if self._camera is not None:
            return
        camera = self._backend.Camera()
        try:
            camera.init(self.context)
        except self._backend.GPhoto2Error as error:
            raise CameraConnectionError(f"Unable to connect to camera ({error}); {MACOS_HINT}") from error
        self._camera = camera

    def disconnect(self) -> None:
        if self._camera is None:
            return
        try:
            self._camera.exit(self.context)
        finally:
            self._camera = None

    def get_camera(self):
        self.connect()
        return self._camera

    def __enter__(self) -> "CameraManager":
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        self.disconnect()
