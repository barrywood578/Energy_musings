#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Support for the Alberta spreadsheet input.  

    Note that this spreadsheet has detailed information
    for each power generating station.
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

sys.path.append('../Common')
from common_defs import *
from demand_file import *

class AB_Spreadsheet_File(object):
    def __init__(self, file_paths = []):
        self.lines = []
        self.files = []
        self.demand_file = demand_file()

        for path in file_paths:
            try:
                self.check_file(path)
                self.read_and_parse_file(path)
                self.files.append(path)
                logging.warning("Parsed file %s" % path)
            except ValueError as e:
                if do_all_files:
                    continue
                print(e)
                sys.exit(-1)

    def check_file(self, file_path):
        if not os.path.isfile(file_path):
            raise ValueError("File '%s' does not exist!" % file_path)
        filename, file_extension = os.path.splitext(file_path)
        if EXCEL_FILE_EXTENSION != file_extension:
            raise ValueError("File '%s' wrong type, want '%s' but got %s!" %
                    (file_path, EXCEL_FILE_EXTENSION, file_extension))

    def read_excel(self, file_path):
        self.wb = load_workbook(filename = file_path)
        for sheet in self.wb:
            if sheet.title != self.wb.active.title:
                continue
            idx = 0
            for row in sheet.iter_rows(min_row = 1):
               vals = [c.value  for c in row]
               for i, val in enumerate(vals):
                   if val is None:
                       vals[i] = ''
                   try:
                       vals[i] = str(vals[i])
                   except UnicodeEncodeError:
                       vals[i].encode("ascii","ignore")
               line = SEPARATOR.join(vals)
               line_crlf = "%s%s%s\n" % (START_END, line, START_END)
               self.lines.append(line_crlf)
               idx += 1

    def _parse_date(self, line_num, token):
        month_abbrev = ["SKIP", "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                                "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        try:
            day = int(token[0:2])
            month = month_abbrev.index(token[2:5])
            year = int(token[5:9])
            hour = int(token[10:12])
        except ValueError as e:
            logging.critical("Could not parse line %d date '%s'.  Halting." % (line_num, token))
            exit()

        return year, month, day, hour

    def parse_lines(self, path):
        if self.lines is []:
            logging.error("%s is empty!" % path)
            return
        logging.info("\nFirst 5 lines\n%s\n" % self.lines[0:5])
        header = self.lines[0].strip()
        toks = [tok.strip() for tok in header[1:-1].split(SEPARATOR)]
        logging.info("\nHeader tokens %s\n" % toks)

        try:
            GMT_index = toks.index("Date_Begin_GMT")
            loc_index = toks.index("Date_Begin_Local")
            load_index = toks.index("ACTUAL_AIL")
        except ValueError as e:
            logging.critical("Could not find GMT, Local time, or AIL index.  Halting.")
            exit()

        for line_num, line in enumerate(self.lines[1:]):
            line = line.strip()
            toks = [tok.strip() for tok in line[1:-1].split(SEPARATOR)]
            try:
                GMT_year, GMT_month, GMT_day, GMT_hour = self._parse_date(line_num, toks[GMT_index])
                loc_year, loc_month, loc_day, loc_hour = self._parse_date(line_num, toks[loc_index])
                the_load = float(toks[load_index])
                new_tuple = [path, line_num,
                             GMT_year, GMT_month, GMT_day, GMT_hour,
                             loc_year, loc_month, loc_day, loc_hour, the_load]
                self.demand_file.add_demand_hour(new_tuple)
            except ValueError as e:
                logging.warning("Error processing %s Line %d:%s" %
                        (path, line_num, line))
                logging.warning(e)
                continue

    def read_and_parse_file(self, path):
        self.lines = []
        self.read_excel(path)
        self.parse_lines(path)

    def print_demand_file(self):
        self.demand_file.write_demand_file()

def create_parser():
    parser = OptionParser(description="Support for Alberta Hourly Load Detailed Excel file.")
    parser.add_option('-x', '--excel',
            dest = 'excel_file_paths',
            action = 'append', type = 'string', default = [],
            help = 'File path to Alberta format Excel file.',
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

    ssheet = AB_Spreadsheet_File(options.excel_file_paths)
    ssheet.print_demand_file()

if __name__ == '__main__':
    sys.exit(main())
