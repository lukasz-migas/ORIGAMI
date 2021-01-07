"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_static_text
from origami.widgets.interactive.plot_parameters.panel_base import PanelSettingsBase


class PanelRMSDSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    rmsd_label_fontsize, rmsd_label_fontweight, rmsd_label_transparency, rmsd_label_color_btn = None, None, None, None
    rmsd_background_color_btn = None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        rmsd_label_fontsize = make_static_text(self, "Label font size:")
        self.rmsd_label_fontsize = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=32, inc=2, size=(50, -1))
        self.rmsd_label_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.rmsd_label_fontweight = make_checkbox(self, "bold")
        self.rmsd_label_fontweight.Bind(wx.EVT_CHECKBOX, self.on_apply)

        rmsd_label_transparency = make_static_text(self, "Background transparency:")
        self.rmsd_label_transparency = wx.SpinCtrlDouble(self, min=0, max=1, inc=0.25, size=(50, -1))
        self.rmsd_label_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        rmsd_label_color_btn = make_static_text(self, "Label color:")
        self.rmsd_label_color_btn = wx.Button(self, wx.ID_ANY, "", size=wx.Size(26, 26), name="rmsd_label_color")
        self.rmsd_label_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        rmsd_background_color_btn = make_static_text(self, "Background color:")
        self.rmsd_background_color_btn = wx.Button(
            self, wx.ID_ANY, "", size=wx.Size(26, 26), name="rmsd_background_color"
        )
        self.rmsd_background_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(rmsd_label_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_label_fontsize, (n, 1), flag=wx.EXPAND)
        grid.Add(self.rmsd_label_fontweight, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_label_transparency, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_label_transparency, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_label_color_btn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_label_color_btn, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_background_color_btn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_background_color_btn, (n, 1), flag=wx.EXPAND)

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


if __name__ == "__main__":

    def _main():
        # Local imports
        from origami.app import App

        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                self.scrolledPanel = PanelRMSDSettings(self, None)

        app = App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
