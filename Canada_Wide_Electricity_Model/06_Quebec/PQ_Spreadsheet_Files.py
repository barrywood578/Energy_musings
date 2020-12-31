#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Support for British Columbia XLSX spreadsheet.

    Computes UTC time for each local date/time,
    and outputs a load file in standard format.
"""

from optparse import OptionParser
from collections import OrderedDict
import operator
import sys
import os
import logging
from datetime import datetime, timezone
import pytz

sys.path.append('../Common')
from common_defs import *
from demand_file import *

class date_n_val(object):
    def __init__(self, the_date, the_val, file_name, line_num):
        date_obj = datetime.strptime(the_date, "%Y/%m/%d")
        self.year = date_obj.year
        self.month = date_obj.month
        self.day = date_obj.day
        self.val = float(the_val)
        self.file_name = file_name
        self.line_num = line_num

class date_val_list(object):
    def __init__(self, target_year):
        self.lines = []
        self.months = {}
        self.year = target_year

    def read_values(self, file_path):
        with open(file_path, 'r') as values_file:
            lines = [line.strip() for line in values_file.readlines()]
        
        for line_num, line in enumerate(lines):
            toks = [tok.strip() for tok in line.split(",")]
            date_val = date_n_val(toks[0], toks[1], file_path, line_num)
            if date_val.year != self.year:
                continue
            if date_val.month not in self.months:
                self.months[date_val.month] = {}
            if date_val.day not in self.months[date_val.month]:
                self.months[date_val.month][date_val.day] = []
            self.months[date_val.month][date_val.day].append(date_val)

    def average_values(self):
        for month in self.months.keys():
            for day in self.months[month].keys():
                value = (sum(date_val.val for date_val in self.months[month][day]) /
                         len(self.months[month][day]))
                date_val = self.months[month][day][0]
                date_val.val = value
                self.months[month][day] = date_val

class PQSpreadsheetFiles(object):
    def __init__(self, min_paths = [], max_paths = [], curve_paths = [], target_year = 2014):
        self.min_vals = date_val_list(target_year)
        self.max_vals = date_val_list(target_year)
        self.curve = [[] for x in range(1, 25)]
        self.demand_file = demand_file()

        self.read_val_files(min_paths, self.min_vals)
        self.read_val_files(max_paths, self.max_vals)
        self.min_vals.average_values()
        self.max_vals.average_values()

        if curve_paths != []:
            self.read_curve_files(curve_paths)
            self.define_curve()

    def read_val_files(self, file_paths, date_val):
        for path in file_paths:
            try:
                self.check_file(path, CSV_FILE_EXTENSION)
                date_val.read_values(path)
                logging.info("Parsed .csv file %s" % path)
            except ValueError as e:
                print(e)
                sys.exit(-1)

    def read_curve_values(self, file_path):
        lines = []
        with open(file_path, 'r') as values_file:
            lines = [line.strip() for line in values_file.readlines()]
        
        for line in lines:
            toks = [tok.strip() for tok in line.split(",")]
            hour, value = [float(tok) for tok in toks]
            if hour < 1.0:
                continue
            hour_int = int(hour)
            self.curve[hour_int].append(value)

    def read_curve_files(self, file_paths):
        self.curve = [[] for x in range(1,25)]
        for path in file_paths:
            try:
                self.check_file(path, CSV_FILE_EXTENSION)
                self.read_curve_values(path)
                logging.info("Parsed .csv file %s" % path)
            except ValueError as e:
                print(e)
                sys.exit(-1)

    def define_curve(self):
        self.curve[0] = min(self.curve[1])
        for i in range(1,24):
            self.curve[i] = sum(self.curve[i]) / len(self.curve[i])

        curve_top = max(self.curve)
        curve_bot = min(self.curve)
        for i in range(0,24):
            self.curve[i] = (self.curve[i] - curve_bot) / (curve_top - curve_bot)

    def check_min_max(self):
        for month in self.min_vals.months.keys():
            for day in self.max_vals.months[month].keys():
                if (month not in self.min_vals.months.keys()):
                    raise ValueError("Month %d does not exist in min" % month)
                if (day not in self.min_vals.months[month].keys()):
                    raise ValueError("Month %d day %d does not exist in min" % (month, day))
            for day in self.min_vals.months[month].keys():
                if (month not in self.max_vals.months.keys()):
                    raise ValueError("Month %d does not exist in max" % month)
                if (day not in self.max_vals.months[month].keys()):
                    raise ValueError("Month %d day %d does not exist in max" % (month, day))
                if (self.min_vals.months[month][day].val > self.max_vals.months[month][day].val):
                    raise ValueError("Month %d day %d Min %f Max %f" %
                                     (month, day, 
                                      self.min_vals.months[month][day],
                                      self.max_vals.months[month][day]))

    def print_min_max(self):
        for month in sorted(self.min_vals.months.keys()):
            for day in sorted(self.min_vals.months[month].keys()):
                print("Month %2d day %2d Min %8.2f Max %8.2f" %
                                      (month, day, 
                                       self.min_vals.months[month][day].val,
                                       self.max_vals.months[month][day].val))

    def print_curve(self):
        for i in range(0,24):
            print("Hour %d Percentage %9.6f" % (i, self.curve[i] * 100))

    def check_file(self, file_path, extension):
        if not os.path.isfile(file_path):
            raise ValueError("File '%s' does not exist!" % file_path)
        filename, file_extension = os.path.splitext(file_path)
        if extension != file_extension:
            raise ValueError("File '%s' wrong type, want '%s' but got %s!" %
                    (file_path, EXCEL_FILE_EXTENSION, file_extension))

    def get_PQ_UTC(self, year, month, day, hour_in, dst_in=False):
        local = pytz.timezone("America/Montreal")
        naive = datetime(year, month, day, hour=hour_in)
        local_dt = local.localize(naive, is_dst=dst_in)
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour

    def generate_demand_file(self):
        dst = False
        for month in sorted(self.min_vals.months.keys()):
            if month > 11:
                break
            for day in sorted(self.min_vals.months[month].keys()):
                if month == 11 and day > 3:
                    break
                min_val = self.min_vals.months[month][day]
                max_val = self.max_vals.months[month][day]
                val_range = max_val.val - min_val.val
                prev_utc_h = -1
                for hour in range(0, 24):
                    try:
                        utc_y, utc_m, utc_d, utc_h = self.get_PQ_UTC(min_val.year, month, day, hour, dst)
                        if prev_utc_h == -1:
                            prev_utc_h = utc_h - 1
                        # Some jiggery pokery around daylight savings time
                        # transitions.  See PQ_Spreadsheet_Files_unittest.py
                        # testcases for get_PQ_UTC for justification.
                        if prev_utc_h != 23 and utc_h - 1 != prev_utc_h:
                            if utc_h == prev_utc_h:
                                dst = True
                                continue
                            else:
                                d_h = [min_val.file_name, min_val.line_num,
                                        utc_y, utc_m, utc_d, utc_h - 1,
                                        min_val.year, month, day, hour - 1,
                                        min_val.val + ((self.curve[hour] + self.curve[hour - 1])/2.0 * val_range)]
                                self.demand_file.add_demand_hour(d_h)
                                dst = False
                        prev_utc_h = utc_h
                    except:
                        dst = True
                        continue
                    d_h = [min_val.file_name, min_val.line_num,
                            utc_y, utc_m, utc_d, utc_h,
                            min_val.year, month, day, hour,
                            min_val.val + (self.curve[hour] * val_range)]
                    self.demand_file.add_demand_hour(d_h)

    def print_demand_file(self):
        self.demand_file.write_demand_file()

def create_parser():
    parser = OptionParser(description="Support for Quebec Extracted data files.")
    parser.add_option('-i', '--minimum',
            dest = 'min_paths',
            action = 'append', type = 'string', default = [],
            help = 'Files for daily minumum measurement.',
            metavar = 'FILE')
    parser.add_option('-a', '--maximum',
            dest = 'max_paths',
            action = 'append', type = 'string', default = [],
            help = 'Files for daily maximum measurement.',
            metavar = 'FILE')
    parser.add_option('-c', '--curve',
            dest = 'curve_paths',
            action = 'append', type = 'string', default = [],
            help = 'Files for daily demand curve measurement.',
            metavar = 'FILE')
    parser.add_option('-y', '--year',
            dest = 'target_year',
            action = 'store', type = 'int', default = 2014,
            help = 'Target year for min/max calculation.',
            metavar = 'year')
    return parser

def main(argv = None):
    logging.basicConfig(level=logging.INFO)
    parser = create_parser()
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = parser.parse_args(argv)
    if len(argv) != 0:
        print('Must enter at least one file path!')
        print
        parser.print_help()
        return -1

    ssheet = PQSpreadsheetFiles(options.min_paths,
                                options.max_paths,
                                options.curve_paths,
                                options.target_year)
    ssheet.check_min_max()
    # ssheet.print_min_max()
    # ssheet.print_curve()
    ssheet.generate_demand_file()
    ssheet.print_demand_file()

if __name__ == '__main__':
    sys.exit(main())
