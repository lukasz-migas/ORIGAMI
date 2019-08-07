# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import wx
from help_documentation import OrigamiHelp
from styles import makeCheckbox


class panelExportSettings(wx.MiniFrame):
    def __init__(self, parent, presenter, config, icons, **kwargs):
        wx.MiniFrame.__init__(
            self,
            parent,
            -1,
            "Import/Export parameters",
            size=(-1, -1),
            style=(wx.DEFAULT_FRAME_STYLE | wx.MAXIMIZE_BOX | wx.CLOSE_BOX),
        )

        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons
        self.help = OrigamiHelp()

        self.importEvent = False
        self.windowSizes = {"Peaklist": (250, 110), "Image": (250, 150), "Files": (310, 140)}

        # make gui items
        self.make_gui()
        self.mainBook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed)
        self.mainBook.SetSelection(self.config.importExportParamsWindow[kwargs["window"]])

        # bind
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

        self.main_sizer.Fit(self)
        self.Centre()
        self.Layout()
        self.Show(True)
        self.SetFocus()

        # fire-up start events
        self.on_page_changed(evt=None)
        self.on_toggle_controls(evt=None)

    def on_key_event(self, evt):
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)

        if evt is not None:
            evt.Skip()

    def on_page_changed(self, evt):
        self.currentPage = self.mainBook.GetPageText(self.mainBook.GetSelection())
        self.SetSize(self.windowSizes[self.currentPage])
        self.Layout()

    def onSetPage(self, **kwargs):
        self.mainBook.SetSelection(self.config.importExportParamsWindow[kwargs["window"]])
        self.on_page_changed(evt=None)

    def onSelect(self, evt):
        self.Destroy()

    def on_close(self, evt):
        """Destroy this frame."""
        self.config.importExportParamsWindow_on_off = False
        self.Destroy()

    # ----

    def make_gui(self):

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        # Setup notebook
        self.mainBook = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.NB_MULTILINE)

        self.parameters_peaklist = wx.Panel(
            self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL
        )
        self.mainBook.AddPage(self.make_panel_Peaklist(self.parameters_peaklist), "Peaklist", False)
        # ------
        self.parameters_image = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.make_panel_Image(self.parameters_image), "Image", False)
        # ------
        self.parameters_files = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.make_panel_Files(self.parameters_files), "Files", False)

        self.main_sizer.Add(self.mainBook, 1, wx.EXPAND | wx.ALL, 2)

        # setup color
        self.mainBook.SetBackgroundColour((240, 240, 240))

    def make_panel_Peaklist(self, panel):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        useInternal_label = wx.StaticText(panel, wx.ID_ANY, "Override imported values:")
        self.peaklist_useInternalWindow_check = makeCheckbox(panel, "")
        self.peaklist_useInternalWindow_check.SetValue(self.config.useInternalMZwindow)
        self.peaklist_useInternalWindow_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.peaklist_useInternalWindow_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        windowSize_label = wx.StaticText(panel, wx.ID_ANY, "± m/z (Da):")
        self.peaklist_windowSize_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.5, max=50, initial=0, inc=1, size=(60, -1)
        )
        self.peaklist_windowSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.peaklist_windowSize_value.SetValue(self.config.mzWindowSize)

        # add to grid
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(useInternal_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.peaklist_useInternalWindow_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(windowSize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.peaklist_windowSize_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        main_sizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_panel_Image(self, panel):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        fileFormat_label = wx.StaticText(panel, wx.ID_ANY, "File format:")
        self.image_fileFormat_choice = wx.Choice(panel, -1, choices=self.config.imageFormatType, size=(-1, -1))
        self.image_fileFormat_choice.SetStringSelection(self.config.imageFormat)
        self.image_fileFormat_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        resolution_label = wx.StaticText(panel, wx.ID_ANY, "Resolution:")
        self.image_resolution = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=50, max=600, initial=0, inc=50, size=(60, -1)
        )
        self.image_resolution.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.image_resolution.SetValue(self.config.dpi)

        transparency_label = wx.StaticText(panel, wx.ID_ANY, "Transparent:")
        self.image_transparency_check = makeCheckbox(panel, "")
        self.image_transparency_check.SetValue(self.config.transparent)
        self.image_transparency_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        resize_label = wx.StaticText(panel, wx.ID_ANY, "Resize:")
        self.image_resize_check = makeCheckbox(panel, "")
        self.image_resize_check.SetValue(self.config.resize)
        self.image_resize_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        # add to grid
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(fileFormat_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.image_fileFormat_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(resolution_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.image_resolution, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.image_transparency_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(resize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.image_resize_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        main_sizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_panel_Files(self, panel):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        delimiter_label = wx.StaticText(panel, wx.ID_ANY, "Delimiter:")
        self.file_delimiter_choice = wx.Choice(
            panel, -1, choices=list(self.config.textOutputDict.keys()), size=(-1, -1)
        )
        self.file_delimiter_choice.SetStringSelection(self.config.saveDelimiterTXT)
        self.file_delimiter_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        default_name_label = wx.StaticText(panel, wx.ID_ANY, "Default name:")
        self.file_default_name_choice = wx.Choice(
            panel, -1, choices=sorted(self.config._plotSettings.keys()), size=(-1, -1)
        )
        self.file_default_name_choice.SetSelection(0)
        self.file_default_name_choice.Bind(wx.EVT_CHOICE, self.onSetupPlotName)

        self.file_default_name = wx.TextCtrl(panel, -1, "", size=(210, -1))
        self.file_default_name.SetValue(
            self.config._plotSettings[self.file_default_name_choice.GetStringSelection()]["default_name"]
        )
        self.file_default_name.Bind(wx.EVT_TEXT, self.on_apply)

        # add to grid
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(delimiter_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.file_delimiter_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(default_name_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.file_default_name_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(
            self.file_default_name, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND
        )
        main_sizer.Add(grid, 0, wx.ALIGN_LEFT, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_apply(self, evt):

        # prevent updating config
        if self.importEvent:
            return

        # Peaklist
        self.config.useInternalMZwindow = self.peaklist_useInternalWindow_check.GetValue()
        self.config.mzWindowSize = self.peaklist_windowSize_value.GetValue()

        # Images
        self.config.dpi = self.image_resolution.GetValue()
        self.config.transparent = self.image_transparency_check.GetValue()
        self.config.resize = self.image_resize_check.GetValue()
        self.config.imageFormat = self.image_fileFormat_choice.GetStringSelection()

        # Files
        self.config.saveDelimiterTXT = self.file_delimiter_choice.GetStringSelection()
        self.config.saveDelimiter = self.config.textOutputDict[self.config.saveDelimiterTXT]
        self.config.saveExtension = self.config.textExtensionDict[self.config.saveDelimiterTXT]

    def on_toggle_controls(self, evt):
        self.config.useInternalMZwindow = self.peaklist_useInternalWindow_check.GetValue()

        if self.config.useInternalMZwindow:
            self.peaklist_windowSize_value.Enable()
        else:
            self.peaklist_windowSize_value.Disable()

        if evt is not None:
            evt.Skip()

    def onSetupPlotName(self, evt):
        # get current plot name
        plotName = self.file_default_name_choice.GetStringSelection()
        # get name
        plotName = self.config._plotSettings[plotName]["default_name"]

        self.file_default_name.SetValue(plotName)
