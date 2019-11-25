"""
Color palette
-------------

Helpers to choose color palette(s), limits etc.

.. autoclass:: ColorPalette
    :members:

.. autoclass:: UserLimits
    :members:

.. autoclass:: SourceLimits
    :members:

Reducer
~~~~~~~

A reducer combines the current state with an action
to produce a new state

.. autofunction:: reducer

Middleware
~~~~~~~~~~

Middleware pre-processes actions prior to the reducer

.. autofunction:: palettes

Actions
~~~~~~~

Actions are small pieces of data used to communicate
with other parts of the system. Reducers and
middleware functions can interpret their contents
and either update state or generate new actions

.. autofunction:: set_fixed

.. autofunction:: set_reverse

.. autofunction:: set_palette_name

.. autofunction:: set_palette_names

.. autofunction:: set_palette_number

.. autofunction:: set_palette_numbers

.. autofunction:: set_source_limits

.. autofunction:: set_user_high

.. autofunction:: set_user_low

"""
import copy
import bokeh.palettes
import bokeh.colors
import bokeh.layouts
import numpy as np
from forest.observe import Observable
from forest.redux import middleware
from forest.rx import Stream
from forest.db.util import autolabel


SET_PALETTE = "SET_PALETTE"
SET_LIMITS = "SET_LIMITS"


def set_fixed(flag):
    """Action to set fix user-defined limits"""
    return {"kind": SET_PALETTE, "payload": {"fixed": flag}}


def set_reverse(flag):
    """Action to reverse color palette colors"""
    return {"kind": SET_PALETTE, "payload": {"reverse": flag}}


def set_palette_name(name):
    """Action to set color palette name"""
    return {"kind": SET_PALETTE, "payload": {"name": name}}


def set_palette_names(names):
    """Action to set all available palettes"""
    return {"kind": SET_PALETTE, "payload": {"names": names}}


def set_palette_number(number):
    """Action to set color palette size"""
    return {"kind": SET_PALETTE, "payload": {"number": number}}


def set_palette_numbers(numbers):
    """Action to set available levels for color palette"""
    return {"kind": SET_PALETTE, "payload": {"numbers": numbers}}


def set_source_limits(low, high):
    """Action to set colorbar limits from column data sources"""
    return {"kind": SET_LIMITS,
            "payload": {"low": low, "high": high},
            "meta": {"origin": "column_data_source"}}


def is_source_origin(action):
    """Detect origin of set_limits action"""
    origin = action.get("meta", {}).get("origin", "")
    return origin == "column_data_source"


def set_user_high(high):
    """Action to set user defined colorbar higher limit"""
    return {"kind": SET_LIMITS,
            "payload": {"high": high},
            "meta": {"origin": "user"}}


def set_user_low(low):
    """Action to set user defined colorbar lower limit"""
    return {"kind": SET_LIMITS,
            "payload": {"low": low},
            "meta": {"origin": "user"}}


def reducer(state, action):
    """Reducer for colorbar actions

    Combines current state with an action to
    produce the next state

    :returns: new state
    :rtype: dict
    """
    state = copy.deepcopy(state)
    kind = action["kind"]
    if kind in [SET_PALETTE, SET_LIMITS]:
        state["colorbar"] = state.get("colorbar", {})
        state["colorbar"].update(action["payload"])
    return state


@middleware
def palettes(store, next_dispatch, action):
    """Color palette middleware

    Encapsulates colorbar user interface logic. For example,
    if a user has chosen to fix their data limits, then
    set_limit actions generated by column data source changes
    are ignored
    """
    kind = action["kind"]
    if kind == SET_PALETTE:
        payload = action["payload"]
        if "name" in payload:
            name = payload["name"]
            numbers = palette_numbers(name)
            next_dispatch(set_palette_numbers(numbers))
            if "colorbar" in store.state:
                if "number" in store.state["colorbar"]:
                    number = store.state["colorbar"]["number"]
                    if number not in numbers:
                        next_dispatch(set_palette_number(max(numbers)))
        next_dispatch(action)
    elif kind == SET_LIMITS:
        if is_fixed(store.state) and is_source_origin(action):
            # Filter SET_LIMIT actions from ColumnDataSource
            return
        next_dispatch(action)
    else:
        next_dispatch(action)


def is_fixed(state):
    """Helper to discover if fixed limits have been selected"""
    return state.get("colorbar", {}).get("fixed", False)


def palette_numbers(name):
    """Helper to choose available color palette numbers"""
    return list(sorted(bokeh.palettes.all_palettes[name].keys()))


class SourceLimits(Observable):
    """Event stream listening to collection of ColumnDataSources"""
    def __init__(self, sources):
        self.sources = sources
        for source in self.sources:
            source.on_change("data", self.on_change)
        super().__init__()

    def on_change(self, attr, old, new):
        images = []
        for source in self.sources:
            if len(source.data["image"]) == 0:
                continue
            images.append(source.data["image"][0])
        if len(images) > 0:
            low = np.min([np.min(x) for x in images])
            high = np.max([np.max(x) for x in images])
            self.notify(set_source_limits(low, high))
        else:
            self.notify(set_source_limits(0, 1))


