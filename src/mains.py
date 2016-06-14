#!/usr/bin/env python
# -*- coding: UTF-8
from utils import check_argv, get_positions
import pdb
import sys
from os.path import isfile
from pach import PacH
from qhull import Qhull
from parser import XesParser
from text_parser import AdHocParser
from comparator_xes import ComparatorXes
from comparator_pnml import ComparatorPnml
from negative_parser import NegativeParser
from pnml import PnmlParser
from config import CONFIGS
from config import logger

config_options = '\n'.join(['\t%s :\t\t %s'%(k,v) for k,v in CONFIGS.items()])

def pach_main():
    usage = 'Usage: ./pach.py <LOG filename> [--debug][--verbose]'\
        '\n\t[--negative <Negative points filename>] [max_coeficient]]'\
        '\n\t[--sampling [<number of samplings>] [<sampling size>]]'\
        '\n\t[--projection [<max group size>] [<connected model>]]'\
        '\n\t[--smt-matrix [<timeout>]]'\
        '\n\t[--smt-iter [<timeout>]]'\
        '\n\t[--sanity-check]'\
        '\nIf using config file, this are the options: \n%s'%config_options
    if not check_argv(sys.argv, minimum=1, maximum=17):
        print usage
        ret = -1
    else:
        ret = 0
        args = {}
        try:
            filename = sys.argv[1]
            if not (filename.endswith('.xes') or filename.endswith('.txt')):
                print filename, ' does not end in .xes not .txt. It should...'
                raise Exception('Filename does not end in .xes')
            if not isfile(filename):
                raise Exception("No such file")
            if '--sampling' in sys.argv or '-s' in sys.argv:
                samp_idx = '-s' in sys.argv and sys.argv.index('-s') or\
                    sys.argv.index('--sampling')
                try:
                    args['samp_num'] = int(sys.argv[samp_idx+1])
                except:
                    pass
                try:
                    args['samp_size'] = int(sys.argv[samp_idx+2])
                except:
                    pass
            if '--projection' in sys.argv or '-p' in sys.argv:
                # None indicates not to do projection.
                # False indicates no limit
                args['proj_size'] = False
                proj_idx = '-p' in sys.argv and sys.argv.index('-p') or\
                    sys.argv.index('--projection')
                try:
                    args['proj_size'] = int(sys.argv[proj_idx+1])
                except:
                    pass
                try:
                    args['proj_connected'] = int(sys.argv[proj_idx+2])
                except:
                    pass
            if '--negative' in sys.argv or '-n' in sys.argv:
                nidx = '-n' in sys.argv and sys.argv.index('-n') or\
                    sys.argv.index('--negative')
                nfilename = sys.argv[nidx+1]
                if not (nfilename.endswith('.xes') or nfilename.endswith('.txt')):
                    print nfilename, ' does not end in .xes not .txt. It should...'
                    raise Exception('Filename does not end in .xes')
                if not isfile(nfilename):
                    raise Exception("No such file")
                args['nfilename'] = nfilename
                try:
                    args['max_coef'] = int(sys.argv[nidx+2])
                except:
                    pass
            if '--smt-matrix' in sys.argv or '-smt-m' in sys.argv:
                smt_idx = '-smt-m' in sys.argv and sys.argv.index('-smt-m') or\
                    sys.argv.index('--smt-matrix')
                args['smt_matrix'] = True
                try:
                    args['smt_timeout'] = int(sys.argv[smt_idx+1])
                except:
                    pass
            elif '--smt-iter' in sys.argv or '-smt-i' in sys.argv:
                smt_idx = '-smt-i' in sys.argv and sys.argv.index('-smt-i') or\
                    sys.argv.index('--smt-iter')
                args['smt_iter'] = True
                try:
                    args['smt_timeout'] = int(sys.argv[smt_idx+1])
                except:
                    pass
            if '--sanity-check' in sys.argv:
                args['sanity_check'] = True
            if '--verbose' in sys.argv:
                args['verbose'] = True
            if '--debug' in sys.argv:
                pdb.set_trace()
            pach = PacH(filename, **args)
            complexity = pach.pach()
            filename = None
            if '--output' in sys.argv or '-o' in sys.argv:
                file_idx = '-o' in sys.argv and sys.argv.index('-o') or\
                    sys.argv.index('--output')
                try:
                    filename = sys.argv[file_idx+1]
                except:
                    pass
            pach.generate_pnml(filename=filename)
        except Exception, err:
            ret = 1
            if hasattr(err, 'message'):
                print 'Error: ', err.message
            else:
                print 'Error: ', err
            logger.error('Error: %s' % err, exc_info=True)
            raise err
        return ret

