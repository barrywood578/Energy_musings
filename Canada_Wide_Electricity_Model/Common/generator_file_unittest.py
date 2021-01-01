#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Support for the common "generation file" file format.

    Each file line is an instance of:
    Fuel, Capacity in MW, GHG per MWh, timezone

"""

from optparse import OptionParser
from collections import OrderedDict
import operator
import sys
import os
import logging
from datetime import datetime, timezone
from common_defs import *
from generator_file import generator, generator_file

import unittest
import mock
from unittest.mock import patch, mock_open, call

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

    def test_read_generator_file_success(self):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'Coal', '1000', '100', 'America/Edmonton'\n"
                    "'NatGas', '1001', '20', 'America/Regina'\n"
                    "'Nuclear', '1002', '1', 'America/Toronto'\n"
                    "'SolarPV', '1003', '15', 'America/Vancouver'\n"
                    "'Hydro', '1004', '8', 'America/Montreal'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            gf = generator_file()
            self.assertFalse(mock_file.called)

            gf.read_generator_file("TestFile")
            mock_file.assert_called_with("TestFile", 'r')
            self.assertEqual(len(gf.gen_db.keys()), 5)
            self.assertTrue("Coal" in gf.gen_db)
            gen_obj = gf.gen_db["Coal"] 
            self.assertEqual(gen_obj.mw, 1000.0)
            self.assertEqual(gen_obj.ghg, 100.0)
            self.assertEqual(gen_obj.tz_str, "America/Edmonton")
            self.assertTrue("NatGas" in gf.gen_db)
            gen_obj = gf.gen_db["NatGas"] 
            self.assertEqual(gen_obj.mw, 1001.0)
            self.assertEqual(gen_obj.ghg, 20.0)
            self.assertEqual(gen_obj.tz_str, "America/Regina")
            self.assertTrue("Nuclear" in gf.gen_db)
            gen_obj = gf.gen_db["Nuclear"] 
            self.assertEqual(gen_obj.mw, 1002.0)
            self.assertEqual(gen_obj.ghg, 1.0)
            self.assertEqual(gen_obj.tz_str, "America/Toronto")
            self.assertTrue("SolarPV" in gf.gen_db)
            gen_obj = gf.gen_db["SolarPV"] 
            self.assertEqual(gen_obj.mw, 1003.0)
            self.assertEqual(gen_obj.ghg, 15.0)
            self.assertEqual(gen_obj.tz_str, "America/Vancouver")
            self.assertTrue("Hydro" in gf.gen_db)
            gen_obj = gf.gen_db["Hydro"] 
            self.assertEqual(gen_obj.mw, 1004.0)
            self.assertEqual(gen_obj.ghg, 8.0)
            self.assertEqual(gen_obj.tz_str, "America/Montreal")

            self.assertEqual(gf.sorted_db, {})

    def test_read_generator_file_fail_1(self):
        file_data= ("Bad_Header\n" 
                    "'Coal', '1000', '100', 'America/Edmonton'\n"
                    "'NatGas', '1001', '20', 'America/Regina'\n"
                    "'Nuclear', '1002', '1', 'America/Toronto'\n"
                    "'SolarPV', '1003', '15', 'America/Vancouver'\n"
                    "'Hydro', '1004', '8', 'America/Montreal'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            with self.assertRaises(Exception) as context:
                gf = generator_file("TestFile")

            # print("Context: '%s'" % str(context.exception))
            self.assertTrue(("File header is 'Bad_Header', not "
                             "'Fuel, Capacity, GHG_MWh, Timezone'.  Halting.")
                             in str(context.exception))

    def test_read_generator_file_fail_2(self):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'Coal', 'BadMW', '100', 'America/Edmonton'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            with self.assertRaises(Exception) as context:
                gf = generator_file("TestFile")

            # print("Context: '%s'" % str(context.exception))
            self.assertTrue(("File TestFile Line 1 bad format, Error "
                             "'could not convert string to float: 'BadMW'' "
                             ": 'Coal', 'BadMW', '100', 'America/Edmonton'")
                             in str(context.exception))

    def test_read_generator_file_fail_3(self):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'Coal', '1000', 'BADGHG', 'America/Edmonton'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            with self.assertRaises(Exception) as context:
                gf = generator_file("TestFile")

            # print("Context: '%s'" % str(context.exception))
            self.assertTrue(("File TestFile Line 1 bad format, "
                             "Error 'could not convert string to "
                             "float: 'BADGHG'' : 'Coal', '1000', "
                             "'BADGHG', 'America/Edmonton'") in str(context.exception))

    def test_read_generator_file_fail_4(self):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'Coal', '1000', '100'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            with self.assertRaises(Exception) as context:
                gf = generator_file("TestFile")

            # print("Context: '%s'" % str(context.exception))
            self.assertTrue(("File TestFile Line 1 bad format, "
                             "Error 'list index out of range' : "
                             "'Coal', '1000', '100'") in str(context.exception))

    def test_get_total_capacity(self):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'Coal', '1000', '100', 'America/Edmonton'\n"
                    "'NatGas', '1001', '20', 'America/Regina'\n"
                    "'Nuclear', '1002', '1', 'America/Toronto'\n"
                    "'SolarPV', '1003', '15', 'America/Vancouver'\n"
                    "'Hydro', '1004', '8', 'America/Montreal'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            gf = generator_file("TestFile")
            self.assertTrue(mock_file.called)
            tot_cap = gf.get_total_capacity("NoDate")
            self.assertEqual(tot_cap, 5010.0)

    def test_get_ghg_emissions_success(self):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'Coal', '1000', '100', 'America/Edmonton'\n"
                    "'NatGas', '1001', '20', 'America/Regina'\n"
                    "'Nuclear', '1002', '1', 'America/Toronto'\n"
                    "'SolarPV', '1003', '15', 'America/Vancouver'\n"
                    "'Hydro', '1004', '8', 'America/Montreal'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            gf = generator_file("TestFile")
            self.assertTrue(mock_file.called)
            self.assertEqual(gf.sorted_db, {})
            tot_cap = gf.get_total_capacity("NoDate")
            self.assertEqual(tot_cap, 5010.0)
            self.assertEqual(gf.sorted_db, {})

            ghg = gf.get_ghg_emissions(1000.0)
            self.assertEqual(ghg, 1000*1)

            ghg = gf.get_ghg_emissions(2000.0)
            self.assertEqual(ghg, 1002*1 + 998*8)

            ghg = gf.get_ghg_emissions(3000.0)
            self.assertEqual(ghg, 1002*1 + 1004*8 + 994*15)

            ghg = gf.get_ghg_emissions(4000.0)
            self.assertEqual(ghg, 1002*1 + 1004*8 + 1003*15 + 991*20)

            ghg = gf.get_ghg_emissions(5000.0)
            self.assertEqual(ghg, 1002*1 + 1004*8 + 1003*15 + 1001*20 + 990*100)

            ghg = gf.get_ghg_emissions(5010.0)
            self.assertEqual(ghg, 1002*1 + 1004*8 + 1003*15 + 1001*20 + 1000*100)

    def test_get_ghg_emissions_failure(self):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'Coal', '1000', '100', 'America/Edmonton'\n"
                    "'NatGas', '1001', '20', 'America/Regina'\n"
                    "'Nuclear', '1002', '1', 'America/Toronto'\n"
                    "'SolarPV', '1003', '15', 'America/Vancouver'\n"
                    "'Hydro', '1004', '8', 'America/Montreal'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            gf = generator_file("TestFile")
            self.assertTrue(mock_file.called)
            self.assertEqual(gf.sorted_db, {})
            tot_cap = gf.get_total_capacity("NoDate")
            self.assertEqual(tot_cap, 5010.0)
            self.assertEqual(gf.sorted_db, {})

            with self.assertRaises(Exception) as context:
                ghg = gf.get_ghg_emissions(6000.0)

            # print("Context: '%s'" % str(context.exception))
            self.assertTrue("Cannot generate 6000.000000 MW" in str(context.exception))

    @patch('builtins.print')
    def test_write_generator_file(self, mock_print):
        file_data= ("Fuel, Capacity, GHG_MWh, Timezone\n" 
                    "'Coal', '1000', '100', 'America/Edmonton'\n"
                    "'NatGas', '1001', '20', 'America/Regina'\n"
                    "'Nuclear', '1002', '1', 'America/Toronto'\n"
                    "'SolarPV', '1003', '15', 'America/Vancouver'\n"
                    "'Hydro', '1004', '8', 'America/Montreal'\n")
        with patch("builtins.open", mock_open(read_data=file_data)) as mock_file:
            gf = generator_file("TestFile")
            self.assertTrue(mock_file.called)
            self.assertEqual(gf.sorted_db, {})
            gf.write_generator_file()
        self.assertEqual(mock_print.call_count, 6)
        calls = [call("Fuel, Capacity, GHG_MWh, Timezone"),
                 call("'Coal', '1000.0', '100.0', 'America/Edmonton'"),
                 call("'Hydro', '1004.0', '8.0', 'America/Montreal'"),
                 call("'NatGas', '1001.0', '20.0', 'America/Regina'"),
                 call("'Nuclear', '1002.0', '1.0', 'America/Toronto'"),
                 call("'SolarPV', '1003.0', '15.0', 'America/Vancouver'")]
        mock_print.assert_has_calls(calls, any_order = False)
if __name__ == '__main__':
    unittest.main()
