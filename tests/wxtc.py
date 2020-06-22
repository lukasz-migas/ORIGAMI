"""wxPython unit-test support"""
# Third-party imports
import wx

INTERVAL = 100


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
        cls.app = wx.App()
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
            self.yield_()
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
        evtLoop = self.app.GetTraits().CreateEventLoop()
        activator = wx.EventLoopActivator(evtLoop)  # automatically restores the old one
        evtLoop.YieldFor(eventsToProcess)

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
        """
        Close dialogs by calling their EndModal method
        """
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


class Namespace(object):
    """Namespace object"""

    def dict(self):
        """Return dictionary of own namespace"""
        return self.__dict__