class UserLimits(Observable):
    """User controlled color mapper limits"""
    def __init__(self):
        self.inputs = {
            "low": bokeh.models.TextInput(title="Low:"),
            "high": bokeh.models.TextInput(title="High:")
        }
        self.inputs["low"].on_change("value", self.on_input_low)
        self.inputs["high"].on_change("value", self.on_input_high)
        self.checkbox = bokeh.models.CheckboxGroup(
                labels=["Fixed"],
                active=[])
        self.checkbox.on_change("active", self.on_checkbox_change)
        self.layout = bokeh.layouts.column(
                self.inputs["low"],
                self.inputs["high"],
                self.checkbox)
        super().__init__()

    def connect(self, store):
        """Connect component to Store

        Convert state stream to properties used
        by render method.

        :param store: instance to dispatch actions and listen to state changes
        :type store: :class:`forest.redux.Store`
        """
        connect(self, store)

    def on_checkbox_change(self, attr, old, new):
        self.notify(set_fixed(len(new) == 1))

    def on_input_low(self, attr, old, new):
        self.notify(set_user_low(float(new)))

    def on_input_high(self, attr, old, new):
        self.notify(set_user_high(float(new)))

    def render(self, props):
        """Update user-defined limits inputs"""
        if "high" in props:
            self.inputs["high"].value = str(props["high"])
        if "low" in props:
            self.inputs["low"].value = str(props["low"])


class Invisible:
    """Control transparency thresholds"""
    def __init__(self, color_mapper):
        self.color_mapper = color_mapper
        self.invisible_on = False
        self.low = 0
        self.invisible_checkbox = bokeh.models.CheckboxButtonGroup(
            labels=["Invisible"],
            active=[])
        self.invisible_checkbox.on_change("active",
                self.on_invisible_checkbox)
        self.invisible_input = bokeh.models.TextInput(
                title="Low:",
                value="0")
        self.invisible_input.on_change("value",
                self.on_invisible_input)
        self.layout = bokeh.layouts.column(
                self.invisible_checkbox,
                self.invisible_input)

    def on_invisible_checkbox(self, attr, old, new):
        if len(new) == 1:
            self.invisible_on = True
        else:
            self.invisible_on = False

    def on_invisible_input(self, attr, old, new):
        self.low = float(new)

    def render(self):
        if self.invisible_on:
            low = self.low
            color = bokeh.colors.RGB(0, 0, 0, a=0)
            self.color_mapper.low_color = color
            self.color_mapper.low = low


def state_to_props(state):
    """Map state to props relevant to component"""
    return state.get("colorbar", None)


def connect(view, store):
    """Connect component to Store"""
    view.subscribe(store.dispatch)
    stream = (Stream()
                .listen_to(store)
                .map(state_to_props)
                .filter(lambda x: x is not None)
                .distinct())
    stream.map(lambda props: view.render(props))


class ColorPalette(Observable):
    """Color palette user interface"""
    def __init__(self, color_mapper):
        self.color_mapper = color_mapper
        self.dropdowns = {
            "names": bokeh.models.Dropdown(label="Palettes"),
            "numbers": bokeh.models.Dropdown(label="N")
        }
        self.dropdowns["names"].on_change("value", self.on_name)
        self.dropdowns["numbers"].on_change("value", self.on_number)

        self.checkbox = bokeh.models.CheckboxButtonGroup(
            labels=["Reverse"],
            active=[])
        self.checkbox.on_change("active", self.on_reverse)

        self.layout = bokeh.layouts.column(
                bokeh.models.Div(text="Color palette:"),
                self.dropdowns["names"],
                self.dropdowns["numbers"],
                self.checkbox)
        super().__init__()

    def connect(self, store):
        """Connect component to Store"""
        connect(self, store)

    def on_name(self, attr, old, new):
        """Event-handler when a palette name is selected"""
        self.notify(set_palette_name(new))

    def on_number(self, attr, old, new):
        """Event-handler when a palette number is selected"""
        self.notify(set_palette_number(int(new)))

    def on_reverse(self, attr, old, new):
        """Event-handler when reverse toggle is changed"""
        self.notify(set_reverse(len(new) == 1))

    def render(self, props):
        """Render component from properties derived from state"""
        assert isinstance(props, dict), "only support dict"
        if "name" in props:
            self.dropdowns["names"].label = props["name"]
        if "number" in props:
            self.dropdowns["numbers"].label = str(props["number"])
        if ("name" in props) and ("number" in props):
            name = props["name"]
            number = props["number"]
            reverse = props.get("reverse", False)
            palette = self.palette(name, number)
            if reverse:
                palette = palette[::-1]
            self.color_mapper.palette = palette
        if "names" in props:
            values = props["names"]
            self.dropdowns["names"].menu = list(zip(values, values))
        if "numbers" in props:
            values = [str(n) for n in props["numbers"]]
            self.dropdowns["numbers"].menu = list(zip(values, values))
        if "low" in props:
            self.color_mapper.low = props["low"]
        if "high" in props:
            self.color_mapper.high = props["high"]

    @staticmethod
    def palette(name, number):
        return bokeh.palettes.all_palettes[name][number]
