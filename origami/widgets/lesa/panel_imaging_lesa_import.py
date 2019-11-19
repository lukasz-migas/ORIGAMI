# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
# Load libraries
import logging
import os

import wx
from pubsub import pub
from styles import ListCtrl
from styles import make_spin_ctrl
from styles import MiniFrame
from styles import set_item_font
from utils.decorators import signal_blocker
from utils.exceptions import MessageError

logger = logging.getLogger("origami")


class PanelImagingImportDataset(MiniFrame):
    """LESA import manager"""

    _peaklist_peaklist = {
        0: {"name": "", "tag": "check", "type": "bool", "show": True, "width": 20},
        1: {"name": "index", "tag": "index", "type": "int", "show": True, "width": 40},
        2: {"name": "filename", "tag": "filename", "type": "str", "show": True, "width": 150},
        3: {"name": "path", "tag": "path", "type": "str", "show": True, "width": 290},
        4: {"name": "m/z range", "tag": "mz_range", "type": "str", "show": True, "width": 80},
        5: {"name": "# scans", "tag": "n_scans", "type": "str", "show": True, "width": 50},
        6: {"name": "scan range", "tag": "scan_range", "type": "str", "show": True, "width": 80},
        7: {"name": "IM", "tag": "ion_mobility", "type": "str", "show": True, "width": 40},
    }

    def __init__(self, parent, presenter, config, icons, **kwargs):
        MiniFrame.__init__(
            self,
            parent,
            title="Imaging: Import LESA",
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
            bind_key_events=False,
        )

        self.parent = parent
        self.presenter = presenter
        self.view = presenter.view
        self.config = config
        self.icons = icons

        self.data_handling = presenter.data_handling
        self.data_processing = presenter.data_processing
        self.data_visualisation = presenter.data_visualisation

        self.panel_plot = self.presenter.view.panelPlots
        self.document_tree = self.presenter.view.panelDocuments.documents

        self._block = False

        # make gui items
        self.make_gui()
        self.on_update_info()
        # subscribe to events
        self.subscribe()

    def subscribe(self):
        """Initilize pubsub subscribers"""
        pub.subscribe(self.on_update_info, "widget.imaging.import.update.spectrum")

    def on_close(self, evt):
        """Destroy this frame"""
        pub.unsubscribe(self.on_update_info, "widget.imaging.import.update.spectrum")
        self.Destroy()

    def make_gui(self):
        """Combine all widgets into one window"""
        # make panel
        settings_panel = self.make_settings_panel(self)
        self._settings_panel_size = settings_panel.GetSize()
        settings_panel.SetMinSize((800, 600))

        # pack elements
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(settings_panel, 1, wx.EXPAND, 0)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)
        self.Layout()

        self.CentreOnScreen()
        self.SetFocus()

    def make_settings_panel(self, split_panel):

        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        info_label = set_item_font(wx.StaticText(panel, wx.ID_ANY, "Instructions"))
        msg = "Please select files and edit pre-processing steps in order to continue. If you want to add files"
        msg += (
            " to existing document, \nplease select the document and the pre-processing parameters will be determined"
        )
        msg += " from the document metadata."
        self.info_label = wx.StaticText(panel, wx.ID_ANY, msg)

        processing_label = set_item_font(wx.StaticText(panel, wx.ID_ANY, "Current pre-processing steps"))
        msg = ""
        self.processing_label = wx.StaticText(panel, wx.ID_ANY, msg)

        # file selection
        self.select_document_btn = wx.Button(panel, wx.ID_OK, "Select document...", size=(-1, 22))
        self.select_document_btn.Bind(wx.EVT_BUTTON, self.on_select_document)

        self.select_files_btn = wx.Button(panel, wx.ID_OK, "Select files...", size=(-1, 22))
        self.select_files_btn.Bind(wx.EVT_BUTTON, self.on_select_files)

        self.processing_btn = wx.Button(panel, wx.ID_OK, "Update processing settings...", size=(-1, 22))
        self.processing_btn.Bind(wx.EVT_BUTTON, self.on_update_settings)

        self.clear_files_btn = wx.Button(panel, wx.ID_OK, "Clear filelist", size=(-1, 22))
        self.clear_files_btn.Bind(wx.EVT_BUTTON, self.on_clear_files)

        # import
        image_dimension_label = set_item_font(wx.StaticText(panel, wx.ID_ANY, "Image dimensions"))
        image_shape_x = wx.StaticText(panel, -1, "Shape (x-dim):")
        self.image_shape_x = make_spin_ctrl(panel, 0, 0, 100, 1, (90, -1), name="shape_x")
        self.image_shape_x.SetBackgroundColour((255, 230, 239))

        image_shape_y = wx.StaticText(panel, -1, "Shape (y-dim):")
        self.image_shape_y = make_spin_ctrl(panel, 0, 0, 100, 1, (90, -1), name="shape_y")
        self.image_shape_y.SetBackgroundColour((255, 230, 239))

        import_label = set_item_font(wx.StaticText(panel, wx.ID_ANY, "Import information"))
        self.import_label = wx.StaticText(panel, wx.ID_ANY, "")
        self.import_btn = wx.Button(panel, wx.ID_OK, "Import", size=(-1, 22))
        self.import_btn.Bind(wx.EVT_BUTTON, self.on_import)

        # make listctrl
        self.make_listctrl_panel(panel)

        horizontal_line_0 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        vertical_line_0 = wx.StaticLine(panel, -1, style=wx.LI_VERTICAL)
        vertical_line_1 = wx.StaticLine(panel, -1, style=wx.LI_VERTICAL)

        # pack buttons
        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.select_document_btn, (n, 0), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.select_files_btn, (n, 1), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.processing_btn, (n, 2), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.clear_files_btn, (n, 3), flag=wx.ALIGN_CENTER)

        # pack heatmap items
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(info_label, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.info_label, (n, 0), wx.GBSpan(2, 2), flag=wx.EXPAND)
        n += 2
        grid.Add(processing_label, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(self.processing_label, (n, 0), wx.GBSpan(6, 4), flag=wx.EXPAND)

        # pack heatmap items
        grid_2 = wx.GridBagSizer(2, 2)
        n = 0
        grid_2.Add(import_label, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid_2.Add(self.import_label, (n, 0), wx.GBSpan(3, 2), flag=wx.EXPAND)

        # pack heatmap items
        grid_3 = wx.GridBagSizer(2, 2)
        n = 0
        grid_3.Add(image_dimension_label, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid_3.Add(image_shape_x, (n, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid_3.Add(self.image_shape_x, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid_3.Add(image_shape_y, (n, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid_3.Add(self.image_shape_y, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(grid_2, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(vertical_line_0, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(grid_3, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(vertical_line_1, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.import_btn, 0, wx.ALL | wx.ALIGN_TOP, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(horizontal_line_0, 0, wx.EXPAND, 10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTRE_HORIZONTAL, 10)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND, 10)
        main_sizer.Add(sizer, 0, wx.ALL | wx.EXPAND, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_listctrl_panel(self, panel):

        self.peaklist = ListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES, column_info=self._peaklist_peaklist)
        for col in range(len(self._peaklist_peaklist)):
            item = self._peaklist_peaklist[col]
            order = col
            name = item["name"]
            width = 0
            if item["show"]:
                width = item["width"]
            self.peaklist.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_CENTER)
            self.peaklist.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        self.peaklist.Bind(wx.EVT_LIST_COL_CLICK, self.on_column_click)
        self.peaklist.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click_on_item)

        self.peaklist.OnCheckItem = self.on_check_item

    def on_double_click_on_item(self, evt):
        """Process double-click event"""
        pass

    def on_get_item_information(self, item_id):
        """Get data inforamtion"""
        information = self.peaklist.on_get_item_information(item_id)

        return information

    @signal_blocker
    def on_column_click(self, evt):
        """Overloaded on_column_click"""
        self.peaklist.on_column_click(evt)
        self.on_update_import_info()

    def on_check_item(self, index, flag):
        "flag is True if the item was checked, False if unchecked"
        if not self._block:
            self.on_update_import_info()

    def on_update_info(self):
        """Update processing parameters"""
        info = ""
        if self.config.ms_process_linearize:
            info += f"Linearize \n"
            info += f"  Mode: {self.config.ms_linearization_mode}\n"
            info += f"  Auto-range: {self.config.ms_auto_range}\n"
            if not self.config.ms_auto_range:
                try:
                    info += f"  m/z range: {self.config.ms_mzStart:.2f} - {self.config.ms_mzEnd:.2f}"
                    info += " (if broader than raw data, it will be cropped appropriately)\n"
                except TypeError:
                    pass
            info += f"  bin size: {self.config.ms_mzBinSize}\n"

        if not info:
            info += "By default, ORIGAMI will pick common mass range (by looking at all the m/z range of each file)\n"
            info += "and use modest 0.01 Da bin size with 'Linear interpolation'"
            self.processing_label.SetForegroundColour(wx.RED)
        else:
            self.processing_label.SetForegroundColour(wx.BLACK)

        self.processing_label.SetLabel(info)

    def on_update_import_info(self):
        """Update import information"""
        n_checked, mz_range, im_on, __ = self.get_list_parameters()

        if not mz_range or not im_on:
            self.import_label.SetLabel("Please load files first")
            self.import_label.SetForegroundColour(wx.RED)
            return

        color = wx.BLACK
        if isinstance(mz_range, list) or isinstance(im_on, list):
            color = wx.RED
        self.import_label.SetForegroundColour(color)

        info = f"Number of files: {n_checked}\n"
        info += f"Mass range: {mz_range}\n"
        info += f"Ion mobility: {im_on}"
        self.import_label.SetLabel(info)

    def on_select_document(self, evt):
        """Select document from the list of current documents (or create a new one) and restore previous metadata"""
        document = self.data_handling._get_document_of_type("Type: Imaging")
        if not document:
            raise MessageError("Error", "Please select document in order to load processing metadata")

        if document:
            logger.info(f"Found document: {document.title}")

        # restore pre-processing parameters
        metadata = document.metadata.get("imaging_lesa")
        if metadata:
            self.config.ms_process_linearize = True
            self.config.ms_linearization_mode = metadata.get("linearization_mode", "Linear interpolation")
            self.config.ms_mzStart = metadata.get("mz_min")
            self.config.ms_mzEnd = metadata.get("mz_max")
            self.config.ms_mzBinSize = metadata.get("mz_bin")
            self.config.ms_auto_range = False
            self.on_update_info()

        # restore dataset filenames
        for spec_dataset in document.multipleMassSpectrum.values():
            file_information = spec_dataset.get("file_information", None)
            if not file_information:
                continue
            # add to table
            self.peaklist.Append(
                [
                    "",
                    file_information["index"],
                    file_information["filename"],
                    file_information["path"],
                    file_information["mz_range"],
                    file_information["n_scans"],
                    file_information["scan_range"],
                    str(file_information["ion_mobility"]),
                ]
            )

    def on_update_settings(self, evt):
        """Open data processing window"""
        self.document_tree.on_open_process_MS_settings(
            disable_plot=True, disable_process=True, update_widget="widget.imaging.import.update.spectrum"
        )

    def on_select_files(self, evt):
        """Select files"""

        def get_file_idx(path):
            __, file = os.path.split(path)
            idx = file.split("_")[-1]
            idx = idx.split(".raw")[0]
            return idx

        # get paths
        filelist = self.data_handling.on_select_LESA_MassLynx_raw()
        # check paths
        if not all([path.endswith(".raw") for path in filelist]):
            raise ValueError(f"One of the selected paths is not of Waters type")

        # read mass range
        for path in filelist:
            __, filename = os.path.split(path)
            if self.check_present(filename):
                logger.warning(f"File {filename} already in the list")
                continue

            # get data
            idx = get_file_idx(path)
            try:
                idx = int(idx)
            except TypeError:
                logger.warning(f"Could not identify the index of {filename}")

            reader = self.data_handling.get_waters_api_reader(path)
            ms_fcn = reader.stats_in_functions[0]
            dt_fcn = reader.stats_in_functions.get(1, False)
            mz_range = ms_fcn["mass_range"]
            n_scans = ms_fcn["n_scans"]
            scan_range = f"0-{n_scans-1}"
            is_im = True if dt_fcn else False

            # add to table
            self.peaklist.Append(
                ["", idx, filename, path, f"{mz_range[0]}-{mz_range[1]}", f"{n_scans}", scan_range, str(is_im)]
            )

        self.on_update_import_info()

    def check_present(self, filename):
        """Check if filename exists in the table"""
        n_rows = self.peaklist.GetItemCount()

        for item_id in range(n_rows):
            information = self.on_get_item_information(item_id)
            if information["filename"] == filename:
                return True
        return False

    def on_clear_files(self, evt):
        """Clear filelist from existing files"""
        from gui_elements.misc_dialogs import DialogBox

        dlg = DialogBox(
            exceptionTitle="Would you like to continue?",
            exceptionMsg="Are you sure you want to clear the filelist? This action cannot be undone.",
            type="Question",
        )
        if dlg == wx.ID_NO:
            msg = "Cancelled was operation"
            logger.info(msg)
            return

        self.peaklist.DeleteAllItems()
        self.on_update_import_info()

    def get_list_parameters(self):
        """Retrieve list parameters"""
        n_rows = self.peaklist.GetItemCount()

        n_checked = 0
        mz_range = []
        im_on = []
        scan_range = []
        if not n_rows:
            return n_checked, mz_range, im_on, scan_range

        for item_id in range(n_rows):
            information = self.on_get_item_information(item_id)
            n_checked += 1 if information["check"] else 0
            mz_range.append(information["mz_range"])
            im_on.append(information["ion_mobility"])
            scan_range.append(information["scan_range"])

        mz_range = list(set(mz_range))
        im_on = list(set(im_on))

        mz_range = mz_range if len(mz_range) > 1 else mz_range[0]
        im_on = im_on if len(im_on) > 1 else im_on[0]

        return n_checked, mz_range, im_on, scan_range

    def get_extraction_filelist(self):
        """Retrieve list parameters for data extraction"""
        from utils.converters import str2int

        n_rows = self.peaklist.GetItemCount()

        filelist = []
        for item_id in range(n_rows):
            information = self.on_get_item_information(item_id)
            if information["check"]:
                path = information["path"]
                idx = information["index"]
                scan_range = information["scan_range"]
                scan_min, scan_max = scan_range.split("-")
                filelist.append([idx, path, str2int(scan_min), str2int(scan_max), information])
        return filelist

    def get_extraction_processing_parameters(self):
        """Retrieve processing parameters"""
        from utils.converters import str2num
        from utils.converters import str2bool
        from utils.ranges import get_min_max

        n_checked, mz_range, im_on, __ = self.get_list_parameters()
        if not n_checked:
            raise MessageError("Error", "Please tick items in the item list before trying to import data.")

        # check image dimensions
        x_dim = self.image_shape_x.GetValue()
        y_dim = self.image_shape_y.GetValue()
        n_files = self.peaklist.GetItemCount()

        if x_dim * y_dim == 0:
            raise MessageError("Error", "Please fill-in image dimensions information!")
        if x_dim * y_dim != n_files:
            raise MessageError("Error", "The number of files does not match image dimensions!")

        # get mass range
        mz_range_out = []
        if isinstance(mz_range, list):
            for _mz_range in mz_range:
                mz_min, mz_max = _mz_range.split("-")
                mz_range_out.extend([str2num(mz_min), str2num(mz_max)])
        else:
            mz_min, mz_max = mz_range.split("-")
            mz_range_out.extend([str2num(mz_min), str2num(mz_max)])

        mz_min, mz_max = get_min_max(mz_range_out)

        if not self.config.ms_process_linearize:
            linearization_mode = "Linear interpolation"
            mz_bin = 0.01
        else:
            linearization_mode = self.config.ms_linearization_mode
            mz_bin = self.config.ms_mzBinSize

        mz_min = max([self.config.ms_mzStart, mz_min])
        mz_max = min([self.config.ms_mzEnd, mz_max])

        # check for ion mobility
        im_on_out = False
        if isinstance(im_on, str):
            im_on_out = str2bool(im_on)

        # build kwargs
        kwargs = dict(
            linearization_mode=linearization_mode,
            mz_min=mz_min,
            mz_max=mz_max,
            mz_bin=mz_bin,
            im_on=im_on_out,
            auto_range=False,
            x_dim=x_dim,
            y_dim=y_dim,
        )

        return kwargs

    def on_import(self, evt):
        """Initilize data import"""
        filelist = self.get_extraction_filelist()
        kwargs = self.get_extraction_processing_parameters()

        self.data_handling.on_open_multiple_LESA_files_fcn(filelist, **kwargs)
