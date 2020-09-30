"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.gui_elements.helpers import make_static_text
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelTandemSettings(PanelSettingsBase):
    """General settings"""

    # ui elements

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        tandem_line_width = make_static_text(self, "Line width:")
        self.tandem_line_width = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0.0, max=100, inc=0.5, size=(50, -1))
        self.tandem_line_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        tandem_line_unlabelled_color_btn = make_static_text(self, "Line color (unlabelled):")
        self.tandem_line_unlabelled_color_btn = wx.Button(
            self, wx.ID_ANY, "", size=wx.Size(26, 26), name="plot_tandem_unlabelled"
        )
        self.tandem_line_unlabelled_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        tandem_line_labelled_color_btn = make_static_text(self, "Line color (labelled):")
        self.tandem_line_labelled_color_btn = wx.Button(
            self, wx.ID_ANY, "", size=wx.Size(26, 26), name="plot_tandem_labelled"
        )
        self.tandem_line_labelled_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(tandem_line_width, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.tandem_line_width, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(tandem_line_unlabelled_color_btn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.tandem_line_unlabelled_color_btn, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(tandem_line_labelled_color_btn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.tandem_line_labelled_color_btn, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_assign_color(self, evt):
        """Update color"""
        # get color

        # source, color_255, color_1 = self._on_assign_color(evt)

        # # update configuration and button color
        # if source == "1d.marker.fill":
        #     CONFIG.marker_fill_color = color_1
        #     self.plot1d_marker_color_btn.SetBackgroundColour(color_255)

    def on_apply(self, evt):
        """Apply other parameters"""
        if self.import_evt:
            return
        self._parse_evt(evt)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.import_evt = False


if __name__ == "__main__":

    def _main():
        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                self.scrolledPanel = PanelTandemSettings(self, None)

        app = wx.App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
