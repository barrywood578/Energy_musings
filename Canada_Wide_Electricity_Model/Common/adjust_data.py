#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Support standard methods of adjusting floating point values in a list

    Currently, this supports both an absolute adjustment of value,
    as well as scaling values with a "ratio".

    The default adjustment value results in no change to the data.
"""

class AdjustData(object):
    def __init__(self, abs_adj=0.0, ratio=1.0):
        self.abs_adj = float(abs_adj)
        self.ratio = float(ratio)

    def adjust(self, data_set):
        updata = []
        for data in data_set:
            updata.append((data * self.ratio) + self.abs_adj)
        return updata
