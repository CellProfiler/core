import pytest

from cellprofiler_core.setting.subscriber import MotionSubscriber


@pytest.fixture
def motion_subscriber() -> MotionSubscriber:
    return MotionSubscriber("example")


class TestMotionSubscriber:
    def test_group(self, motion_subscriber):
        assert motion_subscriber.group == "motiongroup"
