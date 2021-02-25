#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Support for the common "generation profile" file format.

    Each file line contains:


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

class generator(object):
    def __init__(self, capacity=0.0, GHG_MWh=0.0, tz_string="Unknown", gen_file="NoFile"):
        self.mw = float(capacity)
        self.ghg = float(GHG_MWh)
        self.tz_str = tz_string
        self.gen_file = gen_file

class generator_file(object):
    generator_file_header = "Fuel, Capacity, GHG_MWh, Timezone"

    def __init__(self, file_path = ""):
        self.gen_db = {}
        self.sorted_db = {}

        if (file_path == ""):
            return
        self.read_generator_file(file_path)

    def read_generator_file(self, path):
        lines = {}

        with open(path, 'r') as gen_file:
            lines = [line.strip() for line in gen_file.readlines()]

        if (lines[0] != self.generator_file_header):
            raise ValueError("File header is '%s', not '%s'.  Halting." %
                    (lines[0], self.generator_file_header))

        for line_num, line in enumerate(lines[1:]):
            if ((line[0] != START_END) or (line[-1] != START_END)):
                raise ValueError("File %s Line %s delimiters '%s' '%s' not '%s'"
                                 "'%s'. Halting." %
                                 (path, str(line_num), line[0], line[-1], START_END, START_END))
            toks = [tok.strip() for tok in line[1:-1].split(SEPARATOR)]

            try:
                self.add_generator(toks)
            except (IndexError, ValueError) as e:
                raise ValueError("File %s Line %s bad format, Error '%s' : %s" %
                                 (path, str(line_num + 1), str(e), line))

    def add_generator(self, toks):
        fuel = toks[0]
        capacity = toks[1].split(" ")[0].replace(",",'')
        capacity = float(capacity)
        if toks[2] == '':
            ghg = 'NONUMBER'
        else:
            ghg = float(toks[2])
        tz_str = toks[3]
        if fuel in self.gen_db:
            self.gen_db[fuel].mw += capacity
            if not ghg == 'NONUMBER':
                self.gen_db[fuel].ghg = ghg
            if not tz_str == '':
                self.gen_db[fuel].tz_str = tz_str
            return
        self.gen_db[fuel] = generator(capacity, ghg, tz_str)

    def get_total_capacity(self, dt):
        return sum(self.gen_db[key].mw for key in self.gen_db.keys())

    def get_ghg_emissions(self, gen_mw):
        if self.sorted_db == {}:
            self.sorted_db = [[self.gen_db[key].ghg, key] for key in self.gen_db.keys()]
            self.sorted_db.sort(key=lambda x: x[0])
        # print("Len: %d %d" % (len(self.gen_db.keys()), len(self.sorted_db)))
        # print("Sorted_db: %s" % ",".join([str(x) for x in self.sorted_db]))
        tot_ghg = 0
        tot_mw = 0
        for ghg, key in self.sorted_db:
            if tot_mw >= gen_mw:
                break
            mw = self.gen_db[key].mw
            if tot_mw + mw > gen_mw:
                mw = gen_mw - tot_mw
            tot_mw = tot_mw + mw
            tot_ghg = tot_ghg + (mw * ghg)
        if gen_mw > tot_mw:
            raise ValueError("Cannot generate %f MW" % gen_mw)
        return tot_ghg

    def write_generator_file(self):
        if len(self.gen_db) == {}:
            print("Generator file is empty!")
            return
        print(self.generator_file_header)
        for key in sorted(self.gen_db.keys()):
            if self.gen_db[key].mw <= 0.0:
                continue
            field_vals = [key, str(self.gen_db[key].mw), str(self.gen_db[key].ghg),
                          self.gen_db[key].tz_str]
            line_text = SEPARATOR.join(field_vals)
            print("%s%s%s" % (START_END, line_text, START_END))

def create_parser():
    parser = OptionParser(description="Generator file support.")
    parser.add_option('-g', '--gen',
            dest = 'gen_file_path',
            action = 'store', type = 'string', default = "",
            help = 'File path to generator file.',
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

    generator = generator_file(options.gen_file_path)
    generator.write_generator_file()

if __name__ == '__main__':
    sys.exit(main())
