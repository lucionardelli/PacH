"""
This module inherits pyhull halfspace class to add basic functionality
that the other modules lacks of
"""

__author__ = "Lucio Nardelli"
__version__ = "0.1"
__maintainer__ = "Lucio Nardelli"
__email__ = "luci@fceia.unr.edu.ar"
__date__ = "August 27, 2015"

from pyhull.halfspace import Halfspace

import numpy as np

class Halfspace(Halfspace):
    """
    A halfspace defined by dot(normal, coords) + offset <= 0
    """
    def __init__(self, normal, offset):
        super(Halfspace,self).__init__(normal, offset)
        self.dim = len(normal)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        header = "Halfspace in dimension {0}".format(self.dim)
        hs_repr = []
        for idx in xrange(self.dim):
            hs_repr.append("{0:.2f} x{1}".format(self.normal[idx], idx))
        hs_repr = ' + '.join(hs_repr)
        return "{0}\n\t {1} + {2:.2f} <= 0".format(header, hs_repr, self.offset)

    def inside(self, point):
        """
        Determines if given points is inside the halfspace
        Operator determines on wich side of the hyperspace
        is supposed to be

        Args:
            origin: point to check if is in the hyperplane
        """
        # For some reaons cannot import utils here...
        def almost_equal(f1, f2, tolerance=0.00001):
            return abs(f1 - f2) <= tolerance * max(abs(f1), abs(f2))
        try:
            eq_res = np.dot(self.normal,point) + self.offset
        except Exception, err:
            raise WrongDimension()
        return eq_res < 0.0 or almost_equal(eq_res, 0.0, tolerance=0.0001)
