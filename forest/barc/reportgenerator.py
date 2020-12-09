"""
Barc Report Generator
---------------------

This module provides a :class:`BARCReport` to enable the Barc Report Generator

.. module:: labbook
    :synopis:
.. moduleauthors: Dan Walker @ NCAS and Helen Burns & Dan Elis @ CEMAC (Leeds)

.. class:: BARCReport
    :members:

.. description: This module was developed by NCAS and CEMAC as part of the
    WCSSP BARC project.
   Project. This Script does absolutely nothing.
   :license: BSD-3

"""
import bokeh.models

from os.path import basename

from bokeh.models import ColumnDataSource, Paragraph, Select
from bokeh.models.glyphs import Text
from bokeh.core.properties import value
from bokeh.models.tools import PolyDrawTool, PolyEditTool, BoxEditTool
from bokeh.models.tools import PointDrawTool, ToolbarBox, FreehandDrawTool
from bokeh.events import ButtonClick
from forest import wind, data, tools, redux
import forest.middlewares as mws
#from . import front
from .front_tool import FrontDrawTool


class BARCReport:
    '''
     A class for the BARC features.

     It is attached to to the main FOREST instance in the :py:func:`forest.main.main()` function of :py:mod:`forest.main`.
    '''
    barcReport = None
    source = {}

    def __init__(self, figures):
        self.figures = figures
        self.document = bokeh.plotting.curdoc()
        self.barcReport = bokeh.models.layouts.Column(name="barcReport")
        # initalise sources
        self.LoadButton = bokeh.models.widgets.Button(
            name="barc_load", width=50, label="Load")
        self.searchButton = bokeh.models.widgets.Button(
            name="barc_search", width=50, label="Search")



    def Report(self):
        """Barc Report
        """
        UserInput=bokeh.models.Div(text="Test")
        self.barcReport.children.append(UserInput)
        print('test Report')
        return self.barcReport
