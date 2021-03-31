import io
import os
import time
import tempfile
from PIL import Image
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, Union, cast

from bokeh.resources import INLINE, Resources
from bokeh.models.layouts import LayoutDOM
from bokeh.document import Document

from bokeh.io.export import export_png, _TempFile, wait_until_render_complete, _maximize_viewport
from bokeh.io.webdriver import webdriver_control, create_firefox_webdriver
from bokeh.embed import file_html


def get_screenshot_as_png(obj: Union[LayoutDOM, Document], *, driver: "Optional[WebDriver]" = None, timeout: int = 5,
        resources: Resources = INLINE, width: Optional[int] = None, height: Optional[int] = None) -> Image:
    ''' Get a screenshot of a ``LayoutDOM`` object, custom for BARC

    Args:
        obj (LayoutDOM or Document) : a Layout (Row/Column), Plot or Widget
            object or Document to export.

        driver (selenium.webdriver) : a selenium webdriver instance to use
            to export the image.

        timeout (int) : the maximum amount of time to wait for initialization.
            It will be used as a timeout for loading Bokeh, then when waiting for
            the layout to be rendered.

    Returns:
        image (PIL.Image.Image) : a pillow image loaded from PNG.

    .. warning::
        Responsive sizing_modes may generate layouts with unexpected size and
        aspect ratios. It is recommended to use the default ``fixed`` sizing mode.

    '''

    with tempfile.TemporaryDirectory(prefix="barc", dir=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','static'))) as tmp:
        html = get_layout_html(obj, resources=resources, width=width, height=height)
        os.symlink(os.path.abspath("forest"),os.path.join(tmp,'forest'))
        htmlfile = os.path.join(tmp,'barcfigure.html')
        
        with open(htmlfile, mode="w", encoding="utf-8") as f:
            f.write(html)

        web_driver = driver if driver is not None else create_firefox_webdriver()
        web_driver.maximize_window()
        web_driver.get("file:///" + htmlfile)
        wait_until_render_complete(web_driver, timeout)
        [width, height, dpr] = _maximize_viewport(web_driver)
        png = web_driver.get_screenshot_as_png()
        web_driver.quit()

    return (Image.open(io.BytesIO(png))
                 .convert("RGBA")
                 .crop((0, 0, width*dpr, height*dpr))
                 .resize((width, height)))


def get_layout_html(obj: Union[LayoutDOM, Document], *, resources: Resources = INLINE,
        width: Optional[int] = None, height: Optional[int] = None) -> str:
    '''
    Replacement function for Bokeh to add extra CSS
    '''
    resize = False
    if width is not None or height is not None:
        # Defer this import, it is expensive
        from ..models.plots import Plot
        if not isinstance(obj, Plot):
            warnings.warn("Export method called with height or width kwargs on a non-Plot layout. The size values will be ignored.")
        else:
            resize = True

            old_width = obj.plot_width
            old_height = obj.plot_height

            if width is not None:
                obj.plot_width = width
            if height is not None:
                obj.plot_height = height

    template = r"""\
    {% block preamble %}
    <style>
        html, body {
            box-sizing: border-box;
            width: 100%;
            height: 100%;
            margin: 0;
            border: 0;
            padding: 0;
            overflow: hidden;
        }
   /* BARC Font */
   @font-face {
      font-family: BARC;
      src: url('BARC.woff') format('woff');
   }  

    </style>
    {% endblock %}
    """

    try:
        html = file_html(obj, resources, title="", template=template, suppress_callback_warning=True, _always_new=True)
    finally:
        if resize:
            assert isinstance(obj, Plot)
            obj.plot_width = old_width
            obj.plot_height = old_height

    return html

