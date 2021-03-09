#from bokeh.core.properties import Instance
#from bokeh.io import output_file, show
#from bokeh.core.properties import value
from bokeh.models import EditTool, Drag, Tap, CustomJS
#from bokeh.plotting import figure
#from bokeh.util.compiler import TypeScript
#from forest.barc import text_stamp

#from bokeh.models.tools import FrontDrawTool

class FrontDrawTool(EditTool, Drag, Tap):
    '''
    A tool for drawing Beziér curves with Unicode text evenly-spaced along it (e.g. for 
    weather fronts)
    '''
    __css__ = "forest/static/style_barc.css?v=27"
    __implementation__ = "front_tool.ts"

