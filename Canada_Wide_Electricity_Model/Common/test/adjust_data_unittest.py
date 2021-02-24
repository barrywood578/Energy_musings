#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
    Unit test for adjust_data

"""

from adjust_data import AdjustData
from common_defs import *
from math import ceil

import unittest
import mock
from unittest.mock import patch, mock_open, call

class TestAdjustData(unittest.TestCase):

    def setUp(self):
        pass

    def test_constants(self):
        pass

    def test_init(self):
        adj = AdjustData()
        self.assertEqual(adj.abs_adj, 0.0)
        self.assertEqual(adj.ratio, 1.0)

        adj = AdjustData(abs_adj="1000")
        self.assertEqual(adj.abs_adj, 1000.0)
        self.assertEqual(adj.ratio, 1.0)

        adj = AdjustData(abs_adj=9999)
        self.assertEqual(adj.abs_adj, 9999.0)
        self.assertEqual(adj.ratio, 1.0)

        adj = AdjustData(ratio="100")
        self.assertEqual(adj.abs_adj, 0.0)
        self.assertEqual(adj.ratio, 100.0)
        adj = AdjustData(ratio=99)
        self.assertEqual(adj.abs_adj, 0.0)
        self.assertEqual(adj.ratio, 99.0)

    def test_adjust(self):
        adj = AdjustData(abs_adj = "100", ratio = "100")
        upd = adj.adjust([100, 200, 300, 400])
        self.assertEqual(len(upd), 4)
        self.assertEqual(upd[0], (100 * 100) + 100)
        self.assertEqual(upd[1], (200 * 100) + 100)
        self.assertEqual(upd[2], (300 * 100) + 100)
        self.assertEqual(upd[3], (400 * 100) + 100)
