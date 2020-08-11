"""Legend panel"""
# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.config.config import CONFIG
from origami.utils.converters import str2num
from origami.gui_elements.helpers import make_toggle_btn
from origami.gui_elements.views.view_register import VIEW_REG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


class PanelColorbarSettings(PanelSettingsBase):
    """Violin settings"""

    colorbar_tgl, colorbar_position_value, colorbar_width_value, colorbar_width_inset_value = None, None, None, None
    colorbar_pad_value, colorbar_fontsize_value, colorbar_label_format = None, None, None
    colorbar_outline_width_value, colorbar_label_color_btn, colorbar_outline_color_btn = None, None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make colorbar controls"""
        colorbar_tgl = wx.StaticText(self, -1, "Colorbar:")
        self.colorbar_tgl = make_toggle_btn(self, "Off", wx.RED, name="2d.heatmap.colorbar")
        self.colorbar_tgl.Bind(wx.EVT_TOGGLEBUTTON, self.on_toggle_controls)
        self.colorbar_tgl.Bind(wx.EVT_TOGGLEBUTTON, self.on_apply)
        self.colorbar_tgl.Bind(wx.EVT_TOGGLEBUTTON, self.on_update)

        colorbar_label_format = wx.StaticText(self, -1, "Label format:")
        self.colorbar_label_format = wx.Choice(
            self, -1, choices=CONFIG.colorbar_fmt_choices, size=(-1, -1), name="2d.heatmap.colorbar"
        )
        self.colorbar_label_format.Bind(wx.EVT_CHOICE, self.on_apply)
        self.colorbar_label_format.Bind(wx.EVT_CHOICE, self.on_update)

        colorbar_position = wx.StaticText(self, -1, "Position:")
        self.colorbar_position_value = wx.Choice(
            self, -1, choices=CONFIG.colorbar_position_choices, size=(-1, -1), name="2d.heatmap.colorbar"
        )
        self.colorbar_position_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.colorbar_position_value.Bind(wx.EVT_CHOICE, self.on_update)
        self.colorbar_position_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        colorbar_pad = wx.StaticText(self, -1, "Distance:")
        self.colorbar_pad_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.colorbar_pad),
            min=0.0,
            max=2,
            initial=0,
            inc=0.05,
            size=(90, -1),
            name="2d.heatmap.colorbar",
        )
        self.colorbar_pad_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.colorbar_pad_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        colorbar_width_height = wx.StaticText(self, -1, "Width (H) | Height (V) (%):")
        self.colorbar_width_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.colorbar_width),
            min=0.0,
            max=100,
            initial=0,
            inc=0.5,
            size=(90, -1),
            name="2d.heatmap.colorbar",
        )
        self.colorbar_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.colorbar_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        colorbar_width = wx.StaticText(self, -1, "Width (inset) (%):")
        self.colorbar_width_inset_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.colorbar_inset_width),
            min=0.0,
            max=100,
            initial=0,
            inc=5,
            size=(90, -1),
            name="2d.heatmap.colorbar",
        )
        self.colorbar_width_inset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.colorbar_width_inset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        colorbar_fontsize = wx.StaticText(self, -1, "Label font size:")
        self.colorbar_fontsize_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.colorbar_label_size),
            min=0,
            max=32,
            initial=0,
            inc=2,
            size=(90, -1),
            name="2d.heatmap.colorbar",
        )
        self.colorbar_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.colorbar_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        colorbar_label_color = wx.StaticText(self, -1, "Label color:")
        self.colorbar_label_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0.0, name="2d.heatmap.colorbar.label"
        )
        self.colorbar_label_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        colorbar_outline_color = wx.StaticText(self, -1, "Outline color:")
        self.colorbar_outline_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="2d.heatmap.colorbar.outline"
        )
        self.colorbar_outline_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        colorbar_outline_width = wx.StaticText(self, -1, "Frame width:")
        self.colorbar_outline_width_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.colorbar_edge_width),
            min=0,
            max=10,
            initial=CONFIG.colorbar_edge_width,
            inc=1,
            size=(90, -1),
            name="2d.heatmap.colorbar",
        )
        self.colorbar_outline_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.colorbar_outline_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(colorbar_tgl, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_tgl, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_label_format, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_label_format, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_position_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_pad, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_pad_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_width_height, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_width_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_width_inset_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_fontsize_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(colorbar_label_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_label_color_btn, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(colorbar_outline_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_outline_color_btn, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(colorbar_outline_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorbar_outline_width_value, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_apply(self, evt):
        """Apply colorbar parameters"""
        if self.import_evt:
            return
        CONFIG.colorbar = self.colorbar_tgl.GetValue()
        CONFIG.colorbar_position = self.colorbar_position_value.GetStringSelection()
        CONFIG.colorbar_width = str2num(self.colorbar_width_value.GetValue())
        CONFIG.colorbar_pad = str2num(self.colorbar_pad_value.GetValue())
        CONFIG.colorbar_label_size = str2num(self.colorbar_fontsize_value.GetValue())
        CONFIG.colorbar_label_fmt = self.colorbar_label_format.GetStringSelection()
        CONFIG.colorbar_edge_width = str2num(self.colorbar_outline_width_value.GetValue())
        CONFIG.colorbar_inset_width = str2num(self.colorbar_width_inset_value.GetValue())

        if evt is not None:
            evt.Skip()

    def on_update(self, evt):
        """Update 2d plots"""
        evt, source = self._preparse_evt(evt)
        if evt is None:
            return
        if not source.startswith("2d.heatmap.colorbar"):
            self._parse_evt(evt)
            return
        self.on_apply(None)
        name = source.split("2d.")[-1]
        try:
            view = VIEW_REG.view
            view.update_style(name)
        except AttributeError:
            LOGGER.warning("Could not retrieve view - cannot update plot style")
        self._parse_evt(evt)

    def on_toggle_controls(self, evt):
        """Update colorbar controls"""
        CONFIG.colorbar = self.colorbar_tgl.GetValue()
        self.colorbar_tgl.SetLabel("On" if CONFIG.colorbar else "Off")
        self.colorbar_tgl.SetForegroundColour(wx.WHITE)
        self.colorbar_tgl.SetBackgroundColour(wx.BLUE if CONFIG.colorbar else wx.RED)

        CONFIG.colorbar_position = self.colorbar_position_value.GetStringSelection()
        is_inside = CONFIG.colorbar_position.startswith("inside")
        self.colorbar_width_inset_value.Enable(CONFIG.colorbar and is_inside)
        self.colorbar_pad_value.Enable(CONFIG.colorbar and not is_inside)

        self.colorbar_position_value.Enable(CONFIG.colorbar)
        self.colorbar_width_value.Enable(CONFIG.colorbar)
        self.colorbar_fontsize_value.Enable(CONFIG.colorbar)
        self.colorbar_label_format.Enable(CONFIG.colorbar)
        self.colorbar_outline_width_value.Enable(CONFIG.colorbar)
        self.colorbar_label_color_btn.Enable(CONFIG.colorbar)
        self.colorbar_outline_color_btn.Enable(CONFIG.colorbar)

        self._parse_evt(evt)

    def on_assign_color(self, evt):
        """Update color"""

        # get color
        source, color_255, color_1 = self._on_assign_color(evt)

        # update configuration and button color
        if source == "2d.heatmap.colorbar.outline":
            CONFIG.colorbar_edge_color = color_1
            self.colorbar_outline_color_btn.SetBackgroundColour(color_255)
            self.on_update(evt)
        elif source == "2d.heatmap.colorbar.label":
            CONFIG.colorbar_label_color = color_1
            self.colorbar_label_color_btn.SetBackgroundColour(color_255)
            self.on_update(evt)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.colorbar_tgl.SetValue(CONFIG.colorbar)
        self.colorbar_label_format.SetStringSelection(CONFIG.colorbar_label_fmt)
        self.colorbar_position_value.SetStringSelection(CONFIG.colorbar_position)
        self.colorbar_width_value.SetValue(CONFIG.colorbar_width)
        self.colorbar_width_inset_value.SetValue(CONFIG.colorbar_inset_width)
        self.colorbar_fontsize_value.SetValue(CONFIG.colorbar_label_size)
        self.colorbar_label_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.colorbar_label_color))
        self.colorbar_outline_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.colorbar_edge_color))
        self.colorbar_outline_width_value.SetValue(CONFIG.colorbar_edge_width)
        self.colorbar_pad_value.SetValue(CONFIG.colorbar_pad)
        self.import_evt = False
