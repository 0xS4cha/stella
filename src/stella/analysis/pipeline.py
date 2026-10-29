from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .background import estimate_background
from .frame import ExposureInfo, load_frame
from .metrics import ImageMetrics, compute_metrics
from .scoring import QualityScore, ScoringTargets, ScoringWeights, score
from .stars import DetectionConfig, detect_stars


@dataclass(frozen=True)
class AnalysisConfig:
    half_size: bool = True
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    targets: ScoringTargets = field(default_factory=ScoringTargets)
    weights: ScoringWeights = field(default_factory=ScoringWeights)


@dataclass(frozen=True)
class ImageAnalysis:
    source: Path
    exposure: ExposureInfo
    metrics: ImageMetrics
    score: QualityScore

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": str(self.source),
            "exposure": self.exposure.to_dict(),
            "metrics": self.metrics.to_dict(),
            "score": self.score.to_dict(),
        }


def analyze_image(path: Path, config: AnalysisConfig = AnalysisConfig()) -> ImageAnalysis:
    frame = load_frame(path, half_size=config.half_size)
    background = estimate_background(frame.data)
    stars = detect_stars(frame.data, background, config.detection)
    metrics = compute_metrics(frame, background, stars)
    return ImageAnalysis(path, frame.exposure, metrics, score(metrics, config.targets, config.weights))
