import pytest

from stella.camera import CameraController

from .fakes import FakeCamera, FakeManager


@pytest.fixture
def camera():
    return FakeCamera(extra_files=["DSC_0001.NEF"])


@pytest.fixture
def controller(camera):
    return CameraController(FakeManager(camera))
