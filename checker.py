#!/usr/bin/env python
# -*- coding: UTF-8
import sys
sys.path.insert(0, './src')
import copy

from pach import PacH
from pnml import PnmlParser
from comparator import Comparator
from utils import rotate_dict
from config import logger


class Checker(object):

    def __init__(self, pnml_file, xes_log=None):
        self.pnml_file = pnml_file
        parser = PnmlParser(pnml_file)
        parser.parse()
        self.net = parser.petrinet
        self.dim = parser.dim
        self.event_dictionary = parser.event_dictionary
        self.xes_log = xes_log
        self.qhull = self.net.get_qhull()

    def check_hull(self):
        if self.xes_log:
            self.qhull.all_in_file(self.xes_log, event_dictionary=self.event_dictionary)
            # If an error ocurred in the previous call it raise an error
            print "Everything seems fitting for %s"%(self.pnml_file)

if __name__ == '__main__':
    import sys, traceback, pdb
    try:
        pnml_file = sys.argv[1]
        xes_file = sys.argv[2]
        checker = Checker(pnml_file, xes_file)
        checker.check_hull()
    except:
        type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)
