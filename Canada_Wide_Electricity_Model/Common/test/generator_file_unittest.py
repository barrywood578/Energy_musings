#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Unit test for "generation file" support.


"""

from generator_file import generator, generator_file

import unittest
import mock
from unittest.mock import patch, mock_open, call
from datetime import datetime

class TestGenerator(unittest.TestCase):

    def setUp(self):
        pass

    def test_init(self):
        gen = generator()
        self.assertEqual(gen.mw,  0.0)
        self.assertEqual(gen.ghg, 0.0)
        self.assertEqual(gen.tz_str, "Unknown")

        gen = generator(1.1, 2.2, "America/Montreal")
        self.assertEqual(gen.mw,  1.1)
        self.assertEqual(gen.ghg, 2.2)
        self.assertEqual(gen.tz_str, "America/Montreal")

    @patch('os.path.isfile')
    def test_add_gen_file(self, mock_isfile):
        file_data= ("UTC_Year, UTC_Month, UTC_Day, UTC_Hour, Year, Month, Day, Hour, Load(MW)\n"
                    "'2000', '1', '1', '0', '2000', '1', '2', '7', '0.0'\n"
                    "'2000', '1', '1', '1', '2000', '2', '3', '8', '1.0'\n"
                    "'2000', '1', '1', '2', '2000', '3', '4', '9', '3.0'\n"
                    "'2000', '1', '1', '3', '2000', '4', '5', '10', '5.0'\n")
        mock_isfile.return_value = True
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            gen = generator(300, 1000, "TimeZone", gen_path="TestFile")
        self.assertTrue(mock_isfile.called)
        mock_isfile.assert_called_with("TestFile")
        self.assertEqual(gen.mw,  300)
        self.assertEqual(gen.ghg, 1000)
        self.assertEqual(gen.tz_str, "TimeZone")
        self.assertEqual(len(gen.gen_files), 1)

class TestGeneratorFile(unittest.TestCase):
    def setUp(self):
        pass

    def test_constants(self):
        gf = generator_file()
        self.assertEqual(gf.generator_file_header, "Fuel, Capacity, GHG_MWh, Timezone")

    def test_init(self):
        gf = generator_file()
        self.assertEqual(gf.gen_db, {})
        self.assertEqual(gf.sorted_db, {})

    @patch('os.path.isfile')
    def test_read_generator_file_success(self, mock_isfile):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'COAL', '1000', '100', 'America/Edmonton'\n"
                    "'NATGAS', '1001', '20', 'America/Regina'\n"
                    "'NUCLEAR', '1002', '1', 'America/Toronto'\n"
                    "'SOLAR_PV', '1003', '15', 'America/Vancouver'\n"
                    "'HYDRO_RES', '1004', '8', 'America/Montreal'\n")
        mock_isfile.return_value = False
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            gf = generator_file()
            self.assertFalse(mock_file.called)

            gf.read_generator_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(gf.gen_db.keys()), 5)
            self.assertTrue("COAL" in gf.gen_db)
            gen_obj = gf.gen_db["COAL"] 
            self.assertEqual(gen_obj.mw, 1000.0)
            self.assertEqual(gen_obj.ghg, 100.0)
            self.assertEqual(gen_obj.tz_str, "America/Edmonton")
            self.assertTrue("NATGAS" in gf.gen_db)
            gen_obj = gf.gen_db["NATGAS"] 
            self.assertEqual(gen_obj.mw, 1001.0)
            self.assertEqual(gen_obj.ghg, 20.0)
            self.assertEqual(gen_obj.tz_str, "America/Regina")
            self.assertTrue("NUCLEAR" in gf.gen_db)
            gen_obj = gf.gen_db["NUCLEAR"] 
            self.assertEqual(gen_obj.mw, 1002.0)
            self.assertEqual(gen_obj.ghg, 1.0)
            self.assertEqual(gen_obj.tz_str, "America/Toronto")
            self.assertTrue("SOLAR_PV" in gf.gen_db)
            gen_obj = gf.gen_db["SOLAR_PV"] 
            self.assertEqual(gen_obj.mw, 1003.0)
            self.assertEqual(gen_obj.ghg, 15.0)
            self.assertEqual(gen_obj.tz_str, "America/Vancouver")
            self.assertTrue("HYDRO_RES" in gf.gen_db)
            gen_obj = gf.gen_db["HYDRO_RES"] 
            self.assertEqual(gen_obj.mw, 1004.0)
            self.assertEqual(gen_obj.ghg, 8.0)
            self.assertEqual(gen_obj.tz_str, "America/Montreal")

            self.assertEqual(gf.sorted_db, {})

    @patch('os.path.isfile')
    def test_read_generator_file_fail_1(self, mock_isfile):
        file_data= ("Bad_Header\n" 
                    "'COAL', '1000', '100', 'America/Edmonton'\n"
                    "'NATGAS', '1001', '20', 'America/Regina'\n"
                    "'NUCLEAR', '1002', '1', 'America/Toronto'\n"
                    "'SOLAR_PV', '1003', '15', 'America/Vancouver'\n"
                    "'HYDRO_RES', '1004', '8', 'America/Montreal'\n")
        mock_isfile.return_value = False
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            with self.assertRaises(Exception) as context:
                gf = generator_file("TestFile")

            # print("Context: '%s'" % str(context.exception))
            self.assertTrue(("File header is 'Bad_Header', not "
                             "'Fuel, Capacity, GHG_MWh, Timezone'.  Halting.")
                             in str(context.exception))

    @patch('os.path.isfile')
    def test_read_generator_file_fail_2(self, mock_isfile):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'COAL', 'BadMW', '100', 'America/Edmonton'\n")
        mock_isfile.return_value = False
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            with self.assertRaises(Exception) as context:
                gf = generator_file("TestFile")

            # print("Context: '%s'" % str(context.exception))
            self.assertTrue(("File TestFile Line 1 bad format, Error "
                             "'could not convert string to float: 'BadMW'' "
                             ": 'COAL', 'BadMW', '100', 'America/Edmonton'")
                             in str(context.exception))

    @patch('os.path.isfile')
    def test_read_generator_file_fail_3(self, mock_isfile):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'COAL', '1000', 'BADGHG', 'America/Edmonton'\n")
        mock_isfile.return_value = False
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            with self.assertRaises(Exception) as context:
                gf = generator_file("TestFile")

            # print("Context: '%s'" % str(context.exception))
            self.assertTrue(("File TestFile Line 1 bad format, "
                             "Error 'could not convert string to "
                             "float: 'BADGHG'' : 'COAL', '1000', "
                             "'BADGHG', 'America/Edmonton'") in str(context.exception))

    @patch('os.path.isfile')
    def test_read_generator_file_fail_4(self, mock_isfile):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'COAL', '1000', '100'\n")
        mock_isfile.return_value = False
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            with self.assertRaises(Exception) as context:
                gf = generator_file("TestFile")

            # print("Context: '%s'" % str(context.exception))
            self.assertTrue(("File TestFile Line 1 bad format, "
                             "Error 'list index out of range' : "
                             "'COAL', '1000', '100'") in str(context.exception))

    @patch('os.path.isfile')
    def test_get_total_capacity(self, mock_isfile):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'COAL', '1000', '100', 'America/Edmonton'\n"
                    "'NATGAS', '1001', '20', 'America/Regina'\n"
                    "'NUCLEAR', '1002', '1', 'America/Toronto'\n"
                    "'SOLAR_PV', '1003', '15', 'America/Vancouver'\n"
                    "'HYDRO_RES', '1004', '8', 'America/Montreal'\n")
        mock_isfile.return_value = False
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            gf = generator_file("TestFile")
            self.assertTrue(mock_file.called)
            tot_cap = gf.get_total_capacity("NoDate")
            self.assertEqual(tot_cap, 5010.0)

    @patch('os.path.isfile')
    def test_get_ghg_emissions_success(self, mock_isfile):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'COAL', '1000', '100', 'America/Edmonton'\n"
                    "'NATGAS', '1001', '20', 'America/Regina'\n"
                    "'NUCLEAR', '1002', '1', 'America/Toronto'\n"
                    "'SOLAR_PV', '1003', '15', 'America/Vancouver'\n"
                    "'HYDRO_RES', '1004', '8', 'America/Montreal'\n")
        mock_isfile.return_value = False
        date = datetime(2000, 1, 1, hour=0)
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            gf = generator_file("TestFile")
            self.assertTrue(mock_file.called)
            self.assertEqual(gf.sorted_db, {})
            tot_cap = gf.get_total_capacity(date) 
            self.assertEqual(tot_cap, 5010.0)
            self.assertEqual(gf.sorted_db, {})

            ghg, f_ghg, gen_db  = gf.get_ghg_emissions(1000.0, date)
            self.assertEqual(ghg, 1000*1)
            self.assertEqual(f_ghg, 0)
            self.assertEqual(len(gen_db.keys()), 1)
            self.assertEqual(gen_db["NUCLEAR"][0], 1000)
            self.assertEqual(gen_db["NUCLEAR"][1], 1000*1)

            ghg, f_ghg, gen_db   = gf.get_ghg_emissions(2000.0, date)
            self.assertEqual(ghg, 1002*1 + 998*8)
            self.assertEqual(f_ghg, 0)
            self.assertEqual(len(gen_db.keys()), 2)
            self.assertEqual(gen_db["NUCLEAR"][0], 1002)
            self.assertEqual(gen_db["NUCLEAR"][1], 1002*1)
            self.assertEqual(gen_db["HYDRO_RES"][0], 998)
            self.assertEqual(gen_db["HYDRO_RES"][1], 998*8)

            ghg, f_ghg, gen_db   = gf.get_ghg_emissions(3000.0, date)
            self.assertEqual(ghg, 1002*1 + 1004*8 + 994*15)
            self.assertEqual(f_ghg, 0)
            self.assertEqual(len(gen_db.keys()), 3)
            self.assertEqual(gen_db["NUCLEAR"][0], 1002)
            self.assertEqual(gen_db["NUCLEAR"][1], 1002*1)
            self.assertEqual(gen_db["HYDRO_RES"][0], 1004)
            self.assertEqual(gen_db["HYDRO_RES"][1], 1004*8)
            self.assertEqual(gen_db["SOLAR_PV"][0], 994)
            self.assertEqual(gen_db["SOLAR_PV"][1], 994*15)

            ghg, f_ghg, gen_db   = gf.get_ghg_emissions(4000.0, date)
            self.assertEqual(ghg, 1002*1 + 1004*8 + 1003*15 + 991*20)
            self.assertEqual(f_ghg, 991*20)
            self.assertEqual(len(gen_db.keys()), 4)
            self.assertEqual(gen_db["NUCLEAR"][0], 1002)
            self.assertEqual(gen_db["NUCLEAR"][1], 1002*1)
            self.assertEqual(gen_db["HYDRO_RES"][0], 1004)
            self.assertEqual(gen_db["HYDRO_RES"][1], 1004*8)
            self.assertEqual(gen_db["SOLAR_PV"][0], 1003)
            self.assertEqual(gen_db["SOLAR_PV"][1], 1003*15)
            self.assertEqual(gen_db["NATGAS"][0], 991)
            self.assertEqual(gen_db["NATGAS"][1], 991*20)

            ghg, f_ghg, gen_db   = gf.get_ghg_emissions(5000.0, date)
            self.assertEqual(ghg, 1002*1 + 1004*8 + 1003*15 + 1001*20 + 990*100)
            self.assertEqual(f_ghg, 1001*20 + 990*100)
            self.assertEqual(len(gen_db.keys()), 5)
            self.assertEqual(gen_db["NUCLEAR"][0], 1002)
            self.assertEqual(gen_db["NUCLEAR"][1], 1002*1)
            self.assertEqual(gen_db["HYDRO_RES"][0], 1004)
            self.assertEqual(gen_db["HYDRO_RES"][1], 1004*8)
            self.assertEqual(gen_db["SOLAR_PV"][0], 1003)
            self.assertEqual(gen_db["SOLAR_PV"][1], 1003*15)
            self.assertEqual(gen_db["NATGAS"][0], 1001)
            self.assertEqual(gen_db["NATGAS"][1], 1001*20)
            self.assertEqual(gen_db["COAL"][0], 990)
            self.assertEqual(gen_db["COAL"][1], 990*100)

            ghg, f_ghg, gen_db   = gf.get_ghg_emissions(5010.0, date)
            self.assertEqual(ghg, 1002*1 + 1004*8 + 1003*15 + 1001*20 + 1000*100)

    @patch('os.path.isfile')
    def test_add_generator_success(self, mock_isfile):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'COAL', '10,000', '100', 'America/Edmonton'\n"
                    "'NATGAS', '11,001', '20', 'America/Regina'\n"
                    "'NUCLEAR', '12,002', '1', 'America/Toronto'\n"
                    "'SOLAR_PV', '13,003', '15', 'America/Vancouver'\n"
                    "'HYDRO_RES', '14,004', '8', 'America/Montreal'\n")
        mock_isfile.return_value = False
        date = datetime(2000, 1, 1, hour=0)
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            gf = generator_file("TestFile")
            self.assertTrue(mock_file.called)
            self.assertEqual(gf.sorted_db, {})
            tot_cap = gf.get_total_capacity(date)
            self.assertEqual(tot_cap, 60010.0)
            self.assertEqual(gf.sorted_db, {})

            gf.add_generator(['COAL', '9,876', '20', 'America/Regina'], "")
            self.assertEqual(gf.gen_db['COAL'].mw, 19876.0)
            self.assertEqual(gf.gen_db['COAL'].ghg, 20.0)
            self.assertEqual(gf.gen_db['COAL'].tz_str, 'America/Regina')
            self.assertEqual(gf.gen_db['COAL'].gen_files, [])
            self.assertTrue(gf.gen_db['COAL'].min_time is None)
            self.assertTrue(gf.gen_db['COAL'].max_time is None)

            gf.add_generator(['NATGAS', '0.0', '99.0', ''], "")
            self.assertEqual(gf.gen_db['NATGAS'].mw, 11001.0)
            self.assertEqual(gf.gen_db['NATGAS'].ghg, 99.0)
            self.assertEqual(gf.gen_db['NATGAS'].tz_str, 'America/Regina')
            self.assertEqual(gf.gen_db['NATGAS'].gen_files, [])
            self.assertTrue(gf.gen_db['NATGAS'].min_time is None)
            self.assertTrue(gf.gen_db['NATGAS'].max_time is None)

            gf.add_generator(['NUCLEAR', '0.0', '', 'NewTimeZone'], "")
            self.assertEqual(gf.gen_db['NUCLEAR'].mw, 12002.0)
            self.assertEqual(gf.gen_db['NUCLEAR'].ghg, 1.0)
            self.assertEqual(gf.gen_db['NUCLEAR'].tz_str, 'NewTimeZone')
            self.assertEqual(gf.gen_db['NUCLEAR'].gen_files, [])
            self.assertTrue(gf.gen_db['NUCLEAR'].min_time is None)
            self.assertTrue(gf.gen_db['NUCLEAR'].max_time is None)


    @patch('os.path.isfile')
    def test_get_ghg_emissions_failure(self, mock_isfile):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'COAL', '1000', '100', 'America/Edmonton'\n"
                    "'NATGAS', '1001', '20', 'America/Regina'\n"
                    "'NUCLEAR', '1002', '1', 'America/Toronto'\n"
                    "'SOLAR_PV', '1003', '15', 'America/Vancouver'\n"
                    "'HYDRO_RES', '1004', '8', 'America/Montreal'\n")
        mock_isfile.return_value = False
        date = datetime(2000, 1, 1, hour=0)
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            gf = generator_file("TestFile")
            self.assertTrue(mock_file.called)
            self.assertEqual(gf.sorted_db, {})
            tot_cap = gf.get_total_capacity(date)
            self.assertEqual(tot_cap, 5010.0)
            self.assertEqual(gf.sorted_db, {})

            ghg = gf.get_ghg_emissions(6000.0, date)

    @patch('os.path.isfile')
    @patch('builtins.print')
    def test_write_generator_file(self, mock_print, mock_isfile):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'COAL', '1000', '100', 'America/Edmonton'\n"
                    "'NATGAS', '1001', '20', 'America/Regina'\n"
                    "'NUCLEAR', '1002', '1', 'America/Toronto'\n"
                    "'SOLAR_PV', '1003', '15', 'America/Vancouver'\n"
                    "'HYDRO_RES', '1004', '8', 'America/Montreal'\n")
        mock_isfile.return_value = False
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            gf = generator_file("TestFile")
            self.assertTrue(mock_file.called)
            self.assertEqual(gf.sorted_db, {})
        with patch("builtins.open", mock_open()) as mock_out:
            gf.write_generator_file("FakeFile")
        self.assertEqual(mock_print.call_count, 6)
        mock_out.assert_called_with("FakeFile", "w")
        calls = [
           call("Fuel, Capacity, GHG_MWh, Timezone", file=mock_out()), 
           call("'COAL', '1000.0', '100.0', 'America/Edmonton'",
                                                     file=mock_out()), 
           call("'NATGAS', '1001.0', '20.0', 'America/Regina'",
                                                     file=mock_out()), 
           call("'NUCLEAR', '1002.0', '1.0', 'America/Toronto'",
                                                     file=mock_out()), 
           call("'SOLAR_PV', '1003.0', '15.0', 'America/Vancouver'",
                                                     file=mock_out()), 
           call("'HYDRO_RES', '1004.0', '8.0', 'America/Montreal'",
                                                     file=mock_out())]
        mock_print.assert_has_calls(calls, any_order=True)
        self.assertEqual(mock_print.call_count, 6)

if __name__ == '__main__':
    unittest.main()
