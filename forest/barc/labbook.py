"""
Barc Lab Book
---------------------

This module provides a :class:`BARCLab` to enable the Barc Lab Book

.. module:: labbook
    :synopis:
.. moduleauthors: Dan Walker @ NCAS and Helen Burns & Dan Elis @ CEMAC (Leeds)

.. class:: BARCLab
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


class BARCLab:
    '''
     A class for the BARC features.

     It is attached to to the main FOREST instance in the :py:func:`forest.main.main()` function of :py:mod:`forest.main`.
    '''
    barc = None
    source = {}

    def __init__(self, figures):
        self.figures = figures
        self.document = bokeh.plotting.curdoc()
        self.barcBook = bokeh.models.layouts.Column(name="barcBook")
        # initalise sources


    def LabBook(self):
        """Barc Lab Book
        """
        self.barcBook.children.append(bokeh.models.Div(text="lab div:"))
        print('testlab book')
        return self.barcBook
