# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import wx
from styles import makeCheckbox


class dialog_customise_smart_zoom(wx.Dialog):
    """Dialog to control how smart-zoom behaves in the MS/DT panel"""

    def __init__(self, parent, presenter, config, **kwargs):
        wx.Dialog.__init__(
            self, parent, -1, 'Smart zoom settings...', size=(-1, -1),
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),
        )

        self.parent = parent
        self.presenter = presenter
        self.config = config

        self.make_gui()
        self.CentreOnScreen()
        self.SetFocus()

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def on_ok(self, evt):
        self.EndModal(wx.OK)

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 10)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def make_panel(self):
        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        visualisation_mode = wx.StaticText(panel, -1, 'Visualisation mode:')
        self.visualisation_mode = wx.Choice(
            panel, -1, choices=self.config.smart_zoom_view_mode_choices, size=(-1, -1),
        )
        self.visualisation_mode.SetStringSelection(self.config.smart_zoom_view_mode)
        self.visualisation_mode.Bind(wx.EVT_CHOICE, self.on_apply)
        self.visualisation_mode.Disable()

        hz_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        smart_zoom_check = wx.StaticText(panel, -1, 'Enable smart zoom:')
        self.smart_zoom_check = makeCheckbox(panel, '')
        self.smart_zoom_check.SetValue(self.config.smart_zoom_enable)
        self.smart_zoom_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        smart_zoom_downsampling_method = wx.StaticText(panel, -1, 'Downsampling method:')
        self.smart_zoom_downsampling_method = wx.Choice(
            panel, -1, choices=self.config.smart_zoom_downsampling_method_choices, size=(-1, -1),
        )
        self.smart_zoom_downsampling_method.SetStringSelection(self.config.smart_zoom_downsampling_method)
        self.smart_zoom_downsampling_method.Bind(wx.EVT_CHOICE, self.on_apply)

        smart_zoom_soft_max = wx.StaticText(panel, -1, 'Soft maximum:')
        self.smart_zoom_soft_max = wx.SpinCtrlDouble(
            panel, -1, value=str(self.config.smart_zoom_soft_max),
            min=1000, max=50000, initial=self.config.smart_zoom_soft_max, inc=2500, size=(-1, -1),
        )
        self.smart_zoom_soft_max.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        smart_zoom_hard_max = wx.StaticText(panel, -1, 'Hard maximum:')
        self.smart_zoom_hard_max = wx.SpinCtrlDouble(
            panel, -1, value=str(self.config.smart_zoom_hard_max),
            min=25000, max=200000, initial=self.config.smart_zoom_hard_max, inc=25000, size=(-1, -1),
        )
        self.smart_zoom_hard_max.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        smart_zoom_min_search = wx.StaticText(panel, -1, 'Minimum m/z division range:')
        self.smart_zoom_min_search = wx.SpinCtrlDouble(
            panel, -1, value=str(self.config.smart_zoom_min_search),
            min=1, max=100, initial=self.config.smart_zoom_min_search, inc=1, size=(-1, -1),
        )
        self.smart_zoom_min_search.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        smart_zoom_max_search = wx.StaticText(panel, -1, 'Maximum m/z division range:')
        self.smart_zoom_max_search = wx.SpinCtrlDouble(
            panel, -1, value=str(self.config.smart_zoom_max_search),
            min=1, max=100, initial=self.config.smart_zoom_max_search, inc=1, size=(-1, -1),
        )
        self.smart_zoom_max_search.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        hz_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        smart_zoom_subsample_default = wx.StaticText(panel, -1, 'Sub-sample default:')
        self.smart_zoom_subsample_default = wx.SpinCtrlDouble(
            panel, -1, value=str(self.config.smart_zoom_subsample_default),
            min=2, max=100, initial=self.config.smart_zoom_subsample_default, inc=1, size=(-1, -1),
        )
        self.smart_zoom_subsample_default.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(visualisation_mode, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.visualisation_mode, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(hz_line_1, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        grid.Add(smart_zoom_check, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.smart_zoom_check, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(hz_line_2, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        grid.Add(
            smart_zoom_downsampling_method, (y, 0), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(
            self.smart_zoom_downsampling_method, (y, 1), wx.GBSpan(
                1, 1,
            ), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL,
        )
        y = y + 1
        grid.Add(smart_zoom_soft_max, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.smart_zoom_soft_max, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(smart_zoom_hard_max, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.smart_zoom_hard_max, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(smart_zoom_min_search, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.smart_zoom_min_search, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(smart_zoom_max_search, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.smart_zoom_max_search, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(smart_zoom_subsample_default, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.smart_zoom_subsample_default, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def on_apply(self, evt):

        self.config.smart_zoom_downsampling_method = self.smart_zoom_downsampling_method.GetStringSelection()
        self.config.smart_zoom_view_mode = self.visualisation_mode.GetStringSelection()

        self.config.smart_zoom_enable = self.smart_zoom_check.GetValue()
        self.config.smart_zoom_soft_max = int(self.smart_zoom_soft_max.GetValue())
        self.config.smart_zoom_hard_max = int(self.smart_zoom_hard_max.GetValue())
        self.config.smart_zoom_min_search = int(self.smart_zoom_min_search.GetValue())
        self.config.smart_zoom_max_search = int(self.smart_zoom_max_search.GetValue())
        self.config.smart_zoom_subsample_default = int(self.smart_zoom_subsample_default.GetValue())
