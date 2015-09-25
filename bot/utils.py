__author__ = 'Matthew Tuusberg'

import sys

PYTHON3 = sys.version_info[0] > 2


# decode a string. if str is a python 3 string, do nothing.
def decode(str_, codec='utf8'):
    if PYTHON3:
        return str_
    else:
        return str_.decode(codec)


# encode a string. if str is a python 3 string, do nothing.
def encode(str_, codec='utf8'):
    if PYTHON3:
        return str_
    else:
        return str_.encode(codec)
