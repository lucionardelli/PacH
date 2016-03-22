
from os.path import isfile
import os, shutil, sys, traceback
import copy

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + '/src')
from pach import PacH
import qhull, pnml
from utils import check_argv, parse_config, parse_config_output

import fnmatch
import os

matches = []
for root, dirnames, filenames in os.walk('../Experiments'):
    for filename in fnmatch.filter(filenames, '*.pnml'):
        matches.append(os.path.join(root, filename))

for filename in matches:
	try:
		parser = pnml.PnmlParser(filename)
		parser.parse()
		parsed_petrinet = parser.petrinet
		event_dictionary = parser.event_dictionary
		qhull = copy.deepcopy(parsed_petrinet.get_qhull(neg_points=list([])))
		com = qhull.complexity()
		dim = qhull.dim
	except:
		continue
	print filename, com, dim

	
