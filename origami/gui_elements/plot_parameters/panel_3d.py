"""Legend panel"""
# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.styles import set_item_font
from origami.utils.color import convert_rgb_1_to_255
from origami.config.config import CONFIG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


class Panel3dSettings(PanelSettingsBase):
    """Violin settings"""

    plot3d_background_color_btn, plot3d_colormap_value, plot3d_opacity_value, = None, None, None
    plot3d_clim_max_value, plot3d_fontsize_value, plot3d_margin_x_value, plot3d_margin_y_value = None, None, None, None
    plot3d_margin_z_value, plot3d_axis_color_btn, plot3d_clim_min_value = None, None, None
    plot3d_tick_size_value = None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make 3d plot panel"""
        background_color_label = wx.StaticText(self, -1, "Background color:")
        self.plot3d_background_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="heatmap.3d.background.color"
        )
        self.plot3d_background_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.heatmap_3d_background_color))
        self.plot3d_background_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        # plot3d_camera = wx.StaticText(self, -1, "Camera:")
        # self.plot3d_camera_value = wx.Choice(self, -1, choices=CONFIG.cmaps2, size=(-1, -1),
        # name="heatmap.3d.camera")
        # self.plot3d_camera_value.SetStringSelection(CONFIG.currentCmap)
        # self.plot3d_camera_value.Bind(wx.EVT_CHOICE, self.on_apply)
        # self.plot3d_camera_value.Bind(wx.EVT_CHOICE, self.on_update)

        plot3d_colormap = wx.StaticText(self, -1, "Colormap:")
        self.plot3d_colormap_value = wx.Choice(
            self, -1, choices=CONFIG.cmaps2, size=(-1, -1), name="heatmap.3d.colormap"
        )
        self.plot3d_colormap_value.SetStringSelection(CONFIG.heatmap_3d_colormap)
        self.plot3d_colormap_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.plot3d_colormap_value.Bind(wx.EVT_CHOICE, self.on_update)

        opacity = wx.StaticText(self, -1, "Opacity:")
        self.plot3d_opacity_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.heatmap_3d_opacity),
            min=0,
            max=1,
            initial=0,
            inc=0.05,
            size=(50, -1),
            name="heatmap.3d.opacity",
        )
        self.plot3d_opacity_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot3d_opacity_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        plot3d_min = wx.StaticText(self, -1, "Contrast min:")
        self.plot3d_clim_min_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.heatmap_3d_clim_min),
            min=0,
            max=1,
            initial=0,
            inc=0.05,
            size=(50, -1),
            name="heatmap.3d.clim",
        )
        self.plot3d_clim_min_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot3d_clim_min_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        plot3d_max = wx.StaticText(self, -1, "Contrast max:")
        self.plot3d_clim_max_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.heatmap_3d_clim_max),
            min=0,
            max=1,
            initial=0,
            inc=0.05,
            size=(50, -1),
            name="heatmap.3d.clim",
        )
        self.plot3d_clim_max_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot3d_clim_max_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        font_size = wx.StaticText(self, -1, "Font size (px):")
        self.plot3d_fontsize_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.heatmap_3d_axis_font_size),
            min=0,
            max=48,
            initial=0,
            inc=4,
            name="heatmap.3d.font",
        )
        self.plot3d_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot3d_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        tick_size = wx.StaticText(self, -1, "Tick size (px):")
        self.plot3d_tick_size_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.heatmap_3d_axis_tick_size),
            min=0,
            max=48,
            initial=0,
            inc=4,
            name="heatmap.3d.tick",
        )
        self.plot3d_tick_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot3d_tick_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        margin_x = wx.StaticText(self, -1, "Label margin (x):")
        self.plot3d_margin_x_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.heatmap_3d_axis_x_margin),
            min=0,
            max=150,
            initial=0,
            inc=5,
            name="heatmap.3d.margin.x",
        )
        self.plot3d_margin_x_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot3d_margin_x_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        margin_y = wx.StaticText(self, -1, "Label margin (y):")
        self.plot3d_margin_y_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.heatmap_3d_axis_y_margin),
            min=0,
            max=150,
            initial=0,
            inc=5,
            name="heatmap.3d.margin.y",
        )
        self.plot3d_margin_y_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot3d_margin_y_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        margin_z = wx.StaticText(self, -1, "Label margin (z):")
        self.plot3d_margin_z_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.heatmap_3d_axis_z_margin),
            min=0,
            max=150,
            initial=0,
            inc=5,
            name="heatmap.3d.margin.z",
        )
        self.plot3d_margin_z_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot3d_margin_z_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        axis_color_label = wx.StaticText(self, -1, "Axes color:")
        self.plot3d_axis_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="heatmap.3d.axis.color"
        )
        self.plot3d_axis_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.heatmap_3d_axis_color))
        self.plot3d_axis_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        heatmap_parameters_label = wx.StaticText(self, -1, "Heatmap parameters")
        set_item_font(heatmap_parameters_label)

        n_col = 2
        grid = wx.GridBagSizer(2, 2)
        # plot controls
        n = 0
        grid.Add(heatmap_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(background_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot3d_background_color_btn, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(plot3d_colormap, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot3d_colormap_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(opacity, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot3d_opacity_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(plot3d_min, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot3d_clim_min_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(plot3d_max, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot3d_clim_max_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(font_size, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot3d_fontsize_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(tick_size, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot3d_tick_size_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(margin_x, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot3d_margin_x_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(margin_y, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot3d_margin_y_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(margin_z, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot3d_margin_z_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(axis_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot3d_axis_color_btn, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_apply(self, evt):
        """Update 3d parameters"""
        if self.import_evt:
            return

        CONFIG.heatmap_3d_colormap = self.plot3d_colormap_value.GetStringSelection()
        CONFIG.heatmap_3d_opacity = self.plot3d_opacity_value.GetValue()
        CONFIG.heatmap_3d_clim_min = self.plot3d_clim_min_value.GetValue()
        CONFIG.heatmap_3d_clim_max = self.plot3d_clim_max_value.GetValue()
        CONFIG.heatmap_3d_axis_font_size = self.plot3d_fontsize_value.GetValue()
        CONFIG.heatmap_3d_axis_tick_size = self.plot3d_tick_size_value.GetValue()
        CONFIG.heatmap_3d_axis_x_margin = self.plot3d_margin_x_value.GetValue()
        CONFIG.heatmap_3d_axis_y_margin = self.plot3d_margin_y_value.GetValue()
        CONFIG.heatmap_3d_axis_z_margin = self.plot3d_margin_z_value.GetValue()

        if evt is not None:
            evt.Skip()

    def on_update(self, evt):
        """Update 3d plots"""
        if evt is None:
            return
        source = evt.GetEventObject().GetName()
        if not source.startswith("heatmap.3d"):
            self._parse_evt(evt)
            return
        self.on_apply(None)
        name = source.split("heatmap.3d.")[-1]
        try:
            view = self.panel_plot.get_view_from_name()
            view.update_style(name)
        except AttributeError:
            LOGGER.warning("Could not retrieve view - cannot update plot style")
        self._parse_evt(evt)

    def on_assign_color(self, evt):
        """Update color"""

        # get color
        source, color_255, color_1 = self._on_assign_color(evt)

        # update configuration and button color
        if source == "heatmap.3d.background.color":
            CONFIG.heatmap_3d_background_color = color_1
            self.plot3d_background_color_btn.SetBackgroundColour(color_255)
            self.on_update_3d(evt)
        elif source == "heatmap.3d.axis.color":
            CONFIG.heatmap_3d_axis_color = color_1
            self.plot3d_axis_color_btn.SetBackgroundColour(color_255)
            self.on_update_3d(evt)
