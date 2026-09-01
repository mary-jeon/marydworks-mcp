import pytest

from sw.models import SwError
from sw.write import MATE_TYPES, validate_mates


def test_valid():
    ms = validate_mates([
        {"type": "coincident", "a": {"name": "Face@S1-1", "type": "FACE", "xyz_mm": [0, 0, 0]},
         "b": {"name": "Face@S2-1", "type": "FACE", "xyz_mm": [1, 2, 3]}},
        {"type": "distance", "a": {"name": "", "type": "FACE", "xyz_mm": [0, 0, 0]},
         "b": {"name": "", "type": "FACE", "xyz_mm": [0, 0, 0]}, "distance_mm": 10},
    ])
    assert ms[0]["code"] == MATE_TYPES["coincident"] and ms[1]["distance_m"] == 0.01


def test_invalid_type_and_missing_distance():
    with pytest.raises(SwError):
        validate_mates([{"type": "tangent", "a": {}, "b": {}}])
    with pytest.raises(SwError):
        validate_mates([{"type": "distance", "a": {"type": "FACE", "xyz_mm": [0, 0, 0]}, "b": {"type": "FACE", "xyz_mm": [0, 0, 0]}}])
