# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import re
from copy import deepcopy
from time import time as ttime

import wx
from gui_elements.dialog_color_picker import DialogColorPicker
from help_documentation import OrigamiHelp
from styles import makeCheckbox
from styles import makeStaticBox
from styles import makeStaticText
from styles import validator
from utils.color import convertRGB1to255
from utils.converters import str2num


class panelCustomiseInteractive(wx.MiniFrame):
    """
    Panel where you can customise interactive plots
    """

    def __init__(self, presenter, parent, config, icons, **kwargs):
        wx.MiniFrame.__init__(
            self,
            parent,
            -1,
            "Customise interactive plot...",
            size=(-1, -1),
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER,
        )
        tstart = ttime()
        self._loading_ = True
        self.presenter = presenter
        self.parent = parent
        self.config = config
        self.icons = icons
        self.help = OrigamiHelp()

        # retrieve data from kwargs
        self.data = kwargs.pop("data")
        self.document_title = kwargs.pop("document_title")
        self.item_type = kwargs.pop("item_type")
        self.item_title = kwargs.pop("item_title")
        self.kwargs = deepcopy(self.data.get("interactive_params", {}))

        self._checkInteractiveParameters()

        # make gui items
        self.make_gui()
        self.Layout()
        self.SetSize((521, 550))
        self.SetMinSize((521, 550))
        self.SetFocus()

        # bind
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

        self.onEnableDisable_widgets(None)

        self._loading_ = False

        self.parent.onUpdateItemParameters(self.document_title, self.item_type, self.item_title, self.kwargs)

        msg = "Customising parameters of: {} - {} - {}. Startup took {:.3f} seconds".format(
            self.document_title, self.item_type, self.item_title, ttime() - tstart
        )
        print(msg)

    def on_key_event(self, evt):
        """Respond to key press"""
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)

        if evt is not None:
            evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def _checkInteractiveParameters(self):

        if "widgets" not in self.kwargs:
            self.kwargs["widgets"] = {}

        if "tools" not in self.kwargs:
            self.kwargs["tools"] = {}

        if "preprocessing_properties" not in self.kwargs:
            self.kwargs["preprocessing_properties"] = {}

        if "plot_properties" not in self.kwargs:
            self.kwargs["plot_properties"] = {}

        if "legend_properties" not in self.kwargs:
            self.kwargs["legend_properties"] = {}

        if "colorbar_properties" not in self.kwargs:
            self.kwargs["colorbar_properties"] = {}

        if "annotation_properties" not in self.kwargs:
            self.kwargs["annotation_properties"] = {}

        if "frame_properties" not in self.kwargs:
            self.kwargs["frame_properties"] = {}

        if "overlay_properties" not in self.kwargs:
            self.kwargs["overlay_properties"] = {}

        # plot size information
        if "plot_width" not in self.kwargs:
            self.kwargs["plot_width"] = self.config.figWidth
        if "plot_height" not in self.kwargs:
            self.kwargs["plot_height"] = self.config.figHeight

        # plot information
        if "xlimits" not in self.kwargs:
            self.kwargs["xlimits"] = None
        if "ylimits" not in self.kwargs:
            self.kwargs["ylimits"] = None

    def _check_allowed_windows(self):
        """
        Check which settings can be displayed for selected item
        """
        allowed_window = [
            "general",
            "plots",
            "tools",
            "annotations",
            "legend",
            "colorbar",
            "overlay",
            "widgets",
            "preprocess",
        ]
        remove_window_list = []

        if self.item_type in ["1D", "RT", "MS"]:
            remove_window_list = ["overlay", "colorbar"]
        elif self.item_type in ["2D"]:
            remove_window_list = ["annotations"]
        elif self.item_type in ["Overlay", "Statistical"]:
            method = re.split("-|,|:|__", self.item_title)
            if method[0] in [
                "Mask",
                "Transparent",
                "RMSD",
                "RMSF",
                "Mean",
                "Standard Deviation",
                "Variance",
                "RMSD Matrix",
            ]:
                remove_window_list = ["preprocess", "annotations"]
            elif method[0] in ["1D", "RT"]:
                remove_window_list = ["colorbar"]
        elif self.item_type in ["Annotated data"]:
            remove_window_list = ["overlay"]
        #
        for item in remove_window_list:
            try:
                allowed_window.remove(item)
            except Exception:
                pass

        #             if any(method[0] in item for item in ['Mask', 'Transparent']):
        #                 preset = 'Overlay'
        #             elif any(method[0] in item for item in ['RMSD', 'RMSF', 'Mean',
        #                                                     'Standard Deviation',
        #                                                     'Variance', 'RMSD Matrix']):
        #                 preset = '2D'
        #             elif any(method[0] in item for item in ['1D', 'RT']):
        #                 preset = '1D'

        return allowed_window

    def onUpdateDocument(self):
        self.parent.onUpdateItemParameters(self.document_title, self.item_type, self.item_title, self.kwargs)

    def make_gui(self):

        allowed_windows = self._check_allowed_windows()

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        # Setup notebook
        self.mainBook = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        # general
        if "general" in allowed_windows:
            self.settings_general = wx.Panel(
                self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.NB_MULTILINE
            )
            self.mainBook.AddPage(self.makeGeneralPanel(self.settings_general), "General", False)

        if "preprocess" in allowed_windows:
            self.settings_preprocess = wx.Panel(
                self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.NB_MULTILINE
            )
            self.mainBook.AddPage(self.makePreprocessingPanel(self.settings_preprocess), "Pre-process", False)

        # annotations
        if "plots" in allowed_windows:
            self.settings_plot = wx.Panel(
                self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.NB_MULTILINE
            )
            self.mainBook.AddPage(self.makePlotPanel(self.settings_plot), "Plot", False)

        # annotations
        if "annotations" in allowed_windows:
            self.settings_annotations = wx.Panel(
                self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.NB_MULTILINE
            )
            self.mainBook.AddPage(self.makeAnnotationsPanel(self.settings_annotations), "Annotations", False)

        # colorbar
        if "colorbar" in allowed_windows:
            self.settings_colorbar = wx.Panel(
                self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.NB_MULTILINE
            )
            self.mainBook.AddPage(self.makeColorbarPanel(self.settings_colorbar), "Colorbar", False)

        # legend
        if "legend" in allowed_windows:
            self.settings_legend = wx.Panel(
                self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.NB_MULTILINE
            )
            self.mainBook.AddPage(self.makeLegendPanel(self.settings_legend), "Legend", False)

        # overlay
        if "overlay" in allowed_windows:
            self.settings_overlay = wx.Panel(
                self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.NB_MULTILINE
            )
            self.mainBook.AddPage(self.makeOverlayPanel(self.settings_overlay), "Overlay", False)

        # tools
        if "tools" in allowed_windows:
            self.settings_tools = wx.Panel(
                self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.NB_MULTILINE
            )
            self.mainBook.AddPage(self.makeToolsPanel(self.settings_tools), "Tools", False)

        # widgets
        if "widgets" in allowed_windows:
            self.settings_widgets = wx.Panel(
                self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL | wx.NB_MULTILINE
            )
            self.mainBook.AddPage(self.makeWidgetsPanel(self.settings_widgets), "Widgets", False)

    def makeGeneralPanel(self, panel):

        figure_height_label = makeStaticText(panel, "Height:")
        self.figure_height_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=2000,
            inc=100,
            size=(70, -1),
            value=str(self.kwargs.get("plot_height", self.config.figHeight1D)),
            initial=self.kwargs.get("plot_height", self.config.figHeight1D),
        )
        self.figure_height_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)

        figure_width_label = makeStaticText(panel, "Width:")
        self.figure_width_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=2000,
            inc=100,
            size=(70, -1),
            value=str(self.kwargs.get("plot_width", self.config.figWidth1D)),
            initial=self.kwargs.get("plot_width", self.config.figWidth1D),
        )
        self.figure_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)

        figureSize_staticBox = makeStaticBox(panel, "Figure parameters", size=(-1, -1), color=wx.BLACK)
        figureSize_staticBox.SetSize((-1, -1))
        figureSize_box_sizer = wx.StaticBoxSizer(figureSize_staticBox, wx.HORIZONTAL)
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(figure_height_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.figure_height_value, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(figure_width_label, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.figure_width_value, (y, 3), flag=wx.ALIGN_CENTER_VERTICAL)
        figureSize_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        title_fontsize_label = makeStaticText(panel, "Title font size")
        self.frame_title_fontsize = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=32,
            inc=2,
            size=(50, -1),
            value=str(
                self.kwargs.get("frame_properties", {}).get("title_fontsize", self.config.interactive_title_fontSize)
            ),
            initial=self.kwargs.get("frame_properties", {}).get(
                "title_fontsize", self.config.interactive_label_fontSize
            ),
        )
        self.frame_title_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)
        self.frame_title_fontsize.SetToolTip(wx.ToolTip("Title font size. Value in points."))

        self.frame_title_weight = makeCheckbox(panel, "bold", name="frame")
        self.frame_title_weight.SetValue(
            self.kwargs.get("frame_properties", {}).get("title_fontweight", self.config.interactive_title_weight)
        )
        self.frame_title_weight.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.frame_title_weight.SetToolTip(wx.ToolTip("Title font weight."))

        label_fontsize_label = makeStaticText(panel, "Label font size")
        self.frame_label_fontsize = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=32,
            inc=2,
            size=(50, -1),
            value=str(
                self.kwargs.get("frame_properties", {}).get("label_fontsize", self.config.interactive_label_fontSize)
            ),
            initial=self.kwargs.get("frame_properties", {}).get(
                "label_fontsize", self.config.interactive_label_fontSize
            ),
        )
        self.frame_label_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)
        self.frame_label_fontsize.SetToolTip(wx.ToolTip("Label font size. Value in points."))

        self.frame_label_weight = makeCheckbox(panel, "bold", name="frame")
        self.frame_label_weight.SetValue(
            self.kwargs.get("frame_properties", {}).get("label_fontweight", self.config.interactive_label_weight)
        )
        self.frame_label_weight.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.frame_label_weight.SetToolTip(wx.ToolTip("Label font weight."))

        ticks_fontsize_label = makeStaticText(panel, "Tick font size")
        self.frame_ticks_fontsize = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=32,
            inc=2,
            size=(50, -1),
            value=str(
                self.kwargs.get("frame_properties", {}).get("tick_fontsize", self.config.interactive_tick_fontSize)
            ),
            initial=self.kwargs.get("frame_properties", {}).get("tick_fontsize", self.config.interactive_tick_fontSize),
        )
        self.frame_ticks_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)
        self.frame_ticks_fontsize.SetToolTip(wx.ToolTip("Tick font size. Value in points."))

        # axes parameters
        fontSize_staticBox = makeStaticBox(panel, "Font parameters", size=(-1, -1), color=wx.BLACK)
        fontSize_staticBox.SetSize((-1, -1))
        fontSize_box_sizer = wx.StaticBoxSizer(fontSize_staticBox, wx.HORIZONTAL)
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(title_fontsize_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.frame_title_fontsize, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.frame_title_weight, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        y = y + 1
        grid.Add(label_fontsize_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.frame_label_fontsize, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.frame_label_weight, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        y = y + 1
        grid.Add(ticks_fontsize_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.frame_ticks_fontsize, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        fontSize_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        plot_xmin_label = makeStaticText(panel, "X min:")
        self.plot_xmin_value = wx.TextCtrl(panel, -1, "", size=(80, -1), validator=validator("float"))
        self.plot_xmin_value.Bind(wx.EVT_TEXT, self.on_apply_general)

        plot_xmax_label = makeStaticText(panel, "X max:")
        self.plot_xmax_value = wx.TextCtrl(panel, -1, "", size=(80, -1), validator=validator("float"))
        self.plot_xmax_value.Bind(wx.EVT_TEXT, self.on_apply_general)

        if self.kwargs["xlimits"] is not None:
            try:
                self.plot_xmin_value.SetValue(str(float(self.kwargs["xlimits"][0])))
            except Exception:
                pass
            try:
                self.plot_xmax_value.SetValue(str(float(self.kwargs["xlimits"][1])))
            except Exception:
                pass

        plot_ymin_label = makeStaticText(panel, "Y min:")
        self.plot_ymin_value = wx.TextCtrl(panel, -1, "", size=(80, -1), validator=validator("float"))
        self.plot_ymin_value.Bind(wx.EVT_TEXT, self.on_apply_general)

        plot_ymax_label = makeStaticText(panel, "Y max:")
        self.plot_ymax_value = wx.TextCtrl(panel, -1, "", size=(80, -1), validator=validator("float"))
        self.plot_ymax_value.Bind(wx.EVT_TEXT, self.on_apply_general)

        # set y-mins
        if self.kwargs["ylimits"] is not None:
            try:
                self.plot_ymin_value.SetValue(str(float(self.kwargs["ylimits"][0])))
            except Exception:
                pass
            try:
                self.plot_ymax_value.SetValue(str(float(self.kwargs["ylimits"][1])))
            except Exception:
                pass

        # axes parameters
        plotSize_staticBox = makeStaticBox(panel, "Plot parameters", size=(-1, -1), color=wx.BLACK)
        plotSize_staticBox.SetSize((-1, -1))
        plotSize_box_sizer = wx.StaticBoxSizer(plotSize_staticBox, wx.HORIZONTAL)
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(plot_xmin_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_xmin_value, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(plot_xmax_label, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_xmax_value, (y, 3), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(plot_ymin_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_ymin_value, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(plot_ymax_label, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_ymax_value, (y, 3), flag=wx.ALIGN_CENTER_VERTICAL)
        plotSize_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        label_label = wx.StaticText(panel, -1, "Label:")
        self.frame_label_xaxis_check = makeCheckbox(panel, "x-axis", name="frame")
        self.frame_label_xaxis_check.SetValue(self.kwargs.get("frame_properties", {}).get("label_xaxis", True))
        self.frame_label_xaxis_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.frame_label_xaxis_check.SetToolTip(wx.ToolTip("Show labels on the x-axis."))

        self.frame_label_yaxis_check = makeCheckbox(panel, "y-axis", name="frame")
        self.frame_label_yaxis_check.SetValue(self.kwargs.get("frame_properties", {}).get("label_yaxis", True))
        self.frame_label_yaxis_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.frame_label_yaxis_check.SetToolTip(wx.ToolTip("Show labels on the y-axis."))

        tickLabels_label = wx.StaticText(panel, -1, "Tick labels:")
        self.frame_tick_labels_xaxis_check = makeCheckbox(panel, "x-axis", name="frame")
        self.frame_tick_labels_xaxis_check.SetValue(
            self.kwargs.get("frame_properties", {}).get("tick_labels_xaxis", True)
        )
        self.frame_tick_labels_xaxis_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.frame_tick_labels_xaxis_check.SetToolTip(wx.ToolTip("Show tick labels on the x-axis"))

        self.frame_tick_labels_yaxis_check = makeCheckbox(panel, "y-axis", name="frame")
        self.frame_tick_labels_yaxis_check.SetValue(
            self.kwargs.get("frame_properties", {}).get("tick_labels_yaxis", True)
        )
        self.frame_tick_labels_yaxis_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.frame_tick_labels_yaxis_check.SetToolTip(wx.ToolTip("Show tick labels on the y-axis"))

        ticks_label = wx.StaticText(panel, -1, "Ticks:")
        self.frame_ticks_xaxis_check = makeCheckbox(panel, "x-axis", name="frame")
        self.frame_ticks_xaxis_check.SetValue(self.kwargs.get("frame_properties", {}).get("ticks_xaxis", True))
        self.frame_ticks_xaxis_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.frame_ticks_xaxis_check.SetToolTip(wx.ToolTip("Show ticks on the x-axis"))

        self.frame_ticks_yaxis_check = makeCheckbox(panel, "y-axis", name="frame")
        self.frame_ticks_yaxis_check.SetValue(self.kwargs.get("frame_properties", {}).get("ticks_yaxis", True))
        self.frame_ticks_yaxis_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.frame_ticks_yaxis_check.SetToolTip(wx.ToolTip("Show ticks on the y-axis"))

        borderLeft_label = makeStaticText(panel, "Border\nleft")
        self.frame_border_min_left = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=100,
            inc=5,
            size=(50, -1),
            value=str(
                self.kwargs.get("frame_properties", {}).get("border_left", self.config.interactive_border_min_left)
            ),
            initial=int(
                self.kwargs.get("frame_properties", {}).get("border_left", self.config.interactive_border_min_left)
            ),
        )
        self.frame_border_min_left.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.frame_border_min_left.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)

        borderRight_label = makeStaticText(panel, "Border\nright")
        self.frame_border_min_right = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=100,
            inc=5,
            size=(50, -1),
            value=str(
                self.kwargs.get("frame_properties", {}).get("border_right", self.config.interactive_border_min_right)
            ),
            initial=int(
                self.kwargs.get("frame_properties", {}).get("border_right", self.config.interactive_border_min_right)
            ),
        )
        self.frame_border_min_right.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.frame_border_min_right.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)

        borderTop_label = makeStaticText(panel, "Border\ntop")
        self.frame_border_min_top = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=100,
            inc=5,
            size=(50, -1),
            value=str(
                self.kwargs.get("frame_properties", {}).get("border_top", self.config.interactive_border_min_top)
            ),
            initial=int(
                self.kwargs.get("frame_properties", {}).get("border_top", self.config.interactive_border_min_top)
            ),
        )
        self.frame_border_min_top.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.frame_border_min_top.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)

        borderBottom_label = makeStaticText(panel, "Border\nbottom")
        self.frame_border_min_bottom = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=100,
            inc=5,
            size=(50, -1),
            value=str(
                self.kwargs.get("frame_properties", {}).get("border_bottom", self.config.interactive_border_min_bottom)
            ),
            initial=int(
                self.kwargs.get("frame_properties", {}).get("border_bottom", self.config.interactive_border_min_bottom)
            ),
        )
        self.frame_border_min_bottom.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.frame_border_min_bottom.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)

        outlineWidth_label = makeStaticText(panel, "Outline\nwidth")
        self.frame_outline_width = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=5,
            inc=0.5,
            size=(50, -1),
            value=str(
                self.kwargs.get("frame_properties", {}).get("outline_width", self.config.interactive_outline_width)
            ),
            initial=self.kwargs.get("frame_properties", {}).get("outline_width", self.config.interactive_outline_width),
        )
        self.frame_outline_width.SetToolTip(wx.ToolTip("Plot outline line thickness"))
        self.frame_outline_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)

        outlineTransparency_label = makeStaticText(panel, "Outline\nalpha")
        self.frame_outline_alpha = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=1,
            inc=0.05,
            size=(50, -1),
            value=str(
                self.kwargs.get("frame_properties", {}).get("outline_alpha", self.config.interactive_outline_alpha)
            ),
            initial=self.kwargs.get("frame_properties", {}).get("outline_alpha", self.config.interactive_outline_alpha),
        )
        self.frame_outline_alpha.SetToolTip(wx.ToolTip("Plot outline line transparency value"))
        self.frame_outline_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_general)

        frame_background_color = makeStaticText(panel, "Background\ncolor")
        self.frame_background_colorBtn = wx.Button(panel, wx.ID_ANY, size=wx.Size(26, 26), name="background_color")
        self.frame_background_colorBtn.SetBackgroundColour(
            convertRGB1to255(
                self.kwargs.get("frame_properties", {}).get(
                    "background_color", self.config.interactive_background_color
                )
            )
        )
        self.frame_background_colorBtn.Bind(wx.EVT_BUTTON, self.on_apply_color)

        frame_gridline_label = makeStaticText(panel, "Grid lines:")
        self.frame_gridline_check = makeCheckbox(panel, "show")
        self.frame_gridline_check.SetValue(
            self.kwargs.get("frame_properties", {}).get("gridline", self.config.interactive_grid_line)
        )
        self.frame_gridline_check.Bind(wx.EVT_CHECKBOX, self.on_apply_general)
        self.frame_gridline_check.SetToolTip(wx.ToolTip("Show gridlines in the plot area."))

        frame_gridline_color = makeStaticText(panel, "Grid\ncolor")
        self.frame_gridline_color = wx.Button(panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="gridline_color")
        self.frame_gridline_color.SetBackgroundColour(
            convertRGB1to255(
                self.kwargs.get("frame_properties", {}).get("gridline_color", self.config.interactive_grid_line_color)
            )
        )
        self.frame_gridline_color.Bind(wx.EVT_BUTTON, self.on_apply_color)
        self.frame_gridline_check.SetToolTip(wx.ToolTip("Gridlines color. Only takes effect if gridlines are shown."))

        # axes parameters
        frameParameters_staticBox = makeStaticBox(panel, "Frame parameters", size=(-1, -1), color=wx.BLACK)
        frameParameters_staticBox.SetSize((-1, -1))
        frame_box_sizer = wx.StaticBoxSizer(frameParameters_staticBox, wx.HORIZONTAL)
        axis_grid = wx.GridBagSizer(2, 2)
        y = 0
        axis_grid.Add(label_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_label_xaxis_check, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(self.frame_label_yaxis_check, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        axis_grid.Add(tickLabels_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_tick_labels_xaxis_check, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(self.frame_tick_labels_yaxis_check, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        axis_grid.Add(ticks_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_ticks_xaxis_check, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(self.frame_ticks_yaxis_check, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        axis_grid.Add(borderLeft_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_border_min_left, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(borderRight_label, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_border_min_right, (y, 3), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(borderTop_label, (y, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_border_min_top, (y, 5), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(borderBottom_label, (y, 6), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_border_min_bottom, (y, 7), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        axis_grid.Add(outlineWidth_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_outline_width, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(outlineTransparency_label, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_outline_alpha, (y, 3), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(frame_background_color, (y, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_background_colorBtn, (y, 5), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        axis_grid.Add(frame_gridline_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_gridline_check, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(frame_gridline_color, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_gridline_color, (y, 3), flag=wx.ALIGN_CENTER_VERTICAL)
        frame_box_sizer.Add(axis_grid, 0, wx.EXPAND, 10)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(figureSize_box_sizer, (y, 0), flag=wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)
        y = y + 1
        grid.Add(fontSize_box_sizer, (y, 0), flag=wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)
        y = y + 1
        grid.Add(plotSize_box_sizer, (y, 0), flag=wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)
        y = y + 1
        grid.Add(frame_box_sizer, (y, 0), flag=wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, wx.ALIGN_CENTER_HORIZONTAL, 2)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def makePlotPanel_scatter(self, panel):

        plot_scatter_shape_choice = makeStaticText(panel, "Marker shape:")
        self.plot_scatter_shape_choice = wx.ComboBox(
            panel, -1, choices=self.config.interactive_scatter_marker_choices, style=wx.CB_READONLY
        )
        self.plot_scatter_shape_choice.SetStringSelection(
            self.kwargs.get("plot_properties", {}).get("scatter_shape", self.config.interactive_scatter_marker)
        )
        self.plot_scatter_shape_choice.Bind(wx.EVT_COMBOBOX, self.on_apply_plots)

        plot_scatter_size_value = makeStaticText(panel, "Marker size:")
        self.plot_scatter_size_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0.5,
            max=100,
            inc=5,
            size=(50, -1),
            value=str(self.kwargs.get("plot_properties", {}).get("scatter_size", self.config.interactive_scatter_size)),
            initial=self.kwargs.get("plot_properties", {}).get("scatter_size", self.config.interactive_scatter_size),
        )
        self.plot_scatter_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_plots)

        plot_scatter_transparency_value = makeStaticText(panel, "Marker transparency:")
        self.plot_scatter_transparency_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=1,
            inc=0.25,
            size=(50, -1),
            value=str(
                self.kwargs.get("plot_properties", {}).get(
                    "scatter_transparency", self.config.interactive_scatter_alpha
                )
            ),
            initial=self.kwargs.get("plot_properties", {}).get(
                "scatter_transparency", self.config.interactive_scatter_alpha
            ),
        )
        self.plot_scatter_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_plots)

        plot_scatter_line_width_value = makeStaticText(panel, "Edge width:")
        self.plot_scatter_line_width_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=5,
            inc=0.25,
            size=(50, -1),
            value=str(
                self.kwargs.get("plot_properties", {}).get(
                    "scatter_line_width", self.config.interactive_scatter_lineWidth
                )
            ),
            initial=self.kwargs.get("plot_properties", {}).get(
                "scatter_line_width", self.config.interactive_scatter_lineWidth
            ),
        )
        self.plot_scatter_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_plots)

        plot_scatter_marker_edge_sameAsFill = makeStaticText(panel, "Edge same as fill:")
        self.plot_scatter_marker_edge_sameAsFill = makeCheckbox(panel, "")
        self.plot_scatter_marker_edge_sameAsFill.SetValue(
            self.kwargs.get("plot_properties", {}).get(
                "scatter_edge_color_sameAsFill", self.config.interactive_scatter_sameAsFill
            )
        )
        self.plot_scatter_marker_edge_sameAsFill.Bind(wx.EVT_CHECKBOX, self.on_apply_plots)

        plot_scatter_marker_edge_colorBtn = makeStaticText(panel, "Edge color:")
        self.plot_scatter_marker_edge_colorBtn = wx.Button(
            panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="plot_scatter_edge_color"
        )
        self.plot_scatter_marker_edge_colorBtn.SetBackgroundColour(
            convertRGB1to255(
                self.kwargs.get("plot_properties", {}).get(
                    "scatter_edge_color", self.config.interactive_scatter_edge_color
                )
            )
        )
        self.plot_scatter_marker_edge_colorBtn.Bind(wx.EVT_BUTTON, self.on_apply_color)

        staticBox = makeStaticBox(panel, "Scatter parameters", size=(-1, -1), color=wx.BLACK)
        staticBox.SetSize((-1, -1))
        grid_box_sizer = wx.StaticBoxSizer(staticBox, wx.HORIZONTAL)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(plot_scatter_shape_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_scatter_shape_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(plot_scatter_size_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_scatter_size_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_scatter_transparency_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_scatter_transparency_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_scatter_line_width_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_scatter_line_width_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_scatter_marker_edge_sameAsFill, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_scatter_marker_edge_sameAsFill, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_scatter_marker_edge_colorBtn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_scatter_marker_edge_colorBtn, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)

        grid_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return grid_box_sizer

    def makePlotPanel_bar(self, panel):

        plot_bar_width_value = makeStaticText(panel, "Bar width:")
        self.plot_bar_width_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0.01,
            max=10,
            inc=0.25,
            size=(50, -1),
            value=str(self.kwargs.get("plot_properties", {}).get("bar_width", self.config.interactive_bar_width)),
            initial=self.kwargs.get("plot_properties", {}).get("bar_width", self.config.interactive_bar_width),
        )
        self.plot_bar_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_plots)

        plot_bar_transparency_value = makeStaticText(panel, "Bar transparency:")
        self.plot_bar_transparency_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=1,
            inc=0.25,
            size=(50, -1),
            value=str(
                self.kwargs.get("plot_properties", {}).get("bar_transparency", self.config.interactive_bar_alpha)
            ),
            initial=self.kwargs.get("plot_properties", {}).get("bar_transparency", self.config.interactive_bar_alpha),
        )
        self.plot_bar_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_plots)

        plot_bar_line_width_value = makeStaticText(panel, "Edge width:")
        self.plot_bar_line_width_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=5,
            inc=0.25,
            size=(50, -1),
            value=str(
                self.kwargs.get("plot_properties", {}).get("bar_line_width", self.config.interactive_bar_lineWidth)
            ),
            initial=self.kwargs.get("plot_properties", {}).get("bar_line_width", self.config.interactive_bar_lineWidth),
        )
        self.plot_bar_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_plots)

        plot_bar_edge_sameAsFill = makeStaticText(panel, "Edge same as fill:")
        self.plot_bar_edge_sameAsFill = makeCheckbox(panel, "")
        self.plot_bar_edge_sameAsFill.SetValue(
            self.kwargs.get("plot_properties", {}).get(
                "bar_edge_color_sameAsFill", self.config.interactive_bar_sameAsFill
            )
        )
        self.plot_bar_edge_sameAsFill.Bind(wx.EVT_CHECKBOX, self.on_apply_plots)

        plot_bar_edge_colorBtn = makeStaticText(panel, "Edge color:")
        self.plot_bar_edge_colorBtn = wx.Button(panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="plot_bar_edge_color")
        self.plot_bar_edge_colorBtn.SetBackgroundColour(
            convertRGB1to255(
                self.kwargs.get("plot_properties", {}).get("bar_edge_color", self.config.interactive_bar_edge_color)
            )
        )
        self.plot_bar_edge_colorBtn.Bind(wx.EVT_BUTTON, self.on_apply_color)

        staticBox = makeStaticBox(panel, "Bar parameters", size=(-1, -1), color=wx.BLACK)
        staticBox.SetSize((-1, -1))
        grid_box_sizer = wx.StaticBoxSizer(staticBox, wx.HORIZONTAL)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(plot_bar_width_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_bar_width_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(plot_bar_transparency_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_bar_transparency_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_bar_line_width_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_bar_line_width_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_bar_edge_sameAsFill, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_bar_edge_sameAsFill, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_bar_edge_colorBtn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_bar_edge_colorBtn, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)

        grid_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return grid_box_sizer

    def makePlotPanel_plot1D(self, panel):

        plot_line_width_label = makeStaticText(panel, "Line width:")
        self.plot_line_width_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=5,
            inc=0.5,
            size=(50, -1),
            value=str(self.kwargs.get("plot_properties", {}).get("line_width", self.config.interactive_line_width)),
            initial=self.kwargs.get("plot_properties", {}).get("line_width", self.config.interactive_line_width),
        )
        self.plot_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_plots)

        plot_line_transparency_label = makeStaticText(panel, "Line transparency:")
        self.plot_line_transparency_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=1,
            inc=0.25,
            size=(50, -1),
            value=str(
                self.kwargs.get("plot_properties", {}).get("line_transparency", self.config.interactive_line_alpha)
            ),
            initial=self.kwargs.get("plot_properties", {}).get("line_transparency", self.config.interactive_line_alpha),
        )
        self.plot_line_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_plots)

        plot_line_style_label = makeStaticText(panel, "Line style:")
        self.plot_line_style_choice = wx.ComboBox(
            panel,
            -1,
            choices=self.config.interactive_line_style_choices,
            value=self.kwargs.get("plot_properties", {}).get("line_style", self.config.interactive_line_style),
            style=wx.CB_READONLY,
        )
        self.plot_line_style_choice.Bind(wx.EVT_COMBOBOX, self.on_apply_plots)

        plot_line_color_label = makeStaticText(panel, "Line color:")
        self.plot_line_color_colorBtn = wx.Button(panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="plot_line_color")
        self.plot_line_color_colorBtn.SetBackgroundColour(
            convertRGB1to255(
                self.kwargs.get("plot_properties", {}).get("line_color", self.config.interactive_line_color)
            )
        )
        self.plot_line_color_colorBtn.Bind(wx.EVT_BUTTON, self.on_apply_color)

        plot_fill_under_label = makeStaticText(panel, "Shade under line:")
        self.plot_line_shade_under = makeCheckbox(panel, "")
        self.plot_line_shade_under.SetValue(
            self.kwargs.get("plot_properties", {}).get("line_shade_under", self.config.interactive_line_shade_under)
        )
        self.plot_line_shade_under.Bind(wx.EVT_CHECKBOX, self.on_apply_plots)

        plot_shade_transparency_label = makeStaticText(panel, "Shade transparency:")
        self.plot_shade_transparency_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=1,
            inc=0.25,
            size=(50, -1),
            value=str(
                self.kwargs.get("plot_properties", {}).get(
                    "shade_transparency", self.config.interactive_line_shade_alpha
                )
            ),
            initial=self.kwargs.get("plot_properties", {}).get(
                "shade_transparency", self.config.interactive_line_shade_alpha
            ),
        )
        self.plot_shade_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_plots)

        plot_hover_linkX_label = makeStaticText(panel, "Hover linked to X-axis:")
        self.plot_line_linkX = makeCheckbox(panel, "")
        self.plot_line_linkX.SetValue(
            self.kwargs.get("plot_properties", {}).get("hover_link_x", self.config.linkXYaxes)
        )
        self.plot_line_linkX.Bind(wx.EVT_CHECKBOX, self.on_apply_plots)
        self.plot_line_linkX.SetToolTip(
            wx.ToolTip("Hover linked to the x-axis values. Can *significantly* slow plots with many data points!")
        )

        staticBox = makeStaticBox(panel, "Line plot parameters", size=(-1, -1), color=wx.BLACK)
        staticBox.SetSize((-1, -1))
        grid_box_sizer = wx.StaticBoxSizer(staticBox, wx.HORIZONTAL)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(plot_line_width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_line_width_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_line_transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_line_transparency_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_line_style_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_line_style_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(plot_line_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_line_color_colorBtn, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_fill_under_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_line_shade_under, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_shade_transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_shade_transparency_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_hover_linkX_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_line_linkX, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return grid_box_sizer

    def makePlotPanel_waterfall(self, panel):

        multiline_yaxis_increment_label = makeStaticText(panel, "Y-axis increment:")
        self.waterfall_yaxis_increment_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            inc=0.25,
            min=0,
            max=10,
            size=(50, -1),
            value=str(
                self.kwargs.get("plot_properties", {}).get(
                    "waterfall_increment", self.config.interactive_waterfall_increment
                )
            ),
            initial=self.kwargs.get("plot_properties", {}).get(
                "waterfall_increment", self.config.interactive_waterfall_increment
            ),
        )
        self.waterfall_yaxis_increment_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_plots)

        multiline_shade_under_label = makeStaticText(panel, "Shade under line:")
        self.waterfall_shade_under_value = makeCheckbox(panel, "")
        self.waterfall_shade_under_value.SetValue(
            self.kwargs.get("plot_properties", {}).get(
                "waterfall_shade_under", self.config.interactive_waterfall_shade_under
            )
        )
        self.waterfall_shade_under_value.Bind(wx.EVT_CHECKBOX, self.on_apply_plots)

        multiline_shade_transparency_label = makeStaticText(panel, "Shade transparency:")
        self.waterfall_shade_transparency_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            inc=0.25,
            min=0,
            max=1,
            size=(50, -1),
            value=str(
                self.kwargs.get("plot_properties", {}).get(
                    "waterfall_shade_transparency", self.config.interactive_waterfall_shade_alpha
                )
            ),
            initial=self.kwargs.get("plot_properties", {}).get(
                "waterfall_shade_transparency", self.config.interactive_waterfall_shade_alpha
            ),
        )
        self.waterfall_shade_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_plots)

        grid_staticBox = makeStaticBox(panel, "Waterfall parameters", size=(-1, -1), color=wx.BLACK)
        grid_staticBox.SetSize((-1, -1))
        grid_box_sizer = wx.StaticBoxSizer(grid_staticBox, wx.HORIZONTAL)
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(multiline_yaxis_increment_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.waterfall_yaxis_increment_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(multiline_shade_under_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.waterfall_shade_under_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(multiline_shade_transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.waterfall_shade_transparency_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return grid_box_sizer

    def makePlotPanel_plot2D(self, panel):

        colormap_label = makeStaticText(panel, "Colormap:")
        self.plot_colormap_choice = wx.ComboBox(
            panel,
            -1,
            choices=self.config.cmaps2,
            value=self.kwargs.get("plot_properties", {}).get("colormap", self.config.currentCmap),
            style=wx.CB_READONLY,
        )
        self.plot_colormap_choice.Bind(wx.EVT_COMBOBOX, self.on_apply_plots)

        staticBox = makeStaticBox(panel, "Heatmap parameters", size=(-1, -1), color=wx.BLACK)
        staticBox.SetSize((-1, -1))
        grid_box_sizer = wx.StaticBoxSizer(staticBox, wx.HORIZONTAL)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(colormap_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_colormap_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return grid_box_sizer

    def makePlotPanel_tandem(self, panel):

        plot_tandem_line_width_value = makeStaticText(panel, "Line width:")
        self.plot_tandem_line_width_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0.0,
            max=100,
            inc=0.5,
            size=(50, -1),
            value=str(self.kwargs.get("plot_properties", {}).get("tandem_line_width", 1.0)),
            initial=self.kwargs.get("plot_properties", {}).get("tandem_line_width", 1.0),
        )
        self.plot_tandem_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_plots)

        plot_tandem_line_unlabelled_colorBtn = makeStaticText(panel, "Line color (unlabelled):")
        self.plot_tandem_line_unlabelled_colorBtn = wx.Button(
            panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="plot_tandem_unlabelled"
        )
        self.plot_tandem_line_unlabelled_colorBtn.SetBackgroundColour(
            convertRGB1to255(
                self.kwargs.get("plot_properties", {}).get("tandem_line_color_unlabelled", (0.0, 0.0, 0.0))
            )
        )
        self.plot_tandem_line_unlabelled_colorBtn.Bind(wx.EVT_BUTTON, self.on_apply_color)

        plot_tandem_line_labelled_colorBtn = makeStaticText(panel, "Line color (labelled):")
        self.plot_tandem_line_labelled_colorBtn = wx.Button(
            panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="plot_tandem_labelled"
        )
        self.plot_tandem_line_labelled_colorBtn.SetBackgroundColour(
            convertRGB1to255(self.kwargs.get("plot_properties", {}).get("tandem_line_color_labelled", (1.0, 0.0, 0.0)))
        )
        self.plot_tandem_line_labelled_colorBtn.Bind(wx.EVT_BUTTON, self.on_apply_color)

        staticBox = makeStaticBox(panel, "TAndem MS/MS parameters", size=(-1, -1), color=wx.BLACK)
        staticBox.SetSize((-1, -1))
        grid_box_sizer = wx.StaticBoxSizer(staticBox, wx.HORIZONTAL)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(plot_tandem_line_width_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_tandem_line_width_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(plot_tandem_line_unlabelled_colorBtn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_tandem_line_unlabelled_colorBtn, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_tandem_line_labelled_colorBtn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.plot_tandem_line_labelled_colorBtn, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)

        grid_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return grid_box_sizer

    def makePlotPanel(self, panel):

        plot1D_box_sizer = self.makePlotPanel_plot1D(panel)
        plot2D_box_sizer = self.makePlotPanel_plot2D(panel)
        waterfall_box_sizer = self.makePlotPanel_waterfall(panel)
        scatter_box_sizer = self.makePlotPanel_scatter(panel)
        bar_box_sizer = self.makePlotPanel_bar(panel)
        tandem_box_sizer = self.makePlotPanel_tandem(panel)

        # Add to grid sizer
        sizer_left = wx.BoxSizer(wx.VERTICAL)
        sizer_left.Add(plot1D_box_sizer, 0, wx.EXPAND, 0)
        sizer_left.Add(plot2D_box_sizer, 0, wx.EXPAND, 0)
        sizer_left.Add(waterfall_box_sizer, 0, wx.EXPAND, 0)
        sizer_left.Add(tandem_box_sizer, 0, wx.EXPAND, 0)

        sizer_right = wx.BoxSizer(wx.VERTICAL)
        sizer_right.Add(scatter_box_sizer, 0, wx.EXPAND, 0)
        sizer_right.Add(bar_box_sizer, 0, wx.EXPAND, 0)

        # pack elements
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(sizer_left, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        main_sizer.Add(sizer_right, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def makePreprocessingPanel(self, panel):

        preprocess_linearize = makeStaticText(panel, "Linearize:")
        self.preprocess_linearize_check = makeCheckbox(panel, "")
        self.preprocess_linearize_check.SetValue(
            self.kwargs.get("preprocessing_properties", {}).get("linearize", self.config.interactive_ms_linearize)
        )
        self.preprocess_linearize_check.Bind(wx.EVT_CHECKBOX, self.on_apply_preprocess)

        preprocess_linearize_binsize_label = makeStaticText(panel, "Bin size:")
        self.preprocess_linearize_binsize_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0.005,
            max=5,
            inc=0.1,
            size=(75, -1),
            value=str(
                self.kwargs.get("preprocessing_properties", {}).get(
                    "linearize_binsize", self.config.interactive_ms_binSize
                )
            ),
            initial=self.kwargs.get("preprocessing_properties", {}).get(
                "linearize_binsize", self.config.interactive_ms_binSize
            ),
        )
        self.preprocess_linearize_binsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_preprocess)

        preprocess_linearize_limit_label = makeStaticText(panel, "Minimun size:")
        self.preprocess_linearize_limit_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=500,
            max=100000,
            inc=5000,
            size=(75, -1),
            value=str(self.kwargs.get("preprocessing_properties", {}).get("linearize_limit", 25000)),
            initial=self.kwargs.get("preprocessing_properties", {}).get("linearize_limit", 25000),
        )
        self.preprocess_linearize_limit_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_preprocess)

        staticBox = makeStaticBox(panel, "Line parameters", size=(-1, -1), color=wx.BLACK)
        staticBox.SetSize((-1, -1))
        grid_box_sizer = wx.StaticBoxSizer(staticBox, wx.HORIZONTAL)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(preprocess_linearize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.preprocess_linearize_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(preprocess_linearize_binsize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.preprocess_linearize_binsize_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(preprocess_linearize_limit_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.preprocess_linearize_limit_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        preprocess_subsample = makeStaticText(panel, "Subsample:")
        self.preprocess_subsample_check = makeCheckbox(panel, "")
        self.preprocess_subsample_check.SetValue(self.kwargs.get("preprocessing_properties", {}).get("subsample", True))
        self.preprocess_subsample_check.Bind(wx.EVT_CHECKBOX, self.on_apply_preprocess)

        preprocess_subsample_frequency_label = makeStaticText(panel, "Frequency:")
        self.preprocess_subsample_frequency_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=5,
            max=100,
            inc=5,
            size=(75, -1),
            value=str(self.kwargs.get("preprocessing_properties", {}).get("subsample_frequency", 20)),
            initial=self.kwargs.get("preprocessing_properties", {}).get("subsample_frequency", 20),
        )
        self.preprocess_subsample_frequency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_preprocess)

        preprocess_subsample_limit_label = makeStaticText(panel, "Minimun size:")
        self.preprocess_subsample_limit_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=500,
            max=100000,
            inc=5000,
            size=(75, -1),
            value=str(self.kwargs.get("preprocessing_properties", {}).get("subsample_limit", 20000)),
            initial=self.kwargs.get("preprocessing_properties", {}).get("subsample_limit", 20000),
        )
        self.preprocess_subsample_limit_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_preprocess)

        staticBox = makeStaticBox(panel, "Heatmap parameters", size=(-1, -1), color=wx.BLACK)
        staticBox.SetSize((-1, -1))
        heatmap_box_sizer = wx.StaticBoxSizer(staticBox, wx.HORIZONTAL)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(preprocess_subsample, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.preprocess_subsample_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(preprocess_subsample_frequency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.preprocess_subsample_frequency_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(preprocess_subsample_limit_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.preprocess_subsample_limit_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        heatmap_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(grid_box_sizer, wx.ALIGN_CENTER_HORIZONTAL, 2)
        main_sizer.Add(heatmap_box_sizer, wx.ALIGN_CENTER_HORIZONTAL, 2)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def makeOverlayPanel_grid(self, panel):

        grid_add_labels_label = makeStaticText(panel, "Add labels:")
        self.overlay_grid_show_labels = makeCheckbox(panel, "")
        self.overlay_grid_show_labels.SetValue(
            self.kwargs.get("overlay_properties", {}).get("overlay_grid_add_labels", False)
        )
        self.overlay_grid_show_labels.Bind(wx.EVT_CHECKBOX, self.on_apply_overlay)

        annotation_fontSize_label = makeStaticText(panel, "Font size:")
        self.overlay_grid_fontSize_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=32,
            inc=2,
            size=(50, -1),
            value=str(
                self.kwargs.get("overlay_properties", {}).get(
                    "grid_label_fontsize", self.config.interactive_grid_label_size
                )
            ),
            initial=self.kwargs.get("overlay_properties", {}).get(
                "grid_label_fontsize", self.config.interactive_grid_label_size
            ),
        )
        self.overlay_grid_fontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        self.overlay_grid_fontWeight_value = makeCheckbox(panel, "bold")
        self.overlay_grid_fontWeight_value.SetValue(
            self.kwargs.get("overlay_properties", {}).get(
                "grid_label_fontweight", self.config.interactive_grid_label_weight
            )
        )
        self.overlay_grid_fontWeight_value.Bind(wx.EVT_CHECKBOX, self.on_apply_overlay)

        annotation_fontColor_label = makeStaticText(panel, "Font color:")
        self.overlay_grid_label_colorBtn = wx.Button(
            panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="overlay_grid_label_color"
        )
        self.overlay_grid_label_colorBtn.SetBackgroundColour(
            convertRGB1to255(
                self.kwargs.get("overlay_properties", {}).get(
                    "grid_label_color", self.config.interactive_annotation_color
                )
            )
        )
        self.overlay_grid_label_colorBtn.Bind(wx.EVT_BUTTON, self.on_apply_color)

        annotation_xpos_label = makeStaticText(panel, "Position offset X:")
        self.overlay_grid_xpos_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            inc=5,
            min=-100,
            max=100,
            size=(50, -1),
            value=str(
                self.kwargs.get("overlay_properties", {}).get(
                    "grid_position_offset_x", self.config.interactive_ms_annotations_offsetX
                )
            ),
            initial=self.kwargs.get("overlay_properties", {}).get(
                "grid_position_offset_x", self.config.interactive_ms_annotations_offsetX
            ),
        )
        self.overlay_grid_xpos_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        annotation_ypos_label = makeStaticText(panel, "Position offset Y:")
        self.overlay_grid_ypos_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=-100,
            max=100,
            inc=5,
            size=(50, -1),
            value=str(
                self.kwargs.get("overlay_properties", {}).get(
                    "grid_position_offset_y", self.config.interactive_ms_annotations_offsetY
                )
            ),
            initial=self.kwargs.get("overlay_properties", {}).get(
                "grid_position_offset_y", self.config.interactive_ms_annotations_offsetY
            ),
        )
        self.overlay_grid_ypos_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        grid_staticBox = makeStaticBox(panel, "Grid (NxN) parameters", size=(-1, -1), color=wx.BLACK)
        grid_staticBox.SetSize((-1, -1))
        grid_box_sizer = wx.StaticBoxSizer(grid_staticBox, wx.HORIZONTAL)
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(grid_add_labels_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.overlay_grid_show_labels, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(annotation_fontSize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.overlay_grid_fontSize_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_grid_fontWeight_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(annotation_fontColor_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.overlay_grid_label_colorBtn, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(annotation_xpos_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.overlay_grid_xpos_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(annotation_ypos_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.overlay_grid_ypos_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return grid_box_sizer

    def makeOverlayPanel_overlay(self, panel):

        overlay_layout_label = makeStaticText(panel, "Layout:")
        self.overlay_layout = wx.ComboBox(
            panel,
            -1,
            style=wx.CB_READONLY,
            choices=["Rows", "Columns"],
            value=self.kwargs.get("overlay_properties", {}).get("overlay_layout", self.config.plotLayoutOverlay),
        )
        self.overlay_layout.Bind(wx.EVT_COMBOBOX, self.on_apply_overlay)
        self.overlay_layout.SetToolTip(
            wx.ToolTip(
                "Layout to be used when creating mask/transparent plot. "
                + "Currently, actual overlaying of two heatmaps is not possible"
            )
        )

        overlay_linkXY_label = makeStaticText(panel, "Link XY axes:")
        self.overlay_linkXY = makeCheckbox(panel, "")
        self.overlay_linkXY.SetValue(
            self.kwargs.get("overlay_properties", {}).get("overlay_link_xy", self.config.linkXYaxes)
        )
        self.overlay_linkXY.Bind(wx.EVT_CHECKBOX, self.on_apply_overlay)
        self.overlay_linkXY.SetToolTip(wx.ToolTip("Hover response when zooming/panning"))

        overlay_colormap_1_label = makeStaticText(panel, "Colormap (1):")
        self.overlay_colormap_1 = wx.ComboBox(
            panel,
            -1,
            style=wx.CB_READONLY,
            choices=self.config.cmaps2,
            value=self.kwargs.get("overlay_properties", {}).get("overlay_colormap_1", "Reds"),
        )
        self.overlay_colormap_1.Bind(wx.EVT_COMBOBOX, self.on_apply_overlay)

        overlay_colormap_2_label = makeStaticText(panel, "Colormap (2):")
        self.overlay_colormap_2 = wx.ComboBox(
            panel,
            -1,
            style=wx.CB_READONLY,
            choices=self.config.cmaps2,
            value=self.kwargs.get("overlay_properties", {}).get("overlay_colormap_2", "Blues"),
        )
        self.overlay_colormap_2.Bind(wx.EVT_COMBOBOX, self.on_apply_overlay)

        overlay_merge_tools_label = makeStaticText(panel, "Merge tools:")
        self.overlay_merge_tools = makeCheckbox(panel, "")
        self.overlay_merge_tools.SetValue(self.kwargs.get("overlay_properties", {}).get("overlay_merge_tools", False))
        self.overlay_merge_tools.Bind(wx.EVT_CHECKBOX, self.on_apply_overlay)
        self.overlay_merge_tools.SetToolTip(
            wx.ToolTip("Merge tools for both plots. If checked, a lot of the tools will be removed by default.")
        )

        overlay_staticBox = makeStaticBox(panel, "Mask/Transparency parameters", size=(-1, -1), color=wx.BLACK)
        overlay_staticBox.SetSize((-1, -1))
        overlay_box_sizer = wx.StaticBoxSizer(overlay_staticBox, wx.HORIZONTAL)
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(overlay_layout_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.overlay_layout, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(overlay_linkXY_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.overlay_linkXY, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(overlay_colormap_1_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.overlay_colormap_1, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(overlay_colormap_2_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.overlay_colormap_2, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(overlay_merge_tools_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.overlay_merge_tools, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        overlay_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return overlay_box_sizer

    def makeOverlayPanel_rmsd(self, panel):
        rmsd_label_fontsize = makeStaticText(panel, "Label font size:")
        self.rmsd_label_fontsize = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=32,
            inc=2,
            size=(50, -1),
            value=str(
                self.kwargs.get("overlay_properties", {}).get(
                    "rmsd_label_fontsize", self.config.interactive_annotation_fontSize
                )
            ),
            initial=self.kwargs.get("overlay_properties", {}).get(
                "rmsd_label_fontsize", self.config.interactive_annotation_fontSize
            ),
        )
        self.rmsd_label_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        self.rmsd_label_fontweight = makeCheckbox(panel, "bold")
        self.rmsd_label_fontweight.SetValue(
            self.kwargs.get("overlay_properties", {}).get(
                "rmsd_label_fontweight", self.config.interactive_annotation_weight
            )
        )
        self.rmsd_label_fontweight.Bind(wx.EVT_CHECKBOX, self.on_apply_overlay)

        rmsd_label_transparency_label = makeStaticText(panel, "Background transparency:")
        self.rmsd_label_transparency = wx.SpinCtrlDouble(
            panel,
            min=0,
            max=1,
            inc=0.25,
            size=(50, -1),
            value=str(
                self.kwargs.get("overlay_properties", {}).get(
                    "rmsd_background_transparency", self.config.interactive_annotation_alpha
                )
            ),
            initial=self.kwargs.get("overlay_properties", {}).get(
                "rmsd_background_transparency", self.config.interactive_annotation_alpha
            ),
        )
        self.rmsd_label_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        rmsd_label_color_label = makeStaticText(panel, "Label color:")
        self.rmsd_label_colorBtn = wx.Button(panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="rmsd_label_color")
        self.rmsd_label_colorBtn.SetBackgroundColour(
            convertRGB1to255(
                self.kwargs.get("overlay_properties", {}).get(
                    "rmsd_label_color", self.config.interactive_annotation_color
                )
            )
        )
        self.rmsd_label_colorBtn.Bind(wx.EVT_BUTTON, self.on_apply_color)

        rmsd_background_color_label = makeStaticText(panel, "Background color:")
        self.rmsd_background_colorBtn = wx.Button(
            panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="rmsd_background_color"
        )
        self.rmsd_background_colorBtn.SetBackgroundColour(
            convertRGB1to255(
                self.kwargs.get("overlay_properties", {}).get(
                    "rmsd_background_color", self.config.interactive_annotation_background_color
                )
            )
        )
        self.rmsd_background_colorBtn.Bind(wx.EVT_BUTTON, self.on_apply_color)

        rmsd_staticBox = makeStaticBox(panel, "RMSD parameters", size=(-1, -1), color=wx.BLACK)
        rmsd_staticBox.SetSize((-1, -1))
        rmsd_box_sizer = wx.StaticBoxSizer(rmsd_staticBox, wx.HORIZONTAL)
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(rmsd_label_fontsize, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_label_fontsize, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.rmsd_label_fontweight, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(rmsd_label_transparency_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_label_transparency, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(rmsd_label_color_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_label_colorBtn, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(rmsd_background_color_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_background_colorBtn, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        rmsd_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return rmsd_box_sizer

    def makeOverlayPanel_rmsd_matrix(self, panel):

        rmsd_matrix_colormap = makeStaticText(panel, "Colormap:")
        self.rmsd_matrix_colormap = wx.ComboBox(
            panel,
            -1,
            style=wx.CB_READONLY,
            choices=self.config.cmaps2,
            value=self.kwargs.get("overlay_properties", {}).get("rmsd_matrix_colormap", "coolwarm"),
        )
        self.rmsd_matrix_colormap.Bind(wx.EVT_COMBOBOX, self.on_apply_overlay)

        annotation_fontSize_label = makeStaticText(panel, "Font size:")
        self.rmsd_matrix_fontSize_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=32,
            inc=2,
            size=(50, -1),
            value=str(
                self.kwargs.get("overlay_properties", {}).get(
                    "rmsd_matrix_label_fontsize", self.config.interactive_ms_annotations_fontSize
                )
            ),
            initial=self.kwargs.get("overlay_properties", {}).get(
                "rmsd_matrix_label_fontsize", self.config.interactive_ms_annotations_fontSize
            ),
        )
        self.rmsd_matrix_fontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        self.rmsd_matrix_fontWeight_value = makeCheckbox(panel, "bold")
        self.rmsd_matrix_fontWeight_value.SetValue(
            self.kwargs.get("overlay_properties", {}).get(
                "rmsd_matrix_label_fontweight", self.config.interactive_ms_annotations_fontWeight
            )
        )
        self.rmsd_matrix_fontWeight_value.Bind(wx.EVT_CHECKBOX, self.on_apply_overlay)

        annotation_fontColor_label = makeStaticText(panel, "Font color:")
        self.rmsd_matrix_fontColor_colorBtn = wx.Button(
            panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="rmsd_matrix_label_color"
        )
        self.rmsd_matrix_fontColor_colorBtn.SetBackgroundColour(
            convertRGB1to255(
                self.kwargs.get("overlay_properties", {}).get(
                    "rmsd_matrix_label_color", self.config.interactive_ms_annotations_label_color
                )
            )
        )
        self.rmsd_matrix_fontColor_colorBtn.Bind(wx.EVT_BUTTON, self.on_apply_color)

        self.rmsd_matrix_auto_fontColor_value = makeCheckbox(panel, "Auto-determine\nlabel color")
        self.rmsd_matrix_auto_fontColor_value.SetValue(
            self.kwargs.get("overlay_properties", {}).get("rmsd_matrix_auto_label_color", False)
        )
        self.rmsd_matrix_auto_fontColor_value.Bind(wx.EVT_CHECKBOX, self.on_apply_overlay)

        annotation_xpos_label = makeStaticText(panel, "Position offset X:")
        self.rmsd_matrix_xpos_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            inc=5,
            min=-100,
            max=100,
            size=(50, -1),
            value=str(
                self.kwargs.get("overlay_properties", {}).get(
                    "rmsd_matrix_position_offset_x", self.config.interactive_ms_annotations_offsetX
                )
            ),
            initial=self.kwargs.get("overlay_properties", {}).get(
                "rmsd_matrix_position_offset_x", self.config.interactive_ms_annotations_offsetX
            ),
        )
        self.rmsd_matrix_xpos_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        annotation_ypos_label = makeStaticText(panel, "Position offset Y:")
        self.rmsd_matrix_ypos_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=-100,
            max=100,
            inc=5,
            size=(50, -1),
            value=str(
                self.kwargs.get("overlay_properties", {}).get(
                    "rmsd_matrix_position_offset_y", self.config.interactive_ms_annotations_offsetY
                )
            ),
            initial=self.kwargs.get("overlay_properties", {}).get(
                "rmsd_matrix_position_offset_y", self.config.interactive_ms_annotations_offsetY
            ),
        )
        self.rmsd_matrix_ypos_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        xaxis_rotation_label = makeStaticText(panel, "X-axis tick rotation:")
        self.rmsd_matrix_xaxis_rotation_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=180,
            inc=45,
            size=(50, -1),
            value=str(self.kwargs.get("overlay_properties", {}).get("rmsd_matrix_xaxis_rotation", 120)),
            initial=self.kwargs.get("overlay_properties", {}).get("rmsd_matrix_xaxis_rotation", 120),
        )
        self.rmsd_matrix_xaxis_rotation_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        rmsd_matrix_staticBox = makeStaticBox(panel, "RMSD Matrix parameters", size=(-1, -1), color=wx.BLACK)
        rmsd_matrix_staticBox.SetSize((-1, -1))
        rmsd_matrix_box_sizer = wx.StaticBoxSizer(rmsd_matrix_staticBox, wx.HORIZONTAL)
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(rmsd_matrix_colormap, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.rmsd_matrix_colormap, (n, 1), (1, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(annotation_fontSize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.rmsd_matrix_fontSize_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.rmsd_matrix_fontWeight_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(annotation_fontColor_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.rmsd_matrix_fontColor_colorBtn, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.rmsd_matrix_auto_fontColor_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(annotation_xpos_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.rmsd_matrix_xpos_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(annotation_ypos_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.rmsd_matrix_ypos_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(xaxis_rotation_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.rmsd_matrix_xaxis_rotation_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        rmsd_matrix_box_sizer.Add(grid, 0, wx.EXPAND, 10)
        return rmsd_matrix_box_sizer

    def makeOverlayPanel_multiline(self, panel):

        multiline_shade_under_label = makeStaticText(panel, "Shade under line:")
        self.multiline_shade_under_value = makeCheckbox(panel, "")
        self.multiline_shade_under_value.SetValue(
            self.kwargs.get("overlay_properties", {}).get("multiline_shade_under", False)
        )
        self.multiline_shade_under_value.Bind(wx.EVT_CHECKBOX, self.on_apply_overlay)

        multiline_shade_transparency_label = makeStaticText(panel, "Shade transparency:")
        self.multiline_shade_transparency_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            inc=0.25,
            min=0,
            max=1,
            size=(50, -1),
            value=str(self.kwargs.get("overlay_properties", {}).get("multiline_shade_transparency", 0.25)),
            initial=self.kwargs.get("overlay_properties", {}).get("multiline_shade_transparency", 0.25),
        )
        self.multiline_shade_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        grid_staticBox = makeStaticBox(panel, "Multi-line parameters", size=(-1, -1), color=wx.BLACK)
        grid_staticBox.SetSize((-1, -1))
        grid_box_sizer = wx.StaticBoxSizer(grid_staticBox, wx.HORIZONTAL)
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(multiline_shade_under_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.multiline_shade_under_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(multiline_shade_transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.multiline_shade_transparency_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return grid_box_sizer

    def makeOverlayPanel_rmsf(self, panel):

        plot_line_width_label = makeStaticText(panel, "Line width:")
        self.rmsf_line_width_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=5,
            inc=0.5,
            size=(50, -1),
            value=str(
                self.kwargs.get("overlay_properties", {}).get("rmsf_line_width", self.config.interactive_line_width)
            ),
            initial=self.kwargs.get("overlay_properties", {}).get(
                "rmsf_line_width", self.config.interactive_line_width
            ),
        )
        self.rmsf_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        plot_line_transparency_label = makeStaticText(panel, "Line transparency:")
        self.rmsf_line_transparency_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=1,
            inc=0.25,
            size=(50, -1),
            value=str(
                self.kwargs.get("overlay_properties", {}).get(
                    "rmsf_line_transparency", self.config.interactive_line_alpha
                )
            ),
            initial=self.kwargs.get("overlay_properties", {}).get(
                "rmsf_line_transparency", self.config.interactive_line_alpha
            ),
        )
        self.rmsf_line_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        plot_line_style_label = makeStaticText(panel, "Line style:")
        self.rmsf_line_style_choice = wx.ComboBox(
            panel,
            -1,
            choices=self.config.interactive_line_style_choices,
            value=self.kwargs.get("overlay_properties", {}).get("rmsf_line_style", self.config.interactive_line_style),
            style=wx.CB_READONLY,
        )
        self.rmsf_line_style_choice.Bind(wx.EVT_COMBOBOX, self.on_apply_overlay)

        plot_line_color_label = makeStaticText(panel, "Line color:")
        self.rmsf_line_color_colorBtn = wx.Button(panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="rmsf_line_color")
        self.rmsf_line_color_colorBtn.SetBackgroundColour(
            convertRGB1to255(self.kwargs.get("overlay_properties", {}).get("rmsf_line_color", (0.0, 0.0, 0.0)))
        )
        self.rmsf_line_color_colorBtn.Bind(wx.EVT_BUTTON, self.on_apply_color)

        plot_fill_under_label = makeStaticText(panel, "Shade under line:")
        self.rmsf_line_shade_under = makeCheckbox(panel, "")
        self.rmsf_line_shade_under.SetValue(
            self.kwargs.get("overlay_properties", {}).get("rmsf_line_shade_under", False)
        )
        self.rmsf_line_shade_under.Bind(wx.EVT_CHECKBOX, self.on_apply_overlay)

        plot_shade_transparency_label = makeStaticText(panel, "Shade transparency:")
        self.rmsf_shade_transparency_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=1,
            inc=0.25,
            size=(50, -1),
            value=str(
                self.kwargs.get("overlay_properties", {}).get(
                    "rmsf_shade_transparency", self.config.interactive_line_alpha
                )
            ),
            initial=self.kwargs.get("overlay_properties", {}).get(
                "rmsf_shade_transparency", self.config.interactive_line_alpha
            ),
        )
        self.rmsf_shade_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        staticBox = makeStaticBox(panel, "RMSF parameters", size=(-1, -1), color=wx.BLACK)
        staticBox.SetSize((-1, -1))
        grid_box_sizer = wx.StaticBoxSizer(staticBox, wx.HORIZONTAL)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(plot_line_width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.rmsf_line_width_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_line_transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.rmsf_line_transparency_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_line_style_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.rmsf_line_style_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(plot_line_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.rmsf_line_color_colorBtn, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_fill_under_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.rmsf_line_shade_under, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(plot_shade_transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.rmsf_shade_transparency_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return grid_box_sizer

    def makeOverlayPanel(self, panel):

        overlay_box_sizer = self.makeOverlayPanel_overlay(panel)
        grid_box_sizer = self.makeOverlayPanel_grid(panel)
        rmsd_box_sizer = self.makeOverlayPanel_rmsd(panel)
        rmsd_matrix_box_sizer = self.makeOverlayPanel_rmsd_matrix(panel)
        multiline_box_sizer = self.makeOverlayPanel_multiline(panel)
        rmsf_box_sizer = self.makeOverlayPanel_rmsf(panel)

        # Add to grid sizer
        sizer_left = wx.BoxSizer(wx.VERTICAL)
        sizer_left.Add(overlay_box_sizer, 0, wx.EXPAND, 0)
        sizer_left.Add(rmsd_box_sizer, 0, wx.EXPAND, 0)
        sizer_left.Add(rmsd_matrix_box_sizer, 0, wx.EXPAND, 0)

        sizer_right = wx.BoxSizer(wx.VERTICAL)
        sizer_right.Add(grid_box_sizer, 0, wx.EXPAND, 0)
        sizer_right.Add(rmsf_box_sizer, 0, wx.EXPAND, 0)
        sizer_right.Add(multiline_box_sizer, 0, wx.EXPAND, 0)

        # pack elements
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(sizer_left, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        main_sizer.Add(sizer_right, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def makeAnnotationsPanel(self, panel):

        annotation_show_annotations_label = makeStaticText(panel, "Show annotations:")
        self.annotation_showAnnotations = wx.CheckBox(panel, -1, "", (15, 30))
        self.annotation_showAnnotations.SetValue(
            self.kwargs.get("annotation_properties", {}).get("show_annotations", True)
        )
        self.annotation_showAnnotations.Bind(wx.EVT_CHECKBOX, self.on_apply_annotation)
        self.annotation_showAnnotations.SetToolTip(wx.ToolTip("Show annotations in exported plot - when available"))

        annotation_annotate_peak_label = makeStaticText(panel, "Add label to peaks:")
        self.annotation_peakLabel = wx.CheckBox(panel, -1, "", (15, 30))
        self.annotation_peakLabel.SetValue(
            self.kwargs.get("annotation_properties", {}).get(
                "show_labels", self.config.interactive_ms_annotations_labels
            )
        )
        self.annotation_peakLabel.Bind(wx.EVT_CHECKBOX, self.on_apply_annotation)
        self.annotation_peakLabel.SetToolTip(wx.ToolTip("A pre-defined (by you) label will be added to selected peaks"))

        annotation_xpos_label = makeStaticText(panel, "Position offset X:")
        self.annotation_xpos_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            inc=5,
            min=-100,
            max=100,
            size=(50, -1),
            value=str(
                self.kwargs.get("annotation_properties", {}).get(
                    "position_offset_x", self.config.interactive_ms_annotations_offsetX
                )
            ),
            initial=self.kwargs.get("annotation_properties", {}).get(
                "position_offset_x", self.config.interactive_ms_annotations_offsetX
            ),
        )
        self.annotation_xpos_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_annotation)

        annotation_ypos_label = makeStaticText(panel, "Position offset Y:")
        self.annotation_ypos_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=-100,
            max=100,
            inc=5,
            size=(50, -1),
            value=str(
                self.kwargs.get("annotation_properties", {}).get(
                    "position_offset_y", self.config.interactive_ms_annotations_offsetY
                )
            ),
            initial=self.kwargs.get("annotation_properties", {}).get(
                "position_offset_y", self.config.interactive_ms_annotations_offsetY
            ),
        )
        self.annotation_ypos_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_annotation)

        annotation_rotation_label = makeStaticText(panel, "Label rotation:")
        self.annotation_rotation_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=180,
            inc=45,
            size=(50, -1),
            value=str(
                self.kwargs.get("annotation_properties", {}).get(
                    "label_rotation", self.config.interactive_ms_annotations_rotation
                )
            ),
            initial=self.kwargs.get("annotation_properties", {}).get(
                "label_rotation", self.config.interactive_ms_annotations_rotation
            ),
        )
        self.annotation_rotation_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_annotation)

        annotation_fontSize_label = makeStaticText(panel, "Font size:")
        self.annotation_fontSize_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=32,
            inc=2,
            size=(50, -1),
            value=str(
                self.kwargs.get("annotation_properties", {}).get(
                    "label_fontsize", self.config.interactive_ms_annotations_fontSize
                )
            ),
            initial=self.kwargs.get("annotation_properties", {}).get(
                "label_fontsize", self.config.interactive_ms_annotations_fontSize
            ),
        )
        self.annotation_fontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_annotation)

        self.annotation_fontWeight_value = makeCheckbox(panel, "bold")
        self.annotation_fontWeight_value.SetValue(
            self.kwargs.get("annotation_properties", {}).get(
                "label_fontweight", self.config.interactive_ms_annotations_fontWeight
            )
        )
        self.annotation_fontWeight_value.Bind(wx.EVT_CHECKBOX, self.on_apply_annotation)

        annotation_fontColor_label = makeStaticText(panel, "Font color:")
        self.annotation_fontColor_colorBtn = wx.Button(
            panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="annotation_color"
        )
        self.annotation_fontColor_colorBtn.SetBackgroundColour(
            convertRGB1to255(
                self.kwargs.get("annotation_properties", {}).get(
                    "label_color", self.config.interactive_ms_annotations_label_color
                )
            )
        )
        self.annotation_fontColor_colorBtn.Bind(wx.EVT_BUTTON, self.on_apply_color)

        self.annotation_fontColor_presets_value = makeCheckbox(panel, "use preset colors")
        self.annotation_fontColor_presets_value.SetValue(
            self.kwargs.get("annotation_properties", {}).get("label_use_preset_color", False)
        )
        self.annotation_fontColor_presets_value.Bind(wx.EVT_CHECKBOX, self.on_apply_annotation)

        annotation_highlight_peak_label = makeStaticText(panel, "Add patch to peaks:")
        self.annotation_peakHighlight = wx.CheckBox(panel, -1, "", (15, 30))
        self.annotation_peakHighlight.SetValue(
            self.kwargs.get("annotation_properties", {}).get(
                "show_patches", self.config.interactive_ms_annotations_highlight
            )
        )
        self.annotation_peakHighlight.Bind(wx.EVT_CHECKBOX, self.on_apply_annotation)
        self.annotation_peakHighlight.SetToolTip(
            wx.ToolTip("A rectangular-shaped patch will be added to the spectrum to highlight selected peaks")
        )

        annotation_patch_transparency_label = makeStaticText(panel, "Patch transparency:")
        self.annotation_patch_transparency_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            inc=0.25,
            min=0,
            max=1,
            size=(50, -1),
            value=str(
                self.kwargs.get("annotation_properties", {}).get(
                    "patch_transparency", self.config.interactive_ms_annotations_transparency
                )
            ),
            initial=self.kwargs.get("annotation_properties", {}).get(
                "patch_transparency", self.config.interactive_ms_annotations_transparency
            ),
        )
        self.annotation_patch_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_annotation)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(annotation_show_annotations_label, (n, 0), flag=wx.ALIGN_LEFT)
        grid.Add(self.annotation_showAnnotations, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(annotation_annotate_peak_label, (n, 0), flag=wx.ALIGN_LEFT)
        grid.Add(self.annotation_peakLabel, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(annotation_xpos_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.annotation_xpos_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(annotation_ypos_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.annotation_ypos_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(annotation_rotation_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.annotation_rotation_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(annotation_fontSize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.annotation_fontSize_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.annotation_fontWeight_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(annotation_fontColor_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.annotation_fontColor_colorBtn, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(annotation_highlight_peak_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.annotation_peakHighlight, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(annotation_patch_transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.annotation_patch_transparency_value, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.ALIGN_LEFT | wx.ALL, 2)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def makeLegendPanel(self, panel):

        legend_label = makeStaticText(panel, "Legend:")
        self.legend_legend = wx.CheckBox(panel, -1, "", (15, 30))
        self.legend_legend.SetValue(
            self.kwargs.get("legend_properties", {}).get("legend", self.config.interactive_legend)
        )
        self.legend_legend.Bind(wx.EVT_CHECKBOX, self.on_apply_legend)

        position_label = makeStaticText(panel, "Position:")
        self.legend_position = wx.ComboBox(
            panel,
            -1,
            style=wx.CB_READONLY,
            choices=self.config.interactive_legend_location_choices,
            value=self.kwargs.get("legend_properties", {}).get(
                "legend_location", self.config.interactive_legend_location
            ),
        )
        self.legend_position.Bind(wx.EVT_COMBOBOX, self.on_apply_legend)

        orientation_label = makeStaticText(panel, "Orientation:")
        self.legend_orientation = wx.ComboBox(
            panel,
            -1,
            style=wx.CB_READONLY,
            choices=self.config.interactive_legend_orientation_choices,
            value=self.kwargs.get("legend_properties", {}).get(
                "legend_orientation", self.config.interactive_legend_orientation
            ),
        )
        self.legend_orientation.Bind(wx.EVT_COMBOBOX, self.on_apply_legend)

        fontSize_label = makeStaticText(panel, "Font size:")
        self.legend_fontSize = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            value=str(
                self.kwargs.get("legend_properties", {}).get(
                    "legend_font_size", self.config.interactive_legend_font_size
                )
            ),
            min=0,
            max=32,
            initial=self.kwargs.get("legend_properties", {}).get(
                "legend_font_size", self.config.interactive_legend_font_size
            ),
            inc=2,
            size=(50, -1),
        )
        self.legend_fontSize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_legend)

        legendAlpha_label = makeStaticText(panel, "Legend transparency:")
        self.legend_transparency = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            value=str(
                self.kwargs.get("legend_properties", {}).get(
                    "legend_background_alpha", self.config.interactive_legend_background_alpha
                )
            ),
            min=0,
            max=1,
            initial=self.kwargs.get("legend_properties", {}).get(
                "legend_background_alpha", self.config.interactive_legend_background_alpha
            ),
            inc=0.25,
            size=(50, -1),
        )
        self.legend_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_legend)

        action_label = makeStaticText(panel, "Action:")
        self.legend_click_policy = wx.ComboBox(
            panel,
            -1,
            choices=self.config.interactive_legend_click_policy_choices,
            value=self.kwargs.get("legend_properties", {}).get(
                "legend_click_policy", self.config.interactive_legend_click_policy
            ),
            style=wx.CB_READONLY,
        )
        self.legend_click_policy.Bind(wx.EVT_COMBOBOX, self.on_apply_legend)
        #         self.legend_click_policy.Bind(wx.EVT_COMBOBOX, self.onEnableDisable_legend)

        muteAlpha_label = makeStaticText(panel, "Line transparency:")
        self.legend_mute_transparency = wx.SpinCtrlDouble(
            panel,
            min=0,
            max=1,
            inc=0.25,
            size=(50, -1),
            value=str(
                self.kwargs.get("legend_properties", {}).get(
                    "legend_mute_alpha", self.config.interactive_legend_mute_alpha
                )
            ),
            initial=self.kwargs.get("legend_properties", {}).get(
                "legend_mute_alpha", self.config.interactive_legend_mute_alpha
            ),
        )
        self.legend_mute_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_legend)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(legend_label, (n, 0), flag=wx.ALIGN_LEFT)
        grid.Add(self.legend_legend, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(position_label, (n, 0), flag=wx.ALIGN_LEFT)
        grid.Add(self.legend_position, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(orientation_label, (n, 0), flag=wx.ALIGN_LEFT)
        grid.Add(self.legend_orientation, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(fontSize_label, (n, 0), flag=wx.ALIGN_LEFT)
        grid.Add(self.legend_fontSize, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(legendAlpha_label, (n, 0), flag=wx.ALIGN_LEFT)
        grid.Add(self.legend_transparency, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(action_label, (n, 0), flag=wx.ALIGN_LEFT)
        grid.Add(self.legend_click_policy, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(muteAlpha_label, (n, 0), flag=wx.ALIGN_LEFT)
        grid.Add(self.legend_mute_transparency, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.ALIGN_LEFT | wx.ALL, 2)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def makeColorbarPanel(self, panel):
        SC_SIZE = (75, -1)
        colorbar_label = makeStaticText(panel, "Colorbar:")
        self.colorbar_colorbar = wx.CheckBox(panel, -1, "", (15, 30))
        self.colorbar_colorbar.SetValue(
            self.kwargs.get("colorbar_properties", {}).get("colorbar", self.config.interactive_colorbar)
        )
        self.colorbar_colorbar.Bind(wx.EVT_CHECKBOX, self.on_apply_colorbar)
        self.colorbar_colorbar.SetToolTip(wx.ToolTip("Add colorbar to the plot"))

        colorbar_modify_label = makeStaticText(panel, "Modify tick values:")
        self.colorbar_modify_ticks = wx.CheckBox(panel, -1, "", (15, 30))
        self.colorbar_modify_ticks.SetValue(
            self.kwargs.get("colorbar_properties", {}).get(
                "modify_ticks", self.config.interactive_colorbar_modify_ticks
            )
        )
        self.colorbar_modify_ticks.Bind(wx.EVT_CHECKBOX, self.on_apply_colorbar)
        self.colorbar_modify_ticks.SetToolTip(wx.ToolTip("Show ticks as percentage (0 - % - 100)"))

        precision_label = makeStaticText(panel, "Precision:")
        self.colorbar_precision = wx.SpinCtrlDouble(
            panel,
            min=0,
            max=5,
            inc=1,
            size=SC_SIZE,
            value=str(
                self.kwargs.get("colorbar_properties", {}).get("precision", self.config.interactive_colorbar_precision)
            ),
            initial=self.kwargs.get("colorbar_properties", {}).get(
                "precision", self.config.interactive_colorbar_precision
            ),
        )
        self.colorbar_precision.SetToolTip(wx.ToolTip("Number of decimal places in the colorbar tickers"))
        self.colorbar_precision.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_colorbar)

        self.colorbar_useScientific = wx.CheckBox(panel, -1, "Scientific notation", (-1, -1))
        self.colorbar_useScientific.SetValue(
            self.kwargs.get("colorbar_properties", {}).get(
                "use_scientific", self.config.interactive_colorbar_useScientific
            )
        )
        self.colorbar_useScientific.SetToolTip(wx.ToolTip("Enable/disable scientific notation of colorbar tickers"))
        self.colorbar_useScientific.Bind(wx.EVT_CHECKBOX, self.on_apply_colorbar)

        colorbar_edge_color_label = makeStaticText(panel, "Edge color:")
        self.colorbar_edge_color = wx.Button(panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="colorbar_edge_color")
        self.colorbar_edge_color.SetBackgroundColour(
            convertRGB1to255(
                self.kwargs.get("colorbar_properties", {}).get(
                    "edge_color", self.config.interactive_colorbar_edge_color
                )
            )
        )
        self.colorbar_edge_color.Bind(wx.EVT_BUTTON, self.on_apply_color)
        self.colorbar_edge_color.SetToolTip(wx.ToolTip("Color of the colorbar edge"))

        colorbar_edge_width_label = makeStaticText(panel, "Edge width:")
        self.colorbar_edge_width = wx.SpinCtrlDouble(
            panel,
            inc=1.0,
            size=SC_SIZE,
            min=0,
            max=5,
            value=str(
                self.kwargs.get("colorbar_properties", {}).get(
                    "edge_width", self.config.interactive_colorbar_edge_width
                )
            ),
            initial=self.kwargs.get("colorbar_properties", {}).get(
                "edge_width", self.config.interactive_colorbar_edge_width
            ),
        )
        self.colorbar_edge_width.SetToolTip(wx.ToolTip("Width of the colorbar edge"))
        self.colorbar_edge_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_colorbar)

        colorbar_label_fontsize = makeStaticText(panel, "Label font size:")
        self.colorbar_label_fontsize = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=32,
            inc=2,
            size=SC_SIZE,
            value=str(
                self.kwargs.get("colorbar_properties", {}).get(
                    "label_fontsize", self.config.interactive_colorbar_label_fontSize
                )
            ),
            initial=self.kwargs.get("colorbar_properties", {}).get(
                "label_fontsize", self.config.interactive_colorbar_label_fontSize
            ),
        )
        self.colorbar_label_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_colorbar)

        self.colorbar_label_fontweight = makeCheckbox(panel, "bold")
        self.colorbar_label_fontweight.SetValue(
            self.kwargs.get("colorbar_properties", {}).get(
                "label_fontweight", self.config.interactive_colorbar_label_weight
            )
        )
        self.colorbar_label_fontweight.Bind(wx.EVT_CHECKBOX, self.on_apply_colorbar)

        labelOffset_label = makeStaticText(panel, "Label offset:")
        self.colorbar_label_offset = wx.SpinCtrlDouble(
            panel,
            inc=1,
            size=SC_SIZE,
            min=0,
            max=100,
            value=str(
                self.kwargs.get("colorbar_properties", {}).get(
                    "label_offset", self.config.interactive_colorbar_label_offset
                )
            ),
            initial=self.kwargs.get("colorbar_properties", {}).get(
                "label_offset", self.config.interactive_colorbar_label_offset
            ),
        )
        self.colorbar_label_offset.SetToolTip(wx.ToolTip("Distance between the colorbar ticks and the labels"))
        self.colorbar_label_offset.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_colorbar)

        position_label = makeStaticText(panel, "Position:")
        self.colorbar_position = wx.ComboBox(
            panel,
            style=wx.CB_READONLY,
            choices=self.config.interactive_colorbarPosition_choices,
            value=self.kwargs.get("colorbar_properties", {}).get("position", self.config.interactive_colorbar_location),
        )
        self.colorbar_position.SetToolTip(
            wx.ToolTip(
                "Colorbar position next to the plot. The colorbar orientation changes automatically. "
                + "If the value is set to 'above'/'below', you might want to set the position offset x/y to 0."
            )
        )
        self.colorbar_position.Bind(wx.EVT_COMBOBOX, self.on_apply_colorbar)

        offsetX_label = makeStaticText(panel, "Position offset X:")
        self.colorbar_offset_x = wx.SpinCtrlDouble(
            panel,
            inc=5,
            size=SC_SIZE,
            min=0,
            max=100,
            value=str(
                self.kwargs.get("colorbar_properties", {}).get(
                    "position_offset_x", self.config.interactive_colorbar_offset_x
                )
            ),
            initial=self.kwargs.get("colorbar_properties", {}).get(
                "position_offset_x", self.config.interactive_colorbar_offset_x
            ),
        )
        self.colorbar_offset_x.SetToolTip(
            wx.ToolTip(
                "Colorbar position offset in the X axis. Adjust if colorbar is too close or too far away from the plot"
            )
        )
        self.colorbar_offset_x.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_colorbar)

        offsetY_label = makeStaticText(panel, "Position offset Y:")
        self.colorbar_offset_y = wx.SpinCtrlDouble(
            panel,
            inc=5,
            size=SC_SIZE,
            min=0,
            max=100,
            value=str(
                self.kwargs.get("colorbar_properties", {}).get(
                    "position_offset_y", self.config.interactive_colorbar_label_offset
                )
            ),
            initial=self.kwargs.get("colorbar_properties", {}).get(
                "position_offset_y", self.config.interactive_colorbar_offset_y
            ),
        )
        self.colorbar_offset_y.SetToolTip(
            wx.ToolTip(
                "Colorbar position offset in the Y axis. Adjust if colorbar is too close or too far away from the plot"
            )
        )
        self.colorbar_offset_y.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_colorbar)

        padding_label = makeStaticText(panel, "Pad:")
        self.colorbar_padding = wx.SpinCtrlDouble(
            panel,
            inc=5,
            size=SC_SIZE,
            min=0,
            max=100,
            value=str(self.kwargs.get("colorbar_properties", {}).get("pad", self.config.interactive_colorbar_padding)),
            initial=self.kwargs.get("colorbar_properties", {}).get("pad", self.config.interactive_colorbar_padding),
        )
        self.colorbar_padding.SetToolTip(wx.ToolTip(""))
        self.colorbar_padding.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_colorbar)

        if self.kwargs.get("colorbar_properties", {}).get("width", self.config.interactive_colorbar_width) == "auto":
            self.kwargs["colorbar_properties"]["width"] = self.kwargs["colorbar_properties"].get(
                "height", self.config.interactive_colorbar_width
            )
        margin_label = makeStaticText(panel, "Width:")
        self.colorbar_width = wx.SpinCtrlDouble(
            panel,
            inc=5,
            size=SC_SIZE,
            min=0,
            max=100,
            value=str(self.kwargs.get("colorbar_properties", {}).get("width", self.config.interactive_colorbar_width)),
            initial=self.kwargs.get("colorbar_properties", {}).get("width", self.config.interactive_colorbar_width),
        )
        self.colorbar_width.SetToolTip(wx.ToolTip("Width of the colorbar"))
        self.colorbar_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_colorbar)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(colorbar_label, (n, 0), flag=wx.ALIGN_LEFT)
        grid.Add(self.colorbar_colorbar, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(colorbar_modify_label, (n, 0), flag=wx.ALIGN_LEFT)
        grid.Add(self.colorbar_modify_ticks, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(precision_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.colorbar_precision, (n, 1), flag=wx.EXPAND)
        grid.Add(self.colorbar_useScientific, (n, 2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(colorbar_edge_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.colorbar_edge_color, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(colorbar_edge_width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.colorbar_edge_width, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(colorbar_label_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.colorbar_label_fontsize, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.colorbar_label_fontweight, (n, 2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(labelOffset_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.colorbar_label_offset, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(position_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.colorbar_position, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(offsetX_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.colorbar_offset_x, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(offsetY_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.colorbar_offset_y, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(padding_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.colorbar_padding, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(margin_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.colorbar_width, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.ALIGN_LEFT | wx.ALL, 2)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def makeWidgetsPanel(self, panel):

        self.widgets_add_widgets = makeCheckbox(panel, "Add custom JS widgets")
        self.widgets_add_widgets.Bind(wx.EVT_CHECKBOX, self.onEnableDisable_widgets)
        self.widgets_add_widgets.SetValue(
            self.kwargs.get("widgets", {}).get("add_custom_widgets", self.config.interactive_custom_scripts)
        )

        self.widgets_check_all_widgets = makeCheckbox(panel, "Check/uncheck all")
        self.widgets_check_all_widgets.Bind(wx.EVT_CHECKBOX, self.onCheck_widgets)
        self.widgets_check_all_widgets.SetValue(False)

        # general
        general_staticBox = makeStaticBox(panel, "General widgets", size=(-1, -1), color=wx.BLACK)
        general_staticBox.SetSize((-1, -1))
        general_box_sizer = wx.StaticBoxSizer(general_staticBox, wx.HORIZONTAL)

        self.widgets_general_zoom_1D = makeCheckbox(panel, "Y-axis scale slider")
        self.widgets_general_zoom_1D.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_general_zoom_1D.SetValue(self.kwargs.get("widgets", {}).get("slider_zoom", False))

        self.widgets_general_hover_mode = makeCheckbox(panel, "Hover mode toggle")
        self.widgets_general_hover_mode.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_general_hover_mode.SetValue(self.kwargs.get("widgets", {}).get("hover_mode", False))

        general_grid = wx.GridBagSizer(2, 2)
        y = 0
        general_grid.Add(self.widgets_general_zoom_1D, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        general_grid.Add(self.widgets_general_hover_mode, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        general_box_sizer.Add(general_grid, 0, wx.EXPAND, 10)

        # color
        color_staticBox = makeStaticBox(panel, "Color widgets", size=(-1, -1), color=wx.BLACK)
        color_staticBox.SetSize((-1, -1))
        color_box_sizer = wx.StaticBoxSizer(color_staticBox, wx.HORIZONTAL)

        self.widgets_color_colorblind = makeCheckbox(panel, "Colorblind toggle")
        self.widgets_color_colorblind.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_color_colorblind.SetValue(self.kwargs.get("widgets", {}).get("colorblind_safe_1D", False))

        self.widgets_color_colormap = makeCheckbox(panel, "Colormap dropdown")
        self.widgets_color_colormap.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_color_colormap.SetValue(self.kwargs.get("widgets", {}).get("colorblind_safe_2D", False))

        color_grid = wx.GridBagSizer(2, 2)
        y = 0
        color_grid.Add(self.widgets_color_colorblind, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        color_grid.Add(self.widgets_color_colormap, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        color_box_sizer.Add(color_grid, 0, wx.EXPAND, 10)

        # labels
        labels_staticBox = makeStaticBox(panel, "Label and annotation widgets", size=(-1, -1), color=wx.BLACK)
        labels_staticBox.SetSize((-1, -1))
        labels_box_sizer = wx.StaticBoxSizer(labels_staticBox, wx.HORIZONTAL)

        self.widgets_labels_show = makeCheckbox(panel, "Show/hide toggle")
        self.widgets_labels_show.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_labels_show.SetValue(self.kwargs.get("widgets", {}).get("label_toggle", False))

        self.widgets_labels_font_size = makeCheckbox(panel, "Font size slider")
        self.widgets_labels_font_size.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_labels_font_size.SetValue(self.kwargs.get("widgets", {}).get("label_size_slider", False))

        self.widgets_labels_rotate = makeCheckbox(panel, "Rotation slider")
        self.widgets_labels_rotate.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_labels_rotate.SetValue(self.kwargs.get("widgets", {}).get("label_rotation", False))

        self.widgets_labels_offset_x = makeCheckbox(panel, "Offset x slider")
        self.widgets_labels_offset_x.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_labels_offset_x.SetValue(self.kwargs.get("widgets", {}).get("label_offset_x", False))

        self.widgets_labels_offset_y = makeCheckbox(panel, "Offset y slider")
        self.widgets_labels_offset_y.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_labels_offset_y.SetValue(self.kwargs.get("widgets", {}).get("label_offset_y", False))

        labels_grid = wx.GridBagSizer(2, 2)
        y = 0
        labels_grid.Add(self.widgets_labels_show, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        labels_grid.Add(self.widgets_labels_font_size, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        labels_grid.Add(self.widgets_labels_rotate, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        labels_grid.Add(self.widgets_labels_offset_x, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        labels_grid.Add(self.widgets_labels_offset_y, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        labels_box_sizer.Add(labels_grid, 0, wx.EXPAND, 10)

        # legend
        legend_staticBox = makeStaticBox(panel, "Legend widgets", size=(-1, -1), color=wx.BLACK)
        legend_staticBox.SetSize((-1, -1))
        legend_box_sizer = wx.StaticBoxSizer(legend_staticBox, wx.HORIZONTAL)

        self.widgets_legend_show = makeCheckbox(panel, "Show/hide toggle")
        self.widgets_legend_show.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_legend_show.SetValue(self.kwargs.get("widgets", {}).get("legend_toggle", False))

        self.widgets_legend_transparency = makeCheckbox(panel, "Transparency slider")
        self.widgets_legend_transparency.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_legend_transparency.SetValue(self.kwargs.get("widgets", {}).get("legend_transparency", False))

        self.widgets_legend_orientation = makeCheckbox(panel, "Orientation radiobox")
        self.widgets_legend_orientation.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_legend_orientation.SetValue(self.kwargs.get("widgets", {}).get("legend_orientation", False))

        self.widgets_legend_position = makeCheckbox(panel, "Position dropdown")
        self.widgets_legend_position.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_legend_position.SetValue(self.kwargs.get("widgets", {}).get("legend_position", False))

        legend_grid = wx.GridBagSizer(2, 2)
        y = 0
        legend_grid.Add(self.widgets_legend_show, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        legend_grid.Add(self.widgets_legend_transparency, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        legend_grid.Add(self.widgets_legend_orientation, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        legend_grid.Add(self.widgets_legend_position, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        legend_box_sizer.Add(legend_grid, 0, wx.EXPAND, 10)

        # scatter
        scatter_staticBox = makeStaticBox(panel, "Scatter widgets", size=(-1, -1), color=wx.BLACK)
        scatter_staticBox.SetSize((-1, -1))
        scatter_box_sizer = wx.StaticBoxSizer(scatter_staticBox, wx.HORIZONTAL)

        self.widgets_scatter_size = makeCheckbox(panel, "Size slider")
        self.widgets_scatter_size.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_scatter_size.SetValue(self.kwargs.get("widgets", {}).get("scatter_size", False))

        self.widgets_scatter_transparency = makeCheckbox(panel, "Transparency slider")
        self.widgets_scatter_transparency.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_scatter_transparency.SetValue(self.kwargs.get("widgets", {}).get("scatter_transparency", False))

        scatter_grid = wx.GridBagSizer(2, 2)
        y = 0
        scatter_grid.Add(self.widgets_scatter_size, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        scatter_grid.Add(self.widgets_scatter_transparency, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        scatter_box_sizer.Add(scatter_grid, 0, wx.EXPAND, 10)

        # processing
        processing_staticBox = makeStaticBox(panel, "Data processing widgets", size=(-1, -1), color=wx.BLACK)
        processing_staticBox.SetSize((-1, -1))
        processing_box_sizer = wx.StaticBoxSizer(processing_staticBox, wx.HORIZONTAL)

        self.widgets_processing_normalization = makeCheckbox(panel, "Normalization modes dropdown")
        self.widgets_processing_normalization.Bind(wx.EVT_CHECKBOX, self.on_apply_widgets)
        self.widgets_processing_normalization.SetValue(
            self.kwargs.get("widgets", {}).get("processing_normalization", False)
        )

        processing_grid = wx.GridBagSizer(2, 2)
        y = 0
        processing_grid.Add(self.widgets_processing_normalization, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        processing_box_sizer.Add(processing_grid, 0, wx.EXPAND, 10)

        grid_1 = wx.GridBagSizer(2, 2)
        y = 0
        grid_1.Add(self.widgets_add_widgets, (y, 0), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        y = y + 1
        grid_1.Add(self.widgets_check_all_widgets, (y, 0), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)

        # Add to grid sizer
        sizer_left = wx.BoxSizer(wx.VERTICAL)
        sizer_left.Add(grid_1, 0, wx.EXPAND, 0)
        sizer_left.Add(general_box_sizer, 0, wx.EXPAND, 0)
        sizer_left.Add(labels_box_sizer, 0, wx.EXPAND, 0)
        sizer_left.Add(scatter_box_sizer, 0, wx.EXPAND, 0)

        sizer_right = wx.BoxSizer(wx.VERTICAL)
        sizer_right.Add(color_box_sizer, 0, wx.EXPAND, 0)
        sizer_right.Add(legend_box_sizer, 0, wx.EXPAND, 0)
        sizer_right.Add(processing_box_sizer, 0, wx.EXPAND, 0)

        # pack elements
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(sizer_left, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        main_sizer.Add(sizer_right, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

        #         grid_1 = wx.GridBagSizer(2, 2)
        #         y = 0
        #         grid_1.Add(self.widgets_add_widgets, (y,0), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT)
        #         y = y+1
        #         grid_1.Add(self.widgets_check_all_widgets, (y,0), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT)
        #         y = y+1
        #         grid_1.Add(general_box_sizer, (y,0), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT)
        #         grid_1.Add(color_box_sizer, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT)
        #         y = y+1
        #         grid_1.Add(labels_box_sizer, (y,0), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT)
        #         grid_1.Add(legend_box_sizer, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT)
        #         y = y+1
        #         grid_1.Add(scatter_box_sizer, (y,0), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT)
        #         grid_1.Add(processing_box_sizer, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT)
        #
        #         # pack elements
        #         main_sizer = wx.BoxSizer(wx.VERTICAL)
        #         main_sizer.Add(grid_1, 0, wx.ALIGN_LEFT|wx.ALL, 2)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def makeToolsPanel(self, panel):

        tools_position = makeStaticText(panel, "Position:")
        self.tools_position_choice = wx.ComboBox(
            panel,
            style=wx.CB_READONLY,
            choices=["above", "right", "below", "left"],
            value=self.kwargs.get("tools", {}).get("position", "right"),
        )
        self.tools_position_choice.SetToolTip(wx.ToolTip("Position of the toolbar."))
        self.tools_position_choice.Bind(wx.EVT_COMBOBOX, self.on_apply_tools)

        self.tools_check_all = makeCheckbox(panel, "Check default")
        self.tools_check_all.Bind(wx.EVT_CHECKBOX, self.onCheck_tools)

        self.tools_save_check = makeCheckbox(panel, "Save")
        self.tools_save_check.Bind(wx.EVT_CHECKBOX, self.on_apply_tools)
        self.tools_save_check.SetValue(self.kwargs.get("tools", {}).get("save", True))

        self.tools_reset_check = makeCheckbox(panel, "Reset")
        self.tools_reset_check.Bind(wx.EVT_CHECKBOX, self.on_apply_tools)
        self.tools_reset_check.SetValue(self.kwargs.get("tools", {}).get("reset", True))

        self.tools_hover_check = makeCheckbox(panel, "Hover")
        self.tools_hover_check.Bind(wx.EVT_CHECKBOX, self.on_apply_tools)
        self.tools_hover_check.SetValue(self.kwargs.get("tools", {}).get("hover", True))

        self.tools_crosshair_check = makeCheckbox(panel, "Crosshair")
        self.tools_crosshair_check.Bind(wx.EVT_CHECKBOX, self.on_apply_tools)
        self.tools_crosshair_check.SetValue(self.kwargs.get("tools", {}).get("crosshair", True))

        self.tools_pan_xy_check = makeCheckbox(panel, "Pan (both)")
        self.tools_pan_xy_check.Bind(wx.EVT_CHECKBOX, self.on_apply_tools)
        self.tools_pan_xy_check.SetValue(self.kwargs.get("tools", {}).get("pan", True))

        self.tools_pan_x_check = makeCheckbox(panel, "Pan (horizontal)")
        self.tools_pan_x_check.Bind(wx.EVT_CHECKBOX, self.on_apply_tools)
        self.tools_pan_x_check.SetValue(self.kwargs.get("tools", {}).get("xpan", False))

        self.tools_pan_y_check = makeCheckbox(panel, "Pan (vertical)")
        self.tools_pan_y_check.Bind(wx.EVT_CHECKBOX, self.on_apply_tools)
        self.tools_pan_y_check.SetValue(self.kwargs.get("tools", {}).get("ypan", False))

        self.tools_boxzoom_xy_check = makeCheckbox(panel, "Box zoom (both)")
        self.tools_boxzoom_xy_check.Bind(wx.EVT_CHECKBOX, self.on_apply_tools)
        self.tools_boxzoom_xy_check.SetValue(self.kwargs.get("tools", {}).get("boxzoom", True))

        self.tools_boxzoom_x_check = makeCheckbox(panel, "Box zoom (horizontal)")
        self.tools_boxzoom_x_check.Bind(wx.EVT_CHECKBOX, self.on_apply_tools)
        self.tools_boxzoom_x_check.SetValue(self.kwargs.get("tools", {}).get("xbox_zoom", False))

        self.tools_boxzoom_y_check = makeCheckbox(panel, "Box zoom (vertical)")
        self.tools_boxzoom_y_check.Bind(wx.EVT_CHECKBOX, self.on_apply_tools)
        self.tools_boxzoom_y_check.SetValue(self.kwargs.get("tools", {}).get("ybox_zoom", False))

        self.tools_wheel_check = makeCheckbox(panel, "Wheel")
        self.tools_wheel_check.Bind(wx.EVT_CHECKBOX, self.on_apply_tools)
        self.tools_wheel_check.SetValue(self.kwargs.get("tools", {}).get("wheel", True))

        self.tools_wheel_choice = wx.ComboBox(
            panel,
            style=wx.CB_READONLY,
            choices=["Wheel zoom (both)", "Wheel zoom (horizontal)", "Wheel zoom (vertical)"],
            value=self.kwargs.get("tools", {}).get("wheel_type", "Wheel zoom (both)"),
        )
        self.tools_wheel_choice.SetToolTip(wx.ToolTip("Only one wheel-type is permitted."))
        self.tools_wheel_choice.Bind(wx.EVT_COMBOBOX, self.on_apply_tools)

        tools_staticBox = makeStaticBox(panel, "Available tools", size=(-1, -1), color=wx.BLACK)
        tools_staticBox.SetSize((-1, -1))
        tools_box_sizer = wx.StaticBoxSizer(tools_staticBox, wx.HORIZONTAL)

        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(self.tools_save_check, (y, 0), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        y = y + 1
        grid.Add(self.tools_reset_check, (y, 0), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        y = y + 1
        grid.Add(self.tools_hover_check, (y, 0), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        grid.Add(self.tools_crosshair_check, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        y = y + 1
        grid.Add(self.tools_pan_xy_check, (y, 0), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        grid.Add(self.tools_pan_x_check, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        grid.Add(self.tools_pan_y_check, (y, 2), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        y = y + 1
        grid.Add(self.tools_boxzoom_xy_check, (y, 0), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        grid.Add(self.tools_boxzoom_x_check, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        grid.Add(self.tools_boxzoom_y_check, (y, 2), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        y = y + 1
        grid.Add(self.tools_wheel_check, (y, 0), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        grid.Add(self.tools_wheel_choice, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        tools_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        wheel_choices = ["Wheel zoom (both)", "Wheel zoom (horizontal)", "Wheel zoom (vertical)", "auto", "None"]
        active_wheel = makeStaticText(panel, "Active wheel:")
        self.tools_active_wheel_choice = wx.ComboBox(
            panel,
            style=wx.CB_READONLY,
            choices=wheel_choices,
            value=self.kwargs.get("tools", {}).get("active_wheel_type", "Wheel zoom (both)"),
        )
        self.tools_active_wheel_choice.Bind(wx.EVT_COMBOBOX, self.on_apply_tools)

        drag_choices = [
            "Box zoom (both)",
            "Box zoom (horizontal)",
            "Box zoom (vertical)",
            "Pan (both)",
            "Pan (horizontal)",
            "Pan (vertical)",
            "auto",
            "None",
        ]
        active_drag = makeStaticText(panel, "Active drag:")
        self.tools_active_drag_choice = wx.ComboBox(
            panel,
            style=wx.CB_READONLY,
            choices=drag_choices,
            value=self.kwargs.get("tools", {}).get("active_drag_type", "Box zoom (both)"),
        )
        self.tools_active_drag_choice.Bind(wx.EVT_COMBOBOX, self.on_apply_tools)

        active_inspect = makeStaticText(panel, "Active inspect:")
        self.tools_active_inspect_choice = wx.ComboBox(
            panel,
            style=wx.CB_READONLY,
            choices=self.config.interactive_activeHoverTools_choices,
            value=self.kwargs.get("tools", {}).get("active_inspect_type", "Hover"),
        )
        self.tools_active_inspect_choice.Bind(wx.EVT_COMBOBOX, self.on_apply_tools)

        active_staticBox = makeStaticBox(panel, "Active tools", size=(-1, -1), color=wx.BLACK)
        active_staticBox.SetSize((-1, -1))
        active_box_sizer = wx.StaticBoxSizer(active_staticBox, wx.HORIZONTAL)

        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(active_wheel, (y, 0), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        grid.Add(self.tools_active_wheel_choice, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        y = y + 1
        grid.Add(active_drag, (y, 0), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        grid.Add(self.tools_active_drag_choice, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        y = y + 1
        grid.Add(active_inspect, (y, 0), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        grid.Add(self.tools_active_inspect_choice, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        active_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        grid_main = wx.GridBagSizer(2, 2)
        y = 0
        grid_main.Add(tools_position, (y, 0), flag=wx.ALIGN_LEFT)
        grid_main.Add(self.tools_position_choice, (y, 1), flag=wx.EXPAND)
        y = y + 1
        grid_main.Add(self.tools_check_all, (y, 0), wx.GBSpan(1, 3), flag=wx.EXPAND | wx.ALIGN_LEFT)
        y = y + 1
        grid_main.Add(tools_box_sizer, (y, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        y = y + 1
        grid_main.Add(active_box_sizer, (y, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid_main, 0, wx.ALIGN_LEFT | wx.ALL, 2)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def on_apply_tools(self, evt):
        if self._loading_:
            return

        self.kwargs["tools"]["position"] = self.tools_position_choice.GetStringSelection()
        self.kwargs["tools"]["hover"] = self.tools_hover_check.GetValue()
        self.kwargs["tools"]["pan"] = self.tools_pan_xy_check.GetValue()
        self.kwargs["tools"]["xpan"] = self.tools_pan_x_check.GetValue()
        self.kwargs["tools"]["ypan"] = self.tools_pan_y_check.GetValue()
        self.kwargs["tools"]["box_zoom"] = self.tools_boxzoom_xy_check.GetValue()
        self.kwargs["tools"]["xbox_zoom"] = self.tools_boxzoom_x_check.GetValue()
        self.kwargs["tools"]["ybox_zoom"] = self.tools_boxzoom_y_check.GetValue()
        self.kwargs["tools"]["save"] = self.tools_save_check.GetValue()
        self.kwargs["tools"]["crosshair"] = self.tools_crosshair_check.GetValue()
        self.kwargs["tools"]["reset"] = self.tools_reset_check.GetValue()
        self.kwargs["tools"]["wheel"] = self.tools_wheel_check.GetValue()
        self.kwargs["tools"]["wheel_type"] = self.tools_wheel_choice.GetStringSelection()
        if self.kwargs["tools"]["wheel"]:
            if self.kwargs["tools"]["wheel_type"] == "Wheel zoom (both)":
                self.kwargs["tools"]["wheel_zoom"] = True
                self.kwargs["tools"]["xwheel_zoom"] = False
                self.kwargs["tools"]["ywheel_zoom"] = False
            elif self.kwargs["tools"]["wheel_type"] == "Wheel zoom (horizontal)":
                self.kwargs["tools"]["wheel_zoom"] = False
                self.kwargs["tools"]["xwheel_zoom"] = True
                self.kwargs["tools"]["ywheel_zoom"] = False
            elif self.kwargs["tools"]["wheel_type"] == "Wheel zoom (vertical)":
                self.kwargs["tools"]["wheel_zoom"] = False
                self.kwargs["tools"]["xwheel_zoom"] = False
                self.kwargs["tools"]["ywheel_zoom"] = True
        else:
            self.kwargs["tools"]["wheel_zoom"] = False
            self.kwargs["tools"]["xwheel_zoom"] = False
            self.kwargs["tools"]["ywheel_zoom"] = False

        _active_replace_ = {
            "Box zoom (both)": "box_zoom",
            "Box zoom (horizontal)": "xbox_zoom",
            "Box zoom (vertical)": "ybox_zoom",
            "Pan (both)": "pan",
            "Pan (horizontal)": "xpan",
            "Wheel zoom (both)": "wheel_zoom",
            "Wheel zoom (horizontal)": "xwheel_zoom",
            "Wheel zoom (vertical)": "ywheel_zoom",
            "Pan (vertical)": "ypan",
            "auto": "auto",
            "None": None,
            "Hover": "hover",
            "Crosshair": "crosshair",
        }

        self.kwargs["tools"]["active_drag_type"] = self.tools_active_drag_choice.GetStringSelection()
        self.kwargs["tools"]["active_drag"] = _active_replace_[self.kwargs["tools"]["active_drag_type"]]
        self.kwargs["tools"]["active_inspect_type"] = self.tools_active_inspect_choice.GetStringSelection()
        self.kwargs["tools"]["active_inspect"] = _active_replace_[self.kwargs["tools"]["active_inspect_type"]]
        self.kwargs["tools"]["active_wheel_type"] = self.tools_active_wheel_choice.GetStringSelection()
        self.kwargs["tools"]["active_wheel"] = _active_replace_[self.kwargs["tools"]["active_wheel_type"]]

        # create string representation of tools
        on_tools = []
        for key in self.kwargs["tools"]:
            if key in [
                "on_tools",
                "wheel",
                "wheel_type",
                "position",
                "active_drag_type",
                "active_inspect_type",
                "active_wheel_type",
            ]:
                continue
            elif key in ["active_drag", "active_inspect", "active_wheel"]:
                active_value = self.kwargs["tools"][key]
                if active_value not in ["auto", "None", None]:
                    on_tools.append(active_value)
            elif self.kwargs["tools"][key]:
                on_tools.append(key)

        # remove duplicates
        on_tools = list(set(on_tools))

        # join together
        self.kwargs["tools"]["on_tools"] = ",".join(on_tools)

        self.onUpdateDocument()

    def onCheck_tools(self, evt):
        itemList = [
            self.tools_hover_check,
            self.tools_save_check,
            self.tools_reset_check,
            self.tools_pan_xy_check,
            self.tools_boxzoom_xy_check,
            self.tools_wheel_check,
        ]
        disableList = [
            self.tools_crosshair_check,
            self.tools_pan_x_check,
            self.tools_pan_y_check,
            self.tools_boxzoom_x_check,
            self.tools_boxzoom_y_check,
        ]

        for item in itemList:
            item.SetValue(True)
        for item in disableList:
            item.SetValue(False)
        self.tools_wheel_choice.SetStringSelection("Wheel zoom (both)")

        self.on_apply_tools(None)

    def on_apply_widgets(self, evt):
        if self._loading_:
            return

        self.kwargs["widgets"]["add_custom_widgets"] = self.widgets_add_widgets.GetValue()

        self.kwargs["widgets"]["label_toggle"] = self.widgets_labels_show.GetValue()
        self.kwargs["widgets"]["label_size_slider"] = self.widgets_labels_font_size.GetValue()
        self.kwargs["widgets"]["label_rotation"] = self.widgets_labels_rotate.GetValue()
        self.kwargs["widgets"]["label_offset_x"] = self.widgets_labels_offset_x.GetValue()
        self.kwargs["widgets"]["label_offset_y"] = self.widgets_labels_offset_y.GetValue()

        self.kwargs["widgets"]["slider_zoom"] = self.widgets_general_zoom_1D.GetValue()
        self.kwargs["widgets"]["hover_mode"] = self.widgets_general_hover_mode.GetValue()
        self.kwargs["widgets"]["colorblind_safe_1D"] = self.widgets_color_colorblind.GetValue()
        self.kwargs["widgets"]["colorblind_safe_2D"] = self.widgets_color_colorblind.GetValue()
        self.kwargs["widgets"]["colorblind_safe_scatter"] = self.widgets_color_colorblind.GetValue()
        self.kwargs["widgets"]["colormap_change"] = self.widgets_color_colormap.GetValue()

        self.kwargs["widgets"]["legend_toggle"] = self.widgets_legend_show.GetValue()
        self.kwargs["widgets"]["legend_position"] = self.widgets_legend_position.GetValue()
        self.kwargs["widgets"]["legend_orientation"] = self.widgets_legend_orientation.GetValue()
        self.kwargs["widgets"]["legend_transparency"] = self.widgets_legend_transparency.GetValue()

        self.kwargs["widgets"]["scatter_size"] = self.widgets_scatter_size.GetValue()
        self.kwargs["widgets"]["scatter_transparency"] = self.widgets_scatter_transparency.GetValue()
        self.kwargs["widgets"]["processing_normalization"] = self.widgets_processing_normalization.GetValue()

        self.onUpdateDocument()

    def onCheck_widgets(self, evt):
        itemList = [
            self.widgets_labels_show,
            self.widgets_labels_font_size,
            self.widgets_labels_rotate,
            self.widgets_labels_offset_x,
            self.widgets_labels_offset_y,
            self.widgets_general_zoom_1D,
            self.widgets_general_hover_mode,
            self.widgets_color_colorblind,
            self.widgets_color_colormap,
            self.widgets_legend_show,
            self.widgets_legend_orientation,
            self.widgets_legend_position,
            self.widgets_legend_transparency,
            self.widgets_labels_show,
            self.widgets_scatter_size,
            self.widgets_scatter_transparency,
            self.widgets_processing_normalization,
        ]

        if self.widgets_check_all_widgets.GetValue():
            for item in itemList:
                item.SetValue(True)
        else:
            for item in itemList:
                item.SetValue(False)

        self.on_apply_widgets(None)

    def on_apply_colorbar(self, evt):
        if self._loading_:
            return

        self.kwargs["colorbar_properties"]["colorbar"] = self.colorbar_colorbar.GetValue()
        self.kwargs["colorbar_properties"]["precision"] = int(self.colorbar_precision.GetValue())
        self.kwargs["colorbar_properties"]["use_scientific"] = self.colorbar_useScientific.GetValue()
        self.kwargs["colorbar_properties"]["label_offset"] = int(self.colorbar_label_offset.GetValue())
        self.kwargs["colorbar_properties"]["position"] = self.colorbar_position.GetStringSelection()
        self.kwargs["colorbar_properties"]["position_offset_x"] = int(self.colorbar_offset_x.GetValue())
        self.kwargs["colorbar_properties"]["position_offset_y"] = int(self.colorbar_offset_y.GetValue())
        self.kwargs["colorbar_properties"]["pad"] = int(self.colorbar_padding.GetValue())
        self.kwargs["colorbar_properties"]["width"] = int(self.colorbar_width.GetValue())
        self.kwargs["colorbar_properties"]["edge_width"] = self.colorbar_edge_width.GetValue()
        self.kwargs["colorbar_properties"]["modify_ticks"] = self.colorbar_modify_ticks.GetValue()
        self.kwargs["colorbar_properties"]["label_fontsize"] = self.colorbar_label_fontsize.GetValue()
        self.kwargs["colorbar_properties"]["label_fontweight"] = self.colorbar_label_fontweight.GetValue()

        if self.kwargs["colorbar_properties"]["position"] in ("right", "left"):
            self.kwargs["colorbar_properties"]["orientation"] = "vertical"
            self.kwargs["colorbar_properties"]["height"] = "auto"
            self.kwargs["colorbar_properties"]["label_align"] = "left"
        else:
            self.kwargs["colorbar_properties"]["orientation"] = "horizontal"
            self.kwargs["colorbar_properties"]["height"] = int(self.colorbar_width.GetValue())
            self.kwargs["colorbar_properties"]["width"] = "auto"
            self.kwargs["colorbar_properties"]["label_align"] = "center"

        self.onUpdateDocument()

    def on_apply_legend(self, evt):
        if self._loading_:
            return

        self.kwargs["legend_properties"]["legend"] = self.legend_legend.GetValue()
        self.kwargs["legend_properties"]["legend_location"] = self.legend_position.GetStringSelection()
        self.kwargs["legend_properties"]["legend_click_policy"] = self.legend_click_policy.GetStringSelection()
        self.kwargs["legend_properties"]["legend_orientation"] = self.legend_orientation.GetStringSelection()
        self.kwargs["legend_properties"]["legend_font_size"] = self.legend_fontSize.GetValue()
        self.kwargs["legend_properties"]["legend_background_alpha"] = self.legend_transparency.GetValue()
        self.kwargs["legend_properties"]["legend_mute_alpha"] = self.legend_mute_transparency.GetValue()

        self.onUpdateDocument()

    def on_apply_annotation(self, evt):
        if self._loading_:
            return

        self.kwargs["annotation_properties"]["show_annotations"] = self.annotation_showAnnotations.GetValue()
        self.kwargs["annotation_properties"]["show_labels"] = self.annotation_peakLabel.GetValue()
        self.kwargs["annotation_properties"]["show_patches"] = self.annotation_peakHighlight.GetValue()
        self.kwargs["annotation_properties"]["position_offset_x"] = self.annotation_xpos_value.GetValue()
        self.kwargs["annotation_properties"]["position_offset_y"] = self.annotation_ypos_value.GetValue()
        self.kwargs["annotation_properties"]["label_rotation"] = self.annotation_rotation_value.GetValue()
        self.kwargs["annotation_properties"]["label_fontsize"] = self.annotation_fontSize_value.GetValue()
        self.kwargs["annotation_properties"]["label_fontweight"] = self.annotation_fontWeight_value.GetValue()
        self.kwargs["annotation_properties"]["patch_transparency"] = self.annotation_patch_transparency_value.GetValue()

        self.onUpdateDocument()

    def on_apply_general(self, evt):
        if self._loading_:
            return

        # figure parameters
        self.kwargs["plot_height"] = int(self.figure_height_value.GetValue())
        self.kwargs["plot_width"] = int(self.figure_width_value.GetValue())

        # plot parameters
        xlimits = [str2num(self.plot_xmin_value.GetValue()), str2num(self.plot_xmax_value.GetValue())]
        self.kwargs["xlimits"] = xlimits
        ylimits = [str2num(self.plot_ymin_value.GetValue()), str2num(self.plot_ymax_value.GetValue())]
        self.kwargs["ylimits"] = ylimits

        # frame parameters
        self.kwargs["frame_properties"]["title_fontsize"] = self.frame_title_fontsize.GetValue()
        self.kwargs["frame_properties"]["title_fontweight"] = self.frame_title_weight.GetValue()
        self.kwargs["frame_properties"]["label_fontsize"] = self.frame_label_fontsize.GetValue()
        self.kwargs["frame_properties"]["label_fontweight"] = self.frame_label_weight.GetValue()
        self.kwargs["frame_properties"]["tick_fontsize"] = self.frame_ticks_fontsize.GetValue()

        self.kwargs["frame_properties"]["label_xaxis"] = self.frame_label_xaxis_check.GetValue()
        if self.kwargs["frame_properties"]["label_xaxis"]:
            self.kwargs["frame_properties"]["label_xaxis_fontsize"] = self.kwargs["frame_properties"]["label_fontsize"]
        else:
            self.kwargs["frame_properties"]["label_xaxis_fontsize"] = 0

        self.kwargs["frame_properties"]["label_yaxis"] = self.frame_label_yaxis_check.GetValue()
        if self.kwargs["frame_properties"]["label_yaxis"]:
            self.kwargs["frame_properties"]["label_yaxis_fontsize"] = self.kwargs["frame_properties"]["label_fontsize"]
        else:
            self.kwargs["frame_properties"]["label_yaxis_fontsize"] = 0

        self.kwargs["frame_properties"]["ticks_xaxis"] = self.kwargs["frame_properties"]["tick_fontsize"]
        if self.kwargs["frame_properties"]["ticks_xaxis"]:
            self.kwargs["frame_properties"]["ticks_xaxis_color"] = "#000000"
        else:
            self.kwargs["frame_properties"]["ticks_xaxis_color"] = None

        self.kwargs["frame_properties"]["ticks_yaxis"] = self.frame_ticks_yaxis_check.GetValue()
        if self.kwargs["frame_properties"]["ticks_yaxis"]:
            self.kwargs["frame_properties"]["ticks_yaxis_color"] = "#000000"
        else:
            self.kwargs["frame_properties"]["ticks_yaxis_color"] = None

        self.kwargs["frame_properties"]["tick_labels_xaxis"] = self.frame_tick_labels_xaxis_check.GetValue()
        if self.kwargs["frame_properties"]["tick_labels_xaxis"]:
            self.kwargs["frame_properties"]["tick_labels_xaxis_fontsize"] = self.kwargs["frame_properties"][
                "tick_fontsize"
            ]
        else:
            self.kwargs["frame_properties"]["tick_labels_xaxis_fontsize"] = 0

        self.kwargs["frame_properties"]["tick_labels_yaxis"] = self.frame_tick_labels_yaxis_check.GetValue()
        if self.kwargs["frame_properties"]["tick_labels_yaxis"]:
            self.kwargs["frame_properties"]["tick_labels_yaxis_fontsize"] = self.kwargs["frame_properties"][
                "tick_fontsize"
            ]
        else:
            self.kwargs["frame_properties"]["tick_labels_yaxis_fontsize"] = 0

        # border parameters
        self.kwargs["frame_properties"]["border_left"] = int(self.frame_border_min_left.GetValue())
        self.kwargs["frame_properties"]["border_right"] = int(self.frame_border_min_right.GetValue())
        self.kwargs["frame_properties"]["border_top"] = int(self.frame_border_min_top.GetValue())
        self.kwargs["frame_properties"]["border_bottom"] = int(self.frame_border_min_bottom.GetValue())

        self.kwargs["frame_properties"]["outline_width"] = self.frame_outline_width.GetValue()
        self.kwargs["frame_properties"]["outline_transparency"] = self.frame_outline_alpha.GetValue()

        self.kwargs["frame_properties"]["gridline"] = self.frame_gridline_check.GetValue()

        self.onUpdateDocument()

    def on_apply_color(self, evt):
        source = evt.GetEventObject().GetName()

        dlg = DialogColorPicker(self, self.config.customColors)
        if dlg.ShowModal() == "ok":
            color_255, color_1, __ = dlg.GetChosenColour()
            self.config.customColors = dlg.GetCustomColours()

            if source == "gridline_color":
                self.frame_gridline_color.SetBackgroundColour(color_255)
                self.kwargs["frame_properties"]["gridline_color"] = color_1
            elif source == "background_color":
                self.frame_background_colorBtn.SetBackgroundColour(color_255)
                self.kwargs["frame_properties"]["background_color"] = color_1
            elif source == "annotation_color":
                self.annotation_fontColor_colorBtn.SetBackgroundColour(color_255)
                self.kwargs["annotation_properties"]["label_color"] = color_1
            elif source == "colorbar_edge_color":
                self.colorbar_edge_color.SetBackgroundColour(color_255)
                self.kwargs["colorbar_properties"]["edge_color"] = color_1
            elif source == "rmsd_label_color":
                self.rmsd_label_colorBtn.SetBackgroundColour(color_255)
                self.kwargs["overlay_properties"]["rmsd_label_color"] = color_1
            elif source == "rmsd_background_color":
                self.rmsd_background_colorBtn.SetBackgroundColour(color_255)
                self.kwargs["overlay_properties"]["rmsd_background_color"] = color_1
            elif source == "rmsd_matrix_label_color":
                self.rmsd_matrix_fontColor_colorBtn.SetBackgroundColour(color_255)
                self.kwargs["overlay_properties"]["rmsd_matrix_label_color"] = color_1
            elif source == "overlay_grid_label_color":
                self.overlay_grid_label_colorBtn.SetBackgroundColour(color_255)
                self.kwargs["overlay_properties"]["grid_label_color"] = color_1
            elif source == "plot_line_color":
                self.plot_line_color_colorBtn.SetBackgroundColour(color_255)
                self.kwargs["plot_properties"]["line_color"] = color_1
            elif source == "rmsf_line_color":
                self.rmsf_line_color_colorBtn.SetBackgroundColour(color_255)
                self.kwargs["overlay_properties"]["rmsf_line_color"] = color_1
            elif source == "plot_bar_edge_color":
                self.plot_bar_edge_colorBtn.SetBackgroundColour(color_255)
                self.kwargs["plot_properties"]["bar_edge_color"] = color_1
            elif source == "plot_scatter_edge_color":
                self.plot_scatter_marker_edge_colorBtn.SetBackgroundColour(color_255)
                self.kwargs["plot_properties"]["scatter_edge_color"] = color_1
            elif source == "plot_tandem_labelled":
                self.plot_tandem_line_labelled_colorBtn.SetBackgroundColour(color_255)
                self.kwargs["plot_properties"]["tandem_line_color_labelled"] = color_1
            elif source == "plot_tandem_unlabelled":
                self.plot_tandem_line_unlabelled_colorBtn.SetBackgroundColour(color_255)
                self.kwargs["plot_properties"]["tandem_line_color_unlabelled"] = color_1

            # update document
            self.onUpdateDocument()
        else:
            return

    def on_apply_overlay(self, evt):
        if self._loading_:
            return
        # rmsd
        self.kwargs["overlay_properties"]["rmsd_label_fontsize"] = self.rmsd_label_fontsize.GetValue()
        self.kwargs["overlay_properties"]["rmsd_label_fontweight"] = self.rmsd_label_fontweight.GetValue()
        self.kwargs["overlay_properties"]["rmsd_background_transparency"] = self.rmsd_label_transparency.GetValue()

        # rmsd matrix
        self.kwargs["overlay_properties"]["rmsd_matrix_position_offset_x"] = self.rmsd_matrix_xpos_value.GetValue()
        self.kwargs["overlay_properties"]["rmsd_matrix_position_offset_y"] = self.rmsd_matrix_ypos_value.GetValue()
        self.kwargs["overlay_properties"]["rmsd_matrix_label_fontsize"] = self.rmsd_matrix_fontSize_value.GetValue()
        self.kwargs["overlay_properties"]["rmsd_matrix_label_fontweight"] = self.rmsd_matrix_fontWeight_value.GetValue()
        self.kwargs["overlay_properties"][
            "rmsd_matrix_xaxis_rotation"
        ] = self.rmsd_matrix_xaxis_rotation_value.GetValue()
        self.kwargs["overlay_properties"]["rmsd_matrix_colormap"] = self.rmsd_matrix_colormap.GetStringSelection()
        self.kwargs["overlay_properties"][
            "rmsd_matrix_auto_label_color"
        ] = self.rmsd_matrix_auto_fontColor_value.GetValue()

        # multi-line
        self.kwargs["overlay_properties"]["multiline_shade_under"] = self.multiline_shade_under_value.GetValue()
        self.kwargs["overlay_properties"][
            "multiline_shade_transparency"
        ] = self.multiline_shade_transparency_value.GetValue()

        # mask/transparency
        self.kwargs["overlay_properties"]["overlay_merge_tools"] = self.overlay_merge_tools.GetValue()
        self.kwargs["overlay_properties"]["overlay_link_xy"] = self.overlay_linkXY.GetValue()
        self.kwargs["overlay_properties"]["overlay_layout"] = self.overlay_layout.GetStringSelection()
        self.kwargs["overlay_properties"]["overlay_colormap_1"] = self.overlay_colormap_1.GetStringSelection()
        self.kwargs["overlay_properties"]["overlay_colormap_2"] = self.overlay_colormap_2.GetStringSelection()

        # grid (nxn)
        self.kwargs["overlay_properties"]["overlay_grid_add_labels"] = self.overlay_grid_show_labels.GetValue()
        self.kwargs["overlay_properties"]["grid_label_fontsize"] = self.overlay_grid_fontSize_value.GetValue()
        self.kwargs["overlay_properties"]["grid_label_fontweight"] = self.overlay_grid_fontWeight_value.GetValue()
        self.kwargs["overlay_properties"]["grid_position_offset_x"] = self.overlay_grid_xpos_value.GetValue()
        self.kwargs["overlay_properties"]["grid_position_offset_y"] = self.overlay_grid_ypos_value.GetValue()

        self.kwargs["overlay_properties"]["rmsf_line_width"] = self.rmsf_line_width_value.GetValue()
        self.kwargs["overlay_properties"]["rmsf_line_transparency"] = self.rmsf_line_transparency_value.GetValue()
        self.kwargs["overlay_properties"]["rmsf_line_style"] = self.rmsf_line_style_choice.GetStringSelection()
        self.kwargs["overlay_properties"]["rmsf_line_shade_under"] = self.rmsf_line_shade_under.GetValue()
        self.kwargs["overlay_properties"]["rmsf_shade_transparency"] = self.rmsf_shade_transparency_value.GetValue()

        self.onUpdateDocument()

    def on_apply_plots(self, evt):
        if self._loading_:
            return

        # line plots
        self.kwargs["plot_properties"]["line_width"] = self.plot_line_width_value.GetValue()
        self.kwargs["plot_properties"]["line_transparency"] = self.plot_line_transparency_value.GetValue()
        self.kwargs["plot_properties"]["line_style"] = self.plot_line_style_choice.GetStringSelection()
        self.kwargs["plot_properties"]["line_shade_under"] = self.plot_line_shade_under.GetValue()
        self.kwargs["plot_properties"]["shade_transparency"] = self.plot_shade_transparency_value.GetValue()
        self.kwargs["plot_properties"]["hover_link_x"] = self.plot_line_linkX.GetValue()
        if self.kwargs["plot_properties"]["hover_link_x"]:
            self.kwargs["plot_properties"]["hover_mode"] = "vline"
        else:
            self.kwargs["plot_properties"]["hover_mode"] = "mouse"

        # waterfall plots
        self.kwargs["plot_properties"]["waterfall_increment"] = self.waterfall_yaxis_increment_value.GetValue()
        self.kwargs["plot_properties"]["waterfall_shade_under"] = self.waterfall_shade_under_value.GetValue()
        self.kwargs["plot_properties"][
            "waterfall_shade_transparency"
        ] = self.waterfall_shade_transparency_value.GetValue()

        # heatmaps
        self.kwargs["plot_properties"]["colormap"] = self.plot_colormap_choice.GetStringSelection()

        # bar plots
        self.kwargs["plot_properties"]["bar_width"] = self.plot_bar_width_value.GetValue()
        self.kwargs["plot_properties"]["bar_transparency"] = self.plot_bar_transparency_value.GetValue()
        self.kwargs["plot_properties"]["bar_line_width"] = self.plot_bar_line_width_value.GetValue()
        self.kwargs["plot_properties"]["bar_edge_color_sameAsFill"] = self.plot_bar_edge_sameAsFill.GetValue()

        # scatter plots
        self.kwargs["plot_properties"]["scatter_shape"] = self.plot_scatter_shape_choice.GetStringSelection()
        self.kwargs["plot_properties"]["scatter_size"] = self.plot_scatter_size_value.GetValue()
        self.kwargs["plot_properties"]["scatter_transparency"] = self.plot_scatter_transparency_value.GetValue()
        self.kwargs["plot_properties"]["scatter_line_width"] = self.plot_scatter_line_width_value.GetValue()
        self.kwargs["plot_properties"][
            "scatter_edge_color_sameAsFill"
        ] = self.plot_scatter_marker_edge_sameAsFill.GetValue()

        # tandem
        self.kwargs["plot_properties"]["tandem_line_width"] = self.plot_tandem_line_width_value.GetValue()

        self.onUpdateDocument()

    def on_apply_preprocess(self, evt):
        if self._loading_:
            return

        # line plots
        self.kwargs["preprocessing_properties"]["linearize"] = self.preprocess_linearize_check.GetValue()
        self.kwargs["preprocessing_properties"][
            "linearize_binsize"
        ] = self.preprocess_linearize_binsize_value.GetValue()
        self.kwargs["preprocessing_properties"]["linearize_limit"] = self.preprocess_linearize_limit_value.GetValue()

        self.kwargs["preprocessing_properties"]["subsample"] = self.preprocess_subsample_check.GetValue()
        self.kwargs["preprocessing_properties"][
            "subsample_frequency"
        ] = self.preprocess_subsample_frequency_value.GetValue()
        self.kwargs["preprocessing_properties"]["subsample_limit"] = self.preprocess_subsample_limit_value.GetValue()

        self.onUpdateDocument()

    def onEnableDisable_widgets(self, evt):
        itemList = [
            self.widgets_labels_show,
            self.widgets_labels_font_size,
            self.widgets_labels_rotate,
            self.widgets_labels_offset_x,
            self.widgets_labels_offset_y,
            self.widgets_general_zoom_1D,
            self.widgets_general_hover_mode,
            self.widgets_color_colorblind,
            self.widgets_color_colormap,
            self.widgets_legend_show,
            self.widgets_legend_orientation,
            self.widgets_legend_position,
            self.widgets_legend_transparency,
            self.widgets_labels_show,
            self.widgets_scatter_size,
            self.widgets_scatter_transparency,
            self.widgets_processing_normalization,
        ]

        if self.widgets_add_widgets.GetValue():
            for item in itemList:
                item.Enable()
        else:
            for item in itemList:
                item.Disable()

        self.on_apply_widgets(None)
