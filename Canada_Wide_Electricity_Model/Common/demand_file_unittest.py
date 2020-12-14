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
from common_defs import *
from demand_file import *

class TestDemandHour(unittest.TestCase):

    def setUp(self):
        pass

    def test_constants(self):
        demand_hr = demand_hour()
        self.assertEqual(demand_hr.default_year, "0000")
        self.assertEqual(demand_hr.default_month, "00")
        self.assertEqual(demand_hr.default_day, "00")
        self.assertEqual(demand_hr.default_hour, "24")
        self.assertEqual(demand_hr.default_demand, "000000.0")

    def test_init(self):
        demand_hr = demand_hour()
        self.assertEqual(demand_hr.file_path, "")
        self.assertEqual(demand_hr.line_num, "")
        self.assertEqual(demand_hr.UTC_Y, "0000")
        self.assertEqual(demand_hr.UTC_M, "00")
        self.assertEqual(demand_hr.UTC_D, "00")
        self.assertEqual(demand_hr.UTC_H, "24")
        self.assertEqual(demand_hr.local_Y, "0000")
        self.assertEqual(demand_hr.local_M, "00")
        self.assertEqual(demand_hr.local_D, "00")
        self.assertEqual(demand_hr.local_H, "24")
        self.assertEqual(demand_hr.demand_MW, "000000.0")

    def test_get_list(self):
        the_list = ["file_path", "Line", "1967", "01", "02", "03",
                                         "1978", "04", "05", "06",
                                         "123456.7"]
        demand_hr = demand_hour(the_list)
        new_list = demand_hr.get_list_from_demand_hour()

        self.assertEqual(new_list[0], "file_path")
        self.assertEqual(new_list[1], "Line")
        self.assertEqual(new_list[2], "1967")
        self.assertEqual(new_list[3], "01")
        self.assertEqual(new_list[4], "02")
        self.assertEqual(new_list[5], "03")
        self.assertEqual(new_list[6], "1978")
        self.assertEqual(new_list[7], "04")
        self.assertEqual(new_list[8], "05")
        self.assertEqual(new_list[9], "06")
        self.assertEqual(new_list[10], "123456.7")

        demand_hr = demand_hour()
        new_list = demand_hr.get_list_from_demand_hour()

        self.assertEqual(new_list[0], "")
        self.assertEqual(new_list[1], "")
        self.assertEqual(new_list[2], "0000")
        self.assertEqual(new_list[3], "00")
        self.assertEqual(new_list[4], "00")
        self.assertEqual(new_list[5], "24")
        self.assertEqual(new_list[6], "0000")
        self.assertEqual(new_list[7], "00")
        self.assertEqual(new_list[8], "00")
        self.assertEqual(new_list[9], "24")
        self.assertEqual(new_list[10], "000000.0")

    def test_validate(self):
        bad_list = ["file_path", "Line", "Year", "Month", "Day", "Hour",
                                         "Year", "Month", "Day", "Hour",
                                         "Load"]
        ok_list = ["file_path", "Line", "1967", "01", "02", "03",
                                        "1978", "04", "05", "06",
                                        "123456.7"]
        test_list = copy.deepcopy(ok_list)

        demand_hr = demand_hour(test_list)
        self.assertTrue(demand_hr.validate_ymdhMW())

        for i in range(2, 11):
            test_list[i-1] = ok_list[i-1]
            test_list[i] = bad_list[i]
            demand_hr = demand_hour(test_list)
            self.assertFalse(demand_hr.validate_ymdhMW())

    def test_add_demand_hour_success(self):
        list_1 = ["path 1", "line 1", "2006", "01", "02", "03",
                                      "2006", "01", "02", "10", "10203.7"]
        list_2 = ["path 2", "line 2", "2006", "02", "03", "04",
                                      "2006", "02", "03", "11", "20304.7"]
        list_3 = ["path 3", "line 3", "2007", "02", "03", "05",
                                      "2007", "02", "03", "11", "123456.7"]
        demand = demand_file()

        demand.add_demand_hour(list_1)
        demand.add_demand_hour(list_2)
        demand.add_demand_hour(list_3)

        self.assertEqual(demand.xref_load["2006"]["01"]["02"]["03"], 10203.7)
        self.assertEqual(demand.xref_load["2006"]["02"]["03"]["04"], 20304.7)
        self.assertEqual(demand.xref_load["2007"]["02"]["03"]["05"], 123456.7)

    def test_add_demand_hour_failure(self):
        list_1 = ["path 1", "line 1", "2006", "01", "02", "03",
                                      "2006", "01", "02", "10", "10203.7"]
        list_2 = ["path 2", "line 2", "2006", "01", "02", "03",
                                      "2006", "02", "03", "11", "20304.7"]
        demand = demand_file()

        demand.add_demand_hour(list_1)
        self.assertRaises(ValueError, demand.add_demand_hour, list_2)

if __name__ == '__main__':
    unittest.main()
