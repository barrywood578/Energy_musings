#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Unit test for demand file.

"""

from demand_file import demand_hour, demand_file

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

        self.assertEqual(demand.xref_load["2006"]["01"]["02"]["03"], "path 1")
        self.assertEqual(demand.xref_load["2006"]["02"]["03"]["04"], "path 2")
        self.assertEqual(demand.xref_load["2007"]["02"]["03"]["05"], "path 3")

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
            self.assertEqual(df.dbase, [])
            self.assertEqual(df.xref_load, {})
            self.assertFalse(mock_file.called)

    def test_init_with_file(self):
        file_data = self.file_header + ("\n"
        "'test1.xlsx', '1', '2006', '11', '2', '8', '2006', '3', '4', '5', '6851.0'\n"
        "'test2.xlsx', '2', '2006', '12', '3', '9', '2006', '6', '7', '8', '6599.9'\n"
        )

        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            df = demand_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(df.dbase), 2)
            self.assertEqual(df.dbase[0].file_path, "test1.xlsx")
            self.assertEqual(df.dbase[0].line_num, "1")
            self.assertEqual(df.dbase[0].UTC_Y, "2006")
            self.assertEqual(df.dbase[0].UTC_M, "11")
            self.assertEqual(df.dbase[0].UTC_D, "2")
            self.assertEqual(df.dbase[0].UTC_H, "8")
            self.assertEqual(df.dbase[0].local_Y, "2006")
            self.assertEqual(df.dbase[0].local_M, "3")
            self.assertEqual(df.dbase[0].local_D, "4")
            self.assertEqual(df.dbase[0].local_H, "5")
            self.assertEqual(df.dbase[0].demand_MW, "6851.0")
            self.assertEqual(df.dbase[1].file_path, "test2.xlsx")
            self.assertEqual(df.dbase[1].line_num, "2")
            self.assertEqual(df.dbase[1].UTC_Y, "2006")
            self.assertEqual(df.dbase[1].UTC_M, "12")
            self.assertEqual(df.dbase[1].UTC_D, "3")
            self.assertEqual(df.dbase[1].UTC_H, "9")
            self.assertEqual(df.dbase[1].local_Y, "2006")
            self.assertEqual(df.dbase[1].local_M, "6")
            self.assertEqual(df.dbase[1].local_D, "7")
            self.assertEqual(df.dbase[1].local_H, "8")
            self.assertEqual(df.dbase[1].demand_MW, "6599.9")
            self.assertEqual(len(df.xref_load.keys()), 1)
            self.assertTrue("2006" in df.xref_load.keys())
            self.assertEqual(len(df.xref_load["2006"].keys()), 2)
            self.assertTrue("11" in df.xref_load["2006"].keys())
            self.assertEqual(len(df.xref_load["2006"]["11"].keys()), 1)
            self.assertTrue("2" in df.xref_load["2006"]["11"].keys())
            self.assertEqual(len(df.xref_load["2006"]["11"]["2"].keys()), 1)
            self.assertTrue("8" in df.xref_load["2006"]["11"]["2"].keys())
            self.assertEqual(df.xref_load["2006"]["11"]["2"]["8"],"test1.xlsx")
            self.assertTrue("12" in df.xref_load["2006"].keys())
            self.assertEqual(len(df.xref_load["2006"]["12"].keys()), 1)
            self.assertTrue("3" in df.xref_load["2006"]["12"].keys())
            self.assertEqual(len(df.xref_load["2006"]["12"]["3"].keys()), 1)
            self.assertTrue("9" in df.xref_load["2006"]["12"]["3"].keys())
            self.assertEqual(df.xref_load["2006"]["12"]["3"]["9"],"test2.xlsx")

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
            self.assertEqual(len(df.dbase), 2)
            self.assertEqual(df.dbase[0].file_path, "test1.xlsx")
            self.assertEqual(df.dbase[0].line_num, "1")
            self.assertEqual(df.dbase[0].UTC_Y, "2006")
            self.assertEqual(df.dbase[0].UTC_M, "11")
            self.assertEqual(df.dbase[0].UTC_D, "2")
            self.assertEqual(df.dbase[0].UTC_H, "8")
            self.assertEqual(df.dbase[0].local_Y, "2006")
            self.assertEqual(df.dbase[0].local_M, "3")
            self.assertEqual(df.dbase[0].local_D, "4")
            self.assertEqual(df.dbase[0].local_H, "5")
            self.assertEqual(df.dbase[0].demand_MW, "6851.0")
            self.assertEqual(df.dbase[1].file_path, "test2.xlsx")
            self.assertEqual(df.dbase[1].line_num, "2")
            self.assertEqual(df.dbase[1].UTC_Y, "2006")
            self.assertEqual(df.dbase[1].UTC_M, "12")
            self.assertEqual(df.dbase[1].UTC_D, "3")
            self.assertEqual(df.dbase[1].UTC_H, "9")
            self.assertEqual(df.dbase[1].local_Y, "2006")
            self.assertEqual(df.dbase[1].local_M, "6")
            self.assertEqual(df.dbase[1].local_D, "7")
            self.assertEqual(df.dbase[1].local_H, "8")
            self.assertEqual(df.dbase[1].demand_MW, "6580.0")
            self.assertEqual(len(df.xref_load.keys()), 1)
            self.assertTrue("2006" in df.xref_load.keys())
            self.assertEqual(len(df.xref_load["2006"].keys()), 2)
            self.assertTrue("11" in df.xref_load["2006"].keys())
            self.assertEqual(len(df.xref_load["2006"]["11"].keys()), 1)
            self.assertTrue("2" in df.xref_load["2006"]["11"].keys())
            self.assertEqual(len(df.xref_load["2006"]["11"]["2"].keys()), 1)
            self.assertTrue("8" in df.xref_load["2006"]["11"]["2"].keys())
            self.assertEqual(df.xref_load["2006"]["11"]["2"]["8"],"test1.xlsx")
            self.assertTrue("12" in df.xref_load["2006"].keys())
            self.assertEqual(len(df.xref_load["2006"]["12"].keys()), 1)
            self.assertTrue("3" in df.xref_load["2006"]["12"].keys())
            self.assertEqual(len(df.xref_load["2006"]["12"]["3"].keys()), 1)
            self.assertTrue("9" in df.xref_load["2006"]["12"]["3"].keys())
            self.assertEqual(df.xref_load["2006"]["12"]["3"]["9"],"test2.xlsx")

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
            self.assertEqual(len(df.dbase), 1)
            self.assertEqual(df.dbase[0].file_path, "test1.xlsx")
            self.assertEqual(df.dbase[0].line_num, "1")
            self.assertEqual(df.dbase[0].UTC_Y, "2006")
            self.assertEqual(df.dbase[0].UTC_M, "11")
            self.assertEqual(df.dbase[0].UTC_D, "2")
            self.assertEqual(df.dbase[0].UTC_H, "8")
            self.assertEqual(df.dbase[0].local_Y, "2006")
            self.assertEqual(df.dbase[0].local_M, "3")
            self.assertEqual(df.dbase[0].local_D, "4")
            self.assertEqual(df.dbase[0].local_H, "5")
            self.assertEqual(df.dbase[0].demand_MW, "6851.0")
            self.assertEqual(len(df.xref_load.keys()), 1)
            self.assertTrue("2006" in df.xref_load.keys())
            self.assertEqual(len(df.xref_load["2006"].keys()), 1)
            self.assertTrue("11" in df.xref_load["2006"].keys())
            self.assertEqual(len(df.xref_load["2006"]["11"].keys()), 1)
            self.assertTrue("2" in df.xref_load["2006"]["11"].keys())
            self.assertEqual(len(df.xref_load["2006"]["11"]["2"].keys()), 1)
            self.assertTrue("8" in df.xref_load["2006"]["11"]["2"].keys())
            self.assertEqual(df.xref_load["2006"]["11"]["2"]["8"],"test1.xlsx")
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
            self.assertEqual(len(df.dbase), 1)
            self.assertEqual(df.dbase[0].file_path, "test1.xlsx")
            self.assertEqual(df.dbase[0].line_num, "1")
            self.assertEqual(df.dbase[0].UTC_Y, "2006")
            self.assertEqual(df.dbase[0].UTC_M, "11")
            self.assertEqual(df.dbase[0].UTC_D, "2")
            self.assertEqual(df.dbase[0].UTC_H, "8")
            self.assertEqual(df.dbase[0].local_Y, "2006")
            self.assertEqual(df.dbase[0].local_M, "3")
            self.assertEqual(df.dbase[0].local_D, "4")
            self.assertEqual(df.dbase[0].local_H, "5")
            self.assertEqual(df.dbase[0].demand_MW, "6851.0")
            self.assertEqual(len(df.xref_load.keys()), 1)
            self.assertTrue("2006" in df.xref_load.keys())
            self.assertEqual(len(df.xref_load["2006"].keys()), 1)
            self.assertTrue("11" in df.xref_load["2006"].keys())
            self.assertEqual(len(df.xref_load["2006"]["11"].keys()), 1)
            self.assertTrue("2" in df.xref_load["2006"]["11"].keys())
            self.assertEqual(len(df.xref_load["2006"]["11"]["2"].keys()), 1)
            self.assertTrue("8" in df.xref_load["2006"]["11"]["2"].keys())
            self.assertEqual(df.xref_load["2006"]["11"]["2"]["8"],"test1.xlsx")
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

if __name__ == '__main__':
    unittest.main()
