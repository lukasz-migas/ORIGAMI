# Standard library imports
import os
import logging
from enum import IntEnum
from typing import Dict
from typing import List
from typing import Optional

# Third-party imports
import wx
from pubsub import pub

# Local imports
# from origami.styles import make_menu_item
from origami.styles import MiniFrame
from origami.styles import set_item_font
from origami.styles import make_menu_item
from origami.styles import make_bitmap_btn
from origami.icons.assets import Icons
from origami.objects.misc import FileItem
from origami.config.config import CONFIG
from origami.utils.converters import str2num
from origami.utils.decorators import signal_blocker
from origami.utils.exceptions import MessageError
from origami.config.environment import ENV
from origami.gui_elements.panel_base import TableMixin

logger = logging.getLogger(__name__)


class TableColumnIndex(IntEnum):
    check = 0
    filename = 1
    path = 2
    variable = 3
    mz_range = 4
    n_scans = 5
    scan_range = 6
    im_check = 7
    document = 8


class PanelImportManagerBase(MiniFrame, TableMixin):
    """Generic file manager"""

    TABLE_DICT = {
        0: {"name": "", "tag": "check", "type": "bool", "order": 0, "id": wx.NewIdRef(), "show": True, "width": 20},
        1: {
            "name": "filename",
            "tag": "filename",
            "type": "str",
            "order": 1,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 100,
        },
        2: {"name": "path", "tag": "path", "type": "str", "order": 2, "id": wx.NewIdRef(), "show": True, "width": 220},
        3: {
            "name": "variable",
            "tag": "variable",
            "type": "float",
            "order": 3,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 80,
        },
        4: {
            "name": "m/z range",
            "tag": "mz_range",
            "type": "str",
            "order": 4,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 80,
        },
        5: {
            "name": "# scans",
            "tag": "n_scans",
            "type": "str",
            "order": 5,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 55,
        },
        6: {
            "name": "scan range",
            "tag": "scan_range",
            "type": "str",
            "order": 6,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 80,
        },
        7: {
            "name": "IM",
            "tag": "ion_mobility",
            "type": "str",
            "order": 7,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 40,
        },
        8: {
            "name": "document",
            "tag": "document",
            "type": "str",
            "order": 8,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 100,
        },
    }
    TABLE_COLUMN_INDEX = TableColumnIndex
    TABLE_STYLE = wx.LC_REPORT | wx.LC_VRULES | wx.LC_HRULES | wx.LC_SINGLE_SEL
    TABLE_ALLOWED_EDIT = [TABLE_COLUMN_INDEX.variable]

    HELP_MD = """## Table controls

    Double-click on an item will open new window where you can change the index/variable value of the selected item
    Double-click + CTRL button will check/uncheck the selected item
    """
    HELP_LINK = "https://origami.lukasz-migas.com/"

    # module specific parameters
    DOCUMENT_TYPE = None
    PUB_SUBSCRIBE_EVENT = None
    SUPPORTED_FILE_FORMATS = [".raw"]
    DIALOG_SIZE = (800, 600)
    USE_COLOR = False
    CONFIG_NAME = None

    # UI elements
    main_sizer = None
    info_label = None
    info_btn = None
    import_label = None
    import_btn = None
    processing_label = None
    processing_btn = None
    select_document_btn = None
    select_files_btn = None
    clear_files_btn = None

    def __init__(self, parent, presenter, **kwargs):
        MiniFrame.__init__(
            self,
            parent,
            title=kwargs.pop("title", "Import multiple raw files"),
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
            bind_key_events=False,
        )
        TableMixin.__init__(self)

        self.parent = parent
        self.presenter = presenter
        self._icons = Icons()
        self._block = False
        self.document_title = ""
        self._last_dir = ""

        # make gui items
        self.make_gui()
        self.on_update_info()

        # subscribe to events
        self.subscribe()
        self.bind_events()
        self.setup()

    def setup(self):
        """Finalizes setting up of the panel"""

    @property
    def data_handling(self):
        raise NotImplementedError("Must implement method")

    @property
    def document_tree(self):
        raise NotImplementedError("Must implement method")

    def on_update_implementation(self, metadata):
        """Update UI elements of the implementation"""
        pass

    def make_implementation_panel(self, panel):
        return None

    def on_double_click_on_item(self, evt):
        """Process double-click event"""
        from origami.gui_elements.misc_dialogs import DialogSimpleAsk

        info = self.on_get_item_information()
        if hasattr(evt, "ControlDown") and evt.ControlDown():  # noqa
            self.peaklist.CheckItem(self.peaklist.item_id, not info["check"])
        else:
            value = DialogSimpleAsk(
                "Please specify index value", "Please specify index value", info["variable"], "float"
            )
            if value is not None:
                self.on_update_value_in_peaklist(self.peaklist.item_id, "variable", value)

    def get_parameters_implementation(self):
        """Retrieve processing parameters that are specific for the implementation"""
        return dict()

    @signal_blocker
    def on_column_click(self, evt):
        """Overloaded on_column_click"""
        self.peaklist.on_column_click(evt)
        self.on_update_import_info()

    def on_update_document(self, item_id: Optional[int] = None, item_info: Optional[Dict] = None):
        pass

    def on_menu_item_right_click(self, evt):
        self.peaklist.item_id = evt.GetIndex()

        menu = wx.Menu()
        menu_edit = make_menu_item(parent=menu, text="Edit\tDouble-click", bitmap=self._icons["edit"])
        menu.Append(menu_edit)
        menu_remove = make_menu_item(parent=menu, text="Remove item\tDelete", bitmap=self._icons["bin"])
        menu.Append(menu_remove)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_double_click_on_item, menu_edit)
        self.Bind(wx.EVT_MENU, self.on_delete_item, menu_remove)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_close(self, evt):
        """Destroy this frame"""
        if self.PUB_SUBSCRIBE_EVENT:
            pub.unsubscribe(self.on_update_info, self.PUB_SUBSCRIBE_EVENT)
        self.Destroy()

    def subscribe(self):
        """Initialize PubSub subscribers"""
        if self.PUB_SUBSCRIBE_EVENT:
            pub.subscribe(self.on_update_info, self.PUB_SUBSCRIBE_EVENT)

    def bind_events(self):
        """Bind extra events"""
        self.peaklist.OnCheckItem = self.on_check_item

    def make_gui(self):
        """Combine all widgets into one window"""

        # make panel
        settings_panel = self.make_panel(self)
        settings_panel.SetMinSize(self.DIALOG_SIZE)

        # pack elements
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(settings_panel, 1, wx.EXPAND, 0)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)
        self.Layout()

        self.CentreOnScreen()
        self.SetFocus()

    def make_panel(self, split_panel):
        """Combine various subsections of the panel into one cohesive UI"""
        # instantiate panel for the entire UI
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="info")

        # collect info panel
        grid, btn_grid = self.make_info_panel(panel)

        # instantiate table
        self.peaklist = self.make_table(self.TABLE_DICT, panel)

        # get implementation panel
        impl_sizer = self.make_implementation_panel(panel)

        # instantiate import section
        import_sizer = self.make_import_panel(panel)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTRE_HORIZONTAL, 10)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND, 10)

        if impl_sizer is not None:
            main_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 10)
            main_sizer.Add(impl_sizer, 0, wx.ALL | wx.EXPAND, 5)

        main_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 10)
        main_sizer.Add(import_sizer, 0, wx.ALL | wx.EXPAND, 5)

        self.info_btn = make_bitmap_btn(
            panel, wx.ID_ANY, self._icons["info"], style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        self.info_btn.Bind(wx.EVT_BUTTON, self.on_open_info)
        main_sizer.Add(self.info_btn, 0, wx.ALIGN_RIGHT)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_import_panel(self, panel):
        """Make import sub-panel that allows user to import data"""
        import_label = set_item_font(wx.StaticText(panel, wx.ID_ANY, "Import information"))
        self.import_label = wx.StaticText(panel, wx.ID_ANY, "", size=(-1, 60))

        self.import_btn = wx.Button(panel, wx.ID_OK, "Import", size=(-1, 22))
        self.import_btn.Bind(wx.EVT_BUTTON, self.on_import)

        label_sizer = wx.BoxSizer(wx.VERTICAL)
        label_sizer.Add(import_label)
        label_sizer.Add(self.import_label, 1)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(label_sizer, 1)
        sizer.AddSpacer(20)
        sizer.Add(self.import_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        return sizer

    def make_info_panel(self, panel):
        """Make information sub-panel that informs the user of what to do"""
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

        # pack buttons
        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.select_document_btn, (n, 0), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.select_files_btn, (n, 1), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.processing_btn, (n, 2), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.clear_files_btn, (n, 3), flag=wx.ALIGN_CENTER)

        return grid, btn_grid

    def on_check_item(self, _index, _flag):
        """flag is True if the item was checked, False if unchecked"""
        if not self._block:
            self.on_update_import_info()

    def on_update_info(self):
        """Update processing parameters"""
        info = ""
        if CONFIG.ms_process_linearize:
            info += f"Linearize \n"
            info += f"    Mode: {CONFIG.ms_linearization_mode}\n"
            info += f"    Auto-range: {CONFIG.ms_auto_range}\n"
            if not CONFIG.ms_auto_range:
                try:
                    info += f"    m/z range: {CONFIG.ms_mzStart:.2f} - {CONFIG.ms_mzEnd:.2f}"
                    info += " (if broader than raw data, it will be cropped appropriately)\n"
                except TypeError:
                    pass
            info += f"    bin size: {CONFIG.ms_mzBinSize}\n"
        if not info:
            info += "By default, ORIGAMI will pick common mass range (by looking at all the m/z range of each file)\n"
            info += "and use modest 0.01 Da bin size with 'Linear interpolation'\n\n"
            self.processing_label.SetForegroundColour(wx.RED)
        else:
            self.processing_label.SetForegroundColour(wx.BLACK)

        if CONFIG.ms_process_threshold:
            info += f"Subtract baseline \n"
            info += f"   Mode: {CONFIG.ms_baseline}"

        self.processing_label.SetLabel(info)

    def _on_get_document(self):
        """Get instance of selected document - the dialog also allows the user to load already existing document that
        is not found in the environment or create a new one if one does not exist."""
        from origami.gui_elements.dialog_select_document import DialogSelectDocument

        document_title = None

        dlg = DialogSelectDocument(self, document_type=self.DOCUMENT_TYPE)
        if dlg.ShowModal() == wx.ID_OK:
            document_title = dlg.current_document
        dlg.Destroy()

        if document_title is not None:
            return ENV[document_title]

    def on_select_document(self, _):
        """Select document from the list of current documents (or create a new one) and restore previous metadata"""

        document = self._on_get_document()

        if not document:
            raise MessageError("Error", "Please select document in order to load processing metadata")

        if document:
            logger.info(f"Found document: {document.title}")

        # restore pre-processing parameters
        metadata = dict()
        if self.CONFIG_NAME is not None:
            metadata = document.get_config(self.CONFIG_NAME)

        if metadata:
            # linearization
            CONFIG.ms_process_linearize = True
            CONFIG.ms_linearization_mode = metadata.get("linearization_mode", "Linear interpolation")
            CONFIG.ms_mzStart = metadata.get("mz_min", CONFIG.ms_mzStart)
            CONFIG.ms_mzEnd = metadata.get("mz_max", CONFIG.ms_mzEnd)
            CONFIG.ms_mzBinSize = metadata.get("mz_bin", CONFIG.ms_mzBinSize)
            CONFIG.ms_auto_range = False

            # baseline
            CONFIG.ms_process_threshold = metadata.get("baseline_correction", CONFIG.ms_process_threshold)
            CONFIG.ms_baseline = metadata.get("baseline_method", CONFIG.ms_baseline)
            CONFIG.ms_threshold = metadata.get("baseline_threshold", CONFIG.ms_threshold)
            CONFIG.ms_baseline_polynomial_order = metadata.get(
                "baseline_polynomial_order", CONFIG.ms_baseline_polynomial_order
            )
            CONFIG.ms_baseline_curved_window = metadata.get("baseline_curved_window", CONFIG.ms_baseline_curved_window)
            CONFIG.ms_baseline_median_window = metadata.get("baseline_median_window", CONFIG.ms_baseline_median_window)
            CONFIG.ms_baseline_tophat_window = metadata.get("baseline_tophat_window", CONFIG.ms_baseline_tophat_window)
            self.on_update_info()
            self.on_update_implementation(metadata)

        self.document_title = document.title

        # restore dataset filenames
        mass_spectra = document["MassSpectra"]
        for name in mass_spectra:
            obj = mass_spectra[name]
            if "file_info" not in obj.attrs:
                continue
            file_information = obj.attrs["file_info"]["information"]
            if not file_information:
                continue
            self.on_add_to_table(
                dict(
                    filename=file_information["filename"],
                    path=file_information["path"],
                    variable=file_information["variable"],
                    mz_range=file_information["mz_range"],
                    n_scans=file_information["n_scans"],
                    scan_range=file_information["scan_range"],
                    ion_mobility=str(file_information["ion_mobility"]),
                    document=file_information["document"],
                )
            )

    def on_update_settings(self, _):
        """Open data processing window"""
        self.document_tree.on_open_process_MS_settings(
            disable_plot=True, disable_process=True, update_widget=self.PUB_SUBSCRIBE_EVENT
        )

    def on_get_files(self):
        """Collects a list of files from directory"""
        from origami.gui_elements.dialog_multi_directory_picker import DialogMultiDirPicker

        dlg = DialogMultiDirPicker(self, extension=self.SUPPORTED_FILE_FORMATS, last_dir=self._last_dir)
        if dlg.ShowModal() == "ok":
            pathlist = dlg.get_paths()
            self._last_dir = dlg.last_path
            return pathlist
        return []

    def _parse_path(self, path):
        """Parses path and returns appropriate data

        This method should be overwritten to provide correct data in the table
        """
        return dict()

    def _check_paths(self, filelist):
        """Checks whether all paths in the filelist match the correct format"""

        for extension in self.SUPPORTED_FILE_FORMATS:
            if not all([path.endswith(extension) for path in filelist]):
                raise ValueError(
                    f"One or more of the selected paths does not have the correct file extension "
                    f"({self.SUPPORTED_FILE_FORMATS})"
                )

    def on_select_files(self, _):
        """Select files"""
        filelist = self.on_get_files()

        self._check_paths(filelist)

        # read mass range
        for path in filelist:
            __, filename = os.path.split(path)
            if self.check_present(filename):
                logger.warning(f"File {filename} already in the list")
                continue

            parsed_data = self._parse_path(path)

            self.on_add_to_table(dict(filename=filename, path=path, document=self.document_title, **parsed_data))

        self.on_update_import_info()

    def check_present(self, filename):
        """Check if filename exists in the table"""
        n_rows = self.peaklist.GetItemCount()

        for item_id in range(n_rows):
            information = self.on_get_item_information(item_id)
            if information["filename"] == filename:
                return True
        return False

    def on_clear_files(self, _):
        """Clear filelist from existing files"""
        # self.on_delete_all(None)
        self.on_delete_selected(None)
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

    def get_extraction_filelist(self) -> List[FileItem]:
        """Retrieve list parameters for data extraction"""
        from origami.utils.converters import str2int

        filelist = []
        for item_id in range(self.n_rows):
            information = self.on_get_item_information(item_id)
            if information["check"]:
                path = information["path"]
                variable = information["variable"]
                im_on = information["ion_mobility"]
                scan_range = information["scan_range"]
                scan_min, scan_max = scan_range.split("-")
                mz_range = information["mz_range"]
                mz_min, mz_max = mz_range.split("-")
                filelist.append(
                    FileItem(
                        variable,
                        path,
                        [str2int(scan_min), str2int(scan_max)],
                        [str2num(mz_min), str2num(mz_max)],
                        im_on,
                        information,
                    )
                )
        return filelist

    def get_parameters(self):
        """Retrieve processing parameters"""
        from origami.utils.converters import str2num
        from origami.utils.converters import str2bool
        from origami.utils.ranges import get_min_max

        n_checked, mz_range, im_on, __ = self.get_list_parameters()
        if not n_checked:
            raise MessageError("Error", "Please tick items in the item list before trying to import data.")

        # check image dimensions
        impl_kwargs = self.get_parameters_implementation()

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

        if not CONFIG.ms_process_linearize:
            linearization_mode = "Linear interpolation"
            mz_bin = 0.01
        else:
            linearization_mode = CONFIG.ms_linearization_mode
            mz_bin = CONFIG.ms_mzBinSize

        mz_min = max([CONFIG.ms_mzStart, mz_min])
        mz_max = min([CONFIG.ms_mzEnd, mz_max])

        # check for ion mobility
        im_on_out = False
        if isinstance(im_on, str):
            im_on_out = str2bool(im_on)

        # build kwargs
        kwargs = dict(
            linearization_mode=linearization_mode,
            x_min=mz_min,
            x_max=mz_max,
            bin_size=mz_bin,
            auto_range=False,
            im_on=im_on_out,
            baseline_correction=CONFIG.ms_process_threshold,
            baseline_method=CONFIG.ms_baseline,
            baseline_threshold=CONFIG.ms_threshold,
            baseline_polynomial_order=CONFIG.ms_baseline_polynomial_order,
            baseline_curved_window=CONFIG.ms_baseline_curved_window,
            baseline_median_window=CONFIG.ms_baseline_median_window,
            baseline_tophat_window=CONFIG.ms_baseline_tophat_window,
            **impl_kwargs,
        )

        return kwargs

    def on_update_import_info(self):
        """Update import information"""
        info, color = self._on_update_import_info()
        self.import_label.SetForegroundColour(color)
        self.import_label.SetLabel(info)

    def on_import(self, _):
        """Initialize data import"""
        filelist = self.get_extraction_filelist()
        kwargs = self.get_parameters()

        self._import(filelist, **kwargs)

    def _import(self, filelist: List[FileItem], **parameters: Dict):
        """Actual implementation of how data should be imported

        Parameters
        ----------
        filelist : List[FileItem]
            list containing all necessary data and metadata to perform data import
        parameters : Dict
            dictionary containing pre-processing parameters
        """
        raise NotImplementedError("Must implement method")

    def _on_update_import_info(self):
        """Returns string to be inserted into the import label"""
        n_checked, mz_range, im_on, __ = self.get_list_parameters()

        if not mz_range or not im_on:
            return "Please load files first", wx.RED

        color = wx.BLACK
        if isinstance(mz_range, list) or isinstance(im_on, list):
            color = wx.RED

        info = f"Number of files: {n_checked}\n"
        info += f"Mass range: {mz_range}\n"
        info += f"Ion mobility: {im_on}"

        return info, color


def main():

    app = wx.App()
    ex = PanelImportManagerBase(None, None)
    ex.on_add_to_table({"variable": 1})
    ex.on_add_to_table({"variable": 4})

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
