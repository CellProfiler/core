import matplotlib.pyplot
import matplotlib.quiver
import numpy


class Motion:
    u: numpy.array
    v: numpy.array

    step: int

    def __init__(self, u: numpy.array, v: numpy.array, step: int = 8):
        assert u.shape == v.shape

        self.u = u
        self.v = v

        self.step = step

    @property
    def coordinates(self) -> [numpy.array, numpy.array]:
        r, c = self.u.shape

        return numpy.arange(0, c, self.step), numpy.arange(r, -1, -self.step)

    @property
    def magnitude(self) -> numpy.array:
        rho = numpy.sqrt(self.u ** 2 + self.v ** 2)

        phi = numpy.arctan2(self.v, self.u)

        return rho, phi

    def plot(self) -> matplotlib.quiver.Quiver:
        u = self.u[:: self.step, :: self.step]
        v = self.v[:: self.step, :: self.step]

        return matplotlib.pyplot.quiver(*self.coordinates, u, v, self.magnitude)
