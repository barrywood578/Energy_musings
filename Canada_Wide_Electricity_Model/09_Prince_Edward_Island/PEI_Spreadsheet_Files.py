#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Support for Prince Edward Island Comma Separated Values files.

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
from datetime import datetime, timezone, timedelta
import pytz

sys.path.append('../Common')
from common_defs import *
from demand_file import *
from hourly_mw_file import HourlyMWFile

class date_n_val(object):
    def __init__(self, the_date, the_val):
        date_obj = datetime.strptime(the_date, "%Y/%m/%d %H:%M")
        self.year = date_obj.year
        self.month = date_obj.month
        self.day = date_obj.day
        self.hour = date_obj.hour
        self.minute = date_obj.minute
        self.val = float(the_val)

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
            val = date_n_val(toks[0], toks[1])
            if val.year != self.year:
                continue
            if val.month not in self.months:
                self.months[val.month] = {}
            if val.day not in self.months[val.month]:
                self.months[val.month][val.day] = {}
            if val.hour not in self.months[val.month][val.day]:
                self.months[val.month][val.day][val.hour] = {}
            if val.minute not in self.months[val.month][val.day][val.hour]:
                self.months[val.month][val.day][val.hour][val.minute] = []
            self.months[val.month][val.day][val.hour][val.minute].append(
                                                              [file_path, line_num, val.val])

    def extract_values(self):
        for month in sorted(self.months.keys()):
            for day in sorted(self.months[month].keys()):
                for hour in sorted(self.months[month][day].keys()):
                    minutes = sorted(self.months[month][day][hour].keys())
                    max_start = max(self.months[month][day][hour][minutes[0]],
                                    key = lambda t: t[2])
                    min_start = min(self.months[month][day][hour][minutes[0]],
                                    key = lambda t: t[2])
                    max_end = max(self.months[month][day][hour][minutes[-1]],
                                    key = lambda t: t[2])
                    min_end = min(self.months[month][day][hour][minutes[-1]],
                                    key = lambda t: t[2])

                    ## Based on trend, pick a value:
                    ## If the trend is up, pick the maximum
                    ## If the trend is down, pick a minimum
                    ## If there is no clear trend, average
                    pick = "Average"
                    if (max_end[2] > max_start[2]) and (min_end[2] > min_start[2]):
                        pick = "Maximum"
                    elif (max_start[2] > max_end[2]) and (min_start[2] > min_end[2]):
                        pick = "Minimum"

                    all_vals = []
                    for minute in minutes:
                        all_vals.extend(self.months[month][day][hour][minute])

                    if pick == "Minimum":
                        self.months[month][day][hour] = min(all_vals, key = lambda t: t[2])
                    elif pick == "Minimum":
                        self.months[month][day][hour] = max(all_vals, key = lambda t: t[2])
                    else:
                        path_line_value = all_vals[0]
                        path_line_value[2]= sum(val[2] for val in all_vals) / len(all_vals)
                        self.months[month][day][hour] = path_line_value

    def check_dates(self):
        all_dates_present = True
        first_date = datetime(self.year, 1, 1, 0, 0, 0, 0)

        while (first_date.year == self.year):
            if first_date.month in self.months.keys():
                if first_date.day in self.months[first_date.month].keys():
                    if first_date.hour not in self.months[first_date.month][first_date.day]:
                        logging.error("Month %d Day %d Hour %d not present." %
                                     (first_date.month, first_date.day, first_date.hour))
                        all_dates_preset = False;
                    first_date = first_date + timedelta(hours = 1)
                else:
                    logging.error("Month %d Day %d not present." %
                                 (first_date.month, first_date.day))
                    all_dates_preset = False;
                    first_date = first_date + timedelta(days = 1)
            else:
                logging.error("Month %d not present." % first_date.month)
                all_dates_preset = False;
                if first_date.month == 12:
                    return all_dates_present
                first_date = first_date.replace(month=first_date.month + 1,
                                                day = 1, hour = 0)
        return all_dates_present

    def print_vals(self):
        for month in sorted(self.months.keys()):
            for day in sorted(self.months[month].keys()):
                for hour in sorted(self.months[month][day].keys()):
                    print("M %d D %d H %d Val %s" %
                         (month, day, hour, self.months[month][day][hour]))

class PEISpreadsheetFiles(object):
    def __init__(self, paths = [], demand =True, target_year = 2020):
        self.vals = date_val_list(target_year)
        self.target_year = target_year
        self.demand = demand
        if self.demand:
            self.demand_file = demand_file()
        else:
            self.demand_file = HourlyMWFile()
        self.files = []

        self.read_val_files(paths, self.vals)
        self.vals.extract_values()
        self.files = sorted(paths)

    def read_val_files(self, file_paths, date_val):
        for path in file_paths:
            try:
                self.check_file(path, CSV_FILE_EXTENSION)
                date_val.read_values(path)
                logging.warning("Parsed .csv file %s" % path)
            except ValueError as e:
                print(e)
                sys.exit(-1)

    def check_file(self, file_path, extension):
        if not os.path.isfile(file_path):
            raise ValueError("File '%s' does not exist!" % file_path)
        filename, file_extension = os.path.splitext(file_path)
        if extension != file_extension:
            raise ValueError("File '%s' wrong type, want '%s' but got %s!" %
                    (file_path, EXCEL_FILE_EXTENSION, file_extension))

    ## Note: create_demand_file assumes a full year of data, starting with
    ## January 1 at midnight local time.
    def create_demand_file(self):
        local = pytz.timezone("America/Halifax")
        naive = datetime(self.target_year, 1, 1, hour=0)
        local_dt = local.localize(naive, False)
        utc_dt = local_dt.astimezone(pytz.utc)

        for month in sorted(self.vals.months.keys()):
            for day in sorted(self.vals.months[month].keys()):
                for hour in sorted(self.vals.months[month][day].keys()):
                    path, line, load = self.vals.months[month][day][hour]
                    if load < 0.0:
                        load = 0.0
                    if self.demand:
                        self.demand_file.add_demand_hour([path, line,
                                   utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour,
                                   self.target_year, month, day, hour, load])
                    else:
                        self.demand_file.add_mw_hour(path, line,
                          [utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour,
                           self.target_year, month, day, hour, load])
                    utc_dt = utc_dt + timedelta(hours = 1)

    def print_demand_file(self):
        if self.demand:
            self.demand_file.write_demand_file()
        else:
            self.demand_file.write_hourly_mw_file()

def create_parser():
    parser = OptionParser(description="Support for Prince Edward Island Hourly Load CSV files.")
    parser.add_option('-c', '--csv',
            dest = 'csv_files',
            action = 'append', type = 'string', default = [],
            help = 'Files for daily load measurement.',
            metavar = 'FILE')
    parser.add_option('-y', '--year',
            dest = 'target_year',
            action = 'store', type = 'int', default = 2020,
            help = 'Target year for daily load calculation.',
            metavar = 'year')
    parser.add_option('-n', '--not_demand',
            dest = 'demand',
            action = 'store_false', default = True,
            help = 'Output a demand file or an hourly mw file.',
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

    ssheet = PEISpreadsheetFiles(options.csv_files,
                                options.demand,
                                options.target_year)
    ## ssheet.vals.check_dates()
    ## ssheet.vals.print_vals()
    ssheet.create_demand_file()
    ssheet.print_demand_file()

if __name__ == '__main__':
    sys.exit(main())
