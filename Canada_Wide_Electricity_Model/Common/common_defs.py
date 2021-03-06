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
FOSSFUEL="fossil"

FILE_GEN_PV="gen__pv.txt"
FILE_GEN_WIND="gen__wind.txt"
FILE_LOAD_DB="load_db.txt"
FILE_GEN_DB="gen_db.txt"

MAPPING_KEYWORDS = {
    FUEL_NUCLEAR : {KEYWORDS: ['nuclear'],
                    FILENAME:"",
                    FOSSFUEL:False},
    FUEL_HYDRO_RESERVOIR :
                   {KEYWORDS: ['hydro', "reservoir"],
                    FILENAME:"gen__res.txt",
                    FOSSFUEL:False},
    FUEL_HYDRO_RUN_OF_RVR :
                   {KEYWORDS: ['hydro', "run of river", "run-of-the-river"],
                    FILENAME:"gen__rvr.txt",
                    FOSSFUEL:False},
    FUEL_CO_GEN :  {KEYWORDS: ['waste heat', 'blast furnace', 'cogeneration'],
                    FILENAME:"gen__co.txt",
                    FOSSFUEL:False},
    FUEL_BIOMASS : {KEYWORDS: ['biomass', 'biogas', 'waste', 'landfill gas', 'digester gas', 'other'],
                    FILENAME:"gen__bio.txt",
                    FOSSFUEL:False},
    FUEL_NATURAL_GAS :
                   {KEYWORDS: ['natural gas', 'dual fuel', 'gas', 'simple_cycle', 'combined_cycle'],
                    FILENAME:"",
                    FOSSFUEL:True},
    FUEL_OIL :     {KEYWORDS: ['fuel oil', 'diesel'],
                    FILENAME:"",
                    FOSSFUEL:True},
    FUEL_COAL:     {KEYWORDS: ['coal', 'coke'],
                    FILENAME:"",
                    FOSSFUEL:True},
    FUEL_WIND :    {KEYWORDS: ['wind'],
                    FILENAME: FILE_GEN_WIND,
                    FOSSFUEL:False},
    FUEL_SOLAR_PV: {KEYWORDS: ['solar', 'photoelectric', 'photovoltaic'],
                    FILENAME: FILE_GEN_PV,
                    FOSSFUEL:False},
    FUEL_STORAGE : {KEYWORDS: ['battery', 'pumped'],
                    FILENAME:"",
                    FOSSFUEL:False},
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

def get_fossil_fuel(fuel):
    try:
        return MAPPING_KEYWORDS[fuel][FOSSFUEL]
    except KeyError:
        return ''
