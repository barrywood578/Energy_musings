#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Support for the common "demand profile" file format.

    Each file line contains:
    Source file, line number,
    Universal Coordinated Time (UCT) Year, Month, Day, Hour
    Local Year, Month, Day, Hour
    Load in megawatts (MW), to one decimal place.

"""

from optparse import OptionParser
from collections import OrderedDict
import operator
import sys
import os
import logging
import copy
from datetime import datetime, timezone, timedelta
from math import ceil
from common_defs import *
from adjust_data import AdjustData

class fp_mw(object):
    def __init__(self, fp="", mw=0.0):
        self.fp = fp
        self.mw = float(mw)

class demand_hour(object):
    default_year = "0000"
    default_month = "00"
    default_day = "00"
    default_hour = "24"
    default_demand = "000000.0"

    def __init__(self, values = ["", "", "0000", "00", "00", "24", 
                                         "0000", "00", "00", "24", "000000.0"]):
        self.file_path = ""
        self.line_num = ""
        self.UTC_Y = ""
        self.UTC_M = ""
        self.UTC_D = ""
        self.UTC_H = ""
        self.local_Y = ""
        self.local_M = ""
        self.local_D = ""
        self.local_H = ""
        self.demand_MW = ""

        self.set_demand_hour_to_list(values)

    def validate_ymdhMW(self):
        UTC = ("%s-%s-%s" % (self.UTC_Y, self.UTC_M, self.UTC_D))
        local = ("%s-%s-%s" % (self.local_Y, self.local_M, self.local_D))

        try:
            self.UTC_Y     = str(int(self.UTC_Y))
            self.UTC_M     = str(int(self.UTC_M))
            self.UTC_D     = str(int(self.UTC_D))
            self.UTC_H     = str(int(self.UTC_H))
            self.local_Y   = str(int(self.local_Y))
            self.local_M   = str(int(self.local_M))
            self.local_D   = str(int(self.local_D))
            self.local_H   = str(int(self.local_H))
            self.demand_MW = str(float(self.demand_MW))
            UTC_date = datetime.strptime(UTC, '%Y-%m-%d')
            local_date = datetime.strptime(local, '%Y-%m-%d')
            if (not ((int(self.UTC_H) in range(0, 24)) and
                     (int(self.local_H) in range(0, 24)))):
                return False
            if ((float(self.demand_MW) > 999999.9) or
                     (float(self.demand_MW) < 0.0)):
                return False
        except ValueError as e:
            logging.info("File %s Line %s Data validation error." %
                         (self.file_path, str(self.line_num)))
            logging.info(e)
            return False

        return True

    def get_list_from_demand_hour(self):
        return [self.file_path,
                self.line_num,
                self.UTC_Y,
                self.UTC_M,
                self.UTC_D,
                self.UTC_H,
                self.local_Y,
                self.local_M,
                self.local_D,
                self.local_H,
                self.demand_MW]

    def set_demand_hour_to_list(self, the_list):
        if not (len(the_list) == 11):
            raise ValueError("List must have 11 entries, not '%s'" %
                              ','.join(the_list))
        self.file_path = str(the_list[0])
        self.line_num  = str(the_list[1])
        self.UTC_Y     = str(the_list[2])
        self.UTC_M     = str(the_list[3])
        self.UTC_D     = str(the_list[4])
        self.UTC_H     = str(the_list[5])
        self.local_Y   = str(the_list[6])
        self.local_M   = str(the_list[7])
        self.local_D   = str(the_list[8])
        self.local_H   = str(the_list[9])
        self.demand_MW = str(the_list[10])

class demand_file(object):
    demand_file_header = "File, LineNum, UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)"

    def __init__(self, file_path = ""):
        self.dbase = []
        self.xref_load = {}

        if (file_path == ""):
            return
        self.read_demand_file(file_path)

    def _get_xref_keys_from_time(self, UTC):
        y = str(UTC.year)
        m = str(UTC.month)
        d = str(UTC.day)
        h = str(UTC.hour)
        return y, m, d, h

    def read_demand_file(self, path):
        lines = []

        with open(path, 'r') as the_file:
            lines = [line.strip() for line in the_file.readlines()]

        if (lines[0] != self.demand_file_header):
            raise ValueError("File header is '%s', not '%s'.  Halting." %
                    (lines[0], self.demand_file_header))

        for line_num, line in enumerate(lines[1:]):
            if ((line[0] != START_END) or (line[-1] != START_END)):
                raise ValueError("File %s Line %d delimiters '%s' '%s' not '%s'"
                                 "'%s'. Halting." %
                                 (path, line_num+1, line[0], line[-1],
                                                START_END, START_END))
            toks = [tok.strip() for tok in line[1:-1].split(SEPARATOR)]

            try:
                self.add_demand_hour(toks)
            except ValueError as e:
                print(str(e))
                raise ValueError("File %s Line %d Invalid format '%s'" %
                        (path, line_num+1, line))

    def add_xref_load(self, d_hr):
        if not d_hr.UTC_Y in self.xref_load:
            self.xref_load[d_hr.UTC_Y] = {}

        if not d_hr.UTC_M in self.xref_load[d_hr.UTC_Y]:
            self.xref_load[d_hr.UTC_Y][d_hr.UTC_M] = {}

        if not d_hr.UTC_D in self.xref_load[d_hr.UTC_Y][d_hr.UTC_M]:
            self.xref_load[d_hr.UTC_Y][d_hr.UTC_M][d_hr.UTC_D] = {}

        if d_hr.UTC_H in self.xref_load[d_hr.UTC_Y][d_hr.UTC_M][d_hr.UTC_D]:
            raise ValueError(
                "File %s Line %s Duplicate %s %s %s %s! Original file %s" %
                (d_hr.file_path, d_hr.line_num,
                 d_hr.UTC_Y, d_hr.UTC_M, d_hr.UTC_D, d_hr.UTC_H,
                 self.xref_load[d_hr.UTC_Y][d_hr.UTC_M][d_hr.UTC_D][d_hr.UTC_H].fp))

        self.xref_load[d_hr.UTC_Y][d_hr.UTC_M][d_hr.UTC_D][d_hr.UTC_H] = (
                fp_mw(d_hr.file_path, d_hr.demand_MW))

    def add_demand_hour(self, field_list):
        d_hr = demand_hour(field_list)

        if (d_hr.validate_ymdhMW()):
            self.dbase.append(d_hr)
            self.add_xref_load(d_hr)
            return

        raise ValueError("Invalid demand hour: %s" % field_list)

    def duplicate_demand(self, src_UTC, new_UTC, interval, adjustment):
        hours = (interval.days * 24) + ceil(interval.seconds/3600)
        for i in range(0, hours):
            y, m, d, h = self._get_xref_keys_from_time(src_UTC)
            mw = self.xref_load[y][m][d][h].mw
            new_mw = adjustment.adjust([mw])[0]
            field_list = ["Dupped", 0,
                         new_UTC.year, new_UTC.month, new_UTC.day, new_UTC.hour,
                         new_UTC.year, new_UTC.month, new_UTC.day, new_UTC.hour,
                         new_mw]
            self.add_demand_hour(field_list)
            src_UTC = src_UTC + timedelta(hours=1)
            new_UTC = new_UTC + timedelta(hours=1)

    def adjust_demand(self, src_UTC, interval, adj):
        hours = (interval.days * 24) + ceil(interval.seconds/3600)
        for i in range(0, hours):
            y, m, d, h = self._get_xref_keys_from_time(src_UTC)
            new_mw = adj.adjust([self.xref_load[y][m][d][h].mw])[0]
            self.xref_load[y][m][d][h].mw = new_mw
            src_UTC = src_UTC + timedelta(hours=1)

    def get_demand(self, UTC):
        try:
            return self.xref_load[str(UTC.year)][str(UTC.month)][str(UTC.day)][str(UTC.hour)].mw
        except:
            return LOAD_ERROR

    def write_demand_file(self):
        if len(self.dbase) == 0:
            print("Demand file is empty!")
            return
        print(self.demand_file_header)
        for line in self.dbase:
            field_vals = line.get_list_from_demand_hour()
            line_text = SEPARATOR.join(field_vals)
            print("%s%s%s" % (START_END, line_text, START_END))

def create_parser():
    parser = OptionParser(description="Demand file support.")
    parser.add_option('-d', '--demand',
            dest = 'demand_file_paths',
            action = 'store', type = 'string', default = "",
            help = 'File path to demand file.',
            metavar = 'FILE')
    return parser

def main(argv = None):
    logging.basicConfig(level=logging.WARN)

    parser = create_parser()
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = parser.parse_args(argv)
    if len(argv) != 0:
        print('Must enter at least one file path!')
        print
        parser.print_help()
        return -1

    demand = demand_file(options.demand_file_paths)
    demand.write_demand_file()

if __name__ == '__main__':
    sys.exit(main())
