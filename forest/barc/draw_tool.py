from bokeh.core.properties import Instance
from bokeh.io import output_file, show
from bokeh.core.properties import value
from bokeh.models import ColumnDataSource, EditTool, Drag, Tap, CustomJS
from bokeh.plotting import figure
from bokeh.util.compiler import TypeScript
from forest.barc import text_stamp

#from bokeh.models.tools import FrontDrawTool

output_file('tool.html')

class FrontDrawTool(EditTool, Drag, Tap):
    __implementation__ = "draw_tool.ts"
    #source = Instance(ColumnDataSource)

plot = figure(x_range=(0, 10), y_range=(0, 10))

#plot.bezier(x0=[6.92,1.95], y0=[9.31,8.25], x1=[6.83,4.23], y1=[2.62,5.21], cx0=[2.17,3.15], cy0=[8.21,4.25], cx1=[1.73,2.47], cy1=[4.00,5.00])
#source = ColumnDataSource(data=dict(xs=[6.92,1.95], ys=[9.31,8.25], x0=[6.92,1.95], y0=[9.31,8.25], x1=[6.83,4.23], y1=[2.62,5.21], cx0=[2.17,3.15], cy0=[8.21,4.25], cx1=[1.73,2.47], cy1=[4.00,5.00], angle=[None,None]))
#source = ColumnDataSource(data=dict(xs=[None], ys=[None], x0=[None], y0=[None], x1=[None], y1=[None], cx0=[None], cy0=[None], cx1=[None], cy1=[None],angle=[None]))
source = ColumnDataSource(data=dict(xs=[], ys=[]))#, x0=[], y0=[], x1=[], y1=[], cx0=[], cy0=[], cx1=[], cy1=[],angle=[]))
renderers = [
   #order matters! Typescript assumes multiline, bézier, text_stamp
   plot.multi_line(xs='xs',ys='ys', color="#aaaaaa", line_width=1, source=source),
   plot.bezier(x0='x0', y0='y0', x1='x1', y1='y1', cx0='cx0', cy0='cy0', cx1="cx1", cy1="cy1", source=ColumnDataSource(data=dict(x0=[], y0=[], x1=[], y1=[], cx0=[], cy0=[], cx1=[], cy1=[])), line_color="#d95f02", line_width=2),
   plot.text_stamp(x='x', y='y', angle='angle', color="red", text=value('▲'), source=ColumnDataSource(data=dict(x=[], y=[], angle=[])))
]

source.js_on_change('data',
   CustomJS(args=dict(datasource =source), code="""
      console.log(datasource.data);
   """
   ));

plot.add_tools(FrontDrawTool(renderers=renderers))
plot.title.text = "Draw on the plot"
#plot.bezier(x0=[6.92,1.95], y0=[9.31,8.25], x1=[6.83,4.23], y1=[2.62,5.21], cx0=[2.17,3.15], cy0=[8.21,4.25], cx1=[1.73,2.47], cy1=[4.00,5.00])

show(plot)
