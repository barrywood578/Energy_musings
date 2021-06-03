#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Support for fetching all Newfoundland demand reports.
    All reports are in PDF format.

    Computes UTC time for each local date/time,
    and outputs a load file in standard format.
"""

from optparse import OptionParser
from collections import OrderedDict
import re
import operator
import sys
import os
import logging
from urllib.parse import urlparse
import fitz
from datetime import datetime, timedelta
import pytz

sys.path.append('../Common')
from common_defs import *
from demand_file import DemandFile

class calibration_pixel(object):
    def __init__(self):
        self.x = 0
        self.y = 0
        self.value = 0

class graph_label(object):
    def __init__(self):
        self.value = 0
        self.ul_x = 0
        self.ul_y = 0
        self.lr_x = 0
        self.lr_y = 0

B4_EDGE = True
AFT_EDGE = False
WHITE = [255, 255, 255]
BLACK = [0, 0, 0]
RED = [255, 0, 0]
GREEN = [0, 255, 0]
BLUE = [0, 0, 255]
BLUEISH = [0,49, 204]
BLUE_2  = [0,51, 204]
BLUE_3  = [1,51, 203]
LEFT = [-1, 0]
RIGHT = [1, 0]
UP = [0, -1]
DOWN = [0, 1]
INVALID = -1

class NL_PDF_Processing(object):

    def __init__(self, filepaths, directories, annotate):
        logging.info("Finding files")
        for folder in directories:
            try:
                for path, dirs, files in os.walk(folder):
                    for filename in files:
                        if os.path.splitext(filename)[1] == PDF_FILE_EXTENSION:
                            filepaths.append(os.path.join(path, filename))
            except ValueError as e:
                logging.critical("%s directory not processed" % folder)
                continue

        self.filepaths = sorted(filepaths)
        self.years = {}
        self.demand_file = DemandFile()
        self.annotate = annotate
        self.x_scale = 2
        self.y_scale = 2
        self.scaling = fitz.Matrix(self.x_scale, self.y_scale)

        # Variables used when processing a file
        self.filepath = ""
        self.doc = ""
        self.page = ""
        self.pix = ""
        self.file_report_time = ""
        self.file_utc = ""
        self.labels = []
        self.cal_x1 = calibration_pixel()
        self.cal_x2 = calibration_pixel()
        self.cal_y1 = calibration_pixel()
        self.cal_y2 = calibration_pixel()


    # Unwanted files come in a few flavours:
    # - Any file that cannot be openned by fitz (PDF support)
    # - Files that are not load reports:
    #   - Files with multiple pages
    #   - Files without an internal report date
    # - Earlier report revisions for the same date
    def remove_unwanted_files(self):
        logging.info("Removing unwanted files")
        list_to_skip = []

        for filename in self.filepaths:
            try:
                self.doc = fitz.open(filename)
                if (len(list(self.doc.pages())) > 1):
                    list_to_skip.append(filename)
                    self.doc.close()
                    continue
                self.page = self.doc.loadPage(0)
                file_dt = self.get_report_datetime(filename, self.page)
                self.doc.close()
            except:
                list_to_skip.append(filename)
                self.doc.close()
                continue

            found_dup = self.found_dup_file(filename, file_dt)
            if found_dup:
                old_file = self.years[file_dt.year][file_dt.month][file_dt.day][0]
                old_rev = self.get_revision(old_file)
                new_rev = self.get_revision(filename)
                if (old_rev < new_rev):
                    list_to_skip.append(old_file)
                    self.years[file_dt.year][file_dt.month][file_dt.day] = [filename]
                else:
                    list_to_skip.append(filename)

        for filename in list_to_skip:
            logging.warning("   SKIPPING '%s'" % filename)
            self.filepaths.remove(filename)

    # File revisions are found in file names.
    # The revision identifiers come in many forms:
    # RevX
    # revX
    # R.X
    # R. X
    # get_revision will find revision numbers for the above patterns,
    # and return the appropriate number.
    #
    # If no revision number exists in the file name, the revision
    # number is 0.
    def get_revision(self, old_file):
        pattern = re.compile(r"R\.")
        toks = pattern.split(old_file)
        if len(toks) > 1:
            return 1

        revision = "rev"
        filename = old_file.lower()
        idx = filename.find(revision)
        if idx > 0:
            toks = [tok.strip() for tok in filename[idx+len(revision):].split(".")]
            for tok in toks:
                try:
                    rev = int(tok)
                    return rev
                except ValueError:
                    continue
                return 1
        return 0

    def process_files(self):
        self.remove_unwanted_files()
        logging.info("Processing files")
        try:
            for filepath in self.filepaths:
                self.filepath = filepath
                logging.info("Processing '%s'" % filepath)
    
                self.doc = fitz.open(filepath)
                self.page = self.doc.loadPage(0)
                self.pix = self.page.getPixmap(matrix=self.scaling, alpha = False)
                self.file_report_time = self.get_report_datetime(filepath, self.page)
                self.file_utc = self.get_NL_UTC(self.file_report_time)
                self.labels = self.find_labels()
                self.find_x1(WHITE)
                self.find_x2(WHITE)
                self.find_y1()
                self.find_y2(WHITE)
                self.make_measurements(WHITE, BLUE)
                self.mark_calibration_points()
                self.write_png_file()
                self.doc.close()
        except ValueError as e:
            self.mark_calibration_points()
            self.write_png_file()
            self.doc.close()
            raise e

    # Get reporting date from page text.
    #
    # Date comes on a line with the form:
    # - NLH System Supply And Demand\n
    #   March 12, 2017
    #   NOTE: Sometimes the above line is part of the same
    #   text block, sometimes it is the next text block.
    # - Actual 24 Hour System Performance For March 12, 2017
    # - Actual 24 Hour System Performance For Sunday, March 12, 2017
    def get_report_datetime(self, filepath, page):
        old_label_str = "nlh system supply and demand"
        label_str = 'actual 24 hour system performance for '
        # test_str =  'actual 24 hour system performance for may 09, 2014'

        date_str = ""
        blocks = page.getText("blocks")
        for blk_idx, block in enumerate(blocks):
            test_str = block[4].encode("ASCII", 'replace')
            test_str = test_str.decode("ASCII")
            test_str = test_str.replace("?", " ")
            lower = test_str.strip().lower()
            idx = lower.find(old_label_str)
            if idx >= 0:
                date_str = lower[idx + len(old_label_str):].strip()
                if len(date_str) < 5:
                    date_str = blocks[blk_idx + 1][4].strip()
                break
            idx = lower.find(label_str)
            if idx < 0:
                continue
            lower = lower[idx + len(label_str):]
            toks = [tok.strip() for tok in lower.split(" ")]
            if len(toks) == 4:
                date_str = " ".join(toks[1:])
                break
            if len(toks) == 3:
                date_str = " ".join(toks)
                break
            logging.warning("Report datetime prefix match but tokens %d '%s'" % (len(toks), toks))
        if date_str == "":
            raise ValueError("%s: Could not find report date" % filepath)
        return datetime.strptime(date_str, '%B %d, %Y')

    # Maintain a dictionary based on report year, month, day
    # Returns True if there is another file already registered
    # for that year/month/day
    def found_dup_file(self, filepath, dt):
        found_dup = False
        year = dt.year
        month = dt.month
        day = dt.day

        if dt.year not in self.years:
            self.years[dt.year] = {}
        if dt.month not in self.years[dt.year]:
            self.years[dt.year][dt.month] = {}
        if dt.day in self.years[dt.year][dt.month]:
            found_dup = True
        else:
            self.years[dt.year][dt.month][dt.day] = [filepath]

        return found_dup

    # Labels are the text labels for the vertical (load) axis.
    # They are distinguished from other text blocks by
    # - can be converted to an integer
    # - the integer is greater than or equal to 200
    # The label location indicates the likely vertical and
    # horizontal location of graph axes.
    def find_labels(self):
        new_label = []
        labels = []
        for block in self.page.getText("blocks"):
            toks = [tok.strip() for tok in block[4].split(" ")]
            if len(toks) > 1:
                continue
            try:
                value = int(toks[0])
                if value < 200:
                    continue
                new_label = graph_label()
                new_label.value = value
                new_label.ul_x = block[0] * self.x_scale
                new_label.ul_y = block[1] * self.y_scale
                new_label.lr_x = block[2] * self.x_scale
                new_label.lr_y = block[3] * self.y_scale
                labels.append(new_label)
            except ValueError as e:
                continue
        labels.sort(key = lambda x: x.value, reverse=True)
        if len(labels) == 0:
            raise ValueError("%s : No labels found for vertical axis." %
                             self.filepath)
        return labels

    def search_right(self, start_pixel, background, edge):
        return self.search_pixels(start_pixel, background, RIGHT, edge)

    def search_left(self, start_pixel, background, edge):
        return self.search_pixels(start_pixel, background, LEFT, edge)

    def search_up(self, start_pixel, background, edge):
        return self.search_pixels(start_pixel, background, UP, edge)

    def search_down(self, start_pixel, background, edge):
        return self.search_pixels(start_pixel, background, DOWN, edge)

    # Searches for a background/not background transition based on the
    # colour of the start_pixel.
    # 
    # Direction is a 2 entry list of values to be added to start_pixel
    # for the search.
    #
    # Edge is either
    # - B4_EDGE  - return last pixel before the transition
    # - AFT_EDGE - return the first pixel after the transition
    def search_pixels(self, start_pixel, background, direction, edge):
        st_pix = self.pix.pixel(int(start_pixel[0]), int(start_pixel[1]))
        match_background = True
        for idx, pix_val in enumerate(st_pix):
            if (pix_val != background[idx]):
                match_background = False
                break
        found_it = INVALID
        for srch_cnt in range(1, max(self.pix.width, self.pix.height)):
            x = int(start_pixel[0]) + (srch_cnt * direction[0])
            y = int(start_pixel[1]) + (srch_cnt * direction[1])
            if (x < 0) or (x >= self.pix.width):
                break
            if (y < 0) or (y >= self.pix.height):
                break
            srch_pix = self.pix.pixel(x, y)
            # INFW remove before submission
            # print("x %d y %d pixel %s" % (x, y, str(srch_pix)))
            srch_pix_is_bkgrnd = True
            for idx, pix_val in enumerate(srch_pix):
                if (pix_val != background[idx]):
                    srch_pix_is_bkgrnd = False
                    break
            if (srch_pix_is_bkgrnd != match_background):
                found_it = srch_cnt
                if edge == B4_EDGE:
                    found_it = found_it - 1
                break

        rc = [INVALID, INVALID]
        if found_it != INVALID:
            rc = [start_pixel[0] + (found_it * direction[0]),
                  start_pixel[1] + (found_it * direction[1])]
        return rc

    #  Diagram of graph showing locations of X1/X2 and Y1/Y2
    #    Y2_________________________________________
    #    |                                         |
    #    |                                         |
    #    |                                         |
    #    |                                         |
    #    |                                         |
    #  X/Y1_______________________________________X2
    #
    def find_calibration_points(self, background):
        self.find_x1(background)
        self.find_x2(background)
        self.find_y1()
        self.find_y2(background)

    # Search for X1 based on the location of the bottom label
    # for the vertical axis.
    #
    # X1 is the pixel in the upper right corner of the intersection of
    # the horizontal and vertical axes.
    #
    # X1 is associated with the horizontal axis.
    def find_x1(self, background):
        bot_label = self.labels[-1]
        
        search_start = [bot_label.lr_x, bot_label.ul_y]
        vert_axis_start = self.search_right(search_start, background, AFT_EDGE)
        if (vert_axis_start[0] == INVALID):
            raise ValueError("%s: Could not find x1 vertical axis start." % self.filepath)
        vert_axis_end = self.search_right(vert_axis_start, background, B4_EDGE)
        if (vert_axis_end[0] == INVALID):
            raise ValueError("%s: Could not find x1 vertical axis end." % self.filepath)

        b4_vert_axis_start = [vert_axis_start[0] - 1, vert_axis_start[1]]
        horiz_axis_start = self.search_down(b4_vert_axis_start, background, AFT_EDGE)
        if (horiz_axis_start[0] == INVALID):
            raise ValueError("%s: Could not find x1 horizontal axis start." % self.filepath)

        self.cal_x1.x = vert_axis_end[0]
        self.cal_x1.y = horiz_axis_start[1]
        self.cal_x1.value = self.file_report_time
        
    # X2 is the pixel in the upper left corner of the intersection of
    # the bottom horizontal and right vertical axes.
    #
    # X2 is associated with the horizontal axis.
    def find_x2(self, background):
        start_pix = [self.cal_x1.x + 1, self.cal_x1.y - 1]

        right_box_start = self.search_right(start_pix, background, AFT_EDGE)
        if (right_box_start[0] == INVALID):
            raise ValueError("%s: Could not find x2 right box start." % self.filepath)
        self.cal_x2.x = right_box_start[0]
        self.cal_x2.y = self.cal_x1.y
        self.cal_x2.value = self.file_report_time + timedelta(days = 1)

    # Y1 is the same location as X1.
    #
    # Y1 is associated with the vertical axis.
    def find_y1(self):
        self.cal_y1.x = self.cal_x1.x
        self.cal_y1.y = self.cal_x1.y
        self.cal_y1.value = float(self.labels[-1].value)

    # Search for Y2 based on the location of the top label
    # for the vertical axis.
    #
    # Y2 is the pixel in the lower right corner of the intersection of
    # the top horizontal and left vertical axes.
    #
    # Y2 is associated with the vertical axis.
    def find_y2(self, background):
        top_label = self.labels[0]
        start_pix = [top_label.lr_x, top_label.lr_y]

        vert_axis_start = self.search_right(start_pix, background, AFT_EDGE)
        if (vert_axis_start[0] == INVALID):
            raise ValueError("%s: Could not find y2 top vertical axis start." % self.filepath)
        vert_axis_end = self.search_right(vert_axis_start, background, B4_EDGE)
        if (vert_axis_end[0] == INVALID):
            raise ValueError("%s: Could not find y2 top vertical axis end." % self.filepath)

        start_pix = [vert_axis_end[0] + 1, vert_axis_end[1]]
        horiz_axis_start = self.search_up(start_pix, background, AFT_EDGE)
        if (horiz_axis_start[0] == INVALID):
            raise ValueError("%s: Could not find y2 top horizontal axis start." % self.filepath)
        self.cal_y2.x = vert_axis_end[0]
        self.cal_y2.y = horiz_axis_start[1]
        self.cal_y2.value = float(top_label.value)

    def colour_match(self, start_pixel, end_pixel, direction, line_colours):
        if INVALID in start_pixel or INVALID in end_pixel:
            return False

        checks = []
        pix_diff = int(max([abs(a - b) for a, b in zip(start_pixel, end_pixel)]))
        found = False
        for offset in range(0, pix_diff):
            pixel = [int(a + offset*b) for a,b in zip(start_pixel, direction)]
            pixel_colour = self.pix.pixel(pixel[0], pixel[1])

            for colour in line_colours:
                checks = [ a in range(b-3,b+4) for a, b in zip(pixel_colour, colour)]
                if False not in checks:
                    found = True
                    break
            if found:
                break
        return found and (len(checks) != 0)

    def get_NL_UTC(self, time_in):
        local = pytz.timezone("America/St_Johns")
        naive = datetime(time_in.year, time_in.month, time_in.day, time_in.hour)
        local_dt = local.localize(naive, False)
        return local_dt.astimezone(pytz.utc)

    # Make measurements for each hour in the graph.
    #
    # Search up from the horizontal axis until a blue(ish) line
    # is found.  The measurement is the center of the blue(ish) line.
    #
    # It may not be possible to get a measurement at the computed 'x'
    # coordinate for hour 0 or when daylight savings time starts,
    # so keep bumping the X coordinate to the right
    # until a measurement can be made.
    def make_measurements(self, background, line_colour):
        local_tz = pytz.timezone("America/St_Johns")
        LOAD_LINE_COLOURS = [BLUE, BLUEISH, BLUE_2, BLUE_3]

        horiz_pixels = self.cal_x2.x - self.cal_x1.x 
        vert_pixels = self.cal_y1.y - self.cal_y2.y 

        pixels_per_hour = float(horiz_pixels) / 24.0
        value_per_pixel = float(self.cal_y2.value - self.cal_y1.value) / float(self.cal_y1.y - self.cal_y2.y)  

        time_utc = self.file_utc
        time_local = self.file_report_time

        for hour in range(0,24):
            if time_local.day != self.file_report_time.day:
                break
            x_offset = 1
            found = False
            while (x_offset < self.pix.width) and not found:
                start_pix = [self.cal_x1.x + int(float(time_local.hour) * pixels_per_hour) + x_offset,
                            self.cal_x1.y - 1]
                start_pix = self.search_up(start_pix, background, AFT_EDGE)
                end_pix = self.search_up(start_pix, background, B4_EDGE)
                while not self.colour_match(start_pix, end_pix, UP, LOAD_LINE_COLOURS):
                    start_pix = self.search_up(end_pix, background, AFT_EDGE)
                    end_pix = self.search_up(start_pix, background, B4_EDGE)
                    if (start_pix[0] == INVALID) or (end_pix[0] == INVALID):
                        x_offset += 1
                        break
                found = self.colour_match(start_pix, end_pix, UP, LOAD_LINE_COLOURS)
            if not found:
                raise ValueError("%s: Could not make measurement for hour %d." % (self.filepath, hour))
            sample_y = float(start_pix[1] + end_pix[1])/2.0
            the_load = ((float(self.cal_y1.y) - sample_y) * value_per_pixel) + self.cal_y1.value
            self.demand_file.add_mw_hour(self.filepath, hour, [self.filepath, hour,
                                              time_utc.year, time_utc.month, time_utc.day, time_utc.hour,
                                              time_local.year, time_local.month, time_local.day, time_local.hour, the_load])
            # Annotate the measurement range and horizontal axis
            self.add_horiz_line(start_pix, RED)
            self.add_vert_line(start_pix, RED)
            self.add_horiz_line(end_pix, RED)
            self.add_vert_line(end_pix, RED)
            self.add_vert_line([end_pix[0], self.cal_x1.y], RED)

            time_utc = time_utc + timedelta(hours=1)
            time_local = time_utc.replace(tzinfo=pytz.utc).astimezone(local_tz)
            time_local = local_tz.normalize(time_local)

    # The following routines leverage the ability to mark locations
    # in the rendered page, and then write that rendered page as a
    # .png file.  This can be useful for debugging, and for confirming
    # the location of measurements.
    #
    # Note that all marking routines, as well as the ability to writh
    # the .png file, are controlled by "self.annotate".  If this parameter
    # is false, no .png file is written and no pixels will be changed.
    #
    # NOTE: Only mark points after measurements have been
    #       taken, otherwise the markings can influence measurements...
    def mark_calibration_points(self):
        self.add_cross([self.labels[0].ul_x, self.labels[0].ul_y], GREEN)
        self.add_cross([self.labels[0].lr_x, self.labels[0].lr_y], GREEN)

        self.add_ex([self.labels[-1].ul_x, self.labels[-1].ul_y], GREEN)
        self.add_ex([self.labels[-1].lr_x, self.labels[-1].lr_y], GREEN)

        self.add_cross([self.cal_x1.x, self.cal_x1.y], RED)
        self.add_cross([self.cal_x2.x, self.cal_x2.y], RED)
        self.add_ex([self.cal_y1.x, self.cal_y1.y], BLACK)
        self.add_ex([self.cal_y2.x, self.cal_y2.y], BLACK)

    # Add a '+' like marking in the selected colour
    def add_cross(self, center_pixel, colour):
        if not self.annotate:
            return
        arm_len_pixels = 10
        arm_width_pixels = 1

        center_x = int(center_pixel[0])
        center_y = int(center_pixel[1])
        # Horizontal arm
        for x in range(center_x - arm_len_pixels, center_x + arm_len_pixels + 1):
            for y in range(center_y - arm_width_pixels, center_y + arm_width_pixels + 1):
                self.pix.setPixel(x, y, colour)
        # Vertical arm
        for x in range(center_x - arm_width_pixels, center_x + arm_width_pixels+ 1):
            for y in range(center_y - arm_len_pixels, center_y + arm_len_pixels+ 1):
                self.pix.setPixel(x, y, colour)

    # Add an 'X' like marking in the selected colour
    def add_ex(self, center_pixel, colour):
        if not self.annotate:
            return
        arm_len_pixels = 10
        arm_width_pixels = 2

        center_x = int(center_pixel[0])
        center_y = int(center_pixel[1])

        # Draw all four arms at the same time
        for arm_len in range(0, arm_len_pixels):
            for arm_width in range(0, (arm_width_pixels * 2) + 1):
                self.pix.setPixel(center_x - arm_len - arm_width_pixels + arm_width,
                                  center_y - arm_len,
                                  colour)
                self.pix.setPixel(center_x + arm_len - arm_width_pixels + arm_width,
                                  center_y - arm_len,
                                  colour)
                self.pix.setPixel(center_x - arm_len - arm_width_pixels + arm_width,
                                  center_y + arm_len,
                                  colour)
                self.pix.setPixel(center_x + arm_len - arm_width_pixels + arm_width,
                                  center_y + arm_len,
                                  colour)

    def add_horiz_line(self, center_pixel, colour):
        if not self.annotate:
            return

        line_len_pixels = 10
        center_x = int(center_pixel[0])
        center_y = int(center_pixel[1])

        for arm_pixel in range(center_x - line_len_pixels, center_x + line_len_pixels + 1):
            self.pix.setPixel(arm_pixel, center_y, colour)

    def add_vert_line(self, center_pixel, colour):
        if not self.annotate:
            return
        line_len_pixels = 10
        center_x = int(center_pixel[0])
        center_y = int(center_pixel[1])

        for arm_pixel in range(center_y - line_len_pixels, center_y + line_len_pixels + 1):
            self.pix.setPixel(center_x, arm_pixel, colour)

    def write_png_file(self):
        if not self.annotate:
            return
        png = self.filepath + ".png"
        self.pix.writePNG(png)

    def print_demand_file(self):
        self.demand_file.write_hourly_mw_file()

def create_parser():
    parser = OptionParser(description="Fetches all Newfoundland and Labrador Daily Load Report Files.")
    parser.add_option('-f', '--filepath',
            dest = 'filepaths',
            action = 'append', type = 'string', default = [],
            help = 'Filepath of a PDF documents.',
            metavar = 'FILE')
    parser.add_option('-d', '--directory',
            dest = 'directories',
            action = 'append', type = 'string', default = [],
            help = 'Directories of a PDF documents.',
            metavar = 'DIR')
    parser.add_option('-a', '--annotate',
            dest = 'annotate',
            action = 'store_true', default = False,
            help = 'Write annotated .png file for every PDF.',
            metavar = 'FLAG')
    parser.add_option('-l', '--load',
            dest = 'load',
            action = 'store_true', default = False,
            help = 'Print demand load file.',
            metavar = 'FLAG')
    return parser

def main(argv = None):
    logging.basicConfig(level=logging.INFO)
    parser = create_parser()
    if argv is None:
        argv = sys.argv[1:]

    (options, argv) = parser.parse_args(argv)
    if len(argv) != 0:
        print('Must enter at least one file path!')
        print
        parser.print_help()
        return -1

    load = NL_PDF_Processing(options.filepaths, options.directories, options.annotate)
    load.process_files()
    if options.load:
        load.print_demand_file()

if __name__ == '__main__':
    sys.exit(main())
