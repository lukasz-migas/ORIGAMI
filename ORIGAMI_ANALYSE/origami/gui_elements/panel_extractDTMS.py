import wx
import numpy as np
import math

from styles import validator
from toolbox import str2num

import readers.io_waters_raw as io_waters


class panel_extractDTMS(wx.MiniFrame):
    """
    Miniframe enabling extraction of DT/MS heatmap
    """

    def __init__(self, parent, presenter, config, icons):
        wx.MiniFrame.__init__(self, parent, -1, 'Extract DT/MS...', size=(-1, -1),
                              style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER |
                              wx.RESIZE_BOX | wx.MAXIMIZE_BOX)
        self.view = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons

        self.block_update = False

        self.make_gui()

        # setup gui pview
        self.on_setup_gui()

        self.CentreOnScreen()
        self.Show(True)

        # bind events
        wx.EVT_CLOSE(self, self.on_close)

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 0)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def make_panel(self):
        panel = wx.Panel(self, -1, size=(-1, -1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # add extraction controls
        self.info_bar = wx.StaticText(panel, -1, "")
        self.info_bar.SetLabel("")

        mz_min_label = wx.StaticText(panel, wx.ID_ANY, u"m/z (min):")
        self.mz_min_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                        validator=validator('floatPos')
                                        )
        self.mz_min_value.Bind(wx.EVT_TEXT, self.on_apply)

        mz_max_label = wx.StaticText(panel, wx.ID_ANY, u"m/z (max): ")
        self.mz_max_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                        validator=validator('floatPos')
                                        )
        self.mz_max_value.Bind(wx.EVT_TEXT, self.on_apply)

        mz_bin_label = wx.StaticText(panel, wx.ID_ANY, u"m/z (bin size): ")
        self.mz_bin_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                        validator=validator('floatPos')
                                        )
        self.mz_bin_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.msg_bar = wx.StaticText(panel, -1, "")
        self.msg_bar.SetLabel("")

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_3 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        # add buttons
        self.add_to_document_btn = wx.Button(panel, wx.ID_ANY, "Add to document...", size=(-1, 22))
        self.add_to_document_btn.Bind(wx.EVT_BUTTON, self.on_add_to_document)

        self.extract_btn = wx.Button(panel, wx.ID_ANY, "Extract", size=(-1, 22))
        self.extract_btn.Bind(wx.EVT_BUTTON, self.on_extract_data)

        self.plot_btn = wx.Button(panel, wx.ID_ANY, "Plot", size=(-1, 22))
        self.plot_btn.Bind(wx.EVT_BUTTON, self.on_add_to_document)

        self.save_to_file_btn = wx.Button(panel, wx.ID_ANY, "Save as...", size=(-1, 22))
        self.save_to_file_btn.Bind(wx.EVT_BUTTON, self.on_add_to_document)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(self.info_bar, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(mz_min_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_min_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(mz_max_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_max_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(mz_bin_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_bin_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.msg_bar, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line_3, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.add_to_document_btn, (n, 0), wx.GBSpan(1, 1),
                 flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.extract_btn, (n, 1), wx.GBSpan(1, 1),
                 flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.plot_btn, (n, 2), wx.GBSpan(1, 1),
                 flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.save_to_file_btn, (n, 3), wx.GBSpan(1, 1),
                 flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def on_setup_gui(self):
        try:
            document_title = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        except:
            return

        document = self.presenter.documentsDict[document_title]
        parameters = document.parameters
        self.parameters = parameters

        info = "Experimental mass range: {:.2f}-{:.2f}".format(parameters.get("startMS", "N/A"),
                                                               parameters.get("endMS", "N/A"))
        self.info_bar.SetLabel(info)

        # check if user has previously defined any values
        if self.config.extract_dtms_mzStart not in [0, "", None]:
            self.mz_min_value.SetValue(str(self.config.extract_dtms_mzStart))
        if self.config.extract_dtms_mzEnd not in [0, "", None]:
            self.mz_max_value.SetValue(str(self.config.extract_dtms_mzEnd))
        if self.config.extract_dtms_mzBinSize not in [0, "", None]:
            self.mz_bin_value.SetValue(str(self.config.extract_dtms_mzBinSize))

    def check_user_input(self):
        self.block_update = True
        if self.config.extract_dtms_mzStart in [0, "", None, "None"]:
            self.config.extract_dtms_mzStart = self.parameters["startMS"]

        if self.config.extract_dtms_mzEnd in [0, "", None, "None"]:
            self.config.extract_dtms_mzEnd = self.parameters["endMS"]

        # check values are in correct order
        if self.config.extract_dtms_mzStart > self.config.extract_dtms_mzEnd:
            self.config.extract_dtms_mzStart, self.config.extract_dtms_mzEnd = \
                self.config.extract_dtms_mzEnd, self.config.extract_dtms_mzStart

        # check if values are the same
        if self.config.extract_dtms_mzStart == self.config.extract_dtms_mzEnd:
            self.config.extract_dtms_mzEnd += 1

        # check if values are below experimental range
        if self.config.extract_dtms_mzStart < self.parameters["startMS"]:
            self.config.extract_dtms_mzStart = self.parameters["startMS"]

        if self.config.extract_dtms_mzEnd > self.parameters["endMS"]:
            self.config.extract_dtms_mzEnd = self.parameters["endMS"]

        if self.config.extract_dtms_mzBinSize in [0, "", None, "None"]:
            self.config.extract_dtms_mzBinSize = 1

        self.on_setup_gui()
        self.block_update = False

    def on_apply(self, evt):
        if self.block_update:
            return

        self.config.extract_dtms_mzStart = str2num(self.mz_min_value.GetValue())
        self.config.extract_dtms_mzEnd = str2num(self.mz_max_value.GetValue())
        self.config.extract_dtms_mzBinSize = str2num(self.mz_bin_value.GetValue())

        try:
            n_points = int(math.floor((self.config.extract_dtms_mzEnd - self.config.extract_dtms_mzStart) /
                                      self.config.extract_dtms_mzBinSize))
            if n_points > 0:
                info = "Number of points: {}".format(n_points)
            else:
                info = ""
        except (ZeroDivisionError, TypeError):
            info = ""
        self.msg_bar.SetLabel(info)

        if evt is not None:
            evt.Skip()

    def on_add_to_document(self, evt):
        pass

    def on_extract_data(self, evt):

        # check user input
        self.check_user_input()

        try:
            document_title = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        except:
            return

        document = self.presenter.documentsDict[document_title]
        path = document.path

        print(self.config.extract_dtms_mzStart, self.config.extract_dtms_mzEnd, self.config.extract_dtms_mzBinSize)

        # m/z spacing, default is 1 Da
        n_points = int(math.floor((self.config.extract_dtms_mzEnd - self.config.extract_dtms_mzStart) /
                                  self.config.extract_dtms_mzBinSize))

        # Extract and load data
        extract_kwargs = {'return_data':True}
        data = io_waters.rawMassLynx_MZDT_extract(path=path,
                                                         driftscope_path=self.config.driftscopePath,
                                                         mz_start=self.config.extract_dtms_mzStart,
                                                         mz_end=self.config.extract_dtms_mzEnd,
                                                         mz_nPoints=n_points,
                                                         **extract_kwargs)
        print(data.shape)

#         # Get x/y axis
#         xlabelsMZDT = np.linspace(parameters['startMS'] - self.config.ms_dtmsBinSize,
#                                   parameters['endMS'] + self.config.ms_dtmsBinSize,
#                                   nPoints, endpoint=True)
#         ylabelsMZDT = 1 + np.arange(len(imsDataMZDT[:, 1]))
#
#         # Plot
#         self.view.panelPlots.on_plot_MSDT(imsDataMZDT, xlabelsMZDT, ylabelsMZDT,
#                                           'm/z', 'Drift time (bins)')
#
#         document.gotDTMZ = True
#         document.DTMZ = {'zvals':imsDataMZDT, 'xvals':xlabelsMZDT,
#                           'yvals':ylabelsMZDT, 'xlabels':'m/z',
#                           'ylabels':'Drift time (bins)',
#                           'cmap':self.config.currentCmap}
#         self.OnUpdateDocument(document, 'document')
