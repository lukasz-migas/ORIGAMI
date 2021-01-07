"""Notification toast"""
# Third-party imports
import wx
from wx.adv import NotificationMessage


def Notification(title: str, message: str, parent=None, flags=wx.ICON_INFORMATION, timeout: float = 5):  # noqa
    """Create a Toast-like notification that is shown to the user

    Parameters
    ----------
    title : str
        title of the message
    message : str
        message to be shown to the user
    parent :
        parent to be associated with the notification
    flags :
        flags to be setup for the message. Use one of  ICON_INFORMATION , ICON_WARNING and ICON_ERROR
    timeout : float
        amount of time the message is shown for
    """
    notify = NotificationMessage(title=title, message=message, parent=parent, flags=flags)
    notify.Show(timeout=timeout)
    return notify


def _main():
    # Local imports
    from origami.app import App

    app = App()
    Notification("ORIGAMI", "Here is a notification from ORIGAMI")


if __name__ == "__main__":
    _main()
