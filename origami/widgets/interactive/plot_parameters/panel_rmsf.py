"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_static_text
from origami.widgets.interactive.plot_parameters.panel_base import PanelSettingsBase


class PanelRMSFSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    rmsf_line_width, rmsf_line_transparency, rmsf_line_style_choice, rmsf_line_color_btn = None, None, None, None
    rmsf_line_fill_under, rmsf_fill_transparency = None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        rmsf_line_width = make_static_text(self, "Line width:")
        self.rmsf_line_width = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=5, inc=0.5, size=(50, -1))
        self.rmsf_line_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        rmsf_line_transparency = make_static_text(self, "Line transparency:")
        self.rmsf_line_transparency = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=1, inc=0.25, size=(50, -1))
        self.rmsf_line_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        rmsf_line_style_choice = make_static_text(self, "Line style:")
        self.rmsf_line_style_choice = wx.ComboBox(
            self, -1, choices=CONFIG.bokeh_line_style_choices, style=wx.CB_READONLY
        )
        self.rmsf_line_style_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)

        rmsf_line_color_btn = make_static_text(self, "Line color:")
        self.rmsf_line_color_btn = wx.Button(self, wx.ID_ANY, "", size=wx.Size(26, 26), name="rmsf_line_color")
        self.rmsf_line_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        rmsf_line_fill_under = make_static_text(self, "Shade under line:")
        self.rmsf_line_fill_under = make_checkbox(self, "")
        self.rmsf_line_fill_under.Bind(wx.EVT_CHECKBOX, self.on_apply)

        rmsf_fill_transparency = make_static_text(self, "Shade transparency:")
        self.rmsf_fill_transparency = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=1, inc=0.25, size=(50, -1))
        self.rmsf_fill_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(rmsf_line_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsf_line_width, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsf_line_transparency, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsf_line_transparency, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsf_line_style_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsf_line_style_choice, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsf_line_color_btn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsf_line_color_btn, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsf_line_fill_under, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsf_line_fill_under, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsf_fill_transparency, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsf_fill_transparency, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_assign_color(self, evt):
        """Update color"""
        # get color
        source, color_255, color_1 = self._on_assign_color(evt)

        # # update configuration and button color
        # if source == "1d.marker.fill":
        #     CONFIG.marker_fill_color = color_1
        #     self.plot1d_marker_color_btn.SetBackgroundColour(color_255)

    def on_apply(self, evt):
        """Apply other parameters"""
        if self.import_evt:
            return
        self._parse_evt(evt)

    def _on_set_config(self, config):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.import_evt = False


if __name__ == "__main__":  # pragma: no cover

    def _main():

        from origami.app import App

        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                self.scrolledPanel = PanelRMSFSettings(self, None)

        app = App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
