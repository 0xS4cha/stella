from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll, Vertical
from textual.widgets import Header, Footer, Log, Button, Input, Label, Static
from textual import work
from ..camera.controller import CameraController

class SettingInput(Static):
    def __init__(self, name: str, value: str):
        super().__init__()
        self.setting_name = name
        self.setting_value = value

    def compose(self) -> ComposeResult:
        yield Label(self.setting_name)
        yield Input(value=str(self.setting_value), id=f"input_{self.setting_name.replace('-', '_')}")

class CameraApp(App):
    CSS = """
    #sidebar {
        width: 30%;
        border-right: solid green;
    }
    #main_area {
        width: 70%;
    }
    SettingInput {
        margin-bottom: 1;
    }
    Button {
        margin: 1;
        width: 100%;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "capture", "Capture Image"),
        ("r", "reload", "Reload Settings")
    ]

    def __init__(self):
        super().__init__()
        self.controller = CameraController()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with VerticalScroll(id="sidebar"):
                pass
            with Vertical(id="main_area"):
                yield Button("Capture Image", id="btn_capture", variant="primary")
                yield Log(id="status_log")
        yield Footer()

    def on_mount(self) -> None:
        self.log_message("Initializing camera connection...")
        self.connect_camera()

    @work(thread=True)
    def connect_camera(self):
        try:
            self.controller.connect()
            self.call_from_thread(self.log_message, "Camera connected successfully.")
            self.load_settings()
        except Exception as e:
            self.call_from_thread(self.log_message, f"Connection failed: {e}")

    @work(thread=True)
    def load_settings(self):
        self.call_from_thread(self.log_message, "Fetching settings...")
        try:
            settings = self.controller.get_all_settings()
            self.call_from_thread(self.populate_sidebar, settings)
            self.call_from_thread(self.log_message, "Settings loaded.")
        except Exception as e:
            self.call_from_thread(self.log_message, f"Failed to fetch settings: {e}")

    def populate_sidebar(self, settings):
        sidebar = self.query_one("#sidebar")
        for child in sidebar.children:
            child.remove()
        for name, value in settings.items():
            sidebar.mount(SettingInput(name, value))

    @work(thread=True)
    def capture_image(self):
        self.call_from_thread(self.log_message, "Capturing image...")
        try:
            result = self.controller.capture_image(download=True)
            self.call_from_thread(self.log_message, f"Image saved to: {result}")
        except Exception as e:
            self.call_from_thread(self.log_message, f"Capture failed: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_capture":
            self.capture_image()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        input_widget = event.input
        setting_name_id = input_widget.id.replace("input_", "")
        
        original_name = None
        for child in self.query_one("#sidebar").children:
            if hasattr(child, 'setting_name') and child.setting_name.replace('-', '_') == setting_name_id:
                original_name = child.setting_name
                break
                
        if original_name:
            new_value = input_widget.value
            self.apply_setting(original_name, new_value)

    @work(thread=True)
    def apply_setting(self, name, value):
        self.call_from_thread(self.log_message, f"Applying {name}={value}...")
        try:
            self.controller.set_setting(name, value)
            self.call_from_thread(self.log_message, f"Setting applied: {name}")
        except Exception as e:
            self.call_from_thread(self.log_message, f"Failed to set {name}: {e}")

    def action_capture(self) -> None:
        self.capture_image()

    def action_reload(self) -> None:
        self.load_settings()

    def log_message(self, message: str) -> None:
        status_log = self.query_one("#status_log", Log)
        status_log.write_line(message)

    def on_unmount(self) -> None:
        try:
            self.controller.disconnect()
        except:
            pass
