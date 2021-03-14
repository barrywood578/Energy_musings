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
        self.assertTrue(ymdh.min_time is None)
        self.assertTrue(ymdh.max_time is None)

    def test_get_keys_from_time(self):
        ymdh = YMDHData()
        UTC = datetime(2006, 11, 11)
        val = ymdh.get_value(UTC)
        self.assertTrue(isnan(val))
        val = ymdh.get_value("Not a Date")
        self.assertTrue(isnan(val))

    def test_is_empty(self):
        ymdh = YMDHData()
        self.assertTrue(ymdh.is_empty())

        UTC = datetime(2006, 1, 2, hour=5)
        Y, M, D, H = ymdh._get_keys_from_time(UTC)
        ymdh.add_ymdh(UTC, 3.0, [Y, M, D, H, Y, M, D, H, 3.0])
        self.assertFalse(ymdh.is_empty())

    def test_add_ymdh(self):
        UTC = datetime(2006, 1, 2, hour=5)
        ymdh = YMDHData()
        Y, M, D, H = ymdh._get_keys_from_time(UTC)
        ymdh.add_ymdh(UTC, 3.0, [Y, M, D, H, 1, 2, 3, 4, 3.0])
        UTC = UTC + timedelta(hours=1)
        Y, M, D, H = ymdh._get_keys_from_time(UTC)
        ymdh.add_ymdh(UTC, 6.0, [Y, M, D, H, 5, 6, 7, 8, 6.0])

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
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][0], "2006")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][1], "1")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][2], "2")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][3], "5")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][4], 1)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][5], 2)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][6], 3)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][7], 4)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][8], 3)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["6"].val, 6.0)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["6"].data_array[0][0], "2006")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["6"].data_array[0][1], "1")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["6"].data_array[0][2], "2")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["6"].data_array[0][3], "6")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["6"].data_array[0][4], 5)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["6"].data_array[0][5], 6)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["6"].data_array[0][6], 7)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["6"].data_array[0][7], 8)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["6"].data_array[0][8], 6)

    def test_add_ymdh_dup(self):
        UTC = datetime(2006, 1, 2, hour=5)
        ymdh = YMDHData()
        Y, M, D, H = ymdh._get_keys_from_time(UTC)
        ymdh.add_ymdh(UTC, 3.0, [Y, M, D, H, 1, 2, 3, 4, 3.0])
        ymdh.add_ymdh(UTC, 6.0, [Y, M, D, H, 5, 6, 7, 8, 6.0], ignore_dup=True)

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
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][0], "2006")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][1], "1")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][2], "2")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][3], "5")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][4], 1)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][5], 2)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][6], 3)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][7], 4)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[0][8], 3)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[1][0], "2006")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[1][1], "1")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[1][2], "2")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[1][3], "5")
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[1][4], 5)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[1][5], 6)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[1][6], 7)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[1][7], 8)
        self.assertEqual(ymdh.dbase["2006"]["1"]["2"]["5"].data_array[1][8], 6)

    def test_add_ymdh_dup_fail(self):
        UTC = datetime(2006, 1, 2, hour=5)
        ymdh = YMDHData()
        Y, M, D, H = ymdh._get_keys_from_time(UTC)
        ymdh.add_ymdh(UTC, 3.0, [Y, M, D, H, Y, M, D, H, 3.0])

        with self.assertRaises(Exception) as context:
            ymdh.add_ymdh(UTC, 6.0, [Y, M, D, H, Y, M, D, H, 6.0])
        print("%s" % str(context.exception))
        self.assertTrue("Duplicate line at time 2006 1 2 5:00!"
                        "Original data '3.0', '2006', '1', '2', '5', '2006', '1', '2', '5', '3.0', '\n'"
                        in str(context.exception))

    def test_iterator(self):
        file_data= [['2000', '1', '3', '7', '2000', '1', '2', '7', '123000.0'],
                    ['2000', '1', '3', '8', '2000', '2', '3', '8', '12300.0'],
                    ['2000', '1', '4', '9', '2000', '3', '4', '9', '1230.0'],
                    ['2000', '1', '4', '10', '2000', '4', '5', '10', '123.0'],
                    ['2000', '2', '5', '11', '2000', '5', '6', '11', '12.3'],
                    ['2000', '2', '5', '12', '2000', '6', '7', '12', '1.23'],
                    ['2000', '2', '6', '13', '2000', '7', '8', '13', '345.0'],
                    ['2000', '2', '6', '14', '2000', '8', '9', '14', '100000.0']]
        ymdh = YMDHData()
        for data in file_data:
            UTC = datetime(int(data[0]), int(data[1]), int(data[2]), hour=int(data[3]))
            ymdh.add_ymdh(UTC, float(data[8]), data)

        for i, data in enumerate(ymdh):
            self.assertEqual(data.val, float(file_data[i][8]))
            for d_tok, y_tok in zip(data.data_array[0], file_data[i]):
                self.assertEqual(d_tok, y_tok)

    def test_get_subset(self):
        def check_test(subset, exp_subset):
            self.assertEqual(len(subset), len(exp_subset))
            for x, y in zip(subset, exp_subset):
                self.assertEqual(x, y)

        data = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        ymdh = YMDHData()
        # checking first of 3 keys
        testset = ymdh._get_subset(data, True, False, 5, 6)
        exp_testset = data[5:]
        check_test(testset, exp_testset)

        # checking middle of 3 keys
        testset = ymdh._get_subset(data, False, False, 5, 6)
        exp_testset = data
        check_test(testset, exp_testset)

        # checking last of 3 keys
        testset = ymdh._get_subset(data, False, True, 5, 6)
        exp_testset = data[:7]
        check_test(testset, exp_testset)

        # checking first of 2 keys
        testset = ymdh._get_subset(data, True, False, 5, 6)
        exp_testset = data[5:]
        check_test(testset, exp_testset)

        # checking last of 2 keys
        testset = ymdh._get_subset(data, False, True, 5, 6)
        exp_testset = data[:7]
        check_test(testset, exp_testset)

        # checking only key, all values allowed
        testset = ymdh._get_subset(data, True, True, 0, 9)
        exp_testset = data
        check_test(testset, exp_testset)

        # checking only key, subrange allowed
        testset = ymdh._get_subset(data, True, True, 5, 6)
        exp_testset = data[5:7]
        check_test(testset, exp_testset)

        # checking only key, subrange allowed
        testset = ymdh._get_subset(data, True, True, 5, 5)
        exp_testset = data[5:6]
        check_test(testset, exp_testset)

    def test_gen_func(self):
        file_data= [['2000', '1', '1', '1', '2000', '1', '2', '7', '123000.0'],
                    ['2000', '1', '1', '23', '2000', '2', '3', '8', '12300.0'],
                    ['2000', '1', '2', '1', '2000', '3', '4', '9', '1230.0'],
                    ['2000', '1', '30', '1', '2000', '4', '5', '10', '123.0'],
                    ['2000', '1', '30', '23', '2000', '4', '5', '10', '123.0'],
                    ['2000', '2', '5', '11', '2000', '5', '6', '11', '12.3'],
                    ['2000', '2', '5', '12', '2000', '6', '7', '12', '1.23'],
                    ['2000', '2', '6', '13', '2000', '7', '8', '13', '345.0'],
                    ['2000', '2', '6', '14', '2000', '8', '9', '14', '100000.0'],
                    ['2000', '12', '1', '1', '2000', '5', '6', '11', '12.3'],
                    ['2000', '12', '31', '5', '2000', '7', '8', '13', '345.0'],
                    ['2000', '12', '31', '23', '2000', '6', '7', '12', '1.23'],
                    ['2001', '1', '3', '7', '2000', '1', '2', '7', '123000.0'],
                    ['2001', '1', '3', '8', '2000', '2', '3', '8', '12300.0'],
                    ['2001', '1', '4', '9', '2000', '3', '4', '9', '1230.0'],
                    ['2001', '1', '4', '10', '2000', '4', '5', '10', '123.0'],
                    ['2001', '2', '5', '11', '2000', '5', '6', '11', '12.3'],
                    ['2001', '2', '5', '12', '2000', '6', '7', '12', '1.23'],
                    ['2001', '2', '6', '13', '2000', '7', '8', '13', '345.0'],
                    ['2001', '2', '6', '14', '2000', '8', '9', '14', '100000.0'],
                    ['2001', '12', '31', '1', '2000', '7', '8', '13', '345.0'],
                    ['2001', '12', '31', '5', '2000', '7', '8', '13', '345.0'],
                    ['2001', '12', '31', '23', '2000', '8', '9', '14', '100000.0']]
        ymdh = YMDHData()
        for data in file_data:
            UTC = datetime(int(data[0]), int(data[1]), int(data[2]), hour=int(data[3]))
            ymdh.add_ymdh(UTC, float(data[-1]), data)

        count = 0
        st_dt = datetime(2000, 1, 1, hour=0)
        end_dt = datetime(2001, 1, 2, hour=0)
        interval = end_dt - st_dt
        print("Date: %s Interval %s EndDate %s" % (st_dt.strftime(DATE_FORMAT), str(interval),
                                                   (st_dt + interval).strftime(DATE_FORMAT)))
        for data in ymdh.gen_func(st_dt, interval):
            print("    %d %s" % (count, ",".join(data.data_array[0])))
            for x, y in zip(data.data_array[0], file_data[count]):
                self.assertEqual(x, y)
            dt = ymdh._get_UTC_from_va(data)
            self.assertEqual(dt.year, 2000)
            count += 1
        self.assertEqual(count, 12)

        count = 0
        st_dt = datetime(2000, 12, 31, hour=23)
        end_dt = datetime(2001, 1, 1, hour=0)
        interval = end_dt - st_dt
        print("Date: %s Interval %s EndDate %s" % (st_dt.strftime(DATE_FORMAT), str(interval),
                                                   (st_dt + interval).strftime(DATE_FORMAT)))
        for data in ymdh.gen_func(st_dt, interval):
            print("    %d %s" % (count, ",".join(data.data_array[0])))
            for x, y in zip(data.data_array[0], file_data[count+11]):
                self.assertEqual(x, y)
            dt = ymdh._get_UTC_from_va(data)
            self.assertEqual(dt.year, 2000)
            count += 1
        self.assertEqual(count, 1)

        count = 0
        st_dt = datetime(2000, 2, 1, hour=0)
        end_dt = datetime(2000, 3, 1, hour=0)
        interval = end_dt - st_dt
        print("Date: %s Interval %s EndDate %s" % (st_dt.strftime(DATE_FORMAT), str(interval),
                                                   (st_dt + interval).strftime(DATE_FORMAT)))
        for data in ymdh.gen_func(st_dt, interval):
            print("    %d %s" % (count, ",".join(data.data_array[0])))
            for x, y in zip(data.data_array[0], file_data[count+5]):
                self.assertEqual(x, y)
            dt = ymdh._get_UTC_from_va(data)
            self.assertEqual(dt.year, 2000)
            count += 1
        self.assertEqual(count, 4)

        count = 0
        st_dt = datetime(2001, 1, 1, hour=0)
        end_dt = datetime(2002, 1, 1, hour=0)
        interval = end_dt - st_dt
        print("Date: %s Interval %s EndDate %s" % (st_dt.strftime(DATE_FORMAT), str(interval),
                                                   (st_dt + interval).strftime(DATE_FORMAT)))
        for data in ymdh.gen_func(st_dt, interval):
            print("    %d %s" % (count, ",".join(data.data_array[0])))
            for x, y in zip(data.data_array[0], file_data[count+12]):
                self.assertEqual(x, y)
            dt = ymdh._get_UTC_from_va(data)
            self.assertEqual(dt.year, 2001)
            count += 1
        self.assertEqual(count, 11)

        count = 0
        st_dt = datetime(2001, 12, 1, hour=0)
        end_dt = datetime(2002, 1, 1, hour=0)
        interval = end_dt - st_dt
        print("Date: %s Interval %s EndDate %s" % (st_dt.strftime(DATE_FORMAT), str(interval),
                                                   (st_dt + interval).strftime(DATE_FORMAT)))
        for data in ymdh.gen_func(st_dt, interval):
            print("    %d %s" % (count, ",".join(data.data_array[0])))
            for x, y in zip(data.data_array[0], file_data[count+20]):
                self.assertEqual(x, y)
            dt = ymdh._get_UTC_from_va(data)
            self.assertEqual(dt.year, 2001)
            count += 1
        self.assertEqual(count, 3)

    def test_get_value(self):
        UTC = datetime(2006, 1, 2, hour=5)
        ymdh = YMDHData()
        Y, M, D, H = ymdh._get_keys_from_time(UTC)
        ymdh.add_ymdh(UTC, 3.0, [Y, M, D, H, Y, M, D, H, 3.0])
        val = ymdh.get_value(UTC)
        self.assertEqual(val, 3.0)
        UTC = datetime(2007, 1, 2, hour=5)
        val = ymdh.get_value(UTC)
        self.assertTrue(isnan(val))

    def test_get_data(self):
        UTC = datetime(2006, 1, 2, hour=5)
        ymdh = YMDHData()
        Y, M, D, H = ymdh._get_keys_from_time(UTC)
        ymdh.add_ymdh(UTC, 3.0, [Y, M, D, H, Y, M, D, H, 3.0])
        dat = ymdh.get_data(UTC)
        self.assertEqual(dat.val, 3.0)
        self.assertEqual(len(dat.data_array), 1)
        self.assertEqual(len(dat.data_array[0]), 9)
        self.assertEqual(dat.data_array[0][0], Y)
        self.assertEqual(dat.data_array[0][1], M)
        self.assertEqual(dat.data_array[0][2], D)
        self.assertEqual(dat.data_array[0][3], H)
        self.assertEqual(dat.data_array[0][4], Y)
        self.assertEqual(dat.data_array[0][5], M)
        self.assertEqual(dat.data_array[0][6], D)
        self.assertEqual(dat.data_array[0][7], H)
        self.assertEqual(dat.data_array[0][8], 3.0)

    def test_duplicate_data(self):
        start_time = datetime(2006, 1, 2, hour=0)
        ymdh = YMDHData()
        for i in range(0, 24):
            UTC = start_time + timedelta(hours=i)
            y, m, d, h = ymdh._get_keys_from_time(UTC)
            ymdh.add_ymdh(UTC, i+4, [y, m, d, h, i, i+1, i+2, i+3, i+4])
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
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].val, i + 4)
                self.assertEqual(len(ymdh.dbase["2006"]["1"][D][H].data_array), 1)
                self.assertEqual(len(ymdh.dbase["2006"]["1"][D][H].data_array[0]), 9)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][-4], i+1)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][-3], i+2)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][-2], i+3)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][-1], i+4)
        for h in range(0, 24):
            H = str(h)
            self.assertTrue(
                        ymdh.dbase["2006"]["1"]["2"][H].data_array[0][8] is
                        ymdh.dbase["2006"]["1"]["7"][H].data_array[0][8])
            for i in range(0, 4):
                print("%d %d" % (h, i))
                self.assertFalse(
                        ymdh.dbase["2006"]["1"]["2"][H].data_array[0][i] is
                        ymdh.dbase["2006"]["1"]["7"][H].data_array[0][i])
                self.assertTrue(
                        ymdh.dbase["2006"]["1"]["2"][H].data_array[0][i+4] is
                        ymdh.dbase["2006"]["1"]["7"][H].data_array[0][i+4])


    def test_adjust_values(self):
        start_time = datetime(2006, 1, 2, hour=0)
        ymdh = YMDHData()
        for i in range(0, 24):
            UTC = start_time + timedelta(hours=i)
            ymdh.add_ymdh(UTC, (i+1) * 100, ["2006", "1", "2", str(i), i+1, i+2, i+3, i+4, (i+1) * 100])
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
                self.assertEqual(len(ymdh.dbase["2006"]["1"][D][H].data_array[0]), 9)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][0], "2006")
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][1], "1")
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][2], D)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][3], H)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][4], i+1)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][5], i+2)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][6], i+3)
                self.assertEqual(ymdh.dbase["2006"]["1"][D][H].data_array[0][7], i+4)

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
            Y, M, D, H = ymdh._get_keys_from_time(UTC)
            val = (i+1) * 100
            ymdh.add_ymdh(UTC, val, [Y, M, D, H, Y, M, D, H, val])

            UTC = start_time + timedelta(hours=i+48)
            Y, M, D, H = ymdh._get_keys_from_time(UTC)
            ymdh.add_ymdh(UTC, val, [Y, M, D, H, Y, M, D, H, val])

            UTC = start_time + timedelta(hours=i+96)
            Y, M, D, H = ymdh._get_keys_from_time(UTC)
            ymdh.add_ymdh(UTC, val, [Y, M, D, H, Y, M, D, H, val])

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
            y, m, d, h = ymdh._get_keys_from_time(UTC)
            ymdh.add_ymdh(UTC, i+1, [y, m, d, h, y, m, d, h, i+4])

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
                Y, M, D, H = ymdh._get_keys_from_time(UTC)
                ymdh.add_ymdh(UTC, i+1, [Y, M, D, H, Y, M, D, H, i+1])

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
        abs_adj = 1
        ratio_adj = 1.1

        def local_check(d, h):
            offset = timedelta(days=d, hours=h)
            src_data = ymdh.get_data(start_time + offset)
            trg_data = ymdh.get_data(target_time + offset)
            self.assertEqual(len(src_data.data_array), len(trg_data.data_array))
            for src, trg in zip(src_data.data_array, trg_data.data_array):
                self.assertTrue(src[0] in ["2006", "2007"])
                self.assertEqual(trg[0], "2019")
                self.assertEqual(src[8], trg[8])
                self.assertTrue(src[8] is trg[8])
                for i in range(1, 4):
                    self.assertEqual(src[i], trg[i])
                    self.assertEqual(src[i+4], trg[i+4])
                    self.assertFalse(src[i] is trg[i])
                    self.assertTrue(src[i+4] is trg[i+4])
            self.assertFalse(src_data is trg_data)
            self.assertFalse(src_data.val is trg_data.val)
            self.assertEqual((trg_data.val * ratio_adj) + abs_adj, src_data.val)

        hr_offset = 5
        start_time = datetime(2006, 1, 1, hour=hr_offset)
        ymdh = YMDHData()
        # Create a year long range of data
        for day in range(0, 365):
            for hour in range(0, 24):
                UTC = start_time + timedelta(days=day, hours=hour)
                y, m, d, h = ymdh._get_keys_from_time(UTC)
                i = (int(d)*24) + int(h)
                ymdh.add_ymdh(UTC, i+4, [y, m, d, h, y, m, d, h, i+4])

        target_time = datetime(2019, 1, 1, hour=0)
        interval = timedelta(days=365)

        ymdh.create_base(target_time, interval)
        adj = AdjustData(abs_adj=abs_adj, ratio=ratio_adj)
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
