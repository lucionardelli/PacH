#!/usr/bin/env python
# -*- coding: UTF-8

from fractions import Fraction
from utils import almost_equal
from config import *
from math import floor

def rationalize(num, max_denom=100):
    num = format(num, '.%dg'%TRUNCATE)
    rational = Fraction(num).limit_denominator(max_denom)
    return rational.numerator, rational.denominator

def integer_coeff(float_list):
    minimum = None
    abs_float = []
    modif = []
    for fl in float_list:
        if almost_equal(fl, 0.0, tolerance=TOLERANCE):
            fl = 0.0
        if fl >= 0:
            modif.append(1)
        else:
            fl = abs(fl)
            modif.append(-1)
        abs_float.append(fl)
        if fl and (minimum is None or fl <= minimum):
            minimum = fl
    bigger_one = []
    for fl in float_list:
        fl = fl / minimum
        bigger_one.append(int(floor(fl)))
    return bigger_one
