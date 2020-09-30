"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_static_text
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelRMSDMatrixSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    rmsd_matrix_colormap, rmsd_matrix_fontsize, rmsd_matrix_fontweight = None, None, None
    rmsd_matrix_font_color_btn, rmsd_matrix_font_color_auto, rmsd_matrix_offset_x = None, None, None
    rmsd_matrix_offset_y, rmsd_matrix_rotation = None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""
        rmsd_matrix_colormap = make_static_text(self, "Colormap:")
        self.rmsd_matrix_colormap = wx.ComboBox(self, -1, style=wx.CB_READONLY, choices=CONFIG.colormap_choices)
        self.rmsd_matrix_colormap.Bind(wx.EVT_COMBOBOX, self.on_apply)

        rmsd_matrix_fontsize = make_static_text(self, "Font size:")
        self.rmsd_matrix_fontsize = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=32, inc=2, size=(50, -1))
        self.rmsd_matrix_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.rmsd_matrix_fontweight = make_checkbox(self, "bold")
        self.rmsd_matrix_fontweight.Bind(wx.EVT_CHECKBOX, self.on_apply)

        rmsd_matrix_font_color_btn = make_static_text(self, "Font color:")
        self.rmsd_matrix_font_color_btn = wx.Button(
            self, wx.ID_ANY, "", size=wx.Size(26, 26), name="rmsd_matrix_label_color"
        )
        self.rmsd_matrix_font_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        rmsd_matrix_font_color_auto = make_static_text(self, "Auto-determine label color:")
        self.rmsd_matrix_font_color_auto = make_checkbox(self, "")
        self.rmsd_matrix_font_color_auto.Bind(wx.EVT_CHECKBOX, self.on_apply)

        rmsd_matrix_offset_x = make_static_text(self, "Position offset X:")
        self.rmsd_matrix_offset_x = wx.SpinCtrlDouble(self, wx.ID_ANY, inc=5, min=-100, max=100, size=(50, -1))
        self.rmsd_matrix_offset_x.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        rmsd_matrix_offset_y = make_static_text(self, "Position offset Y:")
        self.rmsd_matrix_offset_y = wx.SpinCtrlDouble(self, wx.ID_ANY, min=-100, max=100, inc=5, size=(50, -1))
        self.rmsd_matrix_offset_y.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        rmsd_matrix_rotation = make_static_text(self, "X-axis tick rotation:")
        self.rmsd_matrix_rotation = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=180, inc=45, size=(50, -1))
        self.rmsd_matrix_rotation.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(rmsd_matrix_colormap, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_matrix_colormap, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_matrix_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_matrix_fontsize, (n, 1), flag=wx.EXPAND)
        grid.Add(self.rmsd_matrix_fontweight, (n, 2), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(rmsd_matrix_font_color_btn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_matrix_font_color_btn, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_matrix_font_color_auto, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_matrix_font_color_auto, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_matrix_offset_x, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_matrix_offset_x, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_matrix_offset_y, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_matrix_offset_y, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_matrix_rotation, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_matrix_rotation, (n, 1), flag=wx.EXPAND)

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

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.import_evt = False


if __name__ == "__main__":

    def _main():
        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                self.scrolledPanel = PanelRMSDMatrixSettings(self, None)

        app = wx.App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
