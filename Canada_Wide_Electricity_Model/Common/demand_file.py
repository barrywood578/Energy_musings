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
from ymdh_data import VA, YMDHData

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

class demand_file(YMDHData):
    demand_file_header = "File, LineNum, UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)"

    def __init__(self, file_path = ""):
        super(demand_file, self).__init__()
        self.demand = []
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
                self.add_demand_hour(toks, True)
            except ValueError as e:
                print(str(e))
                raise ValueError("File %s Line %d Invalid format '%s'" %
                        (path, line_num+1, line))

    def add_demand_hour(self, field_list, ignore_dup=False):
        d_hr = demand_hour(field_list)

        if (d_hr.validate_ymdhMW()):
            self.demand.append(d_hr)
            UTC = datetime(int(d_hr.UTC_Y),
                           int(d_hr.UTC_M),
                           int(d_hr.UTC_D),
                           hour=int(d_hr.UTC_H))
            self.add_ymdh(UTC, float(d_hr.demand_MW), field_list,
                          ignore_dup=ignore_dup)
            return
        raise ValueError("Invalid demand hour: %s" % field_list)


    def get_demand(self, UTC):
        return self.get_value(UTC)

    def duplicate_demand(self, UTC, new_UTC, interval, adj):
        self.duplicate_data(UTC, new_UTC, interval, adj)

    def adjust_demand(self, UTC, interval, adj):
        self.adjust_values(UTC, interval, adj)

    # NOTE: calls to duplidate_demand and adjust_demand do not
    #       modify the files read in!
    def write_demand_file(self):
        if len(self.demand) == 0:
            print("Demand file is empty!")
            return
        print(self.demand_file_header)
        for line in self.demand:
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