def parser_main():
    usage = """
        Usage: ./parser.py <LOG filename> [--verbose][--debug]
    """
    if not check_argv(sys.argv, minimum=1, maximum=4):
        print usage
        ret = -1
    else:
        ret = 0
        try:
            if '--debug' in sys.argv:
                pdb.set_trace()
            filename = sys.argv[1]
            if not (filename.endswith('.xes') or filename.endswith('.txt')):
                print filename, ' does not end in .xes nor .txt. It should...'
                raise Exception('Filename has wrong extension')
            if not isfile(filename):
                raise Exception("No such file")
            if filename.endswith('.xes'):
                obj = XesParser(filename)
            elif filename.endswith('.txt'):
                obj = AdHocParser(filename)
            obj.parse()
            if '--verbose' in sys.argv:
                print 'Parse done. Calcuting Parikhs vector'
            obj.parikhs_vector()
            print 'Se encontraron {0} puntos en un espacio de dimensión {1}'.format(
                    len(obj.pv_set), obj.dim)
            if '--verbose' in sys.argv:
                print "#"*15
        except Exception, err:
            ret = 1
            if hasattr(err, 'message'):
                print 'Error: ', err.message
            else:
                print 'Error: ', err
            logger.error('Error: %s' % err, exc_info=True)
            raise err
        return ret

def qhull_main():
    usage = 'Usage: ./qhull.py <points> [--debug][--verbose]'
    if not check_argv(sys.argv, minimum=1, maximum=5):
        print usage
        ret =  -1
    else:
        ret = 0
        try:
            import ast
            try:
                if isfile(sys.argv[1]):
                    print sys.argv[1], 'assumed to be a file'
                    with open(sys.argv[1], 'r') as ffile:
                            points = ffile.readline()
                else:
                    points = sys.argv[1]
                points = ast.literal_eval(points)
                if '--verbose' in sys.argv:
                    print "Se colectaron ", len(points), " puntos"
                points = set(map(lambda x: tuple(x),points))
                if '--verbose' in sys.argv:
                    print "Se colectaron ", len(points), " puntos DIFERENTES"
            except:
                ret = -1
                print "We are sorry. We weren't able to read the points"
            else:
                if '--debug' in sys.argv:
                    pdb.set_trace()
                qhull = Qhull(points)
                point_qty = qhull.compute()
                print "Computed MCH with ", point_qty," points"
                if '--verbose' in sys.argv:
                    print 'This are the points:'
                    print(qhull.vertices)
        except Exception, err:
            ret = 1
            if hasattr(err, 'message'):
                print 'Error: ', err.message
            else:
                print 'Error: ', err
            logger.error('Error: %s' % err, exc_info=True)
            raise err
    return ret

def negative_parser_main():
    usage = """
        Usage: ./negative_parser.py <negative XES LOG filename> [--verbose][--debug]
    """
    if not check_argv(sys.argv, minimum=1, maximum=4):
        print usage
        ret = -1
    else:
        ret = 0
        try:
            filename = sys.argv[1]
            if not filename.endswith('.xes'):
                print filename, ' does not end in .xes. It should...'
                raise Exception('Filename has wrong extension')
            if not isfile(filename):
                raise Exception("No such file")
            if '--debug' in sys.argv:
                pdb.set_trace()
            obj = NegativeParser(filename)
            obj.parse()
            if '--verbose' in sys.argv:
                print 'Parse done. Calcuting Parikhs vector'
            obj.parikhs_vector()
            print 'Se encontraron {0} puntos en un espacio de dimensión {1}'.format(
                    len(obj.pv_set), obj.dim)
            if '--verbose' in sys.argv:
                print "#"*15
        except Exception, err:
            ret = 1
            if hasattr(err, 'message'):
                print 'Error: ', err.message
            else:
                print 'Error: ', err
            logger.error('Error: %s' % err, exc_info=True)
            raise err
        return ret

