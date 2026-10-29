from dataclasses import asdict, dataclass

from .errors import EnvironmentDataError


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
    elevation_m: float = 0.0

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise EnvironmentDataError(f"Latitude out of range: {self.latitude}")
        if not -180.0 <= self.longitude <= 180.0:
            raise EnvironmentDataError(f"Longitude out of range: {self.longitude}")

    def to_dict(self) -> dict[str, float]:
        return asdict(self)
