#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Constant definitions common to all files.
"""

SEPARATOR = "', '"
KEY_SEPARATOR = "-"
START_END = "'"
EXCEL_FILE_EXTENSION = ".xlsx"
CSV_FILE_EXTENSION = ".csv"
PDF_FILE_EXTENSION = ".pdf"
DATE_FORMAT = '%Y-%m-%d %H:%M'

INVALID_VALUE = float('nan')
INVALID_LIST = "INVALID"

FUEL_NUCLEAR = 'NUCLEAR'
FUEL_HYDRO_RESERVOIR = 'HYDRO_RES'
FUEL_HYDRO_RUN_OF_RVR = 'HYDRO_RUN'
FUEL_CO_GEN = 'CO_GEN'
FUEL_BIOMASS = 'BIOMASS'
FUEL_NATURAL_GAS = 'NATGAS'
FUEL_OIL = 'OIL'
FUEL_COAL = 'COAL'
FUEL_WIND = 'WIND'
FUEL_SOLAR_PV = 'SOLAR_PV'
FUEL_STORAGE = 'STORAGE'

#########################

MAPPING_KEYWORDS = {
    FUEL_NUCLEAR : ['nuclear'],
    FUEL_HYDRO_RESERVOIR : ['hydro', "reservoir"],
    FUEL_HYDRO_RUN_OF_RVR : ['hydro', "run of river", "run-of-the-river"],
    FUEL_CO_GEN : ['waste heat', 'blast furnace', 'cogeneration'],
    FUEL_BIOMASS : ['biomass', 'biogas', 'waste', 'other'],
    FUEL_NATURAL_GAS : ['natural gas', 'dual fuel', 'gas', 'simple_cycle', 'combined_cycle'],
    FUEL_OIL : ['fuel oil', 'diesel'],
    FUEL_COAL: ['coal', 'coke'],
    FUEL_WIND : ['wind'],
    FUEL_SOLAR_PV : ['solar', 'photoelectric', 'photovoltaic'],
    FUEL_STORAGE : ['battery', 'pumped']
}

def find_fuel(target):
    target_l = target.strip().lower()
    for key in MAPPING_KEYWORDS.keys():
        for substr in MAPPING_KEYWORDS[key]:
            if substr in target_l:
                return key
    return ''
