import os
import gphoto2 as gp
from .manager import CameraManager
from .config import CameraConfig

class CameraController:
    def __init__(self):
        self.manager = CameraManager()
        self.config = CameraConfig(self.manager)

    def connect(self):
        self.manager.connect()

    def disconnect(self):
        self.manager.disconnect()

    def capture_image(self, download=True, target_path="."):
        camera = self.manager.get_camera()
        file_path = camera.capture(gp.GP_CAPTURE_IMAGE)
        
        if download:
            target_file = os.path.join(target_path, file_path.name)
            camera_file = camera.file_get(
                file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
            camera_file.save(target_file)
            return target_file
        
        return file_path.name

    def get_all_settings(self):
        return self.config.list_all_parameters()

    def get_setting(self, name):
        return self.config.get_parameter(name)

    def set_setting(self, name, value):
        self.config.set_parameter(name, value)
