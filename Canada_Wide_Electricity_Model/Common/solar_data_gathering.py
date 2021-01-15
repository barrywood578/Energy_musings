#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Query NREL PVWatts web interface for the solar generation
    capacity at a particular location.

"""

from optparse import OptionParser
from collections import OrderedDict
import operator
import sys
from datetime import datetime, timedelta
import logging
import xml.etree.ElementTree as ET
import urllib3
import pv_solar_file
from common_defs import *

class SolarGeneration(object):
    BAD_LAT_LON = -181
    API = 'https://developer.nrel.gov/api/pvwatts/v6.xml?'
    # A personal key for accessing the PVWatts interface.
    # If no key is supplied, "DEMO_KEY" is used.  The DEMO_KEY
    # allows a much lower query rate.
    KEY = 'api_key='
    # Nameplate capacity in kilowatts
    CAPACITY = '&system_capacity='
    # Location may be specified as either latitude/longitude, or and address.
    # Latitued and longitude must be integers.  Address can be anything that
    # Google Maps can understand.
    LAT = '&lat='
    LON = '&lon='
    ADDRESS = '&address='
    # ARRAY_TYPE:
    #0 	Fixed - Open Rack
    #1 	Fixed - Roof Mounted
    #2 	1-Axis
    #3 	1-Axis Backtracking (eliminates inter-array shading)
    #4 	2-Axis
    ARRAY_TYPE = '&array_type=3'
    TILT = '&tilt='
    # Either 0 (southern hemisphere) or 180 (Northern Hemisphere)
    AZIMUTH = '&azimuth=180'
    # Percentage of power losses in the system
    LOSSES = '&losses=10'
    # Module type:
    # 0 - Standard, 14-17% conversion efficiency
    # 1 - Premium, 18-20% conversion efficiency
    # 2 - Thin film, 11% conversion efficiency
    MOD_TYPE = '&module_type=2'
    # Weather data:
    # nsrdb: NREL Physical Solar Model (PSM) Typical Meteorological Year
    # tmy2 : TMY2 station data
    # tmy3 : TMY3 station data
    # intl : International station data
    DATASET = '&dataset=nsrdb'
    HOURLY_TIMEFRAME = '&timeframe=hourly'
    MONTHLY_TIMEFRAME = '&timeframe=monthly'

    def __init__(self, key_file="", pv_solar_path=""): 
        self.tables = []
        self.pv = pv_solar_file.pv_solar_file()
        self.pv_solar_path = pv_solar_path
        self.http = urllib3.PoolManager()
        try:
            with open(key_file) as keyfile:
                key = [line.strip() for line in keyfile.readlines()]
                self.KEY += key[0]
        except:
            self.KEY += "DEMO_KEY"

    def determine_latitude(self, address):
        query = self.form_query(address, 0, 0, 10000, short=True)
        root = self.get_query_response(query)
        lats = root.findall('*/lat')
        return int(float(lats[0].text) + 0.5)

    def get_UTC_0(self, root):
        tz = root.findall('*/tz')
        if len(tz) != 1:
            raise ValueError("Multiple timezones? %d" % len(tz))
        tz = float(tz[0].text)
        hours = int(abs(tz))
        minutes = int((abs(tz) - hours) * 60.0)
        tz_delta = timedelta(hours=hours, minutes=minutes)
        logging.debug("TZ_DELTA: %d %d" % (hours, minutes))
        basetime = datetime(2019, 1, 1, hour=0, minute=0) + tz_delta
        logging.debug("UTC: %s" % basetime.strftime(DATE_FORMAT))
        return basetime

    def form_query(self, address, lat, lon, capacity_kw, short=False):
        if lat == self.BAD_LAT_LON:
            tilt = self.determine_latitude(address)
        else:
            if lat == '':
                tilt = 0.0
            else:
                tilt = lat
        query = self.API+self.KEY+self.CAPACITY + ("%f" % capacity_kw)
        if address == "":
            query += self.LAT + ("%d" % lat) + self.LON + ("%d" % lon) 
        else:
            query += self.ADDRESS + address
        query += self.TILT + ("%d" % tilt)
        query += (self.ARRAY_TYPE  + self.AZIMUTH + self.LOSSES +
                  self.MOD_TYPE + self.DATASET)
        if short:
            query += self.MONTHLY_TIMEFRAME
        else:
            query += self.HOURLY_TIMEFRAME
        logging.debug("QUERY: %s" % query)
        return query

    def print_tree(self, root, depth):
        for item in root:
            print ("    " * depth, item.tag, item.attrib, item.text)
            if (depth < 2):
                self.print_tree(item, depth+1)

    def get_query_response(self, query):
        response = self.http.request('GET', query)
        root = ET.fromstring(response.data)
        err_text = self.get_errors(root)
        if err_text != "":
            raise ValueError("Query had errors: %s" % err_text)
        return root

    def get_errors(self, root):
        resp = ""
        for err in root.findall("errors/*"):
            resp += "\n" + err.text
        return resp

    def add_new_site(self, address, lat, lon, capacity_kw):
        query = self.form_query(address, lat, lon, capacity_kw)
        root = self.get_query_response(query)
        UTC = self.get_UTC_0(root)
        # self.print_tree(root, 0)
        hours = root.findall("*/ac/ac")
        if not len(hours) == 24*365:
            raise ValueError("Query returned incorrect hours: %d" % len(hours))

        if address == '':
            address = "%d,%d" % (lat, lon)
        l_tm = datetime(2019, 1, 1, 0, 0)
        one_hour = timedelta(hours = 1)

        for idx, hour in enumerate(hours):
            capacity = float(hour.text) / 1000.0
            self.pv.add_pv_solar_hour(address, idx, UTC.year, UTC.month, UTC.day, UTC.hour,
                                      l_tm.year, l_tm.month, l_tm.day, l_tm.hour,
                                      capacity)
            l_tm += one_hour
            UTC += one_hour

    def write_solar_generator_file(self):
        self.pv.write_pv_solar_file(self.pv_solar_path)

def create_parser():
    parser = OptionParser(description="Get solar generation data based on location and capacity of the solar array.")
    parser.add_option('-l', '--lat_lon',
            dest = 'lat_lon',
            action = 'store', type = 'string', default = "",
            help = "Integer latitude,longitude  of the solar array, -180 to 180.",
            metavar = 'LAT_LON')
    parser.add_option('-a', '--address',
            dest = 'address',
            action = 'append', type = 'string', default = [],
            help = "Text address of the solar array.",
            metavar = 'ADDRESS')
    parser.add_option('-c', '--capacity',
            dest = 'capacity',
            action = 'store', type = 'float', default = 10.0,
            help = "Name plate capacity in kW of the solar array.",
            metavar = 'CAPACITY')
    parser.add_option('-k', '--keyfile',
            dest = 'key_file',
            action = 'store', type = 'string', default = "DEMO_KEY",
            help = "File whose first line is a user key for PVWatts.",
            metavar = 'FILE')
    return parser

def main(argv = None):
    logging.basicConfig(level=logging.INFO)

    parser = create_parser()
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = parser.parse_args(argv)
    if len(argv) != 0 or (options.address == "" and options.lat_lon == ""):
        parser.print_help()
        return -1

    lat = SolarGeneration.BAD_LAT_LON
    lon = SolarGeneration.BAD_LAT_LON
    if options.address == "":
        try:
            lat, lon = [int(x.strip()) for x in options.lat_lon.split(',')]
        except:
            parser.print_help()
            return -1

    pv = SolarGeneration(options.key_file)
    for address in options.address:
        pv.add_new_site(address, lat, lon, options.capacity)
    pv.write_solar_generator_file()

if __name__ == '__main__':
    sys.exit(main())
