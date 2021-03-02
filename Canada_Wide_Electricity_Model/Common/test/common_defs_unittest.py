#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Unit test for common definitions

"""

import os
import path
from common_defs import *
import unittest
from math import isnan

class TestConstants(unittest.TestCase):

    def setUp(self):
        pass

    def test_constants(self):
        self.assertEqual(SEPARATOR, "', '")
        self.assertEqual(KEY_SEPARATOR, "-")
        self.assertEqual(START_END, "'")
        self.assertEqual(EXCEL_FILE_EXTENSION, ".xlsx")
        self.assertEqual(CSV_FILE_EXTENSION, ".csv")
        self.assertEqual(PDF_FILE_EXTENSION, ".pdf")
        self.assertEqual(DATE_FORMAT, '%Y-%m-%d %H:%M')
        
        self.assertTrue(isnan(INVALID_VALUE))
        self.assertEqual(INVALID_LIST, "INVALID")

        self.assertEqual(FUEL_NUCLEAR, 'NUCLEAR')
        self.assertEqual(FUEL_HYDRO_RESERVOIR, 'HYDRO_RES')
        self.assertEqual(FUEL_HYDRO_RUN_OF_RVR, 'HYDRO_RUN')
        self.assertEqual(FUEL_CO_GEN, 'CO_GEN')
        self.assertEqual(FUEL_BIOMASS, 'BIOMASS')
        self.assertEqual(FUEL_NATURAL_GAS, 'NATGAS')
        self.assertEqual(FUEL_OIL, 'OIL')
        self.assertEqual(FUEL_COAL, 'COAL')
        self.assertEqual(FUEL_WIND, 'WIND')
        self.assertEqual(FUEL_SOLAR_PV, 'SOLAR_PV')
        self.assertEqual(FUEL_STORAGE, 'STORAGE')

    def test_find_fuel(self):
        self.assertEqual(find_fuel("NOFUEL"), '')
        self.assertEqual(find_fuel("nuclear"), 'NUCLEAR')
        self.assertEqual(find_fuel("hydro"), 'HYDRO_RES')
        self.assertEqual(find_fuel("reservoir"), 'HYDRO_RES')
        self.assertEqual(find_fuel("run of river"), 'HYDRO_RUN')
        self.assertEqual(find_fuel("run-of-the-river"), 'HYDRO_RUN')
        self.assertEqual(find_fuel("waste heat"), 'CO_GEN')
        self.assertEqual(find_fuel("blast furnace"), 'CO_GEN')
        self.assertEqual(find_fuel("cogeneration"), 'CO_GEN')
        self.assertEqual(find_fuel("biomass"), 'BIOMASS')
        self.assertEqual(find_fuel("biogas"), 'BIOMASS')
        self.assertEqual(find_fuel("waste"), 'BIOMASS')
        self.assertEqual(find_fuel("other"), 'BIOMASS')
        self.assertEqual(find_fuel("natural gas"), 'NATGAS')
        self.assertEqual(find_fuel("dual fuel"), 'NATGAS')
        self.assertEqual(find_fuel("gas"), 'NATGAS')
        self.assertEqual(find_fuel("simple_cycle"), 'NATGAS')
        self.assertEqual(find_fuel("combined_cycle"), 'NATGAS')
        self.assertEqual(find_fuel("fuel oil"), 'OIL')
        self.assertEqual(find_fuel("diesel"), 'OIL')
        self.assertEqual(find_fuel("coal"), 'COAL')
        self.assertEqual(find_fuel("coke"), 'COAL')
        self.assertEqual(find_fuel("wind"), 'WIND')
        self.assertEqual(find_fuel("solar"), 'SOLAR_PV')
        self.assertEqual(find_fuel("photoelectric"), 'SOLAR_PV')
        self.assertEqual(find_fuel("photovoltaic"), 'SOLAR_PV')
        self.assertEqual(find_fuel("battery"), 'STORAGE')
        self.assertEqual(find_fuel("pumped"), 'STORAGE')

    def test_constants_completeness(self):
        # The following lines confirm that all definitions in the
        # common_defs.py file are checked, assuming each definition
        # has exactly one '=' character.
        file_path = "common_defs.py"
        if not os.path.isfile(file_path):
            file_path = "Common/common_defs.py"
        with open(file_path, 'r') as tempfile:
            counts = [line.strip().count('=') for line in tempfile.readlines()]
        self.assertEqual(sum(counts), 22)

if __name__ == '__main__':
    unittest.main()
