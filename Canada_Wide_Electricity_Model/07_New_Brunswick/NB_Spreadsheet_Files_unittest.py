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
from NB_Spreadsheet_Files import NBSpreadsheetFiles

class TestNBSpreadsheetFile(unittest.TestCase):

    def setUp(self):
        pass

    def test_constants(self):
        pass

    def test_utc_conversion(self):
        ssheet = NBSpreadsheetFiles()

        y, m, d, h = ssheet._get_NB_UTC(2000, 1, 1, 0)
        self.assertEqual(y, 2000)
        self.assertEqual(m, 1)
        self.assertEqual(d, 1)
        self.assertEqual(h, 4)

        y, m, d, h = ssheet._get_NB_UTC(2000, 1, 1, 20)
        self.assertEqual(y, 2000)
        self.assertEqual(m, 1)
        self.assertEqual(d, 2)
        self.assertEqual(h, 0)

        y, m, d, h = ssheet._get_NB_UTC(2000,12,31,21)
        self.assertEqual(y, 2001)
        self.assertEqual(m, 1)
        self.assertEqual(d, 1)
        self.assertEqual(h, 1)

        y, m, d, h = ssheet._get_NB_UTC(2017, 6,21,22)
        self.assertEqual(y, 2017)
        self.assertEqual(m, 6)
        self.assertEqual(d,22)
        self.assertEqual(h, 1)

        ## Times around DST changes - spring forward at 2 a.m.
        y, m, d, h = ssheet._get_NB_UTC(2013, 3,10, 1)
        self.assertEqual(y, 2013)
        self.assertEqual(m, 3)
        self.assertEqual(d,10)
        self.assertEqual(h, 5)

        y, m, d, h = ssheet._get_NB_UTC(2013, 3,10, 3)
        self.assertEqual(y, 2013)
        self.assertEqual(m, 3)
        self.assertEqual(d,10)
        self.assertEqual(h, 6)

        ## Times around DST changes - fall back at 2 a.m.
        ## Repeat 1 a.m., with and then without DST.
        y, m, d, h = ssheet._get_NB_UTC(2013,11, 3, 0, True)
        self.assertEqual(y, 2013)
        self.assertEqual(m,11)
        self.assertEqual(d, 3)
        self.assertEqual(h, 3)

        y, m, d, h = ssheet._get_NB_UTC(2013,11, 3, 1, True)
        self.assertEqual(y, 2013)
        self.assertEqual(m,11)
        self.assertEqual(d, 3)
        self.assertEqual(h, 4)

        y, m, d, h = ssheet._get_NB_UTC(2013,11, 3, 1, False)
        self.assertEqual(y, 2013)
        self.assertEqual(m,11)
        self.assertEqual(d, 3)
        self.assertEqual(h, 5)

        y, m, d, h = ssheet._get_NB_UTC(2013,11, 3, 2, False)
        self.assertEqual(y, 2013)
        self.assertEqual(m,11)
        self.assertEqual(d, 3)
        self.assertEqual(h, 6)

if __name__ == '__main__':
    unittest.main()
