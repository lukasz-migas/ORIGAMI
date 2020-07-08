# Third-party imports
import wx
import clr

# Local imports
from System.Threading import Thread
from System.Threading import ThreadStart
from System.Threading import ApartmentState

SWF = clr.AddReference("System.Windows.Forms")


def app_thread():
    app = wx.App()
    frame = wx.Frame(None)
    wx.DirPickerCtrl(frame)
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    thread = Thread(ThreadStart(app_thread))
    thread.SetApartmentState(ApartmentState.STA)
    thread.Start()
    thread.Join()
