from dataclasses import replace

import pytest

from stella.analysis import ImageMetrics, ScoringWeights, score

GOOD = ImageMetrics(
    background_level=0.06,
    background_rms=0.004,
    background_gradient=0.001,
    star_count=500,
    star_density=200.0,
    median_fwhm=3.0,
    median_elongation=1.05,
    snr=80.0,
    saturated_fraction=0.0,
    saturated_stars=0,
)


def test_good_frame_scores_high():
    assert score(GOOD).total > 0.9


@pytest.mark.parametrize(
    "changes, component",
    [
        ({"background_level": 0.6}, "exposure"),
        ({"background_level": 0.005}, "exposure"),
        ({"median_fwhm": 9.0}, "sharpness"),
        ({"saturated_fraction": 0.01}, "clipping"),
        ({"snr": 3.0}, "signal"),
    ],
)
def test_defects_lower_the_matching_component(changes, component):
    degraded = score(replace(GOOD, **changes))
    assert degraded.components[component] < score(GOOD).components[component]
    assert degraded.total < score(GOOD).total


def test_weights_are_normalised():
    only_stars = ScoringWeights(stars=1, sharpness=0, roundness=0, exposure=0, signal=0, clipping=0)
    result = score(GOOD, weights=only_stars)
    assert result.total == result.components["stars"]
