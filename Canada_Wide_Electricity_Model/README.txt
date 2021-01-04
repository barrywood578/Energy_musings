PYTHON PACKAGES
- Revision 3.8 of python
- openpyxl
- pytz(?)
- PyMuPDF 

STATUS
Development of a cross-Canada electricity grid model.
Currently gathering hourly load data for all provinces,
starting in on the 'model' part.

THINGS TO RUN
All unit tests for all modules can be executed using the following:
python -m unittest discover . -v -p '*unittest.py'

Load data is assembled from a variety of files using a variety of methods.
To general all load data based on current files, execute:
./run_load_data_assembly.sh
