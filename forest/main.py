import bokeh.plotting
import bokeh.models
import bokeh.events
import bokeh.colors
from bokeh.core.properties import value
import os
from forest import _profile as profile
from forest import (
        drivers,
        dimension,
        screen,
        tools,
        series,
        data,
        geo,
        colors,
        layers,
        db,
        keys,
        plugin,
        presets,
        redux,
        rx,
        navigate,
        parse_args)
import forest.app
import forest.actions
from forest.barc.toolbar import BARC
from forest.barc.labbook import BARCLab
from forest.barc.reportgenerator import BARCReport
import forest.components
import forest.components.borders
import forest.components.title
from forest.components import tiles, html_ready
import forest.config as cfg
import forest.middlewares as mws
import forest.gallery
from forest.db.util import autolabel


def map_figure(x_range, y_range):
    """Adjust Figure settings to present web map tiles"""
    figure = bokeh.plotting.figure(
        x_range=x_range,
        y_range=y_range,
        x_axis_type="mercator",
        y_axis_type="mercator",
        css_classes=["forestfig"],
        active_scroll="wheel_zoom")
    figure.axis.visible = False
    figure.toolbar.logo = None
    figure.toolbar_location = None
    figure.min_border = 0
    return figure


def configure(argv=None):
    args = parse_args.parse_args(argv)
    data.AUTO_SHUTDOWN = args.auto_shutdown
    if len(args.files) > 0:
        if args.config_file is not None:
            raise Exception('--config-file and [FILE [FILE ...]] not compatible')
        config = cfg.from_files(args.files, args.file_type)
    else:
        config = cfg.Config.load(
                args.config_file,
                variables=cfg.combine_variables(
                    os.environ,
                    args.variables))
    return config


