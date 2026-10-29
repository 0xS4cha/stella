import gphoto2 as gp


class FakeWidget:
    def __init__(self, name, widget_type, value=None, choices=(), value_range=None, readonly=False, children=()):
        self.name = name
        self.type = widget_type
        self.value = value
        self.choices = list(choices)
        self.value_range = value_range
        self.readonly = readonly
        self.children = list(children)

    def get_name(self):
        return self.name

    def get_label(self):
        return self.name.title()

    def get_type(self):
        return self.type

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    def get_readonly(self):
        return int(self.readonly)

    def count_choices(self):
        return len(self.choices)

    def get_choice(self, index):
        return self.choices[index]

    def get_range(self):
        return self.value_range

    def count_children(self):
        return len(self.children)

    def get_child(self, index):
        return self.children[index]

    def get_child_by_name(self, name):
        for child in self.children:
            if child.name == name:
                return child
            if child.children:
                try:
                    return child.get_child_by_name(name)
                except gp.GPhoto2Error:
                    pass
        raise gp.GPhoto2Error(gp.GP_ERROR_BAD_PARAMETERS)


def build_tree():
    return FakeWidget(
        "main",
        gp.GP_WIDGET_WINDOW,
        children=[
            FakeWidget(
                "capturesettings",
                gp.GP_WIDGET_SECTION,
                children=[
                    FakeWidget("iso", gp.GP_WIDGET_RADIO, "400", choices=["100", "400", "800", "1600"]),
                    FakeWidget("shutterspeed", gp.GP_WIDGET_RADIO, "1/60", choices=["1/60", "1", "30"]),
                    FakeWidget("imagequality", gp.GP_WIDGET_RADIO, "JPEG Fine", choices=["JPEG Fine", "NEF (Raw)"]),
                    FakeWidget("whitebalance", gp.GP_WIDGET_RADIO, "Auto", choices=["Auto", "Daylight"]),
                    FakeWidget("expprogram", gp.GP_WIDGET_RADIO, "M", choices=["M", "A"], readonly=True),
                    FakeWidget("exposurecompensation", gp.GP_WIDGET_RANGE, 0.0, value_range=(-5.0, 5.0, 0.3)),
                    FakeWidget("longexpnr", gp.GP_WIDGET_TOGGLE, 0),
                    FakeWidget("artist", gp.GP_WIDGET_TEXT, ""),
                ],
            )
        ],
    )


class FakeFilePath:
    def __init__(self, folder, name):
        self.folder = folder
        self.name = name


class FakeCameraFile:
    def __init__(self, name):
        self.name = name

    def save(self, target):
        with open(target, "w") as handle:
            handle.write(self.name)


class FakeCamera:
    def __init__(self, tree=None, extra_files=()):
        self.tree = tree or build_tree()
        self.extra_files = list(extra_files)
        self.pending = []
        self.writes = 0
        self.captures = 0
        self.initialized = False

    def init(self, context):
        self.initialized = True

    def exit(self, context):
        self.initialized = False

    def get_config(self, context):
        return self.tree

    def set_config(self, tree, context):
        self.writes += 1
        self.tree = tree

    def capture(self, kind, context):
        self.captures += 1
        self.pending = list(self.extra_files)
        return FakeFilePath("/store_00010001/DCIM/100NCD60", f"DSC_{self.captures:04d}.JPG")

    def wait_for_event(self, timeout, context):
        if self.pending:
            name = self.pending.pop(0)
            return gp.GP_EVENT_FILE_ADDED, FakeFilePath("/store_00010001/DCIM/100NCD60", name)
        return gp.GP_EVENT_TIMEOUT, None

    def file_get(self, folder, name, kind, context):
        return FakeCameraFile(name)


class FakeManager:
    def __init__(self, camera=None):
        self.camera = camera or FakeCamera()
        self.context = object()

    def connect(self):
        self.camera.init(self.context)

    def disconnect(self):
        self.camera.exit(self.context)

    def get_camera(self):
        return self.camera
