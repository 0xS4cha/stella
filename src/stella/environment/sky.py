from dataclasses import asdict, dataclass

from .errors import EnvironmentDataError

BORTLE_SQM_LOWER_BOUNDS = {
    1: 21.99,
    2: 21.89,
    3: 21.69,
    4: 20.49,
    5: 19.50,
    6: 18.94,
    7: 18.38,
    8: 17.80,
    9: 0.0,
}
BORTLE_TYPICAL_SQM = {1: 22.0, 2: 21.94, 3: 21.79, 4: 21.09, 5: 20.0, 6: 19.22, 7: 18.66, 8: 18.09, 9: 17.5}


@dataclass(frozen=True)
class SkyQuality:
    bortle: int
    sqm: float

    @classmethod
    def from_bortle(cls, bortle: int) -> "SkyQuality":
        if bortle not in BORTLE_TYPICAL_SQM:
            raise EnvironmentDataError(f"Bortle class must be between 1 and 9, got {bortle}")
        return cls(bortle, BORTLE_TYPICAL_SQM[bortle])

    @classmethod
    def from_sqm(cls, sqm: float) -> "SkyQuality":
        if not 0.0 < sqm < 23.0:
            raise EnvironmentDataError(f"SQM must be a sky brightness in mag/arcsec², got {sqm}")
        bortle = next(level for level, bound in BORTLE_SQM_LOWER_BOUNDS.items() if sqm >= bound)
        return cls(bortle, sqm)

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)
