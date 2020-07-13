import bokeh.plotting
import bokeh.models
from bokeh.core.properties import DistanceSpec, StringSpec, ColorSpec, FontSizeSpec

class TextStamp(bokeh.models.Text):
    __implementation__ = "text_stamp.ts"
    _args = ('value', 'colour', 'fontsize')
    x = DistanceSpec(units_default="screen")
    y = DistanceSpec(units_default="screen")
    value = StringSpec(default="🌧")
    colour = ColorSpec(default="fuchsia")
    fontsize = FontSizeSpec(default="30px")

def text_stamp():
    '''Dummy function to be replaced with decorated function'''
    return True


# Extend bokeh.plotting.Figure to support .barb()
if not hasattr(bokeh.plotting.Figure, 'text_stamp'):
    bokeh.plotting.Figure.text_stamp = bokeh.plotting._decorators.glyph_method(TextStamp)(text_stamp)
