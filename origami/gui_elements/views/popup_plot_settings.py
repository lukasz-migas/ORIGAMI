"""Popup plot settings"""
# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.popup import PopupBase
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font


class PopupPlotPanelSettings(PopupBase):
    """Create popup window to modify few uncommon settings"""

    disable_extraction = None
    disable_popup = None
    ms_extract_heatmap = None
    ms_show_heatmap_popup = None
    ms_extract_rt = None
    ms_show_rt_popup = None
    ms_extract_dt = None
    ms_show_dt_popup = None
    rt_extract_ms = None
    rt_show_ms_popup = None
    dt_extract_ms = None
    dt_show_ms_popup = None
    heatmap_extract_ms = None
    heatmap_show_ms_popup = None
    heatmap_extract_rt = None
    heatmap_show_rt_popup = None
    dtms_extract_rt = None
    dtms_show_rt_popup = None

    def __init__(self, parent, style=wx.BORDER_SIMPLE):
        PopupBase.__init__(self, parent, style)

    def make_panel(self):
        """Make popup window"""

        # shortcuts
        shortcuts_panel = wx.StaticText(self, -1, "Shortcuts")
        set_item_font(shortcuts_panel)

        disable_extraction = wx.StaticText(self, -1, "Enable/disable all data extraction")
        self.disable_extraction = make_checkbox(self, "")
        self.disable_extraction.SetValue(True)
        self.disable_extraction.Bind(wx.EVT_CHECKBOX, self.on_toggle)
        set_tooltip(self.disable_extraction, "")

        disable_popup = wx.StaticText(self, -1, "Enable/disable all popups")
        self.disable_popup = make_checkbox(self, "")
        self.disable_popup.SetValue(True)
        self.disable_popup.Bind(wx.EVT_CHECKBOX, self.on_toggle)
        set_tooltip(self.disable_popup, "")

        # mass spectrum panel
        ms_panel = wx.StaticText(self, -1, "Panel: Mass spectrum")
        set_item_font(ms_panel)

        ms_extract_heatmap = wx.StaticText(self, -1, "Allow extraction of ion heatmap when CTRL+drag in mass spectrum:")
        self.ms_extract_heatmap = make_checkbox(self, "")
        self.ms_extract_heatmap.SetValue(CONFIG.plot_panel_ms_extract_heatmap)
        self.ms_extract_heatmap.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.ms_extract_heatmap, "")

        ms_show_heatmap_popup = wx.StaticText(self, -1, "Show ion heatmap popup window after data extraction:")
        self.ms_show_heatmap_popup = make_checkbox(self, "")
        self.ms_show_heatmap_popup.SetValue(CONFIG.plot_panel_ms_extract_heatmap_popup)
        self.ms_show_heatmap_popup.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.ms_show_heatmap_popup, "")

        ms_extract_rt = wx.StaticText(self, -1, "Allow extraction of ion chromatogram when CTRL+drag in mass spectrum:")
        self.ms_extract_rt = make_checkbox(self, "")
        self.ms_extract_rt.SetValue(CONFIG.plot_panel_ms_extract_rt)
        self.ms_extract_rt.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.ms_extract_rt, "")

        ms_show_rt_popup = wx.StaticText(self, -1, "Show chromatogram popup window after data extraction:")
        self.ms_show_rt_popup = make_checkbox(self, "")
        self.ms_show_rt_popup.SetValue(CONFIG.plot_panel_ms_extract_rt_popup)
        self.ms_show_rt_popup.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.ms_show_rt_popup, "")

        ms_extract_dt = wx.StaticText(self, -1, "Allow extraction of ion mobilogram when CTRL+drag in mass spectrum:")
        self.ms_extract_dt = make_checkbox(self, "")
        self.ms_extract_dt.SetValue(CONFIG.plot_panel_ms_extract_dt)
        self.ms_extract_dt.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.ms_extract_dt, "")

        ms_show_dt_popup = wx.StaticText(self, -1, "Show mobilogram popup window after data extraction:")
        self.ms_show_dt_popup = make_checkbox(self, "")
        self.ms_show_dt_popup.SetValue(CONFIG.plot_panel_ms_extract_dt_popup)
        self.ms_show_dt_popup.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.ms_show_dt_popup, "")

        # chromatogram panel
        rt_panel = wx.StaticText(self, -1, "Panel: Chromatogram")
        set_item_font(rt_panel)

        rt_extract_ms = wx.StaticText(self, -1, "Allow extraction of mass spectrum when CTRL+drag in chromatogram:")
        self.rt_extract_ms = make_checkbox(self, "")
        self.rt_extract_ms.SetValue(CONFIG.plot_panel_rt_extract_ms)
        self.rt_extract_ms.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.rt_extract_ms, "")

        rt_show_ms_popup = wx.StaticText(self, -1, "Show mass spectrum popup window after data extraction:")
        self.rt_show_ms_popup = make_checkbox(self, "")
        self.rt_show_ms_popup.SetValue(CONFIG.plot_panel_rt_extract_ms_popup)
        self.rt_show_ms_popup.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.rt_show_ms_popup, "")

        # mobilogram panel
        dt_panel = wx.StaticText(self, -1, "Panel: Mobilogram")
        set_item_font(dt_panel)

        dt_extract_ms = wx.StaticText(self, -1, "Allow extraction of mass spectrum when CTRL+drag in mobilogram:")
        self.dt_extract_ms = make_checkbox(self, "")
        self.dt_extract_ms.SetValue(CONFIG.plot_panel_dt_extract_ms)
        self.dt_extract_ms.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.dt_extract_ms, "")

        dt_show_ms_popup = wx.StaticText(self, -1, "Show mass spectrum popup window after data extraction:")
        self.dt_show_ms_popup = make_checkbox(self, "")
        self.dt_show_ms_popup.SetValue(CONFIG.plot_panel_dt_extract_ms_popup)
        self.dt_show_ms_popup.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.rt_show_ms_popup, "")

        # heatmap panel
        heatmap_panel = wx.StaticText(self, -1, "Panel: Heatmap")
        set_item_font(heatmap_panel)

        heatmap_extract_ms = wx.StaticText(self, -1, "Allow extraction of mass spectrum when CTRL+drag in heatmap:")
        self.heatmap_extract_ms = make_checkbox(self, "")
        self.heatmap_extract_ms.SetValue(CONFIG.plot_panel_heatmap_extract_ms)
        self.heatmap_extract_ms.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.heatmap_extract_ms, "")

        heatmap_show_ms_popup = wx.StaticText(self, -1, "Show mass spectrum popup window after data extraction:")
        self.heatmap_show_ms_popup = make_checkbox(self, "")
        self.heatmap_show_ms_popup.SetValue(CONFIG.plot_panel_heatmap_extract_ms_popup)
        self.heatmap_show_ms_popup.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.heatmap_show_ms_popup, "")

        heatmap_extract_rt = wx.StaticText(self, -1, "Allow extraction of mass spectrum when CTRL+drag in heatmap:")
        self.heatmap_extract_rt = make_checkbox(self, "")
        self.heatmap_extract_rt.SetValue(CONFIG.plot_panel_heatmap_extract_rt)
        self.heatmap_extract_rt.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.heatmap_extract_rt, "")

        heatmap_show_rt_popup = wx.StaticText(self, -1, "Show mass spectrum popup window after data extraction:")
        self.heatmap_show_rt_popup = make_checkbox(self, "")
        self.heatmap_show_rt_popup.SetValue(CONFIG.plot_panel_heatmap_extract_rt_popup)
        self.heatmap_show_rt_popup.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.heatmap_show_rt_popup, "")

        # dt/ms panel
        dtms_panel = wx.StaticText(self, -1, "Panel: DT/MS")
        set_item_font(dtms_panel)

        dtms_extract_rt = wx.StaticText(self, -1, "Allow extraction of chromatogram when CTRL+drag in DT/MS:")
        self.dtms_extract_rt = make_checkbox(self, "")
        self.dtms_extract_rt.SetValue(CONFIG.plot_panel_dtms_extract_rt)
        self.dtms_extract_rt.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.dtms_extract_rt, "")

        dtms_show_rt_popup = wx.StaticText(self, -1, "Show chromatogram popup window after data extraction:")
        self.dtms_show_rt_popup = make_checkbox(self, "")
        self.dtms_show_rt_popup.SetValue(CONFIG.plot_panel_dtms_extract_rt_popup)
        self.dtms_show_rt_popup.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.dtms_show_rt_popup, "")

        n_col = 2
        grid = wx.GridBagSizer(2, 2)
        # mass spectrum panel
        n = 0
        grid.Add(shortcuts_panel, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(disable_extraction, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.disable_extraction, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(disable_popup, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.disable_popup, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_panel, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_extract_heatmap, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_extract_heatmap, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_show_heatmap_popup, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_show_heatmap_popup, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_extract_rt, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_extract_rt, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_show_rt_popup, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_show_rt_popup, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_extract_dt, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_extract_dt, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_show_dt_popup, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_show_dt_popup, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        # chromatogram panel
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(rt_panel, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(rt_extract_ms, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rt_extract_ms, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rt_show_ms_popup, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rt_show_ms_popup, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        # mobilogram panel
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(dt_panel, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(dt_extract_ms, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.dt_extract_ms, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(dt_show_ms_popup, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.dt_show_ms_popup, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        # heatmap panel
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(heatmap_panel, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(heatmap_extract_ms, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.heatmap_extract_ms, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(heatmap_show_ms_popup, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.heatmap_show_ms_popup, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(heatmap_extract_rt, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.heatmap_extract_rt, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(heatmap_show_rt_popup, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.heatmap_show_rt_popup, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        # heatmap panel
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(dtms_panel, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(dtms_extract_rt, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.dtms_extract_rt, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(dtms_show_rt_popup, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.dtms_show_rt_popup, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        self.set_info(sizer)

        self.SetSizerAndFit(sizer)
        self.Layout()

    def on_toggle(self, _evt):
        """Quickly iterate through all objects"""
        disable_extraction = self.disable_extraction.GetValue()
        self.ms_extract_heatmap.SetValue(disable_extraction)
        self.ms_extract_rt.SetValue(disable_extraction)
        self.ms_extract_dt.SetValue(disable_extraction)
        self.rt_extract_ms.SetValue(disable_extraction)
        self.dt_extract_ms.SetValue(disable_extraction)
        self.heatmap_extract_ms.SetValue(disable_extraction)
        self.heatmap_extract_rt.SetValue(disable_extraction)
        self.dtms_extract_rt.SetValue(disable_extraction)

        disable_popup = self.disable_popup.GetValue()
        self.ms_show_heatmap_popup.SetValue(disable_popup)
        self.ms_show_rt_popup.SetValue(disable_popup)
        self.ms_show_dt_popup.SetValue(disable_popup)
        self.rt_show_ms_popup.SetValue(disable_popup)
        self.dt_show_ms_popup.SetValue(disable_popup)
        self.heatmap_show_ms_popup.SetValue(disable_popup)
        self.heatmap_show_rt_popup.SetValue(disable_popup)
        self.dtms_show_rt_popup.SetValue(disable_popup)

        self.on_apply(None)

    def on_apply(self, evt):
        """Update settings"""
        CONFIG.plot_panel_ms_extract_heatmap = self.ms_extract_heatmap.GetValue()
        CONFIG.plot_panel_ms_extract_heatmap_popup = self.ms_show_heatmap_popup.GetValue()
        CONFIG.plot_panel_ms_extract_rt = self.ms_extract_rt.GetValue()
        CONFIG.plot_panel_ms_extract_rt_popup = self.ms_show_rt_popup.GetValue()
        CONFIG.plot_panel_ms_extract_dt = self.ms_extract_dt.GetValue()
        CONFIG.plot_panel_ms_extract_dt_popup = self.ms_show_dt_popup.GetValue()

        CONFIG.plot_panel_rt_extract_ms = self.rt_extract_ms.GetValue()
        CONFIG.plot_panel_rt_extract_ms_popup = self.rt_show_ms_popup.GetValue()

        CONFIG.plot_panel_dt_extract_ms = self.dt_extract_ms.GetValue()
        CONFIG.plot_panel_dt_extract_ms_popup = self.dt_show_ms_popup.GetValue()

        CONFIG.plot_panel_heatmap_extract_ms = self.heatmap_extract_ms.GetValue()
        CONFIG.plot_panel_heatmap_extract_ms_popup = self.heatmap_show_ms_popup.GetValue()
        CONFIG.plot_panel_heatmap_extract_rt = self.heatmap_extract_rt.GetValue()
        CONFIG.plot_panel_heatmap_extract_rt_popup = self.heatmap_show_rt_popup.GetValue()

        CONFIG.plot_panel_dtms_extract_rt = self.dtms_extract_rt.GetValue()
        CONFIG.plot_panel_dtms_extract_rt_popup = self.dtms_show_rt_popup.GetValue()

        if evt is not None:
            evt.Skip()
