#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Unit test for "hourly generation file" support.
"""

from hourly_mw_file import HourlyMWFile
from datetime import datetime

import sys
import unittest
import mock
from unittest.mock import patch, mock_open, call, MagicMock
import logging
from math import isnan

class TestHourlyMWFile(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_constants(self):
        pv = HourlyMWFile()
        self.assertEqual(pv.file_header, ("UTC_Year, UTC_Month, UTC_Day, "
                                                   "UTC_Hour, Year, Month, Day, Hour, Load(MW)"))

    def test_init(self):
        pv = HourlyMWFile()
        self.assertEqual(pv.lines, [])

    def test_read_hourly_mw_file_success(self):
        file_data= ("UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)\n"
                    "'2000', '1', '3', '7', '2000', '1', '2', '7', '123000.0'\n"
                    "'2000', '1', '3', '8', '2000', '2', '3', '8', '12300.0'\n"
                    "'2000', '1', '4', '9', '2000', '3', '4', '9', '1230.0'\n"
                    "'2000', '1', '4', '10', '2000', '4', '5', '10', '123.0'\n"
                    "'2000', '2', '5', '11', '2000', '5', '6', '11', '12.3'\n"
                    "'2000', '2', '5', '12', '2000', '6', '7', '12', '1.23'\n"
                    "'2000', '2', '6', '13', '2000', '7', '8', '13', '345.0'\n"
                    "'2000', '2', '6', '14', '2000', '8', '9', '14', '100000.0'")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            pv = HourlyMWFile()
            self.assertFalse(mock_file.called)

            pv.read_hourly_mw_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')

            lines = [line.strip() for line in file_data.split("\n")]
            lines = [[tok.strip() for tok in line[1:-1].split("', '")] for line in lines[1:]]
            for li_no, line in enumerate(lines):
                self.assertEqual(len(line), 9)
                for i in range(0,len(line)):
                    self.assertEqual(pv.lines[li_no][2+i], line[i])
                UTC = datetime(int(line[0]), int(line[1]), int(line[2]), hour=int(line[3]))
                self.assertEqual(pv.get_mw_hour(UTC), float(line[8]))

    # Test bad header in file
    def test_read_hourly_mw_file_fail_1(self):
        file_data= ("Bad Header\n"
                    "'2000', '1', '3', '7', '2000', '1', '2', '7', '123000.0'\n"
                    "'2000', '1', '3', '8', '2000', '2', '3', '8', '12300.0'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            with self.assertRaises(Exception) as context:
                pv = HourlyMWFile("TestFile")
                self.assertEqual(pv.lines, {})

            #print("\nHeader Context: '%s'" % str(context.exception))
            self.assertTrue(("File header is 'Bad Header', not "
                             "'UTC_Year, UTC_Month, UTC_Day, UTC_Hour, "
                             "Year, Month, Day, Hour, Load(MW)'.  Halting.")
                             in str(context.exception))

    # Test bad delimiters
    def test_read_hourly_mw_file_fail_2(self):
        file_data= ("UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)\n"
                    "'2000', '1', '3', '7', '2000', '1', '2', '7', '123000.0'\n"
                    "X2000', '1', '3', '8', '2000', '2', '3', '8Y\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            with self.assertRaises(Exception) as context:
                pv = HourlyMWFile("TestFile")
                self.assertTrue("2000" in pv.dbase)
                self.assertTrue("1" in pv.dbase["2000"])
                self.assertTrue("3" in pv.dbase["2000"]["1"])
                self.assertTrue("7" in pv.dbase["2000"]["1"]["3"])
                self.assertEqual(pv.dbase["2000"]["1"]["3"]["7"].local_Y, "2000")
                self.assertEqual(pv.dbase["2000"]["1"]["3"]["7"].local_M, "1")
                self.assertEqual(pv.dbase["2000"]["1"]["3"]["7"].local_D, "2")
                self.assertEqual(pv.dbase["2000"]["1"]["3"]["7"].local_H, "7")
                self.assertEqual(pv.dbase["2000"]["1"]["3"]["7"].dbase_kW, 123000.0)

            # print("\nDelim Context: '%s'" % str(context.exception))
            self.assertTrue("File TestFile Line 2 delimiters 'X' 'Y' not ''''''. Halting."
                             in str(context.exception))

    # Test bad date data
    def test_read_hourly_mw_file_fail_3(self):
        file_data= ("UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)\n"
                    "'2000', '1', '3', '7', '2000', '1', '2', '7', '123000.0'\n"
                    "'BADYEAR', '1', '3', '8', '2000', '2', '3', '8', '12300.0'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            with self.assertRaises(Exception) as context:
                pv = HourlyMWFile("TestFile")
                self.assertTrue("2000" in pv.capacity)
                self.assertTrue("1" in pv.capacity["2000"])
                self.assertTrue("3" in pv.capacity["2000"]["1"])
                self.assertTrue("7" in pv.capacity["2000"]["1"]["3"])
                self.assertEqual(pv.capacity["2000"]["1"]["3"]["7"].local_Y, "2000")
                self.assertEqual(pv.capacity["2000"]["1"]["3"]["7"].local_M, "1")
                self.assertEqual(pv.capacity["2000"]["1"]["3"]["7"].local_D, "2")
                self.assertEqual(pv.capacity["2000"]["1"]["3"]["7"].local_H, "7")
                self.assertEqual(pv.capacity["2000"]["1"]["3"]["7"].capacity_kW, 123000.0)

            # print("\nFail 3 Context: '%s'" % str(context.exception))
            self.assertTrue(("File TestFile Line 2 Invalid format "
                             "''BADYEAR', '1', '3', '8', "
                             "'2000', '2', '3', '8', '12300.0''")
                             in str(context.exception))

    # Test bad MW data
    def test_read_hourly_mw_file_fail_4(self):
        file_data= ("UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)\n"
                    "'2000', '1', '3', '7', '2000', '1', '2', '7', '123000.0'\n"
                    "'2000', '1', '3', '8', '2000', '2', '3', '8', 'BADMW'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            with self.assertRaises(Exception) as context:
                pv = HourlyMWFile("TestFile")
                self.assertTrue("2000" in pv.capacity)
                self.assertTrue("1" in pv.capacity["2000"])
                self.assertTrue("3" in pv.capacity["2000"]["1"])
                self.assertTrue("7" in pv.capacity["2000"]["1"]["3"])
                self.assertEqual(pv.capacity["2000"]["1"]["3"]["7"].local_Y, "2000")
                self.assertEqual(pv.capacity["2000"]["1"]["3"]["7"].local_M, "1")
                self.assertEqual(pv.capacity["2000"]["1"]["3"]["7"].local_D, "2")
                self.assertEqual(pv.capacity["2000"]["1"]["3"]["7"].local_H, "7")
                self.assertEqual(pv.capacity["2000"]["1"]["3"]["7"].capacity_kW, 123000.0)

            # print("Context: '%s'" % str(context.exception))
            self.assertTrue(("File TestFile Line 2 Invalid format "
                             "''2000', '1', '3', '8', "
                             "'2000', '2', '3', '8', 'BADMW'")
                             in str(context.exception))

    # Test wrong number of items in line
    def test_read_hourly_mw_file_fail_5(self):
        file_data= ("UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)\n"
                    "'2000', '1', '3', '7', '2000', '1', '2', '7', '123000.0'\n"
                    "'2000', '1', '3', '8', '2000', '2', '3', '8', '23456.0', 'Extra'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            with self.assertRaises(Exception) as context:
                pv = HourlyMWFile("TestFile")
                self.assertTrue("2000" in pv.capacity)
                self.assertTrue("1" in pv.capacity["2000"])
                self.assertTrue("3" in pv.capacity["2000"]["1"])
                self.assertTrue("7" in pv.capacity["2000"]["1"]["3"])
                self.assertEqual(pv.capacity["2000"]["1"]["3"]["7"].local_Y, "2000")
                self.assertEqual(pv.capacity["2000"]["1"]["3"]["7"].local_M, "1")
                self.assertEqual(pv.capacity["2000"]["1"]["3"]["7"].local_D, "2")
                self.assertEqual(pv.capacity["2000"]["1"]["3"]["7"].local_H, "7")
                self.assertEqual(pv.capacity["2000"]["1"]["3"]["7"].capacity_kW, 123000.0)

            #print("\nFail 5 Context: '%s'" % str(context.exception))
            self.assertTrue(("File TestFile Line 2 Bad format "
                             "''2000', '1', '3', '8', "
                             "'2000', '2', '3', '8', '23456.0', 'Extra''")
                             in str(context.exception))

    def test_validate_fields_success(self):
        data = [["2000", "1", "1", "0", "2000", "1", "1", "0", "0.0"],
                ["2000", "12", "31", "23", "2000", "12", "31", "23", "1000000.0"]]

        pv = HourlyMWFile()
        for item in data:
            U_Y, U_M, U_D, U_H, Cap = pv.validate_fields("NoFile", 100, item)
            self.assertEqual(U_Y, int(item[0]))
            self.assertEqual(U_M, int(item[1]))
            self.assertEqual(U_D, int(item[2]))
            self.assertEqual(U_H, int(item[3]))
            self.assertEqual(Cap, float(item[8]))

    def test_validate_fields_failure_conversion(self):
        data = [["BadYear", "1", "1", "0", "2000", "1", "1", "0", "0.0"],
                ["2000", "BadMonth", "1", "0", "2000", "1", "1", "0", "0.0"],
                ["2000", "1", "BadDay", "0", "2000", "1", "1", "0", "0.0"],
                ["2000", "1", "1", "BadHour", "2000", "1", "1", "0", "0.0"],
                ["2000", "1", "1", "0", "BadYear", "1", "1", "0", "0.0"],
                ["2000", "1", "1", "0", "2000", "BadMonth", "1", "0", "0.0"],
                ["2000", "1", "1", "0", "2000", "1", "BadDay", "0", "0.0"],
                ["2000", "1", "1", "0", "2000", "1", "1", "BadHour", "0.0"],
                ["2000", "1", "1", "0", "2000", "1", "1", "0", "BadCap"]]

        pv = HourlyMWFile()
        for item in data:
            with self.assertRaises(Exception) as context:
                U_Y, U_M, U_D, U_H, Cap = pv.validate_fields("NoFile", 100, item)
            # print("Context: '%s'" % str(context.exception))
            self.assertTrue("File NoFile Line 100 Data validation error." in str(context.exception))

    def test_validate_fields_failure_dates(self):
        data = [["2000", "0", "1", "0", "2000", "1", "1", "0", "0.0"],
                ["2000", "1", "0", "0", "2000", "1", "1", "0", "0.0"],
                ["2000", "1", "1", "-1", "2000", "1", "1", "0", "0.0"],
                ["2000", "1", "1", "0", "2000", "0", "1", "0", "0.0"],
                ["2000", "1", "1", "0", "2000", "1", "0", "0", "0.0"],
                ["2000", "1", "1", "0", "2000", "1", "1", "-1", "0.0"],
                ["2000", "13", "31", "23", "2000", "12", "31", "23", "1000000.0"],
                ["2000", "12", "32", "23", "2000", "12", "31", "23", "1000000.0"],
                ["2000", "12", "31", "24", "2000", "12", "31", "23", "1000000.0"],
                ["2000", "12", "31", "23", "2000", "13", "31", "23", "1000000.0"],
                ["2000", "12", "31", "23", "2000", "12", "32", "23", "1000000.0"],
                ["2000", "12", "31", "23", "2000", "12", "31", "24", "1000000.0"]]
        pv = HourlyMWFile()
        for item in data:
            with self.assertRaises(Exception) as context:
                U_Y, U_M, U_D, U_H, Cap = pv.validate_fields("NoFile", 100, item)
            # print("\nDate Context: '%s'" % str(context.exception))
            self.assertTrue("File NoFile Line 100 Data validation error."
                            in str(context.exception))

    def test_validate_fields_failure_capacity(self):
        data = [ ["2000", "1", "1", "0", "2000", "1", "1", "0", "-1.0"],
                ["2000", "12", "31", "23", "2000", "12", "31", "23", "1000000.1"]]
        pv = HourlyMWFile()
        for item in data:
            with self.assertRaises(Exception) as context:
                U_Y, U_M, U_D, U_H, Cap = pv.validate_fields("NoFile", 100, item)
            # print("\nCapacity Context: '%s'" % str(context.exception))
            self.assertTrue("File NoFile Line 100 Data validation error."
                             in str(context.exception))

    def test_get_hourly_mw_capacity(self):
        file_data= ("UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)\n"
                    "'2000', '1', '3', '7', '2000', '1', '2', '7', '123000.0'\n"
                    "'2000', '1', '3', '8', '2000', '2', '3', '8', '12300.0'\n"
                    "'2000', '1', '4', '9', '2000', '3', '4', '9', '1230.0'\n"
                    "'2000', '1', '4', '10', '2000', '4', '5', '10', '123.0'\n"
                    "'2000', '2', '5', '11', '2000', '5', '6', '11', '12.3'\n"
                    "'2000', '2', '5', '12', '2000', '6', '7', '12', '1.23'\n"
                    "'2000', '2', '6', '13', '2000', '7', '8', '13', '345.0'\n"
                    "'2000', '2', '6', '14', '2000', '8', '9', '14', '100000.0'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            pv = HourlyMWFile("TestFile")
            self.assertTrue(mock_file.called)
            mock_file.assert_called_with("TestFile", 'r')

            UTC = datetime(2000, 1, 3, hour=7)
            cap = pv.get_mw_hour(UTC)
            self.assertEqual(cap, 123000.0)

            UTC = datetime(2000, 1, 3, hour=8)
            cap = pv.get_mw_hour(UTC)
            self.assertEqual(cap, 12300.0)

            UTC = datetime(2000, 1, 4, hour=9)
            cap = pv.get_mw_hour(UTC)
            self.assertEqual(cap, 1230.0)

            UTC = datetime(2000, 1, 4, hour=10)
            cap = pv.get_mw_hour(UTC)
            self.assertEqual(cap, 123.0)

            UTC = datetime(2000, 2, 5, hour=11)
            cap = pv.get_mw_hour(UTC)
            self.assertEqual(cap, 12.30)

            UTC = datetime(2000, 2, 5, hour=12)
            cap = pv.get_mw_hour(UTC)
            self.assertEqual(cap, 1.230)

            UTC = datetime(2000, 2, 6, hour=13)
            cap = pv.get_mw_hour(UTC)
            self.assertEqual(cap, 345.0)

            UTC = datetime(2000, 2, 6, hour=14)
            cap = pv.get_mw_hour(UTC)
            self.assertEqual(cap, 100000.0)

            UTC = datetime(2000, 7,12, hour=2)
            cap = pv.get_mw_hour(UTC)
            self.assertTrue(isnan(cap))

    @patch('builtins.print')
    def test_write_hourly_mw_file(self, mock_print):
        file_data= ("UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)\n"
                    "'2000', '1', '3', '7', '2000', '1', '2', '7', '123000.0'\n"
                    "'2000', '1', '3', '8', '2000', '2', '3', '8', '12300.0'\n"
                    "'2000', '1', '4', '9', '2000', '3', '4', '9', '1230.0'\n"
                    "'2000', '1', '4', '10', '2000', '4', '5', '10', '123.0'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            pv = HourlyMWFile("TestFile")
            self.assertTrue(mock_file.called)
            pv.write_hourly_mw_file()
        self.assertEqual(mock_print.call_count, 5)
        calls = [call("UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)",
                     file=sys.stdout),
                 call("'2000', '1', '3', '7', '2000', '1', '2', '7', '123000.0'",
                     file=sys.stdout),
                 call("'2000', '1', '3', '8', '2000', '2', '3', '8', '12300.0'",
                     file=sys.stdout),
                 call("'2000', '1', '4', '9', '2000', '3', '4', '9', '1230.0'",
                     file=sys.stdout),
                 call("'2000', '1', '4', '10', '2000', '4', '5', '10', '123.0'",
                     file=sys.stdout)]
        mock_print.assert_has_calls(calls, any_order = False)

    @patch('builtins.print')
    def test_write_hourly_mw_file_realfile(self, mock_print):
        file_data= ("UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)\n"
                    "'2000', '1', '3', '7', '2000', '1', '2', '7', '123000.0'\n"
                    "'2000', '1', '3', '8', '2000', '2', '3', '8', '12300.0'\n"
                    "'2000', '1', '4', '9', '2000', '3', '4', '9', '1230.0'\n"
                    "'2000', '1', '4', '10', '2000', '4', '5', '10', '123.0'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            pv = HourlyMWFile("TestFile")
            self.assertTrue(mock_file.called)
            with patch("builtins.open", mock_open()) as mock_out:
                pv.write_hourly_mw_file("TestOut")
            self.assertEqual(mock_print.call_count, 5)
            calls = [call("UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)",
                     file=mock_out()),
                 call("'2000', '1', '3', '7', '2000', '1', '2', '7', '123000.0'",
                     file=mock_out()),
                 call("'2000', '1', '3', '8', '2000', '2', '3', '8', '12300.0'",
                     file=mock_out()),
                 call("'2000', '1', '4', '9', '2000', '3', '4', '9', '1230.0'",
                     file=mock_out()),
                 call("'2000', '1', '4', '10', '2000', '4', '5', '10', '123.0'",
                     file=mock_out())]
            mock_print.assert_has_calls(calls, any_order = False)

if __name__ == '__main__':
    unittest.main()
