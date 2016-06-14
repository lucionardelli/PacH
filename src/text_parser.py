#!/usr/bin/env python
# -*- coding: UTF-8
from os.path import isfile
from lxml import etree
import pdb
import numpy as np

from config import logger

from generic_parser import GenericParser

class AdHocParser(GenericParser):
    def _parse(self):
        """
            parse txt file given as argument,
            returning a dict of trace (as list of char), and the lenght of it
                the maximum lenght in between all traces
                the (first) trace where this maximum is reached
        """
        with open(self.filename,'r') as ffile:
            # Iterate over traces
            for idx, trace in enumerate(ffile.readlines()):
                # Iterate over the events of the given trace
                trace = trace.replace('  ',' ')
                trace = trace.strip()
                trace = trace.replace('\n','')
                for event_idx, value in enumerate(trace.split(' ')):
                    # Search the list of points for current trace
                    tr_val = self.traces.setdefault(idx,{'trace': [], 'length': 0,})
                    if value not in self.event_dictionary:
                        self.event_dictionary[value] = len(self.event_dictionary)
                    tr_val['trace'].append(value)
                    tr_val['length'] += 1
        self.dim = len(self.event_dictionary)
        return True


    def _make_parikhs_vector(self):
        """
            make parickhs vector of all traces
        """
        hiper_zero = np.array([0]*self.dim)
        # Zero always belongs to the point lattice
        self.pv_set.add(tuple(hiper_zero))
        for idx,trace in self.traces.items():
            # Zero always belong to a Parikhs vector
            this_pv_trace = self.pv_traces.setdefault(idx,[hiper_zero])
            for val in trace['trace']:
                pos = self.event_dictionary.get(val)
                # Copy last point
                last_pv = this_pv_trace[-1].copy()
                # And add one to the corresponding event
                self.add_to_position(last_pv, pos, value=1)
                # Add it to the point set
                self.pv_set.add(tuple(last_pv))
                # Add the Parikh vector to the lattice of all points
                this_pv_trace.append(last_pv)
        self.pv_array = np.array(list(self.pv_set))
        return True


if __name__ == '__main__':
    import sys, traceback
    from mains import parser_main
    try:
        parser_main()
    except Exception, err:
        logger.error('Error: %s' % err, exc_info=True)
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        #pdb.post_mortem(tb)

