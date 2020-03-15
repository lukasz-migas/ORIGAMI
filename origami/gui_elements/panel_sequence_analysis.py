# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
# Third-party imports
# Third-party imports
# Third-party imports
import wx

# Local imports
from origami.help_documentation import OrigamiHelp


class panelSequenceAnalysis(wx.MiniFrame):
    """
    Simple GUI to view and analyse sequences
    """

    def __init__(self, parent, presenter, config, icons):
        wx.MiniFrame.__init__(
            self, parent, -1, "Sequence analysis...", size=(-1, -1), style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER
        )

        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons

        self.help = OrigamiHelp()

        # make gui items
        self.make_gui()

        self.Centre()
        self.Layout()
        self.SetFocus()

        # bind
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

    # ----

    def on_key_event(self, evt):
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)
        elif key_code == 83:  # key = s
            self.onSelect(evt=None)
        elif key_code == 85:  # key = u
            self.onPlot(evt=None)

        evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""

        self.Destroy()

    # ----

    def onSelect(self, evt):

        self.Destroy()

    def onPlot(self, evt):
        """
        Update plot with currently selected PCs
        """
        pass

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 1, wx.EXPAND, 5)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

    def make_panel(self):

        panel = wx.Panel(self, -1, size=(-1, -1))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # make editor
        title_label = wx.StaticText(panel, -1, "Title::")
        self.title_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), style=wx.BORDER_SUNKEN)

        sequence_label = wx.StaticText(panel, -1, "Sequence:")
        self.sequence_value = wx.TextCtrl(panel, -1, "", size=(400, 200), style=wx.BORDER_SUNKEN)

        self.sequence_loadBtn = wx.BitmapButton(
            panel,
            wx.ID_ANY,
            self.icons.iconsLib["load16"],
            size=(26, 26),
            style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )

        self.sequence_converter = wx.BitmapButton(
            panel,
            wx.ID_ANY,
            self.icons.iconsLib["aa3to1_16"],  # change to 3 <-> 1
            size=(26, 26),
            style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )

        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        vertical_line_1 = wx.StaticLine(panel, -1, style=wx.LI_VERTICAL)
        vertical_line_2 = wx.StaticLine(panel, -1, style=wx.LI_VERTICAL)
        vertical_line_3 = wx.StaticLine(panel, -1, style=wx.LI_VERTICAL)
        vertical_line_4 = wx.StaticLine(panel, -1, style=wx.LI_VERTICAL)

        LABEL_SIZE = (100, -1)
        TEXT_SIZE = (60, -1)
        length_label = wx.StaticText(panel, -1, "Length:", size=LABEL_SIZE)
        mw_label = wx.StaticText(panel, -1, "Av. mass:", size=LABEL_SIZE)
        pI_label = wx.StaticText(panel, -1, "pI:", size=LABEL_SIZE)

        self.length_value = wx.StaticText(panel, -1, "", size=TEXT_SIZE)
        self.mw_value = wx.StaticText(panel, -1, "", size=TEXT_SIZE)
        self.pI_value = wx.StaticText(panel, -1, "", size=(50, -1))

        minCCS_label = wx.StaticText(panel, -1, "Compact CCS (Å²):", size=LABEL_SIZE)
        maxCCS_label = wx.StaticText(panel, -1, "Extended CCS (Å²):", size=LABEL_SIZE)
        kappa_label = wx.StaticText(panel, -1, "κ value:", size=(50, -1))

        self.minCCS_value = wx.StaticText(panel, -1, "", size=TEXT_SIZE)
        self.maxCCS_value = wx.StaticText(panel, -1, "", size=TEXT_SIZE)
        self.kappa_value = wx.StaticText(panel, -1, "", size=TEXT_SIZE)

        # make buttons
        self.calculateBtn = wx.Button(panel, wx.ID_OK, "Calculate", size=(-1, 22))
        self.plotBtn = wx.Button(panel, wx.ID_OK, "Plot", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))

        self.calculateBtn.Bind(wx.EVT_BUTTON, self.onSelect)
        self.plotBtn.Bind(wx.EVT_BUTTON, self.onPlot)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.GridBagSizer(5, 5)
        y = 0
        btn_grid.Add(self.calculateBtn, (y, 0), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.plotBtn, (y, 1), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.cancelBtn, (y, 2), flag=wx.ALIGN_CENTER)

        info_grid = wx.GridBagSizer(5, 5)
        y = 0
        info_grid.Add(length_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        info_grid.Add(self.length_value, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        info_grid.Add(vertical_line_1, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        info_grid.Add(mw_label, (y, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        info_grid.Add(self.mw_value, (y, 4), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        info_grid.Add(vertical_line_2, (y, 5), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND | wx.ALIGN_LEFT)
        info_grid.Add(pI_label, (y, 6), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        info_grid.Add(self.pI_value, (y, 7), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        y += 1
        info_grid.Add(minCCS_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        info_grid.Add(self.minCCS_value, (y, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        info_grid.Add(vertical_line_3, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        info_grid.Add(maxCCS_label, (y, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        info_grid.Add(self.maxCCS_value, (y, 4), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        info_grid.Add(vertical_line_4, (y, 5), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        info_grid.Add(kappa_label, (y, 6), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        info_grid.Add(self.kappa_value, (y, 7), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(title_label, (y, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_TOP)
        grid.Add(self.title_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(sequence_label, (y, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_TOP)
        grid.Add(self.sequence_value, (y, 1), wx.GBSpan(2, 6), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.sequence_loadBtn, (y, 7), flag=wx.ALIGN_LEFT | wx.ALIGN_TOP)
        y += 1
        grid.Add(self.sequence_converter, (y, 7), flag=wx.ALIGN_LEFT | wx.ALIGN_TOP)
        y += 1
        grid.Add(horizontal_line, (y, 0), wx.GBSpan(1, 8), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        y += 1
        grid.Add(info_grid, (y, 0), wx.GBSpan(1, 8), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        y += 1
        grid.Add(btn_grid, (y, 0), wx.GBSpan(1, 8), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)

        main_sizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def updateMS(self, evt):
        pass

        if evt is not None:
            evt.Skip()
