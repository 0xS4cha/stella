import pytest

from stella.environment import NIKON_D60, Lens, exposure_limits, npf_rule, rule_500


def test_d60_sensor_geometry():
    assert NIKON_D60.pixel_pitch_um == pytest.approx(6.09, abs=0.01)
    assert NIKON_D60.crop_factor == pytest.approx(1.52, abs=0.01)


def test_rule_500_for_kit_lens():
    assert rule_500(NIKON_D60, Lens(18, 3.5)) == pytest.approx(18.2, abs=0.1)


def test_npf_is_stricter_and_tightens_with_focal_length():
    wide, tele = Lens(18, 3.5), Lens(55, 5.6)
    assert npf_rule(NIKON_D60, wide) == pytest.approx(17.0, abs=0.1)
    assert npf_rule(NIKON_D60, tele) < npf_rule(NIKON_D60, wide)


def test_declination_extends_exposure():
    lens = Lens(18, 3.5)
    assert npf_rule(NIKON_D60, lens, declination_deg=60) == pytest.approx(2 * npf_rule(NIKON_D60, lens))


def test_recommended_is_capped_by_body():
    limits = exposure_limits(NIKON_D60, Lens(8, 3.5))
    assert limits.npf_s > 30
    assert limits.recommended_s == 30.0
