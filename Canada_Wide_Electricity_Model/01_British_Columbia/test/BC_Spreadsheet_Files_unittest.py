#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Support for the common "demand profile" file format.

    Each file line is an instance of
    Greenwich Mean Time Year, Month, Day, Hour

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
# print("BC: sys.path %s" % sys.path)

from BC_Spreadsheet_Files import BCSpreadsheetFiles

class TestBCSpreadsheetFile(unittest.TestCase):

    def setUp(self):
        pass

    def test_constants(self):
        pass

    def test_utc_conversion(self):
        ssheet = BCSpreadsheetFiles()

        y, m, d, h = ssheet._get_BC_UTC(2000, 1, 1, 0)
        self.assertEqual(y, 2000)
        self.assertEqual(m, 1)
        self.assertEqual(d, 1)
        self.assertEqual(h, 8)

        y, m, d, h = ssheet._get_BC_UTC(2000, 1, 1, 16)
        self.assertEqual(y, 2000)
        self.assertEqual(m, 1)
        self.assertEqual(d, 2)
        self.assertEqual(h, 0)

        y, m, d, h = ssheet._get_BC_UTC(2000,12,31,17)
        self.assertEqual(y, 2001)
        self.assertEqual(m, 1)
        self.assertEqual(d, 1)
        self.assertEqual(h, 1)

        y, m, d, h = ssheet._get_BC_UTC(2017, 6,21,18)
        self.assertEqual(y, 2017)
        self.assertEqual(m, 6)
        self.assertEqual(d,22)
        self.assertEqual(h, 1)

        ## Times around DST changes - spring forward
        y, m, d, h = ssheet._get_BC_UTC(2006, 4, 2, 1)
        self.assertEqual(y, 2006)
        self.assertEqual(m, 4)
        self.assertEqual(d, 2)
        self.assertEqual(h, 9)

        y, m, d, h = ssheet._get_BC_UTC(2006, 4, 2, 3)
        self.assertEqual(y, 2006)
        self.assertEqual(m, 4)
        self.assertEqual(d, 2)

        self.assertEqual(h,10)

        ## Times around DST changes - fall back
        y, m, d, h = ssheet._get_BC_UTC(2006,10,29, 2, True)
        self.assertEqual(y, 2006)
        self.assertEqual(m,10)
        self.assertEqual(d,29)
        self.assertEqual(h,10)

        y, m, d, h = ssheet._get_BC_UTC(2006,10,29, 2, False)
        self.assertEqual(y, 2006)
        self.assertEqual(m,10)
        self.assertEqual(d,29)
        self.assertEqual(h,10)

        y, m, d, h = ssheet._get_BC_UTC(2006,10,29, 2, False)
        self.assertEqual(y, 2006)
        self.assertEqual(m,10)
        self.assertEqual(d,29)
        self.assertEqual(h,10)

        y, m, d, h = ssheet._get_BC_UTC(2006,10,29, 2, True)
        self.assertEqual(y, 2006)
        self.assertEqual(m,10)
        self.assertEqual(d,29)
        self.assertEqual(h,10)

        y, m, d, h = ssheet._get_BC_UTC(2006,10,29, 1, True)
        self.assertEqual(y, 2006)
        self.assertEqual(m,10)
        self.assertEqual(d,29)
        self.assertEqual(h, 8)

        y, m, d, h = ssheet._get_BC_UTC(2006,10,29, 1, False)
        self.assertEqual(y, 2006)
        self.assertEqual(m,10)
        self.assertEqual(d,29)
        self.assertEqual(h, 9)

        y, m, d, h = ssheet._get_BC_UTC(2006,10,29, 1, False)
        self.assertEqual(y, 2006)
        self.assertEqual(m,10)
        self.assertEqual(d,29)
        self.assertEqual(h, 9)

        y, m, d, h = ssheet._get_BC_UTC(2006,10,29, 1, True)
        self.assertEqual(y, 2006)
        self.assertEqual(m,10)
        self.assertEqual(d,29)
        self.assertEqual(h, 8)

if __name__ == '__main__':
    unittest.main()
