#!/bin/bash
#
# This script runs the load data assembly procedures for each province.

function check_rc(){
        rc=$?
        echo ---------------------------------------
        if [[ $rc != 0 ]];
        then
                echo $1 ' FAILURE!'
                exit $rc
        else
                echo $1 ' SUCCESS!'
        fi
        echo ---------------------------------------
}

cd 01_British_Columbia
echo 'Starting British Columbia...'
./BC_Spreadsheet_Files.py -a > load_db_BC.txt
check_rc 'British Columbia'

cd ../02_Alberta
echo 'Starting Alberta...'
./AB_Spreadsheet_File.py -x Hourly-Metered-Volumes-and-Pool-Price-and-AIL-01-2008-10-2020.xlsx > load_db_AB.txt
check_rc 'Alberta'

cd ../05_Ontario
echo 'Starting Ontario...'
./ON_Spreadsheet_Files.py -a -d > load_db_ON.txt
check_rc 'Ontario'

cd ../06_Quebec
echo 'Starting Quebec...'
./PQ_Spreadsheet_Files.py -i QuebecDemand_Partial_Lower_Line.csv -i QuebecDemand_Partial_Lower_Line_ON_overlap.csv -a QuebecDemand_Upper_Line.csv -y 2014 -a QuebecDemand_Upper_Supplemental.csv -c Quebec_Daily_Demand_Curve_2019_Jan_22.csv > load_db_PQ.txt
check_rc load_file_PQ.txt

cd ../07_New_Brunswick
echo 'Starting New Brunswick...'
./NB_Spreadsheet_Files.py -a > load_db_NB.txt
check_rc 'New Brunswick'

cd ../08_Nova_Scotia
echo 'Starting Nova Scotia...'
./NS_Spreadsheet_Files.py -a -y 2020 > load_db_NS.txt
check_rc 'Nova Scotia'

cd ../09_Prince_Edward_Island
echo 'Starting Prince Edward Island...'
./PEI_Spreadsheet_Files.py -y 2020 -c PEI_Load_2020_01.csv -c PEI_Load_2020_02.csv -c PEI_Load_2020_03.csv -c PEI_Load_2020_04.csv -c PEI_Load_2020_05.csv -c PEI_Load_2020_06.csv -c PEI_Load_2020_07.csv -c PEI_Load_2020_08.csv -c PEI_Load_2020_09.csv -c PEI_Load_2020_10.csv -c PEI_Load_2020_11.csv > load_db_PEI.txt
check_rc 'Prince Edward Island Load'
./PEI_Spreadsheet_Files.py -y 2020 -c PEI_Wind_2020_01.csv -c PEI_Wind_2020_02.csv -c PEI_Wind_2020_03.csv -c PEI_Wind_2020_04.csv -c PEI_Wind_2020_05.csv -c PEI_Wind_2020_06.csv -c PEI_Wind_2020_07.csv -c PEI_Wind_2020_08.csv -c PEI_Wind_2020_09.csv -c PEI_Wind_2020_10.csv -c PEI_Wind_2020_11.csv > wind_gen_db_PEI.txt
check_rc 'Prince Edward Island Wind'

cd ../10_Newfoundland_and_Labrador
echo 'Starting Newfoundland and Labrador...'
./NL_pdf_files.py -d ../www.pub.nl.ca -l > load_db_NL.txt
check_rc 'Newfoundland and Labrador'

cd ..
