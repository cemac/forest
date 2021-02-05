"""
Barc Tool Bar
---------------------

This module provides a :class:`BARC` to enable the Barc Tool Bar

.. module:: toolbar
    :synopsis: The barc tool bar and methods required to enable the barc plugin
    fuctionality
.. moduleauthors: Dan Walker @ NCAS and Helen Burns & Dan Elis @ CEMAC (Leeds)

.. class:: BARC
    :members:
        ToolBar: Creates tool bar of tools listed below
        polyLine: FreehandDrawTool
        polyDraw: PolygonDrawTool
        polyEdit: edit verticies of polygon
        boxEdit: BoxDraw and edit tool
        textStamp: method to enable text stamping
        windBarb: stamp a windbarb
        weatherFront: Bézier curves, optionally with text glyphs repeated along them, e.g. for warm fronts.
        display_glyphs: displays the selected Category of textstamps
        set_glyphs: set textstamps to display
        call: Callback function to dynamically alter tool bar
.. description: This module was developed by NCAS and CEMAC as part of the
    WCSSP BARC project.
   Project. This Script does absolutely nothing.
   :license: BSD-3

"""
import bokeh.models
import json
import sqlite3
import time
import pandas as pd

from os.path import basename

from bokeh.models import ColumnDataSource, Paragraph, Select, Dropdown
from bokeh.models.glyphs import Text
from bokeh.core.properties import value
from bokeh.models.tools import PolyDrawTool, PolyEditTool, BoxEditTool
from bokeh.models.tools import PointDrawTool, ToolbarBox, FreehandDrawTool
from bokeh.events import ButtonClick
from forest import wind, data, tools, redux
import forest.middlewares as mws
#from . import front
from .front_tool import FrontDrawTool


