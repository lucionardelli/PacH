#!/usr/bin/env python
# -*- coding: UTF-8
from halfspace import Halfspace
from custom_exceptions import IncorrectOutput, CannotGetHull
from convexhull import ConvexHull
from stopwatch import StopWatchObj
from config import logger

from itertools import izip
from z3 import (Solver,
    Int,
    Ints,
    Or,
    And,
    simplify,
    unsat,
    unknown
)

class SMTHull(ConvexHull):

    def __parse_smt_solution(self, model):
        """
         input: Output solution for Z3 Solver
         output: (dimension,nbr_facets,[halfspaces])
        """
        dim = len(list(self.points)[0])

        facets = []
        try:
            facet_number = model[Int("FacetNumber")].as_long()
            for yaxis in xrange(facet_number):
                ti = Int('b%s' % yaxis)
                offset = model[ti].as_long()
                coefficients = []
                for xaxis in xrange(dim):
                    coeff = model[Int('a%s,%s'%(yaxis,xaxis))].as_long()
                    coefficients.append(coeff)
                hs = Halfspace(coefficients,offset)
                facets.append(hs)
        except Exception, err:
            logger.error('Incorrect output of smt-hull! Error: %s', err)
            raise IncorrectOutput()
        return (dim, facet_number, facets)

    def __smt_solution(self, equation_number):
        if len(self.points) < 1:
            logger.info('Cannot find solution for SMT-HULL with no points!')
            raise Exception('Cannot find solution for SMT-HULL with no points!')
        timeout = 3000 # TODO As argument?
        points = self.points
        dim = len(list(self.points)[0])
        logger.info('Searching for hull in dimension %s based on %s points using SMT',
                dim,len(points))
        neg_points = self.neg_points or []

        """
        Ax+b<=0

        A \in mxn
        donde m es la cantidad a minimizar (i.e. la cantidad de ecuaciones)
        y n es igual a la dimensión en donde habitan los puntos

        Matrix's coefficients are represented as a#y,#x donde '#x' indica la columna e '#y' la fila
        """
        matrix = []
        evaluations = set()
        negatives = {}
        # Build the SMT-System
        for yaxis in xrange(equation_number):
            # Define the list of coefficients for this equation
            coeff_list = Ints(' '.join('a%s,%s'%(yaxis,xaxis) for xaxis in xrange(dim)))
            # Define independent term for this equation
            ti = Int('b%s' % yaxis)
            # Build the matrix
            matrix.append(coeff_list + [ti])

        # Every point should be a solution of the system
        # i.e. it should we true that A[yaxis] * point + b[yaxis] >= 0
        for idx, point in enumerate(points):
            evaluation = ti
            for coeff, val in izip(coeff_list, point):
                if val:
                    evaluation += coeff * val
            # Add to the "evaluation restriction set"
            evaluations.add(evaluation >= 0)
        # Every negative point should NOT be a solution of the system
        # i.e. it should we true that A[E] * npoint + b[E] < 0 for some E
        #TODO TODO
        for idx, npoint in enumerate(list(neg_points)[0:20]):
            this_npoint_set = negatives.setdefault(npoint,set())
            evaluation = ti
            for coeff, nval in izip(coeff_list, npoint):
                if nval:
                    evaluation += coeff * nval
            # Add to this point "negative restriction set"
            this_npoint_set.add(evaluation < 0)
        # Build the SMT problem
        logger.info("Building solver for solution with %s equations",equation_number)
        solver = Solver()
        solver.set("zero_accuracy",10)
        solver.set("timeout", timeout)

        # All evaluations should be satisfied
        solver.add(And(list(evaluations)))
        for npoint, this_npoint_set in negatives.iteritems():
            solver.add(Or(list(this_npoint_set)))

        # Add facetnumber to the solver's solution for used when parsing output
        solver.add(Int("FacetNumber") == equation_number)

        sol = solver.check()
        if sol == unsat:
            ret = False
            logger.info('Z3 returns UNSAT: Cannot get hull without adding neg info')
        elif sol == unknown:
            ret = False
            logger.info('Z3 returns UNKNOWN: Cannot get hull in less than %s miliseconds', timeout)
        else:
            ret = solver.model()
            logger.info('Z3 returns valid model in lest than %s miliseconds', timeout)
            logger.debug('Z3 Model:\n %s', ret)
        return ret

    def __smt_hull_bs(self, min_eq_nbr=1, max_eq_nbr=99):
        if max_eq_nbr > 5000:
            logger.error('Cannot get solution with less than 5000 equations')
            raise CannotGetHull()
        logger.info("Calling SMT-Hull bisecting from %s to %s",min_eq_nbr, max_eq_nbr)
        middle = (min_eq_nbr + max_eq_nbr) / 2
        sol = self.__smt_solution(middle)
        if not sol:
            # Cannot get solution, try with more equations
            logger.debug("Cannot get solution, try with more equations")
            ret = self.__smt_hull_bs(min_eq_nbr=middle, max_eq_nbr=(max_eq_nbr * 2))
        elif min_eq_nbr in (middle,max_eq_nbr):
            # Found best solution!
            logger.info("Found the best solution with %s equations",middle)
            ret = sol
        else:
            # Found solution. Is there a better one?
            assert min_eq_nbr <= middle, "Error bisecting for SMT-Hull"
            ret = self.__smt_hull_bs(min_eq_nbr=min_eq_nbr, max_eq_nbr=middle) or sol
        return ret

    @StopWatchObj.stopwatch
    def compute_hiperspaces(self):
        # Checks made in parent class
        super(SMTHull,self).compute_hiperspaces()
        if not self.neg_points:
            logger.error('No negative points, cannot get hull using SMT!')
            raise CannotGetHull()

        model = self.__smt_hull_bs(min_eq_nbr=1, max_eq_nbr=20)
        try:
            dim, facets_nbr, facets = self.__parse_smt_solution(model)
        except IncorrectOutput, err:
            logger.error('Could not get hull')
            raise CannotGetHull()
        logger.info('Found hull in dimension %s of %s facets',
                dim,facets_nbr)
        self.dim = dim
        self.facets = facets
        return self.dim

if __name__ == '__main__':
    import sys, traceback,pdb
    from mains import qhull_main
    try:
        smt_qhull_main()
    except Exception, err:
        logger.error('SMT-Hull Error: %s' % err, exc_info=True)
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        #pdb.post_mortem(tb)
