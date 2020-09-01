"""Legend panel"""
# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.config.config import CONFIG
from origami.utils.converters import str2num
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.views.view_register import VIEW_REG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


class PanelRMSFSettings(PanelSettingsBase):
    """Violin settings"""

    rmsd_line_width_value, rmsd_color_line_btn, rmsd_line_style_value = None, None, None
    rmsd_line_hatch_value, rmsd_alpha_value, rmsd_vspace_value = None, None, None
    rmsd_underline_color_btn, rmsd_line_alpha_label = None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        rmsd_hspace_label = wx.StaticText(self, -1, "Vertical spacing:")
        self.rmsd_vspace_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.rmsf_h_space),
            min=0,
            max=1,
            initial=CONFIG.rmsf_h_space,
            inc=0.05,
            size=(90, -1),
            name="rmsf.grid",
        )
        self.rmsd_vspace_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.rmsd_vspace_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)
        set_tooltip(self.rmsd_vspace_value, "Vertical spacing between RMSF and heatmap plot.")

        rmsd_line_width = wx.StaticText(self, -1, "Line width:")
        self.rmsd_line_width_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.rmsf_line_width),
            min=1,
            max=100,
            initial=CONFIG.rmsf_line_width,
            inc=1,
            size=(90, -1),
            name="rmsf.line",
        )
        self.rmsd_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.rmsd_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        rmsd_line_color = wx.StaticText(self, -1, "Line color:")
        self.rmsd_color_line_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="rmsf.line"
        )
        self.rmsd_color_line_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        rmsd_line_style = wx.StaticText(self, -1, "Line style:")
        self.rmsd_line_style_value = wx.Choice(self, -1, choices=CONFIG.lineStylesList, size=(-1, -1), name="rmsf.line")
        self.rmsd_line_style_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.rmsd_line_style_value.Bind(wx.EVT_CHOICE, self.on_update)

        rmsd_line_alpha_label = wx.StaticText(self, -1, "Line transparency:")
        self.rmsd_line_alpha_label = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.rmsf_line_transparency),
            min=0,
            max=1,
            initial=CONFIG.rmsf_line_transparency,
            inc=0.25,
            size=(90, -1),
            name="rmsf.line",
        )
        self.rmsd_line_alpha_label.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.rmsd_line_alpha_label.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        rmsd_line_hatch = wx.StaticText(self, -1, "Fill hatch:")
        self.rmsd_line_hatch_value = wx.Choice(
            self, -1, choices=list(CONFIG.lineHatchDict.keys()), size=(-1, -1), name="rmsf.fill"
        )
        self.rmsd_line_hatch_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.rmsd_line_hatch_value.Bind(wx.EVT_CHOICE, self.on_update)

        rmsd_underline_color = wx.StaticText(self, -1, "Fill color:")
        self.rmsd_underline_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="rmsf.fill"
        )
        self.rmsd_underline_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        rmsd_alpha_label = wx.StaticText(self, -1, "Fill transparency:")
        self.rmsd_alpha_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.rmsf_fill_transparency),
            min=0,
            max=1,
            initial=CONFIG.rmsf_fill_transparency,
            inc=0.25,
            size=(90, -1),
            name="rmsf.fill",
        )
        self.rmsd_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.rmsd_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(rmsd_hspace_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_vspace_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_line_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_line_width_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_line_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_color_line_btn, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(rmsd_line_style, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_line_style_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_line_alpha_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_line_alpha_label, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_line_hatch, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_line_hatch_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_underline_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_underline_color_btn, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(rmsd_alpha_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_alpha_value, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_apply(self, evt):
        """Apply other parameters"""
        if self.import_evt:
            return
        CONFIG.rmsf_line_style = self.rmsd_line_style_value.GetStringSelection()
        CONFIG.rmsf_line_width = self.rmsd_line_width_value.GetValue()
        CONFIG.rmsf_line_transparency = self.rmsd_line_alpha_label.GetValue()

        CONFIG.rmsf_fill_hatch = CONFIG.lineHatchDict[self.rmsd_line_hatch_value.GetStringSelection()]
        CONFIG.rmsf_fill_transparency = str2num(self.rmsd_alpha_value.GetValue())

        CONFIG.rmsf_h_space = str2num(self.rmsd_vspace_value.GetValue())

        if evt is not None:
            evt.Skip()

    def on_update(self, evt):
        """Update 1d plots"""
        evt, source = self._preparse_evt(evt)
        if evt is None:
            return
        if not source.startswith("rmsf"):
            self._parse_evt(evt)
            return
        self.on_apply(None)

        try:
            view = VIEW_REG.view
            view.update_style(source)
        except (AttributeError, KeyError):
            LOGGER.warning("Could not retrieve view - cannot update plot style")
        self._parse_evt(evt)

    def on_assign_color(self, evt):
        """Update color"""
        # get color
        source, color_255, color_1 = self._on_assign_color(evt)

        # update configuration and button color
        if source == "rmsf.line":
            CONFIG.rmsf_line_color = color_1
            self.rmsd_color_line_btn.SetBackgroundColour(color_255)
            self.on_update(evt)
        elif source == "rmsf.fill":
            CONFIG.rmsf_fill_color = color_1
            self.rmsd_underline_color_btn.SetBackgroundColour(color_255)
            self.on_update(evt)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.rmsd_line_width_value.SetValue(CONFIG.rmsf_line_width)
        self.rmsd_color_line_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.rmsf_line_color))
        self.rmsd_line_style_value.SetStringSelection(CONFIG.rmsf_line_style)
        self.rmsd_line_alpha_label.SetValue(CONFIG.rmsf_line_transparency)

        self.rmsd_line_hatch_value.SetStringSelection(
            list(CONFIG.lineHatchDict.keys())[list(CONFIG.lineHatchDict.values()).index(CONFIG.rmsf_fill_hatch)]
        )
        self.rmsd_underline_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.rmsf_fill_color))
        self.rmsd_alpha_value.SetValue(CONFIG.rmsf_fill_transparency)
        self.rmsd_vspace_value.SetValue(CONFIG.rmsf_h_space)
        self.import_evt = False


class _TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
        self.scrolledPanel = PanelRMSFSettings(self, None)


def _main():

    app = wx.App()

    ex = _TestFrame()

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
