from dataclasses import asdict, dataclass
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

import exifread
import numpy as np
import rawpy
from PIL import Image

from .errors import AnalysisError

RAW_SUFFIXES = {".nef", ".nrw", ".cr2", ".cr3", ".arw", ".dng", ".raf", ".orf", ".rw2"}
LUMINANCE_WEIGHTS = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"


@dataclass(frozen=True)
class ExposureInfo:
    camera_model: str | None = None
    iso: int | None = None
    exposure_time: float | None = None
    f_number: float | None = None
    focal_length: float | None = None
    taken_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Frame:
    source: Path
    data: np.ndarray
    raw: bool
    binning: int
    exposure: ExposureInfo

    @property
    def native_megapixels(self) -> float:
        height, width = self.data.shape
        return height * width * self.binning**2 / 1e6


def load_frame(path: Path, half_size: bool = True) -> Frame:
    if not path.exists():
        raise AnalysisError(f"Image not found: {path}")
    exposure = read_exposure(path)
    if path.suffix.lower() in RAW_SUFFIXES:
        return Frame(path, _load_raw(path, half_size), True, 2 if half_size else 1, exposure)
    return Frame(path, _load_rendered(path), False, 1, exposure)


def read_exposure(path: Path) -> ExposureInfo:
    with path.open("rb") as handle:
        tags = exifread.process_file(handle, details=False)
    return ExposureInfo(
        camera_model=_text(tags.get("Image Model")),
        iso=_integer(tags.get("EXIF ISOSpeedRatings")),
        exposure_time=_number(tags.get("EXIF ExposureTime")),
        f_number=_number(tags.get("EXIF FNumber")),
        focal_length=_number(tags.get("EXIF FocalLength")),
        taken_at=_timestamp(tags.get("EXIF DateTimeOriginal")),
    )


def luminance(rgb: np.ndarray) -> np.ndarray:
    return np.ascontiguousarray(rgb[..., :3] @ LUMINANCE_WEIGHTS, dtype=np.float32)


def srgb_to_linear(values: np.ndarray) -> np.ndarray:
    return np.where(values <= 0.04045, values / 12.92, ((values + 0.055) / 1.055) ** 2.4).astype(np.float32)


def _load_raw(path: Path, half_size: bool) -> np.ndarray:
    try:
        with rawpy.imread(str(path)) as raw:
            rgb = raw.postprocess(
                gamma=(1, 1),
                no_auto_bright=True,
                output_bps=16,
                use_camera_wb=True,
                half_size=half_size,
                user_flip=0,
            )
    except rawpy.LibRawError as error:
        raise AnalysisError(f"Unable to decode RAW file {path}: {error}") from error
    return luminance(rgb.astype(np.float32) / 65535.0)


def _load_rendered(path: Path) -> np.ndarray:
    try:
        with Image.open(path) as image:
            rgb = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    except OSError as error:
        raise AnalysisError(f"Unable to decode image {path}: {error}") from error
    return luminance(srgb_to_linear(rgb))


def _first_value(tag):
    if tag is None or not getattr(tag, "values", None):
        return None
    return tag.values[0] if isinstance(tag.values, list) else tag.values


def _number(tag) -> float | None:
    value = _first_value(tag)
    if value is None:
        return None
    try:
        return float(Fraction(value.num, value.den)) if hasattr(value, "den") else float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _integer(tag) -> int | None:
    number = _number(tag)
    return int(number) if number is not None else None


def _text(tag) -> str | None:
    return str(tag).strip() if tag is not None else None


def _timestamp(tag) -> datetime | None:
    try:
        return datetime.strptime(str(tag), EXIF_DATETIME_FORMAT) if tag is not None else None
    except ValueError:
        return None
