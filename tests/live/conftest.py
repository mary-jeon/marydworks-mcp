"""Live tests run against a real SolidWorks session.

Copy `config.example.json` to `config.json` (git-ignored) and fill it with a part/assembly
that is currently open in SolidWorks. All expected values come from that file, so the
tests carry no project-specific data.
"""
import json
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="session")
def cfg():
    path = os.path.join(HERE, "config.json")
    if not os.path.isfile(path):
        pytest.skip("tests/live/config.json 없음 — config.example.json을 복사해 채우세요")
    with open(path, encoding="utf-8") as f:
        return json.load(f)
