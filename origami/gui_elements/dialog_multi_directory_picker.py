# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import wx
import wx.lib.agw.multidirdialog as MDD
from utils.path import clean_up_MDD_path


class DialogMultiDirectoryPicker(MDD.MultiDirDialog):

    def __init__(
            self,
            parent,
            title='Choose directories...',
            default_path=None,
            style=MDD.DD_MULTIPLE | MDD.DD_DIR_MUST_EXIST,
    ):

        MDD.MultiDirDialog.__init__(
            self, parent=parent, title=title, defaultPath=default_path,
            agwStyle=style,
        )

    def ShowModal(self):
        """Simplified ShowModal(), returning strings 'ok' or 'cancel'. """
        result = MDD.MultiDirDialog.ShowModal(self)

        output = 'cancel'
        if result == wx.ID_OK:
            output = 'ok'

        return output

    def GetPaths(self, *args, **kwargs):
        """Clean-up the list of paths that is returned from the GetPaths function"""
        path_list = MDD.MultiDirDialog.GetPaths(self, *args, **kwargs)
        return [clean_up_MDD_path(path) for path in path_list]
