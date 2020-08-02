"""Extract DT/MS"""
# Standard library imports
import os
import math
import logging

# Third-party imports
import wx
import numpy as np

# Local imports
from origami.styles import MiniFrame
from origami.styles import Validator
from origami.icons.assets import Icons
from origami.config.config import CONFIG
from origami.utils.converters import str2num
from origami.config.environment import ENV
from origami.gui_elements.panel_base import DatasetMixin

logger = logging.getLogger(__name__)


class PanelProcessExtractMSDT(MiniFrame, DatasetMixin):
    """Panel enabling extraction of new or additional MS/DT data"""

    PANEL_BASE_TITLE = "Extract DT/MS"
    HELP_LINK = "https://origami.lukasz-migas.com/"
    PANEL_STATUSBAR_COLOR = wx.BLACK

    # ui elements
    mz_min_value = None
    mz_max_value = None
    mz_bin_value = None
    info_bar = None
    extract_btn = None
    add_to_document_btn = None
    save_to_file_btn = None
    cancel_btn = None

    # parameters
    parameters = None

    def __init__(self, parent, presenter, document_title: str = None):
        MiniFrame.__init__(self, parent, title="Extract DT/MS...")
        self._icons = Icons()
        self.view = parent
        self.presenter = presenter

        self.block_update = False

        self.make_gui()

        # setup data storage
        self.document_title = document_title
        self.dataset_name = None
        self.msdt_obj = None
        self.msdt_title = None

        # setup gui view
        self.on_setup_gui()

        self.CenterOnParent()
        self.SetFocus()

    @property
    def data_handling(self):
        """Return handle to `data_handling`"""
        return self.presenter.data_handling

    @property
    def panel_plot(self):
        """Return handle to `panel_plot`"""
        return self.view.panelPlots

    @property
    def document_tree(self):
        """Return handle to `document_tree`"""
        return self.presenter.view.panelDocuments.documents

    def on_close(self, evt, force: bool = False):
        """Close window"""
        self._dataset_mixin_teardown()
        MiniFrame.on_close(self, evt, force=force)

    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self, -1)

        # add extraction controls
        self.info_bar = wx.StaticText(panel, -1, "")
        self.info_bar.SetLabel("")

        mz_min_label = wx.StaticText(panel, wx.ID_ANY, "m/z (min):")
        self.mz_min_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.mz_min_value.Bind(wx.EVT_TEXT, self.on_apply)

        mz_max_label = wx.StaticText(panel, wx.ID_ANY, "m/z (max): ")
        self.mz_max_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.mz_max_value.Bind(wx.EVT_TEXT, self.on_apply)

        mz_bin_label = wx.StaticText(panel, wx.ID_ANY, "m/z (bin size): ")
        self.mz_bin_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.mz_bin_value.Bind(wx.EVT_TEXT, self.on_apply)

        # statusbar
        statusbar = self.make_statusbar(panel, "right")

        # add buttons
        self.extract_btn = wx.Button(panel, wx.ID_ANY, "Extract", size=(-1, -1))
        self.extract_btn.Bind(wx.EVT_BUTTON, self.on_extract_data)

        self.add_to_document_btn = wx.Button(panel, wx.ID_ANY, "Add to document...", size=(-1, -1))
        self.add_to_document_btn.Bind(wx.EVT_BUTTON, self.on_add_to_document)

        self.save_to_file_btn = wx.Button(panel, wx.ID_ANY, "Save as...", size=(-1, -1))
        self.save_to_file_btn.Bind(wx.EVT_BUTTON, self.on_save)

        self.cancel_btn = wx.Button(panel, wx.ID_ANY, "Cancel", size=(-1, -1))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.BoxSizer(wx.HORIZONTAL)
        btn_grid.Add(self.extract_btn)
        btn_grid.Add(self.add_to_document_btn)
        btn_grid.Add(self.save_to_file_btn)
        btn_grid.Add(self.cancel_btn)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(mz_min_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_min_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(mz_max_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_max_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(mz_bin_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_bin_value, (n, 1), flag=wx.EXPAND)
        grid.AddGrowableCol(1, 1)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.info_bar, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 10)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)
        main_sizer.Add(statusbar, 0, wx.EXPAND, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_setup_gui(self):
        """Setup GUI so it matches current document"""

        document = ENV.on_get_document()
        if document is None:
            return

        parameters = document.parameters
        self.parameters = parameters

        info = "Experimental mass range: {:.2f}-{:.2f}".format(
            parameters.get("start_ms", -1), parameters.get("end_ms", -1)
        )
        self.info_bar.SetLabel(info)

        # check if user has previously defined any values
        if CONFIG.msdt_panel_extract_mz_start not in [0, "", None]:
            mz_min = CONFIG.msdt_panel_extract_mz_start
        else:
            mz_min = self.parameters["start_ms"]
        self.mz_min_value.SetValue(str(mz_min))

        if CONFIG.msdt_panel_extract_mz_end not in [0, "", None]:
            mz_max = CONFIG.msdt_panel_extract_mz_end
        else:
            mz_max = self.parameters["end_ms"]
        self.mz_max_value.SetValue(str(mz_max))

        if CONFIG.msdt_panel_extract_mz_bin_size not in [0, "", None]:
            mz_bin_size = CONFIG.msdt_panel_extract_mz_bin_size
        else:
            mz_bin_size = 0.1
        self.mz_bin_value.SetValue(str(mz_bin_size))

        # setup mixins
        self._dataset_mixin_setup()

    def _update_msg_bar(self, info=None):
        if info is None:
            try:
                n_points = int(
                    math.floor(
                        (CONFIG.msdt_panel_extract_mz_end - CONFIG.msdt_panel_extract_mz_start)
                        / CONFIG.msdt_panel_extract_mz_bin_size
                    )
                )
                if n_points > 0:
                    info = "Number of m/z bins: {}".format(n_points)
                else:
                    info = ""
            except (ZeroDivisionError, TypeError):
                info = ""
        self.display_label.SetLabel(info)

    def check_user_input(self):
        """Check user input and if incorrect correct the values"""
        self.block_update = True
        if CONFIG.msdt_panel_extract_mz_start in [0, "", None, "None"]:
            CONFIG.msdt_panel_extract_mz_start = self.parameters["start_ms"]

        if CONFIG.msdt_panel_extract_mz_end in [0, "", None, "None"]:
            CONFIG.msdt_panel_extract_mz_end = self.parameters["end_ms"]

        # check values are in correct order
        if CONFIG.msdt_panel_extract_mz_start > CONFIG.msdt_panel_extract_mz_end:
            CONFIG.msdt_panel_extract_mz_start, CONFIG.msdt_panel_extract_mz_end = (
                CONFIG.msdt_panel_extract_mz_end,
                CONFIG.msdt_panel_extract_mz_start,
            )

        # check if values are the same
        if CONFIG.msdt_panel_extract_mz_start == CONFIG.msdt_panel_extract_mz_end:
            CONFIG.msdt_panel_extract_mz_end += 1

        # check if values are below experimental range
        if CONFIG.msdt_panel_extract_mz_start < self.parameters["start_ms"]:
            CONFIG.msdt_panel_extract_mz_start = self.parameters["start_ms"]

        if CONFIG.msdt_panel_extract_mz_end > self.parameters["end_ms"]:
            CONFIG.msdt_panel_extract_mz_end = self.parameters["end_ms"]

        if CONFIG.msdt_panel_extract_mz_bin_size in [0, "", None, "None"]:
            CONFIG.msdt_panel_extract_mz_bin_size = 1

        self.on_setup_gui()
        self.block_update = False

    def on_apply(self, evt):
        """Update values on event"""
        if self.block_update:
            return

        CONFIG.msdt_panel_extract_mz_start = str2num(self.mz_min_value.GetValue())
        CONFIG.msdt_panel_extract_mz_end = str2num(self.mz_max_value.GetValue())
        CONFIG.msdt_panel_extract_mz_bin_size = str2num(self.mz_bin_value.GetValue())
        self._update_msg_bar()

        if evt is not None:
            evt.Skip()

    @staticmethod
    def on_check_mass_range(mz_min, mz_max, shape):
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
            mz_min - CONFIG.msdt_panel_extract_mz_bin_size,
            mz_max + CONFIG.msdt_panel_extract_mz_bin_size,
            mz_len,
            endpoint=True,
        )

        return mz_x

    def on_check_data(self):
        """Check whether data was extracted"""
        is_present = True
        # check if data is already extracted
        if self.msdt_obj is None:
            is_present = False
            self.display_label.SetLabel("Data not present - make sure you extract it first.")

        return is_present

    def on_extract_data(self, _evt):
        """Extract data and show on plot"""
        # clear previous msg
        self._update_msg_bar()

        # check user input
        self.check_user_input()

        document = ENV.on_get_document(self.document_title)
        path = document.get_file_path("main")

        title = (
            f"MZ_{CONFIG.msdt_panel_extract_mz_start:.2f}-{CONFIG.msdt_panel_extract_mz_end:.2f} "
            f"(bin={CONFIG.msdt_panel_extract_mz_bin_size:4f})"
        )

        if self.msdt_obj is None or self.msdt_title != title:
            msdt_obj = self.data_handling.waters_im_extract_msdt(
                path,
                CONFIG.msdt_panel_extract_mz_start,
                CONFIG.msdt_panel_extract_mz_end,
                CONFIG.msdt_panel_extract_mz_bin_size,
            )

            self.msdt_obj = msdt_obj
            self.msdt_title = title
        else:
            msdt_obj = self.msdt_obj

        self.panel_plot.view_msdt.plot(obj=msdt_obj)

        # notify the user that update was made
        self._update_msg_bar(
            "Data was extracted! It had dimensions {} x {}".format(msdt_obj.shape[0], msdt_obj.shape[1])
        )

    def on_add_to_document(self, _evt):
        """Extract data and add it to the document"""
        if not self.on_check_data():
            return
        document = ENV.on_get_document(self.document_title)
        title = (
            f"MZ_{CONFIG.msdt_panel_extract_mz_start:.2f}-{CONFIG.msdt_panel_extract_mz_end:.2f} "
            f"(bin={CONFIG.msdt_panel_extract_mz_bin_size:3f})"
        )

        if self.msdt_obj is None or self.msdt_title != title:
            self.on_extract_data(None)

        # get extracted object
        msdt_obj = self.msdt_obj

        # add the object to document
        document.add_msdt(title, msdt_obj)

        # display object in the window

        # notify document tree of changes
        self.document_tree.on_update_document(msdt_obj.DOCUMENT_KEY, title, self.document_title)

    def on_save(self, _evt):
        """Export data to a text file"""
        if not self.on_check_data():
            return

        document = ENV.on_get_document(self.document_title)
        default_name = f"{self.msdt_title}{CONFIG.saveExtension}"
        default_path = os.path.join(document.output_path, default_name)
        filename = self.data_handling.on_get_csv_filename(default_name, default_path)
        if filename in ["", None]:
            self._update_msg_bar("Action was cancelled")
            return

        self.msdt_obj.to_csv(filename)
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
#             self.view.panelPlots.on_plot_dtms(data, mz_x, self.y_data, 'm/z', 'Drift time (bins)')
#             data, mz_x = pr_heatmap.bin_mean_array(self.z_data, self.x_data, division_factor)
#             self.view.panelPlots.on_plot_dtms(data, mz_x, self.y_data, 'm/z', 'Drift time (bins)')
def _main():
    app = wx.App()
    ex = PanelProcessExtractMSDT(None, None)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
