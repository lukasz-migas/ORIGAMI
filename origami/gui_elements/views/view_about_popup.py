# Third-party imports
import wx

# Local imports
from origami.gui_elements.popup import PopupBase
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_bitmap_btn


class ViewAboutPopup(PopupBase):
    """Create popup window to modify few uncommon settings"""

    plot_id = None
    plot_type = None
    view_type = None
    document_title = None
    dataset_name = None
    plot_size = None

    INFO_MESSAGE = "Right-click or double-click inside the popup window to close it."

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

        self.plot_size = wx.StaticText(self, wx.ID_ANY)
        self.plot_size.SetLabel(str(self.view.panel.GetSize()))
        set_tooltip(self.plot_size, "Current size of the plot in pixels.")

        self.document_title = wx.StaticText(self, wx.ID_ANY)
        if self.view.document_name:
            self.document_title.SetLabel(self.view.document_name)
        set_tooltip(self.document_title, "Name of the document the plot is associated with.")

        self.dataset_name = wx.StaticText(self, wx.ID_ANY)
        if self.view.dataset_name:
            self.dataset_name.SetLabel(self.view.dataset_name)
        set_tooltip(self.dataset_name, "Name of the dataset the plot is associated with. Name includes the group name.")

        btn_clipboard = make_bitmap_btn(self, -1, self.view._icons.filelist)  # noqa
        set_tooltip(btn_clipboard, "Copy figure to clipboard")
        self.Bind(wx.EVT_BUTTON, self.view.on_copy_to_clipboard, btn_clipboard)

        btn_png = make_bitmap_btn(self, -1, self.view._icons.png)  # noqa
        set_tooltip(btn_png, "Save figure")
        self.Bind(wx.EVT_BUTTON, self.view.on_save_figure, btn_png)

        btn_clear = make_bitmap_btn(self, -1, self.view._icons.clear)  # noqa
        set_tooltip(btn_clear, "Clear figure")
        self.Bind(wx.EVT_BUTTON, self.view.on_clear_plot, btn_clear)

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(btn_clipboard)
        btn_sizer.Add(btn_png)
        btn_sizer.Add(btn_clear)

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
        grid.Add(wx.StaticText(self, -1, "Plot size (px):"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot_size, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(self, -1, "Document title:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.document_title, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(self, -1, "Dataset name:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.dataset_name, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        self.set_info(sizer)
        self.set_close_btn(sizer)
        self.set_title("About plot", True)

        self.SetSizerAndFit(sizer)
        self.Layout()
