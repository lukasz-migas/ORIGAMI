"""wxPython unit-test support"""
# Standard library imports
from typing import List
from typing import Union

# Third-party imports
import wx

# Local imports
from origami.app import App

INTERVAL = 100
WAIT = 50


class WidgetTestCase:
    """
    A testcase that will create an app and frame for various widget test
    modules to use. They can inherit from this class to save some work. This
    is also good for test cases that just need to have an application object
    created.
    """

    @classmethod
    def setup_class(cls):
        """Setup"""
        cls.app = App()
        wx.Log.SetActiveTarget(wx.LogStderr())
        cls.frame = wx.Frame(None, title="WTC: " + cls.__class__.__name__)
        cls.frame.Show()
        cls.frame.PostSizeEvent()

    @classmethod
    def teardown_class(cls):
        """Teardown"""

        def _cleanup():
            for tlw in wx.GetTopLevelWindows():
                if tlw:
                    if isinstance(tlw, wx.Dialog) and tlw.IsModal():
                        tlw.EndModal(0)
                        wx.CallAfter(tlw.Destroy)
                    else:
                        tlw.Close(force=True)
            wx.WakeUpIdle()

        timer = wx.PyTimer(_cleanup)
        timer.Start(100)
        cls.app.MainLoop()
        del cls.app

    def run_dialog(self, dlg):
        """Run dialog"""
        if "wxMac" not in wx.PlatformInfo:
            # Something is causing a hang when running one of these tests, so
            # for now we'll not actually test ShowModal on Macs.
            # TODO: FIX THIS!!
            wx.CallLater(250, dlg.EndModal, wx.ID_OK)
            val = dlg.ShowModal()
            dlg.Destroy()
            assert val == wx.ID_OK
        else:
            dlg.Show()
            dlg.Destroy()
        self.yield_()

    # helper methods
    def yield_(self, eventsToProcess=wx.EVT_CATEGORY_ALL):  # noqa
        """
        Since the tests are usually run before MainLoop is called then we
        need to make our own EventLoop for Yield to actually do anything
        useful.
        """
        evt_loop = self.app.GetTraits().CreateEventLoop()
        activator = wx.EventLoopActivator(evt_loop)  # automatically restores the old one
        evt_loop.YieldFor(eventsToProcess)

    def update_(self, window):
        """
        Since Update() will not trigger paint events on Mac faster than
        1/30 of second we need to wait a little to ensure that there will
        actually be a paint event while we are yielding.
        """
        if "wxOSX" in wx.PlatformInfo:
            wx.MilliSleep(40)  # a little more than 1/30, just in case
        window.Update()
        self.yield_()

    @staticmethod
    def close_dialogs():
        """Close dialogs by calling their EndModal method"""
        # self.yield_()
        for w in wx.GetTopLevelWindows():
            if isinstance(w, wx.Dialog):
                w.EndModal(wx.ID_CANCEL)

    def wait_for(self, milliseconds):
        """Wait for `milliseconds` ms"""
        intervals = milliseconds / INTERVAL
        while True:
            wx.MilliSleep(INTERVAL)
            self.yield_()
            if hasattr(self, "flag") and self.flag:
                break
            if intervals <= 0:
                break
            intervals -= 1

    def sim_button_click_evt(self, button: wx.Button, handlers: List):
        """Simulate button click"""
        evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId, button.GetId())
        for handler in handlers:
            handler(evt)
        self.yield_()

    def sim_checkbox_click_evt(self, checkbox: wx.CheckBox, value: bool, handlers: List):
        """Simulate wx.CheckBox click"""
        checkbox.SetValue(value)
        evt = wx.PyCommandEvent(wx.EVT_CHECKBOX.typeId, checkbox.GetId())
        for handler in handlers:
            handler(evt)
        self.yield_()

    def sim_textctrl_click_evt(self, textctrl: wx.TextCtrl, value: Union[str, int, float], handlers: List):
        """Simulate wx.CheckBox click"""
        value = str(value)
        textctrl.SetValue(value)
        evt = wx.PyCommandEvent(wx.EVT_TEXT.typeId, textctrl.GetId())
        for handler in handlers:
            handler(evt)
        self.yield_()

    def sim_toggle_click_evt(self, toggle: wx.ToggleButton, value: bool, handlers: List):
        """Simulate wx.CheckBox click"""
        toggle.SetValue(value)
        evt = wx.PyCommandEvent(wx.EVT_TOGGLEBUTTON.typeId, toggle.GetId())
        for handler in handlers:
            handler(evt)
        self.yield_()

    def sim_combobox_click_evt(self, combobox: Union[wx.ComboBox, wx.Choice], value: Union[int, str], handlers: List):
        """Simulate wx.CheckBox click"""
        if isinstance(value, str):
            combobox.SetStringSelection(value)
        else:
            combobox.SetSelection(value)

        if isinstance(combobox, wx.ComboBox):
            evt = wx.PyCommandEvent(wx.EVT_COMBOBOX.typeId, combobox.GetId())
        else:
            evt = wx.PyCommandEvent(wx.EVT_CHOICE.typeId, combobox.GetId())
        for handler in handlers:
            handler(evt)
        self.yield_()

    def sim_spin_ctrl_click_evt(
        self, spin_ctrl: Union[wx.SpinCtrlDouble, wx.SpinCtrl], value: Union[int, float], handlers: List
    ):
        """Simulate wx.CheckBox click"""
        spin_ctrl.SetValue(value)

        if isinstance(spin_ctrl, wx.SpinCtrlDouble):
            evt = wx.PyCommandEvent(wx.EVT_SPINCTRLDOUBLE.typeId, spin_ctrl.GetId())
        else:
            evt = wx.PyCommandEvent(wx.EVT_SPINCTRL.typeId, spin_ctrl.GetId())

        for handler in handlers:
            handler(evt)
        self.yield_()

    def sim_listctrl_select_evt(self, listctrl: wx.ListCtrl, index: int, handlers: List):
        """Simulate selection of item in ListCtrl"""
        listctrl.Select(index)
        evt = wx.PyCommandEvent(wx.EVT_LIST_ITEM_SELECTED.typeId, listctrl.GetId())

        for handler in handlers:
            handler(evt)
        self.yield_()


class Namespace(object):
    """Namespace object"""

    def dict(self):
        """Return dictionary of own namespace"""
        return self.__dict__
