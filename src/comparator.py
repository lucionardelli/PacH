#!/usr/bin/env python
# -*- coding: UTF-8
import copy
from os.path import isfile

from pach import PacH
from parser import XesParser
from config import logger
class Comparator(object):

    def __init__(self, no_smt_qhull, iter_qhull, matrix_qhull,
            max_coef=10, smt_timeout_iter=30, smt_timeout_matrix=300):
        # Hull for NO SMT
        self.max_coef = max_coef
        self.qhull_no_smt = no_smt_qhull
        self.no_smt_initial_complexity = no_smt_qhull.complexity()
        # Hull for SMT iterative simp
        self.timeout_smt_iter = smt_timeout_iter
        self.qhull_smt_iter =  iter_qhull
        self.iter_initial_complexity = iter_qhull.complexity()
        # Hull for SMT matrix simp
        self.timeout_smt_matrix = smt_timeout_matrix
        self.qhull_smt_matrix = matrix_qhull
        self.matrix_initial_complexity = matrix_qhull.complexity()
        assert no_smt_qhull.dim == iter_qhull.dim == matrix_qhull.dim,\
                'The 3 hulls must have the same dimention'
        self.dim = self.qhull_no_smt.dim

    def neg_simp_no_smt(self,log_file='',event_dictionary={}):
        # No smt simplification
        logger.info('NO-SMT: Starting to simplify model from negative points')
        qhull = self.qhull_no_smt
        old_len = len(qhull.facets)
        qhull.no_smt_simplify(max_coef=self.max_coef)
        if log_file and log_file.endswith('.xes'):
            # Sanity check
            qhull.all_in_file(log_file, event_dictionary=event_dictionary)
        removed = old_len - len(qhull.facets)
        if removed:
            logger.info('NO-SMT: We removed %d facets without allowing negative points',removed)
        else:
            logger.info("NO-SMT: Couldn't simplify model without adding negative points")

    def neg_simp_smt_iterative(self):
        # Iterative smt simplification
        logger.info('SMT-ITER: Starting to simplify model from negative points')
        qhull = self.qhull_smt_iter
        old_len = len(qhull.facets)
        qhull.smt_facet_simplify(timeout=self.timeout_smt_iter)
        removed = old_len - len(qhull.facets)
        if removed:
            logger.info('SMT-ITER: We removed %d facets without allowing negative points',removed)
        else:
            logger.info("SMT-ITER: Couldn't simplify model without adding negative points")

    def neg_simp_smt_matrix(self):
        # Matrix smt simplification
        logger.info('SMT-MATRIX: Starting to simplify model from negative points')
        qhull = self.qhull_smt_matrix
        old_len = len(qhull.facets)
        qhull.smt_hull_simplify(timeout=self.timeout_smt_matrix)
        removed = old_len - len(qhull.facets)
        if removed:
            logger.info('SMT-MATRIX: We removed %d facets without allowing negative points',removed)
        else:
            logger.info("SMT-MATRIX: Couldn't simplify model without adding negative points")

    def complexity(self):
        return {'no_smt': self.qhull_no_smt.complexity(),
                'smt_iterative': self.qhull_smt_iter.complexity(),
                'smt_matrix': self.qhull_smt_matrix.complexity(),
                }

    def generate_pnml(self, filename='', reversed_dictionary={}):
        filename = filename or 'Generated automagically comparator.py'
        pach = PacH(filename)
        pach.reversed_dictionary = reversed_dictionary
        pach.dim = self.dim
        def_name = pach.get_def_pnml_name()
        if def_name.endswith('.pnml'):
            def_name = def_name[:-5]
        # For every benchmark, generate a PNML
        for benchmark in ['no_smt', 'smt_iter', 'smt_matrix']:
            qhull = getattr(self,'qhull_'+benchmark)
            pach.qhull = qhull
            filename = def_name + '_' + benchmark + '.pnml'
            pach.generate_pnml(filename=filename)
            logger.info('Generated the PNML %s for %s', filename, benchmark)
        return True

    def compare(self,log_file='', event_dictionary={}):
        self.neg_simp_no_smt(log_file=log_file, event_dictionary=event_dictionary)
        self.neg_simp_smt_iterative()
        self.neg_simp_smt_matrix()
        return self.complexity()

    def generate_outputs(self, filename=''):
        filename = filename or 'Generated automagically'
        pach = PacH(filename)
        pach.dim = self.dim
        # For every benchmark, generate the output
        qhull = self.qhull_no_smt
        pach.output.get('times',{}).update(qhull.output.get('times',{}))
        pach.qhull = qhull
        pach.smt_matrix = False
        pach.smt_iter = False
        # Force initial complexity for effectiveness calculation
        pach.initial_complexity = self.no_smt_initial_complexity
        pach.generate_output_file()
        logger.info('Generated output for NO SMT simplification')
        qhull = self.qhull_smt_iter
        pach.output.get('times',{}).update(qhull.output.get('times',{}))
        pach.qhull = qhull
        pach.smt_matrix = False
        pach.smt_iter = True
        # Force initial complexity for effectiveness calculation
        pach.initial_complexity = self.iter_initial_complexity
        pach.generate_output_file()
        logger.info('Generated output for Iterative SMT simplification')
        qhull = self.qhull_smt_matrix
        pach.output.get('times',{}).update(qhull.output.get('times',{}))
        pach.qhull = qhull
        pach.smt_matrix = True
        pach.smt_iter = False
        # Force initial complexity for effectiveness calculation
        pach.initial_complexity = self.matrix_initial_complexity
        pach.generate_output_file()
        logger.info('Generated output for Matrix SMT simplification')
        return True

    def check_hull(self, log_file='', event_dictionary={}):
        if not (log_file.endswith('.xes')):
            print log_file, ' does not end in .xes. It should...'
            raise Exception('Filename does not end in .xes')
        if not isfile(log_file):
            raise Exception("No such file")
        # For every benchmark, check that the hull accepts the positive log
        parser = XesParser(log_file)
        parser.event_dictionary = event_dictionary or {}
        parser.parse()
        parser.parikhs_vector()
        for benchmark in ['no_smt', 'smt_iter', 'smt_matrix']:
            qhull = getattr(self,'qhull_'+benchmark)
            try:
                qhull.all_in(parser.pv_set)
            except Exception, err:
                logger.error("Error running check_hull for %s, file %s",benchmark, log_file, exc_info=True)
                raise
        return True
