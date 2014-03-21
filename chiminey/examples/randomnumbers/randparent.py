# Copyright (C) 2014, RMIT University

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.


import logging
from chiminey.corestages import Parent


logger = logging.getLogger(__name__)


class RandParent(Parent):
    '''
        Holds common methods that are needed by two or more stages
    '''
    def get_internal_sweep_map(self, settings, **kwargs):
        '''
            Defines multiple processes within a single job
            Number of processes generated is the cross-product of the values in the entire map
            The values in the process can be used in a template instantiation
            Returns a dict where its
                - key correspond to template variable name,
                - value is a list of possible values for that template variable
            e.g., if map = {"var": [7,9]}, this map result in 2 processes being generated,
                    - template variable "var" = 7 in process 1
                    - template variable "var" = 9 in process 2
            e.g., if map = {"var1": [7,9], "var2": [42]}, this map result in 2 processes being generated,
                    - template variable "var1"=7, "var2"=42  in process 1
                    - template variable "var2"=9, "var2"=42 in process 2
        '''
        rand_index = 42
        map = {'val': [1, 2]}
        return map, rand_index
