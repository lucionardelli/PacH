#!/usr/bin/env python
# -*- coding: UTF-8
from os.path import isfile
import os, shutil

from comparator_xes import ComparatorXes
from config import logger
from utils import check_argv, parse_config, parse_config_output
from config import CONFIGS

config_options = '\n'.join(['\t%s :\t %s'%(k,v) for k,v in CONFIGS.items()])

def main(*args, **kwargs):
    usage = """
        Usage: ./xes_comparator_script.py <.ini config filename>

        Config file options:
     %s\n
NOTE: Do you have the needed environment variables?
    - XES : Path to .xes file with traces (for running PacH)
    - PNML : Path to .pnml file with Petri net model (for simplifying PROM models)
    - NXES : Path to .xes file with negative traces
    - PETRI : Path where simplified .pnml files should be moved to after script ends
    - STATS : Path where statistic files should be moved to after script ends
  IMPORTANT: NO PATH MUST END IN '/' (it is added automatically)
    """%(config_options)
    if not check_argv(sys.argv, minimum=1, maximum=4):
        print usage
        ret = -1
    else:
        ret = 0
        try:
            config_file = sys.argv[1]
            if not config_file.endswith('.ini'):
                print config_file, ' does not end in .ini. It should...'
                raise Exception('Filename has wrong extension')
            if not isfile(config_file):
                raise Exception("No such file")
            if '--debug' in sys.argv:
                pdb.set_trace()
            for filename, arguments in parse_config(config_file):
                comparator = ComparatorXes(filename, **arguments)
                complexity = comparator.compare()
                comparator.generate_pnml()
                comparator.generate_outputs()
                if '--verbose' in sys.argv:
                    print complexity
            pnml_folder,out_folder = parse_config_output(config_file)
            pwd = os.getcwd()
            for basename in os.listdir(pwd):
                if basename.endswith('.pnml'):
                    pnml_file = os.path.join(pwd, basename)
                    if os.path.isfile(pnml_file):
                        shutil.copy2(pnml_file, pnml_folder)
                        os.remove(pnml_file)
                elif basename.endswith('.out'):
                    out_file = os.path.join(pwd, basename)
                    if os.path.isfile(out_file):
                        shutil.copy2(out_file, out_folder)
                        os.remove(out_file)
        except Exception, err:
            ret = 1
            if hasattr(err, 'message'):
                print 'Error: ', err.message
            else:
                print 'Error: ', err
            raise
        return ret


if __name__ == '__main__':
    import sys, traceback, pdb
    import faulthandler
    faulthandler.enable()
    try:
        main()
    except Exception, err:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        print err
        #pdb.post_mortem(tb)

