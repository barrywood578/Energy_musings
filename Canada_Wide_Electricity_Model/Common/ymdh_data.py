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

    def __iter__(self):
        self.Ys = sorted(list(self.dbase.keys()))
        self.Ms = []
        self.Ds = []
        self.Hs = []
        self.Y_i = -1
        self.M_i = -1
        self.D_i = -1
        self.H_i = -1
        if len(self.Ys) == 0:
            return self
        return self

    def __next__(self):
        self.H_i += 1
        if self.H_i >= len(self.Hs):
            self.H_i = 0
            self.D_i += 1
            if self.D_i >= len(self.Ds):
                self.D_i = 0
                self.M_i += 1
                if self.M_i >= len(self.Ms):
                    self.M_i = 0
                    self.Y_i += 1
                    if self.Y_i >= len(self.Ys):
                        raise StopIteration
                    self.Y = self.Ys[self.Y_i]
                    self.Ms = list(self.dbase[self.Y].keys())
                self.M = self.Ms[self.M_i]
                self.Ds = list(self.dbase[self.Y][self.M].keys())
            self.D = self.Ds[self.D_i]
            self.Hs = list(self.dbase[self.Y][self.M][self.D].keys())
        self.H = self.Hs[self.H_i]
        return self.dbase[self.Y][self.M][self.D][self.H]

    def _get_subset(self, keys, is_start, is_end, start, end):
        ret = keys
        if is_start and is_end:
            keys = [x for x in keys if (int(x) >= start and int(x) <= end)]
        elif is_start:
            keys = [x for x in keys if int(x) >= start]
        elif is_end:
            keys = [x for x in keys if int(x) <= end]
        return keys

    def gen_func(self, UTC=None, interval=None, debug=False):
        start_time = UTC
        end_time = UTC + interval - timedelta(hours=1)

        Ys = sorted([x for x in self.dbase.keys() if (int(x) >= start_time.year and int(x) <= end_time.year)])
        for Y in Ys:
            i_Y = int(Y)
            Ms = self._get_subset(self.dbase[Y].keys(),
                                 start_time.year == i_Y,
                                 end_time.year == i_Y,
                                 start_time.month, end_time.month)
            for M in Ms:
                i_M = int(M)
                Ds = self._get_subset(self.dbase[Y][M].keys(),
                                     start_time.year == i_Y and start_time.month == i_M,
                                     end_time.year == i_Y and end_time.month == i_M,
                                     start_time.day, end_time.day)
                for D in Ds:
                    i_D = int(D)
                    Hs = self._get_subset(self.dbase[Y][M][D].keys(),
                                         start_time.year == i_Y and start_time.month == i_M and start_time.day == i_D,
                                         end_time.year == i_Y and end_time.month == i_M and end_time.day == i_D,
                                         start_time.hour, end_time.hour)
                    for H in Hs:
                        yield self.dbase[Y][M][D][H]

    def _get_keys_from_time(self, UTC):
        y = str(UTC.year)
        m = str(UTC.month)
        d = str(UTC.day)
        h = str(UTC.hour)
        return y, m, d, h

    def _get_keys_from_va(self, va):
        Y, M, D, H = va.data_array[0][-9:-5]
        return Y, M, D, H

    def _get_UTC_from_va(self, va):
        y, m, d, h = [int(x) for x in self._get_keys_from_va(va)]
        return datetime(y, m, d, hour=h)

    def is_empty(self):
        return self.dbase == {}

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
                    ret = datetime(int(Y), int(m), int(d), hour=int(h))
                    return ret
                except KeyError:
                    pass
        raise ValueError("No other year has same Month/Day/Hour!\n%s-%s-%s-%s"
                         % (y, m, d, h))

    def add_ymdh(self, UTC, val, data, ignore_dup=False):
        if self.min_time is None:
            self.min_time = UTC
            self.max_time = UTC
        elif UTC < self.min_time:
            self.min_time = UTC
        elif UTC > self.max_time:
            self.max_time = UTC

        va = VA(val, data)
        if data != []:
            date = self._get_UTC_from_va(va)
            if date != UTC:
                raise ValueError("Data %s does not match UTC %s" %
                                 (date.strftime(DATE_FORMAT),
                                  UTC.strftime(DATE_FORMAT)))
        Y, M, D, H = self._get_keys_from_time(UTC)

        if not Y in self.dbase:
            self.dbase[Y] = {}

        if not M in self.dbase[Y]:
            self.dbase[Y][M] = {}

        if not D in self.dbase[Y][M]:
            self.dbase[Y][M][D] = {}

        if H in self.dbase[Y][M][D]:
            if ignore_dup:
                self.dbase[Y][M][D][H] = self.dbase[Y][M][D][H] + va
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
            return VA(INVALID_VALUE)
        try:
            return self.dbase[Y][M][D][H]
        except:
            pass
        return VA(INVALID_VALUE)

    def duplicate_data(self, UTC, new_UTC, interval, adjustment=AdjustData(),
                             debug=False):
        delta = new_UTC - UTC
        for va in self.gen_func(UTC, interval, debug=debug):
            Y, M, D, H = self._get_keys_from_va(va)
            src_UTC = self._get_UTC_from_va(va)
            trg_UTC = src_UTC + delta
            vl = copy.deepcopy(va)
            newval = adjustment.adjust([vl.val])[0]

            ty, tm, td, th = self._get_keys_from_time(trg_UTC)
            for da in vl.data_array:
                da[-9] = ty
                da[-8] = tm
                da[-7] = td
                da[-6] = th
            #if debug:
            #    print("Duplicate: src %s trg %s" % (src_UTC.strftime(DATE_FORMAT),
            #                                        trg_UTC.strftime(DATE_FORMAT)))
            self.add_ymdh(trg_UTC, newval, [])
            self.dbase[ty][tm][td][th].data_array = vl.data_array

    def adjust_values(self, UTC, interval, adj, debug=False):
        for va in self.gen_func(UTC, interval, debug):
            va.val = adj.adjust([va.val])[0]

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
                self.duplicate_data(src, targ, one_hour, debug=True)

    def create_base(self, UTC, interval):
        missing = self.verify_range(UTC, interval)
        if len(missing):
            logging.debug("Base missing following intervals:")
        else:
            logging.debug("Base already present.")
        for miss_u, miss_i in missing:
            logging.debug("    Start %s Interval %s" % (miss_u.strftime(DATE_FORMAT), str(miss_i)))
            self.copy_nearest(miss_u, miss_i)

