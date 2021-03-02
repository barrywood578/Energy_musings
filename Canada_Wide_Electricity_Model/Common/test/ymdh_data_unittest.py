#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Unit test for ymdh_data file.

"""

from adjust_data import AdjustData
from ymdh_data import VA, YMDHData
from datetime import datetime, timezone, timedelta
from common_defs import *

import unittest
import mock
from math import isnan
from unittest.mock import patch, mock_open, call

class TestVA(unittest.TestCase):

    def setUp(self):
        pass

    def test_constants(self):
        self.assertEqual(SEPARATOR, "', '")
        self.assertEqual(START_END, "'")
        self.assertTrue(isnan(INVALID_VALUE))
        self.assertEqual(INVALID_LIST, "INVALID")

    def test_init_success(self):
        va = VA(1.0)
        self.assertEqual(va.val, 1.0)
        self.assertEqual(va.data_array, [[]])

        va = VA(99.0, [1, 2, 3, "Stuff"])
        self.assertEqual(va.val, 99.0)
        self.assertEqual(len(va.data_array), 1)
        self.assertEqual(len(va.data_array[0]), 4)
        self.assertEqual(va.data_array[0][0], 1)
        self.assertEqual(va.data_array[0][1], 2)
        self.assertEqual(va.data_array[0][2], 3)
        self.assertEqual(va.data_array[0][3], "Stuff")

        inval = VA(INVALID_VALUE)
        self.assertTrue(isnan(inval.val))
        self.assertEqual(inval.data_array, "INVALID")

    def test_add(self):
        va1 = VA(1.0, [1])
        va2 = VA(2.0, [2])
        va3 = va1 + va2

        self.assertEqual(va3.val, 3.0)
        self.assertEqual(len(va3.data_array), 2)
        self.assertEqual(len(va3.data_array[0]), 1)
        self.assertEqual(len(va3.data_array[1]), 1)
        self.assertEqual(va3.data_array[0][0], 1)
        self.assertEqual(va3.data_array[1][0], 2)

        inval = VA(INVALID_VALUE)

        with self.assertRaises(Exception) as context:
            va4 = va3 + inval
        self.assertTrue("Adding NaN!" in str(context.exception))

    def test_string(self):
        va1 = VA(1.0, [1])
        va2 = VA(2.0, [2])
        va3 = va1 + va2
        tstr = str(va3)
        self.assertEqual(tstr, "'3.0', '1', '\n', '2', '\n'")

class TestYMDHData(unittest.TestCase):

    def setUp(self):
        pass

    def test_constants(self):
        pass

    def test_init(self):
        ymdh = YMDHData()
        self.assertEqual(ymdh.dbase, {})

    def test_get_keys_from_time(self):
        ymdh = YMDHData()
        UTC = datetime(2006, 11, 11)
        val = ymdh.get_value(UTC)
        self.assertTrue(isnan(val))
        val = ymdh.get_value("Not a Date")
        self.assertTrue(isnan(val))

    def test_add_ymdh(self):
        UTC = datetime(2006, 1, 2, hour=5)
        ymdh = YMDHData()
        ymdh.add_ymdh(UTC, 3.0, [1, 2, 3, 4])
        UTC = UTC + timedelta(hours=1)
        ymdh.add_ymdh(UTC, 6.0, [5, 6, 7, 8])

        self.assertEqual(len(ymdh.dbase), 1)
        self.assertTrue("2006" in ymdh.dbase.keys())
        self.assertEqual(len(ymdh.dbase["2006"]), 1)
        self.assertTrue("1" in ymdh.dbase["2006"].keys())
        self.assertEqual(len(ymdh.dbase["2006"]["1"]), 1)
        self.assertTrue("2" in ymdh.dbase["2006"]["1"].keys())
        self.assertEqual(len(ymdh.dbase["2006"]["1"]["2"]), 2)
        self.assertTrue("5" in ymdh.dbase["2006"]["1"]["2"].keys())
        self.assertTrue("6" in ymdh.dbase["2006"]["1"]["2"].keys())
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].val, 3.0)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][0], 1)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][1], 2)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][2], 3)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][3], 4)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["6"].val, 6.0)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["6"].data_array[0][0], 5)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["6"].data_array[0][1], 6)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["6"].data_array[0][2], 7)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["6"].data_array[0][3], 8)

    def test_add_ymdh_dup(self):
        UTC = datetime(2006, 1, 2, hour=5)
        ymdh = YMDHData()
        ymdh.add_ymdh(UTC, 3.0, [1, 2, 3, 4])
        ymdh.add_ymdh(UTC, 6.0, [5, 6, 7, 8], ignore_dup=True)

        self.assertEqual(len(ymdh.dbase), 1)
        self.assertTrue("2006" in ymdh.dbase.keys())
        self.assertEqual(len(ymdh.dbase["2006"]), 1)
        self.assertTrue("1" in ymdh.dbase["2006"].keys())
        self.assertEqual(len(ymdh.dbase["2006"]["1"]), 1)
        self.assertTrue("2" in ymdh.dbase["2006"]["1"].keys())
        self.assertEqual(len(ymdh.dbase["2006"]["1"]["2"]), 1)
        self.assertTrue("5" in ymdh.dbase["2006"]["1"]["2"].keys())
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].val, 9.0)
        self.assertEqual(len(ymdh.dbase["2006"]["1"]["2"]["5"].data_array), 2)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][0], 1)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][1], 2)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][2], 3)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][3], 4)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[1][0], 5)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[1][1], 6)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[1][2], 7)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[1][3], 8)

    def test_add_ymdh_dup_fail(self):
        UTC = datetime(2006, 1, 2, hour=5)
        ymdh = YMDHData()
        ymdh.add_ymdh(UTC, 3.0, [1, 2, 3, 4])

        with self.assertRaises(Exception) as context:
            ymdh.add_ymdh(UTC, 6.0, [5, 6, 7, 8])
        print("%s" % str(context.exception))
        self.assertTrue("Duplicate line at time 2006 1 2 5:00!"
                        "Original data '3.0', '1', '2', '3', '4', '\n'"
                        in str(context.exception))

    def test_get_value(self):
        UTC = datetime(2006, 1, 2, hour=5)
        ymdh = YMDHData()
        ymdh.add_ymdh(UTC, 3.0, [1, 2, 3, 4])
        val = ymdh.get_value(UTC)
        self.assertEqual(val, 3.0)
        UTC = datetime(2007, 1, 2, hour=5)
        val = ymdh.get_value(UTC)
        self.assertEqual(val, 3.0)

    def test_get_data(self):
        UTC = datetime(2006, 1, 2, hour=5)
        ymdh = YMDHData()
        ymdh.add_ymdh(UTC, 3.0, [1, 2, 3, 4])
        dat = ymdh.get_data(UTC)
        self.assertEqual(dat.val, 3.0)
        self.assertEqual(len(dat.data_array), 1)
        self.assertEqual(len(dat.data_array[0]), 4)
        self.assertEqual(dat.data_array[0][0], 1)
        self.assertEqual(dat.data_array[0][1], 2)
        self.assertEqual(dat.data_array[0][2], 3)
        self.assertEqual(dat.data_array[0][3], 4)

    def test_duplicate_data(self):
        start_time = datetime(2006, 1, 2, hour=0)
        ymdh = YMDHData()
        for i in range(0, 24):
            UTC = start_time + timedelta(hours=i)
            ymdh.add_ymdh(UTC, i, [i+1, i+2, i+3, i+4])
        interval = timedelta(hours=24)
        new_time = start_time + timedelta(days=5)
        adj = AdjustData()
        ymdh.duplicate_data(start_time, new_time, interval, adj)

        self.assertEqual(len(ymdh.dbase), 1)
        self.assertTrue("2006" in ymdh.dbase.keys())
        self.assertEqual(len(ymdh.dbase["2006"]), 1)
        self.assertTrue("1" in ymdh.dbase["2006"].keys())
        self.assertEqual(len(ymdh.dbase["2006"]["1"]), 2)
        self.assertTrue("2" in ymdh.dbase["2006"]["1"].keys())
        self.assertTrue("7" in ymdh.dbase["2006"]["1"].keys())
        self.assertEqual(len(ymdh.dbase["2006"]["1"]["2"]), 24)
        self.assertEqual(len(ymdh.dbase["2006"]["1"]["7"]), 24)

        for D in ["2", "7"]:
            for i in range(0, 24):
                H = str(i)
                self.assertTrue(H in ymdh.dbase["2006"]["1"][D].keys())
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].val, i)
                self.assertEqual(len(ymdh.dbase["2006"]["1"][D][H].data_array), 1)
                self.assertEqual(len(ymdh.dbase["2006"]["1"][D][H].data_array[0]), 4)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][0], i+1)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][1], i+2)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][2], i+3)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][3], i+4)

    def test_adjust_values(self):
        start_time = datetime(2006, 1, 2, hour=0)
        ymdh = YMDHData()
        for i in range(0, 24):
            UTC = start_time + timedelta(hours=i)
            ymdh.add_ymdh(UTC, (i+1) * 100, [i+1, i+2, i+3, i+4])
        interval = timedelta(hours=24)
        new_time = start_time + timedelta(days=5)
        adj = AdjustData()
        ymdh.duplicate_data(start_time, new_time, interval, adj)
        adj = AdjustData(abs_adj=100, ratio=1.1)
        ymdh.adjust_values(start_time, interval, adj)

        self.assertEqual(len(ymdh.dbase), 1)
        self.assertTrue("2006" in ymdh.dbase.keys())
        self.assertEqual(len(ymdh.dbase["2006"]), 1)
        self.assertTrue("1" in ymdh.dbase["2006"].keys())
        self.assertEqual(len(ymdh.dbase["2006"]["1"]), 2)
        self.assertTrue("2" in ymdh.dbase["2006"]["1"].keys())
        self.assertTrue("7" in ymdh.dbase["2006"]["1"].keys())
        self.assertEqual(len(ymdh.dbase["2006"]["1"]["2"]), 24)
        self.assertEqual(len(ymdh.dbase["2006"]["1"]["7"]), 24)

        for D in ["2", "7"]:
            for i in range(0, 24):
                H = str(i)
                self.assertTrue(H in ymdh.dbase["2006"]["1"][D].keys())
                self.assertEqual(len(ymdh.dbase["2006"]["1"][D][H].data_array), 1)
                self.assertEqual(len(ymdh.dbase["2006"]["1"][D][H].data_array[0]), 4)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][0], i+1)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][1], i+2)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][2], i+3)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][3], i+4)

        D2 = "2"
        D7 = "7"
        for i in range(0, 24):
            H = str(i)
            self.assertEqual(ymdh.dbase["2006"]["1"][D2][H].val, 
                             (ymdh.dbase["2006"]["1"][D7][H].val * 1.1) + 100)