def main(argv=None):
    config = configure(argv=argv)

    # Feature toggles
    if "feature" in config.plugins:
        features = plugin.call(config.plugins["feature"].entry_point)
    else:
        features = config.features
    data.FEATURE_FLAGS = features

    # Full screen map
    viewport = config.default_viewport
    x_range, y_range = geo.web_mercator(
        viewport.lon_range,
        viewport.lat_range)

    figure = map_figure(x_range, y_range)
    figures = [figure]
    for _ in range(2):
        f = map_figure(figure.x_range, figure.y_range)
        figures.append(f)

    figure_row = layers.FigureRow(figures)

    color_mapper = bokeh.models.LinearColorMapper(
            low=0,
            high=1,
            palette=bokeh.palettes.Plasma[256])

    # Convert config to datasets
    datasets = {}
    datasets_by_pattern = {}
    label_to_pattern = {}
    for group, dataset in zip(config.file_groups, config.datasets):
        datasets[group.label] = dataset
        datasets_by_pattern[group.pattern] = dataset
        label_to_pattern[group.label] = group.pattern



    # print('\n\n\n\n', datasets, '\n\n\n\n')

    '''# Lakes
    for figure in figures:
        add_feature(figure, data.LAKES, color="lightblue")

    features = []
    for figure in figures:
        render2 = add_feature(figure, data.LAKES, color="lightblue")
        features += [
            add_feature(figure, data.COASTLINES),
            add_feature(figure, data.BORDERS)]

    # Disputed borders
    for figure in figures:
        add_feature(figure, data.DISPUTED, color="red")
    '''



    toggle = bokeh.models.CheckboxGroup(
            labels=["Coastlines"],
            active=[0],
            width=135)

    def on_change(attr, old, new):
        if len(new) == 1:
            for feature in features:
                feature.visible = True
        else:
            for feature in features:
                feature.visible = False

    toggle.on_change("active", on_change)

    dropdown = bokeh.models.Dropdown(
            label="Color",
            menu=[
                ("Black", "black"),
                ("White", "white")],
            width=50)
    autolabel(dropdown)

    def on_change(event):
        for feature in features:
            feature.glyph.line_color = new

    dropdown.on_click(on_change)

    layers_ui = layers.LayersUI()

    # Add optional sub-navigators
    sub_navigators = {
        key: dataset.navigator()
        for key, dataset in datasets_by_pattern.items()
        if hasattr(dataset, "navigator")
    }
    navigator = navigate.Navigator(sub_navigators)

    middlewares = [
        keys.navigate,
        db.InverseCoordinate("pressure"),
        db.next_previous,
        db.Controls(navigator),  # TODO: Deprecate this middleware
        colors.palettes,
        colors.middleware(),
        presets.Middleware(presets.proxy_storage(config.presets_file)),
        presets.middleware,
        layers.middleware,
        navigator,
        mws.echo,
    ]
    store = redux.Store(
        forest.reducer,
        middlewares=middlewares)

    app = forest.app.Application()
    app.add_component(forest.components.title.Title())

    # Coastlines, borders, lakes and disputed borders
    view = forest.components.borders.View()
    for figure in figures:
        view.add_figure(figure)
    view.connect(store)
    border_ui = forest.components.borders.UI()
    border_ui.connect(store)

    # Colorbar user interface
    component = forest.components.ColorbarUI()
    app.add_component(component)

    # Add time user interface
    if config.defaults.timeui:
        component = forest.components.TimeUI()
        component.layout = bokeh.layouts.row(component.layout, name="time")
        app.add_component(component)

    # Connect MapView orchestration to store
    opacity_slider = forest.layers.OpacitySlider()
    source_limits = colors.SourceLimits().connect(store)
    factory_class = forest.layers.factory(color_mapper,
                                          figures,
                                          source_limits,
                                          opacity_slider)
    gallery = forest.gallery.Gallery.map_view(datasets, factory_class)
    gallery.connect(store)

    # Connect layers controls
    layers_ui.add_subscriber(store.dispatch)
    layers_ui.connect(store)

    # Connect tools controls

    display_names = {
            "time_series": "Display Time Series",
            "profile": "Display Profile",
            }

    display_names2 = {"barc": "BARC Toolkit"}
    available_features = {k: display_names[k]
                          for k in display_names.keys() if data.FEATURE_FLAGS[k]}
    available_features2 = {k: display_names2[k]
                          for k in display_names2.keys() if data.FEATURE_FLAGS[k]}
    tools_panel = tools.ToolsPanel(available_features)
    tools_panel2 = tools.ToolsPanel(available_features2)
    tools_panel.connect(store)
    tools_panel2.connect(store)
    #barc_toolbar=bokeh.models.tools.Toolbar(tools=barc_tools,logo=None)
    if data.FEATURE_FLAGS["BARC"]:
         barc = BARC(figures, store)
         tools_panel2.layout.children.append(barc.tool_bar)
         barclab = BARCLab(figures)
         barcreport = BARCReport(figures)
         barclabpanel= tools.ToolsPanel(available_features2)
         barcreportpanel=tools.ToolsPanel(available_features2)
         barclabpanel.connect(store)
         barcreportpanel.connect(store)
         barclabpanel.layout.children.append(barclab.LabBook())
         barcreportpanel.layout.children.append(barcreport.Report())
         #tools_panel2.layout.children.append(barc.ToolBar())

    # Navbar components
    navbar = Navbar(show_diagram_button=len(available_features) > 0)
    navbar.connect(store)

    # Connect tap listener
    tap_listener = screen.TapListener()
    tap_listener.connect(store)

    # Connect figure controls/views
    if config.defaults.figures.ui:
        figure_ui = layers.FigureUI(config.defaults.figures.maximum)
        figure_ui.connect(store)
    figure_row.connect(store)

    # Tiling picker
    if config.use_web_map_tiles:
        tile_picker = forest.components.TilePicker()
        for figure in figures:
            tile_picker.add_figure(figure)

        tile_picker.connect(store)

    if not data.FEATURE_FLAGS["multiple_colorbars"]:
        # Connect color palette controls
        colors.ColorMapperView(color_mapper).connect(store)
        color_palette = colors.ColorPalette().connect(store)

        # Connect limit controllers to store
        user_limits = colors.UserLimits().connect(store)

    # Preset
    if config.defaults.presetui:
        preset_ui = presets.PresetUI().connect(store)

    # Connect navigation controls
    controls = db.ControlView()
    controls.connect(store)

    # Add support for a modal dialogue
    if data.FEATURE_FLAGS["multiple_colorbars"]:
        view = forest.components.modal.Tabbed()
    else:
        view = forest.components.modal.Default()
    modal = forest.components.Modal(view=view)
    modal.connect(store)

    # Connect components to Store
    app.connect(store)

    # Set initial state
    store.dispatch(forest.actions.set_state(config.state).to_dict())

    # Pre-select menu choices (if any)
    for pattern, _ in sub_navigators.items():
        state = db.initial_state(navigator, pattern=pattern)
        store.dispatch(forest.actions.update_state(state).to_dict())
        break

    # Set default time series visibility
    store.dispatch(tools.on_toggle_tool("time_series", False))

    # Set default profile visibility
    store.dispatch(tools.on_toggle_tool("profile", False))

    # Set top-level navigation
    store.dispatch(db.set_value("patterns", config.patterns))

    # Pre-select first map_view layer
    for label, dataset in datasets.items():
        pattern = label_to_pattern[label]
        for variable in navigator.variables(pattern):
            spec = {"label": label,
                    "dataset": label,
                    "variable": variable,
                    "active": [0]}
            store.dispatch(forest.layers.save_layer(0, spec))
            break
        break

    # Set variable dimensions (needed by modal dialogue)
    for label, dataset in datasets.items():
        pattern = label_to_pattern[label]
        values = navigator.variables(pattern)
        store.dispatch(dimension.set_variables(label, values))

    # Organise controls/settings
    layouts = {}
    layouts["controls"] = []
    if config.defaults.figures.ui:
        layouts["controls"] += [
                bokeh.models.Div(text="Layout:"),
                figure_ui.layout]
    layouts["controls"] += [
        bokeh.models.Div(text="Navigate:"),
        controls.layout,
        bokeh.models.Div(text="Compare:"),
        layers_ui.layout
    ]

    layouts["settings"] = [
        bokeh.models.Div(text="Borders, coastlines and lakes:"),
        border_ui.layout,
        opacity_slider.layout,
    ]

    if not data.FEATURE_FLAGS["multiple_colorbars"]:
        layouts["settings"].append(color_palette.layout)
        layouts["settings"].append(user_limits.layout)
    if config.defaults.presetui:
        layouts["settings"].append(preset_ui.layout)
    if config.use_web_map_tiles:
        layouts["settings"].append(bokeh.models.Div(text="Tiles:"))
        layouts["settings"].append(tile_picker.layout)

    tabs = bokeh.models.Tabs(tabs=[
        bokeh.models.Panel(
            child=bokeh.layouts.column(*layouts["controls"]),
            title="Control"
        ),
        bokeh.models.Panel(
            child=bokeh.layouts.column(*layouts["settings"]),
            title="Settings")
        ])

    tool_figures = {}
    if data.FEATURE_FLAGS["time_series"]:
        # Series sub-figure widget
        series_figure = bokeh.plotting.figure(
                    plot_width=400,
                    plot_height=200,
                    x_axis_type="datetime",
                    toolbar_location=None,
                    border_fill_alpha=0)
        series_figure.toolbar.logo = None

        gallery = forest.gallery.Gallery.series_view(datasets,
                                                     series_figure)
        gallery.connect(store)

        tool_figures["series_figure"] = series_figure

    if data.FEATURE_FLAGS["profile"]:
        # Profile sub-figure widget
        profile_figure = bokeh.plotting.figure(
                    plot_width=300,
                    plot_height=450,
                    toolbar_location=None,
                    border_fill_alpha=0)
        profile_figure.toolbar.logo = None
        profile_figure.y_range.flipped = True

        gallery = forest.gallery.Gallery.profile_view(datasets,
                                                      profile_figure)
        gallery.connect(store)

        tool_figures["profile_figure"] = profile_figure

    tool_layout = tools.ToolLayout(**tool_figures)
    tool_layout.connect(store)
    # Set up barc tabs
    layouts["barc"] = []
    layouts["barc"].append(tools_panel2.layout)
    layouts["barc"].append(barclabpanel.layout)
    layouts["barcreport"] = []
    layouts["barcreport"].append(barcreportpanel.layout)
    tabs2 = bokeh.models.Tabs(tabs=[
        bokeh.models.Panel(
            child=bokeh.layouts.column(*layouts["barc"]),
            title="LabBook"
        ),
        bokeh.models.Panel(
            child=bokeh.layouts.column(*layouts["barcreport"]),
            title="Report Generator")
        ])
    for f in figures:
        f.on_event(bokeh.events.Tap, tap_listener.update_xy)
        marker = screen.MarkDraw(f).connect(store)

    control_root = bokeh.layouts.column(
            tabs,
            name="controls")

    # Add key press support
    key_press = keys.KeyPress()
    key_press.add_subscriber(store.dispatch)

    # Add HTML ready support
    obj = html_ready.HTMLReady(key_press.hidden_button)
    obj.connect(store)

    document = bokeh.plotting.curdoc()
    document.title = "FOREST"
    document.add_root(control_root)
    document.add_root(
        bokeh.layouts.column(
            tools_panel.layout,
            tool_layout.layout,
            width=400,
            name="series"))
    # Add Barc tool bar
    document.add_root(
        bokeh.layouts.column(
            tabs2,
            width=400,
            name="barc"))
    for root in navbar.roots:
        document.add_root(root)
    for root in app.roots:
        document.add_root(root)
    document.add_root(figure_row.layout)
    document.add_root(key_press.hidden_button)
    document.add_root(modal.layout)


