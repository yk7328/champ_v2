import numpy as np


class SextractorPoint(object):
    __slots__ = ['c', 'r', 'flux', 'flux_err', 'flags', 'width', 'height', 'theta']

    def __init__(self, column, row, flux, flux_err, flags, width, height, theta):
        # Sextractor coordinates are 1-based
        self.c = float(column) - 1.0
        self.r = float(row) - 1.0
        self.flux = float(flux)
        self.flux_err = float(flux_err)
        self.flags = int(flags)
        self.width = float(width)
        self.height = float(height)
        self.theta = float(theta)


class Sextraction(object):
    def __init__(self, lines):
        self.points = []
        for line in filter(lambda x: not x.startswith('#'), lines):
            self.points.append(SextractorPoint(*line.strip().split()))

    @property
    def rcs(self):
        return np.array([(pt.row, pt.column) for pt in self.points])

    @property
    def image(self):
        rcs = self.rcs
        image = np.zeros(rcs.max(axis=0) + 1)
        image[rcs.astype(np.int)[:, 0], rcs.astype(np.int)[:, 1]] = 1
        return image
