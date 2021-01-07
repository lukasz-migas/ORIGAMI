"""Side panel used within the PanelOverlayViewer"""
# Third-party imports
import wx
import wx.lib.scrolledpanel as wxScrolledPanel

# Local imports
from origami.utils.system import running_under_pytest
from origami.widgets.overlay.plot_parameters.panel_rgb import PanelRGBSettings
from origami.widgets.overlay.plot_parameters.panel_rmsd import PanelRMSDSettings
from origami.widgets.overlay.plot_parameters.panel_rmsf import PanelRMSFSettings
from origami.gui_elements.plot_parameters.panel_waterfall import PanelWaterfallSettings
from origami.widgets.overlay.plot_parameters.panel_general import PanelGeneralSettings
from origami.widgets.overlay.plot_parameters.panel_grid_nxn import PanelGridNxNSettings
from origami.widgets.overlay.plot_parameters.panel_grid_tto import PanelGridTTOSettings
from origami.widgets.overlay.plot_parameters.panel_rmsd_matrix import PanelRMSDMatrixSettings


class PanelOverlayViewerSettings(wxScrolledPanel.ScrolledPanel):
    """Settings panel"""

    # ui elements
    _panel_rmsd, _panel_rmsf, _panel_rmsd_matrix, _panel_rgb = None, None, None, None
    _panel_grid_tto, _panel_grid_nxn, _panel_waterfall, _panel_general = None, None, None, None

    # attributes
    block_signal = False

    def __init__(self, parent, view):
        wxScrolledPanel.ScrolledPanel.__init__(self, parent)
        self.parent = parent
        self.view = view

        self.make_gui()

        if not running_under_pytest():
            self.SetupScrolling()

    def make_gui(self):
        """Make GUI"""
        panel = self

        self._panel_general = wx.CollapsiblePane(
            panel, label="General", style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE
        )
        _ = PanelGeneralSettings(self._panel_general.GetPane(), self.view)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_cp_layout, self._panel_general)

        self._panel_rmsd = wx.CollapsiblePane(panel, label="RMSD", style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE)
        _ = PanelRMSDSettings(self._panel_rmsd.GetPane(), self.view)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_cp_layout, self._panel_rmsd)

        self._panel_rmsf = wx.CollapsiblePane(panel, label="RMSF", style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE)
        _ = PanelRMSFSettings(self._panel_rmsf.GetPane(), self.view)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_cp_layout, self._panel_rmsf)

        self._panel_rmsd_matrix = wx.CollapsiblePane(
            panel, label="RMSD Matrix | Dot", style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE
        )
        _ = PanelRMSDMatrixSettings(self._panel_rmsd_matrix.GetPane(), self.view)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_cp_layout, self._panel_rmsd_matrix)

        self._panel_rgb = wx.CollapsiblePane(panel, label="RGB", style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE)
        _ = PanelRGBSettings(self._panel_rgb.GetPane(), self.view)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_cp_layout, self._panel_rgb)

        self._panel_grid_tto = wx.CollapsiblePane(
            panel, label="Grid (2->1)", style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE
        )
        _ = PanelGridTTOSettings(self._panel_grid_tto.GetPane(), self.view)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_cp_layout, self._panel_grid_tto)

        self._panel_grid_nxn = wx.CollapsiblePane(
            panel, label="Grid (n x n)", style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE
        )
        _ = PanelGridNxNSettings(self._panel_grid_nxn.GetPane(), self.view)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_cp_layout, self._panel_grid_nxn)

        self._panel_waterfall = wx.CollapsiblePane(
            panel, label="Waterfall | Overlay", style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE
        )
        _ = PanelWaterfallSettings(self._panel_waterfall.GetPane(), self.view)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_cp_layout, self._panel_waterfall)

        settings_sizer = wx.BoxSizer(wx.VERTICAL)
        settings_sizer.Add(self._panel_general, 0, wx.EXPAND | wx.ALL, 0)
        settings_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 1)
        settings_sizer.Add(self._panel_rmsd, 0, wx.EXPAND | wx.ALL, 0)
        settings_sizer.Add(self._panel_rmsf, 0, wx.EXPAND | wx.ALL, 0)
        settings_sizer.Add(self._panel_rmsd_matrix, 0, wx.EXPAND | wx.ALL, 0)
        settings_sizer.Add(self._panel_rgb, 0, wx.EXPAND | wx.ALL, 0)
        settings_sizer.Add(self._panel_grid_tto, 0, wx.EXPAND | wx.ALL, 0)
        settings_sizer.Add(self._panel_grid_nxn, 0, wx.EXPAND | wx.ALL, 0)
        settings_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 1)
        settings_sizer.Add(self._panel_waterfall, 0, wx.EXPAND | wx.ALL, 0)
        settings_sizer.Fit(panel)
        settings_sizer.SetMinSize((300, -1))
        panel.SetSizerAndFit(settings_sizer)

    def on_cp_layout(self, _evt):
        """Layout"""
        if self.block_signal:
            return
        self.Layout()
        if self.parent:
            self.parent.Layout()

    def setup_method_settings(self, method: str):
        """Close all layouts but the methods"""
        self.block_signal = True

        is_rmsd = method != "RMSD"
        is_rmsf = method != "RMSF"

        self._panel_general.Collapse(False)
        self._panel_rgb.Collapse(method != "RGB")
        self._panel_rmsd.Collapse(is_rmsd or not is_rmsf)
        self._panel_rmsf.Collapse(is_rmsf)
        self._panel_grid_nxn.Collapse(method != "Grid (n x n)")
        self._panel_grid_tto.Collapse(method != "Grid (2->1)")
        self._panel_waterfall.Collapse(method not in ["Waterfall", "Overlay"])
        self._panel_rmsd_matrix.Collapse(method not in ["RMSD Matrix", "RMSD Dot"])
        self.block_signal = False

        self.on_cp_layout(None)


def _main():
    # Local imports
    from origami.app import App
    from origami.utils.screen import move_to_different_screen

    class _TestFrame(wx.Frame):
        def __init__(self):
            wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
            self.scrolledPanel = PanelOverlayViewerSettings(self, None)

    app = App()
    ex = _TestFrame()

    ex.Show()
    move_to_different_screen(ex)
    app.MainLoop()


if __name__ == "__main__":
    _main()
