#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Unit test for common definitions

"""

from common_defs import *
import unittest

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
        
        # The following lines confirm that all definitions in the
        # common_defs.py file are checked, assuming each definition
        # has exactly one '=' character.
        with open("common_defs.py", 'r') as tempfile:
            counts = [line.strip().count('=') for line in tempfile.readlines()]
        self.assertEqual(sum(counts), 7)

if __name__ == '__main__':
    unittest.main()
