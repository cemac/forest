import bokeh.plotting
import bokeh.models
from bokeh.core.properties import DistanceSpec, StringSpec, Color, ColorSpec, FontSizeSpec, Seq, Either

class TextStamp(bokeh.models.Text):
    '''
    Extension of Bokeh's :py:class:`Text <bokeh.models.glyphs.Text>` class, enabling it to function as a 
    renderer.
    '''
    __implementation__ = "text_stamp.ts"
    _args = ('value', 'colour', 'fontsize')
    #x = DistanceSpec(units_default="screen")
    #y = DistanceSpec(units_default="screen")
    value = StringSpec(default="🌧")
    font = 'BARC'
    colour = ColorSpec(default="fuchsia")
    fontsize = FontSizeSpec(default="30px")

def text_stamp():
    '''Dummy function to be replaced with decorated function'''
    return True


# Extend bokeh.plotting.Figure to support .barb()
if not hasattr(bokeh.plotting.Figure, 'text_stamp'):
    bokeh.plotting.Figure.text_stamp = bokeh.plotting._decorators.glyph_method(TextStamp)(text_stamp)
