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
from PQ_Spreadsheet_Files import PQSpreadsheetFiles

class TestPQSpreadsheetFile(unittest.TestCase):

    def setUp(self):
        pass

    def test_constants(self):
        pass

    def test_utc_conversion(self):
        ssheet = PQSpreadsheetFiles()

        y, m, d, h = ssheet.get_PQ_UTC(2014, 1, 1, 0)
        self.assertEqual(y, 2014)
        self.assertEqual(m, 1)
        self.assertEqual(d, 1)
        self.assertEqual(h, 5)

        y, m, d, h = ssheet.get_PQ_UTC(2014, 1, 1, 19)
        self.assertEqual(y, 2014)
        self.assertEqual(m, 1)
        self.assertEqual(d, 2)
        self.assertEqual(h, 0)

        ## Not DST
        y, m, d, h = ssheet.get_PQ_UTC(2014,12,31,20)
        self.assertEqual(y, 2015)
        self.assertEqual(m, 1)
        self.assertEqual(d, 1)
        self.assertEqual(h, 1)

        ## DST
        y, m, d, h = ssheet.get_PQ_UTC(2014, 6,21,20)
        self.assertEqual(y, 2014)
        self.assertEqual(m, 6)
        self.assertEqual(d,22)
        self.assertEqual(h, 0)

        ## Times around DST changes - spring forward
        y, m, d, h = ssheet.get_PQ_UTC(2014, 3, 9, 1, False)
        self.assertEqual(y, 2014)
        self.assertEqual(m, 3)
        self.assertEqual(d, 9)
        self.assertEqual(h, 6)

        y, m, d, h = ssheet.get_PQ_UTC(2014, 3, 9, 1, True)
        self.assertEqual(y, 2014)
        self.assertEqual(m, 3)
        self.assertEqual(d, 9)
        self.assertEqual(h, 6)

        y, m, d, h = ssheet.get_PQ_UTC(2014, 3, 9, 2, False)
        self.assertEqual(y, 2014)
        self.assertEqual(m, 3)
        self.assertEqual(d, 9)
        self.assertEqual(h, 7)

        y, m, d, h = ssheet.get_PQ_UTC(2014, 3, 9, 2, True)
        self.assertEqual(y, 2014)
        self.assertEqual(m, 3)
        self.assertEqual(d, 9)
        self.assertEqual(h, 6)

        y, m, d, h = ssheet.get_PQ_UTC(2014, 3, 9, 3, False)
        self.assertEqual(y, 2014)
        self.assertEqual(m, 3)
        self.assertEqual(d, 9)
        self.assertEqual(h, 7)

        y, m, d, h = ssheet.get_PQ_UTC(2014, 3, 9, 3, True)
        self.assertEqual(y, 2014)
        self.assertEqual(m, 3)
        self.assertEqual(d, 9)
        self.assertEqual(h, 7)

        ## Times around DST changes - fall back
        y, m, d, h = ssheet.get_PQ_UTC(2014,11, 2, 0, True)
        self.assertEqual(y, 2014)
        self.assertEqual(m,11)
        self.assertEqual(d, 2)
        self.assertEqual(h, 4)

        y, m, d, h = ssheet.get_PQ_UTC(2014,11, 2, 0, False)
        self.assertEqual(y, 2014)
        self.assertEqual(m,11)
        self.assertEqual(d, 2)
        self.assertEqual(h, 4)

        y, m, d, h = ssheet.get_PQ_UTC(2014,11, 2, 1, True)
        self.assertEqual(y, 2014)
        self.assertEqual(m,11)
        self.assertEqual(d, 2)
        self.assertEqual(h, 5)

        y, m, d, h = ssheet.get_PQ_UTC(2014,11, 2, 1, False)
        self.assertEqual(y, 2014)
        self.assertEqual(m,11)
        self.assertEqual(d, 2)
        self.assertEqual(h, 6)

        y, m, d, h = ssheet.get_PQ_UTC(2014,11, 2, 2, True)
        self.assertEqual(y, 2014)
        self.assertEqual(m,11)
        self.assertEqual(d, 2)
        self.assertEqual(h, 7)

        y, m, d, h = ssheet.get_PQ_UTC(2014,11, 2, 2, False)
        self.assertEqual(y, 2014)
        self.assertEqual(m,11)
        self.assertEqual(d, 2)
        self.assertEqual(h, 7)

        y, m, d, h = ssheet.get_PQ_UTC(2014,11, 2, 3, True)
        self.assertEqual(y, 2014)
        self.assertEqual(m,11)
        self.assertEqual(d, 2)
        self.assertEqual(h, 8)

        y, m, d, h = ssheet.get_PQ_UTC(2014,11, 2, 3, False)
        self.assertEqual(y, 2014)
        self.assertEqual(m,11)
        self.assertEqual(d, 2)
        self.assertEqual(h, 8)

if __name__ == '__main__':
    unittest.main()
