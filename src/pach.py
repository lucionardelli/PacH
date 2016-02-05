#!/usr/bin/env python
# -*- coding: UTF-8
from qhull import Qhull
from parser import XesParser, AdHocParser
from negative_parser import NegativeParser
from corrmatrix import CorrMatrix
from halfspace import Halfspace
from petrinet import PetriNet, Place, Transition, Arc
from utils import get_positions, rotate_dict
import time
import numpy as np
from random import sample
from datetime import datetime
import os

from custom_exceptions import CannotGetHull, WrongDimension, CannotIntegerify
from sampling import sampling
from projection import projection
from stopwatch_wrapper import stopwatch

from config import logger

class PacH(object):
    def __init__(self, filename, verbose=False,
            samp_num=1, samp_size=None,
            proj_size=None, proj_connected=True,
            nfilename=None, max_coef=10,
            smt_matrix=False,
            smt_iter=False,
            smt_timeout=0,
            sanity_check=False):
        # El archivo de trazas
        logger.info('Positive traces file: %s', filename)
        self.filename = filename
        # El archivo de trazas negativas (if any)
        self.nfilename = nfilename
        logger.info('Negative traces file: %s', nfilename)
        self.verbose = verbose
        # Referentes a las trazas
        self.pv_traces = {}
        self.pv_set = set()
        self.pv_array = np.array([])
        self._qhull = None
        # Referentes a las trazas negativas
        self.max_coef = max_coef
        self.npv_traces = {}
        self.npv_set = set()
        self.npv_array = np.array([])
        # Inicialización de varibales
        self.dim = 0
        if smt_matrix:
            logger.info('Will apply SMT simplification')
        elif smt_iter:
            logger.info('Will apply iterative SMT simplifications')
        else:
            logger.info('No SMT simplification')
        self.smt_iter = smt_iter
        self.smt_matrix = smt_matrix
        self.smt_timeout = smt_timeout
        # Sampling configuration
        # At least we need one "sample"
        self.samp_num = max(samp_num,1)
        if self.samp_num > 1:
            logger.info('Will apply %s samples',self.samp_num)
        self.samp_size = samp_size
        if self.samp_size and self.samp_size != 0:
            logger.info('Samples will have %s points',self.samp_size)
        # Projection configuration
        self.projections = {}
        # If proj_size is None, do not do projection
        if proj_size is not None:
            if proj_size:
                logger.info('Will apply projections of no more of %s points',
                        proj_size)
            else:
                logger.info('Will apply unbonded projections')
        self.proj_size = proj_size
        if proj_connected:
            logger.info('Will try to connect the projections')
        self.proj_connected = proj_connected
        # Do Sanity check after projectiong?
        self.sanity_check = sanity_check
        pp_file = os.path.basename(filename)
        if nfilename:
            pp_nfile = os.path.basename(nfilename)
        else:
            pp_nfile = ''
        self.output = { 'positive': pp_file,
                'negative': pp_nfile,
                'time': '%s'%datetime.now(),
                'dimension': 0,
                'traces': 0,
                'events': 0,
                'complexity': 0,
                'benchmark': '',
                'parse_traces': 0,
                'compute_hiperspaces': 0,
                'overall_time': 0,
                'times': {}}

    @stopwatch
    def parse_negatives(self):
        if not self.nfilename:
            logger.error('No se ha especificado un archivo '\
                    'de trazas negativas!')
            raise Exception('No se ha especificado un archivo '\
                    'de trazas negativas!')
        if self.verbose:
            print 'Starting parse of negative traces\n'
            start_time = time.time()
        if self.nfilename.endswith('.xes'):
            parser = NegativeParser(self.nfilename,
                    required_dimension=self.dim,
                    event_dictionary=self.event_dictionary)
        elif self.filename.endswith('.txt'):
           raise Exception('Not implemented yet!')
        else:
            logger.error("Error in file %s extension. Only '.xes'"\
                    " is allowed!",(self.nfilename or ''))
            raise Exception("Error in file %s extension. Only '.xes'"\
                    " is allowed!"%(self.nfilename or ''))
        parser.parikhs_vector()
        self.npv_traces = parser.pv_traces
        self.npv_set = parser.pv_set
        self.npv_array = parser.pv_array
        if self.verbose:
            print 'Parse of negative traces done\n'
            elapsed_time = time.time() - start_time
            print '# RESULTADO  obtenido en: ', elapsed_time
            print '#'*40+'\n'

    @stopwatch
    def parse_traces(self):
        if self.verbose:
            print 'Starting parse\n'
            start_time = time.time()
        if self.filename.endswith('.xes'):
            parser = XesParser(self.filename)
        elif self.filename.endswith('.txt'):
            parser = AdHocParser(self.filename)
        else:
            logger.error("Error in file %s extension. Only '.xes' and '.txt'"\
                    " are allowed!",(self.filename or ''))
            raise Exception("Error in file %s extension. Only '.xes' and '.txt'"\
                    " are allowed!"%(self.filename or ''))
        parser.parikhs_vector()
        self.event_dictionary = parser.event_dictionary
        self.reversed_dictionary = rotate_dict(parser.event_dictionary)
        self.pv_traces = parser.pv_traces
        self.pv_set = parser.pv_set
        self.pv_array = parser.pv_array
        self.dim = parser.dim
        if self.verbose:
            print 'Parse done\n'
            elapsed_time = time.time() - start_time
            print '# RESULTADO  obtenido en: ', elapsed_time
            print '#'*40+'\n'

    def parse(self):
        self.parse_traces()
        if self.nfilename:
            self.parse_negatives()

    def get_sample(self):
        points = set()
        for p_vect in sample(self.pv_set,
                self.samp_size or len(self.pv_set)):
            points.add(tuple(p_vect))
        return points

    def project(self, points, eigen, cluster):
        """
            Project the points into the cluster
            given by the value of the points
            in the eigen vector
            returns the projection and the list of projected points indexes
        """
        proj_nbr = len(self.projections) + 1
        ret = set()
        # Por cada variable en el cluster
        # busco el valor correspondiente en los puntos iniciales
        # Los voy recorriendo en "orden de correlación"
        # El cluster viene dado por valores absolutos
        # pero por las dudas...
        cluster = list(set([abs(x) for x in cluster]))
        cluster.sort(reverse=True)
        proj_idx = []
        for proj in cluster:
            # Cuando conectamos dos proyecciones pasamos ambos valores concatenados
            proj_idx += [idx%self.dim for idx,val in enumerate(eigen) if abs(val) == proj\
                    and idx%self.dim not in proj_idx]

        for point in points:
            proj_point = list(np.array(point)[proj_idx])
            ret.add(tuple(proj_point))

        self.projections[proj_nbr] = proj_idx
        return (list(ret),proj_idx)

    @property
    def qhull(self):
        if not self._qhull:
            self._qhull = self.get_qhull(self.pv_array)
            self._qhull.prepare_negatives()
        return self._qhull

    @qhull.setter
    def qhull(self, qhull):
        self._qhull = qhull
        return self._qhull

    @property
    def facets(self):
        return self.qhull.facets

    @stopwatch
    @sampling
    @projection
    def get_qhull(self, points):
        points = set(map(tuple, points))
        qhull = Qhull(points, neg_points=list(self.npv_set))
        qhull.compute_hiperspaces()
        self.output['times'].update(qhull.output.get('times',{}))
        return qhull

    @stopwatch
    def no_smt_simplify(self):
        if self.nfilename and not self.smt_matrix and not self.smt_iter:
            logger.debug('Starting to simplify model from negative points')
            if self.verbose:
                print 'Starting to simplify model from negative points\n'
                start_time = time.time()
            old_len = len(self.facets)
            self.qhull.no_smt_simplify(max_coef=self.max_coef)
            removed = old_len - len(self.facets)
            if removed:
                logger.debug('We removed %d facets without allowing negative points',removed)
            else:
                logger.debug("Couldn't simplify model without adding negative points")
            if self.verbose:
                elapsed_time = time.time() - start_time
                print 'Ended simplify from negative points\n'
                print '# RESULTADO  obtenido en: ', elapsed_time
                if removed:
                    print 'We removed %d facets without allowing negative points' % removed
                else:
                    print "Couldn't simplify model without adding negative points"
                print '#'*40+'\n'

    def model(self, points=None):
        if self.verbose:
            print 'Starting modeling\n'
            start_time = time.time()
        # The actual work is done when accesing self.facets
        facets = self.facets
        if self.verbose:
            print "Ended with MCH with ",len(facets)," halfspaces"
            print 'This are them:\n'
            for facet in facets:print facet
        logger.info("Ended with MCH with %s halfspaces",len(facets))
        if self.verbose:
            elapsed_time = time.time() - start_time
            print 'Modeling done\n'
            print '# RESULTADO  obtenido en: ', elapsed_time
            print '#'*40+'\n'

    def smt_simplify(self):
        if self.smt_matrix:
            self.qhull.smt_hull_simplify(timeout=self.smt_timeout)
        elif self.smt_iter:
            self.qhull.smt_facet_simplify(timeout=self.smt_timeout)
        self.output['times'].update(self.qhull.output.get('times',{}))

    @property
    def complexity(self):
        return self.qhull.complexity()

    def pach(self):
        logger.debug('Starting parsing')
        self.parse()
        logger.debug('Starting modeling')
        self.model()
        # Remove unnecesary facets wrt neg traces (if any)
        self.no_smt_simplify()
        # Remove unnecesary facets wrt neg traces
        # Apply smt_simplify.
        # Options are on the hull level, on every facet or none
        self.smt_simplify()
        complexity = self.complexity
        self.output['complexity'] = complexity
        self.generate_output_file()
        return complexity

    def get_def_pnml_name(self, extension='pnml'):
        # Tomo el archivo de entrada y le quito la extensión '.xes' si la tiene
        pp_file = os.path.basename(self.filename)
        def_name = (pp_file.endswith('.xes') and pp_file[:-4])\
                or pp_file or ''
        # Genero un nombre por default
        opts = ''
        if self.samp_num > 1:
            opts += '_s%d'%(self.samp_num)
            if self.samp_size:
                opts += '_%d'%(self.samp_size)
        if self.proj_size is not None:
            opts += '_p%d'%(self.proj_size)
        def_name = '%s.%s'%(def_name+opts,extension)
        return def_name

    @stopwatch
    def generate_pnml(self, filename=None):
        if not filename:
            filename = self.get_def_pnml_name()
        net_name = os.path.basename(filename)
        net_id = net_name.replace(' ','_').lower()

        net = PetriNet(net_id=net_id,name=net_name,filename=filename)
        # Comenzamos con los Places (i.e. un place por cada inecuación)
        nbr_places = 0
        places_list = []
        for idx, place in enumerate(self.facets,1):
            nbr_places += 1
            place_id = "place-%04d"%idx
            place_label = "%s"%place
            marking = abs(place.offset)
            Place(net, place_id, label=place_label, marking=marking)

        # Seguimos con las Transitions (i.e. una transition por cada variable)
        # Se crearán tantas transiciones como dimensiones del espacio
        nbr_transitions = 0
        for idx in xrange(self.dim):
            if idx in self.reversed_dictionary:
                transition_id = self.reversed_dictionary.get(idx).replace(' ','_')
                transition_label = self.reversed_dictionary.get(idx)
            else:
                transition_id = 'trans-%04d'%(idx+1)
                transition_label = 'Transition %04d'%(idx+1)
            Transition(net, transition_id, label=transition_label)

        # Los arcos se arman relacionando los places con las transitions
        # Para cada inecuación, se crean un arco hacia la transition
        # (i.e. variable) con peso igual al coef que la acompaña
        # Salvo que sea 0, claro.

        # Para las transiciones que no tienen
        # al menos un elemento en el preset y uno en el postset
        # (i.e un arco que venga de una place y otra que salga hacia otro place)
        # le creamos un place ficticio para ponerlo en su pre y/o post
        needs_preset = set(range(self.dim))
        needs_postset = set(range(self.dim))

        arcs_list = []
        seen_arcs = []
        for pl_id,place in enumerate(self.facets,1):
            # Contamos desde uno
            place_id = 'place-%04d'%(pl_id)
            for tr_id, value in enumerate(place.normal):
                # Si es cero no crear el arco
                if not value:
                    continue

                if tr_id in self.reversed_dictionary:
                    transition_id = self.reversed_dictionary.get(tr_id).replace(' ','_')
                else:
                    transition_id = 'trans-%04d'%(tr_id+1)
                if value > 0:
                    if tr_id in needs_preset:
                        # Puede que ya le hayamos creado un arco
                        # entrante
                        needs_preset.remove(tr_id)
                    arc_id = 'arc-P%04d-T%s'%(pl_id,transition_id)
                    # El arco sale de un place y va hacia una transition
                    from_id = place_id
                    to_id = transition_id
                else:
                    if tr_id in needs_postset:
                        # Puede que ya le hayamos creado un arco
                        # saliente
                        needs_postset.remove(tr_id)
                    arc_id = 'arc-T%s-P%04d'%(transition_id,pl_id)
                    from_id = transition_id
                    to_id = place_id
                    value = abs(value)
                # No debería pasar, pero por las dudas,
                # evitemos crear arcos repetidos
                if (from_id, to_id) in seen_arcs:
                    print 'El arco está repetido!: ', from_id, to_id
                    continue
                else:
                    seen_arcs.append((from_id, to_id))
                Arc(net, arc_id, from_id, to_id, value=value)

        # Generamos los places y arcos para los bucles de las transitions
        # desconectadas
        loops_list = []
        for idx,tr_id in enumerate(needs_preset | needs_postset):
            pl_id = nbr_places + idx + 1
            place_id = "place-%04d"%(pl_id)
            place_label = 'Dummy place %04d'%(idx+1)

            if tr_id in needs_preset:
                marking = 1
            elif tr_id in needs_postset:
                marking = 0
            else:
                raise Exception('No necesita pre ni post!')

            Place(net, place_id, place_label, marking)
            if tr_id in self.reversed_dictionary:
                transition_id = self.reversed_dictionary.get(tr_id).replace(' ','_')
            else:
                transition_id = 'trans-%04d'%(tr_id)
            if tr_id in needs_preset:
                # Si necesita preset, nos indica que la transición se puede
                # disparar siempre, por lo que generamos un loop
                # con el dummy-place
                arc_id = 'arc-P%04d-T%s'%(pl_id,transition_id)
                Arc(net, arc_id, transition_id,place_id, 1)
                Arc(net, arc_id, place_id, transition_id, 1)
            elif tr_id in needs_postset:
                # Lo agregamos al postset de la transición como una
                # especie de "/dev/null" donde tirar los markings generados
                arc_id = 'arc-T%s-P%04d'%(tr_id,pl_id)
                Arc(net, arc_id, transition_id,place_id, 1)
        net.save()
        logger.info('Generated the PNML %s', filename)
        return True

    def generate_output_file(self):
        outfile = self.get_def_pnml_name(extension='out')
        times = self.output.get('times',{})
        overall = 0
        output = """
Statistic of {positive}: with negative traces from {negative}

    benchmark       ->  {benchmark}
    positive        ->  {positive}
    dimension       ->  {dimension}
    traces          ->  {traces}
    events          ->  {events}
    negative        ->  {negative}
    complexity      ->  {complexity}
    exec_time       ->  {time}
    overall_time    ->  {overall_time}
    details
        parse_traces    ->  {parse_traces}"""
        if self.nfilename:
            output +="""\n        parse_negatives ->  {parse_negatives}"""
            overall += times.get('parse_negatives')
        if self.samp_num > 1:
            output +="""\n        do_sampling     ->  {do_sampling}"""
            overall += times.get('do_sampling')
        if self.proj_size is not None:
            output +="""\n        do_projection   ->  {do_projection}"""
            overall += times.get('do_projection')
        output +="""\n        convexHull      ->  {compute_hiperspaces}"""

        if self.smt_matrix:
            benchmark = 'Matrix SMT Simplification'
            outfile = 'MatrixSMT_' + outfile
            output +="""\n        shift&rotate    ->  {smt_hull_simplify}"""
            overall += times.get('smt_hull_simplify')
        elif self.smt_iter:
            benchmark = 'Iterative SMT Simplification'
            outfile = 'IterativeSMT_' + outfile
            output +="""\n        shift&rotate    ->  {smt_facet_simplify}"""
            overall += times.get('smt_facet_simplify')
        else:
            benchmark = 'No SMT Simplification'
            outfile = 'NoSMT_' + outfile
            output +="""\n        simplify        ->  {no_smt_simplify}"""
            overall += times.get('no_smt_simplify')

        for k in ('parse_traces', 'compute_hiperspaces'):
            overall += times.get(k,0)

        self.output['dimension'] = self.dim
        self.output['traces'] = len(self.pv_traces)
        self.output['events'] = sum(sum(trace[-1]) for idc,trace in self.pv_traces.items())
        self.output['complexity'] = self.complexity
        self.output['benchmark'] = benchmark
        self.output['overall_time'] = overall
        def flatten(dictionary):
            ret = {}
            for k,v in dictionary.items():
                if isinstance(v,dict):
                    ret.update(flatten(v))
                else:
                    ret[k] = v
            return ret
        out_dict = flatten(self.output)
        with open(outfile,'w') as ffile:
            ffile.write(output.format(**out_dict))

if __name__ == '__main__':
    import sys, traceback, pdb
    from mains import pach_main
    try:
        pach_main()
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        #pdb.post_mortem(tb)

