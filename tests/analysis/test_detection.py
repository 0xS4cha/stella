import pytest

from stella.analysis import compute_metrics, detect_stars, estimate_background, score

from .synthetic import as_frame, star_field


def analyze(data, binning=1):
    frame = as_frame(data, binning)
    background = estimate_background(frame.data)
    stars = detect_stars(frame.data, background)
    return background, stars, compute_metrics(frame, background, stars)


def test_background_is_recovered():
    background, _, _ = analyze(star_field(background=0.08, noise=0.005))
    assert background.level == pytest.approx(0.08, abs=0.005)
    assert background.rms == pytest.approx(0.005, rel=0.3)


def test_round_stars_are_detected():
    _, stars, metrics = analyze(star_field(count=150))
    assert 130 <= stars.count <= 160
    assert metrics.median_elongation < 1.2
    assert 2.0 < metrics.median_fwhm < 4.5


def test_trailed_stars_are_elongated():
    _, _, round_metrics = analyze(star_field(sigma=(1.5, 1.5)))
    _, _, trailed_metrics = analyze(star_field(sigma=(5.0, 1.5)))
    assert trailed_metrics.median_elongation > 2.0
    assert score(trailed_metrics).total < score(round_metrics).total
    assert score(trailed_metrics).components["roundness"] == 0.0


def test_binning_scales_fwhm_and_density():
    _, _, native = analyze(star_field(), binning=1)
    _, _, binned = analyze(star_field(), binning=2)
    assert binned.median_fwhm == pytest.approx(2 * native.median_fwhm)
    assert binned.star_density == pytest.approx(native.star_density / 4)


def test_empty_sky():
    _, stars, metrics = analyze(star_field(count=0))
    assert stars.count == 0
    assert metrics.median_fwhm is None
    assert score(metrics).components["stars"] == 0.0
