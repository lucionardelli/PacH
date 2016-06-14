#!/usr/bin/env python
# -*- coding: UTF-8
"""
This module inherits pyhull halfspace class to add basic functionality
that the other modules lacks of
"""

__author__ = "Lucio Nardelli"
__version__ = "1.0"
__maintainer__ = "Lucio Nardelli"
__email__ = "lucio (at) fceia.unr.edu.ar"
__date__ = "August 27, 2015"

from pyhull.halfspace import Halfspace

import numpy as np

from utils import almost_equal, gcd
from rationals import integer_coeff
from custom_exceptions import WrongDimension
from config import *

from z3 import (Solver,
    Optimize,
    Int,
    Or,
    And,
    Implies,
    ForAll,
    simplify,
    unsat,
    unknown
)

COUNTER = 0

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
            self.integerify()

    def __hash__(self):
        """
           Two halfspaces are considered equal if they
           share the normal and the offset.
        """
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
            # We print it as Ax <= t
            if coef > 0:
                hs_repr += " -{0: >3} x{1: <2}".format(coef,idx)
            elif coef < 0:
                hs_repr += " +{0: >3} x{1: <2}".format(abs(coef),idx)
            else:
                # If coefficient is zero, skip it
                pass
        if hs_repr.startswith(' + '):
            # If first coefficient is positive, ignore "sign"
            hs_repr = hs_repr[3:]

        if self.offset > 0:
            ti_repr = ' -{0: >3}'.format(abs(self.offset))
        elif self.offset < 0:
            ti_repr = ' +{0: >3}'.format(abs(self.offset))
        else:
            ti_repr = ''
        return "{0: <10}{1}{2} >= 0".format(header, hs_repr, ti_repr)

    def complexity(self):
        abs_normal = map(abs,self.normal)
        return sum(abs_normal, abs(self.offset))

    def inside(self, point, use_original=False):
        """
        Determines if given points is inside the halfspace
        Operator determines on wich side of the hyperspace
        is supposed to be

        Args:
            origin: point to check if is in the hyperspace
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
            raise WrongDimension(exc_info=True)
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
                # Axis correspond to a new dimension (i.e. and old one)
                idx = ext_dict.index(axis)
                normal.append(self.normal[idx])
                original_normal.append(self.__original_normal[idx])
            else:
                original_normal.append(0)
                normal.append(0)
        self.normal = normal
        self.__original_normal = original_normal

    def integerify(self):
        # If one of the values (i.e. coefficients or it)
        # is not an integer we look for a upper-representation
        # for the halfspace but with integer values
        if any(x for x in self.normal if not float(x).is_integer()):
            integerified = integer_coeff(self.normal+[self.offset])
            self.offset = integerified[-1]
            self.normal = integerified[:-1]
        else:
            self.offset = int(self.offset)
            self.normal = map(int,self.normal)

    # Support for Z3 SMT-Solver
    def smt_solution(self, timeout, neg_points=None, optimize=False):
        # If halfspace's coefficients add to 1 it's
        # as simple as it gets
        normal_sum = sum(abs(x) for x in self.normal)
        if normal_sum == 0:
            return False
        elif normal_sum <= 1:
            simple = True
        else:
            simple = False

        neg_points = neg_points or []

        if optimize:
            solver = Optimize()
        else:
            solver = Solver()
            solver.set("zero_accuracy",10)
        solver.set("timeout", timeout)

        ti = self.offset
        smt_ti = Int("b")
        if ti:
            solver.add(min(0,ti) <= smt_ti, smt_ti <= max(0,ti))
            if optimize:
                # Try to minimize the independent term
                solver.minimize(smt_ti)
        else:
            solver.add(smt_ti == 0)

        variables = set()
        variables_positive = set()

        positive_x = True
        non_trivial = False
        some_consume = False
        some_produce = False

        diff_sol = smt_ti != ti
        smt_keep_sol = ti
        smt_is_sol = smt_ti

        for t_id, coeff in enumerate(self.normal):
            # SMT coefficient
            smt_coeff = Int("a%s" % t_id)
            if optimize:
                # Try to minimize the coefficient
                solver.minimize(smt_coeff)
            # SMT variable
            smt_var = Int("x%s"%t_id)

            # Add SMT varible to the set of variables
            variables.add(smt_var)
            # Add SMT varible basic constraint to the set
            variables_positive.add(smt_var >= 0)

            if coeff:
                # At least one SMT coefficient should be non zero
                non_trivial = Or(non_trivial, smt_coeff != 0)
                # At least one SMT coefficient should be different
                diff_sol = Or(diff_sol, smt_coeff != coeff)
                # Original solution with SMT variable
                smt_keep_sol += coeff * smt_var
                # SMT solution with SMT variable
                smt_is_sol += smt_coeff * smt_var
                # Keep SMT coefficient between original bundaries
                solver.add(min(0,coeff) <= smt_coeff, smt_coeff <= max(0, coeff))

                if not neg_points and not simple:
                    some_produce = Or(some_produce, smt_coeff > 0)
                    some_consume = Or(some_consume, smt_coeff < 0)
            else:
                solver.add(smt_coeff == 0)

    #This is what we want:
        if not neg_points:
            # If there is not negative info, avoid trivial solution (i.e. Not all zero)
            solver.add(simplify(non_trivial))
            if not simple:
                solver.add(simplify(some_consume))
                solver.add(simplify(some_produce))
        # A different solution (i.e. "better")
        solver.add(simplify(diff_sol))
        # If it was a solution before, keep it that way
        solver.add(simplify(ForAll(list(variables), Implies(And(Or(list(variables_positive)), smt_keep_sol <= 0), smt_is_sol <= 0))))

        # New solution shouldn't add a negative point
        for np in neg_points:
            smt_ineq_np = smt_ti
            ineq_np = ti
            for t_id, coeff in enumerate(self.normal):
                ineq_np += coeff * np[t_id]
                smt_coeff = Int("a%s"%(t_id))
                smt_ineq_np += smt_coeff * np[t_id]
            # If neg point was out of this halfspace, keep it out!
            if ineq_np > 0:
                logger.info('Adding HS SMT-NEG restriction')
                solver.add(simplify(smt_ineq_np > 0))

        sol = solver.check()
        if sol == unsat:
            ret = False
            logger.info('Z3 returns UNSAT: Cannot simplify HS without adding neg info')
        elif sol == unknown:
            ret = False
            logger.info('Z3 returns UNKNOWN: Cannot simplify HS in less than %s miliseconds', timeout)
        else:
            ret = solver.model()
        return ret

    def simplify(self, sol):
        normal = []
        if sol:
            offset = sol[Int("b")].as_long()

            for t_id, coeff in enumerate(self.normal):
                smt_coeff = Int("a%s"%(t_id))
                normal.append(int(str(sol[smt_coeff] or 0)))

            self.normal = normal
            self.offset = offset

    def smt_facet_simplify(self, neg_points=None, timeout=0):
        global COUNTER
        COUNTER += 1
        neg_points = neg_points or []
        logger.debug('SMT simplifying facet #%s: %s',COUNTER, self)
        sol = self.smt_solution(timeout, neg_points=neg_points)
        while sol:
            self.simplify(sol)
            sol = self.smt_solution(timeout, neg_points=neg_points)
