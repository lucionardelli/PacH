#!/usr/bin/env python
# -*- coding: UTF-8
from os.path import isfile
from lxml import etree
import pdb
import numpy as np
import logging

from config import logger
from corrmatrix import CorrMatrix

class GenericParser(object):

    def __init__(self, filename):
        if not isfile(filename):
            raise Exception("No such file")
        self.filename = filename
        # Diferent presentation of Parikhs Vectors
        self.pv_set = set()
        self.pv_array = np.array([])
        self.pv_traces = {}
        self.parsed = False
        self.traces = {}
        # Event to value
        self.event_dictionary = {}
        self.dim = 0
        # Represented petrinet
        self.petrinet = None

    def add_to_position(self, xs, position, value=1):
        """
        Given a list of numbers and a position, adds "value" to that position
        changing the same list
        """
        xs[position] += value

    def _parse(self):
        # Placeholder
        return True

    def parse(self):
        self._parse()
        self.parsed = True
        return self.parsed

    def _make_parikhs_vector(self):
        # Placeholder
        return True

    def parikhs_vector(self):
        if not self.parsed:
            # Haven't even parsed the file!
            self.parse()
        self._make_parikhs_vector()
        if logger.isEnabledFor(logging.DEBUG):
            for trace in self.pv_traces:
                logger.debug('Traza {0} with points:'.format(trace))
                for point in self.pv_traces[trace]:
                    logger.debug(point)
        logger.info('Se encontraron %s puntos en un espacio de dimensión %s',
                len(self.pv_set), self.dim)
        return True
