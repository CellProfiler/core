import numpy
import pytest
import skimage.io
import skimage.registration

from cellprofiler_core.motion import Motion


@pytest.fixture
def coordinates() -> [numpy.array, numpy.array]:
    with numpy.load("../data/motion/coordinates.npz") as data:
        return [*data.values()]


@pytest.fixture
def magnitude() -> [numpy.array, numpy.array]:
    with numpy.load("../data/motion/magnitude.npz") as data:
        return [*data.values()]


@pytest.fixture
def motion() -> Motion:
    reference = skimage.io.imread("../data/motion/reference.png")

    image = skimage.io.imread("../data/motion/image.png")

    v, u = skimage.registration.optical_flow_tvl1(reference, image)

    return Motion(u, v)


class TestMotion:
    def test_coordinates(self, motion, coordinates):
        x_x, x_y = motion.coordinates

        y_x, y_y = coordinates

        numpy.testing.assert_array_equal(x_x, y_x)
        numpy.testing.assert_array_equal(x_y, y_y)

    def test_magnitude(self, motion, magnitude):
        x_rho, x_phi = motion.magnitude

        y_rho, y_phi = magnitude

        numpy.testing.assert_array_equal(x_rho, y_rho)
        numpy.testing.assert_array_equal(x_phi, y_phi)