def xes_comparator_main():
    usage = 'Usage: ./comparator.py <LOG filename> [--debug]'\
        '\n\t[--negative <Negative XES points filename>] [max_coeficient]]'\
        '\n\t[--sampling [<number of samplings>] [<sampling size>]]'\
        '\n\t[--projection [<max group size>] [<connected model>]]'\
        '\n\t[--smt-matrix [<timeout>]]'\
        '\n\t[--smt-iter [<timeout>]]'\
        '\nIf using config file, this are the options: \n%s'%config_options
    if not check_argv(sys.argv, minimum=1, maximum=16):
        print usage
        ret = -1
    else:
        ret = 0
        args = {}
        try:
            filename = sys.argv[1]
            if not (filename.endswith('.xes') or filename.endswith('.txt')):
                print filename, ' does not end in .xes not .txt. It should...'
                raise Exception('Filename does not end in .xes')
            if not isfile(filename):
                raise Exception("No such file")
            if '--sampling' in sys.argv or '-s' in sys.argv:
                samp_idx = '-s' in sys.argv and sys.argv.index('-s') or\
                    sys.argv.index('--sampling')
                try:
                    args['samp_num'] = int(sys.argv[samp_idx+1])
                except:
                    pass
                try:
                    args['samp_size'] = int(sys.argv[samp_idx+2])
                except:
                    pass
            if '--projection' in sys.argv or '-p' in sys.argv:
                # None indicates not to do projection.
                # False indicates no limit
                args['proj_size'] = False
                proj_idx = '-p' in sys.argv and sys.argv.index('-p') or\
                    sys.argv.index('--projection')
                try:
                    args['proj_size'] = int(sys.argv[proj_idx+1])
                except:
                    pass
                try:
                    args['proj_connected'] = int(sys.argv[proj_idx+2])
                except:
                    pass
            if '--negative' in sys.argv or '-n' in sys.argv:
                nidx = '-n' in sys.argv and sys.argv.index('-n') or\
                    sys.argv.index('--negative')
                nfilename = sys.argv[nidx+1]
                if not (nfilename.endswith('.xes') or nfilename.endswith('.txt')):
                    print nfilename, ' does not end in .xes. It should...'
                    raise Exception('Filename does not end in .xes')
                if not isfile(nfilename):
                    raise Exception("No such file")
                args['nfilename'] = nfilename
                try:
                    args['max_coef'] = int(sys.argv[nidx+2])
                except:
                    pass
            if '--smt-matrix' in sys.argv or '-smt-m' in sys.argv:
                smt_idx = '-smt-m' in sys.argv and sys.argv.index('-smt-m') or\
                    sys.argv.index('--smt-matrix')
                try:
                    args['smt_timeout_matrix'] = int(sys.argv[smt_idx+1])
                except:
                    pass
            elif '--smt-iter' in sys.argv or '-smt-i' in sys.argv:
                smt_idx = '-smt-i' in sys.argv and sys.argv.index('-smt-i') or\
                    sys.argv.index('--smt-iter')
                args['smt_iter'] = True
                try:
                    args['smt_timeout_iter'] = int(sys.argv[smt_idx+1])
                except:
                    pass
            if '--debug' in sys.argv:
                pdb.set_trace()
            comparator = ComparatorXes(filename, **args)
            complexity = comparator.compare()
            comparator.generate_pnml()
            comparator.generate_outputs()
            if '--verbose' in sys.argv:
                print complexity
        except Exception, err:
            ret = 1
            if hasattr(err, 'message'):
                print 'Error: ', err.message
            else:
                print 'Error: ', err
            logger.error('Error: %s' % err, exc_info=True)
            raise err
        return ret

