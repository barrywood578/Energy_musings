#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Support for the common "hourly generation file" file format.

    Each file line contains:
    Universal Coordinated Time (UCT) Year, Month, Day, Hour
    Local Year, Month, Day, Hour
    Power in kilowatts, to one decimal place
             =========
"""

from optparse import OptionParser
from collections import OrderedDict
import operator
import sys
import os
import logging
import copy
from datetime import datetime, timezone, timedelta
from ymdh_data import YMDHData, VA
from common_defs import *

class HourlyMWFile(YMDHData):
    file_header = "UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)"

    def __init__(self, file_path = ""):
        super(HourlyMWFile, self).__init__()
        self.lines = []
        self.token_count = len(self.file_header.split(", "))

        if (file_path == ""):
            return
        self.read_hourly_mw_file(file_path)

    def read_hourly_mw_file(self, path):
        lines = []

        with open(path, 'r') as the_file:
            lines = [line.strip() for line in the_file.readlines()]

        if (lines[0] != self.file_header):
            raise ValueError("File header is '%s', not '%s'.  Halting." %
                    (lines[0], self.file_header))

        logging.info("Loaded %s" % path)
        for line_num, line in enumerate(lines[1:]):
            if ((line[0] != START_END) or (line[-1] != START_END)):
                raise ValueError("File %s Line %d delimiters '%s' '%s' not '%s'"
                                 "'%s'. Halting." %
                                 (path, line_num+1, line[0], line[-1],
                                                START_END, START_END))
            toks = [tok.strip() for tok in line[1:-1].split(SEPARATOR)]
            if len(toks) != self.token_count:
                raise ValueError("File %s Line %d Bad format '%s'" %
                        (path, line_num+1, line))

            try:
                self.add_mw_hour(path, line_num+1, toks)
            except ValueError as e:
                logging.warning("%s" % str(e))
                raise ValueError("File %s Line %d Invalid format '%s'" %
                        (path, line_num+1, line))

    # This looks a bit weird, but allows additional tokens to be
    # prepended to the UMT, local time, and capacity/load tokens.
    def validate_fields(self, path, line_num, toks):
        try:
            u_y = str(int(toks[-9]))
            u_m = str(int(toks[-8]))
            u_d = str(int(toks[-7]))
            u_h = str(int(toks[-6]))
            l_y = str(int(toks[-5]))
            l_m = str(int(toks[-4]))
            l_d = str(int(toks[-3]))
            l_h = str(int(toks[-2]))
            mw  = str(float(toks[-1]))
            if (not ((int(u_m)  in range (1, 13)) and
                     (int(l_m)  in range (1, 13)) and
                     (int(u_d)  in range (1, 32)) and
                     (int(l_d)  in range (1, 32)) and
                     (int(u_h)  in range (0, 24)) and
                     (int(l_h)  in range (0, 24)))):
                raise ValueError("Dates out of range.")
            if (float(mw) < 0.0) or (float(mw) > 1000000):
                raise ValueError("MW is out of range.")
        except ValueError as e:
            logging.info(e)
            raise ValueError("File %s Line %s Data validation error." %
                             (path, str(line_num)))

        return int(u_y), int(u_m), int(u_d), int(u_h), float(mw)

    def add_mw_hour(self, path, line_num, toks):
        U_Y, U_M, U_D, U_H, load = self.validate_fields(path, line_num, toks)
        data = [path, line_num]
        data.extend(toks)
        self.lines.append(data)
        UTC = datetime(U_Y, U_M, U_D, hour=U_H)
        self.add_ymdh(UTC, load, data, ignore_dup=True)

    def get_mw_hour(self, UTC):
        return self.get_value(UTC)

    def duplicate_mw_hours(self, UTC, new_UTC, interval, adj):
        self.duplicate_data(UTC, new_UTC, interval, adj)

    def adjust_mw_hours(self, UTC, interval, adj):
        self.adjust_values(UTC, interval, adj)

    def write_hourly_mw_file(self, filepath=''):
        if len(self.lines) == 0:
            if filepath == '':
                print("Generator file is empty!")
            return
        if filepath == '':
            outfile = sys.stdout
        else:
            outfile = open(filepath, 'w')

        print(self.file_header, file=outfile)
        for data in self.lines:
            # Do not print file name and line number
            line_text = SEPARATOR.join([str(x) for x in data[2:]])
            print("%s%s%s" % (START_END, line_text, START_END), file=outfile)
        if filepath != '':
            outfile.close()

def create_parser():
    parser = OptionParser(description="Hourly MW File support.")
    parser.add_option('-d', '--hourly_mw',
            dest = 'hourly_mw_file_paths',
            action = 'store', type = 'string', default = "",
            help = 'File path to hourly_mw file.',
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

    hourly_mw = hourly_mw_file(options.hourly_mw_file_paths)
    hourly_mw.write_hourly_mw_file()

if __name__ == '__main__':
    sys.exit(main())
