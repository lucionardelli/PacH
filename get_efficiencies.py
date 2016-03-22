
from os.path import isfile
import os, shutil, sys, traceback
import copy
import re

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + '/src')
from pach import PacH
import qhull, pnml
from utils import check_argv, parse_config, parse_config_output

import fnmatch
import os

matches = []
for root, dirnames, filenames in os.walk('../Experiments/models'):
    for filename in fnmatch.filter(filenames, '*.out'):
        matches.append(os.path.join(root, filename))

for filename in matches:
	with open(filename, 'r') as f:
		text = f.read()
		m = re.search("effectiveness\s*->\s*(\d+\.\d+)", text)
		print filename, m.group(1)

	
