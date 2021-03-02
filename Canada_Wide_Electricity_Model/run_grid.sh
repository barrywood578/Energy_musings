#!/bin/bash
#
# This script runs a grid simulation for each province,
# for the data available for each province.  This is a
# sanity check for both the data and the grid simulator.

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

echo 'Starting British Columbia...'
Common/grid.py -d 01_British_Columbia/load_db_BC.txt -g 01_British_Columbia/gen_db_BC.txt -p 01_British_Columbia/gen_pv_BC.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00"
check_rc 'British Columbia'

echo 'Starting Alberta...'
Common/grid.py -d 02_Alberta/load_db_AB.txt -g 02_Alberta/gen_db_AB.txt -p 02_Alberta/gen_pv_AB.txt -w 02_Alberta/gen_wind_AB_actual.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00"
check_rc 'Alberta'

echo 'Starting Ontario...'
Common/grid.py -d 05_Ontario/load_db_ON.txt -g 05_Ontario/gen_db_ON.txt -p 05_Ontario/gen_pv_ON.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00"
check_rc 'Ontario'

echo 'Starting Quebec...'
Common/grid.py -d 06_Quebec/load_db_PQ.txt -g 06_Quebec/gen_db_PQ.txt -s "2014-01-01 05:00" -e "2015-01-01 04:00"
check_rc load_file_PQ.txt

echo 'Starting New Brunswick...'
Common/grid.py -d 07_New_Brunswick/load_db_NB.txt -g 07_New_Brunswick/gen_db_NB.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00"
check_rc 'New Brunswick'

echo 'Starting Nova Scotia...'
Common/grid.py -d 08_Nova_Scotia/load_db_NS.txt -g 08_Nova_Scotia/gen_db_NS.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00"
check_rc 'Nova Scotia'

echo 'Starting Prince Edward Island...'
Common/grid.py -d 09_Prince_Edward_Island/load_db_PEI.txt -g 09_Prince_Edward_Island/gen_db_PEI.txt -w 09_Prince_Edward_Island/gen_wind_PEI_actual.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00"
check_rc 'Prince Edward Island Wind'

echo 'Starting Newfoundland and Labrador...'
Common/grid.py -d 10_Newfoundland_and_Labrador/load_db_NL.txt -g 10_Newfoundland_and_Labrador/gen_db_NL.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00"
check_rc 'Newfoundland and Labrador'
