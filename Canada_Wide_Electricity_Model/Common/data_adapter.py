#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Scales data found in one or more directories
    into another directory.
"""

from optparse import OptionParser
from collections import OrderedDict
import operator
import sys
import os
import logging
from datetime import datetime, timezone
from adjust_data import AdjustData
import pytz

sys.path.append('../Common')
from common_defs import *
from demand_file import DemandFile
from generator_file import generator_file

class data_adapter(object):
    def __init__(self, src_dir, trg_dir):
        self.src_dir = src_dir
        self.src_load = None
        self.src_gen = None
        self.trg_gen = None

        self.src_load_path = os.path.join(os.path.abspath(src_dir), FILE_LOAD_DB) 
        self.trg_load_path = os.path.join(os.path.abspath(trg_dir), FILE_LOAD_DB) 
        try:
            self.src_load = DemandFile(self.src_load_path)
        except:
            logging.warning("Could not read '%s'" % self.src_load_path)
            self.src_load = DemandFile()

        self.src_gen_path = os.path.join(os.path.abspath(src_dir), FILE_GEN_DB)
        self.trg_gen_path = os.path.join(os.path.abspath(trg_dir), FILE_GEN_DB)
        try:
            self.src_gen = generator_file(self.src_gen_path)
        except:
            logging.warning("Could not read '%s'" % self.src_gen_path)
        try:
            self.trg_gen = generator_file(self.trg_gen_path)
        except:
            logging.warning("Could not read '%s'" % self.trg_gen_path)
            self.trg_gen = generator_file()

    def scale_trg_load(self, adj):
        utc = self.src_load.min_time
        interval = self.src_load.max_time - utc
        self.src_load.adjust_mw_hours(utc, interval, adj)

    def update_trg_gen(self):
        self.trg_gen.copy_missing_data(self.src_gen)

    def write_load_file(self):
        self.src_load.write_hourly_mw_file(filepath=self.trg_load_path)

    def write_gen_file(self):
        self.trg_gen.write_generator_file(filepath=self.trg_gen_path, write_hourly_files=True)

def create_parser():
    parser = OptionParser(description="Clone load and generation data from one province to another.")
    parser.add_option('-s', '--source',
            dest = 'source_dir',
            action = 'store', type = 'string', default = "",
            help = 'Directory of source data files.',
            metavar = 'FILE')
    parser.add_option('-t', '--target',
            dest = 'target_dir',
            action = 'store', type = 'string', default = "",
            help = 'Directory for target data files.',
            metavar = 'FILE')
    parser.add_option('-r', '--load_ratio',
            dest = 'load_ratio',
            action = 'store', type = 'float', default = 1.0,
            help = 'Ratio of source load to target load.',
            metavar = 'FILE')
    parser.add_option('-l', '--write_load',
            dest = 'write_load',
            action = 'store_true', default = False,
            help = 'Write adjusted load file to target directory.',
            metavar = 'FILE')
    parser.add_option('-g', '--write_gen',
            dest = 'write_gen',
            action = 'store_true', default = False,
            help = 'Write adjusted generation file(s) to target directory.',
            metavar = 'FILE')
    return parser

def main(argv = None):
    logging.basicConfig(level=logging.INFO)
    parser = create_parser()
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = parser.parse_args(argv)
    if options.source_dir == "" or options.target_dir == "":
        print('Must enter source and target directories!')
        print
        parser.print_help()
        return -1

    adapter = data_adapter(options.source_dir, options.target_dir)
    if (options.load_ratio != 1.0):
        adj = AdjustData(ratio=options.load_ratio)
        adapter.scale_trg_load(adj)
    if options.write_load:
        adapter.write_load_file()
    if options.write_gen:
        adapter.update_trg_gen()
        adapter.write_gen_file()

if __name__ == '__main__':
    sys.exit(main())
