#!/usr/bin/env python
# -*- coding: UTF-8
"""
This module inherits pyhull halfspace class to add basic functionality
that the other modules lacks of
"""

__author__ = "Lucio Nardelli"
__version__ = "0.1"
__maintainer__ = "Lucio Nardelli"
__email__ = "lucio (at) fceia.unr.edu.ar"
__date__ = "August 27, 2015"

from pyhull.halfspace import Halfspace

import numpy as np

from utils import almost_equal, gcd
from rationals import integer_coeff
from custom_exceptions import WrongDimension
from config import *

try:
    import z3
except:
    #No module named z3, whouldn't be available
    pass

counter = 0

class Halfspace(Halfspace):
    """
    A halfspace defined by dot(normal, coords) + offset <= 0
    """
    def __init__(self, normal, offset, integer_vals=True):
        super(Halfspace,self).__init__(normal, offset)
        self.dim = len(normal)
        self.__original_normal = normal
        self.__original_offset = offset
        if integer_vals:
            logger.debug('Searching for integer coeficients of HS %s', self)
            self.integerify()
            logger.debug('Done %s', self)

    def __hash__(self):
        return hash(str(self.normal + [self.offset]))

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.__str__()

    def __contains__(self, element):
        return self.inside(element)

    def __str__(self):
        header = "HS dim {0}".format(self.dim)
        hs_repr = ''
        for idx,coef in enumerate(self.normal):
            # Queremos dar vuelta el <= a 0 al imprimir
            if coef > 0:
                hs_repr += " - {0: >3} x{1: <2}".format(coef,idx)
            elif coef < 0:
                hs_repr += " + {0: >3} x{1: <2}".format(abs(coef),idx)
            else:
                # Los coeficientes 0 no los imprimimos
                pass
        if hs_repr.startswith(' + '):
            # El primer símbolo no va
            hs_repr = hs_repr[3:]

        if self.offset > 0:
            ti_repr = ' - {0: >3}'.format(abs(self.offset))
        elif self.offset < 0:
            ti_repr = ' + {0: >3}'.format(abs(self.offset))
        else:
            ti_repr = ''
        return "{0: <10}{1} {2} >= 0".format(header, hs_repr, ti_repr)

    def __fstr__(self):
        header = "HS in dim {0}".format(self.dim)
        hs_repr = []
        for idx in xrange(self.dim):
            hs_repr.append("{0:.2f} x{1}".format(self.normal[idx], idx))
        hs_repr = ' + '.join(hs_repr)
        return "{0}\t{1} + {2:.2f} <= 0".format(header, hs_repr, self.offset)

    def inside(self, point, use_original=False):
        """
        Determines if given points is inside the halfspace
        Operator determines on wich side of the hyperspace
        is supposed to be

        Args:
            origin: point to check if is in the hyperplane
        """
        if use_original:
            normal = self.__original_normal
            offset = self.__original_offset
        else:
            normal = self.normal
            offset = self.offset
        try:
            eq_res = np.dot(normal,point) + offset
        except Exception, err:
            raise WrongDimension()
        return eq_res < 0.0 or almost_equal(eq_res, 0.0, tolerance=TOLERANCE)

    def extend_dimension(self, dim, ext_dict):
        """
            dim: the dimension to exetend to
            ext_dict: a list of the "old" points position
                      in the new qhull (given in order)
        """
        self.dim = dim
        original_normal = []
        normal = []
        for axis in xrange(dim):
            if axis in ext_dict:
                # El eje pertenece a una dimensión "de los viejas"
                idx = ext_dict.index(axis)
                normal.append(self.normal[idx])
                original_normal.append(self.__original_normal[idx])
            else:
                original_normal.append(0)
                normal.append(0)
        self.normal = normal
        self.__original_normal = original_normal

    def axis_intersection(self, axis):
        # Buscamos la intersección del hiperespacio con el eje 'axis'
        ret = 0
        if self.normal[axis]:
            ret = (-1 * self.offset) / self.normal[axis]
        return ret

    def integerify(self):
        if any(map(lambda x: not x.is_integer(), self.normal)):
            integerified = integer_coeff(self.normal+[self.offset])
            self.offset = integerified[-1]
            self.normal = integerified[:-1]
        else:
            self.offset = int(self.offset)
            self.normal = map(int,self.normal)

    def smt_solution(self, timeout, neg_points=None):
        if sum(abs(x) for x in self.normal) == 0: return False
        neg_points = neg_points or []
        solver = z3.Solver()
        solver.set("timeout", timeout)
        solver.set("zero_accuracy",10)

        b = self.offset
        z3_b = z3.Int("b")

        if b:
            solver.add(min(0,b) <= z3_b, z3_b <= max(0,b))
        else:
            solver.add(z3_b == 0)

        possible_x = True
        # If halfspace has coefficients adding 1 it's
        # as simple as it gets
        simple = sum(abs(x) for x in self.normal) <= 1
        non_trivial = False
        if not simple:
            some_consume = False
            some_produce = False

        diff_sol = z3_b != b
        h1 = b
        h2 = z3_b
        variables = []

        for t_id, coeff in enumerate(self.normal):
            # NEW:
            if not coeff:
                solver.add(z3.Int("a%s"%t_id) == 0)
                continue
            smt_coeff = z3.Int("a%s"%t_id)
            var = z3.Int("x%s"%t_id)

            variables.append(var)
            possible_x = z3.And(possible_x, var >= 0)

            solver.add(min(0,coeff) <= smt_coeff, smt_coeff <= max(0, coeff))
            if not simple:
                some_consume = z3.Or(some_consume, smt_coeff < 0)
                some_produce = z3.Or(some_produce, smt_coeff > 0)

            non_trivial = z3.Or(non_trivial, smt_coeff != 0)
            diff_sol = z3.Or(diff_sol, smt_coeff != coeff)
            h1 = h1 + coeff * var
            h2 = h2 + smt_coeff * var

        # NEW:
        if not simple and not len(list(neg_points)):
            solver.add(z3.simplify(some_consume))
            solver.add(z3.simplify(some_produce))
            
        # NEW:
        if not len(list(neg_points)):
        	solver.add(z3.simplify(non_trivial))

        # NEW:
        if str(z3.simplify(diff_sol)) != False: solver.add(z3.simplify(diff_sol))
        solver.add(z3.simplify(z3.ForAll(variables, z3.Implies(z3.And(possible_x, h1 <= 0), h2 <= 0))))

        ## non negative point should be a solution
        for np in list(neg_points):
            smt_np = False
            ineq_np = self.offset
            for t_id, coeff in enumerate(self.normal):
                if coeff and np[t_id]:
                    z3_var = z3.Int("a%s"%(t_id))
                    ineq_np = ineq_np + z3_var * np[t_id]
            smt_np = z3.simplify(z3.Or(smt_np, ineq_np > 0))
            # NEW:
            if str(smt_np) != 'False': solver.add(smt_np)

        sol = solver.check()
        if sol == z3.unsat or sol == z3.unknown:
            ret = False
            del(solver)
            del(sol)
        else:
            ret = solver.model()
        return ret

    def simplify(self, sol):
        normal = []
        if sol:
            offset = sol[z3.Int("b")].as_long()

            for t_id, coeff in enumerate(self.normal):
                smt_coeff = z3.Int("a%s"%(t_id))
                normal.append(int(str(sol[smt_coeff] or 0)))
            # NEW:
            if True or sum(abs(x) for x in normal) != 0:
                self.normal = normal
                self.offset = offset

    def smt_facet_simplify(self, neg_points=None, timeout=0):
        neg_points = neg_points or []
        sol = self.smt_solution(timeout, neg_points=neg_points)
        while sol:
            self.simplify(sol)
            sol = self.smt_solution(timeout, neg_points=neg_points)
