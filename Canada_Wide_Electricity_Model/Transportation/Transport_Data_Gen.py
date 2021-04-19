#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Generation of load and power generation for transportation electrification.
"""

from optparse import OptionParser
from collections import OrderedDict
import operator
import sys
import os
import logging
import pytz
from datetime import datetime, timezone, timedelta

curdir = os.path.dirname(os.path.abspath(__file__))
if curdir not in sys.path:
    sys.path.append(curdir)
comdir = os.path.join(os.path.split(curdir)[0], "Common")
if comdir not in sys.path:
    sys.path.append(comdir)

from common_defs import *
from demand_file import DemandFile
from generator_file import generator_file, generator
from hourly_mw_file import HourlyMWFile

class TransportationData(object):
    # Timezone, population 2020, population 2043, from:
    # https://www.statista.com/statistics/481509/canada-population-projection-by-province/

    tz_pop = {"British_Columbia" :
                               ["America/Vancouver" ,5103.5, 6224.4],
              "Alberta"      : ["America/Edmonton" ,4472.8, 6619.2],
              "Saskatechwan" : ["America/Regina" ,1195.1, 1591.2],
              "Manitoba"     : ["America/Winnipeg" ,1381.9, 1741.4],
              "Ontario"      : ["America/Toronto"  ,14677.9, 18263.2],
              "Quebec"       : ["America/Montreal" ,8494.5, 9472.4],
              "New_Brunswich": ["America/Moncton", 775.6, 794],
              "Nova_Scotia"  : ["America/Halifax", 967.1, 993.8],
              "Prince_Edward_Island":
                               ["America/Halifax", 157.4, 197.4],
              "Newfoundland_and_Labradour" :
                               ["America/St_Johns", 522.3, 458.6]
            }
    def __init__(self, year=2020, local_start_hour = 22, charge_hours = 8):
        self.demand_file = DemandFile()
        self.gen_file = generator_file(file_path = "../Common/gen_db_GHG.txt")
        self.demand_file_path = None
        self.year = year
        self.local_start_hour = local_start_hour
        self.charge_hours = charge_hours
        self.gen_file_path = None
        self.tot_pop_2020 = sum(self.tz_pop[k][1] for k in self.tz_pop.keys())
        self.tot_pop_2043 = sum(self.tz_pop[k][2] for k in self.tz_pop.keys())
        self.yearly_pop_delta = (self.tot_pop_2043 - self.tot_pop_2020) / (2043.0-2020) 
        self.tot_pop_year = self.tot_pop_2020 + ((year - 2020.0) * self.yearly_pop_delta)
        self.hour_pct_load = [0.0] * 24
        for province in self.tz_pop.keys():
            dt = datetime(2020,1,1,hour=local_start_hour)
            tz = pytz.timezone(self.tz_pop[province][0])
            offset = tz.utcoffset(dt)
            utc = dt - offset
            prov_pop_delta = (self.tz_pop[province][2] - self.tz_pop[province][1]) / (2043.0 - 2020.0)
            prov_pop_year = self.tz_pop[province][1] + ((year - 2020.0) * prov_pop_delta)
            pct = prov_pop_year / self.tot_pop_year 
            for hour in range(utc.hour, utc.hour + charge_hours):
                h = hour % 24
                self.hour_pct_load[h] += pct
        print("Hour percentage load:")
        for h, pct in enumerate(self.hour_pct_load):
            print ("%d %f" % (h, pct))

    def create_demand_file(self, petajoules = 602.0):
        petajoules_per_day = petajoules / 365.0
        print("Petajoules_per_day %f" % petajoules_per_day)
        self.gen_GW = (petajoules_per_day * 1.0E9) / self.charge_hours / 3600.0
        print("Gen MW is %f" % self.gen_GW)
        dt = datetime(self.year, 1, 1, hour = 0)
        # Account for leap years...
        end_dt = datetime(self.year + 1, 1, 1, hour = 0)
        hours = (end_dt - dt).total_seconds() / 3600
        # Note that 2020 is a leap year with 366 days
        for hour in range (0, int(hours)):
            timenow = dt + timedelta(hours = hour)
            toks = ["Generated", hour,
                    timenow.year, timenow.month, timenow.day, timenow.hour,
                    timenow.year, timenow.month, timenow.day, timenow.hour,
                    self.hour_pct_load[timenow.hour % 24] * self.gen_GW]
            self.demand_file.add_mw_hour("Generated", hour, toks)

    def create_gen_file(self, fuel_type):
        self.gen_file.gen_db[fuel_type].mw = self.gen_GW

    def write_demand_file(self, demand_file_path = ""):
        self.demand_file.write_hourly_mw_file(demand_file_path)

    def write_gen_file(self, gen_path = ""):
        self.gen_file.write_generator_file(filepath=gen_path)

def create_parser():
    parser = OptionParser(description="Support for Alberta Hourly Load Detailed Excel file.")
    parser.add_option('-y', '--year',
            dest = 'year',
            action = 'store', type = 'int', default = 2020,
            help = 'Year of generated data.',
            metavar = 'year')
    parser.add_option('-s', '--start_hour',
            dest = 'start_hour',
            action = 'store', type = 'int', default = 22,
            help = 'Default starting hour for vehicle charging.',
            metavar = 'hour')
    parser.add_option('-c', '--charging_hours',
            dest = 'charging_hours',
            action = 'store', type = 'int', default = 8,
            help = 'Number of hours to charge vehicles.',
            metavar = 'interval')
    parser.add_option('-e', '--energy_petajoules',
            dest = 'petajoules',
            action = 'store', type = 'int', default = 602.7526882,
            help = 'Total amount of energy required to charge vehicles.',
            metavar = 'energy')
    parser.add_option('-f', '--fuel_type',
            dest = 'fuel_type',
            action = 'store', type = 'string', default = "NUCLEAR",
            help = 'Fuel type used to charge vehicles.',
            metavar = 'Fuel')
    parser.add_option('-g', '--gen_file',
            dest = 'gen_file_path',
            action = 'store', type = 'string', default = "",
            help = 'Path to generator file to be written.',
            metavar = 'FILE')
    parser.add_option('-d', '--demand_file',
            dest = 'demand_file_path',
            action = 'store', type = 'string', default = "",
            help = 'Path to demand file to be written.',
            metavar = 'FILE')
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

    trans = TransportationData(year=options.year,
                               local_start_hour=options.start_hour,
                               charge_hours=options.charging_hours)
    trans.create_demand_file(options.petajoules)
    trans.create_gen_file(options.fuel_type)

    trans.write_demand_file(options.demand_file_path)
    trans.write_gen_file(options.gen_file_path)

if __name__ == '__main__':
    sys.exit(main())
