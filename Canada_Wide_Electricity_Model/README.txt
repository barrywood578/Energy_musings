PYTHON PACKAGES
- Anaconda environment manager
- Revision 3.8 of python
- openpyxl
- pytz
- PyMuPDF
- lxml
- urllib3

------
STATUS
------
- Model results have been correlated with 2019 GHG emissions data for
  electricity generation from the Government of Canada (~60 MT CO2)
- Currently investigating electrification of
  - Vehicles
  - Industrial/manufacturing processes
  - Home heating/cooling
  - CCUS

-------------------
ORIGINAL DATA FILES
-------------------
Generally, the original data files for load and generation data are found
within each provinces folder, along with descriptions of where the files came
from.

The major exception is Newfoundland and Labrador, which requires a large
amount of data to be downloaded to a separate folder, as described in the
10_Newfoundland_and_Labrador/Notes_and_URLs.txt file.  The scripts assume
that this separate folder is Canada_Wide_Electricity_Model/www.pub.nl.ca.

-----------------
INSTALLATION TEST
-----------------
All unit tests for all modules can be executed using the following:
python -m pytest

-------------
MODELS TO RUN
-------------
A one year grid simulation is run for each province, and then a
simulation is run for all of Canada, by the following script:
./run_grid.sh

If data has been generated for the Transportation directory,
the script will also run an all-Canada simulation plus Transporation
load and generation.  See the Transportation directory README
for details on creating load and generation files.

-------------
DATA ASSEMBLY
-------------
Load data is assembled from a variety of files using a variety of methods.
To generate all load data based on current files, execute:
./run_load_data_assembly.sh

Generator data is scraped from Wikipedia pages for each province.
To generate all generator data based on current status, execute:
./run_gen_data_assembly.sh <KEY_FILE_NAME>

NOTE: run_load_data_assembly.sh MUST be executed before run_gen_data_assembly.sh
      Saskatchewan and Manitoba generation data are dependent on Alberta
      generation files created by run_load_data_assembly.sh.

NOTE: <KEY_FILE_NAME> is a file containing the key for the PVWatts web
service on its first line.  This file is not necessary, but will result
in faster execution and allow unlimited execution in a day.
Key files are available for free.  Refer to 'api_key'
at https://developer.nrel.gov/docs/solar/pvwatts/v6/ for more information.
