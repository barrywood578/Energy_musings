#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Support for New Brunswich Comma Separated Values files.

    Computes UTC time for each local date/time,
    and outputs a load file in standard format.
"""

from optparse import OptionParser
from collections import OrderedDict
import operator
import sys
import os
import logging
from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl import load_workbook
from datetime import datetime, timezone
import pytz

sys.path.append('../Common')
from common_defs import *
from demand_file import *

class NBSpreadsheetFiles(object):
    UNKNOWN_INDEX = -1
    def __init__(self, do_all_files = False, file_paths = []):
        self.lines = []
        self.files = []
        self.demand_file = demand_file()
        self.dst = False
        self.hour_index = self.UNKNOWN_INDEX
        self.load_index = self.UNKNOWN_INDEX

        if do_all_files:
            file_paths = []
            file_list = [f for f in os.listdir('.') if os.path.isfile(f)]
            for each_file in file_list:
                filename, file_extension = os.path.splitext(each_file)
                if file_extension == CSV_FILE_EXTENSION:
                    file_paths.append(each_file)

        for path in file_paths:
            try:
                self.check_file(path)
                self.read_csv_file(path)
                self.files.append(path)
                logging.warning("Parsed file %s" % path)
            except ValueError as e:
                if do_all_files:
                    continue
                print(e)
                sys.exit(-1)

        self.create_load_db()

    def check_file(self, file_path):
        if not os.path.isfile(file_path):
            raise ValueError("File '%s' does not exist!" % file_path)
        filename, file_extension = os.path.splitext(file_path)
        if CSV_FILE_EXTENSION != file_extension:
            raise ValueError("File '%s' wrong type, want '%s' but got %s!" %
                    (file_path, CSV_FILE_EXTENSION, file_extension))

    def read_csv_file(self, file_path):
        with open(file_path, 'r') as demand_file:
            lines = [line.strip() for line in demand_file.readlines()]

        if lines[0] != "HOUR,NB_LOAD,NB_DEMAND,ISO_NE,NMISA,QUEBEC,NOVA_SCOTIA,PEI":
            raise ValueError("File %s Unknown format" % file_path)

        self.hour_index = 0
        self.load_index = 1

        for line_num, line in enumerate(lines[1:]):
            toks = [tok.strip() for tok in line.split(',')]
            if len(toks) != 8:
                raise ValueError("File %s Line %d has %d tokens" %
                                (file_path, line_num, len(toks)))
            try:
                the_date, the_hour = [tok.strip() for tok in toks[self.hour_index].split(' ')]
                year, month, day = [int(tok.strip()) for tok in the_date.split('-')]
                hour, minute = [int(tok.strip()) for tok in the_hour.split(':')]
                self.lines.append([file_path, line_num, year, month, day, hour, toks[self.load_index]])
            except ValueError as e:
                logging.critical("File %s Line %d processing error." % (file_path, line_num))
                logging.critical("Line: %s." % line)
                logging.critical("date: %s." % the_date)
                logging.critical("hour: %s." % the_hour)
                logging.critical(e)
                return

    def _get_NB_UTC(self, year, month, day, hour_in, dst_in=False):
        local = pytz.timezone("America/Moncton")
        naive = datetime(year, month, day, hour=hour_in)
        local_dt = local.localize(naive, is_dst=dst_in)
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour

    ## Sometimes load figures are "NA", as in Not Available
    ## Interpolate between the previous valid load value and
    ## the next valid load value.  
    def get_next_valid_load(self, prev_load, line_num):
        if self.lines[line_num + 1][self.load_index] == 'NA':
            return ret_next_valid_load(prev_load, line_num + 1)
        return float(prev_load) + float(self.lines[line_num + 1][self.load_index]) / 2;

    def create_load_db(self):
        if self.lines is []:
            logging.error("%s is empty!" % path)
            return

        self.dst = False
        prev_hour = -1
        prev_load = 0

        self.lines.sort(key = lambda x: (x[2], x[3], x[4], x[5]))

        for line_num, line in enumerate(self.lines):
            try:
                path = line[0]
                line_num = int(line[1])
                year = int(line[2])
                month = int(line[3])
                day = int(line[4])
                the_hour = int(line[5])
                if (line[6] == 'NA'):
                    the_load = self.get_next_valid_load(prev_load, line_num)
                else:
                    the_load = float(line[6])
                    prev_load = the_load

                ## Now for some messing about due to Daylight Savings Time entry and exit
                ##
                ## If the time is discontiguous, this is an indication that an hour was skipped
                ## at the start of daylight savings time.  Check for precisely 2 hours, to avoid
                ## obvious rollover at 24.
                if ((the_hour - prev_hour) == 2):
                    self.dst = True

                ## The second instance of an hour indicates that DST has ended.
                if (the_hour == prev_hour):
                    self.dst = False

                utc_y, utc_m, utc_d, utc_h = self._get_NB_UTC(year, month, day, the_hour, self.dst)
                prev_hour = the_hour

                self.demand_file.add_demand_hour([path, line_num,
                                                  utc_y, utc_m, utc_d,    utc_h,
                                                  year , month,   day, the_hour, the_load])
            except ValueError as e:
                logging.warning("Error processing %s Line %d:%s" %
                        (path, line_num, line))
                logging.warning(e)
                continue

    def read_and_parse_file(self, path):
        self.read_csv_file(path)
        self.parse_lines(path)

    def print_demand_file(self):
        self.demand_file.write_demand_file()

def create_parser():
    parser = OptionParser(description="Support for New Brunswich Hourly Load CSV files.")
    parser.add_option('-c', '--csv',
            dest = 'csv_file_paths',
            action = 'append', type = 'string', default = [],
            help = 'File path to New Brunswich format CSV file.',
            metavar = 'FILE')
    parser.add_option('-a', '--all',
            dest = 'all_csv_files',
            action = 'store_true', default = False,
            help = 'Process all .csv files in this directory.',
            metavar = 'FLAG')
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

    ssheet = NBSpreadsheetFiles(options.all_csv_files,
                                options.csv_file_paths)
    ssheet.print_demand_file()

if __name__ == '__main__':
    sys.exit(main())
