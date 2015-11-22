#!/usr/bin/env python
# -*- coding: UTF-8
from os.path import isfile
import os, shutil

from comparator_pnml import ComparatorPnml
from config import logger
from utils import check_argv, parse_config, parse_config_output

def main(*args, **kwargs):
    usage = """
        Usage: ./pnml_comparator_script.py <.ini config filename>
    """
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
                raise Exception("El archivo especificado no existe")
            if '--debug' in sys.argv:
                pdb.set_trace()
            for filename, arguments in parse_config(config_file):
                comparator = ComparatorPnml(filename, **arguments)
                comparator.check_hull()
                complexity = comparator.compare()
                logger.info('%s complexity -> %s',filename,complexity)
                comparator.generate_pnml()
                comparator.generate_outputs()
                comparator.check_hull()
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
            raise err
        return ret


if __name__ == '__main__':
    import sys, traceback, pdb
    try:
        main()
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        #pdb.post_mortem(tb)

