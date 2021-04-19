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
from demand_file import DemandFile
from generator_file import generator_file
from math import isnan, ceil

from common_defs import *

class grid(object):
    def __init__(self, demand_file_paths=[], generator_file_paths=[]):
        self.demand = DemandFile()
        for dem in demand_file_paths:
            self.demand.read_hourly_mw_file(dem)
        self.generator = generator_file()
        for gen in generator_file_paths:
            self.generator.read_generator_file(gen)

    def create_base(self, start_utc, end_utc):
        interval = end_utc - start_utc
        logging.debug("Creating data for %s, %s" % (start_utc.strftime(DATE_FORMAT), str(interval)))
        self.demand.create_base(start_utc, interval)
        self.generator.create_base(start_utc, interval)

    def run(self, start_utc, end_utc):
        req_MWh = 0.0
        gen_MWh = 0.0
        ghg = 0.0
        f_ghg = 0.0
        hours = 0
        brown_hours = 0
        brown_diff = 0.0
        interval = end_utc - start_utc 
        hours = interval.days * 24 + ceil(interval.seconds / 3600) + 1
        logging.info("Run from %s to %s.  %d hours." % ( start_utc.strftime(DATE_FORMAT),
                                                  end_utc.strftime(DATE_FORMAT),
                                                  hours))
        while start_utc < end_utc:
            capacity = self.generator.get_total_capacity(start_utc)
            load = self.demand.get_mw_hour(start_utc)
            if isnan(load):
                raise ValueError("No load for UTC %s" % start_utc.strftime(DATE_FORMAT))
            req_MWh += load
            if (load > capacity):
                brown_hours += 1
                brown_diff = max(brown_diff, load - capacity)
                load = capacity
                
            gen_ghg, foss_ghg, gen_db = self.generator.get_ghg_emissions(load, start_utc)
            gen_MWh += load
            ghg += gen_ghg
            f_ghg += foss_ghg
            if isnan(ghg):
                raise ValueError("%s GHG is NaN" % start_utc.strftime(DATE_FORMAT))
            op = start_utc.strftime(DATE_FORMAT)
            op += " %10.2f" % load
            for fuel in gen_db.keys():
                op = op + (" %s %f Mw %f GHG" % (fuel, gen_db[fuel][0], gen_db[fuel][1]))
            print(op)

            start_utc += timedelta(hours=1)
        return req_MWh, gen_MWh, ghg, f_ghg, hours, brown_hours, brown_diff

def create_parser():
    parser = OptionParser(description="Grid support.")
    parser.add_option('-d', '--demand',
            dest = 'demand_path',
            action = 'append', type = 'string', default = [],
            help = 'File path to demand file.',
            metavar = 'FILE')
    parser.add_option('-g', '--generator',
            dest = 'generator_path',
            action = 'append', type = 'string', default = [],
            help = 'File path to generator file.',
            metavar = 'FILE')
    parser.add_option('-m', '--module',
            dest = 'module_path',
            action = 'append', type = 'string', default = [],
            help = 'Directory containing load and generator files.',
            metavar = 'DIR')
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
    for path in options.module_path:
        if not os.path.isdir(path):
            raise ValueError("Module %s directory not found." % path)
        path = os.path.abspath(path)
        fnames = [FILE_LOAD_DB, FILE_GEN_DB]
        options_f = [options.demand_path, options.generator_path]
        for fname, option in zip(fnames, options_f):
            f_path = os.path.join(path, fname)
            if os.path.isfile(f_path):
                logging.debug("Found file %s" % f_path)
                option.append(f_path)

    if options.demand_path == [] or options.generator_path == []:
        raise ValueError("Must enter at least one demand and generator file.")

    for path in options.demand_path:
        if not os.path.isfile(path):
            raise ValueError("Demand file '%s' not found." % path)

    for path in options.generator_path:
        if not os.path.isfile(path):
            raise ValueError("Generator file '%s' not found." % path)

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
    logging.basicConfig(level=logging.INFO)

    parser = create_parser()
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = parser.parse_args(argv)
    start, end = check_options(options)

    logging.info("Loading Files...")
    the_grid = grid(options.demand_path, options.generator_path)
    logging.info("Creating load/generation baseline...")
    the_grid.create_base(start,end)
    req_MWh, gen_MWh, ghg, f_ghg, hours, brown_hours, brown_diff = the_grid.run(start, end)
    logging.info("Demand is %10.2f TWh" % (req_MWh/1000000))
    logging.info("Generated %10.2f TWh, %10.2f MT CO2 fossil fuel emissions." %
            (gen_MWh/1000000, f_ghg/1E9))
    logging.info("                          %10.2f MT CO2 total emissions." % (ghg/1E9))
    # If the maximum difference between load and supply is 10 kW,
    # fuggetaboutit...
    if ((brown_hours != 0) and (brown_diff > 0.01)):
        logging.info("Demand exceeded supply for %d hours out of %d." % (brown_hours, hours))
        logging.info("Maximum deficiency was %f MW." % brown_diff)

if __name__ == '__main__':
    sys.exit(main())
