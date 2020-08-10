import wx
from origami.gui_elements.popup import PopupBase
from origami.styles import set_tooltip


class ViewAboutPopup(PopupBase):
    """Create popup window to modify few uncommon settings"""

    plot_id = None
    plot_type = None
    view_type = None
    document_title = None
    dataset_name = None

    def __init__(self, parent, view, style=wx.BORDER_SIMPLE):
        self.view = view
        PopupBase.__init__(self, parent, style)

    def make_panel(self):
        """Make popup window"""

        self.plot_id = wx.StaticText(self, wx.ID_ANY)
        self.plot_id.SetLabel(self.view.PLOT_ID)
        set_tooltip(self.plot_id, "Unique ID of the current view.")

        self.view_type = wx.StaticText(self, wx.ID_ANY)
        self.view_type.SetLabel(self.view.VIEW_TYPE)
        set_tooltip(self.view_type, "Type of view.")

        self.plot_type = wx.StaticText(self, wx.ID_ANY)
        if self.view.plot_type:
            self.plot_type.SetLabel(self.view.plot_type)
        set_tooltip(self.plot_type, "Currently shown plot type.")

        self.document_title = wx.StaticText(self, wx.ID_ANY)
        if self.view.document_name:
            self.document_title.SetLabel(self.view.document_name)
        set_tooltip(self.document_title, "Name of the document the plot is associated with.")

        self.dataset_name = wx.StaticText(self, wx.ID_ANY)
        if self.view.dataset_name:
            self.dataset_name.SetLabel(self.view.dataset_name)

        set_tooltip(self.dataset_name, "Name of the dataset the plot is associated with. Name includes the group name.")

        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(wx.StaticText(self, -1, "Unique plot ID:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_id, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(self, -1, "View type:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.view_type, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(self, -1, "Plot type:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_type, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(self, -1, "Document title:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.document_title, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(self, -1, "Dataset name:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.dataset_name, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        self.set_info(sizer)

        self.SetSizerAndFit(sizer)
        self.Layout()
