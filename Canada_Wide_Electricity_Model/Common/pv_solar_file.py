#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Support for the common "pv solar generation" file format.

    Each file line contains:
    Universal Coordinated Time (UCT) Year, Month, Day, Hour
    Local Year, Month, Day, Hour
    Power in kilowatts, to one decimal place

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

class pv_solar_hour(object):
    def __init__(self, values = ["0000", "00", "00", "24", "000000.0"]):
        self.local_Y = ""
        self.local_M = ""
        self.local_D = ""
        self.local_H = ""
        self.capacity_kW = 0.0
        self.set_pv_solar_hour_to_list(values)

    def get_list_from_pv_solar_hour(self):
        return [self.local_Y,
                self.local_M,
                self.local_D,
                self.local_H,
                self.capacity_kW]

    def set_pv_solar_hour_to_list(self, the_list):
        if not (len(the_list) == 5):
            raise ValueError("List must have 5 entries, not '%s'" %
                              ','.join(the_list))
        self.local_Y   = str(the_list[0])
        self.local_M   = str(the_list[1])
        self.local_D   = str(the_list[2])
        self.local_H   = str(the_list[3])
        self.capacity_kW = float(the_list[4])

class pv_solar_file(object):
    pv_solar_file_header = "UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Capacity(kW)"

    def __init__(self, file_path = ""):
        self.capacity = {}

        if (file_path == ""):
            return
        self.read_pv_solar_file(file_path)

    def read_pv_solar_file(self, path):
        lines = []

        with open(path, 'r') as the_file:
            lines = [line.strip() for line in the_file.readlines()]

        if (lines[0] != self.pv_solar_file_header):
            raise ValueError("File header is '%s', not '%s'.  Halting." %
                    (lines[0], self.pv_solar_file_header))

        for line_num, line in enumerate(lines[1:]):
            if ((line[0] != START_END) or (line[-1] != START_END)):
                raise ValueError("File %s Line %d delimiters '%s' '%s' not '%s'"
                                 "'%s'. Halting." %
                                 (path, line_num+1, line[0], line[-1],
                                                START_END, START_END))
            toks = [tok.strip() for tok in line[1:-1].split(SEPARATOR)]
            if len(toks) != 9:
                raise ValueError("File %s Line %d Bad format '%s'" %
                        (path, line_num+1, line))

            try:
                self.add_pv_solar_hour(path, line_num+1, toks[0], toks[1], toks[2], toks[3],
                                                       toks[4], toks[5], toks[6], toks[7], toks[8])
            except ValueError as e:
                logging.warning("%s" % str(e))
                raise ValueError("File %s Line %d Invalid format '%s'" %
                        (path, line_num+1, line))

    def validate_fields(self, path, line_num, UTC_Y, UTC_M, UTC_D, UTC_H,
                            Local_Y, Local_M, Local_D, Local_H, Capacity):
        try:
            U_Y = str(int(UTC_Y))
            U_M = str(int(UTC_M))
            U_D = str(int(UTC_D))
            U_H = str(int(UTC_H))
            L_Y = str(int(Local_Y))
            L_M = str(int(Local_M))
            L_D = str(int(Local_D))
            L_H = str(int(Local_H))
            Cap = str(float(Capacity))
            if (not ((int(U_M)  in range (1, 13)) and
                     (int(L_M)  in range (1, 13)) and
                     (int(U_D)  in range (1, 32)) and
                     (int(L_D)  in range (1, 32)) and
                     (int(U_H)  in range (0, 24)) and
                     (int(L_H)  in range (0, 24)))):
                raise ValueError("Dates out of range.")
            if (float(Cap) < 0.0) or (float(Cap) > 1000000):
                raise ValueError("Capacity is out of range.")
        except ValueError as e:
            logging.info(e)
            raise ValueError("File %s Line %s Data validation error." %
                             (path, str(line_num)))

        return U_Y, U_M, U_D, U_H, L_Y, L_M, L_D, L_H, float(Cap)

    def add_pv_solar_hour(self, path, line_num, UTC_Y, UTC_M, UTC_D, UTC_H, Local_Y, Local_M, Local_D, Local_H, Capacity):
        (U_Y, U_M, U_D, U_H,
         L_Y, L_M, L_D, L_H, cap) = self.validate_fields(path, line_num, UTC_Y, UTC_M, UTC_D, UTC_H,
                                                     Local_Y, Local_M, Local_D, Local_H, Capacity)

        if not U_Y in self.capacity.keys():
            self.capacity[U_Y] = {}
        if not U_M in self.capacity[U_Y].keys():
            self.capacity[U_Y][U_M] = {}
        if not U_D in self.capacity[U_Y][U_M].keys():
            self.capacity[U_Y][U_M][U_D] = {}
        if not U_H in self.capacity[U_Y][U_M][U_D].keys():
            self.capacity[U_Y][U_M][U_D][U_H] = pv_solar_hour([L_Y, L_M, L_D, L_H, cap])
            return
        self.capacity[U_Y][U_M][U_D][U_H].capacity_kW += cap

    def get_pv_solar_capacity(self, UTC):
        try:
            return self.capacity[str(UTC.year)][str(UTC.month)][str(UTC.day)][str(UTC.hour)].capacity_kW
        except:
            return LOAD_ERROR

    def write_pv_solar_file(self, filepath=''):
        if len(self.capacity) == 0:
            if filepath == '':
                print("PV Solar file is empty!")
            return
        if filepath == '':
            outfile = sys.stdout
        else:
            outfile = open(filepath, 'w')
        print(self.pv_solar_file_header, file=outfile)
        for year in self.capacity.keys():
            for month in self.capacity[year].keys():
                for day in self.capacity[year][month].keys():
                    for hour in self.capacity[year][month][day].keys():
                        field_vals = [year, month, day, hour]
                        solar_hour = self.capacity[year][month][day][hour].get_list_from_pv_solar_hour()
                        field_vals.extend([str(x) for x in solar_hour])
                        line_text = SEPARATOR.join(field_vals)
                        print("%s%s%s" % (START_END, line_text, START_END),
                                file=outfile)
        if filepath != '':
            outfile.close()

def create_parser():
    parser = OptionParser(description="PV Solar file support.")
    parser.add_option('-d', '--pv_solar',
            dest = 'pv_solar_file_paths',
            action = 'store', type = 'string', default = "",
            help = 'File path to pv_solar file.',
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

    pv_solar = pv_solar_file(options.pv_solar_file_paths)
    pv_solar.write_pv_solar_file()

if __name__ == '__main__':
    sys.exit(main())
