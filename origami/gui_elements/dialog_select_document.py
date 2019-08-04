# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import wx
from ids import ID_addNewOverlayDoc
from styles import Dialog


class DialogSelectDocument(Dialog):
    """Select document from dropdown list"""

    def __init__(self, parent, **kwargs):
        wx.Dialog.__init__(self, parent, title="Select document...", size=(400, 300))

        self.parent = parent
        self.presenter = kwargs["presenter"]
        self.documentList = kwargs["document_list"]
        self.allow_new_document = kwargs.get("allow_new_document", True)
        self.current_document = None

        # make gui items
        self.make_gui()
        self.CentreOnParent()
        self.SetFocus()

        wx.EVT_CLOSE(self, self.on_close)

    def on_close(self, evt):
        """Destroy this frame."""
        # If pressed Close, return nothing of value
        self.presenter.currentDoc = None
        self.current_document = None

        self.Destroy()

    def make_gui(self):
        """Create GUI"""
        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_select_document, id=wx.ID_ANY)
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_new_document, id=ID_addNewOverlayDoc)
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

    def make_panel(self):
        """Make main panel"""
        panel = wx.Panel(self, -1)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        documentList_label = wx.StaticText(panel, -1, "Choose document:")
        self.document_list_choice = wx.Choice(panel, -1, choices=self.documentList, size=(300, -1))
        self.document_list_choice.Select(0)

        self.ok_btn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, 22))
        self.add_btn = wx.Button(panel, ID_addNewOverlayDoc, "Add new document", size=(-1, 22))
        self.cancel_btn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        # In some cases, we don't want to be able to create new document!
        self.add_btn.Enable(enable=self.allow_new_document)

        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5
        PANEL_SPACE_MAIN = 10

        # pack elements
        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)

        grid.Add(documentList_label, (0, 0))
        grid.Add(self.document_list_choice, (0, 1), wx.GBSpan(1, 3))

        grid.Add(self.ok_btn, (1, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.add_btn, (1, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.cancel_btn, (1, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)

        main_sizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, PANEL_SPACE_MAIN)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def on_select_document(self, evt):
        """Select document"""
        docName = self.document_list_choice.GetStringSelection()
        self.current_document = docName
        self.EndModal(wx.OK)

    def on_new_document(self, evt):
        """Create new document"""
        self.presenter.onAddBlankDocument(evt=evt)
        self.EndModal(wx.OK)
