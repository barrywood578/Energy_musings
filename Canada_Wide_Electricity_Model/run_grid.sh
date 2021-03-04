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
Common/grid.py -d 01_British_Columbia/load_db.txt -g 01_British_Columbia/gen_db.txt -p 01_British_Columbia/gen_pv.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00"
check_rc 'British Columbia'

echo 'Starting Alberta...'
Common/grid.py -d 02_Alberta/load_db.txt -g 02_Alberta/gen_db.txt -p 02_Alberta/gen_pv.txt -w 02_Alberta/gen_wind.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00"
check_rc 'Alberta'

echo 'Starting Ontario...'
Common/grid.py -d 05_Ontario/load_db.txt -g 05_Ontario/gen_db.txt -p 05_Ontario/gen_pv.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00"
check_rc 'Ontario'

echo 'Starting Quebec...'
Common/grid.py -d 06_Quebec/load_db.txt -g 06_Quebec/gen_db.txt -s "2014-01-01 05:00" -e "2015-01-01 04:00"
check_rc load_file_PQ.txt

echo 'Starting New Brunswick...'
Common/grid.py -d 07_New_Brunswick/load_db.txt -g 07_New_Brunswick/gen_db.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00"
check_rc 'New Brunswick'

echo 'Starting Nova Scotia...'
Common/grid.py -d 08_Nova_Scotia/load_db.txt -g 08_Nova_Scotia/gen_db.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00"
check_rc 'Nova Scotia'

echo 'Starting Prince Edward Island...'
Common/grid.py -d 09_Prince_Edward_Island/load_db.txt -g 09_Prince_Edward_Island/gen_db.txt -w 09_Prince_Edward_Island/gen_wind.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00"
check_rc 'Prince Edward Island Wind'

echo 'Starting Newfoundland and Labrador...'
Common/grid.py -d 10_Newfoundland_and_Labrador/load_db.txt -g 10_Newfoundland_and_Labrador/gen_db.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00"
check_rc 'Newfoundland and Labrador'
