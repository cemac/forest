import bokeh.models

import time

from bokeh.models import ColumnDataSource, Paragraph
from bokeh.models.glyphs import Text
from bokeh.core.properties import value
from bokeh.models.tools import PolyDrawTool, PointDrawTool, ToolbarBox,FreehandDrawTool, ProxyToolbar, Toolbar
from bokeh.events import ButtonClick
from forest import wind, data
from . import front

class BARC:
    ''' A class for the BARC features - more documentation needed. ''' 
    barcTools = None
    def __init__(self, figures):
        self.figures = figures
        self.document = bokeh.plotting.curdoc()
        self.barcTools = bokeh.models.layouts.Column(name="barcTools")
        self.source_polyline = ColumnDataSource(data.EMPTY)
        self.source_barb = ColumnDataSource(data.EMPTY)

        self.source_text_stamp = {}
        self.starting_colour = "black" #in CSS-type spec 
        self.starting_width = 2
        self.widthPicker = bokeh.models.widgets.Slider(name="barc_width", end=10.0, start=1.0, value=self.starting_width) 
        self.colourPicker = bokeh.models.widgets.ColorPicker(name="barc_colours", color=self.starting_colour)

        self.glyphs = [
            *range(0x0f0000, 0x0f000a),
            *range(0x0f0027,0x0f0031),
            *range(0x0f004e,0x0f0059), 
            *range(0x0f0075,0x0f007f), 
            *range(0x0f009c,0x0f00a6), 
            *range(0x0f00c3,0x0f00cd), 
            *range(0x0f00ea,0x0f00f4), 
            *range(0x0f0111,0x0f011b), 
            *range(0x0f0138,0x0f0142), 
            *range(0x0f015f,0x0f0169), 
        ] # being the list of unicode character codes for the weather symbols in BARC.woff
    
        ''' For each figure supplied (if multiple) ''' 
        for figure in self.figures:
            figure.toolbar.tools = []
            barc_tools = [
                self.polyLine(),
                self.windBarb()
                ]
            for glyph in self.glyphs:
                self.source_text_stamp[chr(glyph)] = ColumnDataSource(data.EMPTY)
                self.source_text_stamp[chr(glyph)].add([],"datasize")
                self.source_text_stamp[chr(glyph)].add([],"fontsize")
                self.source_text_stamp[chr(glyph)].add([],"colour")
                glyphtool = self.textStamp(chr(glyph))
                barc_tools.append(glyphtool)
            #self.figure.tools = barc_tools
            figure.add_tools(*barc_tools)


    def polyLine(self):
        ''' Freehand Tool '''
        render_lines = []
        self.source_polyline.add([],"colour")
        self.source_polyline.add([],"width")
        for figure in self.figures:
            render_lines.append(  figure.multi_line(
                xs="xs",
                ys="ys",
                line_width="width",
                source=self.source_polyline,
                alpha=0.3,
                color="colour", level="overlay")
                )
        #text = Text(x="xs", y="ys", text=value("abc"), text_color="red", text_font_size="12pt")
        #render_line1 = figure.add_glyph(self.source_polyline,text)
        tool2 = FreehandDrawTool(
                    renderers=[render_lines[0]], 
                    tags=['barcfreehand'],
                    name="barcfreehand"
                    )
        self.source_polyline.js_on_change('data', 
            bokeh.models.CustomJS(args=dict(datasource=self.source_polyline, colourPicker=self.colourPicker, widthPicker=self.widthPicker), code="""
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

    def textStamp(self, glyph = chr(0x0f0000)):
        '''Creates a tool that allows arbitrary Unicode text to be "stamped" on the map. Echos to all figures.

        Params:
            glyph: Arbitrary unicode string, usually a single character.

        returns: 
            PointDrawTool with textStamp functionality.
        '''
        #render_text_stamp = self.figure.circle(x="xs",y="ys",legend_label="X", source=source);
        starting_font_size = 30 #in pixels 

        #render_text_stamp = self.figure.add_glyph(self.source_text_stamp, glyph)
        render_lines = []
        for figure in self.figures:
            render_lines.append(figure.text_stamp(
                x="xs", 
                y="ys", 
                source=self.source_text_stamp[glyph],
                text=value(glyph),  
                text_font='BARC',
                text_color="colour",
                text_font_size="fontsize"
                )
                )
                
        self.source_text_stamp[glyph].js_on_change('data', 
            bokeh.models.CustomJS(args=dict(datasource = self.source_text_stamp[glyph], starting_font_size=starting_font_size, figure=self.figures[0], colourPicker=self.colourPicker), code="""
                for(var g = 0; g < datasource.data['fontsize'].length; g++)
                {
                    if(!datasource.data['colour'][g])
                    {
                        datasource.data['colour'][g] = colourPicker.color;
                    }

                    if(!datasource.data['fontsize'][g])
                    {
                        datasource.data['fontsize'][g] = starting_font_size +'px';
                    }

                    //calculate initial datasize
                    if(!datasource.data['datasize'][g])
                    {
                        var starting_font_proportion = starting_font_size/(figure.inner_height);
                        datasource.data['datasize'][g] = (starting_font_proportion * (figure.y_range.end - figure.y_range.start));
                    }
                }
                """)
        )
        figure.y_range.js_on_change('start',
            bokeh.models.CustomJS(args=dict(render_text_stamp=render_lines[0], glyph=render_lines[0].glyph, figure=self.figures[0], starting_font_size=starting_font_size),code="""

            for(var g = 0; g < render_text_stamp.data_source.data['fontsize'].length; g++)
            {
                 render_text_stamp.data_source.data['fontsize'][g] = (((render_text_stamp.data_source.data['datasize'][g])/ (figure.y_range.end - figure.y_range.start))*figure.inner_height) + 'px';
            }
            glyph.change.emit();
            """)
        )
        #render_text_stamp = bokeh.models.renderers.GlyphRenderer(data_source=ColumnDataSource(dict(x=x, y=y, text="X")), glyph=bokeh.models.Text(x="xs", y="ys", text="text", angle=0.3, text_color="fuchsia"))
        tool3 = PointDrawTool(
                    renderers=render_lines,
                    tags= ['barc'+glyph],
                    )
        return tool3

    def windBarb(self):
        render_lines = []
        for figure in self.figures:
            render_lines.append( figure.barb(
                x="xs", 
                y="ys", 
                u=-50,
                v=-50,
                source=self.source_barb
                ))

        tool4 = PointDrawTool(
                    renderers=render_lines,
                    tags= ['barcwindbarb'],
                    custom_icon = wind.__file__.replace('__init__.py','barb.png')
                    )
                    
        return tool4


    def weatherFront(self,figure,fid:int):
        ''' 
        The weatherfront function of barc

        Arguments:
            Figure - bokeh figure 
            fid (int) - figure index / order
        
        Returns:
            List of custom toolbar elements
        '''
        
        # function to update plot ranges in js
        figure.x_range.js_on_change('start', front.range_change(figure,fid))
        
        # add draw items to toolbar
        toolbars = []
        for front_type in 'warm cold occluded stationary'.split():
            fronttool =  front.front(self,figure,front_type,fid)
            fronttool.tags = ['barc' + front_type +'front']
            toolbars.append( fronttool )
        
        return toolbars #Toolbar(tools = toolbars)

#####################################
#####################################


    def ToolBar(self):
        toolBarList = []
        for i, figure in enumerate(self.figures):
            ### label toolbars
            '''toolBarBoxes.append(
                Paragraph(
                text="""Toolbar: Figure %d"""%(i+1),
                width=200, height=18,
                css_classes=['barc_p','barc_g%d'%i],
                )
            )'''

            figure.add_tools(
                bokeh.models.tools.PanTool(tags=['barcpan']),
                bokeh.models.tools.WheelZoomTool(tags=['barcwheelzoom']),
                bokeh.models.tools.ResetTool(tags=['barcreset']),
                bokeh.models.tools.BoxZoomTool(tags=['barcboxzoom']),
                )

           
            q = time.monotonic() 
            figure.add_tools(*self.weatherFront(figure,i))
            print(time.monotonic() -q, "s")

            toolBarList.append(
                 ToolbarBox(
                     toolbar = figure.toolbar,
                     toolbar_location = None, visible = False,
                     css_classes=['barc_g%d'%i]
                 )
            )
        #self.barcTools.children.extend( toolBarBoxes )
        #tools = sum([ toolbar.tools for toolbar in toolbars ], [])
        #tools.append(self.polyLine())

        toolBarBoxes = bokeh.models.layouts.Column(children=toolBarList)
        

        buttonspec = {
                'freehand': "🖉",
                'windbarb': "🚩",
                'pan': "✥",
                'boxzoom': "🔍",
                'wheelzoom': "📜",
                'reset': "🗘",
                'coldfront': chr(0x0f0186)*2,
                'warmfront': chr(0x0f0187)*2,
                'occludedfront': chr(0x0f0186)+chr(0x0f0187),
                'stationaryfront': chr(0x0f0187)+chr(0x0f0188),
                }
        for glyph in self.glyphs:
            buttonspec[chr(glyph)] = chr(glyph)


        buttons = []

        for each in buttonspec:
            button =bokeh.models.widgets.Button(
                label=buttonspec[each],
                css_classes = ['barc-'+each+'-button','barc-button'],
                aspect_ratio =1,
                margin = (0,0,0,0)
            )
            button.js_on_event(ButtonClick, bokeh.models.CustomJS(args=dict(buttons=list(toolBarBoxes.select({'tags': ['barc'+each]}))), code="""
                var each;
                for(each of buttons) { each.active = true; } 
            """))
            buttons.append(button)

        self.barcTools.children.append( bokeh.layouts.grid(buttons, ncols=9))
        self.barcTools.children.extend([self.colourPicker, self.widthPicker])
        self.barcTools.children.append(toolBarBoxes)


        return self.barcTools
