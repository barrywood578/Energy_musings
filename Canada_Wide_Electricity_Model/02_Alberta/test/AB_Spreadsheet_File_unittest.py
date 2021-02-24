#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Partial unit test of Alberta spreadsheet support.
"""

from optparse import OptionParser
from collections import OrderedDict
import operator
import sys
import os
import logging
import unittest
from datetime import datetime, timezone

curdir = os.path.dirname(os.path.abspath(__file__))
par_dir = os.path.split(curdir)[0]
if par_dir not in sys.path:
    sys.path.append(par_dir)
com_dir = os.path.abspath(os.path.join(par_dir, "../Common"))
if com_dir not in sys.path:
    sys.path.append(com_dir)
# print("AB: sys.path %s" % sys.path)
from AB_Spreadsheet_File import AB_Spreadsheet_File

class TestABSpreadsheetFile(unittest.TestCase):

    def setUp(self):
        pass

    def test_constants(self):
        pass

    def test_parse_date_success(self):
        ssheet = AB_Spreadsheet_File()

        y, m, d, h = ssheet._parse_date(100, "02JAN2008:00:03:04")
        self.assertEqual(y, 2008)
        self.assertEqual(m, 1)
        self.assertEqual(d, 2)
        self.assertEqual(h, 0)

        y, m, d, h = ssheet._parse_date(100, "03FEB2009:04:05:06")
        self.assertEqual(y, 2009)
        self.assertEqual(m, 2)
        self.assertEqual(d, 3)
        self.assertEqual(h, 4)

        y, m, d, h = ssheet._parse_date(100, "04MAR2010:05:06:07")
        self.assertEqual(y, 2010)
        self.assertEqual(m, 3)
        self.assertEqual(d, 4)
        self.assertEqual(h, 5)

        y, m, d, h = ssheet._parse_date(100, "05APR2011:06:07:08")
        self.assertEqual(y, 2011)
        self.assertEqual(m, 4)
        self.assertEqual(d, 5)
        self.assertEqual(h, 6)

        y, m, d, h = ssheet._parse_date(100, "06MAY2012:07:08:09")
        self.assertEqual(y, 2012)
        self.assertEqual(m, 5)
        self.assertEqual(d, 6)
        self.assertEqual(h, 7)

        y, m, d, h = ssheet._parse_date(100, "07JUN2013:08:09:10")
        self.assertEqual(y, 2013)
        self.assertEqual(m, 6)
        self.assertEqual(d, 7)
        self.assertEqual(h, 8)

        y, m, d, h = ssheet._parse_date(100, "08JUL2014:09:10:11")
        self.assertEqual(y, 2014)
        self.assertEqual(m, 7)
        self.assertEqual(d, 8)
        self.assertEqual(h, 9)

        y, m, d, h = ssheet._parse_date(100, "09AUG2015:10:11:12")
        self.assertEqual(y, 2015)
        self.assertEqual(m, 8)
        self.assertEqual(d, 9)
        self.assertEqual(h, 10)


        y, m, d, h = ssheet._parse_date(100, "10SEP2016:11:12:13")
        self.assertEqual(y, 2016)
        self.assertEqual(m, 9)
        self.assertEqual(d, 10)
        self.assertEqual(h, 11)

        y, m, d, h = ssheet._parse_date(100, "11OCT2017:12:13:14")
        self.assertEqual(y, 2017)
        self.assertEqual(m, 10)
        self.assertEqual(d, 11)
        self.assertEqual(h, 12)

        y, m, d, h = ssheet._parse_date(100, "12NOV2018:13:14:15")
        self.assertEqual(y, 2018)
        self.assertEqual(m, 11)
        self.assertEqual(d, 12)
        self.assertEqual(h, 13)

        y, m, d, h = ssheet._parse_date(100, "13DEC2019:14:15:16")
        self.assertEqual(y, 2019)
        self.assertEqual(m, 12)
        self.assertEqual(d, 13)
        self.assertEqual(h, 14)

if __name__ == '__main__':
    unittest.main()
