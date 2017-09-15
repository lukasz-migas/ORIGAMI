# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017 Lukasz G. Migas <lukasz.migas@manchester.ac.uk>

#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
from __future__ import division, print_function
from __builtin__ import str
import os
import numpy as np


def str2num(string):
    try:
        val = float(string)
        return val
    except (ValueError, TypeError):
        return None
    
def num2str(val):
    try:
        string = str(val)
        return string
    except (ValueError, TypeError):
        return None

def str2int(string):
    try:
        val = int(string)
        return val
    except (ValueError, TypeError):
        return None

def float2int(num):
    try:
        val = int(num)
        return val
    except (ValueError, TypeError):
        return num
    
def isempty(input):
    try:
        if np.asarray(input).size == 0 or input is None:
            out = True
        else:
            out = False
    except (TypeError, ValueError, AttributeError):
        print('Could not determine whether object is empty. Output set to FALSE')
        out = False
    return out
    
def str2bool(s):
    if s == 'True':
         return True
    elif s == 'False':
         return False
    else:
         raise ValueError