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
from math import isnan
from datetime import datetime, timezone
from common_defs import *
from hourly_mw_file import HourlyMWFile

class generator(object):
    def __init__(self, capacity=0.0, GHG_MWh=0.0, tz_string="Unknown", gen_path=""):
        self.mw = float(capacity)
        try:
            self.ghg = float(GHG_MWh)
        except:
            self.ghg = 0.0
        self.tz_str = tz_string
        self.gen_files = []
        self.min_time = None
        self.max_time = None
        self.add_gen_file(gen_path)

    # Keep generator files separate for now.
    # Each generator file supports exactly
    # the same date range as all the others.
    def add_gen_file(self, gen_path):
        if not os.path.isfile(gen_path):
            return
        gen_file = HourlyMWFile(gen_path)
        self.gen_files.append(gen_file)

        change = False
        if self.min_time is None:
            self.min_time = gen_file.min_time
            self.max_time = gen_file.max_time
        if self.min_time > gen_file.min_time:
            self.min_time = gen_file.min_time
            change = True
        if self.max_time > gen_file.max_time:
            self.max_time = gen_file.max_time
            change = True

        if change:
            interval = self.max_time - self.min_time
            for gen in self.gen_files:
                gen.create_base(self.min_time, interval)

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
        file_dir = os.path.dirname(path)

        with open(path, 'r') as gen_file:
            lines = [line.strip() for line in gen_file.readlines()]

        logging.info("Loaded %s" % path)
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
                self.add_generator(toks, file_dir)
            except (IndexError, ValueError) as e:
                raise ValueError("File %s Line %s bad format, Error '%s' : %s" %
                                 (path, str(line_num + 1), str(e), line))

    def add_generator(self, toks, file_dir):
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
            self.gen_db
            return
        gen_file_path = os.path.join(file_dir, get_filename(fuel))
        self.gen_db[fuel] = generator(capacity, ghg, tz_str, gen_path=gen_file_path)

    def create_base(self, start_utc, interval):
        for fuel in self.gen_db.keys():
            for f in self.gen_db[fuel].gen_files:
                print("Creating base for %s" % fuel)
                f.create_base(start_utc, interval)

    def get_total_capacity(self, dt):
        tot_mw = 0
        for fuel in self.gen_db.keys():
            mw, ghg = self.generate(fuel, self.gen_db[fuel].mw, dt)
            tot_mw += mw
        return tot_mw

    def generate(self, fuel, gen_mw, date):
        if self.gen_db[fuel].gen_files == []:
            mw = self.gen_db[fuel].mw
        else:
            mw = sum(gen.get_value(date) for gen in self.gen_db[fuel].gen_files)
        mw = min(mw, gen_mw)
        return mw, mw * self.gen_db[fuel].ghg

    def get_ghg_emissions(self, req_mw, date):
        if self.sorted_db == {}:
            self.sorted_db = [[self.gen_db[fuel].ghg, fuel] for fuel in self.gen_db.keys()]
            self.sorted_db.sort(key=lambda x: x[0])
        # print("Len: %d %d" % (len(self.gen_db.keys()), len(self.sorted_db)))
        # print("Sorted_db: %s" % ",".join([str(x) for x in self.sorted_db]))
        tot_ghg = 0
        gen_mw = 0
        for _, fuel in self.sorted_db:
            if gen_mw >= req_mw:
                break
            mw, ghg = self.generate(fuel, req_mw-gen_mw, date)
            if isnan(ghg):
                raise ValueError("%s %s ghg is NaN!" % (date.strftime(DATE_FORMAT), fuel))
            gen_mw = gen_mw + mw
            tot_ghg = tot_ghg + ghg
        if req_mw > gen_mw:
            logging.debug("%s Cannot generate %f MW" % (date.strftime(DATE_FORMAT), req_mw))
        if isnan(tot_ghg):
            raise ValueError("%s ghg is NaN!" % date.strftime(DATE_FORMAT))
        return tot_ghg

    def write_generator_file(self, filepath=''):
        try:
            if filepath == '':
                outfile = sys.stdout
            else:
                outfile = open(filepath, 'w')

            if len(self.gen_db) == {}:
                print("Generator file is empty!", file=outfile)
                return
            print(self.generator_file_header, file=outfile)
            for key in sorted(self.gen_db.keys()):
                if self.gen_db[key].mw <= 0.0:
                    continue
                field_vals = [key, str(self.gen_db[key].mw), str(self.gen_db[key].ghg),
                              self.gen_db[key].tz_str]
                line_text = SEPARATOR.join(field_vals)
                print("%s%s%s" % (START_END, line_text, START_END), file=outfile)
        finally:
            if filepath != '':
                outfile.close()

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
