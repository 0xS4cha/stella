from dataclasses import dataclass, field

import numpy as np

from .metrics import ImageMetrics


@dataclass(frozen=True)
class ScoringTargets:
    star_density: float = 50.0
    fwhm: float = 3.0
    max_elongation: float = 2.0
    background_range: tuple[float, float] = (0.02, 0.12)
    snr: float = 50.0
    max_saturated_fraction: float = 0.005


@dataclass(frozen=True)
class ScoringWeights:
    stars: float = 0.25
    sharpness: float = 0.2
    roundness: float = 0.2
    exposure: float = 0.15
    signal: float = 0.15
    clipping: float = 0.05

    def as_dict(self) -> dict[str, float]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class QualityScore:
    total: float
    components: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, float | dict[str, float]]:
        return {"total": self.total, "components": self.components}


def score(metrics: ImageMetrics, targets: ScoringTargets = ScoringTargets(), weights: ScoringWeights = ScoringWeights()) -> QualityScore:
    components = {
        "stars": 1.0 - float(np.exp(-metrics.star_density / targets.star_density)),
        "sharpness": _sharpness(metrics.median_fwhm, targets.fwhm),
        "roundness": _roundness(metrics.median_elongation, targets.max_elongation),
        "exposure": _exposure(metrics.background_level, targets.background_range),
        "signal": _signal(metrics.snr, targets.snr),
        "clipping": _clip(1.0 - metrics.saturated_fraction / targets.max_saturated_fraction),
    }
    weight_map = weights.as_dict()
    total = sum(components[name] * weight_map[name] for name in components) / sum(weight_map.values())
    return QualityScore(round(total, 4), {name: round(value, 4) for name, value in components.items()})


def _clip(value: float) -> float:
    return float(min(1.0, max(0.0, value)))


def _sharpness(fwhm: float | None, target: float) -> float:
    return _clip(target / fwhm) if fwhm else 0.0


def _roundness(elongation: float | None, maximum: float) -> float:
    return _clip((maximum - elongation) / (maximum - 1.0)) if elongation else 0.0


def _exposure(level: float, bounds: tuple[float, float]) -> float:
    low, high = bounds
    if level < low:
        return _clip(level / low)
    if level > high:
        return _clip(1.0 - (level - high) / (1.0 - high) * 4)
    return 1.0


def _signal(snr: float | None, target: float) -> float:
    return _clip(np.log10(snr) / np.log10(target)) if snr and snr > 1 else 0.0
