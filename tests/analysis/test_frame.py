import numpy as np
import pytest
from PIL import Image
from PIL.TiffImagePlugin import IFDRational

from stella.analysis import AnalysisError, analyze_image, load_frame, srgb_to_linear

from .synthetic import star_field

EXIF_IFD = 0x8769


def save_jpeg(path, data):
    image = Image.fromarray((np.clip(data, 0, 1) * 255).astype(np.uint8))
    exif = Image.Exif()
    exif[0x0110] = "NIKON D60"
    exif_ifd = exif.get_ifd(EXIF_IFD)
    exif_ifd[0x8827] = 1600
    exif_ifd[0x829A] = IFDRational(30, 1)
    exif_ifd[0x829D] = IFDRational(35, 10)
    exif_ifd[0x920A] = IFDRational(18, 1)
    exif_ifd[0x9003] = "2026:10:29 23:15:00"
    image.save(path, exif=exif, quality=95)


def test_png_is_linearised(tmp_path):
    path = tmp_path / "grey.png"
    Image.fromarray(np.full((10, 10), 128, dtype=np.uint8)).save(path)
    frame = load_frame(path)
    assert not frame.raw
    assert frame.data.shape == (10, 10)
    assert float(frame.data.mean()) == pytest.approx(float(srgb_to_linear(np.array(128 / 255))), rel=1e-3)


def test_jpeg_exif_is_read(tmp_path):
    path = tmp_path / "shot.jpg"
    save_jpeg(path, star_field() ** (1 / 2.2))
    exposure = load_frame(path).exposure
    assert exposure.camera_model == "NIKON D60"
    assert exposure.iso == 1600
    assert exposure.exposure_time == 30.0
    assert exposure.f_number == 3.5
    assert exposure.taken_at.hour == 23


def test_full_pipeline(tmp_path):
    path = tmp_path / "shot.jpg"
    save_jpeg(path, star_field() ** (1 / 2.2))
    result = analyze_image(path).to_dict()
    assert result["metrics"]["star_count"] > 100
    assert 0 < result["score"]["total"] <= 1


def test_missing_file(tmp_path):
    with pytest.raises(AnalysisError):
        load_frame(tmp_path / "missing.nef")
