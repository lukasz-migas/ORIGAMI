# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import wx
from styles import Dialog


class DialogAsk(Dialog):
    """
    Simple dialog that will ask what should the new value be.
    """

    def __init__(self, parent, **kwargs):
        Dialog.__init__(self, parent, title='Edit parameters...', size=(400, 300))
#
        self.parent = parent

        self.item_label = kwargs['static_text']
        self.item_value = kwargs['value_text']
        self.item_validator = kwargs['validator']

        self.return_value = None

        if kwargs['keyword'] == 'charge':
            self.SetTitle('Assign charge...')
        elif kwargs['keyword'] == 'alpha':
            self.SetTitle('Assign transparency...')
        elif kwargs['keyword'] == 'mask':
            self.SetTitle('Assign mask...')
        elif kwargs['keyword'] == 'min_threshold':
            self.SetTitle('Assign minimum threshold...')
        elif kwargs['keyword'] == 'max_threshold':
            self.SetTitle('Assign maximum threshold...')
        elif kwargs['keyword'] == 'label':
            self.SetTitle('Assign label...')

        # make gui items
        self.make_gui()

        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

    def on_key_event(self, evt):
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:
            self.on_close(None)
        elif key_code in [wx.WXK_RETURN, 370]:  # enter or enter on numpad
            self.onOK(None)

        if evt is not None:
            evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""

        self.parent.ask_value = None
        self.Destroy()

    def onOK(self, evt):
        self.on_apply(evt=None)

        if self.item_validator == 'integer':
            self.return_value = int(self.item_value)
        elif self.item_validator == 'float':
            self.return_value = float(self.item_value)
        elif self.item_validator == 'str':
            self.return_value = self.item_value

        self.parent.ask_value = self.return_value

        self.EndModal(wx.OK)

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.okBtn.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

    def make_panel(self):

        panel = wx.Panel(self, -1)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.input_label = wx.StaticText(panel, -1, 'Enter value:')
        self.input_label.SetLabel(self.item_label)
        self.input_label.SetFocus()

        if self.item_validator == 'integer':
            self.input_value = wx.SpinCtrlDouble(
                panel, -1,
                value=str(self.item_value),
                min=1, max=200, initial=0, inc=1,
                size=(90, -1),
            )
        elif self.item_validator == 'float':
            self.input_value = wx.SpinCtrlDouble(
                panel, -1,
                value=str(self.item_value),
                min=0, max=1, initial=0, inc=0.1,
                size=(90, -1),
            )

        self.input_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.okBtn = wx.Button(panel, wx.ID_OK, 'Select', size=(-1, 22))
        self.cancelBtn = wx.Button(panel, -1, 'Cancel', size=(-1, 22))

        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5
        PANEL_SPACE_MAIN = 10

        # pack elements
        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)

        grid.Add(self.input_label, (0, 0), wx.GBSpan(2, 3), flag=wx.ALIGN_RIGHT | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        grid.Add(self.input_value, (0, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)

        grid.Add(self.okBtn, (2, 2), wx.GBSpan(1, 1))
        grid.Add(self.cancelBtn, (2, 3), wx.GBSpan(1, 1))

        main_sizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, PANEL_SPACE_MAIN)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def on_apply(self, evt):
        self.item_value = self.input_value.GetValue()

        if evt is not None:
            evt.Skip()
