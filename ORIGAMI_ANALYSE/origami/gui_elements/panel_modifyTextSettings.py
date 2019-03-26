import wx

from icons import IconContainer as icons
from styles import makeCheckbox, validator
from toolbox import num2str


class panelModifyTextSettings(wx.MiniFrame):
    """
    Small panel to modify settings in the Text panel
    """

    def __init__(self, parent, presenter, config, **kwargs):
        wx.MiniFrame.__init__(self, parent, -1, 'Modify settings...', size=(-1, -1),
                              style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER)

        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons()
        self.importEvent = False

        self.SetTitle(kwargs.get('document', "filename"))
        self.itemInfo = kwargs

        # check values
        if self.itemInfo['mask'] in ['', None, 'None']:
            self.itemInfo['mask'] = 1

        if self.itemInfo['alpha'] in ['', None, 'None']:
            self.itemInfo['alpha'] = 1

        if self.itemInfo['colormap'] in ['', None, 'None']:
            self.itemInfo['colormap'] = self.config.currentCmap

        if self.itemInfo['color'][0] == -1:
            self.itemInfo['color'] = (1, 1, 1, 255)

        if self.itemInfo['charge'] in ['', None, 'None']:
            self.itemInfo['charge'] = ""

        # make gui items
        self.makeGUI()

        self.Centre()
        self.Layout()
        self.SetFocus()

        # bind
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)

        # fire-up events
        self.onSetupParameters(evt=None)
    # ----

    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE:
            self.onClose(evt=None)

        evt.Skip()

    def onClose(self, evt):
        """Destroy this frame."""
        self.Destroy()
    # ----

    def onSelect(self, evt):
        self.onCheckID()
        self.OnAssignColor(evt=None)
        self.parent.onUpdateDocument(itemInfo=self.itemInfo, evt=None)
        self.Destroy()

    def makeGUI(self):

        # make panel
        panel = self.makePanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 0)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makePanel(self):

        panel = wx.Panel(self, -1, size=(-1, -1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        select_label = wx.StaticText(panel, wx.ID_ANY, "Select:")
        self.text_select_value = makeCheckbox(panel, "")
        self.text_select_value.Bind(wx.EVT_CHECKBOX, self.onApply)

        filename_label = wx.StaticText(panel, wx.ID_ANY, "Filename:")
        self.text_filename_value = wx.TextCtrl(panel, wx.ID_ANY, "", style=wx.TE_READONLY)

        ion_label = wx.StaticText(panel, wx.ID_ANY, "Ion:")
        self.text_ion_value = wx.TextCtrl(panel, wx.ID_ANY, "", style=wx.TE_READONLY)

        label_label = wx.StaticText(panel, wx.ID_ANY,
                                    "Label:", wx.DefaultPosition,
                                    wx.DefaultSize, wx.ALIGN_LEFT)
        self.text_label_value = wx.TextCtrl(panel, -1, "", size=(90, -1))
        self.text_label_value.SetValue(self.itemInfo['label'])
        self.text_label_value.Bind(wx.EVT_TEXT, self.onApply)

        charge_label = wx.StaticText(panel, wx.ID_ANY, "Charge:")
        self.text_charge_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.text_charge_value.Bind(wx.EVT_TEXT, self.onApply)

        min_threshold_label = wx.StaticText(panel, wx.ID_ANY, "Min threshold:")
        self.text_min_threshold_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                            value="1", min=0.0, max=1.0,
                                            initial=1.0, inc=0.05, size=(60, -1))
        self.text_min_threshold_value.SetValue(self.itemInfo['min_threshold'])
        self.text_min_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        max_threshold_label = wx.StaticText(panel, wx.ID_ANY, "Max threshold:")
        self.text_max_threshold_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                            value="1", min=0.0, max=1.0,
                                            initial=1.0, inc=0.05, size=(60, -1))
        self.text_max_threshold_value.SetValue(self.itemInfo['max_threshold'])
        self.text_max_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        mask_label = wx.StaticText(panel, wx.ID_ANY, "Mask:")
        self.text_mask_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                            value="1", min=0.0, max=1.0,
                                            initial=1.0, inc=0.05, size=(60, -1))
        self.text_mask_value.SetValue(self.itemInfo['mask'])
        self.text_mask_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        transparency_label = wx.StaticText(panel, wx.ID_ANY, "Transparency:")
        self.text_transparency_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                    value="1", min=0.0, max=1.0,
                                                    initial=1.0, inc=0.05, size=(60, -1))
        self.text_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        colormap_label = wx.StaticText(panel, -1, "Colormap:")
        self.text_colormap_value = wx.Choice(panel, -1,
                                               choices=self.config.cmaps2,
                                               size=(-1, -1))
        self.text_colormap_value.Bind(wx.EVT_CHOICE, self.onApply)

        self.text_restrictColormap_value = makeCheckbox(panel, "")
        self.text_restrictColormap_value.Bind(wx.EVT_CHECKBOX, self.onRestrictCmaps)

        color_label = wx.StaticText(panel, -1, "Color:")
        self.text_color_value = wx.Button(panel, wx.ID_ANY, "", wx.DefaultPosition,
                                          wx.Size(26, 26), 0)
        self.text_color_value.SetBackgroundColour(self.itemInfo['color'])
        self.text_color_value.Bind(wx.EVT_BUTTON, self.OnAssignColor)

        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.showBtn = wx.Button(panel, wx.ID_OK, "Show", size=(-1, 22))
        self.previousBtn = wx.Button(panel, wx.ID_OK, "Previous", size=(-1, 22))
        self.nextBtn = wx.Button(panel, wx.ID_OK, "Next", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Close", size=(-1, 22))

        self.showBtn.Bind(wx.EVT_BUTTON, self.onShow)
        self.nextBtn.Bind(wx.EVT_BUTTON, self.onGetNext)
        self.previousBtn.Bind(wx.EVT_BUTTON, self.onGetPrevious)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.showBtn, (n, 0), wx.GBSpan(1, 1))
        btn_grid.Add(self.previousBtn, (n, 1), wx.GBSpan(1, 1))
        btn_grid.Add(self.nextBtn, (n, 2), wx.GBSpan(1, 1))
        btn_grid.Add(self.cancelBtn, (n, 3), wx.GBSpan(1, 1))

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(select_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.text_select_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(filename_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.text_filename_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(ion_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.text_ion_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(label_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.text_label_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(charge_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.text_charge_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(min_threshold_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.text_min_threshold_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(max_threshold_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.text_max_threshold_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(colormap_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.text_colormap_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.text_restrictColormap_value, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(color_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.text_color_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(mask_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.text_mask_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(transparency_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.text_transparency_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n = n + 1
        grid.Add(btn_grid, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        self.enableDisableBoxes(evt=None)

        return panel

    def onShow(self, evt):
        self.parent.on_plot(evt=None, itemID=self.itemInfo['id'])

    def onApply(self, evt):
        self.onCheckID()
        if self.importEvent: return
        self.parent.peaklist.CheckItem(self.itemInfo['id'], self.text_select_value.GetValue())
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.textlistColNames['charge'],
                                           self.text_charge_value.GetValue())
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.textlistColNames['colormap'],
                                           self.text_colormap_value.GetStringSelection())
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.textlistColNames['mask'],
                                           num2str(self.text_mask_value.GetValue()))
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.textlistColNames['alpha'],
                                           num2str(self.text_transparency_value.GetValue()))
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.textlistColNames['label'],
                                           self.text_label_value.GetValue())

        # update ion information
        self.itemInfo['charge'] = self.text_charge_value.GetValue()
        self.itemInfo['colormap'] = self.text_colormap_value.GetStringSelection()
        self.itemInfo['mask'] = self.text_mask_value.GetValue()
        self.itemInfo['alpha'] = self.text_transparency_value.GetValue()
        self.itemInfo['label'] = self.text_label_value.GetValue()
        self.itemInfo['min_threshold'] = self.text_min_threshold_value.GetValue()
        self.itemInfo['max_threshold'] = self.text_max_threshold_value.GetValue()

        # update ion value

        self.OnAssignColor(evt=None)
        self.parent.onUpdateDocument(itemInfo=self.itemInfo, evt=None)

        if evt != None:
            evt.Skip()

    def onSetupParameters(self, evt):
        self.importEvent = True
        self.text_select_value.SetValue(self.itemInfo['select'])
        self.text_filename_value.SetValue(self.itemInfo['document'])

        self.text_charge_value.SetValue(str(self.itemInfo['charge']))
        self.text_label_value.SetValue(self.itemInfo['label'])
        self.text_colormap_value.SetStringSelection(self.itemInfo['colormap'])
        self.text_mask_value.SetValue(self.itemInfo['mask'])
        self.text_transparency_value.SetValue(self.itemInfo['alpha'])
        self.text_color_value.SetBackgroundColour(self.itemInfo['color'])
        self.text_min_threshold_value.SetValue(self.itemInfo['min_threshold'])
        self.text_max_threshold_value.SetValue(self.itemInfo['max_threshold'])

        self.enableDisableBoxes(evt=None)
        self.importEvent = False

    def onUpdateGUI(self, itemInfo):
        """
        @param itemInfo (dict): updating GUI with new item information
        """
        self.itemInfo = itemInfo
        self.SetTitle(self.itemInfo['document'])

        # check values
        if self.itemInfo['mask'] in ['', None, 'None']:
            self.itemInfo['mask'] = 1

        if self.itemInfo['alpha'] in ['', None, 'None']:
            self.itemInfo['alpha'] = 1

        if self.itemInfo['colormap'] in ['', None, 'None']:
            self.itemInfo['colormap'] = self.config.currentCmap

        if self.itemInfo['color'][0] == -1:
              self.itemInfo['color'] = (1, 1, 1, 255)

        if self.itemInfo['charge'] in ['', None, 'None']:
            self.itemInfo['charge'] = ""

        # setup values
        self.onSetupParameters(evt=None)

        self.SetFocus()

    def enableDisableBoxes(self, evt):

        enableList, disableList = [], []

        for item in enableList:
            item.Enable()
        for item in disableList:
            item.Disable()

        if evt != None:
            evt.Skip()

    def OnAssignColor(self, evt):
        self.onCheckID()
        if evt:
            color = self.parent.OnAssignColor(evt=None,
                                              itemID=self.itemInfo['id'],
                                              give_value=True)
            self.text_color_value.SetBackgroundColour(color)
        else:
            color = self.text_color_value.GetBackgroundColour()
            self.parent.peaklist.SetItemBackgroundColour(self.itemInfo['id'], color)

    def onRestrictCmaps(self, evt):
        """
        The cmap list will be restricted to more limited selection
        """
        currentCmap = self.text_colormap_value.GetStringSelection()
        narrowList = self.config.narrowCmapList
        narrowList.append(currentCmap)

        # remove duplicates
        narrowList = sorted(list(set(narrowList)))

        if self.text_restrictColormap_value.GetValue():
            self.text_colormap_value.Clear()
            for item in narrowList:
                self.text_colormap_value.Append(item)
            self.text_colormap_value.SetStringSelection(currentCmap)
        else:
            self.text_colormap_value.Clear()
            for item in self.config.cmaps2:
                self.text_colormap_value.Append(item)
            self.text_colormap_value.SetStringSelection(currentCmap)

    def onGetNext(self, evt):
        self.onCheckID()
        count = self.parent.peaklist.GetItemCount() - 1
        if self.itemInfo['id'] == count:
            new_id = 0
        else:
            new_id = self.itemInfo['id'] + 1

        # get new information
        self.itemInfo = self.parent.OnGetItemInformation(new_id)
        # update table
        self.onSetupParameters(None)
        # update title
        self.SetTitle(self.itemInfo['document'])

    def onGetPrevious(self, evt):
        self.onCheckID()
        count = self.parent.peaklist.GetItemCount() - 1
        if self.itemInfo['id'] == 0:
            new_id = count
        else:
            new_id = self.itemInfo['id'] - 1

        # get new information
        self.itemInfo = self.parent.OnGetItemInformation(new_id)
        # update table
        self.onSetupParameters(None)
        # update title
        self.SetTitle(self.itemInfo['document'])

    def onCheckID(self):
        # check whether ID is still correct
        information = self.parent.OnGetItemInformation(self.itemInfo['id'])

        if information['document'] == self.itemInfo['document']:
            return
        else:
            count = self.parent.peaklist.GetItemCount()
            for row in range(count):
                information = self.parent.OnGetItemInformation(row)
                if information['document'] == self.itemInfo['document']:
                    if information['id'] == self.itemInfo['id']:
                        return
                    else:
                        self.itemInfo['id'] = information['id']
                        return
