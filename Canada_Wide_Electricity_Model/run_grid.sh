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
Common/grid.py -d 01_British_Columbia/load_db.txt -g 01_British_Columbia/gen_db.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00" > /dev/null
check_rc 'British Columbia'

echo 'Starting Alberta...'
Common/grid.py -d 02_Alberta/load_db.txt -g 02_Alberta/gen_db.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00" > /dev/null
check_rc 'Alberta'

echo 'Starting Saskatchewan...'
Common/grid.py -d 03_Saskatchewan/load_db.txt -g 03_Saskatchewan/gen_db.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00" > /dev/null
check_rc 'Saskatchewan'

echo 'Starting Manitoba...'
Common/grid.py -d 04_Manitoba/load_db.txt -g 04_Manitoba/gen_db.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00" > /dev/null
check_rc 'Manitoba'

echo 'Starting Ontario...'
Common/grid.py -d 05_Ontario/load_db.txt -g 05_Ontario/gen_db.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00" > /dev/null
check_rc 'Ontario'

echo 'Starting Quebec...'
Common/grid.py -d 06_Quebec/load_db.txt -g 06_Quebec/gen_db.txt -s "2014-01-01 05:00" -e "2015-01-01 04:00" > /dev/null
check_rc load_file_PQ.txt

echo 'Starting New Brunswick...'
Common/grid.py -d 07_New_Brunswick/load_db.txt -g 07_New_Brunswick/gen_db.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00" > /dev/null
check_rc 'New Brunswick'

echo 'Starting Nova Scotia...'
Common/grid.py -d 08_Nova_Scotia/load_db.txt -g 08_Nova_Scotia/gen_db.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00" > /dev/null
check_rc 'Nova Scotia'

echo 'Starting Prince Edward Island...'
Common/grid.py -d 09_Prince_Edward_Island/load_db.txt -g 09_Prince_Edward_Island/gen_db.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00" > /dev/null
check_rc 'Prince Edward Island Wind'

echo 'Starting Newfoundland and Labrador...'
Common/grid.py -d 10_Newfoundland_and_Labrador/load_db.txt -g 10_Newfoundland_and_Labrador/gen_db.txt -s "2019-01-01 00:00" -e "2019-12-31 23:00" > /dev/null
check_rc 'Newfoundland and Labrador'

echo 'Starting Canada...'
Common/grid.py -m 01_British_Columbia -m 02_Alberta -m 03_Saskatchewan -m 04_Manitoba -m 05_Ontario -m 06_Quebec -m 07_New_Brunswick -m 08_Nova_Scotia -m 09_Prince_Edward_Island -m 10_Newfoundland_and_Labrador -s "2019-01-01 00:00" -e "2019-12-31 23:00" > /dev/null
check_rc 'Canada'
