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

    def test_verify_range(self):
        start_time = datetime(2006, 1, 2, hour=0)
        ymdh = YMDHData()
        for i in range(0, 24):
            UTC = start_time + timedelta(hours=i)
            ymdh.add_ymdh(UTC, (i+1) * 100, [i+1, i+2, i+3, i+4])

            UTC = start_time + timedelta(hours=i+48)
            ymdh.add_ymdh(UTC, (i+1) * 100 + 48, [i+1, i+2, i+3, i+4])

            UTC = start_time + timedelta(hours=i+96)
            ymdh.add_ymdh(UTC, (i+1) * 100 + 96, [i+1, i+2, i+3, i+4])

        start_time = datetime(2006, 1, 1, hour=0)
        missing = ymdh.verify_range(start_time, timedelta(days=5))
        interval = timedelta(hours=24)
        self.assertEqual(len(missing), 3)
        self.assertEqual(missing[0][0], start_time)
        self.assertEqual(missing[0][1], interval)
        self.assertEqual(missing[1][0], start_time + interval + interval)
        self.assertEqual(missing[1][1], interval)
        self.assertEqual(missing[2][0], start_time + interval + interval + interval + interval)
        self.assertEqual(missing[2][1], interval)

    def test_copy_nearest(self):
        start_time = datetime(2006, 1, 1, hour=5)
        ymdh = YMDHData()
        # Create a year long range of data
        for i in range(0, 24*365):
            UTC = start_time + timedelta(hours=i)
            ymdh.add_ymdh(UTC, i+1, [i+1, i+2, i+3, i+4])

        # Create a copy of that data for a New Year
        start_time = datetime(2020, 1, 1, hour=0)
        missing = ymdh.verify_range(start_time, timedelta(hours=24*365))
        for miss_u, miss_i in missing:
            ymdh.copy_nearest(miss_u, miss_i)

    def test_determine_nearest_time(self):
        start_time = datetime(2006, 1, 1, hour=5)
        ymdh = YMDHData()
        # Create a year long range of data
        for d in range(0, 365):
            for h in range(0, 24):
                UTC = start_time + timedelta(days=d, hours=h)
                i = (d*24) + h
                ymdh.add_ymdh(UTC, i+1, [i+1, i+2, i+3, i+4])

        UTC = datetime(2019, 1, 1, hour=0)
        for i in range(0, 24*365):
            target_time = UTC + timedelta(hours=i)
            src_time = ymdh._determine_nearest_time(target_time)
            y, m, d, h = ymdh._get_keys_from_time(src_time)
            Y, M, D, H = ymdh._get_keys_from_time(target_time)
            self.assertNotEqual(y, Y)
            self.assertEqual(m, M)
            self.assertEqual(d, D)
            self.assertEqual(h, H)
            self.assertTrue(y in ymdh.dbase.keys())

    def test_create_base(self):
        def local_check(d, h):
            offset = timedelta(days=d, hours=h)
            src_data = ymdh.get_data(start_time + offset)
            trg_data = ymdh.get_data(target_time + offset)
            self.assertEqual((trg_data.val * 1.1) + 1, src_data.val)
            self.assertEqual(len(src_data.data_array), len(trg_data.data_array))
            for x, y in zip (src_data.data_array, trg_data.data_array):
                self.assertEqual(x, y)
                self.assertFalse(x is y)

        hr_offset = 5
        start_time = datetime(2006, 1, 1, hour=hr_offset)
        ymdh = YMDHData()
        # Create a year long range of data
        for d in range(0, 365):
            for h in range(0, 24):
                UTC = start_time + timedelta(days=d, hours=h)
                i = (d*24) + h
                ymdh.add_ymdh(UTC, i+1, [i+1, i+2, i+3, i+4])

        target_time = datetime(2019, 1, 1, hour=0)
        interval = timedelta(days=365)

        ymdh.create_base(target_time, interval)
        adj = AdjustData(abs_adj=1, ratio=1.1)
        ymdh.adjust_values(start_time, interval, adj)

        target_time = datetime(2019, 1, 1, hour=hr_offset)
        for d in range(0, 365):
            for h in range(0, 24):
                local_check(d, h)
                if d == 364 and h == (23 - hr_offset):
                    break
            if d == 364 and h == (23 - hr_offset):
                break

        start_time = datetime(2007, 1, 1, hour=0)
        target_time = datetime(2019, 1, 1, hour=0)
        d = 0
        for h in range(0, hr_offset):
            local_check(d, h)
