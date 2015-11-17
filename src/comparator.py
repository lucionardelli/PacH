#!/usr/bin/env python
# -*- coding: UTF-8
import time
import numpy as np
import copy

from custom_exceptions import CannotGetHull, WrongDimension, CannotIntegerify
from pach import PacH
from config import logger


class Comparator(object):

    def __init__(self, filename,
            samp_num=1, samp_size=None,
            proj_size=None, proj_connected=True,
            nfilename=None, max_coef=10,
            smt_timeout_iter=0,
            smt_timeout_matrix=0,
            sanity_check=False):
        self.pach = PacH(filename,
            samp_num=samp_num, samp_size=samp_size,
            proj_size=proj_size, proj_connected=proj_connected,
            nfilename=nfilename, max_coef=max_coef,
            sanity_check=sanity_check)
        self.pach.parse()

        qhull = self.pach.qhull
        # Hull for NO SMT
        self.qhull_no_smt = copy.deepcopy(qhull)
        # Hull for SMT iterative simp
        self.timeout_smt_iter = smt_timeout_iter
        self.qhull_smt_iter = copy.deepcopy(qhull)
        # Hull for SMT matrix simp
        self.timeout_smt_matrix = smt_timeout_matrix
        self.qhull_smt_matrix = copy.deepcopy(qhull)

    def neg_simp_no_smt(self):
        # No smt simplification
        if self.pach.nfilename:
            logger.info('NO-SMT: Starting to simplify model from negative points')
            qhull = self.qhull_no_smt
            old_len = len(qhull.facets)
            qhull.no_smt_simplify(max_coef=self.pach.max_coef)
            removed = len(qhull.facets) - old_len
            if removed:
                logger.info('NO-SMT: We removed %d facets without allowing negative points',removed)
            else:
                logger.info("NO-SMT: Couldn't simplify model without adding negative points")

    def neg_simp_smt_iterative(self):
        # Iterative smt simplification
        if self.pach.nfilename:
            logger.info('SMT-ITER: Starting to simplify model from negative points')
            qhull = self.qhull_smt_iter
            old_len = len(qhull.facets)
            qhull.smt_facet_simplify(timeout=self.timeout_smt_iter)
            removed = len(qhull.facets) - old_len
            if removed:
                logger.info('SMT-ITER: We removed %d facets without allowing negative points',removed)
            else:
                logger.info("SMT-ITER: Couldn't simplify model without adding negative points")

    def neg_simp_smt_matrix(self):
        # Matrix smt simplification
        if self.pach.nfilename:
            logger.info('SMT-MATRIX: Starting to simplify model from negative points')
            qhull = self.qhull_smt_matrix
            old_len = len(qhull.facets)
            qhull.smt_hull_simplify(timeout=self.timeout_smt_matrix)
            removed = len(qhull.facets) - old_len
            if removed:
                logger.info('SMT-MATRIX: We removed %d facets without allowing negative points',removed)
            else:
                logger.info("SMT-MATRIX: Couldn't simplify model without adding negative points")

    def complexity(self):
        return {'no_smt': self.qhull_no_smt.complexity(),
                'smt_iterative': self.qhull_smt_iter.complexity(),
                'smt_matrix': self.qhull_smt_matrix.complexity(),
                }

    def generate_pnml(self):
        def_name = self.pach.get_def_pnml_name()
        if def_name.endswith('.pnml'):
            def_name = def_name[:-5]
        # For every benchmark, generate a PNML
        for benchmark in ['no_smt', 'smt_iter', 'smt_matrix']:
            qhull = getattr(self,'qhull_'+benchmark)
            self.pach.qhull = qhull
            filename = def_name + '_' + benchmark + '.pnml'
            self.pach.generate_pnml(filename=filename)
            logger.info('Generated the PNML %s for %s', filename, benchmark)
        return True

    def compare(self):
        self.neg_simp_no_smt()
        self.neg_simp_smt_iterative()
        self.neg_simp_smt_matrix()
        return self.complexity()

    def generate_outputs(self):
        # For every benchmark, generate the output
        qhull = self.qhull_no_smt
        self.pach.output.get('times',{}).update(qhull.output.get('times',{}))
        self.pach.qhull = qhull
        self.pach.smt_matrix = False
        self.pach.smt_iter = False
        self.pach.generate_output_file()
        logger.info('Generated output for NO SMT simplification')
        qhull = self.qhull_smt_iter
        self.pach.output.get('times',{}).update(qhull.output.get('times',{}))
        self.pach.qhull = qhull
        self.pach.smt_matrix = False
        self.pach.smt_iter = True
        self.pach.generate_output_file()
        logger.info('Generated output for Iterative SMT simplification')
        qhull = self.qhull_smt_matrix
        self.pach.output.get('times',{}).update(qhull.output.get('times',{}))
        self.pach.qhull = qhull
        self.pach.smt_matrix = True
        self.pach.smt_iter = False
        self.pach.generate_output_file()
        logger.info('Generated output for Matrix SMT simplification')
        return True

if __name__ == '__main__':
    import sys, traceback, pdb
    from mains import comparator_main
    try:
        comparator_main()
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        #pdb.post_mortem(tb)


