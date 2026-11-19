import pytest

from render import underwater_refraction as mod

CASES = [
    pytest.param('refraction_offset', ((0.5, 0.5), (0.2, 0.0), 9.0, 0.1), (0.502, 0.5), True, id='01_depth_scaled_refraction'),
    pytest.param('caustic_uv', ((0.5, 0.5), 0.5, 2.0), (1.5, 1.0), True, id='02_time_driven_caustic'),
    pytest.param('water_normal', (1.0, 0.0, 1.0), (-0.7071067811865475, -0.0, 0.7071067811865475), True, id='03_water_normal_normalized'),
    pytest.param('refract_visible', (2.0, 1.0, 2.5), False, False, id='04_refraction_occluded'),
    pytest.param('wait_compute', (3, 2), False, False, id='05_compute_read_sync'),
    pytest.param('pass_order', ('transparent',), 20, False, id='06_transparent_after_caustic'),
    pytest.param('caustic_intensity', (1.0, 3840, 2160), 0.25, True, id='07_resolution_independent_caustic'),
    pytest.param('reject_water_depth', (1.02, 1.0, 0.01), True, False, id='08_water_self_depth_rejected'),
    pytest.param('reflection_depth', (1, 1), False, False, id='09_reflection_recursion_guard'),
    pytest.param('split_water_color', ((0.2, 0.6, 0.8), (0.0, 0.5, 0.5)), (0.2, 0.3, 0.4, 0.0, 0.3, 0.4), True, id='10_split_fog_and_caustic'),
    pytest.param('snell_refract', (0.75, 0.5), (0.7603453162872774, False), True, id='11_snell_refraction'),
    pytest.param('caustic_phase', (0.3, 2.0), 0.6, True, id='12_caustic_phase_wrap'),
    pytest.param('normal_key', ('camA', 'left'), 'camA:left', False, id='13_water_normal_camera_key'),
    pytest.param('composite_order', ('bubble',), 30, False, id='14_bubble_composite_order'),
    pytest.param('underwater_tint', (0.2, 0.8, 0.25), 0.35000000000000003, True, id='15_separated_underwater_tint'),
]


def assert_close(actual, expected):
    if isinstance(expected, tuple):
        assert isinstance(actual, tuple) and len(actual) == len(expected)
        for a, e in zip(actual, expected):
            assert_close(a, e)
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(actual) == len(expected)
        for a, e in zip(actual, expected):
            assert_close(a, e)
    elif isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for key in expected:
            assert_close(actual[key], expected[key])
    else:
        assert actual == pytest.approx(expected)


@pytest.mark.parametrize("func_name,args,expected,approx", CASES)
def test_underwater_refraction_contract(func_name, args, expected, approx):
    func = getattr(mod, func_name)
    result = func(*args)
    if approx:
        assert_close(result, expected)
    else:
        assert result == expected
