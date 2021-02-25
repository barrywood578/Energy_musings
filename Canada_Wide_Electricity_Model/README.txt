PYTHON PACKAGES
- Revision 3.8 of python
- openpyxl
- pytz(?)
- PyMuPDF 

------
STATUS
------
Development of a cross-Canada electricity grid model.
Currently gathering hourly load data for all provinces,
and generator data for all provinces, then
starting in on the 'model' part.

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

-------------
THINGS TO RUN
-------------
All unit tests for all modules can be executed using the following:
python -m pytest

Load data is assembled from a variety of files using a variety of methods.
To generate all load data based on current files, execute:
./run_load_data_assembly.sh

Generator data is scraped from Wikipedia pages for each province.
To generate all generator data based on current status, execute:
./run_gen_data_assembly.sh <KEY_FILE_NAME>

NOTE: <KEY_FILE_NAME> is a file containing the key for the PVWatts web
service on its first line.  This file is not necessary, but will result
in faster execution. Key files are available for free.  Refer to 'api_key' 
at https://developer.nrel.gov/docs/solar/pvwatts/v6/ for more information.
