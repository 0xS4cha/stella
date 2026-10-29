import math
from dataclasses import dataclass

FULL_FRAME_DIAGONAL_MM = math.hypot(36.0, 24.0)


@dataclass(frozen=True)
class CameraBody:
    name: str
    sensor_width_mm: float
    sensor_height_mm: float
    width_px: int
    height_px: int
    max_exposure_s: float
    iso_range: tuple[int, int]

    @property
    def pixel_pitch_um(self) -> float:
        return self.sensor_width_mm * 1000.0 / self.width_px

    @property
    def crop_factor(self) -> float:
        return FULL_FRAME_DIAGONAL_MM / math.hypot(self.sensor_width_mm, self.sensor_height_mm)


@dataclass(frozen=True)
class Lens:
    focal_length_mm: float
    max_aperture: float


@dataclass(frozen=True)
class ExposureLimits:
    rule_500_s: float
    npf_s: float
    recommended_s: float

    def to_dict(self) -> dict[str, float]:
        return {"rule_500_s": self.rule_500_s, "npf_s": self.npf_s, "recommended_s": self.recommended_s}


NIKON_D60 = CameraBody(
    name="Nikon D60",
    sensor_width_mm=23.6,
    sensor_height_mm=15.8,
    width_px=3872,
    height_px=2592,
    max_exposure_s=30.0,
    iso_range=(100, 3200),
)


def rule_500(body: CameraBody, lens: Lens) -> float:
    return 500.0 / (lens.focal_length_mm * body.crop_factor)


def npf_rule(body: CameraBody, lens: Lens, aperture: float | None = None, declination_deg: float = 0.0) -> float:
    f_number = aperture or lens.max_aperture
    seconds = (35.0 * f_number + 30.0 * body.pixel_pitch_um) / lens.focal_length_mm
    return seconds / max(math.cos(math.radians(declination_deg)), 1e-3)


def exposure_limits(
    body: CameraBody, lens: Lens, aperture: float | None = None, declination_deg: float = 0.0
) -> ExposureLimits:
    npf = npf_rule(body, lens, aperture, declination_deg)
    return ExposureLimits(
        rule_500_s=round(rule_500(body, lens), 2),
        npf_s=round(npf, 2),
        recommended_s=round(min(npf, body.max_exposure_s), 2),
    )
