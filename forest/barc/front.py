'''
Data for Weather Front drawing on BARC  

'''
from bokeh.models import ColumnDataSource, CustomJS , Paragraph
from bokeh.models.tools import FreehandDrawTool
from forest import data
import time


# def mecator_2_percent(posn):
#     ''' 
#     NO LONGER NEEDED - normalise by range not location
# 
#     Convert between EPSG:3857 WGS 84 / Pseudo-Mercator to a percentage of the lon lat map -180 to 180 and -90 to 90 map
# 
#     x = lon
#     y = lat
#     '''
# 
# 
#     mlon = 20037508.34
#     mlat = 31296372.44
# 
#     x = (np.array(posn['xs']) + mlon) / mlon
#     y = (np.array(posn['ys']) + mlon) / mlon
# 
#     return [[x[i],y[i]] for i in range(len(x))]

    
def range_shift(figure):
    '''
    This needs to happen AFTER document load
    '''
    figure.x_range.start += 10 
    time.sleep(1)
    figure.x_range.start -= 10
    print('shift test')


def range_change(figure,i):
    ''' Callback function on map range change '''
    
    time.sleep(2)
    print ('∆ change')
    
    js = CustomJS(args=dict(xr=figure.x_range,yr=figure.y_range,fig_n=i), code="""
        document.bbox[fig_n] = {x0:xr.start, x1:xr.end, y0:yr.start, y1:yr.end};
        console.log('∆range')
        resize_svg(fig_n)
        """)

    return js
    



def front_callback(cdata,figure,which,fid):
    ''' Update the JS variables containing all drawn front paths. '''
    #pts= mecator_2_percent(data)
    

    js = CustomJS(args=dict(paths = cdata,fronttype = which,figure=figure, fig_n=fid, xr=figure.x_range,yr=figure.y_range),
    code="""
    
        // if we have an empty canvas array - populate this
        if (document.canvases.length != document.n ){get_figures()};
        
        document.fronts[fronttype]=paths.data
        console.log(document.fronts)
        draw_front(fronttype,fig_n)  
        
        // update ranges
        document.bbox[fig_n] = {x0:xr.start, x1:xr.end, y0:yr.start, y1:yr.end};
        resize_svg(fig_n)
          
    """)

    return js
    



    
def front(self, figure, which:str,fid:int):
        '''
        Freehand drawtool for weather fronts
        
        Arguments:
            Figure - bokeh figure
            Which:str - type of front
            fid: figure number (raw)
            
        Documentation of FreehandDrawTool
                
            Draw patch/multi-line
            Click and drag to start drawing and release the mouse button to finish drawing

            Delete patch/multi-line
            Tap a line or patch to select it then press BACKSPACE key while the mouse is within the plot area.

            To Delete multiple patches/lines at once:
            Delete selection
            Select patches/lines with SHIFT+tap (or another selection tool) then press BACKSPACE while the mouse is within the plot area.

        '''
        
        colours = {'warm':'red','cold':'blue','occluded':'purple','stationary':'green'}
        # actual svg colours in static stylesheet
        
        setattr(self, 'source_'+which , ColumnDataSource(data.EMPTY) )
        
        line =  figure.multi_line(
            xs="xs",
            ys="ys",
            source=getattr(self , 'source_'+which ),
            alpha=0.01,
            color=colours[which], level="overlay")
            
        drawfront = FreehandDrawTool(renderers=[line],custom_icon=__file__.replace('front.py','icons/%s.png'%which))
                    
        getattr(self , 'source_'+which ).js_on_change('data', front_callback(line.data_source,figure,which,fid) )
        
        
        # def line_change (attr,old,new):
        #     print('\n\n\n', self.source_polyline.data,attr,old,new)
        # self.source_polyline.on_change('data',line_change)
        
    
        
        return drawfront
        
        