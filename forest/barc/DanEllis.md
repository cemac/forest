# Changes to Forrest Code 
## Dan Ellis 

### Issues


### Notes 
- Run command: `forest --dev --config-file nwcsaftest.yml --show; pkill -9 python
`
- Bokeh can only update free draw arrays in server mode (app) and not within normal usage - this makes testing difficult

- Any files required by app need to be in the `forest/static` folder

- app referenced files are already read from `localhost/forest/static`, and therefore do not need this extension. Just add the file as `.static` is your root directory

- for element styling, use `static/style.css`

- elements do not have ids in bokeh. You therefore need to assign them a *class* often using the `css_classes` argument. Even after doing this, elements are often nested within several divs which contain them. Use your web browser to explore them. your css will likely be along the lines of `div.<classname> div <elementtype>`

- JS code that is run on loading of forest can be found in `static/style.css`. This is your only chance at using vanilla js without the need of callbacks. 

- all other js code can be applied as part of a bokeh callback function.

```
callback = bokeh.models.CustomJS(code="""
     do something;
 """)
 
 var.js_on_event('load|click|mouseover etc.', callback)
 
 ```
 
 - bokeh uses websockets to communicate, and therefore data needs to be serialisable (although all text already is)
 
 - also forest's bokeh uses node to create the server, so node packages are a possiblility, although I have not looked at this in too much detail. 
 
 - To clone fronts across all figures, just copy/duplicate the data arrays to all figures.
 
 
 
### Changes to Forest Code
 
#### 0. Pull request into Forest #319
https://github.com/MetOffice/forest/pull/319

A local server self-termination switch for exiting python on closure of browser window and freeing up the port. 
Correspondance and changes shown in the pull request thread and commits. 
 
#### 1. Barc Logo
 - image added to `static`
 - `main.py` edited to remove label and add `barc_btn` class. 
 - `static/style.css` edited to add relevant styling for button and parent classes. 
 
#### 2 SideBar styling and width 
 - `main.py` callback for width styling
 - `static/style.css` for colour 
 - include width parameter in `openId`
 
#### 3. Remove location sensetive references. 
The barc configuration required for forest and the config file to be run within the forest repository (e.g. for finding the wind barb png file). This has been fixed by reading the absolute location of the library and using that to reference the images. 

- barc/toolbar.py line 119:

 `wind.__file__.replace('__init__.py','barb.png')`
 
#### 4. Toolabar labels 
Added descriptors for each barc toolbar and styling. 'Paragraph' `<p>`  elements at the end of barc/toolbar.py.

#### 5. Reading Figure Bounding Box (see next section )
The bounding box is defined by a Range1 bokeh object. 
The easiest way to extract values from this is using its start and end attributes. This can be done using an on_change function. 
```
figure.x_range.on_change('start', lambda attr, old, new: print("Start", new))
figure.x_range.on_change('end', lambda attr, old, new: print("End", new))
```
For drawing fronts, the js callback can read the rage and scale the saved coordinates to match. This can be defined as 

1. get front locations 
2. get bounding Box

```
This section was changed and is no longer valid - bottom. 

3.  ~~remove front points outside of bounding box  ~~
4.  ~~convert front lines to a percentage of the canvas  ~~
5.  ~~plot fronts using canvas pixels ~~
6.  ~~apply custom front font to canvas lines and also draw these on.  ~~

#####  ~~ Notes  ~~

- save fronts to js, allowing the redrawing on each canvas change 
- use global window elements to share these
- update ranges, and add event listener in js to redrawfronts on canvas rerender.
```
##### Changes 
- added global `document.bbox` parameter in `static/scipt.js`.
- this is an array of dictionaries depicting the x and y min/max ranges 
- population is done as a js callback to change of a figures START x_range parameter (when the image is dragged or zoomed)
- only the start parameter is used for the js_on_change callback as all movements of the figure should trigger this. 
- code for this is stored within the front funciton within `barc/front.py`

#### 6. Hide toolbars for figures not plotted 
Each toolbar section is grouped in a class representing its figure number. This is named `barc_gX` where X is the figure number. The function `hide_figures` which was added to `static/script.js` performs this function and runs when the barc toolbar is opened *and* when the number of figures are changed within 'Settings'. 

This relies on a variable `document.maxfig` which needs to be manually updated if forest ever displays more than 3 plots simultaniously

#### 7. WRAPtoolbar on multiple rows
CSS script was added to force the wrapping of the toolbar elements- `static/style.css`. It was possible to add additional toolbars (see commented out coe in `barc/toolbar`, however this broke the link between the document. Ideally this method is preferred but it may be needed )

###  Draw SVG / WeatherFronts
1. To draw the weather fronts, new freehand draw tools are defined, and custom icons selected. 
2. These provide the drawn path data to the `draw_front` function in `static/script.js` 
3. When the screen is moved (an arificial move of the ranges is triggered in `barc/toolbar.py` to trigger this) the js document reads the Figure Ranges and scales the SVG viewbox to match these. 
4. Using the drawn data, path definitions are created within the SVG. These form the basis of the outline the text will follow. These are not plotted in the figure.
5. Drawn data MUST be divided by a scalar, as otherwise it is not possible to scale a font large enough to appear on the map. This is done by dividing by ~100 by the `scaled` constant in `static/script.js` 
6. Drawings from all figures are merged in javascript, but drawn separately on each figure. 
7. Figure overlays should line up and move together if figures do the same. 


## NOTE
- For efficiency only the latest entry within the document.fronts are drawn. 
- if reimporting a file, a new function which loops across all variables needs to be added. This can be used to call the existing `draw_front` function if needed. 
- If wanting  to duplicate the data across different figures, copy data between different `document.fronts` elements. In python this will be done within the BARC class. 
- Coordinates are still contained within bokeh, and can be extracted and stored in the same way as other annotations (when this is implemented).  
- Fast zoom / pan motions do not send sufficient updates to the callback function and often need a 'small' movement afterwards to align the SVG and canvas fronts. 
- There are more canvas elements than figures. This is due to the timeline in the footer. Selecting query canvas elements within the figure div first: 
```
document.canvases = [...document.querySelectorAll('#figures div[class="bk-root"] canvas')].filter((_, index) =>index % 2 === 0)
```
- Icon files are located within `barc/icons` These can be edited and backgrounds added (they are png files for now. )
### Layering 

Python -> Bokeh -> html + canvas (via websockets) -> JS -> SVG -> python
