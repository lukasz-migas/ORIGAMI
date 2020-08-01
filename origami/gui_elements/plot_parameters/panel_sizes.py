"""Legend panel"""
# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.styles import set_item_font
from origami.config.config import CONFIG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


class PanelSizesSettings(PanelSettingsBase):
    """Violin settings"""

    general_left_value, general_bottom_value, general_width_value = None, None, None
    general_height_value, general_width_inch_value, general_height_inch_value = None, None, None
    general_plot_name_value = None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make plot size panel"""
        general_plot_name = wx.StaticText(self, -1, "Plot name:")
        self.general_plot_name_value = wx.Choice(
            self, -1, choices=sorted(CONFIG._plotSettings.keys()), size=(-1, -1)  # noqa
        )
        self.general_plot_name_value.SetSelection(0)
        self.general_plot_name_value.Bind(wx.EVT_CHOICE, self.on_update_plot_sizes)

        plot_size_label = wx.StaticText(self, -1, "Plot size (proportion)")

        left_label = wx.StaticText(self, -1, "Left")
        self.general_left_value = wx.SpinCtrlDouble(
            self, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.05, size=(60, -1)
        )
        self.general_left_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bottom_label = wx.StaticText(self, -1, "Bottom")
        self.general_bottom_value = wx.SpinCtrlDouble(
            self, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.05, size=(60, -1)
        )
        self.general_bottom_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        width_label = wx.StaticText(self, -1, "Width")
        self.general_width_value = wx.SpinCtrlDouble(
            self, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.05, size=(60, -1)
        )
        self.general_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        height_label = wx.StaticText(self, -1, "Height")
        self.general_height_value = wx.SpinCtrlDouble(
            self, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.05, size=(60, -1)
        )
        self.general_height_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        plot_size_inch = wx.StaticText(self, -1, "Plot size (inch)")

        general_width_inch_value = wx.StaticText(self, -1, "Width (inch)")
        self.general_width_inch_value = wx.SpinCtrlDouble(
            self, -1, value=str(0), min=0, max=20, initial=0, inc=2, size=(60, -1)
        )
        self.general_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        general_height_inch_value = wx.StaticText(self, -1, "Height (inch)")
        self.general_height_inch_value = wx.SpinCtrlDouble(
            self, -1, value=str(0), min=0.0, max=20, initial=0, inc=2, size=(60, -1)
        )
        self.general_height_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        axes_parameters_label = wx.StaticText(self, -1, "Axes parameters")
        set_item_font(axes_parameters_label)

        # add elements to grids
        n_col = 5
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(axes_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(general_plot_name, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.general_plot_name_value, (n, 1), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(left_label, (n, 1), flag=wx.ALIGN_CENTER)
        grid.Add(bottom_label, (n, 2), flag=wx.ALIGN_CENTER)
        grid.Add(width_label, (n, 3), flag=wx.ALIGN_CENTER)
        grid.Add(height_label, (n, 4), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(plot_size_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.general_left_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.general_bottom_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.general_width_value, (n, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.general_height_value, (n, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(general_width_inch_value, (n, 1), flag=wx.ALIGN_CENTER)
        grid.Add(general_height_inch_value, (n, 2), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(plot_size_inch, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.general_width_inch_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.general_height_inch_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_update_plot_sizes(self, _evt):
        """Update plot sizes"""

        # get current plot name
        plot_name = self.general_plot_name_value.GetStringSelection()

        # get axes sizes
        plot_values = CONFIG._plotSettings[plot_name]  # noqa

        # update axes sizes
        axes_size = plot_values["axes_size"]
        for i, item in enumerate(
            [self.general_left_value, self.general_bottom_value, self.general_width_value, self.general_height_value]
        ):
            item.SetValue(axes_size[i])

        # update plot sizes
        plot_sizes = plot_values["resize_size"]
        for i, item in enumerate([self.general_width_inch_value, self.general_height_inch_value]):
            item.SetValue(plot_sizes[i])

    def on_apply(self, evt):
        """Update general parameters"""
        if self.import_evt:
            return

        # general
        plot_name = self.general_plot_name_value.GetStringSelection()
        plot_values = [
            self.general_left_value.GetValue(),
            self.general_bottom_value.GetValue(),
            self.general_width_value.GetValue(),
            self.general_height_value.GetValue(),
        ]
        CONFIG._plotSettings[plot_name]["axes_size"] = plot_values  # noqa

        plot_sizes = [self.general_width_inch_value.GetValue(), self.general_height_inch_value.GetValue()]
        CONFIG._plotSettings[plot_name]["resize_size"] = plot_sizes  # noqa

        # fire events
        try:
            self.panel_plot.plot_update_axes(plot_name)
        except AttributeError:
            LOGGER.warning("Could not retrieve view - cannot update plot size")

        self._parse_evt(evt)