class Navbar:
    """Collection of navbar components"""
    def __init__(self, show_diagram_button=True):
        self.headline = forest.components.Headline()
        self.headline.layout.name = "headline"

        self.buttons = {}
        # Add button to control left drawer
        key = "sidenav_button"
        self.buttons[key] = bokeh.models.Button(
            label="Settings",
            name=key)
        custom_js = bokeh.models.CustomJS(code="""
            openId("sidenav");
        """)
        self.buttons[key].js_on_click(custom_js)

        # Add button to control right drawer
        key = "diagrams_button"
        self.buttons[key] = bokeh.models.Button(
            label = '',# label="Diagrams",# now contains the barc logo
            css_classes=["float-right"],
            name=key)

        custom_js = bokeh.models.CustomJS(code="""
         document.getElementById('diagrams').style.width='310px';
         hide_menus();
        """)

        self.buttons[key].js_on_click(custom_js)

        # Add button to control barc drawer
        key = "barcdiagrams_button"
        self.buttons[key] = bokeh.models.Button(
            label = '',# label="Diagrams",# now contains the barc logo
            css_classes=["float-right",'barc_btn'],
            name=key)

        custom_js = bokeh.models.CustomJS(code="""
         document.getElementById('barcdiagrams').style.width='310px';
         hide_menus();
        """)

        self.buttons[key].js_on_click(custom_js)

        roots = [
            self.buttons["sidenav_button"],
            self.headline.layout,
        ]
        if show_diagram_button:
            roots.append(self.buttons["barcdiagrams_button"])
            roots.append(self.buttons["diagrams_button"])
        self.roots = roots

    def connect(self, store):
        self.headline.connect(store)


def any_none(obj, attrs):
    return any([getattr(obj, x) is None for x in attrs])


if __name__.startswith("bokeh"):
    main()
