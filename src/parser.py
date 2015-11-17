#!/usr/bin/env python
# -*- coding: UTF-8
from os.path import isfile
from lxml import etree
import pdb
import numpy as np

from config import logger

from corrmatrix import CorrMatrix

class XesParser(object):

    def __init__(self,xes_file_name, verbose=False):
        if not isfile(xes_file_name):
            raise Exception("El archivo especificado no existe")
        self.filename = xes_file_name
        # Diferent presentation of Parikhs Vectors
        self.pv_set = set()
        self.pv_array = np.array([])
        self.pv_traces = {}
        self.parsed = False
        self.root = None
        self.traces = {}
        self.max_len = 0
        self.max_len_idx = None
        # Event to value
        self.event_dictionary = {}
        self.dim = 0
        self.verbose = verbose

    def __add_to_position(self, xs, position, value=1):
        """
        Given a list of numbers and a position, adds "value" to that position
        changing the same list
        """
        xs[position] += value

    def _parse(self):
        """
            parse xes file given as argument,
            returning a dict of trace (as list of char), and the lenght of it
                the maximum lenght in between all traces
                the (first) trace where this maximum is reached
        """
        tree = etree.parse(self.filename)
        self.root = tree.getroot()
        # Iteramos sobre todas las trazas
        for idx, trace in enumerate(self.root.iterchildren(tag='{*}trace')):
            # Iteramos sobre todos los eventos de la traza
            for event_idx, event in enumerate(trace.iterchildren(tag='{*}event')):
                # Solo nos interesa el valor
                values = [x.get('value') for x in\
                    event.iterchildren(tag='{*}string')\
                        if x.get('key') == "concept:name"]
                assert len(values) == 1, "No se puede obetner el  valor para el "\
                        "evento {0} de la traza {1}".format(event_idx, idx)
                value = values[0]
                # Buscamos la lista de puntos de la traza
                tr_val = self.traces.setdefault(idx,{'trace': [], 'length': 0,})
                if value not in self.event_dictionary:
                    self.event_dictionary[value] = len(self.event_dictionary)
                tr_val['trace'].append(value)
                tr_val['length'] += 1
                if tr_val['length'] > self.max_len:
                    self.max_len = tr_val['length']
                    self.max_len_idx = idx
        self.dim = len(self.event_dictionary)
        return True

    def parse(self):
        self._parse()
        self.parsed = True
        return self.parsed

    def _make_parikhs_vector(self):
        """
            make parickhs vector of all traces
        """
        hiper_zero = np.array([0]*self.dim)
        # El zero siempre pertencene a todos los Parikhs vector
        self.pv_set.add(tuple(hiper_zero))
        for idx,trace in self.traces.items():
            # El zero siempre pertencene a todos los Parikhs vector
            this_pv_trace = self.pv_traces.setdefault(idx,[hiper_zero])
            for val in trace['trace']:
                # No hay valor por defecto, debería estar siempre en el dict
                pos = self.event_dictionary.get(val)
                # Necesitamos una copia de la última lista para modificarla
                # y sumarle una ocurrencia al evento
                last_pv = this_pv_trace[-1].copy()
                self.__add_to_position(last_pv, pos, value=1)
                # Lo agregamos al conjunto de todos los puntos
                self.pv_set.add(tuple(last_pv))
                # Agregamos el parikh vector al látice de todos los puntos
                this_pv_trace.append(last_pv)
        self.pv_array = np.array(list(self.pv_set))
        return True

    def parikhs_vector(self):
        if not self.parsed:
            # Haven't even parsed the file!
            self.parse()
        self._make_parikhs_vector()
        if self.verbose:
            for trace in self.pv_traces:
                print 'Traza {0} with points:'.format(trace)
                for point in self.pv_traces[trace]:
                    print(point)
        logger.info('Se encontraron %s puntos en un espacio de dimensión %s',
                len(self.pv_set), self.dim)
        return True

class AdHocParser(XesParser):
    def _parse(self):
        """
            parse txt file given as argument,
            returning a dict of trace (as list of char), and the lenght of it
                the maximum lenght in between all traces
                the (first) trace where this maximum is reached
        """
        with open(self.filename,'r') as ffile:
            # Iteramos sobre todas las trazas
            for idx, trace in enumerate(ffile.readlines()):
                # Iteramos sobre todos los eventos de la traza
                trace = trace.replace('  ',' ')
                trace = trace.strip()
                trace = trace.replace('\n','')
                for event_idx, value in enumerate(trace.split(' ')):
                    # Buscamos la lista de puntos de la traza
                    tr_val = self.traces.setdefault(idx,{'trace': [], 'length': 0,})
                    if value not in self.event_dictionary:
                        self.event_dictionary[value] = len(self.event_dictionary)
                    tr_val['trace'].append(value)
                    tr_val['length'] += 1
                    if tr_val['length'] > self.max_len:
                        self.max_len = tr_val['length']
                        self.max_len_idx = idx
        self.dim = len(self.event_dictionary)
        return True

if __name__ == '__main__':
    import sys, traceback
    from mains import parser_main
    try:
        parser_main()
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        #pdb.post_mortem(tb)

