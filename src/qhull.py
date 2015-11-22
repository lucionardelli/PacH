#!/usr/bin/env python
# -*- coding: UTF-8
from pyhull import qconvex
from utils import get_positions
from halfspace import Halfspace
from parser import XesParser
from custom_exceptions import IncorrectOutput, CannotGetHull, LostPoints
from stopwatch_wrapper import stopwatch

import sys
from redirect_output import stderr_redirected
try:
    import z3
except:
    pass

from config import logger

class Qhull(object):

    def __init__(self, points=[], neg_points=[], verbose=False):
        self.points = set(points)
        self.neg_points = set(neg_points)
        self.facets = []
        self.verbose = verbose
        self.output = {}

    def __contains__(self, point):
        return self.is_inside(point)

    def __parse_hs_output(self, output):
        """
         input: Output string for ConvexHull
            The first line is the dimension.
            The second line is the number of facets.
            Each remaining line is the hyperplane's coefficient
                followed by its offset.
         output: (dimension,nbr_facets,[halfspaces])
        """
        try:
            dim = int(output.pop(0)) - 1
            facets_nbr = output.pop(0)
            prepare = [[float(i) for i in row.strip().split()]
                    for row in output]
            facets = [Halfspace(out[:-1],out[-1]) for out in prepare]
        except:
            raise IncorrectOutput()
        return (dim, facets_nbr, facets)

    @stopwatch
    def compute_hiperspaces(self):
        # La característica heurística al buscar conexiones entre
        # diferentes clusters hace que pueda fallar
        # por lo que redirigimos la salida para ser silenciosos
        # en esos casos
        if not len(self.points) > 0:
            logger.error('No points to compute hull!')
            raise Exception('No points to compute hull!')
        stderr_fd = sys.stderr.fileno()
        with open('/tmp/qhull-output.log', 'w') as f, stderr_redirected(f):
            points = list(self.points)
            logger.info('Searching for hull in dimension %s based on %s points',
                    len(points[0]),len(points))
            output = qconvex('n',points)
            if len(output) == 1:
                logger.debug('Could not get Hull. Joggle input?')
        try:
            dim, facets_nbr, facets = self.__parse_hs_output(output)
        except IncorrectOutput:
            logger.warning('Could not get hull')
            raise CannotGetHull()
        logger.info('Found hull in dimension %s of %s facets',
                dim,len(facets))
        self.dim = dim
        self.facets = facets
        if self.verbose:
            print "Computed MCH with ",facets_nbr," halfspaces"
            print 'This are them:\n'
            for facet in self.facets:print facet
        return self.dim

    @stopwatch
    def prepare_negatives(self):
        positive_points = len(self.points)
        actual_neg_points = []
        for npoint in self.neg_points:
            if npoint not in self:
                actual_neg_points.append(npoint)
                positive_points -= 1
        self.net_points = actual_neg_points

    def union(self, facets):
        """
         Merge hull to a list of facets
        """
        fdim = None
        for facet in facets:
            if fdim is None:
                fdim = facet.dim
            else:
                assert fdim == facet.dim, "Not all facets to be merge hava the"\
                        " same dimension!"
        # If fdim is None the facets to merge is empty. We can always do that
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
        """
        ret = {}
        inside = ret.setdefault('inside',[])
        outside = ret.setdefault('outside',[])
        dyt = False
        positions = []
        for point in points:
            if len(point) != self.dim:
                raise ValueError("Convex Hulls and points must live in the same"\
                        " dimension!")
            if point in self:
                inside.append(point)
            else:
                #Shouldn't happen
                really = not point in self
                outside.append(point)
        return ret

    def all_in_file(self, filename, event_dictionary=None):
        # Esto es para chequear que no dejando a nadia afuera
        # hace todo más lento en ejemplos grandes
        parser = XesParser(filename)
        parser.event_dictionary = event_dictionary or {}
        parser.parse()
        parser.parikhs_vector()
        return self.all_in(parser.pv_set)

    @stopwatch
    def all_in(self, points):
        # Esto es para chequear que no dejando a nadia afuera
        # hace todo más lento en ejemplos grandes
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
         "extended" it (making all the other variables zero)
         to the original dimension
        """
        # Nuevamente los odeno y busco la posición
        # en el eigenvector original. Luego "agrando"
        # el qhull en concordancia
        cluster = list(set([abs(x) for x in cluster]))
        cluster.sort(reverse=True)
        orig_dim = orig_dim or self.dim
        proj_idx = []
        for proj in cluster:
            # Cuando conectamos dos proyecciones pasamos ambos valores concatenados
            proj_idx += [idx%orig_dim for idx,val in enumerate(eigen) if abs(val) == proj\
                    and idx%orig_dim not in proj_idx]
        self.extend_dimension(orig_dim, proj_idx)

    def can_eliminate(self,candidate, npoint):
        ret = False
        for facet in set(self.facets)-set(candidate):
            if not facet.inside(npoint):
                ret = True
                break
        return ret

    @stopwatch
    def no_smt_simplify(self, max_coef=10):
        facets = list(self.facets)
        popped = 0
        for idx,facet in enumerate(self.facets):
            if max_coef and len([x for x in facet.normal + [facet.offset]\
                    if abs(x) > max_coef]) > 0:
                # If the max coef is inside the expected
                # we don't try to remove it
                # Creamos un dummy hull para guardar los facets
                # menos el que se considera para eliminar
                tmpqhull = Qhull(set())
                tmpqhull.facets = list(set(facets)-set([facet]))
                simplify = True
                for npoint in self.neg_points:
                    if npoint in tmpqhull:
                        simplify = False
                        break
                if simplify:
                    facets.pop(idx - popped)
                    popped += 1
        logger.info('Popped %d facets using negative info',popped)
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
    @stopwatch
    def smt_solution(self,timeout):
        solver = z3.Solver()
        solver.set("timeout", timeout)

        diff_sol = False
        non_trivial = False
        A1 = True
        A2 = True
        for p_id, place in enumerate(self.facets):
            b = place.offset
            z3_b = z3.Int("b" + str(p_id))
            if b > 0:
                solver.add(z3_b >= 0)
                solver.add(z3_b <= b)
            elif b< 0:
                solver.add(z3_b <= 0)
                solver.add(z3_b >= b)
            else:
                solver.add(z3_b == 0)

            pos_x = True
            simple = sum(abs(x) for x in place.normal) <= 1
            diff_sig = reduce(lambda x,y:x*y, [x + 1 for x in place.normal]) < 1

            if not simple and diff_sig:
                some_produce = False
                some_consume = False
            h1 = b
            h2 = z3_b
            variables = []
            for t_id, val in enumerate(place.normal):
                z3_val = z3.Int("a" + str(p_id) + "," + str(t_id))
                x = z3.Int("x" + str(t_id))
                variables.append(x)
                pos_x = z3.And(pos_x, x >= 0)
                if val:
                    if val > 0:
                        solver.add(0 <= z3_val)
                        solver.add(z3_val <= val)
                    else:
                        solver.add(val <= z3_val)
                        solver.add(z3_val <= 0)
                    if not simple and diff_sig:
                        some_consume = z3.Or(some_consume, z3_val < 0)
                        some_produce = z3.Or(some_produce, z3_val > 0)
                    non_trivial = z3.Or(non_trivial, z3_val != 0)
                    diff_sol = z3.Or(diff_sol, z3_val != val)
                    h1 = h1 + val * x
                    h2 = h2 + z3_val * x
                else:
                    solver.add(z3_val == 0)
            if not simple and diff_sig:
                solver.add(z3.simplify(some_consume))
                solver.add(z3.simplify(some_produce))
            A1 = z3.And(A1, h1 <= 0)
            A2 = z3.And(A2, h2 <= 0)
        solver.add(z3.simplify(non_trivial))
        solver.add(z3.simplify(diff_sol))
        solver.add(z3.simplify(z3.ForAll(variables, z3.Implies(z3.And(pos_x, A1), A2))))
        ## non negative point should be a solution
        for np in list(self.neg_points)[:min(100,len(self.neg_points))]:
            smt_np = False
            for p_id, place in enumerate(self.facets):
                ineq_np = place.offset
                for t_id, val in enumerate(place.normal):
                    z3_var = z3.Int("a" + str(p_id) + "," + str(t_id))
                    ineq_np = ineq_np + z3_var * np[t_id]
                smt_np = z3.simplify(z3.Or(smt_np, ineq_np < 0))
            solver.add(smt_np)
        sol = solver.check()
        if sol == z3.unsat or sol == z3.unknown:
            ret = False
        else:
            ret = solver.model()
        return ret

    @stopwatch
    def smt_simplify(self, sol):
        facets = []
        if sol:
            for p_id, place in enumerate(self.facets):
                normal = []
                b = int(str(sol[z3.Int("b" + str(p_id))]))
                for t_id, val in enumerate(place.normal):
                    z3_val = z3.Int("a" + str(p_id) + "," + str(t_id))
                    normal.append(int(str(sol[z3_val] or 0)))
                if sum(abs(x) for x in normal) != 0:
                    f = Halfspace(normal, b, integer_vals=False)
                    if not f in facets:
                        facets.append(f)
            self.facets = facets

    @stopwatch
    def smt_hull_simplify(self,timeout=0):
        sol = self.smt_solution(timeout)
        while sol:
            self.smt_simplify(sol)
            sol = self.smt_solution(timeout)

    @stopwatch
    def smt_facet_simplify(self,timeout=0):
        for facet in self.facets:
            facet.smt_facet_simplify(neg_points=self.neg_points,timeout=timeout)

if __name__ == '__main__':
    import sys, traceback,pdb
    from mains import qhull_main
    try:
        qhull_main()
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        #pdb.post_mortem(tb)

