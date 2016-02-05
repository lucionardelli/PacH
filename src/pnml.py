#!/usr/bin/env python
# -*- coding: UTF-8
from os.path import isfile
from lxml import etree
import pdb

from config import logger

from petrinet import PetriNet,Place,Transition,Arc

class PnmlParser(object):

    def __init__(self,pnml_file_name, verbose=False):
        if not isfile(pnml_file_name):
            raise Exception("No such file")
        self.filename = pnml_file_name
        self.parsed = False
        self.petrinet = None
        self.root = None
        self.event_dictionary = {}
        self.dim = 0
        self.verbose = verbose

    def _parse(self):
        """
            parse pnml file given as argument,
        """
        tree = etree.parse(self.filename)
        self.root = tree.getroot()
        # Iteramos sobre todas las trazas

        net_node = self.root.find('{*}net')
        net_name = net_node.find('{*}name/{*}text').text
        net_id = net_node.get('id')

        net = PetriNet(net_id=net_id,name=net_name,filename=self.filename)
        # Iteramos sobre los places y los vamos agregando a la red
        for pl_node in net_node.iter('{*}place'):
            pl_id = pl_node.get('id')
            label = pl_node.find('{*}name/{*}text').text
            marking = pl_node.find('{*}initialMarking/{*}text')
            marking = marking is not None and int(marking.text) or 0
            pl = Place(net, pl_id, label=label, marking=marking)
            logger.debug('Creando el place %s',pl)
            if self.verbose:
                print 'Creando el place %s'%pl
        # Iteramos sobre las transiciones y las vamos agregando a la red
        # Una transition por cada variable, por lo que indica la dim
        dim = 0
        for tr_node in net_node.iter('{*}transition'):
            dim += 1
            tr_id = tr_node.get('id')
            label = tr_node.find('{*}name/{*}text').text
            if label not in self.event_dictionary:
                self.event_dictionary[label] = len(self.event_dictionary)
            tr = Transition(net, tr_id, label=label)
            logger.debug('Creando la transition %s',tr)
            if self.verbose:
                print 'Creando la transition %s'%tr
        # Iteramos sobre los arcos y los vamos agregando a la red
        for arc_node in net_node.iter('{*}arc'):
            arc_id = arc_node.get('id')
            from_id = arc_node.get('source')
            to_id = arc_node.get('target')
            try:
                value = int(arc_node.find('{*}value/{*}text').text)
            except:
                # Arcs whith value 1 does not specify value
                value = 1
            arc = Arc(net, arc_id, from_id, to_id, value=value)
            logger.debug('Creando el arco %s',arc)
            if self.verbose:
                print 'Creando el arco %s'%arc
        self.petrinet = net
        self.petrinet.event_dictionary = self.event_dictionary
        self.dim = dim
        return True

    def parse(self):
        self._parse()
        self.parsed = True
        return self.parsed

if __name__ == '__main__':
    import sys, traceback
    from mains import pnml_main
    try:
        pnml_main()
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        #pdb.post_mortem(tb)
