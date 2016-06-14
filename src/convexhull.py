#!/usr/bin/env python
# -*- coding: UTF-8
from pyhull import qconvex
from halfspace import Halfspace
from parser import XesParser
from custom_exceptions import IncorrectOutput, CannotGetHull, LostPoints
from stopwatch import StopWatchObj
from redirect_output import stderr_redirected
from config import logger

import sys
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

class ConvexHull(StopWatchObj):

    def __init__(self, points=[], neg_points=[]):
        super(ConvexHull, self).__init__()
        self.points = set(points)
        self.neg_points = set(neg_points)
        self.facets = []

    def __str__(self):
        return '\n'.join(['%s'%f for f in self.facets])

    def __contains__(self, point):
        return self.is_inside(point)

    def compute_hiperspaces(self):
        if not len(self.points) > 0:
            logger.error('No points to compute hull!')
            raise Exception('No points to compute hull!')
        # Nothing to compute. Intended to be inherithed anr reimplemented
        return True

    @StopWatchObj.stopwatch
    def prepare_negatives(self):
        """
            Ensure that negative points given
            live all outside the hull
        """
        actual_neg_points = []
        removed = 0
        logger.info('Prepare_negatives starts %s points',len(self.neg_points))
        for npoint in self.neg_points:
            if npoint not in self:
                actual_neg_points.append(npoint)
            else:
                removed += 1
        if removed:
            logger.info('prepare_negatives removed %s points',removed)
        self.neg_points = actual_neg_points

    def union(self, facets):
        """
            Merge hull with a list of facets
        """
        fdim = None
        for facet in facets:
            if fdim is None:
                fdim = facet.dim
            else:
                assert fdim == facet.dim, "Not all facets to be merge have the"\
                        " same dimension!"
        # If fdim is None the facets to merge is empty
        # We can always merge with an empty facetdo that
        if fdim is not None and self.dim != fdim:
            raise ValueError("Convex Hulls and facets must live in the same"\
                    " dimension!")
        self.facets = list(set(self.facets) | set(facets))

    def separate(self, points):
        """
            Given a list of points
            (they must all live in the same dimension of the hull)
            it returns a dictionary indicating which one are
            inside and which one are outside
            Used for sanity checks
        """
        ret = {}
        inside = ret.setdefault('inside',[])
        outside = ret.setdefault('outside',[])
        dyt = False
        positions = []
        for point in points:
            if len(point) != self.dim:
                raise ValueError("Convex Hulls (dim %s) and points (dim %s) must live in the same"\
                        " dimension!"%(len(point), self.dim))
            if point in self:
                inside.append(point)
            else:
                #Shouldn't happen
                really = not point in self
                outside.append(point)
        return ret

    def all_in_file(self, filename, event_dictionary=None):
        # Sanity check. Are all points from file inside the Hull?
        # It makes thing slower, speacially in big cases
        parser = XesParser(filename)
        parser.event_dictionary = event_dictionary or {}
        parser.parse()
        parser.parikhs_vector()
        return self.all_in(parser.pv_set)

    @StopWatchObj.stopwatch
    def all_in(self, points):
        # Sanity check. Are points inside the Hull?
        # It makes thing slower, speacially in big cases
        logger.info('Sanity check: Are all points still valid?')
        where = self.separate(points)
        if len(where.get('outside',[])) > 0:
            logger.error('Some points are outisde the hull')
            raise LostPoints('Some points are outisde the hull: %s',
                    where['outside'])
        logger.info('Sanity check passed')
        return True

    def is_inside(self,outsider):
        ret = True
        for facet in self.facets:
            if not outsider in facet:
                ret = False
                break
        return ret

    def restrict_to(self, outsider):
        facets = list(self.facets)
        popped = 0
        for idx,facet in enumerate(self.facets):
            if not facet.inside(outsider):
                facets.pop(idx - popped)
                popped += 1
        self.facets = facets

    def extend_dimension(self, dim, ext_dict):
        """
            dim: the dimension to exetend to
            ext_dict: a list of the "old" points position
                      in the new qhull (given in order)
        """
        self.dim = dim
        for facet in self.facets:
            facet.extend_dimension(dim, ext_dict)

    def extend(self, eigen, cluster, orig_dim=None):
        """
         Given a qhull computed from a cluster (i.e. projection)
         "extend" it (making all the new variables zero)
         to the original dimension
        """
        # Order and search for the actual position
        # on the original eigenvector. Afterwards, "extend"
        # the hull to conform with the original positions
        cluster = list(set([abs(x) for x in cluster]))
        cluster.sort(reverse=True)
        orig_dim = orig_dim or self.dim
        proj_idx = []
        for proj in cluster:
            # Cuando conectamos dos proyecciones pasamos ambos valores concatenados
            proj_idx += [idx%orig_dim for idx,val in enumerate(eigen) if abs(val) == proj\
                    and idx%orig_dim not in proj_idx]
        self.extend_dimension(orig_dim, proj_idx)

    def can_eliminate(self, candidate, npoint):
        """
          Checks whether we can safely (i.e. whitout adding the
          negative point to the hull) remove one facet
        """
        ret = False
        for facet in set(self.facets) - set(candidate):
            if not facet.inside(npoint):
                ret = True
                break
        return ret

    @StopWatchObj.stopwatch
    def no_smt_simplify(self, max_coef=10):
        facets = list(self.facets)
        popped = 0
        if len(self.neg_points):
            for idx,facet in enumerate(self.facets):
                # Create a dummy hull to temporaly store the facets
                # of the original hull except for the candidate to be deleted
                tmpqhull = ConvexHull(set())
                tmpqhull.facets = list(set(facets)-set([facet]))
                simplify = True
                for nidx, npoint in enumerate(self.neg_points):
                    logger.debug('Trying npoint #%s'%nidx)
                    if npoint in tmpqhull:
                        simplify = False
                        logger.debug('Failed due to %s' % nidx)
                        break
                if simplify:
                    facets.pop(idx - popped)
                    popped += 1
            logger.info('Popped %d facets using negative info',popped)
        else:
            logger.info( "NOSMT no negative points around hull!")
        self.facets = facets

    def complexity(self):
        complexity = 0
        for facet in self.facets:
            sum_facet = reduce(lambda x,r: abs(x) + abs(r),
                    facet.normal,
                    facet.offset)
            complexity += sum_facet
        return complexity

    # Support for Z3 SMT-Solver
    @StopWatchObj.stopwatch
    def smt_solution(self, timeout, optimize=False):
        if optimize:
            solver = Optimize()
        else:
            solver = Solver()
            solver.set("zero_accuracy",10)
        solver.set("timeout", timeout)


        non_trivial = False
        diff_sol = False
        smt_keep_sol = True # a.k.a A1
        smt_is_sol = True # a.k.a A2

        some_consume = False
        some_produce = False
        variables = set()
        variables_positive = set()
        for p_id, place in enumerate(self.facets):
            ti = place.offset
            smt_ti = Int("b%s" % p_id)

            if ti:
                solver.add(min(0,ti) <= smt_ti, smt_ti <= max(0, ti))
            else:
                solver.add(smt_ti == 0)


            facet_non_trivial = False
            facet_diff_sol = False
            smt_facet_eval = ti
            smt_facet_sol = ti

            # If halfspace's coefficients add to 1 it's
            # as simple as it gets
            simple = sum(abs(x) for x in place.normal) <= 1
            # do_cons_prod indicates if the place has incoming and outgoing transitions
            do_cons_prod = False
            consume = produce = 0
            for coeff in place.normal:
                if coeff > 0:
                    produce = 1
                elif coeff < 0:
                    consume = 1
                if consume * produce:
                    do_cons_prod = True
                    break

            do_cons_prod = reduce(lambda x,y:x*y, [x + 1 for x in place.normal]) < 1

            for t_id, coeff in enumerate(place.normal):
                # SMT coefficient
                smt_coeff = Int("a%s,%s" % (p_id, t_id))
                if optimize:
                    # Try to minimize the coefficient
                    solver.minimize(smt_coeff)
                # SMT variable
                smt_var = Int("x%s" % t_id)

                # Add SMT varible to the set of variables
                variables.add(smt_var)
                # Add SMT varible basic constraint to the set
                variables_positive.add(smt_var >= 0)
                if coeff:
                    # At least one SMT coefficient should be non zero
                    facet_non_trivial = Or(facet_non_trivial, smt_coeff != 0)
                    # At least one SMT coefficient should be different
                    facet_diff_sol = Or(facet_diff_sol, smt_coeff != coeff)
                    # Original solution with SMT variable
                    smt_facet_eval += coeff * smt_var
                    # SMT solution with SMT variable
                    smt_facet_sol += smt_coeff * smt_var
                    # Keep SMT coefficient between original bundaries
                    solver.add(min(0,coeff) <= smt_coeff, smt_coeff <= max(0, coeff))

                    if not self.neg_points and not simple and do_cons_prod:
                        some_produce = Or(some_produce, smt_coeff > 0)
                        some_consume = Or(some_consume, smt_coeff < 0)
                else:
                    # Keep zero coefficients unchanged
                    solver.add(smt_coeff == 0)
            if not self.neg_points:
                # Avoid trivial solution (i.e. all zeros as coeff)
                non_trivial = Or(non_trivial, facet_non_trivial)
            # Solution of smt must be different
            diff_sol = Or(diff_sol, facet_diff_sol)
            # If point is in old-solution should be in smt-solution
            smt_keep_sol = And(smt_keep_sol, smt_facet_eval <= 0)
            # Solutions shoul be a solution
            smt_is_sol = And(smt_is_sol, smt_facet_sol <= 0)

            if not self.neg_points and not simple and do_cons_prod:
                solver.add(simplify(some_consume))
                solver.add(simplify(some_produce))

            if optimize:
                # Try to minimize the independent term
                solver.minimize(smt_ti)

    # This is what we want:
        if not self.neg_points:
            # If there is not negative info, avoid trivial solution (i.e. Not all zero)
            solver.add(simplify(non_trivial))
        # A different solution (i.e. "better")
        solver.add(simplify(diff_sol))
        # If it was a solution before, keep it that way
        solver.add(simplify(ForAll(list(variables), Implies(And(Or(list(variables_positive)), smt_keep_sol), smt_is_sol))))

        # Negative point shouldn't be a solution
        for np in self.neg_points:
            smt_np = False
            for p_id, place in enumerate(self.facets):
                place_at_np = Int("b%s" % p_id)
                for t_id, coeff in enumerate(place.normal):
                    # If coefficient was zero, it will remain zero
                    if coeff and np[t_id]:
                        smt_coeff = Int("a%s,%s" % (p_id, t_id))
                        place_at_np = place_at_np + smt_coeff * np[t_id]

                smt_np = Or(smt_np, place_at_np > 0)
            # Keep out (NOTE halfspaces are Ax + b <= 0)
            solver.add(simplify(smt_np))

        sol = solver.check()
        if sol == unsat:
            ret = False
            logger.info('Z3 returns UNSAT: Cannot reduce without adding neg info')
        elif sol == unknown:
            ret = False
            logger.info('Z3 returns UNKNOWN: Cannot reduce in less than %s miliseconds', timeout)
        else:
            ret = solver.model()
        return ret

    @StopWatchObj.stopwatch
    def smt_simplify(self, sol):
        facets = set()
        if sol:
            for p_id, place in enumerate(self.facets):
                normal = []
                ti = sol[Int("b%s"%(p_id))].as_long()
                for t_id, val in enumerate(place.normal):
                    smt_coeff = Int("a%s,%s" % (p_id,t_id))
                    normal.append(sol[smt_coeff].as_long())
                if sum(abs(x) for x in normal) != 0:
                    facets.add(Halfspace(normal, ti))
                else:
                    logger.warning('Made all coefficients zero...weird!')
            self.facets = list(facets)

    @StopWatchObj.stopwatch
    def smt_hull_simplify(self, timeout=0):
        sol = self.smt_solution(timeout)
        while sol:
            self.smt_simplify(sol)
            sol = self.smt_solution(timeout)

    @StopWatchObj.stopwatch
    def smt_facet_simplify(self,timeout=0):
        for facet in self.facets:
            facet.smt_facet_simplify(neg_points=self.neg_points, timeout=timeout)
