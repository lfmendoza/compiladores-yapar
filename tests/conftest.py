from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def simple_yalp() -> Path:
    return FIXTURES / "simple.yalp"


@pytest.fixture
def epsilon_yalp() -> Path:
    return FIXTURES / "epsilon.yalp"


@pytest.fixture
def conflict_yalp() -> Path:
    return FIXTURES / "dangling_else.yalp"
