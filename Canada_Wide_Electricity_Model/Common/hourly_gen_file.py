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

class hourly_gen_file(YMDHData):
    hourly_gen_file_header = "UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Capacity(kW)"

    def __init__(self, file_path = ""):
        super(hourly_gen_file, self).__init__()
        self.capacity = []

        if (file_path == ""):
            return
        self.read_hourly_gen_file(file_path)

    def read_hourly_gen_file(self, path):
        lines = []

        with open(path, 'r') as the_file:
            lines = [line.strip() for line in the_file.readlines()]

        if (lines[0] != self.hourly_gen_file_header):
            raise ValueError("File header is '%s', not '%s'.  Halting." %
                    (lines[0], self.hourly_gen_file_header))

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
                self.add_hourly_gen_hour(path, line_num+1,
                                toks[0], toks[1], toks[2], toks[3],
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

    def add_hourly_gen_hour(self, path, line_num,
                                UTC_Y, UTC_M, UTC_D, UTC_H,
                                Local_Y, Local_M, Local_D, Local_H, Capacity):
        (U_Y, U_M, U_D, U_H,
         L_Y, L_M, L_D, L_H, cap) = self.validate_fields(path, line_num,
                                            UTC_Y, UTC_M, UTC_D, UTC_H,
                                            Local_Y, Local_M, Local_D, Local_H,
                                            Capacity)
        data = [path, line_num, U_Y, U_M, U_D, U_H, L_Y, L_M, L_D, L_H, str(cap)]
        self.capacity.append(data)
        UTC = datetime(int(U_Y), int(U_M), int(U_D), hour=int(U_H))
        self.add_ymdh(UTC, float(cap), data, ignore_dup=True)

    def get_hourly_gen_capacity(self, UTC):
        return self.get_value(UTC)

    def write_hourly_gen_file(self, filepath=''):
        if len(self.capacity) == 0:
            if filepath == '':
                print("Generator file is empty!")
            return
        if filepath == '':
            outfile = sys.stdout
        else:
            outfile = open(filepath, 'w')

        print(self.hourly_gen_file_header, file=outfile)
        for data in self.capacity:
            # Skip original file name and line number
            line_text = SEPARATOR.join(data[2:])
            print("%s%s%s" % (START_END, line_text, START_END), file=outfile)
        if filepath != '':
            outfile.close()

def create_parser():
    parser = OptionParser(description="PV Solar file support.")
    parser.add_option('-d', '--hourly_gen',
            dest = 'hourly_gen_file_paths',
            action = 'store', type = 'string', default = "",
            help = 'File path to hourly_gen file.',
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

    hourly_gen = hourly_gen_file(options.hourly_gen_file_paths)
    hourly_gen.write_hourly_gen_file()

if __name__ == '__main__':
    sys.exit(main())
