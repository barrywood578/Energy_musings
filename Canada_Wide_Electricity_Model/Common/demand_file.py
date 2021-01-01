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
from datetime import datetime, timezone
from common_defs import *

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
            UTC_date = datetime.strptime(UTC, '%Y-%m-%d')
            local_date = datetime.strptime(local, '%Y-%m-%d')
            if (not ((int(self.UTC_H) in range(0, 24)) and
                     (int(self.local_H) in range(0, 24)))):
                return False
            if ((float(self.demand_MW) > 999999.9) or
                     (float(self.demand_MW) < 0.0)):
                return False
        except ValueError as e:
            logging.info("File %s Line %s Date validation error." %
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
        self.lines = []
        self.dbase = []
        self.xref_load = {}

        if (file_path == ""):
            return

        try:
            self.read_and_parse_file(file_path)
        except ValueError as e:
            print(e)
            sys.exit(-1)

    def read_demand_file(self, path):
        self.lines = []

        with open(path, 'r') as demand_file:
            lines = [line.strip() for line in demand_file.readlines()]

        if (self.lines[0] != self.demand_file_header):
            raise ValueError("File header is '%s', not '%s'.  Halting." %
                    (self.lines[0], self.demand_file_header))

        for line, line_num in enumerate(self.lines):
            if ((line[0] != START_END) or (line[-1] != START_END)):
                raise ValueError("File %s Line %d delimiters '%s' '%s' not '%s'"
                                 "'%s'. Halting." %
                                 (line[0], line[-1], START_END, START_END))
            toks = [tok.strip() for tok in line[1:-1].split(SEPARATOR)]

            try:
                self.add_demand_hour(toks)
            except ValueError as e:
                print(e)
                raise ValueError("File %s Line %d Invalid format '%s'" %
                        (path, line_num))

    def add_xref_load(self, d_hr):
        if not d_hr.UTC_Y in self.xref_load:
            self.xref_load[d_hr.UTC_Y] = {}

        if not d_hr.UTC_M in self.xref_load[d_hr.UTC_Y]:
            self.xref_load[d_hr.UTC_Y][d_hr.UTC_M] = {}

        if not d_hr.UTC_D in self.xref_load[d_hr.UTC_Y][d_hr.UTC_M]:
            self.xref_load[d_hr.UTC_Y][d_hr.UTC_M][d_hr.UTC_D] = {}

        if d_hr.UTC_H in self.xref_load[d_hr.UTC_Y][d_hr.UTC_M][d_hr.UTC_D]:
            raise ValueError(
                "File %s Line %s Duplicate UTC hour %s! Original %s" %
                (d_hr.file_path, str(d_hr.line_num), str(d_hr.UTC_H),
                 self.xref_load[d_hr.UTC_Y][d_hr.UTC_M][d_hr.UTC_D][d_hr.UTC_H]))

        self.xref_load[d_hr.UTC_Y][d_hr.UTC_M][d_hr.UTC_D][d_hr.UTC_H] = d_hr.file_path

    def add_demand_hour(self, field_list):
        d_hr = demand_hour(field_list)

        if (d_hr.validate_ymdhMW()):
            self.dbase.append(d_hr)
            self.add_xref_load(d_hr)
            return

        raise ValueError("Invalid demand hour: %s" % field_list)

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
            action = 'assign', type = 'string', default = "",
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
    ssheet.print_db()

if __name__ == '__main__':
    sys.exit(main())
