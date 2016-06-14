#!/usr/bin/env python
# -*- coding: UTF-8

from os.path import isfile
from lxml import etree
import pdb

from qhull import Qhull
#from smt_hull import SMTHull as Qhull
from halfspace import Halfspace

from config import logger

class PetriNet(object):
    """
    self.arcs: List of all arcs of this Petri net
    self.transitions: Map of (id, transition) of all transisions of this Petri net
    self.places: Map of (id, place) of all places of this Petri net
    """

    def __init__(self, net_id='', name=''):
        self.name= name or net_id or 'Generated automagically with PacH'
        nosp_name = self.name.replace(' ','_').lower()
        if nosp_name.endswith('.pnml'):
            nosp_name = nosp_name[:-5]
        self.id = net_id or nosp_name
        self.filename = nosp_name + '.pnml'
        # List or arcs
        self.arcs = []
        # Transitions
        self.transitions = {}
        # Places
        self.places = {}
        # Event to value
        self.event_dictionary = {}

    def __str__(self):
        return "PetriNet: '{0}' with {1} Transitions, {2} Places and {3} Arcs".format(
                self.name, len(self.transitions), len(self.places), len(self.arcs))

    def __repr__(self):
        return self.__str__()

    def save(self, filename=None):
        pnml = etree.Element('pnml')
        net = etree.SubElement(pnml, 'net', id=self.id, type="http://www.pnml.org/version-2009/grammar/ptnet")
        net_name = etree.SubElement(net, 'name')
        net_name_text = etree.SubElement(net_name, 'text')
        net_name_text.text = self.name

        page = etree.SubElement(net, 'page', id='page')

        for tr_id, tr in self.transitions.items():
            transition = etree.SubElement(page, 'transition', id=tr_id)
            transition_name = etree.SubElement(transition, 'name')
            transition_name_text = etree.SubElement(transition_name, 'text')
            transition_name_text.text = tr.label

        for pl_id, pl in self.places.items():
            place = etree.SubElement(page, 'place', id=pl_id)
            place_name = etree.SubElement(place, 'name')
            place_name_text = etree.SubElement(place_name, 'text')
            place_name_text.text = pl.label
            place_init_mark = etree.SubElement(place, 'initialMarking')
            place_init_mark_text = etree.SubElement(place_init_mark, 'text')
            place_init_mark_text.text = str(pl.marking)

        for arc in self.arcs:
            if arc.source is None or arc.destination is None:
                logger.error("Invalid ar found: [%s] %s",arc.id,arc)
                continue
            arc_node = etree.SubElement(page, 'arc', id=arc.id,
                    source=arc.source.id, target=arc.destination.id)
            if arc.value > 1:
                arc_value = etree.SubElement(arc_node, 'inscription')
                arc_value_text = etree.SubElement(arc_value, 'text')
                arc_value_text.text = str(arc.value)
        tree = etree.ElementTree(element=pnml)
        tree.write(filename or self.filename, encoding="utf-8",
                xml_declaration=True, method="xml", pretty_print=True)
        logger.info('Generated the PNML %s', self.name)

    def get_qhull(self, neg_points=[], allow_dummy=False):
        """ From a Petrinet, gets it's representationas a Convex Hull
        """
        # Create an empty Convex Hull
        qhull = Qhull(neg_points=neg_points)
        # Default normal for every facet
        dim = len(self.transitions)
        tmpl_normal = [0]*dim
        # Each transition corresponds to one dimension
        # transition.label -> dimension number
        transitions = self.event_dictionary
        # Each facet corresponds to one place
        # place.id -> {normal->[arc.value], offset->marking}
        facets_dict = {}
        for arc in self.arcs:
            # No arc should have zero weight
            if not arc.value:
                logger.error('We found a zero arc: %s',arc)
                raise Exception('We found a zero arc: %s'%arc)
            # NOTE internal representation for Half Spaces
            # is A.x <= 0 instead of A.x >= 0
            if isinstance(arc.source,Transition):
                # If the arc starts in a transition, coefficient should be < 0
                coef = -1*arc.value
                transition = arc.source
                place = arc.destination
            else:
                # If the arc starts in a place, coefficient should be > 0
                coef = arc.value
                place = arc.source
                transition = arc.destination
            x = transitions.setdefault(transition.label,len(transitions))
            facet = facets_dict.setdefault(place.id,{'normal':list(tmpl_normal),
                                                    'in_transitions':[],
                                                    'in_loop': False,
                                                    'out_transitions':[],
                                                    'offset': -1*place.marking,
                                                    'id':place.id})
            if coef < 0:
                facet['in_transitions'].append(transition.label)
            else:
                facet['out_transitions'].append(transition.label)
            # If coefficient for this facet has already been loaded,
            # It means we are in a loop. And once we go loop, we never go back
            if (facet['normal'][x] and allow_dummy) or facet['in_loop']:
                logger.debug('Coeficient already loaded. Loop found for place %s and transition %s! Dummy place?'%(place,transition))
                facet['in_loop'] = True
                coef = 0
            elif facet['normal'][x]:
                raise Exception('Loop found in place %s and transition %s'%(place,transition))
            else:
                facet['normal'][x] = coef

        facets = []
        for pl_id, facet in facets_dict.items():
            # Do not create the facet for dummy places
            if not any(facet['normal']):
                continue
            # Values are always integer
            hs = Halfspace(facet['normal'], facet['offset'], integer_vals=False)
            logger.debug('Adding facet %s',hs)
            facets.append(hs)
        # Remove duplicate facets
        facets = list(set(facets))
        qhull.dim = dim
        qhull.facets = facets
        return qhull

class Transition(object):
    """ Represents a transition of a Petri net.
    """

    def __init__(self, net, tr_id, label=''):
        self.id = tr_id
        self.label = label or 'Transition %s'%(tr_id)
        net.transitions[self.id] = self
        self.__net = net

    def __str__(self):
        return 'Transition {0}'.format(self.label)
    def __repr__(self):
        return self.__str__()

class Place(object):
    """ Represents a place of a Petri net.
    """

    def __init__(self, net, place_id, label='', marking=0):
        self.id = place_id
        self.label = label or 'Place %s'%(tr_id)
        self.marking = marking
        net.places[self.id] = self
        self.__net = net

    def __str__(self):
        return 'Place {0}'.format(self.label)
    def __repr__(self):
        return self.__str__()

class Arc(object):
    """ Represents an arc of a Petri net.
    """

    def __init__(self, net, arc_id, from_id, to_id, value=1):
        self.id = arc_id
        self.from_id = from_id
        self.to_id = to_id
        self.value = value
        net.arcs.append(self)
        self.__net = net
        self._qhull = None

    @property
    def source(self):
        if self.from_id in self.__net.transitions:
            ret =  self.__net.transitions.get(self.from_id)
        else:
            ret = self.__net.places.get(self.from_id)
        return ret

    @property
    def destination(self):
        if self.to_id in self.__net.transitions:
            ret =  self.__net.transitions.get(self.to_id)
        else:
            ret = self.__net.places.get(self.to_id)
        return ret

    def __str__(self):
        return "Arc {0} -> {1}".format(self.source,self.destination)
    def __repr__(self):
        return self.__str__()


