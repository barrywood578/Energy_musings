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

-------------
THINGS TO RUN
-------------
All unit tests for all modules can be executed using the following:
python -m unittest discover . -v -p '*unittest.py'

Load data is assembled from a variety of files using a variety of methods.
To generate all load data based on current files, execute:
./run_load_data_assembly.sh

Generator data is scraped from Wikipedia pages for each province.
To generate all generator data based on current status, execute:
./run_gen_data_assembly.sh <KEY_FILE_NAME>

NOTE: <KEY_FILE_NAME> is a file containing the key for the PVWatts web
service on its first line.  This file is not necessary, but will result
in faster execution.
