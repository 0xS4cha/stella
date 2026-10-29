from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import gphoto2 as gp

from .errors import InvalidSettingValueError

TRUE_VALUES = {"1", "true", "on", "yes"}
FALSE_VALUES = {"0", "false", "off", "no"}


class WidgetType(Enum):
    WINDOW = gp.GP_WIDGET_WINDOW
    SECTION = gp.GP_WIDGET_SECTION
    TEXT = gp.GP_WIDGET_TEXT
    RANGE = gp.GP_WIDGET_RANGE
    TOGGLE = gp.GP_WIDGET_TOGGLE
    RADIO = gp.GP_WIDGET_RADIO
    MENU = gp.GP_WIDGET_MENU
    BUTTON = gp.GP_WIDGET_BUTTON
    DATE = gp.GP_WIDGET_DATE


@dataclass(frozen=True)
class SettingRange:
    minimum: float
    maximum: float
    step: float


@dataclass(frozen=True)
class Setting:
    name: str
    label: str
    type: WidgetType
    value: Any
    readonly: bool
    choices: tuple[str, ...] = field(default_factory=tuple)
    range: SettingRange | None = None

    @classmethod
    def from_widget(cls, widget) -> "Setting":
        widget_type = WidgetType(widget.get_type())
        choices: tuple[str, ...] = ()
        value_range = None
        if widget_type in (WidgetType.RADIO, WidgetType.MENU):
            choices = tuple(widget.get_choice(i) for i in range(widget.count_choices()))
        if widget_type is WidgetType.RANGE:
            value_range = SettingRange(*widget.get_range())
        return cls(
            name=widget.get_name(),
            label=widget.get_label(),
            type=widget_type,
            value=widget.get_value(),
            readonly=bool(widget.get_readonly()),
            choices=choices,
            range=value_range,
        )

    def coerce(self, value: Any) -> Any:
        if self.type is WidgetType.TOGGLE:
            return self._coerce_toggle(value)
        if self.type is WidgetType.RANGE:
            return self._coerce_range(value)
        if self.type in (WidgetType.RADIO, WidgetType.MENU):
            return self._coerce_choice(value)
        if self.type is WidgetType.DATE:
            return self._coerce_int(value)
        if self.type is WidgetType.TEXT:
            return str(value)
        raise InvalidSettingValueError(self.name, value, f"{self.type.name.lower()} widgets cannot be set")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "label": self.label,
            "type": self.type.name.lower(),
            "value": self.value,
            "readonly": self.readonly,
        }
        if self.choices:
            data["choices"] = list(self.choices)
        if self.range:
            data["range"] = {"min": self.range.minimum, "max": self.range.maximum, "step": self.range.step}
        return data

    def _coerce_toggle(self, value: Any) -> int:
        if isinstance(value, bool):
            return int(value)
        normalized = str(value).strip().lower()
        if normalized in TRUE_VALUES:
            return 1
        if normalized in FALSE_VALUES:
            return 0
        raise InvalidSettingValueError(self.name, value, "expected a boolean")

    def _coerce_range(self, value: Any) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise InvalidSettingValueError(self.name, value, "expected a number") from None
        if self.range and not self.range.minimum <= number <= self.range.maximum:
            raise InvalidSettingValueError(
                self.name, value, f"must be between {self.range.minimum} and {self.range.maximum}"
            )
        return number

    def _coerce_choice(self, value: Any) -> str:
        candidate = str(value)
        if candidate in self.choices:
            return candidate
        matches = [choice for choice in self.choices if choice.lower() == candidate.lower()]
        if len(matches) == 1:
            return matches[0]
        raise InvalidSettingValueError(self.name, value, f"expected one of {list(self.choices)}")

    def _coerce_int(self, value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            raise InvalidSettingValueError(self.name, value, "expected an integer") from None
