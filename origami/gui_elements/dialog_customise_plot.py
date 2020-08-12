# Third-party imports
import wx
import numpy as np
import matplotlib.ticker as ticker

# Local imports
from origami.styles import Validator
from origami.utils.labels import _replace_labels
from origami.utils.converters import str2num
from origami.gui_elements.helpers import make_checkbox
from origami.visuals.mpl.normalize import MidpointNormalize


class DialogCustomisePlot(wx.Dialog):
    def __init__(self, parent, presenter, config, **kwargs):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            "Customise plot...",
            size=(-1, -1),
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),
        )

        self.parent = parent
        self.presenter = presenter
        self.config = config

        self.plot = kwargs["plot"]
        if not hasattr(self.plot, "lock_plot_from_updating_size"):
            self.plot.lock_plot_from_updating_size = False

        self.kwargs = kwargs
        self.loading = True

        self.make_gui()
        self.CentreOnParent()
        self.on_populate_panel()
        self.on_check_tools()
        self.loading = False

        if "window_title" in kwargs:
            self.SetTitle("Customising - {}".format(kwargs.pop("window_title")))

        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

    def on_key_event(self, evt):
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)

        if evt is not None:
            evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    # ----

    def onOK(self, evt):
        self.EndModal(wx.OK)

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.resetBtn.Bind(wx.EVT_BUTTON, self.onReset)

        self.saveImageBtn.Bind(wx.EVT_BUTTON, self.saveImage)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

    def make_panel(self):

        TEXT_SIZE = 100
        TEXT_SIZE_SMALL = TEXT_SIZE / 2

        panel = wx.Panel(self, -1)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        xaxis_label = wx.StaticText(panel, -1, "X-axis:")
        yaxis_label = wx.StaticText(panel, -1, "Y-axis:")
        min_label = wx.StaticText(panel, -1, "Min:")
        max_label = wx.StaticText(panel, -1, "Max:")
        major_tickFreq_label = wx.StaticText(panel, -1, "Major tick \nfrequency:")
        minor_tickFreq_label = wx.StaticText(panel, -1, "Minor tick \nfrequency:")
        tick_division_label = wx.StaticText(panel, -1, "Division \nfactor:")

        self.xaxis_min_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=Validator("float"))
        self.xaxis_max_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=Validator("float"))
        self.xaxis_minor_tickreq_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=Validator("float"))
        self.xaxis_major_tickreq_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=Validator("float"))

        self.yaxis_min_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=Validator("float"))
        self.yaxis_max_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=Validator("float"))
        self.yaxis_minor_tickreq_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=Validator("float"))
        self.yaxis_major_tickreq_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=Validator("float"))

        self.xaxis_tick_division_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=Validator("float"))
        self.xaxis_tick_division_value.Disable()
        self.yaxis_tick_division_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=Validator("float"))
        self.yaxis_tick_division_value.Disable()

        self.override_defaults = make_checkbox(panel, "Override extents")

        self.applyBtn = wx.Button(panel, wx.ID_ANY, "Apply scales", size=(-1, -1))
        self.applyBtn.Bind(wx.EVT_BUTTON, self.on_apply_scales)

        scales_grid = wx.GridBagSizer(2, 2)
        n = 0
        scales_grid.Add(min_label, (n, 1), flag=wx.ALIGN_CENTER)
        scales_grid.Add(max_label, (n, 2), flag=wx.ALIGN_CENTER)
        scales_grid.Add(minor_tickFreq_label, (n, 3), flag=wx.ALIGN_CENTER)
        scales_grid.Add(major_tickFreq_label, (n, 4), flag=wx.ALIGN_CENTER)
        scales_grid.Add(tick_division_label, (n, 5), flag=wx.ALIGN_CENTER)
        n += 1
        scales_grid.Add(xaxis_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        scales_grid.Add(self.xaxis_min_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        scales_grid.Add(self.xaxis_max_value, (n, 2), flag=wx.EXPAND)
        scales_grid.Add(self.xaxis_minor_tickreq_value, (n, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        scales_grid.Add(self.xaxis_major_tickreq_value, (n, 4), flag=wx.EXPAND)
        scales_grid.Add(self.xaxis_tick_division_value, (n, 5), flag=wx.EXPAND)
        n += 1
        scales_grid.Add(yaxis_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        scales_grid.Add(self.yaxis_min_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        scales_grid.Add(self.yaxis_max_value, (n, 2), flag=wx.EXPAND)
        scales_grid.Add(self.yaxis_minor_tickreq_value, (n, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        scales_grid.Add(self.yaxis_major_tickreq_value, (n, 4), flag=wx.EXPAND)
        scales_grid.Add(self.yaxis_tick_division_value, (n, 5), flag=wx.EXPAND)
        n += 1
        scales_grid.Add(self.override_defaults, (n, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)
        scales_grid.Add(self.applyBtn, (n, 5), flag=wx.ALIGN_CENTER)

        lineWidth_label = wx.StaticText(panel, -1, "Line width:")
        self.line_width_value = wx.SpinCtrlDouble(
            panel, -1, value="", min=1, max=10, initial=0, inc=1, size=(TEXT_SIZE, -1)
        )
        self.line_width_value.Bind(wx.EVT_TEXT, self.on_apply_plot)

        lineStyle_label = wx.StaticText(panel, -1, "Line style:")
        self.line_style_value = wx.Choice(panel, -1, choices=self.config.lineStylesList, size=(TEXT_SIZE, -1))
        self.line_style_value.Bind(wx.EVT_CHOICE, self.on_apply_plot)

        shade_alpha_label = wx.StaticText(panel, -1, "Shade transparency:")
        self.shade_alpha_value = wx.SpinCtrlDouble(
            panel, -1, value="", min=0, max=1, initial=0.25, inc=0.25, size=(TEXT_SIZE, -1)
        )
        self.shade_alpha_value.Bind(wx.EVT_TEXT, self.on_apply_plot)

        line_grid = wx.GridBagSizer(2, 2)
        n = 0
        line_grid.Add(lineWidth_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        line_grid.Add(self.line_width_value, (n, 1), flag=wx.EXPAND)
        line_grid.Add(lineStyle_label, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        line_grid.Add(self.line_style_value, (n, 3), flag=wx.EXPAND)
        n += 1
        line_grid.Add(shade_alpha_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        line_grid.Add(self.shade_alpha_value, (n, 1), flag=wx.EXPAND)

        legend_fontSize_label = wx.StaticText(panel, -1, "Legend font size:")
        self.legend_fontSize_value = wx.Choice(panel, -1, choices=self.config.legendFontChoice, size=(-1, -1))
        self.legend_fontSize_value.Bind(wx.EVT_CHOICE, self.on_apply_legend)

        legend_patch_alpha_label = wx.StaticText(panel, -1, "Patch transparency:")
        self.legend_patch_alpha_value = wx.SpinCtrlDouble(
            panel, -1, value="", min=0, max=1, initial=0.25, inc=0.25, size=(TEXT_SIZE, -1)
        )
        self.legend_patch_alpha_value.Bind(wx.EVT_TEXT, self.on_apply_legend)

        self.legend_frame_check = make_checkbox(panel, "Frame")
        self.legend_frame_check.Bind(wx.EVT_CHECKBOX, self.on_apply_legend)

        legend_grid = wx.GridBagSizer(2, 2)
        n = 0
        legend_grid.Add(legend_fontSize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        legend_grid.Add(self.legend_fontSize_value, (n, 1), flag=wx.EXPAND)
        legend_grid.Add(legend_patch_alpha_label, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        legend_grid.Add(self.legend_patch_alpha_value, (n, 3), flag=wx.EXPAND)
        legend_grid.Add(self.legend_frame_check, (n, 4), flag=wx.EXPAND)

        colormap_label = wx.StaticText(panel, -1, "Colormap:")
        self.colormap_value = wx.Choice(panel, -1, choices=self.config.colormap_choices, size=(-1, -1), name="color")
        self.colormap_value.Bind(wx.EVT_CHOICE, self.on_apply_colormap)

        colormap_min_label = wx.StaticText(panel, -1, "Min:")
        self.cmap_min_value = wx.SpinCtrlDouble(
            panel, -1, value="", min=0, max=100, initial=0, inc=10, size=(TEXT_SIZE_SMALL, -1)
        )
        self.cmap_min_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_colormap)

        colormap_mid_label = wx.StaticText(panel, -1, "Mid:")
        self.cmap_mid_value = wx.SpinCtrlDouble(
            panel, -1, value="", min=0, max=100, initial=0, inc=10, size=(TEXT_SIZE_SMALL, -1)
        )
        self.cmap_mid_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_colormap)

        colormap_max_label = wx.StaticText(panel, -1, "Max:")
        self.cmap_max_value = wx.SpinCtrlDouble(
            panel, -1, value="", min=0, max=100, initial=0, inc=10, size=(TEXT_SIZE_SMALL, -1)
        )
        self.cmap_max_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_colormap)

        colormap_grid = wx.GridBagSizer(2, 2)
        n = 0
        colormap_grid.Add(colormap_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        colormap_grid.Add(self.colormap_value, (n, 1), flag=wx.EXPAND)
        colormap_grid.Add(colormap_min_label, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        colormap_grid.Add(self.cmap_min_value, (n, 3), flag=wx.EXPAND)
        colormap_grid.Add(colormap_mid_label, (n, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        colormap_grid.Add(self.cmap_mid_value, (n, 5), flag=wx.EXPAND)
        colormap_grid.Add(colormap_max_label, (n, 6), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        colormap_grid.Add(self.cmap_max_value, (n, 7), flag=wx.EXPAND)

        spines_label = wx.StaticText(panel, -1, "Line:")
        self.leftSpines_check = make_checkbox(panel, "Left")
        self.leftSpines_check.Bind(wx.EVT_CHECKBOX, self.on_apply_frame)

        self.rightSpines_check = make_checkbox(panel, "Right")
        self.rightSpines_check.Bind(wx.EVT_CHECKBOX, self.on_apply_frame)

        self.topSpines_check = make_checkbox(panel, "Top")
        self.topSpines_check.SetValue(self.config.axes_frame_spine_top)
        self.topSpines_check.Bind(wx.EVT_CHECKBOX, self.on_apply_frame)

        self.bottomSpines_check = make_checkbox(panel, "Bottom")
        self.bottomSpines_check.Bind(wx.EVT_CHECKBOX, self.on_apply_frame)

        ticks_label = wx.StaticText(panel, -1, "Ticks:")
        self.leftTicks_check = make_checkbox(panel, "Left")
        self.leftTicks_check.Bind(wx.EVT_CHECKBOX, self.on_apply_frame)

        self.rightTicks_check = make_checkbox(panel, "Right")
        self.rightTicks_check.Bind(wx.EVT_CHECKBOX, self.on_apply_frame)

        self.topTicks_check = make_checkbox(panel, "Top")
        self.topTicks_check.Bind(wx.EVT_CHECKBOX, self.on_apply_frame)

        self.bottomTicks_check = make_checkbox(panel, "Bottom")
        self.bottomTicks_check.Bind(wx.EVT_CHECKBOX, self.on_apply_frame)

        tickLabels_label = wx.StaticText(panel, -1, "Tick labels:")
        self.leftTickLabels_check = make_checkbox(panel, "Left")
        self.leftTickLabels_check.Bind(wx.EVT_CHECKBOX, self.on_apply_frame)

        self.rightTickLabels_check = make_checkbox(panel, "Right")
        self.rightTickLabels_check.Bind(wx.EVT_CHECKBOX, self.on_apply_frame)

        self.topTickLabels_check = make_checkbox(panel, "Top")
        self.topTickLabels_check.Bind(wx.EVT_CHECKBOX, self.on_apply_frame)

        self.bottomTickLabels_check = make_checkbox(panel, "Bottom")
        self.bottomTickLabels_check.Bind(wx.EVT_CHECKBOX, self.on_apply_frame)

        frame_lineWidth_label = wx.StaticText(panel, -1, "Frame width:")
        self.frame_width_value = wx.SpinCtrlDouble(
            panel, -1, value="1", min=0, max=10, initial=1, inc=1, size=(TEXT_SIZE, -1)
        )
        self.frame_width_value.Bind(wx.EVT_TEXT, self.on_apply_frame)

        # axes parameters
        axis_grid = wx.GridBagSizer(2, 2)
        n = 0
        axis_grid.Add(spines_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.leftSpines_check, (n, 1), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.rightSpines_check, (n, 2), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.topSpines_check, (n, 3), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.bottomSpines_check, (n, 4), flag=wx.ALIGN_CENTER)
        n += 1
        axis_grid.Add(ticks_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.leftTicks_check, (n, 1), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.rightTicks_check, (n, 2), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.topTicks_check, (n, 3), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.bottomTicks_check, (n, 4), flag=wx.ALIGN_CENTER)
        n += 1
        axis_grid.Add(tickLabels_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.leftTickLabels_check, (n, 1), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.rightTickLabels_check, (n, 2), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.topTickLabels_check, (n, 3), flag=wx.ALIGN_CENTER)
        axis_grid.Add(self.bottomTickLabels_check, (n, 4), flag=wx.ALIGN_CENTER)
        n += 1
        axis_grid.Add(frame_lineWidth_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_width_value, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)

        title_label = wx.StaticText(panel, -1, "Title:")
        self.title_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1))
        self.title_value.Bind(wx.EVT_TEXT, self.on_apply_fonts)

        xaxis_label_label = wx.StaticText(panel, -1, "X axis label:")
        self.xlabel_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1))
        self.xlabel_value.Bind(wx.EVT_TEXT, self.on_apply_fonts)

        yaxis_label_label = wx.StaticText(panel, -1, "Y axis label:")
        self.ylabel_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1))
        self.ylabel_value.Bind(wx.EVT_TEXT, self.on_apply_fonts)

        padding_label = wx.StaticText(panel, -1, "Label pad:")
        self.padding_value = wx.SpinCtrlDouble(panel, -1, min=0, max=100, inc=5, size=(90, -1))
        self.padding_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_fonts)

        titleFontSize_label = wx.StaticText(panel, -1, "Title font size:")
        self.titleFontSize_value = wx.SpinCtrlDouble(panel, -1, min=0, max=60, inc=2, size=(90, -1))
        self.titleFontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_fonts)

        self.titleFontWeight_check = make_checkbox(panel, "Bold")
        self.titleFontWeight_check.Bind(wx.EVT_CHECKBOX, self.on_apply_fonts)

        labelFontSize_label = wx.StaticText(panel, -1, "Label font size:")
        self.labelFontSize_value = wx.SpinCtrlDouble(panel, -1, min=0, max=60, inc=2, size=(90, -1))
        self.labelFontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_fonts)

        self.labelFontWeight_check = make_checkbox(panel, "Bold")
        self.labelFontWeight_check.Bind(wx.EVT_CHECKBOX, self.on_apply_fonts)

        tickFontSize_label = wx.StaticText(panel, -1, "Tick font size:")
        self.tickFontSize_value = wx.SpinCtrlDouble(panel, -1, min=0, max=60, inc=2, size=(90, -1))
        self.tickFontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_fonts)

        self.tickFontWeight_check = make_checkbox(panel, "Bold")
        self.tickFontWeight_check.Bind(wx.EVT_CHECKBOX, self.on_apply_fonts)
        self.tickFontWeight_check.Disable()

        # font parameters
        font_grid = wx.GridBagSizer(2, 2)
        n = 0
        font_grid.Add(title_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        font_grid.Add(self.title_value, (n, 1), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        font_grid.Add(xaxis_label_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        font_grid.Add(self.xlabel_value, (n, 1), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        font_grid.Add(yaxis_label_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        font_grid.Add(self.ylabel_value, (n, 1), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        font_grid.Add(padding_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        font_grid.Add(self.padding_value, (n, 1), flag=wx.EXPAND)
        font_grid.Add(titleFontSize_label, (n, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        font_grid.Add(self.titleFontSize_value, (n, 4), flag=wx.EXPAND)
        font_grid.Add(self.titleFontWeight_check, (n, 5), flag=wx.EXPAND)
        n += 1
        font_grid.Add(labelFontSize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        font_grid.Add(self.labelFontSize_value, (n, 1), flag=wx.EXPAND)
        font_grid.Add(self.labelFontWeight_check, (n, 2), flag=wx.EXPAND)
        font_grid.Add(tickFontSize_label, (n, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        font_grid.Add(self.tickFontSize_value, (n, 4), flag=wx.EXPAND)
        font_grid.Add(self.tickFontWeight_check, (n, 5), flag=wx.EXPAND)

        plotSize_label = wx.StaticText(panel, -1, "Plot size (proportion)")

        left_label = wx.StaticText(panel, -1, "Left")
        self.left_value = wx.SpinCtrlDouble(panel, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.05, size=(60, -1))
        self.left_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_axes)

        bottom_label = wx.StaticText(panel, -1, "Bottom")
        self.bottom_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.05, size=(60, -1)
        )
        self.bottom_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_axes)

        width_label = wx.StaticText(panel, -1, "Width")
        self.width_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.05, size=(60, -1)
        )
        self.width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_axes)

        height_label = wx.StaticText(panel, -1, "Height")
        self.height_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.05, size=(60, -1)
        )
        self.height_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_axes)

        plotSize_window_inch_label = wx.StaticText(panel, -1, "Plot size (inch)")
        width_window_inch_label = wx.StaticText(panel, -1, "Width")
        self.width_window_inch_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=20, initial=0, inc=0.5, size=(60, -1)
        )
        self.width_window_inch_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_size)

        height_window_inch_label = wx.StaticText(panel, -1, "Height")
        self.height_window_inch_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=20, initial=0, inc=0.5, size=(60, -1)
        )
        self.height_window_inch_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_size)

        self.lock_size_plot = make_checkbox(panel, "Lock size")
        self.lock_size_plot.SetValue(self.plot.lock_plot_from_updating_size)
        self.lock_size_plot.Bind(wx.EVT_CHECKBOX, self.on_lock_plot_size)

        # add elements to grids
        axes_grid = wx.GridBagSizer(2, 2)
        n = 0
        axes_grid.Add(left_label, (n, 1), flag=wx.ALIGN_CENTER)
        axes_grid.Add(bottom_label, (n, 2), flag=wx.ALIGN_CENTER)
        axes_grid.Add(width_label, (n, 3), flag=wx.ALIGN_CENTER)
        axes_grid.Add(height_label, (n, 4), flag=wx.ALIGN_CENTER)
        n += 1
        axes_grid.Add(plotSize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axes_grid.Add(self.left_value, (n, 1), flag=wx.ALIGN_CENTER)
        axes_grid.Add(self.bottom_value, (n, 2), flag=wx.ALIGN_CENTER)
        axes_grid.Add(self.width_value, (n, 3), flag=wx.ALIGN_CENTER)
        axes_grid.Add(self.height_value, (n, 4), flag=wx.ALIGN_CENTER)
        n += 1
        axes_grid.Add(width_window_inch_label, (n, 1), flag=wx.ALIGN_CENTER)
        axes_grid.Add(height_window_inch_label, (n, 2), flag=wx.ALIGN_CENTER)
        n += 1
        axes_grid.Add(plotSize_window_inch_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        axes_grid.Add(self.width_window_inch_value, (n, 1), flag=wx.ALIGN_CENTER)
        axes_grid.Add(self.height_window_inch_value, (n, 2), flag=wx.ALIGN_CENTER)
        axes_grid.Add(self.lock_size_plot, (n, 3), (1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_3 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_4 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_5 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_6 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_7 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.lock_plot = make_checkbox(panel, "Lock plot look")
        self.lock_plot.SetValue(self.plot.lock_plot_from_updating)
        self.lock_plot.Bind(wx.EVT_CHECKBOX, self.on_lock_plot)

        self.resetBtn = wx.Button(panel, wx.ID_ANY, "Reset", size=(-1, -1))
        self.cancelBtn = wx.Button(panel, -1, "Cancel", size=(-1, -1))
        self.saveImageBtn = wx.Button(panel, wx.ID_ANY, "Save image", size=(-1, -1))

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(scales_grid, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(line_grid, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(legend_grid, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_7, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(colormap_grid, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_3, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(axis_grid, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_4, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(font_grid, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_5, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(axes_grid, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_6, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(self.resetBtn, (n, 0), flag=wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.saveImageBtn, (n, 1), flag=wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.cancelBtn, (n, 2), flag=wx.ALIGN_CENTER_HORIZONTAL)

        n += 1
        grid.Add(self.lock_plot, (n, 0), flag=wx.ALIGN_CENTER_HORIZONTAL)

        main_sizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def on_populate_panel(self):
        # populate all together
        self.xaxis_min_value.SetValue(str(self.kwargs["xmin"]))
        self.xaxis_max_value.SetValue(str(self.kwargs["xmax"]))
        self.yaxis_min_value.SetValue(str(self.kwargs["ymin"]))
        self.yaxis_max_value.SetValue(str(self.kwargs["ymax"]))
        self.line_width_value.SetValue(self.plot.plot_parameters.get("spectrum_line_width", 1.0))
        try:
            self.line_style_value.SetStringSelection(
                self.config.lineStylesDict[self.plot.plot_parameters.get("spectrum_line_style", "-")]
            )
        except Exception:
            self.line_style_value.SetStringSelection(self.plot.plot_parameters.get("spectrum_line_style", "-"))

        self.xaxis_tick_division_value.SetValue(str(1))
        self.yaxis_tick_division_value.SetValue(str(1))

        self.leftSpines_check.SetValue(self.plot.plot_parameters["axes_frame_spine_left"])
        self.rightSpines_check.SetValue(self.plot.plot_parameters["axes_frame_spine_right"])
        self.topSpines_check.SetValue(self.plot.plot_parameters["axes_frame_spine_top"])
        self.bottomSpines_check.SetValue(self.plot.plot_parameters["axes_frame_spine_bottom"])
        self.leftTicks_check.SetValue(self.plot.plot_parameters["axes_frame_ticks_left"])
        self.rightTicks_check.SetValue(self.plot.plot_parameters["axes_frame_ticks_right"])
        self.topTicks_check.SetValue(self.plot.plot_parameters["axes_frame_ticks_top"])
        self.bottomTicks_check.SetValue(self.plot.plot_parameters["axes_frame_ticks_bottom"])
        self.leftTickLabels_check.SetValue(self.plot.plot_parameters["axes_frame_tick_labels_left"])
        self.rightTickLabels_check.SetValue(self.plot.plot_parameters["axes_frame_tick_labels_right"])
        self.topTickLabels_check.SetValue(self.plot.plot_parameters["axes_frame_tick_labels_top"])
        self.bottomTickLabels_check.SetValue(self.plot.plot_parameters["axes_frame_tick_labels_bottom"])

        self.frame_width_value.SetValue(self.plot.plot_parameters.get("axes_frame_width", 1.0))

        self.xlabel_value.SetValue(self.kwargs["xlabel"])
        self.ylabel_value.SetValue(self.kwargs["ylabel"])
        self.title_value.SetValue(self.kwargs["title"])

        self.padding_value.SetValue(self.plot.plot_parameters["axes_label_pad"])
        self.titleFontSize_value.SetValue(self.plot.plot_parameters["axes_title_font_size"])
        self.labelFontSize_value.SetValue(self.plot.plot_parameters["axes_tick_font_weight"])
        self.tickFontSize_value.SetValue(self.plot.plot_parameters["axes_tick_font_size"])

        if not isinstance(self.plot.plot_parameters["axes_title_font_weight"], bool):
            if self.plot.plot_parameters["axes_title_font_weight"] == "normal":
                self.plot.plot_parameters["axes_title_font_weight"] = False
            else:
                self.plot.plot_parameters["axes_title_font_weight"] = True

        if not isinstance(self.plot.plot_parameters["axes_label_font_weight"], bool):
            if self.plot.plot_parameters["axes_label_font_weight"] == "normal":
                self.plot.plot_parameters["axes_label_font_weight"] = False
            else:
                self.plot.plot_parameters["axes_label_font_weight"] = True

        if not isinstance(self.plot.plot_parameters["axes_tick_font_weight"], bool):
            if self.plot.plot_parameters["axes_tick_font_weight"] == "normal":
                self.plot.plot_parameters["axes_tick_font_weight"] = False
            else:
                self.plot.plot_parameters["axes_tick_font_weight"] = True

        self.titleFontWeight_check.SetValue(self.plot.plot_parameters["axes_title_font_weight"])
        self.labelFontWeight_check.SetValue(self.plot.plot_parameters["axes_label_font_weight"])
        self.tickFontWeight_check.SetValue(self.plot.plot_parameters["axes_tick_font_weight"])

        self.width_window_inch_value.SetValue(self.kwargs["plot_size"][0])
        self.height_window_inch_value.SetValue(self.kwargs["plot_size"][1])

        self.left_value.SetValue(self.kwargs["plot_axes"][0])
        self.bottom_value.SetValue(self.kwargs["plot_axes"][1])
        self.width_value.SetValue(self.kwargs["plot_axes"][2])
        self.height_value.SetValue(self.kwargs["plot_axes"][3])

        self.shade_alpha_value.SetValue(self.plot.plot_parameters.get("spectrum_fill_transparency", 0.25))

        self.legend_patch_alpha_value.SetValue(self.plot.plot_parameters.get("legend_patch_transparency", 0.25))
        self.legend_fontSize_value.SetStringSelection(self.plot.plot_parameters.get("legend_font_size", "large"))
        self.legend_frame_check.SetValue(self.plot.plot_parameters.get("legend_frame", False))

        colormap = self.plot.plot_parameters.get("heatmap_colormap", self.config.heatmap_colormap)
        if colormap not in self.config.colormap_choices:
            colormap = self.config.heatmap_colormap
        self.colormap_value.SetStringSelection(colormap)
        self.cmap_min_value.SetValue(self.plot.plot_parameters.get("heatmap_normalization_min", 0))
        self.cmap_mid_value.SetValue(self.plot.plot_parameters.get("heatmap_normalization_mid", 50))
        self.cmap_max_value.SetValue(self.plot.plot_parameters.get("heatmap_normalization_max", 100))

    def on_check_tools(self, check_type="all"):
        if check_type in ["all", "heatmap_colormap"]:
            if self.plot.cax is None:
                disableList = [self.colormap_value, self.cmap_mid_value, self.cmap_min_value, self.cmap_max_value]
                for item in disableList:
                    item.Disable()

    def on_apply_colormap(self, evt):
        colormap = self.colormap_value.GetStringSelection()
        cmap_min = self.cmap_min_value.GetValue()
        cmap_mid = self.cmap_mid_value.GetValue()
        cmap_max = self.cmap_max_value.GetValue()

        self.plot.cax.set_cmap(colormap)
        if hasattr(self.plot, "plot_data"):
            if "zvals" in self.plot.plot_data:
                # normalize
                zvals_max = np.max(self.plot.plot_data["zvals"])
                cmap_min = (zvals_max * cmap_min) / 100.0
                cmap_mid = (zvals_max * cmap_mid) / 100.0
                cmap_max = (zvals_max * cmap_max) / 100.0

                cmap_norm = MidpointNormalize(midpoint=cmap_mid, v_min=cmap_min, v_max=cmap_max)
                self.plot.plot_parameters["colormap_norm"] = cmap_norm

                if "colormap_norm" in self.plot.plot_parameters:
                    self.plot.cax.set_norm(self.plot.plot_parameters["colormap_norm"])
        #                     cbar_ticks = [cmap_min, median([cmap_min + cmap_max]), cmap_max]

        self.plot.lock_plot_from_updating = False
        self.plot.plot_2d_colorbar_update(**self.plot.plot_parameters)
        #         self.plot.lock_plot_from_updating = True
        self.plot.repaint()

        # update kwargs
        self.plot.plot_parameters["heatmap_normalization_min"] = self.cmap_min_value.GetValue()
        self.plot.plot_parameters["heatmap_normalization_mid"] = self.cmap_mid_value.GetValue()
        self.plot.plot_parameters["heatmap_normalization_max"] = self.cmap_max_value.GetValue()
        self.plot.plot_parameters["heatmap_colormap"] = colormap

    def on_apply_legend(self, evt):

        leg = self.plot.plotMS.axes.get_legend()
        leg.set_frame_on(self.legend_frame_check.GetValue())

        #         print(self.plot.cbar.get_ylim())
        #         print(dir(self.plot.cbar))
        #         print(dir_extra(dir(self.plot.cbar), "get"))
        try:
            patches = leg.get_patches()
            legend_alpha = self.legend_patch_alpha_value.GetValue()
            for i in range(len(patches)):
                color = patches[i].get_facecolor()
                patches[i].set_alpha(legend_alpha)
                patches[i].set_facecolor(color)
        except Exception:
            pass

        try:
            texts = leg.get_texts()
            text_size = self.legend_fontSize_value.GetStringSelection()
            for i in range(len(texts)):
                texts[i].set_fontsize(text_size)
        except Exception:
            pass

        self.plot.repaint()

        self.plot.plot_parameters["legend_font_size"] = self.legend_fontSize_value.GetStringSelection()
        self.plot.plot_parameters["legend_patch_transparency"] = self.legend_patch_alpha_value.GetValue()
        self.plot.plot_parameters["legend_frame"] = self.legend_frame_check.GetValue()

    def on_apply_plot(self, evt):
        if self.loading:
            return
        try:
            line_width = self.line_width_value.GetValue()
            line_style = self.line_style_value.GetStringSelection()
            lines = self.plot.plotMS.get_lines()
            for line in lines:
                line.set_linewidth(line_width)
                line.set_linestyle(line_style)
        except Exception:
            pass

        try:
            shade_value = self.shade_alpha_value.GetValue()
            for i in range(len(self.plot.plotMS.collections)):
                self.plot.plotMS.collections[i].set_alpha(shade_value)
        except Exception:
            pass

        self.plot.repaint()

        self.plot.plot_parameters["spectrum_line_width"] = self.line_width_value.GetValue()
        self.plot.plot_parameters["spectrum_line_style"] = self.line_style_value.GetStringSelection()
        self.plot.plot_parameters["spectrum_fill_transparency"] = self.shade_alpha_value.GetValue()

    def on_apply_frame(self, evt):
        if self.loading:
            return

        frame_width = self.frame_width_value.GetValue()
        self.plot.plotMS.tick_params(
            axis="both",
            left=self.leftTicks_check.GetValue(),
            right=self.rightTicks_check.GetValue(),
            top=self.topTicks_check.GetValue(),
            bottom=self.bottomTicks_check.GetValue(),
            labelleft=self.leftTickLabels_check.GetValue(),
            labelright=self.rightTickLabels_check.GetValue(),
            labeltop=self.topTickLabels_check.GetValue(),
            labelbottom=self.bottomTickLabels_check.GetValue(),
            width=frame_width,
        )

        self.plot.plotMS.spines["left"].set_visible(self.leftSpines_check.GetValue())
        self.plot.plotMS.spines["right"].set_visible(self.rightSpines_check.GetValue())
        self.plot.plotMS.spines["top"].set_visible(self.topSpines_check.GetValue())
        self.plot.plotMS.spines["bottom"].set_visible(self.bottomSpines_check.GetValue())

        [i.set_linewidth(frame_width) for i in self.plot.plotMS.spines.values()]
        self.plot.repaint()

        self.plot.plot_parameters["axes_frame_spine_left"] = self.leftSpines_check.GetValue()
        self.plot.plot_parameters["axes_frame_spine_right"] = self.rightSpines_check.GetValue()
        self.plot.plot_parameters["axes_frame_spine_top"] = self.topSpines_check.GetValue()
        self.plot.plot_parameters["axes_frame_spine_bottom"] = self.bottomSpines_check.GetValue()
        self.plot.plot_parameters["axes_frame_ticks_left"] = self.leftTicks_check.GetValue()
        self.plot.plot_parameters["axes_frame_ticks_right"] = self.rightTicks_check.GetValue()
        self.plot.plot_parameters["axes_frame_ticks_top"] = self.topTicks_check.GetValue()
        self.plot.plot_parameters["axes_frame_ticks_bottom"] = self.bottomTicks_check.GetValue()
        self.plot.plot_parameters["axes_frame_tick_labels_left"] = self.leftTickLabels_check.GetValue()
        self.plot.plot_parameters["axes_frame_tick_labels_right"] = self.rightTickLabels_check.GetValue()
        self.plot.plot_parameters["axes_frame_tick_labels_top"] = self.topTickLabels_check.GetValue()
        self.plot.plot_parameters["axes_frame_tick_labels_bottom"] = self.bottomTickLabels_check.GetValue()
        self.plot.plot_parameters["axes_frame_width"] = frame_width

    def on_apply_fonts(self, evt):
        if self.loading:
            return

        #         leg = self.plot.plotMS.axes.get_legend()
        #         leg.set_title("TESTST")
        #         leg.set_frame_on(True)
        #         leg.set_alpha(0.0)
        #         print(dir_extra(dir(leg), "set"))

        # convert weights
        if self.titleFontWeight_check.GetValue():
            title_weight = "heavy"
        else:
            title_weight = "normal"

        if self.labelFontWeight_check.GetValue():
            label_weight = "heavy"
        else:
            label_weight = "normal"

        if self.tickFontWeight_check.GetValue():
            tick_weight = "heavy"
        else:
            tick_weight = "normal"

        # update title
        self.plot.plotMS.set_title(
            self.title_value.GetValue(), fontsize=self.titleFontSize_value.GetValue(), weight=title_weight
        )

        # update labels
        self.plot.plotMS.set_xlabel(
            _replace_labels(self.xlabel_value.GetValue()),
            labelpad=self.padding_value.GetValue(),
            fontsize=self.labelFontSize_value.GetValue(),
            weight=label_weight,
        )
        self.plot.plotMS.set_ylabel(
            _replace_labels(self.ylabel_value.GetValue()),
            labelpad=self.padding_value.GetValue(),
            fontsize=self.labelFontSize_value.GetValue(),
            weight=label_weight,
        )

        # Setup font size info
        self.plot.plotMS.tick_params(labelsize=self.tickFontSize_value.GetValue())
        self.plot.repaint()

        # update plot kwargs
        self.plot.plot_parameters["axes_label_pad"] = self.padding_value.GetValue()
        self.plot.plot_parameters["axes_tick_font_size"] = self.labelFontSize_value.GetValue()
        self.plot.plot_parameters["axes_label_font_weight"] = label_weight
        self.plot.plot_parameters["axes_tick_font_size"] = self.tickFontSize_value.GetValue()
        self.plot.plot_parameters["axes_tick_font_weight"] = tick_weight
        self.plot.plot_parameters["axes_title_font_size"] = self.titleFontSize_value.GetValue()
        self.plot.plot_parameters["axes_title_font_weight"] = title_weight

    def on_apply_size(self, evt):
        if self.loading:
            return
        dpi = wx.ScreenDC().GetPPI()
        figuire_size = (
            int(self.width_window_inch_value.GetValue() * dpi[0]),
            int(self.height_window_inch_value.GetValue() * dpi[1]),
        )
        self.plot.SetSize(figuire_size)
        self.plot.repaint()

        self.plot.plot_parameters["panel_size"] = figuire_size

    def on_apply_axes(self, evt):
        if self.loading:
            return
        axes_sizes = [
            self.left_value.GetValue(),
            self.bottom_value.GetValue(),
            self.width_value.GetValue(),
            self.height_value.GetValue(),
        ]

        self.plot.plot_update_axes(axes_sizes)
        self.plot.repaint()

        self.plot._axes = axes_sizes

    def on_apply_scales(self, evt):

        if self.loading:
            return
        new_xmin = str2num(self.xaxis_min_value.GetValue())
        new_xmax = str2num(self.xaxis_max_value.GetValue())
        self.plot.plotMS.set_xlim((new_xmin, new_xmax))

        new_ymin = str2num(self.yaxis_min_value.GetValue())
        new_ymax = str2num(self.yaxis_max_value.GetValue())
        self.plot.plotMS.set_ylim((new_ymin, new_ymax))

        try:
            new_xticks = str2num(self.xaxis_major_tickreq_value.GetValue())
            self.plot.plotMS.xaxis.set_major_locator(ticker.MultipleLocator(new_xticks))
        except Exception:
            pass

        try:
            new_xticks = str2num(self.xaxis_minor_tickreq_value.GetValue())
            self.plot.plotMS.xaxis.set_minor_locator(ticker.MultipleLocator(new_xticks))
        except Exception:
            pass

        try:
            new_yticks = str2num(self.yaxis_major_tickreq_value.GetValue())
            self.plot.plotMS.yaxis.set_major_locator(ticker.MultipleLocator(new_yticks))
        except Exception:
            pass

        try:
            new_yticks = str2num(self.yaxis_minor_tickreq_value.GetValue())
            self.plot.plotMS.yaxis.set_minor_locator(ticker.MultipleLocator(new_yticks))
        except Exception:
            pass

        if self.override_defaults.GetValue():
            extent = [new_xmin, new_ymin, new_xmax, new_ymax]
            self.plot.update_extents(extent)
            self.plot.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        self.plot.repaint()

    def onTickFrequency(self, evt):
        #         print(dir_extra(dir(self.plot.plotMS.xaxis), keywords="set"))
        try:
            new_xticks = str2num(self.xaxis_major_tickreq_value.GetValue())
            self.plot.plotMS.xaxis.set_major_locator(ticker.MultipleLocator(new_xticks))
        except Exception:
            pass

        try:
            new_xticks = str2num(self.xaxis_minor_tickreq_value.GetValue())
            self.plot.plotMS.xaxis.set_minor_locator(ticker.MultipleLocator(new_xticks))
        except Exception:
            pass

        try:
            new_yticks = str2num(self.yaxis_major_tickreq_value.GetValue())
            self.plot.plotMS.yaxis.set_major_locator(ticker.MultipleLocator(new_yticks))
        except Exception:
            pass

        try:
            new_yticks = str2num(self.yaxis_minor_tickreq_value.GetValue())
            self.plot.plotMS.yaxis.set_minor_locator(ticker.MultipleLocator(new_yticks))
        except Exception:
            pass

        self.plot.repaint()

    def onReset(self, evt):

        # reset range
        self.plot.plotMS.set_xlim((self.kwargs["xmin"], self.kwargs["xmax"]))
        self.plot.plotMS.set_ylim((self.kwargs["ymin"], self.kwargs["ymax"]))

        # reset tickers
        self.plot.plotMS.xaxis.set_major_locator(self.kwargs["major_xticker"])
        self.plot.plotMS.yaxis.set_major_locator(self.kwargs["major_yticker"])

        self.plot.plotMS.xaxis.set_minor_locator(self.kwargs["minor_xticker"])
        self.plot.plotMS.yaxis.set_minor_locator(self.kwargs["minor_yticker"])

        self.plot.repaint()
        self.on_populate_panel()

    def on_lock_plot_size(self, evt):
        if self.lock_size_plot.GetValue():
            self.plot.lock_plot_from_updating_size = True
        else:
            self.plot.lock_plot_from_updating_size = False

    def on_lock_plot(self, evt):
        if self.lock_plot.GetValue():
            self.plot.lock_plot_from_updating = True
        else:
            self.plot.lock_plot_from_updating = False

    def saveImage(self, evt):

        self.parent.save_images(None, plot_obj=self.plot, image_name="")
