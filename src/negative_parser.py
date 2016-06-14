#!/usr/bin/env python
# -*- coding: UTF-8
from os.path import isfile
from lxml import etree
import pdb
import numpy as np

from config import logger

from generic_parser import GenericParser

class NegativeParser(GenericParser):

    def __init__(self,filename,
            # New values required for negative traces
            required_dimension=0, event_dictionary=None):
        super(NegativeParser,self).__init__(filename)
        self.event_dictionary = event_dictionary or {}
        self.rdim = required_dimension or len(self.event_dictionary)

    def _parse(self):
        """
            parse xes file given as argument,
            returning a dict of trace (as list of char), and the lenght of it
                the maximum lenght in between all traces
                the (first) trace where this maximum is reached
        """
        tree = etree.parse(self.filename)
        self.root = tree.getroot()
        # Iterate over traces
        for idx, trace in enumerate(self.root.iterchildren(tag='{*}trace')):
            # Iterate over the events of the given trace
            for event_idx, event in enumerate(trace.iterchildren(tag='{*}event')):
                # We only care fot the value
                values = [x.get('value') for x in\
                    event.iterchildren(tag='{*}string')\
                        if x.get('key') == "concept:name"]
                assert len(values) == 1, "No se puede obetner el  valor para el "\
                        "evento {0} de la traza {1}".format(event_idx, idx)
                value = values[0]
                # Search the list of points for current trace
                tr_val = self.traces.setdefault(idx,{'trace': [], 'length': 0,})
                if value not in self.event_dictionary:
                    self.event_dictionary[value] = len(self.event_dictionary)
                tr_val['trace'].append(value)
                tr_val['length'] += 1
        self.dim = self.rdim or len(self.event_dictionary)
        return True

    def _make_parikhs_vector(self):
        """
            make parickhs vector of all traces
        """
        hiper_zero = np.array([0]*self.dim)
        # Zero DOERSN'T belong to the negative point lattice
        for idx,trace in self.traces.items():
            # Start from the beginning (i.e. from zero)
            this_pv_trace = self.pv_traces.setdefault(idx,[np.copy(hiper_zero)])
            for val in trace['trace']:
                pos = self.event_dictionary.get(val)
                # Search for the point representing the trace
                # and add this event occurrence
                neg_pv = this_pv_trace[0]
                self.add_to_position(neg_pv, pos, value=1)
            # Only add the last negative point
            # (Other points might or might not be belong to the traces)
            self.pv_set.add(tuple(neg_pv))
        self.pv_array = np.array(list(self.pv_set))
        return True

if __name__ == '__main__':
    import sys, traceback
    from mains import negative_parser_main
    try:
        negative_parser_main()
    except Exception, err:
        logger.error('Error: %s' % err, exc_info=True)
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)

