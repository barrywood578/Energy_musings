#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Unit test for common definitions

"""

import os
import path
from common_defs import *
import unittest
from math import isnan

class TestConstants(unittest.TestCase):

    def setUp(self):
        pass

    def test_constants(self):
        self.assertEqual(SEPARATOR, "', '")
        self.assertEqual(KEY_SEPARATOR, "-")
        self.assertEqual(START_END, "'")
        self.assertEqual(EXCEL_FILE_EXTENSION, ".xlsx")
        self.assertEqual(CSV_FILE_EXTENSION, ".csv")
        self.assertEqual(PDF_FILE_EXTENSION, ".pdf")
        self.assertEqual(LOAD_ERROR, -1.0)
        self.assertEqual(DATE_FORMAT, '%Y-%m-%d %H:%M')
        
        self.assertTrue(isnan(INVALID_VALUE))
        self.assertEqual(INVALID_LIST, "INVALID")

        # The following lines confirm that all definitions in the
        # common_defs.py file are checked, assuming each definition
        # has exactly one '=' character.
        file_path = "common_defs.py"
        if not os.path.isfile(file_path):
            file_path = "Common/common_defs.py"
        with open(file_path, 'r') as tempfile:
            counts = [line.strip().count('=') for line in tempfile.readlines()]
        self.assertEqual(sum(counts), 10)

if __name__ == '__main__':
    unittest.main()
