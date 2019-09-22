# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import wx
from styles import Dialog
from styles import make_checkbox


class dialog_customise_smart_zoom(Dialog):
    """Dialog to control how smart-zoom behaves in the MS/DT panel"""

    def __init__(self, parent, presenter, config, **kwargs):
        Dialog.__init__(self, parent, title="Smart zoom settings...")

        self.parent = parent
        self.presenter = presenter
        self.config = config

        self.make_gui()
        self.CentreOnScreen()
        self.SetFocus()

        self.on_toggle_controls(None)

    def on_ok(self, evt):
        self.EndModal(wx.OK)

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 1, wx.EXPAND, 10)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

    def make_panel(self):
        panel = wx.Panel(self, -1)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        visualisation_mode = wx.StaticText(panel, -1, "Visualisation mode:")
        self.visualisation_mode = wx.Choice(panel, -1, choices=self.config.smart_zoom_view_mode_choices, size=(-1, -1))
        self.visualisation_mode.SetStringSelection(self.config.smart_zoom_view_mode)
        self.visualisation_mode.Bind(wx.EVT_CHOICE, self.on_apply)
        self.visualisation_mode.Disable()

        hz_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        smart_zoom_check = wx.StaticText(panel, -1, "Enable smart zoom:")
        self.smart_zoom_check = make_checkbox(panel, "")
        self.smart_zoom_check.SetValue(self.config.smart_zoom_enable)
        self.smart_zoom_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.smart_zoom_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        smart_zoom_downsampling_method = wx.StaticText(panel, -1, "Downsampling method:")
        self.smart_zoom_downsampling_method = wx.Choice(
            panel, -1, choices=self.config.smart_zoom_downsampling_method_choices, size=(-1, -1)
        )
        self.smart_zoom_downsampling_method.SetStringSelection(self.config.smart_zoom_downsampling_method)
        self.smart_zoom_downsampling_method.Bind(wx.EVT_CHOICE, self.on_apply)

        smart_zoom_soft_max = wx.StaticText(panel, -1, "Soft maximum:")
        self.smart_zoom_soft_max = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(self.config.smart_zoom_soft_max),
            min=1000,
            max=50000,
            initial=self.config.smart_zoom_soft_max,
            inc=2500,
            size=(-1, -1),
        )
        self.smart_zoom_soft_max.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        smart_zoom_hard_max = wx.StaticText(panel, -1, "Hard maximum:")
        self.smart_zoom_hard_max = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(self.config.smart_zoom_hard_max),
            min=25000,
            max=200000,
            initial=self.config.smart_zoom_hard_max,
            inc=25000,
            size=(-1, -1),
        )
        self.smart_zoom_hard_max.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        smart_zoom_min_search = wx.StaticText(panel, -1, "Minimum m/z division range:")
        self.smart_zoom_min_search = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(self.config.smart_zoom_min_search),
            min=1,
            max=100,
            initial=self.config.smart_zoom_min_search,
            inc=1,
            size=(-1, -1),
        )
        self.smart_zoom_min_search.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        smart_zoom_max_search = wx.StaticText(panel, -1, "Maximum m/z division range:")
        self.smart_zoom_max_search = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(self.config.smart_zoom_max_search),
            min=1,
            max=100,
            initial=self.config.smart_zoom_max_search,
            inc=1,
            size=(-1, -1),
        )
        self.smart_zoom_max_search.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        hz_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        smart_zoom_subsample_default = wx.StaticText(panel, -1, "Sub-sample default:")
        self.smart_zoom_subsample_default = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(self.config.smart_zoom_subsample_default),
            min=2,
            max=100,
            initial=self.config.smart_zoom_subsample_default,
            inc=1,
            size=(-1, -1),
        )
        self.smart_zoom_subsample_default.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(visualisation_mode, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.visualisation_mode, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(hz_line_1, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(smart_zoom_check, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.smart_zoom_check, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(hz_line_2, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y += 1
        grid.Add(smart_zoom_downsampling_method, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.smart_zoom_downsampling_method, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(smart_zoom_soft_max, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.smart_zoom_soft_max, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(smart_zoom_hard_max, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.smart_zoom_hard_max, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(smart_zoom_min_search, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.smart_zoom_min_search, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(smart_zoom_max_search, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.smart_zoom_max_search, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(smart_zoom_subsample_default, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.smart_zoom_subsample_default, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

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

        if evt is not None:
            evt.Skip()

    def on_toggle_controls(self, evt):
        self.config.smart_zoom_enable = self.smart_zoom_check.GetValue()

        for obj in [
            self.smart_zoom_downsampling_method,
            self.smart_zoom_soft_max,
            self.smart_zoom_hard_max,
            self.smart_zoom_min_search,
            self.smart_zoom_max_search,
            self.smart_zoom_subsample_default,
        ]:
            obj.Enable(self.config.smart_zoom_enable)

        if evt is not None:
            evt.Skip()
