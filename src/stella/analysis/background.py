from dataclasses import dataclass

import numpy as np
import sep

BOX_SIZE = 64
FILTER_SIZE = 3


@dataclass(frozen=True)
class BackgroundModel:
    level: float
    rms: float
    gradient: float
    surface: np.ndarray

    def subtract(self, data: np.ndarray) -> np.ndarray:
        return np.ascontiguousarray(data - self.surface, dtype=np.float32)

    def to_dict(self) -> dict[str, float]:
        return {"level": self.level, "rms": self.rms, "gradient": self.gradient}


def estimate_background(data: np.ndarray, box_size: int = BOX_SIZE) -> BackgroundModel:
    background = sep.Background(np.ascontiguousarray(data, dtype=np.float32), bw=box_size, bh=box_size, fw=FILTER_SIZE, fh=FILTER_SIZE)
    surface = background.back()
    low, high = np.percentile(surface, [5, 95])
    return BackgroundModel(
        level=float(background.globalback),
        rms=float(background.globalrms),
        gradient=float(high - low),
        surface=surface,
    )
