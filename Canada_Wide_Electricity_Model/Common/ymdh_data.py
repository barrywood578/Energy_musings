#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Support for data indexed by year, month, day and hour.
    Each indexed entry consists of:
    - value
    - array of other information

"""

from optparse import OptionParser
from collections import OrderedDict
import operator
import sys
import os
import logging
import copy
from datetime import datetime, timedelta
from math import ceil, isnan
from common_defs import *

class VA(object):
    def __init__(self, val, data_iter=[]):
        self.val = val
        if isnan(val):
            self.data_array = INVALID_LIST
            return
        t_data_array = []
        for item in data_iter:
            t_data_array.append(item)
        self.data_array = [t_data_array]

    def __add__(self, other):
        if isnan(self.val) or isnan(other.val):
            raise ValueError("Adding NaN!")
        val = self.val + other.val
        ret = VA(val)
        ret.data_array = []
        for x in self.data_array:
            ret.data_array.append(x)
        for x in other.data_array:
            ret.data_array.append(x)
        return ret

    def __str__(self):
        items = [str(self.val)]
        for x in self.data_array:
            for y in x:
                items.append(str(y))
            items.append("\n")
        return "%s%s%s" % (START_END, SEPARATOR.join(items), START_END)

class YMDHData(object):
    def __init__(self, ):
        self.dbase = {}

    def _get_keys_from_time(self, UTC):
        y = str(UTC.year)
        m = str(UTC.month)
        d = str(UTC.day)
        h = str(UTC.hour)
        return y, m, d, h

    def add_ymdh(self, UTC, val, data, ignore_dup=False):
        va = VA(val, data)
        Y, M, D, H = self._get_keys_from_time(UTC)

        if not Y in self.dbase:
            self.dbase[Y] = {}

        if not M in self.dbase[Y]:
            self.dbase[Y][M] = {}

        if not D in self.dbase[Y][M]:
            self.dbase[Y][M][D] = {}

        if H in self.dbase[Y][M][D]:
            if ignore_dup:
                self.dbase[Y][M][D][H] += va
            else:
                raise ValueError("Duplicate line at time %s %s %s %s:00!"
                                 "Original data %s" %
                                 (Y, M, D, H, str(self.dbase[Y][M][D][H])))
            return
        self.dbase[Y][M][D][H] = va

    def get_value(self, UTC):
        Y, M, D, H = self._get_keys_from_time(UTC)
        try:
            return self.dbase[Y][M][D][H].val
        except:
            return 

    def get_data(self, UTC):
        Y, M, D, H = self._get_keys_from_time(UTC)
        try:
            return self.dbase[Y][M][D][H]
        except:
            return VA(INVALID_VALUE)

    def duplicate_data(self, UTC, new_UTC, interval, adjustment):
        hours = (interval.days * 24) + ceil(interval.seconds/3600.0)
        for h_offset in range(0, hours):
            src_UTC = UTC + timedelta(hours=h_offset)
            trg_UTC = new_UTC + timedelta(hours=h_offset)
            y, m, d, h = self._get_keys_from_time(src_UTC)
            vl = copy.copy(self.dbase[y][m][d][h])
            newval = adjustment.adjust([vl.val])[0]
            self.add_ymdh(trg_UTC, newval, [])
            Y, M, D, H = self._get_keys_from_time(trg_UTC)
            self.dbase[Y][M][D][H].data_array = vl.data_array

    def adjust_values(self, UTC, interval, adj):
        hours = (interval.days * 24) + ceil(interval.seconds/3600.0)
        for _ in range(0, hours):
            y, m, d, h = self._get_keys_from_time(UTC)
            newval = adj.adjust([self.dbase[y][m][d][h].val])[0]
            self.dbase[y][m][d][h].val = newval
            src_UTC = src_UTC + timedelta(hours=1)
