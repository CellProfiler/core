import pytest

from cellprofiler_core.setting.text import MotionName


@pytest.fixture
def motion_name() -> MotionName:
    return MotionName("example")


class TestMotionName:
    def test_group(self, motion_name):
        assert motion_name.group == "motiongroup"
