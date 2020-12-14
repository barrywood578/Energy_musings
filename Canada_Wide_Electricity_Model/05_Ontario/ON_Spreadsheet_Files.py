#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Support for Ontario Hydro Public Demand reports, 2015-2019
"""

from optparse import OptionParser
from collections import OrderedDict
import operator
import re
import sys
import os
import logging
from datetime import datetime, timezone, timedelta
import pytz

sys.path.append('../Common')
from common_defs import *
from demand_file import *

class minmax(object):
    def __init__(self, time_id="No Time", demand="No Demand"):
        if (demand == "No Demand") or (time_id == "No Time"):
            self.min_demand = 100000
            self.min_demand_time_id = 'No Time'
            self.max_demand = 0;
            self.max_demand_time_id = 'No Time'
            return

        self.min_demand = self.max_demand = float(demand)
        self.min_demand_time_id = self.max_demand_time_id = time_id

    def update(self, time_id, demand):
        if self.min_demand > demand:
            self.min_demand = demand
            self.min_demand_time_id = time_id
        if self.max_demand < demand:
            self.max_demand = demand
            self.max_demand_time_id = time_id

class minmax_list(object):
    def __init__(self):
        self.list = {}
        self.demand_mm = minmax()
        self.ont_demand_mm = minmax()

    def add_demand(self, time_key, time_ids, demand_in, ont_demand_in):
        time_id = time_ids[0]

        if (time_id not in self.list):
            self.list.update({time_id:minmax_list()})
        self.demand_mm.update(time_key, demand_in)
        self.ont_demand_mm.update(time_key, ont_demand_in)
        if len(time_ids) > 1:
            self.list[time_id].add_demand(time_key, time_ids[1:], demand_in, ont_demand_in)
        else:
            self.list[time_id].demand_mm.update(time_key, demand_in)
            self.list[time_id].ont_demand_mm.update(time_key, ont_demand_in)

class ONSpreadsheetFiles(object):
    MINMAX = "MinMax"
    def __init__(self, file_paths=[], all_csv_files=False):
        self.files = []
        self.analysis_db = minmax_list()
        self.demand_file = demand_file()
        self.dst = False

        if all_csv_files:
            file_paths = []
            file_list = [f for f in os.listdir('.') if os.path.isfile(f)]
            for each_file in file_list:
                filename, file_extension = os.path.splitext(each_file)
                if file_extension == CSV_FILE_EXTENSION:
                    file_paths.append(each_file)

        for path in file_paths:
            try:
                self.check_file(path)
                self._read_and_parse_file(path)
                self.files.append(path)
                logging.warning("Parsed file %s" % path)
            except ValueError as e:
                if all_csv_files:
                    logging.critical("Failed parsing file %s" % path)
                    continue
                print(e)
                sys.exit(-1)

    def check_file(self, file_path):
        if not os.path.isfile(file_path):
            raise ValueError("File '%s' does not exist!" % file_path)
        filename, file_extension = os.path.splitext(file_path)
        if CSV_FILE_EXTENSION != file_extension:
            raise ValueError("File '%s' wrong type, want '%s' but got %s!" %
                    (file_path, CSV_FILE_EXTENSION, file_extension))

    def _extract_year(self, file_name):
        toks = [tok.strip() for tok in file_name.split('_')]

        year = 'Not Found'
        for tok in toks:
            try:
                year_int = int(tok)
                if ((year_int > 2010) and (year_int < 2030)):
                    year = tok
                    break
            except:
                continue
        return year

    def add_analysis(self, year, month, day, hour, demand, ont_demand):
        time_ids = [str(x) for x in [year, month, day, hour]]
        time_key = KEY_SEPARATOR.join(time_ids)

        self.analysis_db.add_demand(time_key, time_ids[1:], demand, ont_demand)

    def _read_and_parse_file(self, path):
        logging.info("Processing file '%s'." % path)

        file_year = self._extract_year(path)
        if file_year == 'Not Found':
            raise ValueError("Invalid Public Demand file name format, no year found: %s" % path)
        file_year = int(file_year)

        with open(path, 'r') as demand_file:
            lines = [line.strip() for line in demand_file.readlines()]

        dst = False
        prev_utc_hour = -1
        for line_num, line in enumerate(lines):
            ## Skip comments at start of file
            if not line[0] == '2':
                continue
            toks = [tok.strip() for tok in line.split(',')]
            if not len(toks) == 4:
                raise ValueError("File %s line %d tokens %d needed 4." %
                                  (path, line_num, len(toks)))
            year, month, day = [int(tok.strip()) for tok in toks[0].split('-')]
            hour = int(toks[1])
            if not dst:
                hour -= 1
            mkt_demand = float(toks[2])
            ont_demand = float(toks[3])
            if not year == file_year:
                raise ValueError("File %s line %d Year %d Expected %d" %
                                  (path, line_num, year, file_year))

            ## Jiggery pokery to deal with Daylight Savings Time (DST) start and end
            utc_year, utc_month, utc_day, utc_hour, year, month, day, hour = self._get_ON_UTC(year, month, day, hour, dst)
            if utc_hour == prev_utc_hour:
                dst = True
                hour += 1
                utc_year, utc_month, utc_day, utc_hour, year, month, day, hour = self._get_ON_UTC(year, month, day, hour, dst)

            if (utc_hour - prev_utc_hour) == 2:
                dst = False
                hour -= 1
                utc_year, utc_month, utc_day, utc_hour, year, month, day, hour = self._get_ON_UTC(year, month, day, hour, dst)

            prev_utc_hour = utc_hour
            self.demand_file.add_demand_hour([path, line_num,
                      utc_year, utc_month, utc_day, utc_hour,
                          year,     month,     day,     hour, ont_demand])
            self.add_analysis(utc_year, utc_month, utc_day, utc_hour, mkt_demand, ont_demand)

    def _get_ON_UTC(self, year, month, day, hour_in, dst_in=False):
        year_out = year
        month_out = month
        day_out = day
        hour_out = hour_in
        if (hour_in > 23):
            hour_out -= 24
            naive = datetime(year, month, day, hour_in - 24)
            naive += timedelta(days=1)
            year_out = naive.year
            month_out = naive.month
            day_out = naive.day
        else:
            naive = datetime(year, month, day, hour=hour_in)
        local = pytz.timezone("America/Toronto")
        local_dt = local.localize(naive, is_dst=dst_in)
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, year_out, month_out, day_out, hour_out

    def print_hourly_min_max(self):
        if self.analysis_db == {}:
            print("Nothing in analysis.")
            return

        print("Month,Day,Hour,Min Demand,Min Demand Time,Max Demand,Max Demand Time,Min Ont Demand,Min Ont Demand Time,Max Ont Demand,Max Ont Demand Time")

        for month in self.analysis_db.list.keys():
            for day in self.analysis_db.list[month].list.keys():
                for hour in self.analysis_db.list[month].list[day].list.keys():
                    print(",".join([month, day, hour,
                             str(self.analysis_db.list[month].list[day].list[hour].demand_mm.min_demand),
                             str(self.analysis_db.list[month].list[day].list[hour].demand_mm.min_demand_time_id),
                             str(self.analysis_db.list[month].list[day].list[hour].demand_mm.max_demand),
                             str(self.analysis_db.list[month].list[day].list[hour].demand_mm.max_demand_time_id),
                             str(self.analysis_db.list[month].list[day].list[hour].ont_demand_mm.min_demand),
                             str(self.analysis_db.list[month].list[day].list[hour].ont_demand_mm.min_demand_time_id),
                             str(self.analysis_db.list[month].list[day].list[hour].ont_demand_mm.max_demand),
                             str(self.analysis_db.list[month].list[day].list[hour].ont_demand_mm.max_demand_time_id)]))

    def print_daily_min_max(self):
        if self.analysis_db == {}:
            print("Nothing in analysis.")
            return

        print("Month,Day,Min Demand,Min Demand Time,Max Demand,Max Demand Time,Min Ont Demand,Min Ont Demand Time,Max Ont Demand,Max Ont Demand Time")
        for month in self.analysis_db.list.keys():
            for day in self.analysis_db.list[month].list.keys():
                print(",".join([month, day,
                         str(self.analysis_db.list[month].list[day].demand_mm.min_demand),
                         str(self.analysis_db.list[month].list[day].demand_mm.min_demand_time_id),
                         str(self.analysis_db.list[month].list[day].demand_mm.max_demand),
                         str(self.analysis_db.list[month].list[day].demand_mm.max_demand_time_id),
                         str(self.analysis_db.list[month].list[day].ont_demand_mm.min_demand),
                         str(self.analysis_db.list[month].list[day].ont_demand_mm.min_demand_time_id),
                         str(self.analysis_db.list[month].list[day].ont_demand_mm.max_demand),
                         str(self.analysis_db.list[month].list[day].ont_demand_mm.max_demand_time_id)]))

    def print_monthly_min_max(self):
        if self.analysis_db == {}:
            print("Nothing in analysis.")
            return

        print("Month,Min Demand,Min Demand Time,Max Demand,Max Demand Time,Min Ont Demand,Min Ont Demand Time,Max Ont Demand,Max Ont Demand Time")
        for month in self.analysis_db.list.keys():
            print(",".join([month,
                     str(self.analysis_db.list[month].demand_mm.min_demand),
                     str(self.analysis_db.list[month].demand_mm.min_demand_time_id),
                     str(self.analysis_db.list[month].demand_mm.max_demand),
                     str(self.analysis_db.list[month].demand_mm.max_demand_time_id),
                     str(self.analysis_db.list[month].ont_demand_mm.min_demand),
                     str(self.analysis_db.list[month].ont_demand_mm.min_demand_time_id),
                     str(self.analysis_db.list[month].ont_demand_mm.max_demand),
                     str(self.analysis_db.list[month].ont_demand_mm.max_demand_time_id)]))

    def print_min_max(self):
        self.print_hourly_min_max()
        self.print_daily_min_max()
        self.print_monthly_min_max()

def create_parser():
    parser = OptionParser(description="Load and analyze public demand report.")
    parser.add_option('-f', '--file',
            dest = 'file_names',
            action = 'append', type = 'string', default = [],
            help = 'Public demand file(s) published by Ontario Hydro',
            metavar = 'FILE')
    parser.add_option('-a', '--all',
        dest = 'all_csv_files',
        action = 'store_true', default = False,
        help = 'Process all .csv files in this directory.',
        metavar = 'FLAG')
    parser.add_option('-d', '--demand',
        dest = 'print_demand',
        action = 'store_true', default = False,
        help = 'Print demand file.',
        metavar = 'FLAG')
    parser.add_option('-m', '--min_max',
        dest = 'print_min_max',
        action = 'store_true', default = False,
        help = 'Print analysis file.',
        metavar = 'FLAG')

    return parser

def validate_options(options):
    if not len(options.file_names) and not options.all_csv_files:
        raise ValueError("Must enter at least one filename.")

    for file_name in options.file_names:
        if not os.path.isfile(file_name):
            raise ValueError("Public demand report file '%s' does not exist." % file_name)

def main(argv = None):
    logging.basicConfig(level=logging.WARN)
    parser = create_parser()
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = parser.parse_args(argv)
    if len(argv) != 0:
        print('Invalid argument!')
        print
        parser.print_help()
        return -1

    try:
        validate_options(options)
    except ValueError as e:
        print(e)
        sys.exit(-1)

    Ontario = ONSpreadsheetFiles(options.file_names, options.all_csv_files)

    if (options.print_demand):
        Ontario.demand_file.write_demand_file()

    if (options.print_min_max):
        Ontario.print_min_max()

if __name__ == '__main__':
    sys.exit(main())
