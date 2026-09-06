import gphoto2 as gp

class CameraManager:
    def __init__(self):
        self.camera = None
        self.context = gp.Context()

    def connect(self):
        if self.camera is None:
            self.camera = gp.Camera()
            self.camera.init(self.context)

    def disconnect(self):
        if self.camera is not None:
            self.camera.exit(self.context)
            self.camera = None

    def get_camera(self):
        if self.camera is None:
            self.connect()
        return self.camera
