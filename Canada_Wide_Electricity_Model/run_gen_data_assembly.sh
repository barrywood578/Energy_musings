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

if [ $# -eq 0 ]; then
	KEY_FILE="DEMO_KEY"
else
	KEY_FILE=$1
fi

echo 'KEY_FILE is ' ${KEY_FILE}

echo 'British Columbia Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_British_Columbia' -t 'America/Vancouver' -k ${KEY_FILE} -s 01_British_Columbia/gen_pv_BC.txt -g Common/gen_db_GHG.txt > 01_British_Columbia/gen_db_BC.txt
check_rc 'British Columbia'

echo 'Alberta Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Alberta' -t 'America/Edmonton' -k ${KEY_FILE} -s 02_Alberta/gen_pv_AB.txt -g Common/gen_db_GHG.txt > 02_Alberta/gen_db_AB.txt
check_rc 'Alberta'

echo 'Saskatchewan Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Saskatchewan' -t 'America/Regina' -k ${KEY_FILE} -s 03_Saskatchewan/gen_pv_SK.txt -g Common/gen_db_GHG.txt > 03_Saskatchewan/gen_db_SK.txt
check_rc 'Saskatchewan'

echo 'Manitoba Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Manitoba' -t 'America/Winnipeg' -k ${KEY_FILE} -s 04_Manitoba/gen_pv_MB.txt -g Common/gen_db_GHG.txt > 04_Manitoba/gen_db_MB.txt
check_rc 'Manitoba'

echo 'Ontario Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Ontario' -t 'America/Toronto' -k ${KEY_FILE} -s 05_Ontario/gen_pv_ON.txt -g Common/gen_db_GHG.txt > 05_Ontario/gen_db_ON.txt
check_rc 'Ontario'

echo 'Quebec Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Quebec' -t 'America/Montreal' -k ${KEY_FILE} -s 06_Quebec/gen_pv_PQ.txt -g Common/gen_db_GHG.txt > 06_Quebec/gen_db_PQ.txt
check_rc 'Quebec'

echo 'New Brunswick Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_New_Brunswick' -t 'America/Moncton' -k ${KEY_FILE} -s 07_New_Brunswick/gen_pv_NB.txt -g Common/gen_db_GHG.txt > 07_New_Brunswick/gen_db_NB.txt
check_rc 'New Brunswick'

echo 'Nova Scotia Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Nova_Scotia' -t 'America/Halifax' -k ${KEY_FILE} -s 08_Nova_Scotia/gen_pv_NS.txt -g Common/gen_db_GHG.txt > 08_Nova_Scotia/gen_db_NS.txt
check_rc 'Nova Scotia'

echo 'Prince Edward Island Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Prince_Edward_Island' -t 'America/Charlottetown' -k ${KEY_FILE} -s 09_Prince_Edward_Island/gen_pv_PEI.txt -g Common/gen_db_GHG.txt > 09_Prince_Edward_Island/gen_db_PEI.txt
check_rc 'Prince Edward Island'

echo 'Newfoundland and Labrador Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Newfoundland_and_Labrador' -t 'America/St_Johns' -k ${KEY_FILE} -s 10_Newfoundland_and_Labrador/gen_pv_NL.txt -g Common/gen_db_GHG.txt > 10_Newfoundland_and_Labrador/gen_db_NL.txt
check_rc 'Newfoundland and Labrador'

