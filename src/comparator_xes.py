#!/usr/bin/env python
# -*- coding: UTF-8
import copy

from pach import PacH
from comparator import Comparator
from config import logger


class ComparatorXes(object):

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
        qhull_no_smt = copy.deepcopy(qhull)
        # Hull for SMT iterative simp
        qhull_smt_iter = copy.deepcopy(qhull)
        # Hull for SMT matrix simp
        qhull_smt_matrix = copy.deepcopy(qhull)

        self.comparator = Comparator(qhull_no_smt, qhull_smt_iter, qhull_smt_matrix,
                max_coef, smt_timeout_iter, smt_timeout_matrix)

    def generate_pnml(self):
        return self.comparator.generate_pnml(filename=self.pach.filename,
                reversed_dictionary=self.pach.reversed_dictionary)

    def compare(self):
        return self.comparator.compare()

    def generate_outputs(self):
        # For every benchmark, generate the output
        qhull = self.comparator.qhull_no_smt
        self.pach.output.get('times',{}).update(qhull.output.get('times',{}))
        self.pach.qhull = qhull
        self.pach.smt_matrix = False
        self.pach.smt_iter = False
        self.pach.generate_output_file()
        logger.info('Generated output for NO SMT simplification')
        qhull = self.comparator.qhull_smt_iter
        self.pach.output.get('times',{}).update(qhull.output.get('times',{}))
        self.pach.qhull = qhull
        self.pach.smt_matrix = False
        self.pach.smt_iter = True
        self.pach.generate_output_file()
        logger.info('Generated output for Iterative SMT simplification')
        qhull = self.comparator.qhull_smt_matrix
        self.pach.output.get('times',{}).update(qhull.output.get('times',{}))
        self.pach.qhull = qhull
        self.pach.smt_matrix = True
        self.pach.smt_iter = False
        self.pach.generate_output_file()
        logger.info('Generated output for Matrix SMT simplification')
        return True

if __name__ == '__main__':
    import sys, traceback, pdb
    from mains import xes_comparator_main
    try:
        xes_comparator_main()
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        #pdb.post_mortem(tb)


