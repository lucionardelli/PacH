#!/usr/bin/env python
# -*- coding: UTF-8
from os.path import isfile
from lxml import etree
import pdb

from config import logger

from petrinet import PetriNet,Place,Transition,Arc
from generic_parser import GenericParser


class PnmlParser(GenericParser):

    def _parse(self):
        """
            parse pnml file given as argument,
        """
        tree = etree.parse(self.filename)
        root = tree.getroot()
        # Iteramos sobre todas las trazas

        net_node = root.find('{*}net')
        net_name = net_node.find('{*}name/{*}text').text
        net_id = net_node.get('id')

        net = PetriNet(net_id=net_id, name=net_name)
        # Iteramos sobre los places y los vamos agregando a la red
        for pl_node in net_node.iter('{*}place'):
            pl_id = pl_node.get('id')
            label = pl_node.find('{*}name/{*}text').text
            marking = pl_node.find('{*}initialMarking/{*}text')
            marking = marking is not None and int(marking.text) or 0
            pl = Place(net, pl_id, label=label, marking=marking)
            logger.debug('Creando el place %s',pl)
        # Iteramos sobre las transiciones y las vamos agregando a la red
        # Una transition por cada variable, por lo que indica la dim
        dim = 0
        for tr_node in net_node.iter('{*}transition'):
            dim += 1
            tr_id = tr_node.get('id')

            # NOTE Remove "+complete" (if any) from label.
            # this have been automatically added in ohter miners
            label = tr_node.find('{*}name/{*}text').text.replace('+complete','')
            if label not in self.event_dictionary:
                self.event_dictionary[label] = len(self.event_dictionary)
            tr = Transition(net, tr_id, label=label)
            logger.debug('Creando la transition %s',tr)
        # Iteramos sobre los arcos y los vamos agregando a la red
        for arc_node in net_node.iter('{*}arc'):
            arc_id = arc_node.get('id')
            from_id = arc_node.get('source')
            to_id = arc_node.get('target')
            try:
                value = int(arc_node.find('{*}inscription/{*}text').text)
            except:
                # Arcs whith value 1 does not specify value
                value = 1
            arc = Arc(net, arc_id, from_id, to_id, value=value)
            logger.debug('Creando el arco %s',arc)
        self.petrinet = net
        self.petrinet.event_dictionary = self.event_dictionary
        self.dim = dim
        return True

    def parikhs_vector(self):
        raise NotImplemented("PNML parser doesn't have (nor will have) this method")

if __name__ == '__main__':
    import sys, traceback
    from mains import pnml_main
    try:
        pnml_main()
    except Exception, err:
        logger.error('Error: %s' % err, exc_info=True)
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        #pdb.post_mortem(tb)
