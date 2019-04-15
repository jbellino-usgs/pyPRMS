
from __future__ import (absolute_import, division, print_function)


class ParameterError(Exception):
    def __init__(self, err_args):
        Exception.__init__(self, err_args)
        self.errArgs = err_args
