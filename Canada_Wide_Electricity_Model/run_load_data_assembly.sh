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
./BC_Spreadsheet_Files.py -a > load_db.txt
check_rc 'British Columbia'
cd ..

cd 02_Alberta
echo 'Starting Alberta...'
rm -f gen__bio.txt
rm -f gen__co.txt
rm -f gen__res.txt
rm -f gen__pv_AB_actual.txt
rm -f gen__wind.txt
./AB_Spreadsheet_File.py -x Hourly-Metered-Volumes-and-Pool-Price-and-AIL-01-2008-10-2020.xlsx -a CSD-Assets.xlsx -g gen_db_AB_2019.txt -p gen__pv_AB_actual.txt > load_db.txt
check_rc 'Alberta'
cd ..

# NOTE, INFW: Saskatchewan and Manitoba are dependent on British Columbia data for now

echo 'Starting Saskatchewan...'
rm -f 03_Saskatchewan/load_db.txt
Common/data_adapter.py -s 01_British_Columbia -t 03_Saskatchewan -r 0.3333333333 -l
check_rc 'Saskatchewan'

echo 'Starting Manitoba...'
rm -f 04_Manitoba/load_db.txt
Common/data_adapter.py -s 01_British_Columbia -t 04_Manitoba -r 0.3333333333 -l
check_rc 'Manitoba'

cd 05_Ontario
echo 'Starting Ontario...'
./ON_Spreadsheet_Files.py -a -d > load_db.txt
cd ..
check_rc 'Ontario'

cd 06_Quebec
echo 'Starting Quebec...'
./PQ_Spreadsheet_Files.py -i QuebecDemand_Partial_Lower_Line.csv -i QuebecDemand_Partial_Lower_Line_ON_overlap.csv -a QuebecDemand_Upper_Line.csv -y 2014 -a QuebecDemand_Upper_Supplemental.csv -c Quebec_Daily_Demand_Curve_2019_Jan_22.csv > load_db.txt
cd ..
check_rc load_file_PQ.txt

cd 07_New_Brunswick
echo 'Starting New Brunswick...'
./NB_Spreadsheet_Files.py -a > load_db.txt
cd ..
check_rc 'New Brunswick'

cd 08_Nova_Scotia
echo 'Starting Nova Scotia...'
./NS_Spreadsheet_Files.py -a -y 2020 > load_db.txt
check_rc 'Nova Scotia'
./NS_Spreadsheet_Files.py -a -y 2021 > load_db_2021.txt
check_rc 'Nova Scotia 2021'
cd ..

cd 09_Prince_Edward_Island
echo 'Starting Prince Edward Island...'
./PEI_Spreadsheet_Files.py -y 2020 -c PEI_Load_2020_01.csv -c PEI_Load_2020_02.csv -c PEI_Load_2020_03.csv -c PEI_Load_2020_04.csv -c PEI_Load_2020_05.csv -c PEI_Load_2020_06.csv -c PEI_Load_2020_07.csv -c PEI_Load_2020_08.csv -c PEI_Load_2020_09.csv -c PEI_Load_2020_10.csv -c PEI_Load_2020_11.csv -c PEI_Load_2020_12.csv > load_db.txt
check_rc 'Prince Edward Island Load 2020'
./PEI_Spreadsheet_Files.py -y 2020 -c PEI_Wind_2020_01.csv -c PEI_Wind_2020_02.csv -c PEI_Wind_2020_03.csv -c PEI_Wind_2020_04.csv -c PEI_Wind_2020_05.csv -c PEI_Wind_2020_06.csv -c PEI_Wind_2020_07.csv -c PEI_Wind_2020_08.csv -c PEI_Wind_2020_09.csv -c PEI_Wind_2020_10.csv -c PEI_Wind_2020_11.csv -c PEI_Wind_2020_12.csv -n > gen__wind.txt
check_rc 'Prince Edward Island Wind 2020'
./PEI_Spreadsheet_Files.py -y 2021 -c PEI_Load_2021_01.csv -c PEI_Load_2021_02.csv -c PEI_Load_2021_03.csv -c PEI_Load_2021_04.csv -c PEI_Load_2021_05.csv -c PEI_Load_2021_06.csv -c PEI_Load_2021_07.csv -c PEI_Load_2021_08.csv -c PEI_Load_2021_09.csv -c PEI_Load_2021_10.csv -c PEI_Load_2021_11.csv -c PEI_Load_2021_12.csv > load_db_2021.txt
check_rc 'Prince Edward Island Load 2021'
./PEI_Spreadsheet_Files.py -y 2021 -c PEI_Wind_2021_01.csv -c PEI_Wind_2021_02.csv -c PEI_Wind_2021_03.csv -c PEI_Wind_2021_04.csv -c PEI_Wind_2021_05.csv -c PEI_Wind_2021_06.csv -c PEI_Wind_2021_07.csv -c PEI_Wind_2021_08.csv -c PEI_Wind_2021_09.csv -c PEI_Wind_2021_10.csv -c PEI_Wind_2021_11.csv -c PEI_Wind_2021_12.csv -n > gen__wind_2021.txt
check_rc 'Prince Edward Island Wind 2021'
cd ..

cd 10_Newfoundland_and_Labrador
echo 'Starting Newfoundland and Labrador...'
./NL_pdf_files.py -d ../www.pub.nl.ca -l > load_db.txt
check_rc 'Newfoundland and Labrador'
cd ..

