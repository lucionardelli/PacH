#!/usr/bin/env python
# -*- coding: UTF-8
import logging

# Float numbers will consider this many decimal part
TRUNCATE=4
# Upper limit for LCM
LCM_LIMIT=5000
# Tolerance for equality comparision
TOLERANCE =0.0001

#General Logging config

LOG_CONFIG = {
    'level': logging.INFO,
    'filename': '/var/log/pach.log',
    'filemode': 'a',
    'format': '%(asctime)s %(levelname)-8s %(message)s',
    'datefmt': '%a, %d %b %Y %H:%M:%S',
}

logging.basicConfig(**LOG_CONFIG)
logger = logging.getLogger('PacHlogger')

# Since K-Means is randomized-seeded we make some retries on errors
KMEANS = 5
