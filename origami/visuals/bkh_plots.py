"""Classes to generate bokeh plots"""
# Standard library imports
from os import mkdir
from os.path import join
from os.path import isdir

# Third-party imports
import wx.html2
from bokeh.models import Div
from bokeh.models import Range1d
from bokeh.models import ColumnDataSource
from bokeh.layouts import column
from bokeh.plotting import figure
from bokeh.io.export import get_layout_html

DEFAULT_TOOLS = "hover, pan,box_zoom,crosshair,reset"


def is_windows():
    return True


TEMP_DIR = r"D:\GitHub\ORIGAMI\origami\TEMPDIR"


class Plot:
    """
    Base class for all other plots
    Pass the layout property into a wx sizer
    """

    def __init__(
        self, parent, options, x_axis_label="X Axis", y_axis_label="Y Axis", x_axis_type="linear", tools=DEFAULT_TOOLS
    ):
        """
        :param parent: the wx UI object where the plot will be displayed
        :param options: user options object for visual preferences
        :type options: Options
        :param x_axis_label: text for the x-axis title
        :type x_axis_label: str
        :param y_axis_label: text for the y-axis title
        :type y_axis_label: str
        :param x_axis_type: x axis type per bokeh (e.g., 'linear' or 'datetime')
        :type x_axis_type: str
        """

        self.options = options

        self.layout = wx.html2.WebView.New(parent)
        self.bokeh_layout = None
        self.html_str = ""

        # For windows users, since wx.html2 requires a file to load rather than passing a string
        # The file name for each plot will be join(TEMP_DIR, "%s.html" % self.type)
        self.type = None

        self.figure = figure(x_axis_type=x_axis_type, tools=tools, toolbar_sticky=True)
        self.figure.xaxis.axis_label = x_axis_label
        self.figure.yaxis.axis_label = y_axis_label

        self.source = {}  # Will be a dictionary of bokeh ColumnDataSources

    def clear_plot(self):
        if self.bokeh_layout:
            self.clear_sources()
            self.figure.xaxis.axis_label = ""
            self.figure.yaxis.axis_label = ""
            self.update_bokeh_layout_in_wx_python()

    def clear_sources(self):
        for key in list(self.source):
            self.clear_source(key)

    def update_bokeh_layout_in_wx_python(self):
        try:
            self.html_str = get_layout_html(self.bokeh_layout)
        except MemoryError:
            print(
                "ERROR: dvha.models.plot in Plot.update_bokeh_layout_in_wx_python with "
                "bokeh.io.export.get_layout_html() raised MemoryError"
            )
        if is_windows():  # Windows requires LoadURL()
            if not isdir(TEMP_DIR):
                mkdir(TEMP_DIR)
            web_file = join(TEMP_DIR, "%s.html" % self.type)
            with open(web_file, "wb") as f:
                f.write(self.html_str.encode("utf-8"))
            self.layout.LoadURL(web_file)
        else:
            self.layout.SetPage(self.html_str, "")

    @staticmethod
    def clean_data(*data, mrn=None, uid=None, dates=None):
        """
        Data used for statistical analysis in Regression and Control Charts requires no 'None' values and the same
        number of points for each variable.  To mitigate this, clean_data will find all studies that have any 'None'
        values and return data without these studies
        :param data: any number of variables, each being a list of values
        :param mrn: mrns in same order as data
        :param uid: study instance uids in same order data
        :param dates: sim study dates in same order as data
        :return: data only including studies with no 'None' values
        :rtype: tuple
        """
        bad_indices = []
        for var in data:
            bad_indices.extend([i for i, value in enumerate(var) if value == "None"])
        bad_indices = set(bad_indices)

        ans = [[value for i, value in enumerate(var) if i not in bad_indices] for var in data]

        for var in [mrn, uid, dates]:
            if var:
                ans.append([value for i, value in enumerate(var) if i not in bad_indices])

        return tuple(ans)

    def set_figure_dimensions(self):
        pass

    def redraw_plot(self):
        self.set_figure_dimensions()
        self.update_bokeh_layout_in_wx_python()


class PlotSpectrum(Plot):
    def __init__(self, parent, options, xvals, yvals, title="Mass Spectrum"):
        Plot.__init__(self, parent, options)

        self.size_factor = {"plot": (0.95, 0.9)}

        self.type = "spectrum"

        self.div_title = Div(text="<b>%s</b>" % title)

        self.parent = parent
        self.options = options

        self.xvals = xvals
        self.yvals = yvals

        self.source = {"plot": ColumnDataSource(data=dict(x=[], y=[]))}

        self.figure = figure(tools=DEFAULT_TOOLS)

        self.initialize_figures()

        self.__add_plot_data()
        self.__do_layout()
        self.__add_hover()

        self.set_figure_dimensions()

        self.set_data()

        self.update_bokeh_layout_in_wx_python()

    def __add_plot_data(self):
        self.figure.line(x="x", y="y", source=self.source["plot"])

    def __do_layout(self):
        self.bokeh_layout = column(self.div_title, self.figure)

    def __add_hover(self):
        pass

    def initialize_figures(self):
        self.figure.xaxis.axis_label_text_baseline = "bottom"
        self.figure.xaxis.axis_label = "m/z"
        self.figure.yaxis.axis_label = "Intensity"

    def set_figure_dimensions(self):
        panel_width, panel_height = self.parent.GetSize()
        self.figure.plot_width = int(self.size_factor["plot"][0] * float(panel_width))
        self.figure.plot_height = int(self.size_factor["plot"][1] * float(panel_height))

    def update_data(self, xvals, yvals):
        self.xvals = xvals
        self.yvals = yvals
        self.set_data()
        self.redraw_plot()

    def set_data(self):
        if len(self.xvals) == 0 or len(self.yvals) == 0:
            return

        self.source["plot"].data = {"x": self.xvals, "y": self.yvals}
        self.figure.x_range = Range1d(min(self.xvals), max(self.xvals))
        self.figure.y_range = Range1d(min(self.yvals), max(self.yvals) * 1.05)
