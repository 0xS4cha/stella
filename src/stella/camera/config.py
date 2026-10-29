from collections.abc import Iterator, Mapping
from typing import Any

import gphoto2 as gp

from .errors import ReadOnlySettingError, SettingNotFoundError
from .manager import CameraManager
from .settings import Setting, WidgetType

CONTAINER_TYPES = {WidgetType.WINDOW, WidgetType.SECTION}


class CameraConfig:
    def __init__(self, manager: CameraManager):
        self.manager = manager

    def get(self, name: str) -> Setting:
        return Setting.from_widget(self._find(self._read_tree(), name))

    def list(self) -> dict[str, Setting]:
        return {setting.name: setting for setting in self._iter_settings(self._read_tree())}

    def apply(self, values: Mapping[str, Any]) -> dict[str, Any]:
        tree = self._read_tree()
        staged = []
        for name, value in values.items():
            widget = self._find(tree, name)
            setting = Setting.from_widget(widget)
            if setting.readonly:
                raise ReadOnlySettingError(name)
            staged.append((widget, setting.name, setting.coerce(value)))
        if not staged:
            return {}
        for widget, _, coerced in staged:
            widget.set_value(coerced)
        self.manager.get_camera().set_config(tree, self.manager.context)
        return {name: coerced for _, name, coerced in staged}

    def set(self, name: str, value: Any) -> Any:
        return self.apply({name: value})[name]

    def _read_tree(self):
        return self.manager.get_camera().get_config(self.manager.context)

    @staticmethod
    def _find(tree, name: str):
        try:
            return tree.get_child_by_name(name)
        except gp.GPhoto2Error:
            raise SettingNotFoundError(name) from None

    @classmethod
    def _iter_settings(cls, node) -> Iterator[Setting]:
        if WidgetType(node.get_type()) in CONTAINER_TYPES:
            for index in range(node.count_children()):
                yield from cls._iter_settings(node.get_child(index))
        else:
            yield Setting.from_widget(node)
