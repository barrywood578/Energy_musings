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
from adjust_data import AdjustData

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
    def __init__(self):
        self.dbase = {}
        self.min_time = None
        self.max_time = None

    def _get_keys_from_time(self, UTC):
        y = str(UTC.year)
        m = str(UTC.month)
        d = str(UTC.day)
        h = str(UTC.hour)
        return y, m, d, h

    def _determine_nearest_time(self, UTC):
        if len(self.dbase.keys()) == 0:
            raise ValueError("Database is empty, no key available!")
        try:
            y, m, d, h = self._get_keys_from_time(UTC)
            val = self.dbase[y][m][d][h]
            return UTC
        except KeyError:
            # Don't count on having another leap year present.
            if m == "2" and d == "29":
                d = "28"
            # See if a different year has the same month/day/hour:
            for Y in sorted(self.dbase.keys()):
                try:
                    val = self.dbase[Y][m][d][h]
                    return datetime(int(Y), int(m), int(d), hour=int(h))
                except KeyError:
                    pass
        raise ValueError("No other year has same Month/Day/Hour!")

    def add_ymdh(self, UTC, val, data, ignore_dup=False):
        if self.min_time is None:
            self.min_time = UTC
            self.max_time = UTC
        elif UTC < self.min_time:
            self.min_time = UTC
        elif UTC > self.max_time:
            self.max_time = UTC

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
        data = self.get_data(UTC)
        return data.val

    def get_data(self, UTC):
        try:
            Y, M, D, H = self._get_keys_from_time(UTC)
        except:
            #print("Could not get keys from time...")
            return VA(INVALID_VALUE)
        try:
            return self.dbase[Y][M][D][H]
        except:
            pass
        #print("%s %s %s %s Not found" % (Y, M, D, H))
        for Y in self.dbase.keys():
            try:
                #print("Trying %s %s %s %s" % (Y, M, D, H))
                return self.dbase[Y][M][D][H]
            except:
                #print("%s %s %s %s Not Found" % (Y, M, D, H))
                pass
        return VA(INVALID_VALUE)

    def duplicate_data(self, UTC, new_UTC, interval, adjustment=AdjustData()):
        hours = (interval.days * 24) + ceil(interval.seconds/3600.0)
        for h_offset in range(0, hours):
            src_UTC = UTC + timedelta(hours=h_offset)
            trg_UTC = new_UTC + timedelta(hours=h_offset)
            y, m, d, h = self._get_keys_from_time(src_UTC)
            vl = copy.deepcopy(self.dbase[y][m][d][h])
            newval = adjustment.adjust([vl.val])[0]
            self.add_ymdh(trg_UTC, newval, [])
            Y, M, D, H = self._get_keys_from_time(trg_UTC)
            self.dbase[Y][M][D][H].data_array = vl.data_array

    def adjust_values(self, UTC, interval, adj):
        hours = (interval.days * 24) + ceil(interval.seconds/3600.0)
        for h_offset in range(0, hours):
            curtime = UTC + timedelta(hours=h_offset)
            y, m, d, h = self._get_keys_from_time(curtime)
            try:
                newval = adj.adjust([self.dbase[y][m][d][h].val])[0]
                self.dbase[y][m][d][h].val = newval
            except KeyError as e:
                logging.critical("Data does not exist for %s" % (curtime.strftime(DATE_FORMAT)))
                raise e

    def verify_range(self, UTC, interval):
        hours = (interval.days * 24) + ceil(interval.seconds/3600.0)
        missing = []
        start_time = None
        start_incr = None
        for hour in range(0, hours):
            incr = timedelta(hours=hour)
            UTC_i = UTC + incr
            y, m, d, h = self._get_keys_from_time(UTC_i)
            try:
                val = self.dbase[y][m][d][h]
                if start_time is not None:
                    missing.append ([start_time, incr - start_incr])
                    start_time = None
                    start_incr = None
            except:
                if start_time is None:
                    start_time = UTC_i
                    start_incr = incr
        if start_time is not None:
            missing.append ([start_time, interval - start_incr])
        return missing

    def copy_nearest(self, UTC, interval):
        hours = (interval.days * 24) + ceil(interval.seconds/3600.0)
        one_hour = timedelta(hours=1)
        for hour in range(0, hours):
            incr = timedelta(hours=hour)
            targ = UTC + incr
            y, m, d, h = self._get_keys_from_time(targ)
            try:
                val = self.dbase[y][m][d][h]
            except KeyError:
                src = self._determine_nearest_time(targ)
                self.duplicate_data(src, targ, one_hour)

    def create_base(self, UTC, interval):
        missing = self.verify_range(UTC, interval)
        for miss_u, miss_i in missing:
            self.copy_nearest(miss_u, miss_i)

