class CameraError(Exception):
    pass


class CameraConnectionError(CameraError):
    pass


class SettingNotFoundError(CameraError):
    def __init__(self, name: str):
        super().__init__(f"Unknown camera setting: {name}")
        self.name = name


class InvalidSettingValueError(CameraError):
    def __init__(self, name: str, value: object, reason: str):
        super().__init__(f"Invalid value {value!r} for {name}: {reason}")
        self.name = name
        self.value = value
        self.reason = reason


class ReadOnlySettingError(CameraError):
    def __init__(self, name: str):
        super().__init__(f"Camera setting is read-only: {name}")
        self.name = name
