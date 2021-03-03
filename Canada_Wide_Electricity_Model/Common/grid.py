#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Runs a grid, which consists:
    - A load file
    - A generator file

"""

from optparse import OptionParser
from collections import OrderedDict
import operator
import sys
import os
import logging
from datetime import datetime, timezone, timedelta
from demand_file import demand_file
from generator_file import generator_file
from hourly_mw_file import HourlyMWFile
from math import isnan, ceil

from common_defs import *

class grid(object):
    def __init__(self, demand_file_path="", generator_file_path="",
                       pv_path="", wind_path=""):
        self.demand = demand_file(demand_file_path)
        self.generator = generator_file(generator_file_path)
        self.pv_gen = None
        self.wind_gen = None
        if not pv_path == "":
            self.pv_gen = HourlyMWFile(pv_path)
        if not wind_path == "":
            self.wind_gen = HourlyMWFile(wind_path)

    def run(self, start_utc, end_utc):
        req_MWh = 0.0
        gen_MWh = 0.0
        ghg = 0.0
        hours = 0
        brown_hours = 0
        capacity = self.generator.get_total_capacity("NoDate")
        interval = end_utc - start_utc 
        hours = interval.days * 24 + ceil(interval.seconds / 3600) + 1
        print("Run from %s to %s.  %d hours." % ( start_utc.strftime(DATE_FORMAT),
                                                  end_utc.strftime(DATE_FORMAT),
                                                  hours))
        while start_utc < end_utc:
            load = self.demand.get_demand(start_utc)
            if isnan(load):
                raise ValueError("No load for UTC %s" % start_utc.strftime(DATE_FORMAT))
            req_MWh += load
            if (load > capacity):
                load = capacity
                brown_hours += 1
            gen_MWh += load
            ghg += self.generator.get_ghg_emissions(load)
            start_utc += timedelta(hours=1)
        return req_MWh, gen_MWh, ghg, hours, brown_hours

def create_parser():
    parser = OptionParser(description="Grid support.")
    parser.add_option('-d', '--demand',
            dest = 'demand_path',
            action = 'store', type = 'string', default = "",
            help = 'File path to demand file.',
            metavar = 'FILE')
    parser.add_option('-g', '--generator',
            dest = 'generator_path',
            action = 'store', type = 'string', default = "",
            help = 'File path to generator file.',
            metavar = 'FILE')
    parser.add_option('-p', '--pv',
            dest = 'pv_path',
            action = 'store', type = 'string', default = "",
            help = 'File path to PV solar generation file. May or may not be present.',
            metavar = 'FILE')
    parser.add_option('-w', '--wind',
            dest = 'wind_path',
            action = 'store', type = 'string', default = "",
            help = 'File path to wind generation file. May or may not be present.',
            metavar = 'FILE')
    parser.add_option('-s', '--start',
            dest = 'start_date',
            action = 'store', type = 'string', default = "",
            help = 'UTC start date for run, YYYY-MM-DD hh:mm',
            metavar = 'YYY-MM-DD hh:mm')
    parser.add_option('-e', '--end',
            dest = 'end_date',
            action = 'store', type = 'string', default = "",
            help = 'UTC end date for run, YYYY-MM-DD hh:mm',
            metavar = 'YYY-MM-DD hh:mm')
    return parser

def check_options(options):
    if not os.path.isfile(options.demand_path):
        raise ValueError("Demand file '%s' not found." % options.demand_path)

    if not os.path.isfile(options.generator_path):
        raise ValueError("Generator file '%s' not found." % options.generator_path)

    if not options.pv_path == "":
        if not os.path.isfile(options.pv_path):
            raise ValueError("PV Solar file '%s' not found." % options.pv_path)

    if not options.wind_path == "":
        if not os.path.isfile(options.wind_path):
            raise ValueError("Wind file '%s' not found." % options.wind_path)

    try:
        start_date = datetime.strptime(options.start_date, DATE_FORMAT) 
    except:
        raise ValueError("Start should be YYYY-MM-DD hh:mm not '%s'" % options.start_date)

    try:
        end_date = datetime.strptime(options.end_date, DATE_FORMAT)
    except:
        raise ValueError("Start should be YYYY-MM-DD hh:mm not '%s'" % options.end_date)

    return start_date, end_date

def main(argv = None):
    logging.basicConfig(level=logging.DEBUG)

    parser = create_parser()
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = parser.parse_args(argv)
    start, end = check_options(options)

    logging.info("Loading Files...")
    the_grid = grid(options.demand_path, options.generator_path, options.pv_path, options.wind_path)
    logging.info("Running Files...")
    req_MWh, gen_MWh, ghg, hours, brown_hours = the_grid.run(start, end)
    logging.info("Demand is %10.2f GWh" % (req_MWh/1000))
    logging.info("Generated %10.2f GWh, %10.2f MT CO2 equivalent emissions." %
            (gen_MWh/1000, ghg/1000000))
    if (brown_hours != 0):
        logging.info("Demand exceeded supply for %d hours out of %d." % (brown_hours, hours))

if __name__ == '__main__':
    sys.exit(main())