def pnml_comparator_main():
    usage = """
        Usage: ./comparator_pnml.py <PNML filename> [--debug]
        '\n\t[--negative <Negative XES points filename>] [max_coeficient]]'\
        '\n\t[--smt-matrix [<timeout>]]'\
        '\n\t[--smt-iter [<timeout>]]'\
        '\nIf using config file, this are the options: \n%s'%config_options
    """
    if not check_argv(sys.argv, minimum=1, maximum=10):
        print usage
        ret = -1
    else:
        ret = 0
        try:
            args = {}
            filename = sys.argv[1]
            if not (filename.endswith('.pnml')):
                print filename, ' does not end in .pnml. It should...'
                raise Exception('Filename has wrong extension')
            if not isfile(filename):
                raise Exception("No such file")
            if '--negative' in sys.argv or '-n' in sys.argv:
                nidx = '-n' in sys.argv and sys.argv.index('-n') or\
                    sys.argv.index('--negative')
                nfilename = sys.argv[nidx+1]
                if not (nfilename.endswith('.xes')):
                    print nfilename, ' does not end in .xes. It should...'
                    raise Exception('Filename does not end in .xes')
                if not isfile(nfilename):
                    raise Exception("No such file")
                args['nfilename'] = nfilename
                try:
                    args['max_coef'] = int(sys.argv[nidx+2])
                except:
                    pass
            if '--smt-matrix' in sys.argv or '-smt-m' in sys.argv:
                smt_idx = '-smt-m' in sys.argv and sys.argv.index('-smt-m') or\
                    sys.argv.index('--smt-matrix')
                try:
                    args['smt_timeout_matrix'] = int(sys.argv[smt_idx+1])
                except:
                    pass
            elif '--smt-iter' in sys.argv or '-smt-i' in sys.argv:
                smt_idx = '-smt-i' in sys.argv and sys.argv.index('-smt-i') or\
                    sys.argv.index('--smt-iter')
                args['smt_iter'] = True
                try:
                    args['smt_timeout_iter'] = int(sys.argv[smt_idx+1])
                except:
                    pass
            if '--debug' in sys.argv:
                pdb.set_trace()
            if '--check' in sys.argv or '-c' in sys.argv:
                lidx = '-c' in sys.argv and sys.argv.index('-c') or\
                    sys.argv.index('--check')
                log_file = sys.argv[lidx+1]
                if not (log_file.endswith('.xes')):
                    print log_file, ' does not end in .xes. It should...'
                    raise Exception('Filename does not end in .xes')
                if not isfile(log_file):
                    raise Exception("No such file")
                args['positive_log'] = log_file
            comparator = ComparatorPnml(filename, **args)
            complexity = comparator.compare()
            comparator.generate_pnml()
            comparator.generate_outputs()
            comparator.check_hull()
            if '--verbose' in sys.argv:
                print complexity
        except Exception, err:
            ret = 1
            if hasattr(err, 'message'):
                print 'Error: ', err.message
            else:
                print 'Error: ', err
            logger.error('Error: %s' % err, exc_info=True)
            raise err
        return ret

def pnml_main():
    usage = """
        Usage: ./pnml.py <PNML filename> [--verbose][--debug][--check <XES Log filename>]
    """
    if not check_argv(sys.argv, minimum=1, maximum=5):
        print usage
        ret = -1
    else:
        ret = 0
        try:
            filename = sys.argv[1]
            if not (filename.endswith('.pnml')):
                print filename, ' does not end in .pnml. It should...'
                raise Exception('Filename has wrong extension')
            if not isfile(filename):
                raise Exception("No such file")
            if '--debug' in sys.argv:
                pdb.set_trace()
            obj = PnmlParser(filename)
            obj.parse()
            if '--verbose' in sys.argv:
                print 'Parse done.'
                print obj.petrinet
            qhull = obj.petrinet.get_qhull()
            if '--check' in sys.argv or '-c' in sys.argv:
                lidx = '-c' in sys.argv and sys.argv.index('-c') or\
                    sys.argv.index('--check')
                log_file = sys.argv[lidx+1]
                if not (log_file.endswith('.xes')):
                    print log_file, ' does not end in .xes. It should...'
                    raise Exception('Filename does not end in .xes')
                if not isfile(log_file):
                    raise Exception("No such file")
                qhull.all_in_file(log_file, event_dictionary=obj.event_dictionary)
            if '--verbose' in sys.argv:
                print 'Got qhull representation whith %s facets.'%(len(qhull.facets))
                print 'This are them:\n'
                for facet in qhull.facets:print facet
        except Exception, err:
            ret = 1
            if hasattr(err, 'message'):
                print 'Error: ', err.message
            else:
                print 'Error: ', err
            logger.error('Error: %s' % err, exc_info=True)
            raise err
        return ret
