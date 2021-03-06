#!/bin/bash
#
# This script runs the generator data assembly procedure for each province.
#
# The generator data is scraped from Wikipedia pages for each province.
# URL's are found in each query.
#
# Saskatechwan and Manitoba load and specific generation data is derived
# from data published for BC and Alberta.

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
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_British_Columbia' -t 'America/Vancouver' -k ${KEY_FILE} -s 01_British_Columbia/gen__pv.txt -g Common/gen_db_GHG.txt > 01_British_Columbia/gen_db.txt
check_rc 'British Columbia'

echo 'Alberta Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Alberta' -t 'America/Edmonton' -k ${KEY_FILE} -s 02_Alberta/gen__pv.txt -g Common/gen_db_GHG.txt > 02_Alberta/gen_db.txt
check_rc 'Alberta'

# NOTE, INFW: Saskatchewan and Manitoba are dependent on Alberta for hourly generation data.

echo 'Saskatchewan Starting...'
rm -f 03_Saskatchewan/gen__*.txt
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Saskatchewan' -t 'America/Regina' -k ${KEY_FILE} -s 03_Saskatchewan/gen__pv.txt -g Common/gen_db_GHG.txt > 03_Saskatchewan/gen_db.txt
check_rc 'Saskatchewan web scraping'
Common/data_adapter.py -s 02_Alberta -t 03_Saskatchewan -g
check_rc 'Saskatchewan'

echo 'Manitoba Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Manitoba' -t 'America/Winnipeg' -k ${KEY_FILE} -s 04_Manitoba/gen__pv.txt -g Common/gen_db_GHG.txt > 04_Manitoba/gen_db.txt
check_rc 'Manitoba web scraping'
rm -f 04_Manitoba/gen__*.txt
Common/data_adapter.py -s 02_Alberta -t 04_Manitoba -g
check_rc 'Manitoba'

echo 'Ontario Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Ontario' -t 'America/Toronto' -k ${KEY_FILE} -s 05_Ontario/gen__pv.txt -g Common/gen_db_GHG.txt > 05_Ontario/gen_db.txt
check_rc 'Ontario'

echo 'Quebec Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Quebec' -t 'America/Montreal' -k ${KEY_FILE} -s 06_Quebec/gen__pv.txt -g Common/gen_db_GHG.txt > 06_Quebec/gen_db.txt
check_rc 'Quebec'

echo 'New Brunswick Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_New_Brunswick' -t 'America/Moncton' -k ${KEY_FILE} -s 07_New_Brunswick/gen__pv.txt -g Common/gen_db_GHG.txt > 07_New_Brunswick/gen_db.txt
check_rc 'New Brunswick'

echo 'Nova Scotia Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Nova_Scotia' -t 'America/Halifax' -k ${KEY_FILE} -s 08_Nova_Scotia/gen__pv.txt -g Common/gen_db_GHG.txt > 08_Nova_Scotia/gen_db.txt
check_rc 'Nova Scotia'

echo 'Prince Edward Island Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Prince_Edward_Island' -t 'America/Charlottetown' -k ${KEY_FILE} -s 09_Prince_Edward_Island/gen__pv.txt -g Common/gen_db_GHG.txt > 09_Prince_Edward_Island/gen_db.txt
check_rc 'Prince Edward Island'

echo 'Newfoundland and Labrador Starting...'
./Common/generator_data_gathering.py -u 'https://en.wikipedia.org/wiki/List_of_generating_stations_in_Newfoundland_and_Labrador' -t 'America/St_Johns' -k ${KEY_FILE} -s 10_Newfoundland_and_Labrador/gen__pv.txt -g Common/gen_db_GHG.txt > 10_Newfoundland_and_Labrador/gen_db.txt
check_rc 'Newfoundland and Labrador'



