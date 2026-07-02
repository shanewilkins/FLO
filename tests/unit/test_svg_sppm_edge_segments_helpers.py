from types import SimpleNamespace

from flo.render._svg_sppm_edge_segments import (
    _candidate_segment_indexes,
    _first_rightward_horizontal_segment_index,
    _longest_segment_index,
)


def _p(x: float, y: float) -> SimpleNamespace:
    return SimpleNamespace(x_px=x, y_px=y)


def test_candidate_segment_indexes_prefers_requested_index():
    points = (_p(0, 0), _p(1, 0), _p(2, 0), _p(3, 0))

    indexes = _candidate_segment_indexes(
        points,
        avoid_near_source=True,
        prefer_near_source=False,
        preferred_index=1,
    )

    assert list(indexes) == [1]


def test_candidate_segment_indexes_handles_preference_modes():
    points = (_p(0, 0), _p(1, 0), _p(2, 0), _p(3, 0))

    near_source = _candidate_segment_indexes(
        points,
        avoid_near_source=False,
        prefer_near_source=True,
        preferred_index=None,
    )
    assert list(near_source) == [0]

    avoid_source = _candidate_segment_indexes(
        points,
        avoid_near_source=True,
        prefer_near_source=False,
        preferred_index=None,
    )
    assert list(avoid_source) == [2]


def test_first_rightward_horizontal_segment_index_selects_expected_segment():
    points = (_p(0, 0), _p(-1, 0), _p(-1, 1), _p(2, 1), _p(2, 3))

    assert _first_rightward_horizontal_segment_index(points) == 2


def test_longest_segment_index_prefers_longest_candidate():
    points = (_p(0, 0), _p(1, 0), _p(1, 4), _p(6, 4))

    assert _longest_segment_index(points, segment_indexes=range(3)) == 2
