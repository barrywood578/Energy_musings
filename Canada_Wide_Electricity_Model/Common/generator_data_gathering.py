#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Scrape provincial generation capability from
    Wikipedia pages.  

"""

from optparse import OptionParser
from collections import OrderedDict
import operator
import sys
import logging
from lxml import etree
import urllib3
from generator_file import generator_file
from solar_data_gathering import SolarGeneration

class my_table_info(object):
    def __init__(self, heading, columns, data):
        self.heading = heading
        self.column_names = columns
        self.data = data

class GeneratorHTML(object):
    def __init__(self, url="", key_file="DEMO_KEY", pv_solar_path=''):
        self.gen_file = generator_file()
        self.pv_solar = SolarGeneration(key_file, pv_solar_path)
        self.tables = []
        if (url == ""):
            return
        http = urllib3.PoolManager()
        response = http.request('GET', url)
        parser = etree.HTMLParser()
        tree = etree.fromstring(response.data, parser)
        self.tables = self.find_tables_in_tree(tree, '');

    def print_tables(self):
        print("======================================")
        for table in self.tables:
            print("HEADING: ", table.heading)
            print(",".join(table.column_names))
            for data in table.data:
                labelled_data = [("%s:%s" % (a, b)) for a,b in zip(table.column_names, data)]
                print(",".join(labelled_data))
            print("======================================")

    def extract_table(self, tree, last_header):
        my_table = my_table_info(last_header, [], [])
        for row in tree:
            if (row.tag == "tr"):
                texts = []
                for col in row:
                    text = ''.join(col.itertext())
                    toks = [tok.strip() for tok in text.split("\n")]
                    text = " ".join(toks)
                    texts.append(text)
                if ('bgcolor' in row.attrib):
                    logging.debug("Discarded row %s:%s" % (row.attrib, ",".join(texts)))
                    continue
                if row[0].tag == 'th':
                    if my_table.column_names == []:
                        found_header = True
                        my_table.column_names = texts
                    else:
                        logging.debug("Discarded subsequent table header")
                        pass
                elif row[0].tag == 'td':
                    if (len(texts) == len(my_table.column_names)):
                        my_table.data.append(texts)
                    else:
                        logging.debug("Discarded table data")
                        pass
        col_count = len(my_table.column_names)
        if col_count == 0:
            logging.debug("Column count is 0!")
            return None
        for row in my_table.data:
            if len(row) != col_count:
                logging.debug("Row count does not match column count!")
                return None
        logging.debug("Found table %s" % my_table.heading)
        return my_table

    def find_tables_in_tree(self, tree, last_header):
        tables = []
        for child in tree:
            tag_str = str(child.tag)
            if tag_str[0] == 'h' and tag_str[1] in ['1', '2', '3']:
                last_header = ''.join(child.itertext())
                continue
            if (child.tag == "tbody"):
                new_table = self.extract_table(child, last_header)
                if not new_table is None:
                    tables.append(new_table)
            tables += self.find_tables_in_tree(child, last_header)
        return tables

    def find_fuel(self, target):
        mapping_keywords = {
            'NUCLEAR': ['nuclear'],
            'HYDRO': ['hydro'],
            'CO_GEN' : ['waste heat', 'blast furnace'],
            'BIOMASS': ['biomass', 'biogas', 'waste'],
            'NATGAS' : ['natural gas', 'dual fuel'],
            'OIL' : ['fuel oil', 'diesel'],
            'COAL': ['coal', 'coke'],
            'WIND' : ['wind'],
            'SOLAR_PV' : ['solar', 'photoelectric', 'photovoltaic'],
            'STORAGE': ['battery', 'pumped']
            }
        target_l = target.strip().lower()
        for key in mapping_keywords.keys():
            for substr in mapping_keywords[key]:
                if substr in target_l:
                    return key
        return ''

    def find_column(self, table, keywords):
        for idx, col in enumerate(table.column_names):
            for kw in keywords:
                if kw in col:
                    return idx
        return -1

    def find_fuel_column(self, table):
        mapping_keywords = ["Type", "Fuel"]
        return self.find_column(table, mapping_keywords)

    def find_capacity_column(self, table):
        mapping_keywords = ["Capacity"]
        return self.find_column(table, mapping_keywords)

    def find_location_column(self, table):
        mapping_keywords = ["Location"]
        return self.find_column(table, mapping_keywords)

    def add_solar_site_data(self, location, capacity):
        if ("off-grid" in location):
            logging.debug("Skipping %s" % location)
            return
        logging.info("Querying PVWATTS, location %s" % location)
        self.pv_solar.add_new_site(location+",Canada", '', '', float(capacity) * 1000.0)

    def map_table_to_generator_file(self, table, tz_string):
        fuel_idx = -1
        fuel = self.find_fuel(table.heading)
        if fuel == '':
            fuel_idx = self.find_fuel_column(table)
        cap_idx = self.find_capacity_column(table)
        loc_idx = self.find_location_column(table)
        if (cap_idx == -1) or ((fuel == '') and (fuel_idx == -1)):
            logging.info("Skipping table %s" % table.heading)
            logging.debug("Skipping table %s, no fuel %s %d or capacity %d" %
                         (table.heading, fuel, fuel_idx, cap_idx))
            return

        fuel_name = fuel
        for row in table.data:
            if row[0].strip().lower() == "total":
                continue
            if fuel == '':
                fuel_name = self.find_fuel(row[fuel_idx])
            if fuel_name == '':
                logging.info("Skipping table %s row %s, no fuel or capacity" %
                             (table.heading, row))
                continue
            capacity = row[cap_idx].strip()
            # Kludged few quick fixes to items in tables...
            if capacity == '':
                capacity = "0.0"
            if capacity[0] == '(':
                logging.info("Skipping table %s row %s, decommissioned." %
                             (table.heading, row))
                continue
            if capacity == "3Solar":
                capacity = "3"
            if capacity == r"829[4]":
                capacity = "829"
            logging.debug("%s:%s" % (fuel_name, capacity))
            self.gen_file.add_generator([fuel_name, capacity, '0.0', tz_string])
            if (fuel_name == "SOLAR_PV") and (not loc_idx == -1):
                self.add_solar_site_data(row[loc_idx], capacity)
        logging.info("Processed table %s" % (table.heading))

    def map_tables_to_generator_file(self, tz_string):
        for table in self.tables:
            if 'off-grid' in table.heading.lower():
                logging.info("Skipping table %s" % table.heading)
                continue
            self.map_table_to_generator_file(table, tz_string)

    def write_generator_file(self):
        self.gen_file.write_generator_file()

    def write_pv_solar_file(self):
        self.pv_solar.write_solar_generator_file()

def create_parser():
    parser = OptionParser(description="Get generation file based on Wikipedia list of generating stations.")
    parser.add_option('-u', '--url',
            dest = 'url_path',
            action = 'store', type = 'string', default = "",
            help = "URL for a provincial list of generating stations.",
            metavar = 'URL')
    parser.add_option('-t', '--timezone',
            dest = 'tz_str',
            action = 'store', type = 'string', default = "",
            help = "Valid pytz timezone string.",
            metavar = 'TIMEZONE')
    parser.add_option('-k', '--keyfile',
            dest = 'key_file',
            action = 'store', type = 'string', default = "DEMO_KEY",
            help = "File whose first line is a user key for PVWatts.",
            metavar = 'FILE')
    parser.add_option('-s', '--solar_file',
            dest = 'pv_solar_file',
            action = 'store', type = 'string', default = "",
            help = "If present, name of file containing hourly PV Solar generation data.",
            metavar = 'FILE')
    return parser

def main(argv = None):
    logging.basicConfig(level=logging.INFO)

    parser = create_parser()
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = parser.parse_args(argv)
    if len(argv) != 0:
        print('Must enter a URL!')
        print
        parser.print_help()
        return -1

    gen_HTML = GeneratorHTML(options.url_path, options.key_file, options.pv_solar_file)
    gen_HTML.map_tables_to_generator_file(options.tz_str)
    gen_HTML.write_generator_file()
    gen_HTML.pv_solar.write_solar_generator_file()

if __name__ == '__main__':
    sys.exit(main())
