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
from datetime import datetime, timezone, timedelta
from common_defs import *
from hourly_mw_file import HourlyMWFile
from adjust_data import AdjustData

class generator(object):
    def __init__(self, capacity=0.0, GHG_MWh=0.0, tz_string="Unknown", gen_path=""):
        self.mw = float(capacity)
        try:
            self.ghg = float(GHG_MWh)
        except:
            self.ghg = 0.0
        self.tz_str = tz_string
        self.gen_files = [HourlyMWFile()]
        self.min_time = None
        self.max_time = None
        self.add_gen_file(gen_path)

    # Keep generator files separate for now.
    # Each generator file supports exactly
    # the same date range as all the others.
    def add_gen_file(self, gen_path):
        gen_file = HourlyMWFile(gen_path)
        if gen_file.is_empty():
            logging.debug("File %s is empty." % gen_path)
            return

        if (len(self.gen_files) == 1) and self.gen_files[0].is_empty():
            self.gen_files = []

        change = False
        if self.min_time is None:
            self.min_time = gen_file.min_time
            self.max_time = gen_file.max_time
        if self.min_time > gen_file.min_time:
            self.min_time = gen_file.min_time
            change = True
        if self.max_time < gen_file.max_time:
            self.max_time = gen_file.max_time
            change = True

        if change:
            interval = self.max_time - self.min_time
            for gen in self.gen_files:
                gen.create_base(self.min_time, interval)

        self.gen_files.append(gen_file)

    def add_mw_hour(self, path, line_num, UMT_Local_MW):
        if len(self.gen_files) != 1:
            raise ValueError("Cannot add mw hour to multiple generator files.")
        dt = datetime(int(UMT_Local_MW[-9]), int(UMT_Local_MW[-8]), int(UMT_Local_MW[-7]),
                      hour=int(UMT_Local_MW[-6]))
        if self.min_time is None:
            self.min_time = dt
            self.max_time = dt
        if self.min_time > dt:
            self.min_time = dt
        if self.max_time < dt:
            self.max_time = dt
        self.gen_files[0].add_mw_hour(path, line_num, UMT_Local_MW)

    def is_empty(self):
        return ((False not in ([x.is_empty() for x in self.gen_files])) or (self.gen_files == []))

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

        logging.debug("Loading %s" % path)
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
        logging.info("Loaded %s" % path)

    def add_generator(self, toks, file_dir):
        fuel = toks[0]
        capacity = toks[1].split(" ")[0].replace(",",'')
        capacity = float(capacity)
        if toks[2] == '':
            ghg = 'NONUMBER'
        else:
            ghg = float(toks[2])
        tz_str = toks[3]

        if file_dir == "":
            gen_file_path = ""
        else:
            gen_file_path = os.path.join(file_dir, get_filename(fuel))
        if fuel in self.gen_db:
            self.gen_db[fuel].mw += capacity
            if not ghg == 'NONUMBER':
                self.gen_db[fuel].ghg = ghg
            if not tz_str == '':
                self.gen_db[fuel].tz_str = tz_str
            self.gen_db[fuel].add_gen_file(gen_file_path)
            return
        self.gen_db[fuel] = generator(capacity, ghg, tz_str, gen_path=gen_file_path)

    def add_mw_hour(self, fuel, path, line_num, UMT_Local_MW):
        if fuel not in self.gen_db:
            raise ValueError("Fuel not present, must add generator")
        self.gen_db[fuel].add_mw_hour(path, line_num, UMT_Local_MW)

    def create_base(self, start_utc, interval):
        for fuel in self.gen_db.keys():
            for f in self.gen_db[fuel].gen_files:
                if f.is_empty():
                    continue
                if f.files == []:
                    fname = "NONAME"
                else:
                    fname = f.files[0]
                logging.debug("Creating base for %10s : %s " % (fuel, fname))
                f.create_base(start_utc, interval)

    def get_total_capacity(self, dt):
        tot_mw = 0
        for fuel in self.gen_db.keys():
            # INFW Storage is not supported, It Needs Further Work
            if fuel == FUEL_STORAGE:
                continue
            mw, ghg = self.generate(fuel, self.gen_db[fuel].mw, dt)
            tot_mw += mw
        return tot_mw

    def generate(self, fuel, gen_mw, date):
        if self.gen_db[fuel].gen_files == []:
            mw = self.gen_db[fuel].mw
        elif (len(self.gen_db[fuel].gen_files) == 1
                and self.gen_db[fuel].gen_files[0].is_empty()):
            mw = self.gen_db[fuel].mw
        else:
            vals = [str(gen.get_value(date)) for gen in self.gen_db[fuel].gen_files]
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
        tot_foss = 0
        gen_mw = 0
        gen_db = {}
        for _, fuel in self.sorted_db:
            # INFW Storage is not supported, It Needs Further Work
            if fuel == FUEL_STORAGE:
                continue
            if gen_mw >= req_mw:
                break
            mw, ghg = self.generate(fuel, req_mw-gen_mw, date)
            if isnan(ghg):
                raise ValueError("%s %s ghg is NaN!" % (date.strftime(DATE_FORMAT), fuel))
            gen_db[fuel] = [mw, ghg]
            gen_mw = gen_mw + mw
            tot_ghg = tot_ghg + ghg
            if get_fossil_fuel(fuel):
               tot_foss += ghg
        if req_mw > gen_mw:
            logging.debug("%s Cannot generate %f MW" % (date.strftime(DATE_FORMAT), req_mw))
        if isnan(tot_ghg):
            raise ValueError("%s ghg is NaN!" % date.strftime(DATE_FORMAT))
        return tot_ghg, tot_foss, gen_db

    # Copy hourly mw generator data from source,
    # scaling according to size.
    def copy_missing_data(self, src):
        for fuel in self.gen_db.keys():
            if not ((len(self.gen_db[fuel].gen_files) == 1)
                    and self.gen_db[fuel].gen_files[0].is_empty()):
                continue
            self.gen_db[fuel].gen_files = []
            if fuel not in src.gen_db:
                continue
            if ((len(src.gen_db[fuel].gen_files) == 1)
                and src.gen_db[fuel].gen_files[0].is_empty()):
                continue
            ratio = self.gen_db[fuel].mw / src.gen_db[fuel].mw
            adj = AdjustData(ratio=ratio)
            logging.info("Copying files for %10s.  %10.2f MW / %10.2f MW ratio %f" %
                        (fuel, self.gen_db[fuel].mw, src.gen_db[fuel].mw, ratio))
            self.gen_db[fuel].min_time = src.gen_db[fuel].min_time
            self.gen_db[fuel].max_time = src.gen_db[fuel].max_time
            for gen in src.gen_db[fuel].gen_files:
                gen_file = copy.deepcopy(gen)
                utc = src.gen_db[fuel].min_time
                interval = src.gen_db[fuel].max_time - utc + timedelta(hours=1)
                gen_file.adjust_values(utc, interval, adj)
                self.gen_db[fuel].gen_files.append(gen_file)

    def write_generator_file(self, filepath='', write_hourly_files=False):
        try:
            if filepath == '':
                outfile = sys.stdout
            else:
                outfile = open(filepath, 'w')

            if len(self.gen_db) == {}:
                print("Generator file is empty!", file=outfile)
                return
            print(self.generator_file_header, file=outfile)
            for fuel in sorted(self.gen_db.keys()):
                if self.gen_db[fuel].mw <= 0.0:
                    continue
                field_vals = [fuel, str(self.gen_db[fuel].mw), str(self.gen_db[fuel].ghg),
                              self.gen_db[fuel].tz_str]
                line_text = SEPARATOR.join(field_vals)
                print("%s%s%s" % (START_END, line_text, START_END), file=outfile)

                if write_hourly_files and filepath != '' and MAPPING_KEYWORDS[fuel][FILENAME] != "":
                    base = os.path.dirname(filepath)
                    gen_fp = os.path.join(base, MAPPING_KEYWORDS[fuel][FILENAME])
                    if not self.gen_db[fuel].is_empty():
                        self.gen_db[fuel].gen_files[0].write_hourly_mw_file(filepath=gen_fp)
                        logging.info("Wrote %s'" % gen_fp)
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
