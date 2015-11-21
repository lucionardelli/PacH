#!/usr/bin/env python
# -*- coding: UTF-8
import copy

from pach import PacH
from pnml import PnmlParser
from comparator import Comparator
from utils import rotate_dict
from config import logger


class ComparatorPnml(object):

    def __init__(self, filename, nfilename=None,
            max_coef=10, smt_timeout_iter=0, smt_timeout_matrix=0):
        self.filename = filename
        parser = PnmlParser(filename)
        parser.parse()
        self.net = parser.petrinet
        self.dim = parser.dim
        #self.event_dictionary = parser.event_dictionary

        # Helper pach. Doesn't actually compute hull
        self.pach = PacH(filename,nfilename=nfilename)
        self.pach.event_dictionary = parser.event_dictionary
        self.pach.reversed_dictionary = rotate_dict(parser.event_dictionary)
        self.pach.parse_negatives()

        qhull = self.net.get_qhull()
        # Hull for NO SMT
        qhull_no_smt = copy.deepcopy(qhull)
        # Hull for SMT iterative simp
        qhull_smt_iter = copy.deepcopy(qhull)
        # Hull for SMT matrix simp
        qhull_smt_matrix = copy.deepcopy(qhull)

        self.comparator = Comparator(qhull_no_smt, qhull_smt_iter, qhull_smt_matrix,
                max_coef, smt_timeout_iter, smt_timeout_matrix)

    def generate_pnml(self):
        output_pnml = self.filename
        output_pnml = (output_pnml.endswith('.pnml') and output_pnml[:-5])\
                or output_pnml or ''
        return self.comparator.generate_pnml(filename=output_pnml,
                reversed_dictionary=self.pach.reversed_dictionary)

    def compare(self):
        return self.comparator.compare()

    def generate_outputs(self):
        # For every benchmark, generate the output
        return self.comparator.generate_outputs(filename=self.filename)

if __name__ == '__main__':
    import sys, traceback, pdb
    from mains import pnml_comparator_main
    try:
        pnml_comparator_main()
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        #pdb.post_mortem(tb)


