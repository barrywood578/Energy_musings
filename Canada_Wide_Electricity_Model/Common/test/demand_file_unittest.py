#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Unit test for demand file.

"""

from demand_file import DemandFile
from adjust_data import AdjustData
from datetime import datetime, timezone, timedelta
from common_defs import *
from math import ceil, isnan
import sys

import unittest
import mock
from unittest.mock import patch, mock_open, call

class TestDemandFile(unittest.TestCase):
    file_header = ("File, LineNum, UTC_Year, UTC_Month, "
                   "UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)")

    def setUp(self):
        pass

    def test_constants(self):
        demand = DemandFile()
        self.assertEqual(demand.file_header, self.file_header)
        self.assertEqual(demand.token_count, 11)

    def test_init(self):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6851.0'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = DemandFile()
            self.assertEqual(df.lines, [])
            self.assertEqual(df.dbase, {})
            self.assertFalse(mock_file.called)

    def test_init_with_file(self):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6599.9'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = DemandFile("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.lines), 2)
            self.assertEqual(df.lines[0][0], "TestFile")
            self.assertEqual(df.lines[0][1], 1)
            self.assertEqual(df.lines[0][2], "test1.xlsx")
            self.assertEqual(df.lines[0][3], "1")
            self.assertEqual(df.lines[0][4], "2006")
            self.assertEqual(df.lines[0][5], "11")
            self.assertEqual(df.lines[0][6], "2")
            self.assertEqual(df.lines[0][7], "8")
            self.assertEqual(df.lines[0][8], "2006")
            self.assertEqual(df.lines[0][9], "3")
            self.assertEqual(df.lines[0][10], "4")
            self.assertEqual(df.lines[0][11], "5")
            self.assertEqual(df.lines[0][12], "6851.0")
            self.assertEqual(df.lines[1][0], "TestFile")
            self.assertEqual(df.lines[1][1], 2)
            self.assertEqual(df.lines[1][2], "test2.xlsx")
            self.assertEqual(df.lines[1][3], "2")
            self.assertEqual(df.lines[1][4], "2006")
            self.assertEqual(df.lines[1][5], "12")
            self.assertEqual(df.lines[1][6], "3")
            self.assertEqual(df.lines[1][7], "9")
            self.assertEqual(df.lines[1][8], "2006")
            self.assertEqual(df.lines[1][9], "6")
            self.assertEqual(df.lines[1][10], "7")
            self.assertEqual(df.lines[1][11], "8")
            self.assertEqual(df.lines[1][12], "6599.9")

    def test_init_with_bad_file_header(self):
        file_data = ("Bad Header!\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6851.0'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            with self.assertRaises(Exception) as context:
                df = DemandFile("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertTrue( ("File header is 'Bad Header!', not "
                              "'File, LineNum, UTC_Year, UTC_Month, UTC_Day, "
                              "UTC_Hour, Year, Month, Day, Hour, Load(MW)'.  Halting.")
                              in str(context.exception))

    def test_read_hourly_mw_file_success(self):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6580.0'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = DemandFile()
            self.assertFalse(mock_file.called)
            df.read_hourly_mw_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.lines), 2)
            self.assertEqual(df.lines[0][0], "TestFile")
            self.assertEqual(df.lines[0][1], 1)
            self.assertEqual(df.lines[0][2], "test1.xlsx")
            self.assertEqual(df.lines[0][3], "1")
            self.assertEqual(df.lines[0][4], "2006")
            self.assertEqual(df.lines[0][5], "11")
            self.assertEqual(df.lines[0][6], "2")
            self.assertEqual(df.lines[0][7], "8")
            self.assertEqual(df.lines[0][8], "2006")
            self.assertEqual(df.lines[0][9], "3")
            self.assertEqual(df.lines[0][10], "4")
            self.assertEqual(df.lines[0][11], "5")
            self.assertEqual(df.lines[0][12], "6851.0")
            self.assertEqual(df.lines[1][0], "TestFile")
            self.assertEqual(df.lines[1][1], 2)
            self.assertEqual(df.lines[1][2], "test2.xlsx")
            self.assertEqual(df.lines[1][3], "2")
            self.assertEqual(df.lines[1][4], "2006")
            self.assertEqual(df.lines[1][5], "12")
            self.assertEqual(df.lines[1][6], "3")
            self.assertEqual(df.lines[1][7], "9")
            self.assertEqual(df.lines[1][8], "2006")
            self.assertEqual(df.lines[1][9], "6")
            self.assertEqual(df.lines[1][10], "7")
            self.assertEqual(df.lines[1][11], "8")
            self.assertEqual(df.lines[1][12], "6580.0")

    def test_read_hourly_mw_file_bad_file_delim(self):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "Xtest2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6899.0Y\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = DemandFile()
            self.assertFalse(mock_file.called)
            with self.assertRaises(Exception) as context:
                df.read_hourly_mw_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.lines), 1)
            self.assertEqual(df.lines[0][0], "TestFile")
            self.assertEqual(df.lines[0][1], 1)
            self.assertEqual(df.lines[0][2], "test1.xlsx")
            self.assertEqual(df.lines[0][3], "1")
            self.assertEqual(df.lines[0][4], "2006")
            self.assertEqual(df.lines[0][5], "11")
            self.assertEqual(df.lines[0][6], "2")
            self.assertEqual(df.lines[0][7], "8")
            self.assertEqual(df.lines[0][8], "2006")
            self.assertEqual(df.lines[0][9], "3")
            self.assertEqual(df.lines[0][10], "4")
            self.assertEqual(df.lines[0][11], "5")
            self.assertEqual(df.lines[0][12], "6851.0")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertTrue( ("File TestFile Line 2 delimiters "
                              "'X' 'Y' not ''''''. Halting.")
                             in str(context.exception))

    @patch('builtins.print')
    def test_read_hourly_mw_file_bad_line(self, mock_print):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '6', '7', '8', '6851.0'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = DemandFile()
            self.assertFalse(mock_file.called)
            with self.assertRaises(Exception) as context:
                df.read_hourly_mw_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.lines), 1)
            self.assertEqual(df.lines[0][0], "TestFile")
            self.assertEqual(df.lines[0][1], 1)
            self.assertEqual(df.lines[0][2], "test1.xlsx")
            self.assertEqual(df.lines[0][3], "1")
            self.assertEqual(df.lines[0][4], "2006")
            self.assertEqual(df.lines[0][5], "11")
            self.assertEqual(df.lines[0][6], "2")
            self.assertEqual(df.lines[0][7], "8")
            self.assertEqual(df.lines[0][8], "2006")
            self.assertEqual(df.lines[0][9], "3")
            self.assertEqual(df.lines[0][10], "4")
            self.assertEqual(df.lines[0][11], "5")
            self.assertEqual(df.lines[0][12], "6851.0")
            mock_file.assert_called_with("TestFile", 'r')
            #print("\n%s" % str(context.exception))
            self.assertTrue(("File TestFile Line 2 Bad format "
                             "''test2.xlsx', '2', '2006', '12', '3', "
                             "'9', '6', '7', '8', '6851.0''")
                             in str(context.exception))

    @patch('builtins.print')
    def test_write_hourly_mw_file(self, mock_print):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6875.0'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = DemandFile("TestFile")
            self.assertTrue(mock_file.called)
            mock_file.assert_called_with("TestFile", 'r')
            df.write_hourly_mw_file()
            calls = [call(('File, LineNum, UTC_Year, UTC_Month, '
                           'UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)'),
                           file=sys.stdout),
                     call(("'test1.xlsx', '1', '2006', '11', '2', "
                           "'8', '2006', '3', '4', '5', '6851.0'"),
                           file=sys.stdout),
                     call(("'test2.xlsx', '2', '2006', '12', '3', "
                           "'9', '2006', '6', '7', '8', '6875.0'"),
                           file=sys.stdout)]
            mock_print.assert_has_calls(calls, any_order = False)

    def test_get_mw_hour_success(self):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6580.0'\n"
        "'test3.xlsx', '3', '2006', '03', '04', '10', '2006', '06', '07', '8', '4562.0'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = DemandFile()
            self.assertFalse(mock_file.called)
            df.read_hourly_mw_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.lines), 3)
            self.assertEqual(len(df.dbase.keys()), 1)
            self.assertTrue("2006" in df.dbase.keys())

            UTC = datetime(2006, 11, 2, hour=8, tzinfo=timezone.utc)
            self.assertEqual(df.get_mw_hour(UTC), 6851.0)
            UTC = datetime(2006, 12, 3, hour=9, tzinfo=timezone.utc)
            self.assertEqual(df.get_mw_hour(UTC), 6580.0)
            UTC = datetime(2006, 3, 4, hour=10, tzinfo=timezone.utc)
            self.assertEqual(df.get_mw_hour(UTC), 4562.0)

    def test_get_mw_hour_failure(self):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6580.0'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = DemandFile()
            self.assertFalse(mock_file.called)
            df.read_hourly_mw_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.lines), 2)
            UTC = datetime(2021,9, 2, hour=8, tzinfo=timezone.utc)
            self.assertTrue(isnan(df.get_mw_hour(UTC)))
            UTC = datetime(2006,9, 2, hour=8, tzinfo=timezone.utc)
            self.assertTrue(isnan(df.get_mw_hour(UTC)))
            UTC = datetime(2006,9, 3, hour=8, tzinfo=timezone.utc)
            self.assertTrue(isnan(df.get_mw_hour(UTC)))
            UTC = datetime(2006,9, 2, hour=7, tzinfo=timezone.utc)
            self.assertTrue(isnan(df.get_mw_hour(UTC)))

    def test_duplicate_mw_hours(self):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '1', '1', '0', '2006', '1', '1', '0', '100.0'\n"
        "'test1.xlsx', '2', '2006', '1', '1', '1', '2006', '1', '1', '1', '101.0'\n"
        "'test1.xlsx', '3', '2006', '1', '1', '2', '2006', '1', '1', '2', '102.0'\n"
        "'test1.xlsx', '4', '2006', '1', '1', '3', '2006', '1', '1', '3', '103.0'\n"
        "'test1.xlsx', '5', '2006', '1', '1', '4', '2006', '1', '1', '4', '104.0'\n"
        "'test1.xlsx', '6', '2006', '1', '1', '5', '2006', '1', '1', '5', '105.0'\n"
        "'test1.xlsx', '7', '2006', '1', '1', '6', '2006', '1', '1', '6', '106.0'\n"
        "'test1.xlsx', '8', '2006', '1', '1', '7', '2006', '1', '1', '7', '107.0'\n"
        "'test1.xlsx', '9', '2006', '1', '1', '8', '2006', '1', '1', '8', '108.0'\n"
        "'test1.xlsx', '10', '2006', '1', '1', '9', '2006', '1', '1', '9', '109.0'\n"
        "'test1.xlsx', '11', '2006', '1', '1', '10', '2006', '1', '1', '10', '110.0'\n"
        "'test1.xlsx', '12', '2006', '1', '1', '11', '2006', '1', '1', '11', '120.0'\n"
        "'test1.xlsx', '13', '2006', '1', '1', '12', '2006', '1', '1', '12', '130.0'\n"
        "'test1.xlsx', '14', '2006', '1', '1', '13', '2006', '1', '1', '13', '140.0'\n"
        "'test1.xlsx', '15', '2006', '1', '1', '14', '2006', '1', '1', '14', '150.0'\n"
        "'test1.xlsx', '16', '2006', '1', '1', '15', '2006', '1', '1', '15', '160.0'\n"
        "'test1.xlsx', '17', '2006', '1', '1', '16', '2006', '1', '1', '16', '170.0'\n"
        "'test1.xlsx', '18', '2006', '1', '1', '17', '2006', '1', '1', '17', '180.0'\n"
        "'test1.xlsx', '19', '2006', '1', '1', '18', '2006', '1', '1', '18', '190.0'\n"
        "'test1.xlsx', '20', '2006', '1', '1', '19', '2006', '1', '1', '19', '200.0'\n"
        "'test1.xlsx', '21', '2006', '1', '1', '20', '2006', '1', '1', '20', '210.0'\n"
        "'test1.xlsx', '22', '2006', '1', '1', '21', '2006', '1', '1', '21', '220.0'\n"
        "'test1.xlsx', '23', '2006', '1', '1', '22', '2006', '1', '1', '22', '230.0'\n"
        "'test1.xlsx', '24', '2006', '1', '1', '23', '2006', '1', '1', '23', '240.0'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = DemandFile()
            self.assertFalse(mock_file.called)
            df.read_hourly_mw_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.lines), 24)

            src_time = datetime(2006, 1, 1, hour=0)
            interval = timedelta(hours=24)
            new_time = src_time + interval
            adj = AdjustData()
            df.duplicate_mw_hours(src_time, new_time, interval, adj)

            self.assertEqual(len(df.lines), 24)
            self.assertEqual(len(df.dbase.keys()), 1)
            self.assertTrue("2006" in df.dbase.keys())
            self.assertEqual(len(df.dbase["2006"].keys()), 1)
            self.assertTrue("1" in df.dbase["2006"].keys())
            self.assertEqual(len(df.dbase["2006"]["1"].keys()), 2)
            self.assertTrue("1" in df.dbase["2006"]["1"].keys())
            self.assertTrue("2" in df.dbase["2006"]["1"].keys())
            self.assertEqual(len(df.dbase["2006"]["1"]["1"].keys()), 24)
            self.assertEqual(len(df.dbase["2006"]["1"]["2"].keys()), 24)
            for hour in range (0, 24):
                self.assertEqual(df.dbase["2006"]["1"]["1"][str(hour)].val,
                                 df.dbase["2006"]["1"]["2"][str(hour)].val)

            interval = timedelta(hours=48)
            new_time = src_time + interval
            adj = AdjustData(abs_adj=100, ratio=1.1)
            df.duplicate_mw_hours(src_time, new_time, interval, adj)

            self.assertEqual(len(df.lines), 24)
            self.assertEqual(len(df.dbase.keys()), 1)
            self.assertTrue("2006" in df.dbase.keys())
            self.assertEqual(len(df.dbase["2006"].keys()), 1)
            self.assertTrue("1" in df.dbase["2006"].keys())
            self.assertEqual(len(df.dbase["2006"]["1"].keys()), 4)
            self.assertTrue("1" in df.dbase["2006"]["1"].keys())
            self.assertTrue("2" in df.dbase["2006"]["1"].keys())
            self.assertTrue("3" in df.dbase["2006"]["1"].keys())
            self.assertTrue("4" in df.dbase["2006"]["1"].keys())
            self.assertEqual(len(df.dbase["2006"]["1"]["1"].keys()), 24)
            self.assertEqual(len(df.dbase["2006"]["1"]["2"].keys()), 24)
            self.assertEqual(len(df.dbase["2006"]["1"]["3"].keys()), 24)
            self.assertEqual(len(df.dbase["2006"]["1"]["4"].keys()), 24)
            for hour in range (0, 24):
                self.assertEqual((df.dbase["2006"]["1"]["1"][str(hour)].val * 1.1) + 100,
                                 df.dbase["2006"]["1"]["3"][str(hour)].val)
                self.assertEqual((df.dbase["2006"]["1"]["2"][str(hour)].val * 1.1) + 100,
                                 df.dbase["2006"]["1"]["4"][str(hour)].val)

    def test_adjust_mw_hours(self):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '1', '1', '0', '2006', '1', '1', '0', '100.0'\n"
        "'test1.xlsx', '2', '2006', '1', '1', '1', '2006', '1', '1', '1', '101.0'\n"
        "'test1.xlsx', '3', '2006', '1', '1', '2', '2006', '1', '1', '2', '102.0'\n"
        "'test1.xlsx', '4', '2006', '1', '1', '3', '2006', '1', '1', '3', '103.0'\n"
        "'test1.xlsx', '5', '2006', '1', '1', '4', '2006', '1', '1', '4', '104.0'\n"
        "'test1.xlsx', '6', '2006', '1', '1', '5', '2006', '1', '1', '5', '105.0'\n"
        "'test1.xlsx', '7', '2006', '1', '1', '6', '2006', '1', '1', '6', '106.0'\n"
        "'test1.xlsx', '8', '2006', '1', '1', '7', '2006', '1', '1', '7', '107.0'\n"
        "'test1.xlsx', '9', '2006', '1', '1', '8', '2006', '1', '1', '8', '108.0'\n"
        "'test1.xlsx', '10', '2006', '1', '1', '9', '2006', '1', '1', '9', '109.0'\n"
        "'test1.xlsx', '11', '2006', '1', '1', '10', '2006', '1', '1', '10', '110.0'\n"
        "'test1.xlsx', '12', '2006', '1', '1', '11', '2006', '1', '1', '11', '120.0'\n"
        "'test1.xlsx', '13', '2006', '1', '1', '12', '2006', '1', '1', '12', '130.0'\n"
        "'test1.xlsx', '14', '2006', '1', '1', '13', '2006', '1', '1', '13', '140.0'\n"
        "'test1.xlsx', '15', '2006', '1', '1', '14', '2006', '1', '1', '14', '150.0'\n"
        "'test1.xlsx', '16', '2006', '1', '1', '15', '2006', '1', '1', '15', '160.0'\n"
        "'test1.xlsx', '17', '2006', '1', '1', '16', '2006', '1', '1', '16', '170.0'\n"
        "'test1.xlsx', '18', '2006', '1', '1', '17', '2006', '1', '1', '17', '180.0'\n"
        "'test1.xlsx', '19', '2006', '1', '1', '18', '2006', '1', '1', '18', '190.0'\n"
        "'test1.xlsx', '20', '2006', '1', '1', '19', '2006', '1', '1', '19', '200.0'\n"
        "'test1.xlsx', '21', '2006', '1', '1', '20', '2006', '1', '1', '20', '210.0'\n"
        "'test1.xlsx', '22', '2006', '1', '1', '21', '2006', '1', '1', '21', '220.0'\n"
        "'test1.xlsx', '23', '2006', '1', '1', '22', '2006', '1', '1', '22', '230.0'\n"
        "'test1.xlsx', '24', '2006', '1', '1', '23', '2006', '1', '1', '23', '240.0'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = DemandFile()
            self.assertFalse(mock_file.called)
            df.read_hourly_mw_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.lines), 24)

            src_time = datetime(2006, 1, 1, hour=0)
            interval = timedelta(hours=24)
            new_time = src_time + interval
            adj = AdjustData()
            print("Srctime: %s" % src_time.strftime(DATE_FORMAT))
            df.duplicate_mw_hours(src_time, new_time, interval, adj)
            adj = AdjustData(abs_adj=50, ratio=0.9)
            print("Srctime: %s" % src_time.strftime(DATE_FORMAT))
            df.adjust_mw_hours(src_time, interval, adj)

            for hour in range (0, 24):
                self.assertEqual(df.dbase["2006"]["1"]["1"][str(hour)].val,
                                (df.dbase["2006"]["1"]["2"][str(hour)].val * 0.9) + 50.0)

if __name__ == '__main__':
    unittest.main()
