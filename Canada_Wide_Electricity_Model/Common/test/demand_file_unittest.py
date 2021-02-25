#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Unit test for demand file.

"""

from demand_file import demand_hour, demand_file
from adjust_data import AdjustData
from datetime import datetime, timezone, timedelta
from common_defs import *
from math import ceil, isnan

import unittest
import mock
from unittest.mock import patch, mock_open, call

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
        test_list = ["file_path", "Line", "1967", "01", "02", "03",
                                        "1978", "04", "05", "06",
                                        "123456.7"]

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

        self.assertEqual(demand.dbase["2006"]["1"]["2"]["3"].data_array[0][0],
                         "path 1")
        self.assertEqual(demand.dbase["2006"]["1"]["2"]["3"].val, 10203.7)
        self.assertEqual(demand.dbase["2006"]["2"]["3"]["4"].data_array[0][0],
                         "path 2")
        self.assertEqual(demand.dbase["2006"]["2"]["3"]["4"].val, 20304.7)
        self.assertEqual(demand.dbase["2007"]["2"]["3"]["5"].data_array[0][0],
                         "path 3")
        self.assertEqual(demand.dbase["2007"]["2"]["3"]["5"].val, 123456.7)

    def test_add_demand_hour_failure(self):
        list_1 = ["path 1", "line 1", "2006", "01", "02", "03",
                                      "2006", "01", "02", "10", "10203.7"]
        list_2 = ["path 2", "line 2", "2006", "01", "02", "03",
                                      "2006", "02", "03", "11", "20304.7"]
        demand = demand_file()

        demand.add_demand_hour(list_1)
        self.assertRaises(ValueError, demand.add_demand_hour, list_2)

class TestDemandFile(unittest.TestCase):
    file_header = ("File, LineNum, UTC_Year, UTC_Month, "
                   "UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)")

    def setUp(self):
        pass

    def test_constants(self):
        demand = demand_file()
        self.assertEqual(demand.demand_file_header, self.file_header)

    def test_init(self):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6851.0'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = demand_file()
            self.assertEqual(df.demand, [])
            self.assertEqual(df.dbase, {})
            self.assertFalse(mock_file.called)

    def test_init_with_file(self):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6599.9'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = demand_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.demand), 2)
            self.assertEqual(df.demand[0].file_path, "test1.xlsx")
            self.assertEqual(df.demand[0].line_num, "1")
            self.assertEqual(df.demand[0].UTC_Y, "2006")
            self.assertEqual(df.demand[0].UTC_M, "11")
            self.assertEqual(df.demand[0].UTC_D, "2")
            self.assertEqual(df.demand[0].UTC_H, "8")
            self.assertEqual(df.demand[0].local_Y, "2006")
            self.assertEqual(df.demand[0].local_M, "3")
            self.assertEqual(df.demand[0].local_D, "4")
            self.assertEqual(df.demand[0].local_H, "5")
            self.assertEqual(df.demand[0].demand_MW, "6851.0")
            self.assertEqual(df.demand[1].file_path, "test2.xlsx")
            self.assertEqual(df.demand[1].line_num, "2")
            self.assertEqual(df.demand[1].UTC_Y, "2006")
            self.assertEqual(df.demand[1].UTC_M, "12")
            self.assertEqual(df.demand[1].UTC_D, "3")
            self.assertEqual(df.demand[1].UTC_H, "9")
            self.assertEqual(df.demand[1].local_Y, "2006")
            self.assertEqual(df.demand[1].local_M, "6")
            self.assertEqual(df.demand[1].local_D, "7")
            self.assertEqual(df.demand[1].local_H, "8")
            self.assertEqual(df.demand[1].demand_MW, "6599.9")
            self.assertEqual(len(df.dbase.keys()), 1)
            self.assertTrue("2006" in df.dbase.keys())
            self.assertEqual(len(df.dbase["2006"].keys()), 2)
            self.assertTrue("11" in df.dbase["2006"].keys())
            self.assertEqual(len(df.dbase["2006"]["11"].keys()), 1)
            self.assertTrue("2" in df.dbase["2006"]["11"].keys())
            self.assertEqual(len(df.dbase["2006"]["11"]["2"].keys()), 1)
            self.assertTrue("8" in df.dbase["2006"]["11"]["2"].keys())
            self.assertEqual(df.dbase["2006"]["11"]["2"]["8"].data_array[0][0],
                             "test1.xlsx")
            self.assertEqual(df.dbase["2006"]["11"]["2"]["8"].val,6851.0)
            self.assertTrue("12" in df.dbase["2006"].keys())
            self.assertEqual(len(df.dbase["2006"]["12"].keys()), 1)
            self.assertTrue("3" in df.dbase["2006"]["12"].keys())
            self.assertEqual(len(df.dbase["2006"]["12"]["3"].keys()), 1)
            self.assertTrue("9" in df.dbase["2006"]["12"]["3"].keys())
            self.assertEqual(df.dbase["2006"]["12"]["3"]["9"].data_array[0][0],
                             "test2.xlsx")
            self.assertEqual(df.dbase["2006"]["12"]["3"]["9"].val,6599.9)

    def test_init_with_bad_file_header(self):
        file_data = ("Bad Header!\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6851.0'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            with self.assertRaises(Exception) as context:
                df = demand_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertTrue( ("File header is 'Bad Header!', not "
                              "'File, LineNum, UTC_Year, UTC_Month, UTC_Day, "
                              "UTC_Hour, Year, Month, Day, Hour, Load(MW)'.  Halting.")
                              in str(context.exception))

    def test_read_demand_file_success(self):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6580.0'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = demand_file()
            self.assertFalse(mock_file.called)
            df.read_demand_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.demand), 2)
            self.assertEqual(df.demand[0].file_path, "test1.xlsx")
            self.assertEqual(df.demand[0].line_num, "1")
            self.assertEqual(df.demand[0].UTC_Y, "2006")
            self.assertEqual(df.demand[0].UTC_M, "11")
            self.assertEqual(df.demand[0].UTC_D, "2")
            self.assertEqual(df.demand[0].UTC_H, "8")
            self.assertEqual(df.demand[0].local_Y, "2006")
            self.assertEqual(df.demand[0].local_M, "3")
            self.assertEqual(df.demand[0].local_D, "4")
            self.assertEqual(df.demand[0].local_H, "5")
            self.assertEqual(df.demand[0].demand_MW, "6851.0")
            self.assertEqual(df.demand[1].file_path, "test2.xlsx")
            self.assertEqual(df.demand[1].line_num, "2")
            self.assertEqual(df.demand[1].UTC_Y, "2006")
            self.assertEqual(df.demand[1].UTC_M, "12")
            self.assertEqual(df.demand[1].UTC_D, "3")
            self.assertEqual(df.demand[1].UTC_H, "9")
            self.assertEqual(df.demand[1].local_Y, "2006")
            self.assertEqual(df.demand[1].local_M, "6")
            self.assertEqual(df.demand[1].local_D, "7")
            self.assertEqual(df.demand[1].local_H, "8")
            self.assertEqual(df.demand[1].demand_MW, "6580.0")
            self.assertEqual(len(df.dbase.keys()), 1)
            self.assertTrue("2006" in df.dbase.keys())
            self.assertEqual(len(df.dbase["2006"].keys()), 2)
            self.assertTrue("11" in df.dbase["2006"].keys())
            self.assertEqual(len(df.dbase["2006"]["11"].keys()), 1)
            self.assertTrue("2" in df.dbase["2006"]["11"].keys())
            self.assertEqual(len(df.dbase["2006"]["11"]["2"].keys()), 1)
            self.assertTrue("8" in df.dbase["2006"]["11"]["2"].keys())
            self.assertEqual(df.dbase["2006"]["11"]["2"]["8"].data_array[0][0],
                             "test1.xlsx")
            self.assertEqual(df.dbase["2006"]["11"]["2"]["8"].val, 6851.0)
            self.assertTrue("12" in df.dbase["2006"].keys())
            self.assertEqual(len(df.dbase["2006"]["12"].keys()), 1)
            self.assertTrue("3" in df.dbase["2006"]["12"].keys())
            self.assertEqual(len(df.dbase["2006"]["12"]["3"].keys()), 1)
            self.assertTrue("9" in df.dbase["2006"]["12"]["3"].keys())
            self.assertEqual(df.dbase["2006"]["12"]["3"]["9"].data_array[0][0],
                             "test2.xlsx")
            self.assertEqual(df.dbase["2006"]["12"]["3"]["9"].val, 6580.0)

    def test_read_demand_file_bad_file_delim(self):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "Xtest2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6899.0Y\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = demand_file()
            self.assertFalse(mock_file.called)
            with self.assertRaises(Exception) as context:
                df.read_demand_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.demand), 1)
            self.assertEqual(df.demand[0].file_path, "test1.xlsx")
            self.assertEqual(df.demand[0].line_num, "1")
            self.assertEqual(df.demand[0].UTC_Y, "2006")
            self.assertEqual(df.demand[0].UTC_M, "11")
            self.assertEqual(df.demand[0].UTC_D, "2")
            self.assertEqual(df.demand[0].UTC_H, "8")
            self.assertEqual(df.demand[0].local_Y, "2006")
            self.assertEqual(df.demand[0].local_M, "3")
            self.assertEqual(df.demand[0].local_D, "4")
            self.assertEqual(df.demand[0].local_H, "5")
            self.assertEqual(df.demand[0].demand_MW, "6851.0")
            self.assertEqual(len(df.dbase.keys()), 1)
            self.assertTrue("2006" in df.dbase.keys())
            self.assertEqual(len(df.dbase["2006"].keys()), 1)
            self.assertTrue("11" in df.dbase["2006"].keys())
            self.assertEqual(len(df.dbase["2006"]["11"].keys()), 1)
            self.assertTrue("2" in df.dbase["2006"]["11"].keys())
            self.assertEqual(len(df.dbase["2006"]["11"]["2"].keys()), 1)
            self.assertTrue("8" in df.dbase["2006"]["11"]["2"].keys())
            self.assertEqual(df.dbase["2006"]["11"]["2"]["8"].data_array[0][0],
                             "test1.xlsx")
            self.assertEqual(df.dbase["2006"]["11"]["2"]["8"].val, 6851.0)
            mock_file.assert_called_with("TestFile", 'r')
            self.assertTrue( ("File TestFile Line 2 delimiters "
                              "'X' 'Y' not ''''''. Halting.")
                             in str(context.exception))

    @patch('builtins.print')
    def test_read_demand_file_bad_line(self, mock_print):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '6', '7', '8', '6851.0'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = demand_file()
            self.assertFalse(mock_file.called)
            with self.assertRaises(Exception) as context:
                df.read_demand_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.demand), 1)
            self.assertEqual(df.demand[0].file_path, "test1.xlsx")
            self.assertEqual(df.demand[0].line_num, "1")
            self.assertEqual(df.demand[0].UTC_Y, "2006")
            self.assertEqual(df.demand[0].UTC_M, "11")
            self.assertEqual(df.demand[0].UTC_D, "2")
            self.assertEqual(df.demand[0].UTC_H, "8")
            self.assertEqual(df.demand[0].local_Y, "2006")
            self.assertEqual(df.demand[0].local_M, "3")
            self.assertEqual(df.demand[0].local_D, "4")
            self.assertEqual(df.demand[0].local_H, "5")
            self.assertEqual(df.demand[0].demand_MW, "6851.0")
            self.assertEqual(len(df.dbase.keys()), 1)
            self.assertTrue("2006" in df.dbase.keys())
            self.assertEqual(len(df.dbase["2006"].keys()), 1)
            self.assertTrue("11" in df.dbase["2006"].keys())
            self.assertEqual(len(df.dbase["2006"]["11"].keys()), 1)
            self.assertTrue("2" in df.dbase["2006"]["11"].keys())
            self.assertEqual(len(df.dbase["2006"]["11"]["2"].keys()), 1)
            self.assertTrue("8" in df.dbase["2006"]["11"]["2"].keys())
            self.assertEqual(df.dbase["2006"]["11"]["2"]["8"].data_array[0][0],
                             "test1.xlsx")
            self.assertEqual(df.dbase["2006"]["11"]["2"]["8"].val, 6851.0)
            mock_file.assert_called_with("TestFile", 'r')
            #print("\n%s" % str(context.exception))
            self.assertTrue(("File TestFile Line 2 Invalid format "
                             "''test2.xlsx', '2', '2006', '12', '3', "
                             "'9', '6', '7', '8', '6851.0''")
                             in str(context.exception))
            calls = [call(("List must have 11 entries, not "
                           "'test2.xlsx,2,2006,12,3,9,6,7,8,6851.0'"))]
            mock_print.assert_has_calls(calls, any_order = False)

    @patch('builtins.print')
    def test_write_demand_file(self, mock_print):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6875.0'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = demand_file("TestFile")
            self.assertTrue(mock_file.called)
            mock_file.assert_called_with("TestFile", 'r')
            df.write_demand_file()
            calls = [call(('File, LineNum, UTC_Year, UTC_Month, '
                           'UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)')),
                     call(("'test1.xlsx', '1', '2006', '11', '2', "
                           "'8', '2006', '3', '4', '5', '6851.0'")),
                     call(("'test2.xlsx', '2', '2006', '12', '3', "
                           "'9', '2006', '6', '7', '8', '6875.0'"))]
            mock_print.assert_has_calls(calls, any_order = False)

    def test_get_demand_success(self):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6580.0'\n"
        "'test3.xlsx', '3', '2006', '03', '04', '10', '2006', '06', '07', '8', '4562.0'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = demand_file()
            self.assertFalse(mock_file.called)
            df.read_demand_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.demand), 3)
            self.assertEqual(len(df.dbase.keys()), 1)
            self.assertTrue("2006" in df.dbase.keys())

            self.assertEqual(len(df.dbase["2006"].keys()), 3)
            self.assertTrue("11" in df.dbase["2006"].keys())
            self.assertEqual(len(df.dbase["2006"]["11"].keys()), 1)
            self.assertTrue("2" in df.dbase["2006"]["11"].keys())
            self.assertEqual(len(df.dbase["2006"]["11"]["2"].keys()), 1)
            self.assertTrue("8" in df.dbase["2006"]["11"]["2"].keys())
            self.assertEqual(df.dbase["2006"]["11"]["2"]["8"].data_array[0][0],
                            "test1.xlsx")
            self.assertEqual(df.dbase["2006"]["11"]["2"]["8"].val, 6851.0)

            self.assertTrue("12" in df.dbase["2006"].keys())
            self.assertEqual(len(df.dbase["2006"]["12"].keys()), 1)
            self.assertTrue("3" in df.dbase["2006"]["12"].keys())
            self.assertEqual(len(df.dbase["2006"]["12"]["3"].keys()), 1)
            self.assertTrue("9" in df.dbase["2006"]["12"]["3"].keys())
            self.assertEqual(df.dbase["2006"]["12"]["3"]["9"].data_array[0][0],
                             "test2.xlsx")
            self.assertEqual(df.dbase["2006"]["12"]["3"]["9"].val, 6580.0)

            self.assertTrue("3" in df.dbase["2006"].keys())
            self.assertEqual(len(df.dbase["2006"]["3"].keys()), 1)
            self.assertTrue("4" in df.dbase["2006"]["3"].keys())
            self.assertEqual(len(df.dbase["2006"]["3"]["4"].keys()), 1)
            self.assertTrue("10" in df.dbase["2006"]["3"]["4"].keys())
            self.assertEqual(df.dbase["2006"]["3"]["4"]["10"].data_array[0][0],
                             "test3.xlsx")
            self.assertEqual(df.dbase["2006"]["3"]["4"]["10"].val, 4562.0)

            UTC = datetime(2006, 11, 2, hour=8, tzinfo=timezone.utc)
            self.assertEqual(df.get_demand(UTC), 6851.0)
            UTC = datetime(2006, 12, 3, hour=9, tzinfo=timezone.utc)
            self.assertEqual(df.get_demand(UTC), 6580.0)
            UTC = datetime(2006, 3, 4, hour=10, tzinfo=timezone.utc)
            self.assertEqual(df.get_demand(UTC), 4562.0)

    def test_get_demand_failure(self):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6580.0'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = demand_file()
            self.assertFalse(mock_file.called)
            df.read_demand_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.demand), 2)
            UTC = datetime(2021,11, 2, hour=8, tzinfo=timezone.utc)
            self.assertTrue(isnan(df.get_demand(UTC)))
            UTC = datetime(2006,12, 2, hour=8, tzinfo=timezone.utc)
            self.assertTrue(isnan(df.get_demand(UTC)))
            UTC = datetime(2006,11, 3, hour=8, tzinfo=timezone.utc)
            self.assertTrue(isnan(df.get_demand(UTC)))
            UTC = datetime(2006,11, 2, hour=7, tzinfo=timezone.utc)
            self.assertTrue(isnan(df.get_demand(UTC)))

    def test_duplicate_demand(self):
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
            df = demand_file()
            self.assertFalse(mock_file.called)
            df.read_demand_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.demand), 24)

            src_time = datetime(2006, 1, 1, hour=0)
            interval = timedelta(hours=24)
            new_time = src_time + interval
            adj = AdjustData()
            df.duplicate_demand(src_time, new_time, interval, adj)

            self.assertEqual(len(df.demand), 24)
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
            df.duplicate_demand(src_time, new_time, interval, adj)

            self.assertEqual(len(df.demand), 24)
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

    def test_adjust_demand(self):
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
            df = demand_file()
            self.assertFalse(mock_file.called)
            df.read_demand_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.demand), 24)

            src_time = datetime(2006, 1, 1, hour=0)
            interval = timedelta(hours=24)
            new_time = src_time + interval
            adj = AdjustData()
            print("Srctime: %s" % src_time.strftime(DATE_FORMAT))
            df.duplicate_demand(src_time, new_time, interval, adj)
            adj = AdjustData(abs_adj=50, ratio=0.9)
            print("Srctime: %s" % src_time.strftime(DATE_FORMAT))
            df.adjust_demand(src_time, interval, adj)

            for hour in range (0, 24):
                self.assertEqual(df.dbase["2006"]["1"]["1"][str(hour)].val,
                                (df.dbase["2006"]["1"]["2"][str(hour)].val * 0.9) + 50.0)

if __name__ == '__main__':
    unittest.main()
