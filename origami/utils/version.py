# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
#
# import wx
# from origami.utils.check import get_latest_version, compare_versions
#
#
# def check_version():
#     try:
#         newVersion = get_latest_version(link=self.config.links['newVersion'])
#         update = compare_versions(newVersion, self.config.version)
#         if not update:
#             try:
#                 if evt.GetId() == ID_CHECK_VERSION:
#                     DialogBox(exceptionTitle='ORIGAMI',
#                            exceptionMsg='You are using the most up to date version %s.' % (self.config.version),
#                            type="Info")
#             except Exception:
#                 pass
#         else:
#             webpage = get_latest_version(get_webpage=True)
#             wx.Bell()
#             message = "Version {} is now available for download.\nYou are currently using version {}.".format(
#                 newVersion, self.config.version)
#             self.onThreading(None, (message, 4),
#                              action='updateStatusbar')
#             msgDialog = DialogNewVersion(self.view, presenter=self, webpage=webpage)
#             msgDialog.ShowModal()
#     except Exception as e:
#         self.onThreading(None, ('Could not check version number', 4),
#                          action='updateStatusbar')
#         logger.error(e)

""" Provide a version for the imimspy library.

This module uses `versioneer`_ to manage version strings. During development,
`versioneer`_ will compute a version string from the current git revision.
For packaged releases based off tags, the version string is hard coded in the
files packaged for distribution.

Attributes:
    __version__:
        The full version string for this installed imimspy library

Functions:
    base_version:
        Return the base version string, without any "dev", "rc" or local build
        information appended.

.. _versioneer: https://github.com/warner/python-versioneer

"""
# Standard library imports
import logging

# Local imports
from origami._version import get_versions

log = logging.getLogger(__name__)

__all__ = ("base_version",)


def base_version() -> str:
    return _base_version_helper(__version__)


def _base_version_helper(version: str) -> str:
    import re

    VERSION_PAT = re.compile(r"^(\d+\.\d+\.\d+)((?:dev|rc).*)?")
    match = VERSION_PAT.search(version)
    assert match is not None
    return match.group(1)


__version__ = get_versions()["version"]
del get_versions
