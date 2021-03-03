#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Support for the common "demand profile" file format.

    Each file line contains:
    Source file, line number,
    Universal Coordinated Time (UCT) Year, Month, Day, Hour
    Local Year, Month, Day, Hour
    Load in megawatts (MW), to one decimal place.

"""

from optparse import OptionParser
from collections import OrderedDict
import operator
import sys
import os
import logging
import copy
from datetime import datetime, timezone, timedelta
from math import ceil
from common_defs import *
from adjust_data import AdjustData
from hourly_mw_file import HourlyMWFile

class DemandFile(HourlyMWFile):

    def __init__(self, file_path = ""):
        super(DemandFile, self).__init__()
        file_header_prefix = "File, LineNum, "
        self.file_header = file_header_prefix + self.file_header
        self.token_count += len(file_header_prefix.split(", ")) - 1

        if (file_path == ""):
            return
        self.read_hourly_mw_file(file_path)

def create_parser():
    parser = OptionParser(description="Demand file support.")
    parser.add_option('-d', '--demand',
            dest = 'demand_file_paths',
            action = 'store', type = 'string', default = "",
            help = 'File path to demand file.',
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

    demand = DemandFile(options.demand_file_paths)
    demand.write_hourly_mw_file()

if __name__ == '__main__':
    sys.exit(main())
