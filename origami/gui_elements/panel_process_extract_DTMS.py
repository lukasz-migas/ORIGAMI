# Standard library imports
import math
import logging

# Third-party imports
import wx
import numpy as np

# Local imports
from origami.styles import MiniFrame
from origami.styles import validator
from origami.utils.converters import str2num

logger = logging.getLogger(__name__)


class PanelProcessExtractDTMS(MiniFrame):
    """
    Miniframe enabling extraction of DT/MS heatmap
    """

    def __init__(self, parent, presenter, config, icons):
        MiniFrame.__init__(self, parent, title="Extract DT/MS...")
        self.view = parent
        self.presenter = presenter
        self.documentTree = self.view.panelDocuments.documents
        self.data_handling = presenter.data_handling
        self.config = config
        self.icons = icons

        self.block_update = False

        self.make_gui()

        # setup data storage
        self.x_data = None
        self.y_data = None
        self.z_data = None

        # setup gui pview
        self.on_setup_gui()

        self.CentreOnScreen()
        self.SetFocus()

    def make_panel(self):
        panel = wx.Panel(self, -1, size=(-1, -1))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # add extraction controls
        self.info_bar = wx.StaticText(panel, -1, "")
        self.info_bar.SetLabel("")

        mz_min_label = wx.StaticText(panel, wx.ID_ANY, "m/z (min):")
        self.mz_min_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.mz_min_value.Bind(wx.EVT_TEXT, self.on_apply)

        mz_max_label = wx.StaticText(panel, wx.ID_ANY, "m/z (max): ")
        self.mz_max_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.mz_max_value.Bind(wx.EVT_TEXT, self.on_apply)

        mz_bin_label = wx.StaticText(panel, wx.ID_ANY, "m/z (bin size): ")
        self.mz_bin_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.mz_bin_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.msg_bar = wx.StaticText(panel, -1, "")
        self.msg_bar.SetLabel("")

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_3 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        # add buttons
        self.extract_btn = wx.Button(panel, wx.ID_ANY, "Extract", size=(-1, 22))
        self.extract_btn.Bind(wx.EVT_BUTTON, self.on_extract_data)

        self.add_to_document_btn = wx.Button(panel, wx.ID_ANY, "Add to document...", size=(-1, 22))
        self.add_to_document_btn.Bind(wx.EVT_BUTTON, self.on_add_to_document)

        self.save_to_file_btn = wx.Button(panel, wx.ID_ANY, "Save as...", size=(-1, 22))
        self.save_to_file_btn.Bind(wx.EVT_BUTTON, self.on_save)

        self.cancel_btn = wx.Button(panel, wx.ID_ANY, "Cancel", size=(-1, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(self.info_bar, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(mz_min_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_min_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(mz_max_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_max_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(mz_bin_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_bin_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(self.msg_bar, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_3, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(self.extract_btn, (n, 0), flag=wx.ALIGN_CENTER)
        grid.Add(self.add_to_document_btn, (n, 1), flag=wx.ALIGN_CENTER)
        grid.Add(self.save_to_file_btn, (n, 2), flag=wx.ALIGN_CENTER)
        grid.Add(self.cancel_btn, (n, 3), flag=wx.ALIGN_CENTER)

        main_sizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_setup_gui(self):

        document, __ = self.on_get_document()
        parameters = document.parameters
        self.parameters = parameters

        info = "Experimental mass range: {:.2f}-{:.2f}".format(
            parameters.get("startMS", "N/A"), parameters.get("endMS", "N/A")
        )
        self.info_bar.SetLabel(info)

        # check if user has previously defined any values
        if self.config.extract_dtms_mzStart not in [0, "", None]:
            mz_min = self.config.extract_dtms_mzStart
        else:
            mz_min = self.parameters["startMS"]
        self.mz_min_value.SetValue(str(mz_min))

        if self.config.extract_dtms_mzEnd not in [0, "", None]:
            mz_max = self.config.extract_dtms_mzEnd
        else:
            mz_max = self.parameters["endMS"]
        self.mz_max_value.SetValue(str(mz_max))

        if self.config.extract_dtms_mzBinSize not in [0, "", None]:
            mz_bin_size = self.config.extract_dtms_mzBinSize
        else:
            mz_bin_size = 0.1
        self.mz_bin_value.SetValue(str(mz_bin_size))

    def _update_msg_bar(self, info=None):
        if info is None:
            try:
                n_points = int(
                    math.floor(
                        (self.config.extract_dtms_mzEnd - self.config.extract_dtms_mzStart)
                        / self.config.extract_dtms_mzBinSize
                    )
                )
                if n_points > 0:
                    info = "Number of m/z bins: {}".format(n_points)
                else:
                    info = ""
            except (ZeroDivisionError, TypeError):
                info = ""
        self.msg_bar.SetLabel(info)

    def check_user_input(self):
        """Check user input and if incorrect correct the values"""
        self.block_update = True
        if self.config.extract_dtms_mzStart in [0, "", None, "None"]:
            self.config.extract_dtms_mzStart = self.parameters["startMS"]

        if self.config.extract_dtms_mzEnd in [0, "", None, "None"]:
            self.config.extract_dtms_mzEnd = self.parameters["endMS"]

        # check values are in correct order
        if self.config.extract_dtms_mzStart > self.config.extract_dtms_mzEnd:
            self.config.extract_dtms_mzStart, self.config.extract_dtms_mzEnd = (
                self.config.extract_dtms_mzEnd,
                self.config.extract_dtms_mzStart,
            )

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
        """Update values on event"""
        if self.block_update:
            return

        self.config.extract_dtms_mzStart = str2num(self.mz_min_value.GetValue())
        self.config.extract_dtms_mzEnd = str2num(self.mz_max_value.GetValue())
        self.config.extract_dtms_mzBinSize = str2num(self.mz_bin_value.GetValue())
        self._update_msg_bar()

        if evt is not None:
            evt.Skip()

    def on_check_mass_range(self, mz_min, mz_max, shape):
        """Check mass range

        Parameters
        ----------
        mz_min: float
        mz_max: float
        shape: tuple

        Returns
        -------
        mz_x: 1D numpy array
        """
        mz_len = shape[1]
        mz_x = np.linspace(
            mz_min - self.config.extract_dtms_mzBinSize,
            mz_max + self.config.extract_dtms_mzBinSize,
            mz_len,
            endpoint=True,
        )

        return mz_x

    def on_check_data(self):
        is_present = True
        # check if data is already extracted
        if self.x_data is None or self.y_data is None or self.z_data is None:
            self.msg_bar.SetLabel("Data not present - make sure you extract it first.")
            is_present = False

        return is_present

    def on_get_document(self):
        document = self.data_handling.on_get_document()

        return document, document.title

    def on_extract_data(self, evt):
        # clear previous msg
        self._update_msg_bar()

        # check user input
        self.check_user_input()

        document, __ = self.on_get_document()
        path = document.path

        # Extract and load data
        mz_x, dt_y, data = self.data_handling._get_driftscope_mobility_vs_spectrum_data(
            path, self.config.extract_dtms_mzStart, self.config.extract_dtms_mzEnd, self.config.extract_dtms_mzBinSize
        )

        # Plot
        self.view.panelPlots.on_plot_MSDT(data, mz_x, dt_y, "m/z", "Drift time (bins)")

        # add data
        self.x_data = mz_x
        self.y_data = dt_y
        self.z_data = data

        # notify the user that update was made
        self._update_msg_bar("Data was extracted! It had dimensions {} x {}".format(dt_y.shape[0], mz_x.shape[0]))

    def on_add_to_document(self, evt):
        if not self.on_check_data():
            return

        document, __ = self.on_get_document()

        document.gotDTMZ = True
        document.DTMZ = {
            "zvals": self.z_data,
            "xvals": self.x_data,
            "yvals": self.y_data,
            "xlabels": "m/z",
            "ylabels": "Drift time (bins)",
            "cmap": self.config.currentCmap,
        }
        self.data_handling.on_update_document(document, "document")

    def on_save(self, evt):
        if not self.on_check_data():
            return

        __, document_title = self.on_get_document()

        zvals = self.z_data
        xvals = self.x_data
        yvals = self.y_data

        default_name = "MSDT_{}{}".format(document_title, self.config.saveExtension)

        saveData = np.vstack((xvals, zvals))
        yvals = list(map(str, yvals.tolist()))
        labels = ["DT"]
        labels.extend(yvals)
        fmts = ["%.4f"] + ["%i"] * len(yvals)

        # Save 2D array
        kwargs = {"default_name": default_name}
        self.documentTree.onSaveData(data=saveData, labels=labels, data_format=fmts, **kwargs)

        self._update_msg_bar("Data was saved to file!")


#     def downsample_array(self):
#         """Downsample MS/DT array"""
#         __, x_dim = self.z_data.shape
#
#         division_factors, division_factor = pr_heatmap.calculate_division_factors(x_dim)
#         if not division_factors:
#             data, mz_x = pr_heatmap.subsample_array(self.z_data, self.x_data, division_factor)
#         else:
#             data, mz_x = pr_heatmap.bin_sum_array(self.z_data, self.x_data, division_factor)
#             self.view.panelPlots.on_plot_MSDT(data, mz_x, self.y_data, 'm/z', 'Drift time (bins)')
#             data, mz_x = pr_heatmap.bin_mean_array(self.z_data, self.x_data, division_factor)
#             self.view.panelPlots.on_plot_MSDT(data, mz_x, self.y_data, 'm/z', 'Drift time (bins)')
