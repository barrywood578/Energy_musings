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

KEYWORDS="keywords"
FILENAME="filename"

FILE_GEN_PV="gen_pv.txt"
FILE_GEN_WIND="gen_wind.txt"
FILE_LOAD_DB="load_db.txt"
FILE_GEN_DB="gen_db.txt"

MAPPING_KEYWORDS = {
    FUEL_NUCLEAR : {KEYWORDS: ['nuclear'],
                    FILENAME:""},
    FUEL_HYDRO_RESERVOIR :
                   {KEYWORDS: ['hydro', "reservoir"],
                    FILENAME:"gen_res.txt"},
    FUEL_HYDRO_RUN_OF_RVR :
                   {KEYWORDS: ['hydro', "run of river", "run-of-the-river"],
                    FILENAME:"gen_rvr.txt"},
    FUEL_CO_GEN :  {KEYWORDS: ['waste heat', 'blast furnace', 'cogeneration'],
                    FILENAME:"gen_co.txt"},
    FUEL_BIOMASS : {KEYWORDS: ['biomass', 'biogas', 'waste', 'landfill gas', 'digester gas', 'other'],
                    FILENAME:"gen_bio.txt"},
    FUEL_NATURAL_GAS :
                   {KEYWORDS: ['natural gas', 'dual fuel', 'gas', 'simple_cycle', 'combined_cycle'],
                    FILENAME:""},
    FUEL_OIL :     {KEYWORDS: ['fuel oil', 'diesel'],
                    FILENAME:""},
    FUEL_COAL:     {KEYWORDS: ['coal', 'coke'],
                    FILENAME:""},
    FUEL_WIND :    {KEYWORDS: ['wind'],
                    FILENAME: FILE_GEN_WIND},
    FUEL_SOLAR_PV: {KEYWORDS: ['solar', 'photoelectric', 'photovoltaic'],
                    FILENAME: FILE_GEN_PV},
    FUEL_STORAGE : {KEYWORDS: ['battery', 'pumped'],
                    FILENAME:""}
}

def find_fuel(target):
    target_l = target.strip().lower()
    for fuel in MAPPING_KEYWORDS.keys():
        for substr in MAPPING_KEYWORDS[fuel][KEYWORDS]:
            if substr in target_l:
                return fuel
    return ''

def get_filename(fuel):
    try:
        return MAPPING_KEYWORDS[fuel][FILENAME]
    except KeyError:
        return ''
