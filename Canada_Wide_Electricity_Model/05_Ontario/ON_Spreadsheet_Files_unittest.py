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
from ON_Spreadsheet_Files import ONSpreadsheetFiles

class TestBCSpreadsheetFile(unittest.TestCase):

    def setUp(self):
        pass

    def test_constants(self):
        pass

    def test_utc_conversion(self):
        ssheet = ONSpreadsheetFiles()

        uy, um, ud, uh, y, m, d, h = ssheet._get_ON_UTC(2000, 1, 1, 0)
        self.assertEqual(uy, 2000)
        self.assertEqual(um, 1)
        self.assertEqual(ud, 1)
        self.assertEqual(uh, 5)

        uy, um, ud, uh, y, m, d, h = ssheet._get_ON_UTC(2000, 1, 1, 19)
        self.assertEqual(uy, 2000)
        self.assertEqual(um, 1)
        self.assertEqual(ud, 2)
        self.assertEqual(uh, 0)

        uy, um, ud, uh, y, m, d, h = ssheet._get_ON_UTC(2000,12,31,19)
        self.assertEqual(uy, 2001)
        self.assertEqual(um, 1)
        self.assertEqual(ud, 1)
        self.assertEqual(uh, 0)

        uy, um, ud, uh, y, m, d, h = ssheet._get_ON_UTC(2017, 6,20,21)
        self.assertEqual(uy, 2017)
        self.assertEqual(um, 6)
        self.assertEqual(ud,21)
        self.assertEqual(uh, 1)

        ## Times around DST changes - spring forward
        uy, um, ud, uh, y, m, d, h = ssheet._get_ON_UTC(2015, 3, 8, 2)
        self.assertEqual(uy, 2015)
        self.assertEqual(um, 3)
        self.assertEqual(ud, 8)
        self.assertEqual(uh, 7)

        uy, um, ud, uh, y, m, d, h = ssheet._get_ON_UTC(2015, 3, 8, 3)
        self.assertEqual(uy, 2015)
        self.assertEqual(um, 3)
        self.assertEqual(ud, 8)
        self.assertEqual(uh, 7)

        uy, um, ud, uh, y, m, d, h = ssheet._get_ON_UTC(2015, 3, 8, 4)
        self.assertEqual(uy, 2015)
        self.assertEqual(um, 3)
        self.assertEqual(ud, 8)
        self.assertEqual(uh, 8)

        ## Times around DST changes - fall back
        uy, um, ud, uh, y, m, d, h = ssheet._get_ON_UTC(2015,11, 1, 0, True)
        self.assertEqual(uy, 2015)
        self.assertEqual(um,11)
        self.assertEqual(ud, 1)
        self.assertEqual(uh, 4)

        uy, um, ud, uh, y, m, d, h = ssheet._get_ON_UTC(2015,11, 1, 1, True)
        self.assertEqual(uy, 2015)
        self.assertEqual(um,11)
        self.assertEqual(ud, 1)
        self.assertEqual(uh, 5)

        uy, um, ud, uh, y, m, d, h = ssheet._get_ON_UTC(2015,11, 1, 1, False)
        self.assertEqual(uy, 2015)
        self.assertEqual(um,11)
        self.assertEqual(ud, 1)
        self.assertEqual(uh, 6)

        uy, um, ud, uh, y, m, d, h = ssheet._get_ON_UTC(2015,11, 1, 2, False)
        self.assertEqual(uy, 2015)
        self.assertEqual(um,11)
        self.assertEqual(ud, 1)
        self.assertEqual(uh, 7)

        uy, um, ud, uh, y, m, d, h = ssheet._get_ON_UTC(2015,11, 1, 3, False)
        self.assertEqual(uy, 2015)
        self.assertEqual(um,11)
        self.assertEqual(ud, 1)
        self.assertEqual(uh, 8)

if __name__ == '__main__':
    unittest.main()
