import numpy as np

from stella.analysis import ExposureInfo, Frame


def star_field(
    count=150,
    shape=(600, 900),
    background=0.05,
    noise=0.004,
    sigma=(1.5, 1.5),
    seed=0,
):
    rng = np.random.default_rng(seed)
    height, width = shape
    data = np.full(shape, background, dtype=np.float64) + rng.normal(0, noise, shape)
    yy, xx = np.mgrid[0:height, 0:width]
    sigma_x, sigma_y = sigma
    for _ in range(count):
        x, y = rng.uniform(25, width - 25), rng.uniform(25, height - 25)
        amplitude = rng.uniform(0.1, 0.4)
        data += amplitude * np.exp(-((xx - x) ** 2 / (2 * sigma_x**2) + (yy - y) ** 2 / (2 * sigma_y**2)))
    return np.clip(data, 0, 1).astype(np.float32)


def as_frame(data, binning=1):
    return Frame(source=None, data=data, raw=False, binning=binning, exposure=ExposureInfo())
