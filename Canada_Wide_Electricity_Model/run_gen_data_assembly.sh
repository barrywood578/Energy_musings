#!/bin/bash
#
# This script runs the generator data assembly procedure for each province.
#
# The generator data is scraped from Wikipedia pages for each province.
# URL's are found in each query.

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

echo 'British Columbia Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_British_Columbia' -t 'America/Vancouver' > 01_British_Columbia/gen_db_BC.txt
check_rc 'British Columbia'

echo 'Alberta Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Alberta' -t 'America/Edmonton' > 02_Alberta/gen_db_AB.txt
check_rc 'Alberta'

echo 'Ontario Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Ontario' -t 'America/Toronto' > 05_Ontario/gen_db_ON.txt
check_rc 'Ontario'

echo 'Quebec Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Quebec' -t 'America/Montreal' > 06_Quebec/gen_db_PQ.txt
check_rc 'Quebec'

echo 'New Brunswick Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_New_Brunswick' -t 'America/Moncton' > 07_New_Brunswick/gen_db_NB.txt
check_rc 'New Brunswick'

echo 'Nova Scotia Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Nova_Scotia' -t 'America/Halifax' > 08_Nova_Scotia/gen_db_NS.txt
check_rc 'Nova Scotia'

echo 'Prince Edward Island Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Prince_Edward_Island' -t 'America/Charlottetown' > 09_Prince_Edward_Island/gen_db_PEI.txt
check_rc 'Prince Edward Island'

echo 'Newfoundland and Labrador Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Newfoundland_and_Labrador' -t 'America/St_Johns' > 10_Newfoundland_and_Labrador/gen_db_NL.txt
check_rc 'Newfoundland and Labrador'

