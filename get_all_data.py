
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

def g(reg, text):
	m = re.search(reg, text, re.M)
	return m.group(1) if m is not None else '###'

root_dir = '../Experiments'

out_matches = []
txt_matches = []
rng_matches = []
ali_matches = []
for root, dirnames, filenames in os.walk(root_dir):
    for filename in fnmatch.filter(filenames, '*.out'):
        out_matches.append(os.path.join(root, filename))
    for filename in fnmatch.filter(filenames, '*.txt'):
    	if not 'alignprec' in filename and not 'negrecprecgen' in filename:
	        txt_matches.append(os.path.join(root, filename))
    for filename in fnmatch.filter(filenames, '*.alignprec.txt'):
        ali_matches.append(os.path.join(root, filename))
    for filename in fnmatch.filter(filenames, '*.negrecprecgen.txt'):
        rng_matches.append(os.path.join(root, filename))

print 'out', 'filename', 'effectiveness', 'complexity', \
			'negative', 'overall_time', 'parse_traces', \
			'do_projection', 'convexHull', 'simplify'
for filename in out_matches:
	with open(filename, 'r') as f:
		text = f.read()
		effectiveness = g("^\s*effectiveness\s*->\s*?(.*?)$", text)
		complexity = g("^\s*complexity\s*->\s*?(.*?)$", text)
		negative = g("^\s*negative\s*->\s*?(.*?)$", text)
		overall_time = g("^\s*overall_time\s*->\s*?(.*?)$", text)
		parse_traces = g("^\s*parse_traces\s*->\s*?(.*?)$", text)
		do_projection = g("^\s*do_projection\s*->\s*?(.*?)$", text)
		convexHull = g("^\s*convexHull\s*->\s*?(.*?)$", text)
		simplify = g("^\s*simplify\s*->\s*?(.*?)$", text)
		print 'out', filename, effectiveness, complexity, \
			negative, overall_time, parse_traces, \
			do_projection, convexHull, simplify
			
print 'txt', 'filename', 'num', 'readlog_avg', 'mine_avg', 'save_avg'
for filename in txt_matches:
	with open(filename, 'r') as f:
		text = f.read()
		all_read = re.findall("read log and setup: (\d+)", text)
		all_mine = re.findall("mine: (\d+)", text)
		all_save = re.findall("save net: (\d+)", text)
		print 'txt', filename, len(all_read), \
			float(sum([int(x) for x in all_read])) / float(len(all_read)) / 1000.0, \
			float(sum([int(x) for x in all_mine])) / float(len(all_mine)) / 1000.0, \
			float(sum([int(x) for x in all_save])) / float(len(all_save)) / 1000.0

print 'ali', 'filename', 'log', 'alignprec'
for filename in ali_matches:
	with open(filename, 'r') as f:
		for line in f:
			split = line.split('\t')
			print 'ali', filename, split[0].strip(), split[1].strip()
			
print 'rng', 'filename', 'log', 'recall', 'precision', 'generalization'
for filename in rng_matches:
	with open(filename, 'r') as f:
		for line in f:
			split = line.split('\t')
			print 'ali', filename, split[0].strip(), split[1].strip(), split[2].strip(), split[3].strip()
			
	
