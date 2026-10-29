from dataclasses import dataclass

import numpy as np
import sep

from .background import BackgroundModel
from .errors import AnalysisError

sep.set_extract_pixstack(2_000_000)
sep.set_sub_object_limit(4096)

FWHM_FACTOR = 2.0 * np.sqrt(np.log(2.0))


@dataclass(frozen=True)
class DetectionConfig:
    threshold: float = 5.0
    min_area: int = 5
    max_fwhm: float = 25.0
    saturation_level: float = 0.98


@dataclass(frozen=True)
class StarCatalog:
    x: np.ndarray
    y: np.ndarray
    flux: np.ndarray
    peak: np.ndarray
    fwhm: np.ndarray
    elongation: np.ndarray
    saturated_count: int

    @property
    def count(self) -> int:
        return int(self.x.size)

    @property
    def median_fwhm(self) -> float | None:
        return float(np.median(self.fwhm)) if self.count else None

    @property
    def median_elongation(self) -> float | None:
        return float(np.median(self.elongation)) if self.count else None

    def to_dict(self) -> dict[str, float | int | None]:
        return {
            "count": self.count,
            "saturated_count": self.saturated_count,
            "median_fwhm": self.median_fwhm,
            "median_elongation": self.median_elongation,
        }


def detect_stars(data: np.ndarray, background: BackgroundModel, config: DetectionConfig = DetectionConfig()) -> StarCatalog:
    residual = background.subtract(data)
    try:
        sources = sep.extract(residual, config.threshold, err=background.rms, minarea=config.min_area)
    except Exception as error:
        raise AnalysisError(f"Star extraction failed: {error}") from error
    sources = sources[((sources["flag"] & ~sep.OBJ_MERGED) == 0) & (sources["b"] > 0)]
    fwhm = FWHM_FACTOR * np.sqrt(sources["a"] ** 2 + sources["b"] ** 2)
    elongation = sources["a"] / sources["b"]
    saturated = sources["peak"] + background.level >= config.saturation_level
    keep = (fwhm <= config.max_fwhm) & ~saturated
    return StarCatalog(
        x=sources["x"][keep],
        y=sources["y"][keep],
        flux=sources["flux"][keep],
        peak=sources["peak"][keep],
        fwhm=fwhm[keep],
        elongation=elongation[keep],
        saturated_count=int(saturated.sum()),
    )