class BARC:
    '''
     A class for the BARC features.

     It is attached to to the main FOREST instance in the :py:func:`forest.main.main()` function of :py:mod:`forest.main`.
    '''

    def __init__(self, figures):
        self.figures = figures
        self.document = bokeh.plotting.curdoc()
        #db for saving
        self.conn = sqlite3.connect("forest/barc/barc-save.sdb")
        self.barcTools = bokeh.models.layouts.Column(name="barcTools")
        # initalise sources
        self.source = {}
        self.source['polyline'] = ColumnDataSource(data.EMPTY)
        self.source['poly_draw'] = ColumnDataSource(data.EMPTY)
        self.source['box_edit'] = ColumnDataSource(data.EMPTY)
        self.source['barb'] = ColumnDataSource(data.EMPTY)
        self.source['fronts'] = ColumnDataSource(data.EMPTY)
        self.source['annotations'] = ColumnDataSource(data=dict(notes=[]))
        # set intial width and colours
        self.starting_colour = "black"  # in CSS-type spec
        self.starting_width = 2
        self.widthPicker = bokeh.models.widgets.Slider(
            title='Select width', name="barc_width", width=200,
            end=10.0,
            start=1.0, value=self.starting_width)
        # colour bar picker
        self.colourPicker = bokeh.models.widgets.ColorPicker(
            title='Stamp colour:', width=50,
            name="barc_colours",
            color=self.starting_colour)
        #glyph annotation box
        self.annotate = bokeh.models.layouts.Column()
        self.annotate.children.extend([
            bokeh.models.widgets.TextInput(title="Title",name='title'),
            bokeh.models.widgets.TextAreaInput(title="Forecaster's Comments", name="forecastnotes", height=150, width=350),
            bokeh.models.widgets.TextAreaInput(title="Brief Description", name="briefdesc", height=150, width=350),
            bokeh.models.widgets.TextAreaInput(title="Further Notes", name="further", height=150, width=350),
        ])
        # Dropdown Menu of stamp categories
        self.stamp_categories=["Group0 - General meteorological symbols", "Group1 - General meteorological symbols", "Group2 - Precipitation fog ice fog or thunderstorm", "Group3 - Duststorm sandstorm drifting or blowing snow",
                               "Group4 - Fog or ice fog at the time of observation", "Group5 - Drizzle", "Group6 - Rain", "Group7 - Solid precipitation not in showers",
                               "Group8 - Showery precipitation or precipitation with recent thunderstorm", "Group9 - Thunderstorms", "Group10 - Hurricanes and Typhoons"]
        self.dropDown = Select(title="Meteorological symbols:", width=300,

                               value="Group0 - General meteorological symbols",
                               options=self.stamp_categories)
        self.dropDown.on_change("value", self.call)
        # Save area
        self.saveArea = bokeh.models.widgets.inputs.TextAreaInput(
            cols=20, max_length=20000,height=200, width=350)
        self.saveArea.js_on_change('value',
                                   bokeh.models.CustomJS(
                                   args=dict(sources=self.source,
                                   saveArea=self.saveArea,
                                   figure=self.figures[0]), code="""
        Object.entries(JSON.parse(saveArea.value)).forEach(([k,v]) => {
            sources[k].change.emit();
            sources[k].data = v;
            if(k.substring(0,10) == 'text_stamp')
            {
                for(var g = 0; g < sources[k].data['fontsize'].length; g++)
                {
                    sources[k].data['fontsize'][g] = (((sources[k].data['datasize'][g])/ (figure.y_range.end - figure.y_range.start))*figure.inner_height) + 'px';
                }
            }
        })
    """)
                                   )

        self.saveButton = bokeh.models.widgets.Button(
            name="barc_save", width=50, label="\U0001f4be")
        self.saveButton.js_on_click(
            bokeh.models.CustomJS(args=dict(sources=self.source,
                                            saveArea=self.saveArea), code="""
                var outdict = {}
                Object.entries(sources).forEach(([k,v]) =>
                {
                        outdict[k] = v.data;
                })
                saveArea.value = JSON.stringify(outdict);
            """)
        )
        self.saveButton.on_click(self.saveDataSources)

        #populate list of saved markups
        c = self.conn.cursor()
        c.execute("SELECT label, CAST(id AS TEXT) FROM saved_data ORDER BY dateTime DESC")
        menu = c.fetchall()
        self.loadButton = bokeh.models.widgets.Dropdown(
            name="barc_load", width=150, label="Load", menu=menu )
        self.loadButton.on_click(self.loadDataSources)

        # from BARC.woff take the index dictionary
        # James's icons correspond pw-000 - pw-099 glyph index 2 to 101
        # James's icons correspond pw-100 - pw-109 glyph index 114 to 123
        glyphIndexMap = {"983040": 2, "983041": 3, "983042": 4, "983043": 5,
                         "983044": 6, "983045": 7, "983046": 8, "983047": 9,
                         "983048": 10, "983049": 11, "983079": 12, "983080": 13,
                         "983081": 14, "983082": 15, "983083": 16, "983084": 17,
                         "983085": 18, "983086": 19, "983087": 20, "983088": 21,
                         "983118": 22, "983119": 23, "983120": 24, "983121": 25,
                         "983122": 26, "983123": 27, "983124": 28, "983125": 29,
                         "983126": 30, "983127": 31, "983157": 32, "983158": 33,
                         "983159": 34, "983160": 35, "983161": 36, "983162": 37,
                         "983163": 38, "983164": 39, "983165": 40, "983166": 41,
                         "983196": 42, "983197": 43, "983198": 44, "983199": 45,
                         "983200": 46, "983201": 47, "983202": 48, "983203": 49,
                         "983204": 50, "983205": 51, "983235": 52, "983236": 53,
                         "983237": 54, "983238": 55, "983239": 56, "983240": 57,
                         "983241": 58, "983242": 59, "983243": 60, "983244": 61,
                         "983274": 62, "983275": 63, "983276": 64, "983277": 65,
                         "983278": 66, "983279": 67, "983280": 68, "983281": 69,
                         "983282": 70, "983283": 71, "983313": 72, "983314": 73,
                         "983315": 74, "983316": 75, "983317": 76, "983318": 77,
                         "983319": 78, "983320": 79, "983321": 80, "983322": 81,
                         "983352": 82, "983353": 83, "983354": 84, "983355": 85,
                         "983356": 86, "983357": 87, "983358": 88, "983359": 89,
                         "983360": 90, "983361": 91, "983391": 92, "983392": 93,
                         "983393": 94, "983394": 95, "983395": 96, "983396": 97,
                         "983397": 98, "983398": 99, "983399": 100, "983400": 101,
                         "983508":114,"983509":115,"983510":116,"983511":117,
                         "983512":118,"983513":119,"983548":120,"983547":121,
                         "983549":122,"983550":123}
        glyphcodes = list(map(int, list(glyphIndexMap.keys())))
        self.allglyphs = glyphcodes
        self.set_glyphs()
        icons = ["pw-%03d" % i for i in range(110)]
        # Make a dictionary from list of codes and icon names
        self.icons = dict(zip(self.allglyphs, icons))
        # Make one ColumnDataSource per glyph
        for glyph in self.allglyphs:
            self.source['text_stamp' +
                        chr(glyph)] = ColumnDataSource(data.EMPTY)
            self.source['text_stamp' + chr(glyph)].add([], "datasize")
            self.source['text_stamp' + chr(glyph)].add([], "fontsize")
            self.source['text_stamp' + chr(glyph)].add([], "colour")

        self.tool_bar =self.ToolBar()

    def set_glyphs(self):
        """Set Glyphs based on drop down selection
        """
        new = self.dropDown.value
        glyphcodes =self.allglyphs
        # Range of glyphs
        # Fonts and icon mapping to go here
        if str(new) == "Group0 - General meteorological symbols":
            self.glyphs = glyphcodes[0:10]
        elif str(new) == "Group1 - General meteorological symbols":
            self.glyphs = glyphcodes[10:19]
        elif str(new) == "Group2 - Precipitation fog ice fog or thunderstorm":
            self.glyphs = glyphcodes[20:30]
        elif str(new) == "Group3 - Duststorm sandstorm drifting or blowing snow":
            self.glyphs = glyphcodes[30:40]
        elif str(new) == "Group4 - Fog or ice fog at the time of observation":
            self.glyphs = glyphcodes[40:50]
        elif str(new) == "Group5 - Drizzle":
            self.glyphs = glyphcodes[50:60]
        elif str(new) == "Group6 - Rain":
            self.glyphs = glyphcodes[60:70]
        elif str(new) == "Group7 - Solid precipitation not in showers":
            self.glyphs = glyphcodes[70:80]
        elif str(new) == "Group8 - Showery precipitation or precipitation with recent thunderstorm":
            self.glyphs = glyphcodes[80:90]
        elif str(new) == "Group9 - Thunderstorms":
            self.glyphs = glyphcodes[90:100]
        elif str(new) == "Group10 - Hurricanes and Typhoons":
            self.glyphs =  glyphcodes[100:110]


    def call(self, attr, old, new):
        """Call back from dropdown click
         Removes and inserts new glyphrow
        """
        self.barcTools.children.remove(self.glyphrow)
        self.set_glyphs()
        self.glyphrow = bokeh.layouts.grid(self.display_glyphs(), ncols=5)
        self.barcTools.children.insert(2, self.glyphrow)

    def polyLine(self):
        '''
            Creates a freehand tool for drawing on the Forest maps.

            :returns: a :py:class:`FreehandDrawTool <bokeh.models.tools.FreehandDrawTool>` instance
        '''
        # colour picker means no longer have separate colour line options
        render_lines = []
        self.source['polyline'].add([], "colour")
        self.source['polyline'].add([], "width")
        for figure in self.figures:
            render_lines.append(figure.multi_line(
                xs="xs",
                ys="ys",
                line_width="width",
                source=self.source['polyline'],
                alpha=0.3,
                color="colour", level="overlay")
            )

        tool2 = FreehandDrawTool(
            renderers=[render_lines[0]],
            tags=['barcfreehand'],
            name="barcfreehand"
        )
        self.source['polyline'].js_on_change('data',
            bokeh.models.CustomJS(args=dict(datasource=self.source['polyline'],
            colourPicker=self.colourPicker, widthPicker=self.widthPicker,
            saveArea=self.saveArea, sources=self.source), code="""
                for(var g = 0; g < datasource.data['colour'].length; g++)
                {
                    if(!datasource.data['colour'][g])
                    {
                        datasource.data['colour'][g] = colourPicker.color;
                    }
                    if(!datasource.data['width'][g])
                    {
                        datasource.data['width'][g] = widthPicker.value;
                    }
                }
                """)
                                             )

        return tool2

    def polyDraw(self):
        '''
            Creates a poly draw tool for drawing on the Forest maps.
            :returns: a :py:class:`PolyDrawTool <bokeh.models.tools.PolyDrawTool>` instance
        '''
        # colour picker means no longer have separate colour line options
        render_lines = []
        self.source['poly_draw'].add([], "colour")
        self.source['poly_draw'].add([], "width")
        for figure in self.figures:
            render_lines.append(figure.patches(
                xs='xs',
                ys='ys',
                color="colour",
                source=self.source['poly_draw'],
                alpha=0.3,
                level="overlay")
            )

        tool2 = PolyDrawTool(
            renderers=[render_lines[0]],
            tags=['barcpoly_draw'],
            name="barcpoly_draw"
        )
        self.source['poly_draw'].js_on_change('data',
                                             bokeh.models.CustomJS(args=dict(datasource=self.source['poly_draw'], colourPicker=self.colourPicker, widthPicker=self.widthPicker, saveArea=self.saveArea, sources=self.source), code="""
                for(var g = 0; g < datasource.data['colour'].length; g++)
                {
                    if(!datasource.data['colour'][g])
                    {
                        datasource.data['colour'][g] = colourPicker.color;
                    }
                    if(!datasource.data['width'][g])
                    {
                        datasource.data['width'][g] = widthPicker.value;
                    }
                }
                """)
        )
        return tool2

    def polyEdit(self):
        '''
            Creates a poly draw tool for drawing on the Forest maps.

            :returns: a PolyDrawTool instance
        '''
        # Not functional yet
        render_lines = []
        for figure in self.figures:
            render_lines.append(figure.patches(
                xs='xs',
                ys='ys',
                source=self.source['poly_draw'],
                alpha=0.3,
                color="colour",
                level="overlay")
            )

        tool2 = PolyEditTool(
            renderers=render_lines[0],
            tags=['barcpoly_edit'],
            name="barcpoly_edit"
        )

        return tool2

    def boxEdit(self):
        '''
            Creates a box edit tool for drawing on the Forest maps.

            :returns: a :py:class:`BoxEditTool <bokeh.models.tools.BoxEditTool>` instance
        '''
        render_lines = []
        self.source['box_edit'].add([], "colour")
        self.source['box_edit'].add([], "width")
        for figure in self.figures:
            render_lines.append(figure.patches(
                xs='xs',
                ys='ys',
                source=self.source['box_edit'],
                alpha=0.3,
                color="colour",
                level="overlay")
            )

        tool2 = BoxEditTool(
            renderers=render_lines,
            tags=['barcbox_edit'],
            name="barcbox_edit"
        )
        self.source['box_edit'].js_on_change('data',
                                             bokeh.models.CustomJS(args=dict(datasource=self.source['box_edit'], colourPicker=self.colourPicker, saveArea=self.saveArea, sources=self.source), code="""
                for(var g = 0; g < datasource.data['colour'].length; g++)
                {
                    if(!datasource.data['colour'][g])
                    {
                        datasource.data['colour'][g] = colourPicker.color;
                    }
                    if(!datasource.data['width'][g])
                    {
                        datasource.data['width'][g] = widthPicker.value;
                    }
                }
                """)
                                             )

        return tool2

    def textStamp(self, glyph=chr(0x0f0000)):
        '''Creates a tool that allows arbitrary Unicode text to be "stamped" on the map. Echos to all figures.

        :param glyph: Arbitrary unicode string, usually (but not required to be) a single character.

        :returns: :py:class:`PointDrawTool <bokeh.models.tools.PointDrawTool>` with textStamp functionality.
        '''

        starting_font_size = 15  # in pixels
        render_lines = []
        for figure in self.figures:
            render_lines.append(figure.text_stamp(
                x="xs",
                y="ys",
                source=self.source['text_stamp' + glyph],
                text=value(glyph),
                text_font='BARC',
                text_color="colour",
                text_font_size="fontsize",
                text_align = 'center',
                text_baseline = 'middle'
            )
            )

        self.source['text_stamp' + glyph].js_on_change('data',
            bokeh.models.CustomJS(args=dict(datasource=self.source['text_stamp' + glyph],
            starting_font_size=starting_font_size, figure=self.figures[0],
            colourPicker=self.colourPicker, widthPicker=self.widthPicker,
            saveArea=self.saveArea), code="""
                for(var g = 0; g < datasource.data['xs'].length; g++)
                {
                    if(!datasource.data['colour'][g])
                    {
                        datasource.data['colour'][g] = colourPicker.color;
                    }

                    if(!datasource.data['fontsize'][g])
                    {
                        datasource.data['fontsize'][g] = (widthPicker.value * starting_font_size) +'px';
                    }

                    //calculate initial datasize
                    if(!datasource.data['datasize'][g])
                    {
                        var starting_font_proportion = (widthPicker.value * starting_font_size)/(figure.inner_height);
                        datasource.data['datasize'][g] = (starting_font_proportion * (figure.y_range.end - figure.y_range.start));
                    }
                }
                """)
        )
        self.figures[0].y_range.js_on_change('start',
            bokeh.models.CustomJS(args=dict(render_text_stamp=render_lines[0],
            figure=self.figures[0]), code="""
            for(var g = 0; g < render_text_stamp.data_source.data['fontsize'].length; g++)
            {
                 render_text_stamp.data_source.data['fontsize'][g] = (((render_text_stamp.data_source.data['datasize'][g])/ (figure.y_range.end - figure.y_range.start))*figure.inner_height) + 'px';
            }
            render_text_stamp.glyph.change.emit();
            """)
        )
        tool3 = PointDrawTool(
            renderers=[render_lines[0]],
            tags=['barc' + glyph],
        )
        return tool3

    def windBarb(self):
        '''
            Draws a windbarb based on u and v values in ms¯¹. Currently fixed to 50ms¯¹.

        '''
        render_lines = []
        for figure in self.figures:
            render_lines.append(figure.barb(
                x="xs",
                y="ys",
                u=-50,
                v=-50,
                source=self.source['barb']
            ))

        tool4 = PointDrawTool(
            renderers=render_lines,
            tags=['barcwindbarb'],
            custom_icon=wind.__file__.replace('__init__.py', 'barb.png')
        )

        return tool4

    def bezierSource(self):
        return ColumnDataSource(data=dict(x0=[], y0=[], x1=[], y1=[], cx0=[], cy0=[], cx1=[], cy1=[]))

    def emptySource(self):
        return ColumnDataSource(data.EMPTY)

    def weatherFront(self, name="warm", symbols=chr(983431), colour="red", text_baseline="bottom", line_colour="black", line2_colour=(0,0,0,0), css_class=None, line_dash="solid", starting_font_size=10, line2_scale_factor=1):
        '''
        The weatherfront function of BARC. This draws a Bézier curve and repeats the symbol(s) along it.

        The colours correspond to the symbols; if there are fewer colours than symbols, it cycles back to the start.
        If there are more colours than symbols, then the excess are ignored.

        Baselines work the same way.

        Defaults correspond to a warm front.

        :param str name: Name of front type
        :param colour: Valid :py:class:`ColorSpec <bokeh.core.properties.ColorSpec>` or list of ColorSpecs
        :param line_colour: Valid :py:class:`ColorSpec <bokeh.core.properties.ColorSpec>`.
        :param line2_colour: Valid :py:class:`ColorSpec <bokeh.core.properties.ColorSpec>` for the second line. Defaults transparent (i.e. invisible)
        :param symbols: Unicode text string or sequence of Unicode text strings. If it is a string with length > 1,
                     the individual characters are spaced out, repeating as necessary. If it is a sequence,
                     each one is treated as a "character", and spaced in the same way. They can be of
                     arbitrary length but long strings may produce undesirable results.
        :param text_baseline: Valid :py:data:`TextBaseline <bokeh.core.enums.TextBaseline>` or list of TextBaselines
        :param str css_class: name of a css class to apply to the button. Defaults to ``barc-<name>-button``, where <name> is the ``name`` parameter.
        :param line_dash: A :py:class:`DashPattern <bokeh.core.properties.DashPattern>` specification.
        :param integer starting_font_size: Initial size of the text stamp. Default 10px.
        :param float line2_scale_factor: Default offset for line 2 is the fontsize. This scale factor multiples the offset. Default 1.

        :returns: :py:class:`FrontDrawTool <forest.barc.front_tool.FrontDrawTool>` instance
        '''

        
        #add definition dict for front<->css mapping, if not already present
        # should be a mapping of name: css_class_name (e.g. "warm":"barc-warm-button")
        if not hasattr(self, 'frontbuttons'):
            self.frontbuttons = {}

        self.frontbuttons[name] = css_class if css_class else 'barc-'+name+'-button'

        if not 'bezier'+name in self.source:
            self.source['bezier'+name] = self.bezierSource()
        if not 'bezier2'+name in self.source:
            self.source['bezier2'+name] = self.emptySource()
            self.source['bezier2'+ name].add([], "dx")
            self.source['bezier2'+ name].add([], "dy")
        if not 'fronts'+name in self.source:
            self.source['fronts'+name] = self.emptySource()

        #if fronts source is changed (e.g. via loadData) trigger bezier redraw
        self.source['fronts'+name].js_on_change('data',
            bokeh.models.CustomJS(args=dict(datasource=self.source['bezier'+name]), code="""
            datasource.change.emit();
            """))

        render_lines = []
        for figure in self.figures:
            render_lines.extend([
               #order matters! Typescript assumes multiline is first
               figure.multi_line(xs='xs',ys='ys', color="#aaaaaa", line_width=1, source=self.source['fronts'+name], tags=['multiline']),
               figure.bezier(x0='x0', y0='y0', x1='x1', y1='y1', cx0='cx0', cy0='cy0', cx1="cx1", cy1="cy1", source=self.source['bezier'+name], line_color=line_colour, line_dash=line_dash, line_width=2, tags=['bezier']),
               figure.multi_line(xs='xs', ys='ys', source=self.source['bezier2'+name], color=line2_colour, line_width=2, tags=['bezier2'])
            ])
            for each in symbols:
                if not 'text' + name+each in self.source:
                  self.source['text' + name+each] = self.emptySource()
                  self.source['text' + name+each].add([], "datasize")
                  self.source['text' + name+each].add([], "fontsize")
                  self.source['text' + name+each].add([], "angle")
                if isinstance(colour, type([])):
                    col = colour[symbols.index(each) % len(colour)]
                else:
                    col = colour
                if isinstance(text_baseline, type([])):
                    baseline = text_baseline[symbols.index(each) % len(colour)]
                else:
                    baseline = text_baseline
                render_lines.append(figure.text_stamp(x='xs', y='ys', angle='angle', text_font_size='fontsize', text_font='BARC', text_baseline=baseline, color=value(col), text=value(each), source=self.source['text'+name+each], tags=['text_stamp','fig'+str(self.figures.index(figure))]))


                self.source['bezier'+name].js_on_change('data', 
                  bokeh.models.CustomJS(args=dict(datasource=self.source['text'+name+each], bez2_ds =self.source['bezier2'+name],
                  front_ds= self.source['fronts'+name],
                  starting_font_size=starting_font_size, figure=self.figures[0], line2_scale_factor=line2_scale_factor,

                  colourPicker=self.colourPicker, widthPicker=self.widthPicker
                  ), code="""
                     let fontsize = (widthPicker.value * starting_font_size) +'pt';
                     let starting_font_proportion = (widthPicker.value * starting_font_size)/(figure.inner_height);
                     let datasize =(starting_font_proportion * (figure.y_range.end - figure.y_range.start));
                    
                     //set all fontsizes and datasizes 
                     datasource.data['fontsize'] = datasource.data['fontsize'].map(function(val, index) { return fontsize; })
                     datasource.data['datasize'] = datasource.data['datasize'].map(function(val,index) { return datasize; });

                     datasource.change.emit();

                     //offset 2nd curve by datasize
                     let last = bez2_ds.data['xs'].length-1; //assume lengths of columns are consistent
                     let magnitude = bez2_ds.data['dx'][last].map(function(val,index){ 
                        return Math.sqrt(val**2 + bez2_ds.data['dy'][last][index]**2)/ (datasize * line2_scale_factor);
                     })
 
                     bez2_ds.data['xs'][last] = bez2_ds.data['xs'][last].map( function(val, index){
                        if(bez2_ds.data['dy'][last][index]) {
                           return val - bez2_ds.data['dy'][last][index]/magnitude[index]
                        } else {
                           return val
                        }
                     })
                        
                     bez2_ds.data['ys'][last] = bez2_ds.data['ys'][last].map( function(val, index){
                        if(bez2_ds.data['dx'][last][index]) {
                           return val + bez2_ds.data['dx'][last][index]/magnitude[index]
                        } else {
                           return val
                        }
                     })

                     //only offset once
                     bez2_ds.data['dx'][last] = bez2_ds.data['dx'][last].map(function(val, index) { return null; })
                     bez2_ds.data['dy'][last] = bez2_ds.data['dy'][last].map(function(val, index) { return null; })
                     bez2_ds.change.emit();
                     """)
                )
                self.figures[0].y_range.js_on_change('start',
                  bokeh.models.CustomJS(args=dict(datasource=self.source['text'+name+each],
                  figure=self.figures[0]), code="""
                  for(var g = 0; g < datasource.data['fontsize'].length; g++)
                  {
                     datasource.data['fontsize'][g] = (((datasource.data['datasize'][g])/ (figure.y_range.end - figure.y_range.start))*figure.inner_height) + 'pt';
                  }
                  datasource.change.emit();
                  """)
                )

        try:
            frontTool = FrontDrawTool(
               renderers=render_lines,
               tags=['barc' + name],
               custom_icon=__file__.replace(basename(__file__),'icons/splines/%s.png' % (name,))
            )
        except FileNotFoundError:
            frontTool = FrontDrawTool(
               renderers=render_lines,
               tags=['barc' + name],
            )
        self.source['fronts'+name].js_on_change('data',
                bokeh.models.CustomJS(args=dict(datasource=self.source['fronts'+name]), code="""
                    """)
        )

        return frontTool

    '''def annotation(self, symbol="📍"):
        """Adds a numbered annotation to the plot.

        :param symbol: String to use as a pin. Defaults to Unicode 1f4cd 'Round Pushpin'.

        :returns: :py:class:`PointDrawTool <bokeh.models.tools.PointDrawTool>` with textStamp functionality.
        """
        render_lines=[]
        for figure in self.figures:
            render_lines.append(
                figure.text_stamp(
                    x='xs',
                    y='ys',
                    text_font='BARC',
                    colour="fuchsia",
                    text=value(symbol),
                    source=self.source['annotations'],
                    tags=['annotation'],
                    text_font_size="20px",
                    text_align = 'center',
                    text_baseline = 'bottom'

                )
            )
        self.source['annotations'].js_on_change('data',
            bokeh.models.CustomJS(args=dict(datasource=self.source,
            annotate=self.annotate), code="""
                datasource['annotations'].data['forecastnotes'][datasource['annotations'].data['xs'].length -1] = JSON.stringify(annotate.children.reduce(function(map, obj) { map[obj.name] = obj.value; return map; }, {}));
                """)
        )

        tool3 = PointDrawTool(
            renderers=render_lines,
            tags=['barcannotation'],
        )

        return tool3'''


    def display_glyphs(self):
        """Displays the selected glyph buttons
        """
        buttonspec = {}
        # self.gyphs is set by the dropDown menu, create a button for
        # each glyph
        for glyph in self.glyphs:
            buttonspec[chr(glyph)] = self.icons[glyph]
        buttons = []
        for each in buttonspec:
            button = bokeh.models.widgets.Button(
                label=buttonspec[each],
                css_classes=['barc-' + buttonspec[each] +
                             '-button', 'barc-button'],
                aspect_ratio=1,
                margin=(0, 0, 0, 0)
            )

            button.js_on_event(ButtonClick, bokeh.models.CustomJS(args=dict(
            buttons=list(self.toolBarBoxes.select({'tags': ['barc' + each]}))),
            code="""
                var each;
                for(each of buttons) { each.active = true; }
            """))
            buttons.append(button)
        return buttons

