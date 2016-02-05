#!/usr/bin/env python
# -*- coding: UTF-8
from custom_exceptions import IncorrectOutput,CannotProject
import numpy as np

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def rotate_dict(dictionary):
    ret = {}
    for k,v in dictionary.items():
        if v in ret:
            raise Exception("This dictonary cannot be rotated."
                    " Map should be 'biyective'")
        else:
            ret[v] = k
    return ret

def check_argv(argv, minimum=1, maximum=1):
    """
        Ensures that the there are at least minimum and at most maximum strings
        in argv
    """
    if maximum < minimum:
        t = minimum
        minimum = maximum
        maximum = t
    ret = minimum < len(argv) < maximum + 1
    return ret and all(map(lambda x: type(x) == type(''), argv))

def almost_equal(f1, f2, tolerance=0.00001):
    # De esta manera evitamos errores al comparar un número con zero
    f1 += 1
    f2 += 1
    return abs(f1 - f2) <= tolerance * max(abs(f1), abs(f2))

def get_positions(eigenvector, cluster):
    """
        Finds the positions of the elements
        of abs(<cluster>) in the abs(eigenvector)
    """
    # We ensure that first argument is a list-like
    evect = list(eigenvector)
    ret = []
    for val in cluster:
        if val in evect:
            ret.append(evect.index(val))
        elif -1*val in evect:
            ret.append(evect.index(-1*val))
    return ret

def my_round(point):
    """
        Custom "round". It doesn't actually round numbers.
        It truncate it if it is "almost" an integer
        If it's positive it returns the ceil and if its
        negative it returns the floor because this
        This behaviour always "adds" points to a model
    """
    ret =int(point)
    if not almost_equal(point,ret):
        ret = point > 0 and int(np.ceil(point)) or int(np.floor(point))
    return ret

def __gcd_two(num1,num2=0):
    while num2:
        num1, num2 = num2, num1%num2
    return num1 or 1

def gcd(*args):
    return reduce(__gcd_two, args)

def __lcm_two(num1,num2=1):
    return num1 * num2 / __gcd_two(num1,num2)

def lcm(*args):
    return reduce(__lcm_two, args)

from ConfigParser import SafeConfigParser
from os.path import isfile
import os
from config import CONFIGS

# Function to parse .ini config files and return values for scripting
def parse_config(options_file):
    parser = SafeConfigParser(os.environ)
    parser.read(options_file)

    # One section per file to compute
    for section in parser.sections():
        if section in ('OUTPUT_DIRS',):
            continue
        print 'Starting:', section
        # Filename is a special option
        filename = parser.get(section, 'filename')
        parser.remove_option(section, 'filename')
        if not isfile(filename):
            raise Exception("No such file")
        arguments = {}
        for arg in CONFIGS:
            if parser.has_option(section,arg):
                # Try to search for actual value, if fails, use as string
                try:
                    val = eval(parser.get(section, arg))
                except:
                    val = parser.get(section, arg)
                arguments[arg] = val
        yield (filename, arguments)

# Function to parse .ini config files and return values for scripting
def parse_config_output(options_file):
    parser = SafeConfigParser(os.environ)
    parser.read(options_file)

    # One section per file to compute
    pnml_dir = parser.get('OUTPUT_DIRS', 'pnml_output')
    out_dir = parser.get('OUTPUT_DIRS', 'statistics_output')
    return pnml_dir, out_dir
