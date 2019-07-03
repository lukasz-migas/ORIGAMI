# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import os
import webbrowser

import wx


class panelHTMLViewer(wx.MiniFrame):

    def __init__(self, parent, config, msg=None, title=None, **kwargs):
        wx.MiniFrame.__init__(
            self, parent, -1, 'HTML viewer', size=(-1, -1),
            style=(
                wx.DEFAULT_FRAME_STYLE |
                wx.MAXIMIZE_BOX | wx.CLOSE_BOX
            ),
        )

        self.parent = parent
        self.config = config

        self.label_header = wx.html.HtmlWindow(
            self, style=wx.TE_READONLY | wx.TE_MULTILINE |
            wx.html.HW_SCROLLBAR_AUTO | wx.BORDER_NONE | wx.html.HTML_URL_IMAGE,
        )

        if msg is None:
            msg = kwargs['html_msg']
        if title is None:
            title = kwargs['title']

        # get current working directory and temporarily change path
        cwd = os.getcwd()
        os.chdir(self.config.cwd)

        self.label_header.SetPage(msg)
        self.label_header.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.on_url)
        self.SetTitle(title)

        try:
            _main_position = self.parent.GetPosition()
            position_diff = []
            for idx in range(wx.Display.GetCount()):
                d = wx.Display(idx)
                position_diff.append(_main_position[0] - d.GetGeometry()[0])

            currentDisplaySize = wx.Display(position_diff.index(min(position_diff))).GetGeometry()
        except Exception:
            currentDisplaySize = None

        if 'window_size' in kwargs:
            if currentDisplaySize is not None:
                screen_width, screen_height = currentDisplaySize[2], currentDisplaySize[3]
                kwargs['window_size'] = list(kwargs['window_size'])

                if kwargs['window_size'][0] > screen_width:
                    kwargs['window_size'][0] = screen_width

                if kwargs['window_size'][1] > screen_height:
                    kwargs['window_size'][1] = screen_height - 75

            self.SetSize(kwargs['window_size'])

        self.Show(True)
        self.CentreOnParent()
        self.SetFocus()
        wx.EVT_CLOSE(self, self.on_close)

        # reset working directory
        os.chdir(cwd)

    def on_url(self, evt):
        link = evt.GetLinkInfo()
        webbrowser.open(link.GetHref())

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()
