#!/usr/bin/env python
# -*- coding: UTF-8
import logging

# Float numbers will consider this many decimal part
TRUNCATE=3
# Upper limit for LCM
LCM_LIMIT=5000
# Tolerance for equality comparision
TOLERANCE =0.0001

#General Logging config

LOG_CONFIG = {
    'level': logging.INFO,
    'filename': '/var/log/pach/pach.log',
    'filemode': 'a',
    'format': '%(asctime)s %(levelname)-8s %(message)s',
    'datefmt': '%d-%b-%y %H:%M:%S',
}

logging.basicConfig(**LOG_CONFIG)
logger = logging.getLogger('PacHlogger')

# Since K-Means is randomized-seeded we make some retries on errors
KMEANS = 5

# Configuration file valid options
CONFIGS = {
    'filename': 'Location of .xes file with traces or .pnml file with Petri net model',
    'positive_log': 'When parsing from PNML, a xes file can of positive log can be used for sanity check the parsed model',
    'nfilename': 'Negative traces file location',
    'samp_num': 'Number of samples to take (Default no sample, use all elements)',
    'samp_size': 'Number of elementes to take on each sample (No default)',
    'proj_size': 'Number for maximum dimension to project to (Default no projection, 0 for no limit)',
    'proj_connected': 'Boolean indicating whether to (try to) connect clusters (default: True)',
    'max_coef': "Maximum allowed in halfspaces. If no coefficient is bigger than this, won't try to simplify",
    'smt_timeout_iter': 'Timeout for smt solution finding when simplifying one halfpsace at the time',
    'smt_timeout_matrix': 'Timeout for smt solution finding when simplifying all hull at once',
    'sanity_check': 'Performs sanity check that all traces are inside hull',
}
