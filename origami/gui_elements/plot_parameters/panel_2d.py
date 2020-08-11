"""Legend panel"""
# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.styles import set_item_font
from origami.config.config import CONFIG
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.gui_elements.views.view_register import VIEW_REG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


class Panel2dSettings(PanelSettingsBase):
    """Violin settings"""

    plot2d_colormap_value, plot2d_n_contour_value = None, None
    plot2d_plot_type_value, plot2d_interpolation_value = None, None
    plot2d_normalization_value, plot2d_min_value, plot2d_mid_value = None, None, None
    plot2d_max_value, plot2d_normalization_gamma_value = None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make 2d plot panel"""
        plot2d_plot_type = wx.StaticText(self, -1, "Plot type:")
        self.plot2d_plot_type_value = wx.Choice(
            self, -1, choices=CONFIG.heatmap_plot_type_choices, size=(-1, -1), name="2d.heatmap.view_type"
        )
        self.plot2d_plot_type_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.plot2d_plot_type_value.Bind(wx.EVT_CHOICE, self.on_plot)
        self.plot2d_plot_type_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        plot2d_interpolation = wx.StaticText(self, -1, "Interpolation:")
        self.plot2d_interpolation_value = wx.Choice(
            self, -1, choices=CONFIG.heatmap_interpolation_choices, size=(-1, -1), name="2d.heatmap.heatmap"
        )
        self.plot2d_interpolation_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.plot2d_interpolation_value.Bind(wx.EVT_CHOICE, self.on_update)

        plot2d_n_contour = wx.StaticText(self, -1, "Number of contour levels:")
        self.plot2d_n_contour_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.heatmap_n_contour),
            min=50,
            max=500,
            initial=0,
            inc=25,
            size=(50, -1),
            name="2d.heatmap.contour",
        )
        self.plot2d_n_contour_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot2d_n_contour_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        plot2d_colormap = wx.StaticText(self, -1, "Colormap:")
        self.plot2d_colormap_value = wx.Choice(
            self, -1, choices=CONFIG.colormap_choices, size=(-1, -1), name="2d.heatmap.heatmap"
        )
        self.plot2d_colormap_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.plot2d_colormap_value.Bind(wx.EVT_CHOICE, self.on_update)

        plot2d_normalization = wx.StaticText(self, -1, "Normalization:")
        self.plot2d_normalization_value = wx.Choice(
            self, -1, choices=CONFIG.heatmap_normalization_choices, size=(-1, -1), name="2d.heatmap.normalization"
        )
        self.plot2d_normalization_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.plot2d_normalization_value.Bind(wx.EVT_CHOICE, self.on_update)
        self.plot2d_normalization_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        plot2d_min = wx.StaticText(self, -1, "Min %:")
        self.plot2d_min_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.heatmap_normalization_min),
            min=0,
            max=100,
            initial=0,
            inc=5,
            size=(50, -1),
            name="2d.heatmap.normalization",
        )
        self.plot2d_min_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot2d_min_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        plot2d_mid = wx.StaticText(self, -1, "Mid %:")
        self.plot2d_mid_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.heatmap_normalization_mid),
            min=0,
            max=100,
            initial=0,
            inc=5,
            size=(50, -1),
            name="2d.heatmap.normalization",
        )
        self.plot2d_mid_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot2d_mid_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        plot2d_max = wx.StaticText(self, -1, "Max %:")
        self.plot2d_max_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.heatmap_normalization_max),
            min=0,
            max=100,
            initial=0,
            inc=5,
            size=(90, -1),
            name="2d.heatmap.normalization",
        )
        self.plot2d_max_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot2d_max_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        plot2d_normalization_gamma = wx.StaticText(self, -1, "Power gamma:")
        self.plot2d_normalization_gamma_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.heatmap_normalization_power_gamma),
            min=0,
            max=3,
            initial=0,
            inc=0.1,
            size=(90, -1),
            name="2d.heatmap.normalization",
        )
        self.plot2d_normalization_gamma_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.plot2d_normalization_gamma_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        heatmap_parameters_label = wx.StaticText(self, -1, "Heatmap parameters")
        set_item_font(heatmap_parameters_label)

        normalization_parameters_label = wx.StaticText(self, -1, "Normalization parameters")
        set_item_font(normalization_parameters_label)

        n_col = 3
        grid = wx.GridBagSizer(2, 2)
        # heatmap controls
        n = 0
        grid.Add(heatmap_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(plot2d_plot_type, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2d_plot_type_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(plot2d_interpolation, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2d_interpolation_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(plot2d_n_contour, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2d_n_contour_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(plot2d_colormap, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2d_colormap_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)

        # normalization controls
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(normalization_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(plot2d_normalization, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2d_normalization_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(plot2d_min, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2d_min_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(plot2d_mid, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2d_mid_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(plot2d_max, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2d_max_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(plot2d_normalization_gamma, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2d_normalization_gamma_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_apply(self, evt):
        """Update 2d parameters"""
        if self.import_evt:
            return
        CONFIG.heatmap_normalization = self.plot2d_normalization_value.GetStringSelection()
        CONFIG.heatmap_colormap = self.plot2d_colormap_value.GetStringSelection()
        CONFIG.heatmap_plot_type = self.plot2d_plot_type_value.GetStringSelection()
        CONFIG.heatmap_interpolation = self.plot2d_interpolation_value.GetStringSelection()
        CONFIG.heatmap_normalization_min = str2num(self.plot2d_min_value.GetValue())
        CONFIG.heatmap_normalization_mid = str2num(self.plot2d_mid_value.GetValue())
        CONFIG.heatmap_normalization_max = str2num(self.plot2d_max_value.GetValue())
        CONFIG.heatmap_normalization_power_gamma = str2num(self.plot2d_normalization_gamma_value.GetValue())
        CONFIG.heatmap_n_contour = str2int(self.plot2d_n_contour_value.GetValue())

        # fire events
        # self.on_apply(evt=None)

        if evt is not None:
            evt.Skip()

    def on_toggle_controls(self, evt):
        """Update heatmap controls"""
        CONFIG.heatmap_normalization = self.plot2d_normalization_value.GetStringSelection()
        if CONFIG.heatmap_normalization == "Midpoint":
            self.plot2d_mid_value.Enable()
            self.plot2d_normalization_gamma_value.Enable(False)
        else:
            if CONFIG.heatmap_normalization == "Power":
                self.plot2d_normalization_gamma_value.Enable()
            else:
                self.plot2d_normalization_gamma_value.Enable(False)
            self.plot2d_mid_value.Enable(False)

        CONFIG.heatmap_plot_type = self.plot2d_plot_type_value.GetStringSelection()
        self.plot2d_interpolation_value.Enable(CONFIG.heatmap_plot_type == "Image")
        self.plot2d_n_contour_value.Enable(CONFIG.heatmap_plot_type == "Contour")

        self._parse_evt(evt)

    def on_update(self, evt):
        """Update 2d plots"""
        if evt is None:
            return
        source = evt.GetEventObject().GetName()
        if not source.startswith("2d.heatmap"):
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

    def on_plot(self, evt):
        """Plot"""

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        # heatmap parameters
        self.plot2d_plot_type_value.SetStringSelection(CONFIG.heatmap_plot_type)
        self.plot2d_interpolation_value.SetStringSelection(CONFIG.heatmap_interpolation)
        self.plot2d_n_contour_value.SetValue(CONFIG.heatmap_n_contour)
        self.plot2d_colormap_value.SetStringSelection(CONFIG.heatmap_colormap)

        # normalization parameters
        self.plot2d_normalization_value.SetStringSelection(CONFIG.heatmap_normalization)
        self.plot2d_min_value.SetValue(CONFIG.heatmap_normalization_min)
        self.plot2d_mid_value.SetValue(CONFIG.heatmap_normalization_mid)
        self.plot2d_max_value.SetValue(CONFIG.heatmap_normalization_max)
        self.plot2d_normalization_gamma_value.SetValue(CONFIG.heatmap_normalization_power_gamma)
        self.import_evt = False
