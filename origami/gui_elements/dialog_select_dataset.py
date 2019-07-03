# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import wx
from styles import Dialog


class DialogSelectDataset(Dialog):
    """
    """

    def __init__(self, parent, presenter, docList, dataList, **kwargs):
        Dialog.__init__(self, parent, title='Copy annotations to document/dataset...', size=(400, 300))

        self.parent = parent
        self.presenter = presenter
        self.documentList = docList
        self.datasetList = dataList

        # make gui items
        self.make_gui()
        if 'set_document' in kwargs:
            self.document_list_choice.SetStringSelection(kwargs['set_document'])
        else:
            self.document_list_choice.SetSelection(0)
        self.on_update_gui(None)

        self.CentreOnParent()
        self.SetFocus()

        wx.EVT_CLOSE(self, self.on_close)

    def on_close(self, evt):
        """Destroy this frame."""

        # If pressed Close, return nothing of value
        self.document = None
        self.dataset = None

        self.Destroy()

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_make_selection, id=wx.ID_OK)
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

    def make_panel(self):

        panel = wx.Panel(self, -1)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        documentList_label = wx.StaticText(panel, -1, 'Document:')
        self.document_list_choice = wx.ComboBox(
            panel, -1, choices=self.documentList,
            size=(300, -1), style=wx.CB_READONLY,
        )
        self.document_list_choice.Select(0)
        self.document_list_choice.Bind(wx.EVT_COMBOBOX, self.on_update_gui)

        datasetList_label = wx.StaticText(panel, -1, 'Dataset:')
        self.dataset_list_choice = wx.ComboBox(panel, -1, choices=[], size=(300, -1), style=wx.CB_READONLY)

        self.ok_btn = wx.Button(panel, wx.ID_OK, 'Select', size=(-1, 22))
        self.cancel_btn = wx.Button(panel, -1, 'Cancel', size=(-1, 22))

        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5
        PANEL_SPACE_MAIN = 10

        # pack elements
        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
        grid.Add(documentList_label, (0, 0))
        grid.Add(self.document_list_choice, (0, 1), wx.GBSpan(1, 3))
        grid.Add(datasetList_label, (1, 0))
        grid.Add(self.dataset_list_choice, (1, 1), wx.GBSpan(1, 3))
        grid.Add(self.ok_btn, (2, 1), wx.GBSpan(1, 1))
        grid.Add(self.cancel_btn, (2, 2), wx.GBSpan(1, 1))

        main_sizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, PANEL_SPACE_MAIN)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def on_update_gui(self, evt):
        document = self.document_list_choice.GetStringSelection()
        spectrum = self.datasetList[document]

        self.dataset_list_choice.SetItems(spectrum)
        self.dataset_list_choice.SetStringSelection(spectrum[0])

    def on_make_selection(self, evt):

        document = self.document_list_choice.GetStringSelection()
        dataset = self.dataset_list_choice.GetStringSelection()
        self.document = document
        self.dataset = dataset
        self.EndModal(wx.OK)