# -----------------------------------------------------------------------------

    def saveDataSources(self):
        '''
          saves current datasources to an sqlite db

          create statement: "CREATE TABLE saved_data (id INTEGER PRIMARY KEY, label TEXT, dateTime INTEGER, json TEXT)"
        '''
        c = self.conn.cursor()

        outdict = {}

        for (k,v) in self.source.items():
            try:
               outdict[k] = v.data
            except:
               print(self.source[k])

        outdict['annotations'] = {}
        for each in self.annotate.children:
            outdict['annotations'][each.name] = each.value

        c.execute("INSERT INTO saved_data (label, dateTime, json) VALUES (?, ?, ?)", [outdict['annotations']['title'], time.time(), json.dumps(outdict)])
        self.conn.commit()

    def loadDataSources(self, event):
        '''
         loads a JSON datasource and updates current sources
        '''
        print(event.item)
        c = self.conn.cursor()

        c.execute("SELECT * FROM saved_data WHERE id=?", [event.item])
        sqlds = c.fetchone()
        jsonds = json.loads(sqlds[3])
        for name in jsonds['annotations']:
            annotes = self.annotate.select({'name': name})
            for n in annotes:
               n.value = jsonds['annotations'][name]
        for each in self.source:
            if each != 'annotations':
               try:
                  self.source[each].data = jsonds[each]
               except KeyError:
                  pass;





    def ToolBar(self):
        """Barc Tool Bar
        """
        toolBarList = []
        # For each figure supplied (if multiple)
        for i, figure in enumerate(self.figures):
            barc_tools = []
            figure.add_tools(
                bokeh.models.tools.UndoTool(tags=['barcundo']),
                bokeh.models.tools.PanTool(tags=['barcpan']),
                bokeh.models.tools.BoxZoomTool(tags=['barcboxzoom']),
                bokeh.models.tools.BoxSelectTool(tags=['barcbox_edit']),
                bokeh.models.tools.ResetTool(tags=['barcreset']),
                bokeh.models.tools.TapTool(tags=['barcreset']),
                self.polyLine(),
                self.polyDraw(),
                self.windBarb(),
                self.weatherFront(name="warm", colour="red", symbols=chr(983431)),
                self.weatherFront(name='cold', colour="blue", symbols=chr(983430)),
                self.weatherFront(name='occluded', colour="purple", symbols=chr(983431)+chr(983430)),
                self.weatherFront(name='stationary', text_baseline=['bottom','top'], colour=['#ff0000','#0000ff'], symbols=chr(983431)+chr(983432)),
                self.weatherFront(name='dryintrusion', colour="#00AAFF", line_colour="#00AAFF", symbols='▮'),
                self.weatherFront(name='dryadvection', colour="blue", line_dash="dashed", symbols=chr(983430)),
                self.weatherFront(name='warmadvection', colour="red", line_dash="dashed", symbols=chr(983431)),
                self.weatherFront(name='convergence', colour="orange", line_colour="orange", text_baseline="alphabetic", symbols=chr(983593), starting_font_size=15),
                self.weatherFront(name='squall', colour="red", line_dash="dashed", text_baseline="alphabetic", line_colour="red", symbols=chr(983590), starting_font_size=30),
                self.weatherFront(name='streamline', colour="#0000f0", text_baseline="middle", line_colour="#00fe00", symbols=chr(9679)),
                self.weatherFront(name='lowleveljet', colour="olive", text_baseline="alphabetic", line_colour="olive", symbols=chr(983552), starting_font_size=20),
                self.weatherFront(name='upper-trough', colour="blue", line_colour="black",line2_colour="black", symbols=chr(983586), starting_font_size=20, line2_scale_factor=0.4),
                self.weatherFront(name='stationary-dry', colour="blue", line_colour="black",line2_colour="black", symbols=" "),
                self.weatherFront(name='quatorial-trough', colour="black", line_colour="black",line2_colour="black", symbols=chr(983591), text_baseline="alphabetic", starting_font_size=20, line2_scale_factor=0.3),
                self.weatherFront(name='monsoon-trough', colour="#fe4b00", line_colour="#fe4b00",line2_colour="#fe4b00", text_baseline="alphabetic", symbols=chr(983592), starting_font_size=20, line2_scale_factor=0.3),
                self.weatherFront(name='nonactive-monsoon-trough', colour="#db6b00", line_colour=(0,0,0,0), text_baseline="alphabetic", symbols=chr(983551), starting_font_size=15),
            )

            for glyph in self.allglyphs:
                glyphtool = self.textStamp(chr(glyph))
                barc_tools.append(glyphtool)
            figure.add_tools(*barc_tools)

            toolBarList.append(
                ToolbarBox(
                    toolbar=figure.toolbar,
                    toolbar_location=None, visible=False,
                    css_classes=['barc_g%d' % i]
                )
            )
        # standard buttons
        toolBarBoxes = bokeh.models.layouts.Column(children=toolBarList)
        self.toolBarBoxes = toolBarBoxes
        buttonspec1 = {
            'undo': 'undo',
            'pan': "move",
            'boxzoom': "boxzoom",
            'box_edit': 'box_edit',
            'reset': 'reset',
            'taptool;': 'tap',
            'freehand': "freehand",
            'poly_draw': 'poly_draw',
            'textbox': 'textbox',
        }

        buttons = []
        for each in buttonspec1:
            button = bokeh.models.widgets.Button(
                label=buttonspec1[each],
                css_classes=['barc-' + buttonspec1[each] +
                             '-button', 'barc-button'],
                aspect_ratio=1,
                margin=(0, 0, 0, 0)
            )
            button.js_on_event(ButtonClick,
            bokeh.models.CustomJS(args=dict(
            buttons=list(toolBarBoxes.select({'tags': ['barc' + each]}))),
            code="""
                    var each;
                    for(each of buttons) { each.active = true; }
                    """))
            buttons.append(button)

        buttons2 = []
        for each in self.frontbuttons:
            button = bokeh.models.widgets.Button(
                label=self.frontbuttons[each],
                css_classes=[self.frontbuttons[each], 'barc-button'],
                aspect_ratio=1,
                margin=(0, 0, 0, 0)
            )
            button.js_on_event(ButtonClick, bokeh.models.CustomJS(
            args=dict(buttons=list(toolBarBoxes.select({'tags': ['barc' + each]}))), code="""
                var each;
                for(each of buttons) { each.active = true; }
            """))
            buttons2.append(button)

        self.barcTools.children.append(bokeh.layouts.grid(buttons, ncols=9))
        self.barcTools.children.append(bokeh.layouts.grid(buttons2, ncols=6))
        self.glyphrow = bokeh.layouts.grid(self.display_glyphs(), ncols=10)
        self.barcTools.children.append(self.glyphrow)
        self.barcTools.children.extend([self.dropDown])
        self.barcTools.children.append(bokeh.layouts.grid([ self.widthPicker, self.colourPicker], ncols=2))
        self.barcTools.children.append(bokeh.layouts.grid([self.saveButton, self.loadButton], ncols=2))
        self.barcTools.children.extend([self.saveArea, self.annotate])
        self.barcTools.children.append(toolBarBoxes)

        return self.barcTools
