from dataclasses import asdict, dataclass

import numpy as np

from .background import BackgroundModel
from .frame import Frame
from .stars import StarCatalog

SATURATION_LEVEL = 0.98


@dataclass(frozen=True)
class ImageMetrics:
    background_level: float
    background_rms: float
    background_gradient: float
    star_count: int
    star_density: float
    median_fwhm: float | None
    median_elongation: float | None
    snr: float | None
    saturated_fraction: float
    saturated_stars: int

    def to_dict(self) -> dict[str, float | int | None]:
        return asdict(self)


def compute_metrics(frame: Frame, background: BackgroundModel, stars: StarCatalog) -> ImageMetrics:
    median_fwhm = stars.median_fwhm * frame.binning if stars.median_fwhm is not None else None
    snr = float(np.median(stars.peak) / background.rms) if stars.count and background.rms > 0 else None
    return ImageMetrics(
        background_level=background.level,
        background_rms=background.rms,
        background_gradient=background.gradient,
        star_count=stars.count,
        star_density=stars.count / frame.native_megapixels,
        median_fwhm=median_fwhm,
        median_elongation=stars.median_elongation,
        snr=snr,
        saturated_fraction=float(np.mean(frame.data >= SATURATION_LEVEL)),
        saturated_stars=stars.saturated_count,
    )
