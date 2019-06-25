import wx
from utils.check import get_latest_version, compare_versions


def check_version():
    try:
        newVersion = get_latest_version(link=self.config.links['newVersion'])
        update = compare_versions(newVersion, self.config.version)
        if not update:
            try:
                if evt.GetId() == ID_CHECK_VERSION:
                    dlgBox(exceptionTitle='ORIGAMI',
                           exceptionMsg='You are using the most up to date version %s.' % (self.config.version),
                           type="Info")
            except Exception:
                pass
        else:
            webpage = get_latest_version(get_webpage=True)
            wx.Bell()
            message = "Version {} is now available for download.\nYou are currently using version {}.".format(
                newVersion, self.config.version)
            self.onThreading(None, (message, 4),
                             action='updateStatusbar')
            msgDialog = DialogNewVersion(self.view, presenter=self, webpage=webpage)
            msgDialog.ShowModal()
    except Exception as e:
        self.onThreading(None, ('Could not check version number', 4),
                         action='updateStatusbar')
        logger.error(e)
