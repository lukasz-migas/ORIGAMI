"""DocumentTree panel"""
# Standard library imports
import gc
import os
import time
import logging
from copy import deepcopy
from functools import partial

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.ids import ID_saveData_csv
from origami.ids import ID_saveData_hdf
from origami.ids import ID_xlabel_1D_ms
from origami.ids import ID_ylabel_2D_ms
from origami.ids import ID_xlabel_1D_ccs
from origami.ids import ID_xlabel_2D_ccs
from origami.ids import ID_ylabel_2D_ccs
from origami.ids import ID_saveData_excel
from origami.ids import ID_xlabel_1D_bins
from origami.ids import ID_ylabel_2D_bins
from origami.ids import ID_ylabel_DTMS_ms
from origami.ids import ID_saveData_pickle
from origami.ids import ID_xlabel_2D_scans
from origami.ids import ID_xlabel_RT_scans
from origami.ids import ID_showPlotDocument
from origami.ids import ID_xlabel_2D_custom
from origami.ids import ID_ylabel_2D_custom
from origami.ids import ID_ylabel_DTMS_bins
from origami.ids import ID_xlabel_1D_restore
from origami.ids import ID_xlabel_2D_actVolt
from origami.ids import ID_xlabel_2D_colVolt
from origami.ids import ID_xlabel_2D_restore
from origami.ids import ID_xlabel_RT_actVolt
from origami.ids import ID_xlabel_RT_colVolt
from origami.ids import ID_xlabel_RT_restore
from origami.ids import ID_ylabel_2D_restore
from origami.ids import ID_xlabel_2D_labFrame
from origami.ids import ID_xlabel_2D_time_min
from origami.ids import ID_xlabel_RT_labFrame
from origami.ids import ID_xlabel_RT_time_min
from origami.ids import ID_getSelectedDocument
from origami.ids import ID_ylabel_DTMS_restore
from origami.ids import ID_xlabel_1D_ms_arrival
from origami.ids import ID_ylabel_2D_ms_arrival
from origami.ids import ID_xlabel_2D_actLabFrame
from origami.ids import ID_xlabel_2D_retTime_min
from origami.ids import ID_xlabel_RT_actLabFrame
from origami.ids import ID_xlabel_RT_retTime_min
from origami.ids import ID_ylabel_DTMS_ms_arrival
from origami.icons.assets import Icons
from origami.utils.secret import get_short_hash
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.objects.document import DocumentStore
from origami.utils.converters import byte2str
from origami.utils.exceptions import MessageError
from origami.config.environment import ENV
from origami.gui_elements.popup import PopupBase
from origami.objects.containers import IonHeatmapObject
from origami.objects.containers import MobilogramObject
from origami.objects.containers import ChromatogramObject
from origami.objects.containers import MassSpectrumObject
from origami.objects.containers import MassSpectrumHeatmapObject
from origami.gui_elements.mixins import DocumentationMixin
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_menu_item
from origami.handlers.query_handler import QUERY_HANDLER
from origami.gui_elements.misc_dialogs import DialogBox
from origami.gui_elements.misc_dialogs import DialogNumberAsk
from origami.gui_elements.misc_dialogs import DialogSimpleAsk

LOGGER = logging.getLogger(__name__)


class Item:
    """Container object to keep track of which item is selected in the Document Tree"""

    def __init__(self):
        self.data = None
        self.title = None
        self.root = None
        self.branch = None
        self.leaf = None
        self.indent = None
        self.current = None

    def __repr__(self):
        return (
            f"Item<\n\ttitle={self.title};\n\troot={self.root};\n\tbranch={self.branch}; "
            f"\n\tleaf={self.leaf};\n\tcurrent={self.current}\n\tindent={self.indent}\n>"
        )

    def update(self, title=None, root=None, branch=None, leaf=None, indent=None, current=None, data=None):
        """Update data"""
        self.title = title
        self.root = root
        self.branch = branch
        self.leaf = leaf
        self.indent = indent
        self.current = current
        self.data = data

    @property
    def data_type(self):
        """Get data type of the document object"""
        self.check_data()
        return self.data.data_type

    @property
    def document_title(self):
        """Get document title of the document object"""
        self.check_data()
        return self.data.title

    @property
    def parameters(self):
        """Get parameters of t he document object"""
        self.check_data()
        if hasattr(self.data, "parameters"):
            return self.data.parameters
        return dict()

    @property
    def is_empty(self):
        """Check where document is empty"""
        return self.data is None

    def check_data(self):
        """Checks whether the current item is empty and if so, gets the last reset document from the environment"""
        if self.data is None:
            try:
                self.data = ENV.on_get_document()
            except KeyError:
                pass

    @property
    def is_group(self):
        """Returns `True` if the current item is the group object (e.g. Mass Spectra)"""
        return self.indent == 2

    @property
    def is_dataset(self):
        """Returns `True` if the current item is a dataset object (e.g. Summed Chromatogram)"""
        return self.indent == 3

    @property
    def is_annotation(self):
        """Returns `True` if the current item is an annotation on the dataset object (e.g. UniDec or Annotations)"""
        return self.indent == 3

    def is_match(self, which, parent: bool = False):
        """Checks whether current selection matches that of a pre-defined data group"""
        check = dict(
            chromatogram=["Chromatograms"],
            spectrum=["Mass Spectra"],
            mobilogram=["Mobilograms"],
            heatmap=["Heatmaps"],
            msdt=["Heatmaps (MS/DT)"],
            annotation=["Annotations"],
            unidec=["UniDec"],
            calibration=["Calibration (CCS)"],
            overlay=["Overlays"],
        )

        item_list = []
        if isinstance(which, str):
            item_list = check.get(which, [])
        elif isinstance(which, list):
            for key in which:
                item_list.extend(check.get(key, []))
        if not item_list:
            return False

        #         is_branch = self.branch in item_list
        is_leaf = self.leaf in item_list
        is_current = self.current in item_list

        if parent:
            if is_leaf and is_current:
                return True
        else:
            if is_current:
                return True
        return False

    def get_query(self, return_subkey: bool = False):
        """Returns query and subkey information about the currently selected item

        This function is mostly used to have an idea what was clicked to display right-click menu on request and such
        """
        subkey = ["", ""]
        query = ["", "", ""]
        item_root = self.root
        item_branch = self.branch
        item_leaf = self.leaf

        if self.indent == 0:
            query = ["Documents", "", ""]
        elif self.indent == 1:
            query = [self.branch, self.leaf, self.leaf]
        elif self.indent == 2:
            query = [self.branch, self.leaf, self.leaf]
        elif self.indent == 3:
            # these are only valid when attached to `main` components of the document
            if self.leaf in ["Annotations", "UniDec"]:
                subkey = [self.leaf, ""]
                item_leaf = self.branch
            query = [item_root, self.branch, item_leaf]
        elif self.indent == 4:
            if item_leaf in ["Annotations", "UniDec"]:
                subkey = [item_leaf, ""]
            if self.branch in ["Annotations", "UniDec"]:
                subkey = [self.branch, self.leaf]
                item_branch = item_root
            query = [self.document_title, item_root, item_branch]
        elif self.indent == 5:
            query = [self.document_title, self.current, item_root]
            subkey = [item_branch, item_leaf]

        if return_subkey:
            return query, subkey
        return query

    def get_name(self, stem: str):
        """Get filename based on the document title"""
        assert isinstance(stem, str)
        item = self.leaf.replace(" ", "-")
        if stem == "":
            return item
        return f"{stem}_{item}"


class PopupDocumentTreeSettings(PopupBase):
    """Create popup window to modify few uncommon settings"""

    item_delete_ask_document_check = None
    item_delete_ask_group_check = None
    item_delete_ask_item_check = None
    item_highlight_check = None
    item_auto_plot_check = None

    def __init__(self, parent, style=wx.BORDER_SIMPLE):
        PopupBase.__init__(self, parent, style)

    def make_panel(self):
        """Make popup window"""
        self.item_delete_ask_document_check = make_checkbox(self, "")
        self.item_delete_ask_document_check.SetValue(CONFIG.tree_panel_delete_document_ask)
        self.item_delete_ask_document_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(
            self.item_delete_ask_document_check,
            "When checked, you will be asked whether you want to continue with deletion of the document. "
            "(Data will remain on the disk)",
        )

        self.item_delete_ask_group_check = make_checkbox(self, "")
        self.item_delete_ask_group_check.SetValue(CONFIG.tree_panel_delete_group_ask)
        self.item_delete_ask_group_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(
            self.item_delete_ask_group_check,
            "When checked, you will be asked whether you want to continue with deletion of the group item and "
            "all of its contents.",
        )

        self.item_delete_ask_item_check = make_checkbox(self, "")
        self.item_delete_ask_item_check.SetValue(CONFIG.tree_panel_delete_item_ask)
        self.item_delete_ask_item_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(
            self.item_delete_ask_item_check,
            "When checked, you will be asked whether you want to continue with deletion of the item.",
        )

        self.item_highlight_check = make_checkbox(self, "")
        self.item_highlight_check.SetValue(CONFIG.tree_panel_item_highlight)
        self.item_highlight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.item_highlight_check, "When checked, currently selected items will be made bold.")

        self.item_auto_plot_check = make_checkbox(self, "")
        self.item_auto_plot_check.SetValue(CONFIG.tree_panel_item_auto_plot)
        self.item_auto_plot_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(
            self.item_auto_plot_check,
            "When checked, items that can be plotted (e.g. MS) will be automatically plotted. Otherwise, "
            "just double-click on an item to view it.",
        )

        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(
            wx.StaticText(self, -1, "Ask for permission as document is being deleted:"),
            (y, 0),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(self.item_delete_ask_document_check, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(
            wx.StaticText(self, -1, "Ask for permission as group item(s) are being deleted:"),
            (y, 0),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(self.item_delete_ask_group_check, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(
            wx.StaticText(self, -1, "Ask for permission as item(s) are being deleted:"),
            (y, 0),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(self.item_delete_ask_item_check, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(
            wx.StaticText(self, -1, "Highlight items on selection:"),
            (y, 0),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(self.item_highlight_check, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(
            wx.StaticText(self, -1, "Auto-plot items on selection:"),
            (y, 0),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(self.item_auto_plot_check, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        self.set_info(sizer)

        self.SetSizerAndFit(sizer)
        self.Layout()

    def on_apply(self, evt):
        """Update settings"""
        CONFIG.tree_panel_delete_document_ask = self.item_delete_ask_document_check.GetValue()
        CONFIG.tree_panel_delete_group_ask = self.item_delete_ask_group_check.GetValue()
        CONFIG.tree_panel_delete_item_ask = self.item_delete_ask_item_check.GetValue()
        CONFIG.tree_panel_item_highlight = self.item_highlight_check.GetValue()
        CONFIG.tree_panel_item_auto_plot = self.item_auto_plot_check.GetValue()

        if evt is not None:
            evt.Skip()


class PanelDocumentTree(wx.Panel, DocumentationMixin):
    """Make documents panel to store all information about open files"""

    HELP_LINK = "www.origami.lukasz-migas.com"

    def __init__(self, parent, config, icons, presenter):
        wx.Panel.__init__(
            self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.Size(250, -1), style=wx.TAB_TRAVERSAL
        )

        self.parent = parent
        self.config = config
        self.presenter = presenter
        self.icons = icons
        self._icons = Icons()

        self.documents = self.make_ui()

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.documents, 1, wx.EXPAND, 0)
        self.sizer.Fit(self)
        self.SetSizer(self.sizer)

        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

    def __del__(self):
        pass

    def on_right_click(self, evt):
        """Right-click menu"""
        # make main menu
        menu = wx.Menu()

        menu_info = make_menu_item(
            parent=menu, evt_id=wx.ID_ANY, text="Learn more about Document Tree...", bitmap=self._icons.info
        )
        self.Bind(wx.EVT_MENU, self.on_open_info, menu_info)

        menu.Append(menu_info)
        menu_settings = make_menu_item(
            parent=menu, evt_id=wx.ID_ANY, text="Document Tree settings", bitmap=self._icons.gear
        )
        self.Bind(wx.EVT_MENU, partial(self.on_open_settings, evt), menu_settings)

        menu.Append(menu_settings)
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def make_ui(self):
        """Instantiate document tree"""
        return DocumentTree(self, self.parent, self.presenter, self.icons, self.config, size=(-1, -1))

    def on_open_settings(self, evt, _evt):
        """Open settings of the Document Tree"""
        popup = PopupDocumentTreeSettings(self.parent)
        popup.position_on_mouse()
        popup.Show()


class DocumentTree(wx.TreeCtrl):
    """Documents tree"""

    _indent_items = ["Annotations", "UniDec"]

    def __init__(
        self,
        parent,
        view,
        presenter,
        icons,
        config,
        size=(-1, -1),
        style=wx.TR_TWIST_BUTTONS | wx.TR_HAS_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT,
    ):
        wx.TreeCtrl.__init__(self, parent, size=size, style=style)

        self.parent = parent
        self.view = view
        self.presenter = presenter
        self.icons = icons
        self.config = config

        self._icons = Icons()

        self._item = Item()
        self._item_id = None
        self._indent = None
        self.title = None

        # widgets
        self._bokeh_panel = None
        self._annotate_panel = None
        self._compare_panel = None
        self._overlay_editor_panel = None
        self._overlay_viewer_panel = None
        self._interactive_editor_panel = None
        self._picker_panel = None
        self._lesa_panel = None
        self._lesa_import_panel = None
        self._manual_import_panel = None
        self._unidec_panel = None
        self._ccs_panel = None

        # set font and colour
        self.SetFont(wx.SMALL_FONT)

        # init bullets
        self.bullets = wx.ImageList(13, 12)
        self.SetImageList(self.bullets)
        self.bullets_dict = self.reset_document_tree_bullets()

        # add root
        root = self.AddRoot("Documents")
        self.SetItemImage(root, 0)

        # Add bindings
        self.Bind(wx.EVT_TREE_KEY_DOWN, self.on_keyboard_event, id=wx.ID_ANY)
        self.Bind(wx.EVT_TREE_ITEM_MENU, self.on_right_click, id=wx.ID_ANY)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_enable_document, id=wx.ID_ANY)
        self.Bind(wx.EVT_TREE_SEL_CHANGING, self.on_item_selecting, id=wx.ID_ANY)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_enable_document, id=wx.ID_ANY)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_keyboard_event, id=wx.ID_ANY)

        ENV.on_change("change", self.env_update_document)
        ENV.on_change("add", self._env_on_change)
        ENV.on_change("rename", self._env_on_change)
        ENV.on_change("delete", self._env_on_change)

    def _env_on_change(self, evt, metadata):
        print(evt, metadata)
        if evt == "add":
            self.add_document(ENV[metadata])
        elif evt == "delete":
            self.remove_document(metadata)

    def _bind_change_label_events(self):
        for xID in [
            ID_xlabel_2D_scans,
            ID_xlabel_2D_colVolt,
            ID_xlabel_2D_actVolt,
            ID_xlabel_2D_labFrame,
            ID_xlabel_2D_actLabFrame,
            #             ID_xlabel_2D_massToCharge,
            #             ID_xlabel_2D_mz,
            #             ID_xlabel_2D_wavenumber,
            ID_xlabel_2D_restore,
            ID_xlabel_2D_ccs,
            #             ID_xlabel_2D_charge,
            ID_xlabel_2D_custom,
            ID_xlabel_2D_time_min,
            ID_xlabel_2D_retTime_min,
        ]:
            self.Bind(wx.EVT_MENU, self.on_change_x_values_and_labels, id=xID)

        for yID in [
            ID_ylabel_2D_bins,
            ID_ylabel_2D_ms,
            ID_ylabel_2D_ms_arrival,
            ID_ylabel_2D_ccs,
            ID_ylabel_2D_restore,
            ID_ylabel_2D_custom,
        ]:
            self.Bind(wx.EVT_MENU, self.on_change_y_values_and_labels, id=yID)

        # 1D
        for yID in [
            ID_xlabel_1D_bins,
            ID_xlabel_1D_ms,
            ID_xlabel_1D_ms_arrival,
            ID_xlabel_1D_ccs,
            ID_xlabel_1D_restore,
        ]:
            self.Bind(wx.EVT_MENU, self.on_change_x_values_and_labels, id=yID)

        # RT
        for yID in [
            ID_xlabel_RT_scans,
            ID_xlabel_RT_time_min,
            ID_xlabel_RT_retTime_min,
            ID_xlabel_RT_restore,
            ID_xlabel_RT_colVolt,
            ID_xlabel_RT_actVolt,
            ID_xlabel_RT_labFrame,
            ID_xlabel_RT_actLabFrame,
        ]:
            self.Bind(wx.EVT_MENU, self.on_change_x_values_and_labels, id=yID)

        # DT/MS
        for yID in [ID_ylabel_DTMS_bins, ID_ylabel_DTMS_ms, ID_ylabel_DTMS_ms_arrival, ID_ylabel_DTMS_restore]:
            self.Bind(wx.EVT_MENU, self.on_change_y_values_and_labels, id=yID)

    def _get_item_info(self):
        """Retrieve information about object"""
        document = ENV.on_get_document()
        if self._item_id is None:
            return document.title, None
        try:
            _, obj_title = self.GetPyData(self._item_id)
        except TypeError:
            return None, None
        return document.title, obj_title

    @staticmethod
    def _get_item_document():
        """Retrieves the document that is associated with particular data object"""
        return ENV.on_get_document()

    def _get_item_object(self):
        """Retrieves container object for particular dataset"""
        document = ENV.on_get_document()
        _, obj_title = self.GetPyData(self._item_id)
        return document[obj_title, True]

    def _get_item_objects(self):
        """Same as `_get_item_object` but the function yields consecutive elements of the group"""
        raise NotImplementedError("Must implement method")

    def _get_item_label(self, x=False, y=False):
        """Get x/y labels from the object"""
        try:
            obj = self._get_item_object()
        except (KeyError, IndexError):
            return None, None
        x_label, y_label = "", ""
        if x:
            x_label = obj.x_label
        if y:
            y_label = obj.y_label

        return x_label, y_label

    def reset_document_tree_bullets(self):
        """Erase all bullets and make defaults."""
        self.bullets.RemoveAll()
        self.bullets.Add(self.icons.bulletsLib["bulletsDoc"])
        self.bullets.Add(self.icons.bulletsLib["bulletsMS"])
        self.bullets.Add(self.icons.bulletsLib["bulletsDT"])
        self.bullets.Add(self.icons.bulletsLib["bulletsRT"])
        self.bullets.Add(self.icons.bulletsLib["bulletsDot"])
        self.bullets.Add(self.icons.bulletsLib["bulletsAnnot"])
        self.bullets.Add(self.icons.bulletsLib["bullets2DT"])
        self.bullets.Add(self.icons.bulletsLib["bulletsCalibration"])
        self.bullets.Add(self.icons.bulletsLib["bulletsOverlay"])
        self.bullets.Add(self.icons.bulletsLib["bulletsDocOn"])
        self.bullets.Add(self.icons.bulletsLib["bulletsMSIon"])
        self.bullets.Add(self.icons.bulletsLib["bulletsDTIon"])
        self.bullets.Add(self.icons.bulletsLib["bulletsRTIon"])
        self.bullets.Add(self.icons.bulletsLib["bulletsDotOn"])
        self.bullets.Add(self.icons.bulletsLib["bulletsAnnotIon"])
        self.bullets.Add(self.icons.bulletsLib["bullets2DTIon"])
        self.bullets.Add(self.icons.bulletsLib["bulletsCalibrationIon"])
        self.bullets.Add(self.icons.bulletsLib["bulletsOverlayIon"])

        return {
            "document": 0,
            "mass_spec": 1,
            "drift_time": 2,
            "rt": 3,
            "dots": 4,
            "annot": 5,
            "heatmap": 6,
            "calibration": 7,
            "overlay": 8,
            "document_on": 9,
            "mass_spec_on": 10,
            "drift_time_on": 11,
            "rt_on": 12,
            "dots_on": 13,
            "annot_on": 14,
            "heatmap_on": 15,
            "calibration_on": 16,
            "overlay_on": 17,
        }

    @property
    def data_handling(self):
        """Return handle to `data_processing`"""
        return self.presenter.data_handling

    @property
    def data_processing(self):
        """Return handle to `data_processing`"""
        return self.presenter.data_processing

    @property
    def data_visualisation(self):
        """Return handle to `data_visualisation`"""
        return self.presenter.data_visualisation

    @property
    def panel_plot(self):
        """Return handle to `data_processing`"""
        return self.view.panelPlots

    def on_item_selecting(self, evt):
        """Update `item_id` while item is being selected in the document  tree"""

        # Get selected item
        if self._item_id is not None and self._item_id.IsOk():
            self.SetItemBold(self._item_id, False)

        self._item_id = evt.GetItem()

        if self._item_id is not None and self._item_id.IsOk() and CONFIG.tree_panel_item_highlight:
            self.SetItemBold(self._item_id)

        # Get indent level for selected item
        self._indent = self.get_item_indent(self._item_id)
        if self._indent >= 1:
            title, _ = self.GetPyData(self._item_id)
            if self._indent == 1:
                root = self.GetItemText(self.GetItemParent(self._item_id))
            else:
                root = self.GetItemText(self.GetItemParent(self.GetItemParent(self._item_id)))
            item = self.get_parent_item(self._item_id, 2)

            self._item.update(
                title=title,
                root=root,
                branch=self.GetItemText(self.GetItemParent(self._item_id)),
                leaf=self.GetItemText(self._item_id),
                indent=self._indent,
            )

            # Check item
            if not item:
                return

            # update item
            self._item.current = self.GetItemText(item)
            self._item.check_data()
            LOGGER.debug(self._item)

            if CONFIG.tree_panel_item_auto_plot:
                if self._item.is_match(
                    ["spectrum", "chromatogram", "mobilogram", "heatmap", "msdt", "tandem", "overlay"]
                ):
                    self.on_show_plot(None)
        else:
            self._item.update()

    def on_enable_document(
        self, get_selected_item=False, loading_data=False, highlight_selected=False, expand_all=False, evt=None
    ):
        """Highlights and returns currently selected document

        Parameters
        ----------
        get_selected_item : bool, optional
            if `True`, the current item will be return alongside its text and the document title
        loading_data : bool, optional
            if `True`, the document will be expanded
        highlight_selected : bool, optional
            if `True`, the current item will be highlighted
        expand_all : bool, optional
            if `True`, all the elements in the branch will be expanded
        evt :
            ignore
        """

        root = self.GetRootItem()
        selected_item = self.GetSelection()
        item, cookie = self.GetFirstChild(root)

        evt_id = None
        if hasattr(evt, "GetId"):
            evt_id = evt.GetId()  # noqa

        while item.IsOk():
            self.SetItemBold(item, False)
            if loading_data:
                self.CollapseAllChildren(item)
            item, cookie = self.GetNextChild(root, cookie)

        # Select parent document
        if selected_item:
            # get parent of the item
            item = self.get_parent_item(selected_item, 1)

            # highlight current item
            if highlight_selected and CONFIG.tree_panel_item_highlight:
                self.SetItemBold(selected_item)

            # item, try setting it bold
            if item and CONFIG.tree_panel_item_highlight:
                self.SetItemBold(item)

            if loading_data or evt_id == ID_getSelectedDocument:
                self.Expand(item)  # Parent item
                if expand_all:
                    self.ExpandAllChildren(item)

            # update window table
            try:
                document_title = self.GetItemText(item)
            except Exception:
                document_title = "Documents"

            title = f"ORIGAMI (v{self.config.version})"
            if document_title != "Documents":
                ENV.current = document_title
                title += f" :: {document_title} [{self._item.data_type}]"
            self.view.SetTitle(title)

            # update statusbar
            msms_text = ""
            ms_text = ""
            parameters = self._item.parameters
            ms_start, ms_end = parameters.get("start_ms", ""), parameters.get("end_ms", "")
            if ms_start and ms_end:
                ms_text = f"{ms_start}-{ms_end}"
            ms_set = parameters.get("set_msms", "")
            if ms_set:
                msms_text = f"MSMS: {ms_set}"
            try:
                self.view.SetStatusText(ms_text, 1)
                self.view.SetStatusText(msms_text, 2)
            except Exception:  # noqa
                pass

            # In case we also interested in selected item
            if get_selected_item:
                selected_item_text = self.GetItemText(selected_item)
                return document_title, selected_item, selected_item_text
            return document_title

        if evt is not None:
            evt.Skip()

    def get_item_indent(self, item):
        """Get indent of the selected item"""
        # Check item first
        if not item.IsOk():
            return False

        # Get Indent
        indent = 0
        root = self.GetRootItem()
        while item.IsOk():
            if item == root:
                return indent
            else:
                item = self.GetItemParent(item)
                indent += 1
        return indent

    def get_parent_item(self, item, level, get_selected=False):
        """ Get parent item for selected item and level"""
        # Get item
        for _ in range(level, self.get_item_indent(item)):
            item = self.GetItemParent(item)

        if get_selected:
            item_text = self.GetItemText(item)
            return item, item_text

        return item

    def get_item_by_data(self, data, root=None):
        """Get DocumentTree item by its data"""
        if root is None:
            root = self.GetRootItem()
        item, cookie = self.GetFirstChild(root)

        while item.IsOk():
            if self.GetPyData(item) is data:
                return item
            elif self.GetPyData(item) == data:
                return item
            if self.ItemHasChildren(item):
                match = self.get_item_by_data(data, item)
                if match.IsOk():
                    return match
            item, cookie = self.GetNextChild(root, cookie)
        return wx.TreeItemId()

    def get_item_by_label(self, search_text, root):
        """Get DocumentTree item by its label"""
        if root is None:
            root = self.GetRootItem()
        item, cookie = self.GetFirstChild(root)

        while item.IsOk():
            text = self.GetItemText(item)
            if text.lower() == search_text.lower():
                return item
            if self.ItemHasChildren(item):
                match = self.get_item_by_label(search_text, item)
                if match.IsOk():
                    return match
            item, cookie = self.GetNextChild(root, cookie)
        return wx.TreeItemId()

    def on_keyboard_event(self, evt):
        """ Shortcut to navigate through Document Tree """
        key = evt.GetKeyCode()

        # delete item
        if key == wx.WXK_DELETE:
            item = self.GetSelection()
            indent = self.get_item_indent(item)
            if indent == 0:
                self.on_delete_all_documents(None)
            else:
                self.on_delete_item(evt=None)
        elif key == 80:
            if self._item.is_match("heatmap"):
                self.on_process_heatmap(None)
            elif self._item.is_match("spectrum"):
                self.on_process_ms(None)
        elif key == 341:  # F2
            self.on_rename_item(None)

        if evt and key not in [wx.WXK_DELETE, 341]:
            evt.Skip()

    def on_update_gui(self, query, sub_key, dataset_name):
        """Update various elements of the UI based on changes made to the document"""
        # TODO: add trigger to update overlay item window when something is deleted
        # TODO: add trigger to update annotations window when something is deleted
        # TODO: add trigger to update interactive window when something is deleted

        # document_title, dataset_type, __ = query
        # document = self.data_handling.on_get_document(document_title)
        # document_type = document.data_type
        #
        # _sub_key_check = all([el == "" for el in sub_key])
        #
        # if not dataset_name:
        #     dataset_name = None
        #
        # if (
        #     dataset_type in ["Drift time (2D, EIC)"]
        #     or dataset_type in ["Drift time (2D, combined voltages, EIC)"]
        #     and document_type == "Type: MANUAL"
        # ):
        #     self.ionPanel.delete_row_from_table(dataset_name, document_title)
        #     self.on_update_extracted_patches(document_title, None, dataset_name)
        #
        # if dataset_type in ["Drift time (2D)"] and document_type == "Type: 2D IM-MS":
        #     self.textPanel.delete_row_from_table(document_title)
        #
        # if dataset_type in ["Mass Spectra"]:
        #     self.filesPanel.delete_row_from_table(dataset_name, document_title)
        #
        # # update comparison viewer
        # if self._compare_panel:
        #     document_spectrum_list = self.data_handling.generate_item_list_mass_spectra("comparison")
        #     document_list = list(document_spectrum_list.keys())
        #     count = sum([len(document_spectrum_list[_title]) for _title in document_spectrum_list])
        #     if count >= 2:
        #         self._compare_panel._set_item_lists(
        #             document_list=document_list, document_spectrum_list=document_spectrum_list, refresh=True
        #         )
        #     else:
        #         DialogBox(
        #             title="Warning",
        #             msg="The MS comparison window requires at least 2 items to compare."
        #             + f" There are only {count} items in the list. The window will be closed",
        #             kind="Error",
        #             show_exception=True,
        #         )
        #         self._compare_panel.on_close(None)
        #
        # # update peak picker
        # if self._picker_panel and self._picker_panel._check_active([document_title, dataset_type, dataset_name]):
        #     DialogBox(
        #         title="Warning",
        #         msg="The peak picking panel is operating on the same item that was just deleted."
        #         + " The window will be closed",
        #         kind="Error",
        #         show_exception=True,
        #     )
        #     self._picker_panel.on_close(None)
        #
        # # update annotations panel
        # if self._annotate_panel and self._annotate_panel._check_active([document_title, dataset_type, dataset_name]):
        #     if not _sub_key_check:
        #         self._annotate_panel.on_clear_table()
        #     else:
        #         DialogBox(
        #             title="Warning",
        #             msg="The annotation panel is operating on the same item that was just deleted."
        #             + " The window will be closed",
        #             kind="Error",
        #             show_exception=True,
        #         )
        #         self._annotate_panel.on_close(None)
        #
        # # delete annotation links
        # if not _sub_key_check:
        #     sub_key_parent, __ = sub_key
        #
        #     if sub_key_parent == "Annotations":
        #         print("delete annotations")
        #     elif sub_key_parent == "UniDec":
        #         print("delete unidec")

    def on_delete_item(self, evt):
        """Delete selected item from the document tree and the presenter dictionary"""
        # retrieve current item
        item = self._item_id

        document_title, item_name = self._get_item_info()
        document = ENV.on_get_document(document_title)

        root = self.GetItemParent(item)

        if self._item.indent >= 1:
            if self._item.indent == 1 and CONFIG.tree_panel_delete_document_ask:
                dlg = DialogBox(
                    title="Delete item",
                    msg=f"Are you sure you would like to delete the `{item_name}` document?"
                    f"\nThis action is irreversible.",
                    kind="Question",
                )
                if dlg == wx.ID_NO:
                    LOGGER.info("Cancelled object deletion")
                    return
                self.on_remove_document(evt)
                return
            if self._item.indent == 2 and CONFIG.tree_panel_delete_group_ask:
                dlg = DialogBox(
                    title="Delete item",
                    msg=f"Are you sure you would like to delete the `{item_name}` and all of its sub-directories?"
                    f"\nThis action is irreversible.",
                    kind="Question",
                )
                if dlg == wx.ID_NO:
                    LOGGER.info("Cancelled object deletion")
                    return
            elif CONFIG.tree_panel_delete_item_ask:
                dlg = DialogBox(
                    title="Delete item",
                    msg=f"Are you sure you would like to delete `{item_name}` from the document?"
                    f"\nThis action is irreversible.",
                    kind="Question",
                )
                if dlg == wx.ID_NO:
                    LOGGER.info("Cancelled object deletion")
                    return

        del document[item_name]
        if item.IsOk():
            self.Delete(item)

        # check whether root object has anything present
        if not self.ItemHasChildren(root):
            if root.IsOk():
                self.Delete(root)

        # send a message to notify of deletion of an object so other UI elements can be updated
        pub.sendMessage("document.delete.item", info=(document_title, item_name))

    def set_document(self, document_old, document_new):
        """Replace old document data with new

        Parameters
        ----------
        document_old: py object
            old document (before any data changes)
        document_new: py object
            new document (after any data changes)
        """

        # try to get dataset object
        try:
            doc_item = self.get_item_by_data(document_old)
        except Exception:
            doc_item = False

        if doc_item is not False:
            try:
                self.SetItemData(doc_item, document_new)
            except Exception:
                self.data_handling.on_update_document(document_new, "document")
        else:
            self.data_handling.on_update_document(document_new, "document")

    def on_double_click(self, _evt):
        """Handle double-click event"""
        t_start = time.time()
        # Get selected item
        item = self.GetSelection()
        self._item_id = item

        # Get the current text value for selected item
        item_type = self.GetItemText(item)
        if item_type == "Documents":
            self.on_right_click_short()
            return

        # Get indent level for selected item
        self._indent = self.get_item_indent(item)

        if self._item.is_empty:
            return
        self.title = self._item.document_title

        if self._indent == 1:  # and self._item_leaf is None:
            self.on_refresh_document()
        elif self._item.is_match("spectrum", True):
            self.on_open_spectrum_comparison_viewer(None)
        elif self._item.is_match("spectrum"):
            if self._item.is_match("spectrum"):
                self.on_show_plot(evt=ID_showPlotDocument)
            if self._item.is_match("unidec"):
                self.on_open_unidec(None)
        #             elif self._item_branch == "UniDec":
        #                 self.on_open_unidec(None)
        #             elif self._item_leaf == "Annotations":
        #                 self.on_open_annotation_editor(None)
        elif self._item.is_match(["chromatogram", "mobilogram", "heatmap", "msdt", "tandem"]):
            if self._item.is_match("annotation"):
                self.on_open_annotation_editor(None)
            else:
                self.on_show_plot(None)
        elif self._item.is_match("calibration"):
            self.on_show_ccs_calibration(None)
        elif self._item.is_match("overlay"):
            self.on_open_overlay_viewer()

        # elif self._document_type == "Sample information":
        #     self.onShowSampleInfo(evt=None)
        # elif self._indent == 1:
        #     self.onOpenDocInfo(evt=None)

        LOGGER.debug(f"It took: {report_time(t_start)} to process double-click.")

    def on_save_document_as(self, _evt):
        """Save current document. With asking for path. """
        raise NotImplementedError("This method is no longer valid - documents are automatically saved")
        # document_title = self._document_data.title
        # self.data_handling.on_save_document_fcn(document_title)

    def on_save_document(self, evt):
        """Save current document. Without asking for path."""
        raise NotImplementedError("This method is no longer valid - documents are automatically saved")
        # if self._document_data is not None:
        #     document_title = self._document_data.title
        #     wx.CallAfter(self.data_handling.on_save_document_fcn, document_title, save_as=False)

    def on_refresh_document(self, _evt=None):
        """Refresh document by replotting all relevant data"""
        document = ENV.get(self.title)
        if document is None:
            return
        self.data_handling.on_setup_basic_document(document)

    def on_check_xlabels_rt(self):
        """Check label of the chromatogram dataset"""

        xlabel, _ = self._get_item_label(x=True)

        xlabel_evt_dict = {
            "Scans": ID_xlabel_RT_scans,
            "Time (mins)": ID_xlabel_RT_time_min,
            "Retention time (mins)": ID_xlabel_RT_retTime_min,
            "Collision Voltage (V)": ID_xlabel_RT_colVolt,
            "Activation Energy (V)": ID_xlabel_RT_actVolt,
            #             "Activation Voltage (V)": ID_xlabel_RT_actVolt,
            "Lab Frame Energy (eV)": ID_xlabel_RT_labFrame,
            "Activation Energy (eV)": ID_xlabel_RT_actLabFrame,
        }

        return xlabel_evt_dict.get(xlabel, None)

    def on_check_xy_labels_heatmap(self):
        """Check label of the heatmap dataset"""
        xlabel_evt_dict = {
            "Scans": ID_xlabel_2D_scans,
            "Time (mins)": ID_xlabel_2D_time_min,
            "Retention time (mins)": ID_xlabel_2D_retTime_min,
            "Collision Voltage (V)": ID_xlabel_2D_colVolt,
            "Activation Voltage (V)": ID_xlabel_2D_actVolt,
            "Lab Frame Energy (eV)": ID_xlabel_2D_labFrame,
            "Activation Energy (eV)": ID_xlabel_2D_actLabFrame,
            #             "Mass-to-charge (Da)": ID_xlabel_2D_massToCharge,
            #             "m/z (Da)": ID_xlabel_2D_mz,
            #             "Wavenumber (cm⁻¹)": ID_xlabel_2D_wavenumber,
            #             "Charge": ID_xlabel_2D_charge,
            "Collision Cross Section (Å²)": ID_xlabel_2D_ccs,
        }

        ylabel_evt_dict = {
            "Drift time (bins)": ID_ylabel_2D_bins,
            "Drift time (ms)": ID_ylabel_2D_ms,
            "Arrival time (ms)": ID_ylabel_2D_ms_arrival,
            "Collision Cross Section (Å²)": ID_ylabel_2D_ccs,
        }

        xlabel, ylabel = self._get_item_label(x=True, y=True)

        return xlabel_evt_dict.get(xlabel, ID_xlabel_2D_custom), ylabel_evt_dict.get(ylabel, ID_ylabel_2D_custom)

    def on_check_xlabels_dt(self):
        """Check labels of the mobilogram dataset"""
        xlabel, _ = self._get_item_label(x=True)

        xlabel_evt_dict = {
            "Drift time (bins)": ID_xlabel_1D_bins,
            "Drift time (ms)": ID_xlabel_1D_ms,
            "Arrival time (ms)": ID_xlabel_1D_ms_arrival,
            "Collision Cross Section (Å²)": ID_xlabel_1D_ccs,
        }

        return xlabel_evt_dict.get(xlabel, ID_ylabel_2D_bins)

    def on_check_xlabels_dtms(self):
        """Check labels of the DT/MS dataset"""
        _, ylabel = self._get_item_label(y=True)

        ylabel_evt_dict = {
            "Drift time (bins)": ID_ylabel_DTMS_bins,
            "Drift time (ms)": ID_ylabel_DTMS_ms,
            "Arrival time (ms)": ID_ylabel_DTMS_ms_arrival,
        }

        return ylabel_evt_dict.get(ylabel, ID_ylabel_DTMS_bins)

    def on_change_charge_state(self, evt):
        """Change charge state for item in the document tree

        TODO: this will not update the ionPanel when assigning charge to Drift time (1D, EIC, DT-IMS)
        """
        raise NotImplementedError("Must implement method")

        # # Check that the user hasn't selected the header
        # if self._document_type in [
        #     "Drift time (2D, EIC)",
        #     "Drift time (2D, combined voltages, EIC)",
        #     "Drift time (2D, processed, EIC)",
        #     "Input data",
        # ] and self._item_leaf in [
        #     "Drift time (2D, EIC)",
        #     "Drift time (2D, combined voltages, EIC)",
        #     "Drift time (2D, processed, EIC)",
        #     "Input data",
        # ]:
        #     raise MessageError("Incorrect data type", "Please select a single ion in the Document panel.\n\n\n")
        #
        # __, data, __ = self._on_event_get_mobility_chromatogram_data()
        # current_charge = data.get("charge", None)
        #
        # charge = DialogSimpleAsk("Type in new charge state", value=str(current_charge))
        #
        # charge = str2int(charge)
        #
        # if charge in ["", "None", None]:
        #     LOGGER.warning(f"The defined value `{charge}` is not correct")
        #     return
        #
        # query_info = self._on_event_get_mobility_chromatogram_query()
        # document = self.data_handling.set_mobility_chromatographic_keyword_data(query_info, charge=charge)
        #
        # # update data in side panel
        # self.ionPanel.on_find_and_update_values(query_info[2], charge=charge)
        #
        # # update document
        # self.data_handling.on_update_document(document, "no_refresh")

    def _on_event_get_mobility_chromatogram_query(self, **kwargs):
        if not all([item in kwargs for item in ["document_title", "dataset_type", "dataset_name"]]):
            query = self._get_query_info_based_on_indent()
        else:
            document_title = kwargs.pop("document_name")
            dataset_type = kwargs.pop("dataset_type")
            dataset_name = kwargs.pop("dataset_name")
            query = [document_title, dataset_type, dataset_name]

        return query

    def _on_event_get_mobility_chromatogram_data(self, **kwargs):
        query = self._on_event_get_mobility_chromatogram_query(**kwargs)

        document, data = self.data_handling.get_mobility_chromatographic_data(query)

        return document, data, query

    def _get_query_info_based_on_indent(self, return_subkey=False, evt=None):
        """Generate query_info keywords that are implied from the indentation of the selected item

        Parameters
        ----------
        return_subkey : bool, optional
            if True, returns the query_info item and associated subkey elements when indent is 4 and 5

        Returns
        -------
        query_info : list
            list of [document_title, dataset_type, dataset_name]

        """
        if self._item.is_empty is None and evt is not None:
            self.on_item_selecting(evt)

        return self._item.get_query(return_subkey)

    def _get_delete_info_based_on_indent(self):
        """Generate query_info keywords that are implied from the indentation of the selected item and modify it to
        enable eaesier determination which items need to be fully deleted (eg. parent) or partial)

        Returns
        query_info : list
            list of [document_title, dataset_type, dataset_type]
        subkey : list
            list of [subkey_type, subkey_name]
        dataset_name : str
            dataset_name
        """
        query, subkey = self._get_query_info_based_on_indent(return_subkey=True)

        dataset_name = ""
        if self._indent in [3, 4, 5]:
            if query[1] != query[2]:
                dataset_name = query[2]
                query[2] = query[1]

        return query, subkey, dataset_name

    @staticmethod
    def _match_plot_type_to_dataset_type(dataset_type, dataset_name):
        _plot_match = {
            #             "mass_spectrum": ["Mass Spectrum", "Mass Spectrum (processed)",
            #  "Mass Spectra"],
            #             "chromatogram": ["Chromatogram", "Chromatograms (EIC)",
            # "Chromatograms (combined voltages, EIC)"],
            #             "mobilogram": ["Drift time (1D)", "Drift time (1D, EIC)", "Drift time (1D, EIC, DT-IMS)"],
            #             "heatmap": ["Drift time (2D)", "Drift time (2D, EIC)",
            #  "Drift time (2D, combined voltages, EIC)"],
            #             "annotated": ["Multi-line:", "Line:", "H-bar:", "V-bar:", "Scatter:", "Waterfall:"],
        }
        for key, items in _plot_match.items():
            if dataset_type in items:
                return key
            elif any(ok_item in dataset_name for ok_item in items):
                return key
        raise MessageError("Failed to find appropriate method", "Failed to find appropriate method")

    @staticmethod
    def _match_plot_type_to_data_obj(data_obj):
        """Return type of plot depending on the data object"""
        if isinstance(data_obj, MassSpectrumObject):
            return "mass_spectrum"
        elif isinstance(data_obj, ChromatogramObject):
            return "chromatogram"
        elif isinstance(data_obj, MobilogramObject):
            return "mobilogram"
        elif isinstance(data_obj, IonHeatmapObject):
            return "heatmap"
        elif isinstance(data_obj, MassSpectrumHeatmapObject):
            return "ms_heatmap"

    def on_open_annotation_editor(self, _evt, document_title: str = None, dataset_name: str = None, data_obj=None):
        """Open annotations panel"""
        from origami.widgets.annotations.panel_annotation_editor import PanelAnnotationEditor

        if self._annotate_panel is not None:
            raise MessageError(
                "Window already open",
                "An instance of annotation window is already open. Please close it first before"
                + " opening another one.",
            )
        # get data and annotations
        if document_title is None or dataset_name is None or data_obj is None:
            document_title, dataset_name = self._get_item_info()
            data_obj = self._get_item_object()

        plot_type = self._match_plot_type_to_data_obj(data_obj)

        # check plot_type has been specified
        if plot_type is None:
            raise MessageError("Not implemented yet", "Function not implemented for this dataset type")

        self._annotate_panel = PanelAnnotationEditor(
            self.view,
            self.presenter,
            self._icons,
            plot_type=plot_type,
            data_obj=data_obj,
            document_title=document_title,
            dataset_name=dataset_name,
        )
        self._annotate_panel.Show()

    def on_duplicate_annotations(self, _evt):
        """Duplicate annotations from one object to another"""
        from origami.gui_elements.dialog_select_dataset import DialogSelectDataset

        # get data and annotations
        document_title, dataset_name = self._get_item_info()
        data_obj = self._get_item_object()
        annotations_obj = data_obj.get_annotations()
        plot_type = self._match_plot_type_to_data_obj(data_obj)

        if len(annotations_obj) == 0:
            raise MessageError("Error", "Annotation object is empty")

        document_spectrum_dict = QUERY_HANDLER.generate_item_dict(plot_type, "dataset_list")
        document_list = list(document_spectrum_dict.keys())

        duplicate_dlg = DialogSelectDataset(
            self.presenter.view,
            document_list,
            document_spectrum_dict,
            set_document=document_title,
            title="Copy annotations to document/dataset...",
        )
        duplicate_dlg.ShowModal()
        duplicate_document = duplicate_dlg.document
        duplicate_type = duplicate_dlg.dataset

        if any(item is None for item in [duplicate_type, duplicate_document]):
            LOGGER.warning("Duplicating annotations was cancelled")
            return
        if dataset_name == duplicate_type:
            LOGGER.warning("Tried to copy annotations to the parent object - cancelled.")
            return

        # make copy of the annotations
        annotations_obj_copy = deepcopy(annotations_obj)

        document_copy_to = ENV.on_get_document(duplicate_document)
        data_obj_copy_to = document_copy_to[duplicate_type, True]

        annotations_obj = data_obj_copy_to.get_annotations()
        if len(annotations_obj) > 0:
            dlg = DialogBox(
                title="Dataset already contains annotations",
                msg="The selected dataset already contains annotations. Would you like"
                + " to continue and overwrite present annotations?",
                kind="Question",
            )
            if dlg == wx.ID_NO:
                LOGGER.info("Cancelled adding annotations to a dataset")
                return
        data_obj_copy_to.set_annotations(annotations_obj_copy)

    def on_action_origami_ms(self, _, document_title=None):
        """Open a dialog where you can specify ORIGAMI-MS parameters"""
        from origami.widgets.origami_ms.dialog_origami_ms import DialogOrigamiMsSettings

        # get document
        document = ENV.on_get_document(document_title)
        if not document.is_origami_ms():
            raise MessageError(
                "Incorrect document type", f"Cannot setup ORIGAMI-MS parameters for {document.data_type} document."
            )

        dlg = DialogOrigamiMsSettings(self.view, self.presenter, document_title=document_title)
        dlg.ShowModal()

    def on_open_interactive_viewer(self, evt):
        """Open a dialog window where you can export data in an interactive format"""
        raise NotImplementedError("Must implement method")

    #         from origami.gui_elements.panel_plot_viewer import PanelPlotViewer
    #
    #         # get data
    #         document_title, dataset_type, dataset_name = self._get_query_info_based_on_indent()
    #         __, data = self.data_handling.get_mobility_chromatographic_data([document_title, dataset_type,
    # dataset_name])
    #
    #         # initialize peak picker
    #         self._bokeh_panel = PanelPlotViewer(
    #             self.presenter.view,
    #             self.presenter,
    #             self.config,
    #             self.icons,
    #             mz_data=data,
    #             document_title=document_title,
    #             dataset_type=dataset_type,
    #             dataset_name=dataset_name,
    #         )
    #         self._bokeh_panel.Show()

    def on_open_ccs_builder(self, _):
        """Open dialog window where CCS calibration can be created"""
        from origami.widgets.ccs.panel_ccs_calibration import PanelCCSCalibration

        document_title, _ = self._get_item_info()

        self._ccs_panel = PanelCCSCalibration(self.view, document_title=document_title)
        self._ccs_panel.Show()

    def on_show_ccs_calibration(self, _evt):
        """Open CCS calibration dialog"""
        document_title, calibration_name = self._get_item_info()
        self.on_open_ccs_editor(None, document_title, calibration_name)

    def on_open_ccs_editor(self, _, document_title: str = None, calibration_name: str = None, calibration_obj=None):
        """Open dialog window where CCS calibration can be edited"""
        from origami.widgets.ccs.panel_ccs_calibration import PanelCCSCalibration

        if document_title is None:
            document_title, _ = self._get_item_info()

        self._ccs_panel = PanelCCSCalibration(
            self.view,
            document_title=document_title,
            calibration_name=calibration_name,
            calibration_obj=calibration_obj,
            check_for_existing=True,
        )
        self._ccs_panel.Show()

    def on_open_overlay_editor(self, _):
        """Open a dialog window where you can overlay and compare objects"""
        from origami.widgets.overlay.panel_overlay_editor import PanelOverlayEditor

        # get list of items
        item_dict = QUERY_HANDLER.generate_item_dict_all("overlay")
        item_list = QUERY_HANDLER.item_dict_to_list(item_dict)

        self._overlay_editor_panel = PanelOverlayEditor(self.view, self.presenter, self._icons, item_list=item_list)
        self._overlay_editor_panel.Show()

    def on_open_overlay_viewer(self):
        """Open overlay viewer"""
        from origami.widgets.overlay.panel_overlay_viewer import PanelOverlayViewer

        # get data object
        group_obj = self._get_item_object()

        self._overlay_viewer_panel = PanelOverlayViewer(self.view, self.presenter, group_obj=group_obj)
        self._overlay_viewer_panel.Show()

    def on_open_interactive_editor(self, _):
        """Open a dialog window where you can overlay and compare objects"""
        from origami.widgets.interactive.panel_interactive_editor import PanelInteractiveEditor

        # get list of items
        item_dict = QUERY_HANDLER.generate_item_dict_all("interactive")
        item_list = QUERY_HANDLER.item_dict_to_list(item_dict)
        if self._interactive_editor_panel:
            self._interactive_editor_panel.on_set_item_list(item_list)
        else:
            self._interactive_editor_panel = PanelInteractiveEditor(
                self.view, self.presenter, self._icons, item_list=item_list
            )
        self._interactive_editor_panel.Show()

    def on_open_lesa_viewer(self, _):
        """Open a dialog window where you can view LESA data"""
        from origami.widgets.lesa.panel_imaging_lesa import PanelImagingLESAViewer

        # get document title
        item_list = QUERY_HANDLER.generate_item_dict_mass_spectra("dataset_list")
        document_title = ENV.current
        if not ENV.on_get_document(document_title).is_imaging():
            raise MessageError("Error", f"Document `{document_title}` is not an Imaging document.")

        item_list = item_list[document_title]

        self._lesa_panel = PanelImagingLESAViewer(
            self.view, self.presenter, document_title=document_title, spectrum_list=item_list
        )
        self._lesa_panel.Show()

    def on_import_lesa_dataset(self, _):
        """Open a dialog window where you can specify LESA import parameters"""
        from origami.widgets.lesa.panel_imaging_lesa_import import PanelImagingImportDataset

        self._lesa_import_panel = PanelImagingImportDataset(self.view, self.presenter)
        self._lesa_import_panel.Show()

    def on_import_manual_dataset(self, activation_type, _):
        """Open a dialog window where you can specify CIU/SID import parameters"""
        from origami.widgets.manual.panel_manual_import import PanelManualImportDataset

        self._manual_import_panel = PanelManualImportDataset(self.view, self.presenter, activation_type=activation_type)
        self._manual_import_panel.Show()

    def on_update_ui(self, value, _evt):
        """Update UI element(s)"""
        if value == "menu.load.override":
            self.config.import_duplicate_panel_ask = not self.config.import_duplicate_panel_ask

    def _get_menu_mobilogram_label(self):
        # Change x-axis label (1D)
        menu_xlabel = wx.Menu()
        menu_xlabel.Append(ID_xlabel_1D_bins, "Drift time (bins)", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_1D_ms, "Drift time (ms)", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_1D_ms_arrival, "Arrival time (ms)", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_1D_ccs, "Collision Cross Section (Å²)", "", wx.ITEM_RADIO)
        menu_xlabel.AppendSeparator()
        menu_xlabel.Append(ID_xlabel_1D_restore, "Restore default", "")

        # bind events
        if self._item.is_match("mobilogram"):
            try:
                item_id = self.on_check_xlabels_dt()
                menu_xlabel.FindItemById(item_id).Check(True)
            except (UnboundLocalError, TypeError, KeyError):
                LOGGER.warning(f"Failed to setup labels for `{self._item.current}` item`")

        return menu_xlabel

    def _get_menu_chromatogram_label(self):
        # Change x-axis label (RT)
        menu_xlabel = wx.Menu()
        menu_xlabel.Append(ID_xlabel_RT_scans, "Scans", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_RT_time_min, "Time (mins)", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_RT_retTime_min, "Retention time (mins)", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_RT_colVolt, "Collision Voltage (V)", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_RT_actVolt, "Activation Energy (V)", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_RT_labFrame, "Lab Frame Energy (eV)", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_RT_actLabFrame, "Activation Energy (eV)", "", wx.ITEM_RADIO)
        menu_xlabel.AppendSeparator()
        menu_xlabel.Append(ID_xlabel_RT_restore, "Restore default", "")

        # bind events
        if self._item.is_match("chromatogram"):
            try:
                item_id = self.on_check_xlabels_rt()
                menu_xlabel.FindItemById(item_id).Check(True)
            except (UnboundLocalError, TypeError, KeyError):
                LOGGER.warning(f"Failed to setup labels for `{self._item.current}` item`")

        return menu_xlabel

    def _get_menu_heatmap_label(self):
        # Change x-axis label (2D)
        menu_xlabel = wx.Menu()
        menu_xlabel.Append(ID_xlabel_2D_scans, "Scans", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_2D_time_min, "Time (mins)", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_2D_retTime_min, "Retention time (mins)", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_2D_colVolt, "Collision Voltage (V)", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_2D_actVolt, "Activation Energy (V)", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_2D_labFrame, "Lab Frame Energy (eV)", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_2D_actLabFrame, "Activation Energy (eV)", "", wx.ITEM_RADIO)
        #         menu_xlabel.Append(ID_xlabel_2D_massToCharge, "Mass-to-charge (Da)", "", wx.ITEM_RADIO)
        #         menu_xlabel.Append(ID_xlabel_2D_mz, "m/z (Da)", "", wx.ITEM_RADIO)
        #         menu_xlabel.Append(ID_xlabel_2D_wavenumber, "Wavenumber (cm⁻¹)", "", wx.ITEM_RADIO)
        #         menu_xlabel.Append(ID_xlabel_2D_charge, "Charge", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_2D_ccs, "Collision Cross Section (Å²)", "", wx.ITEM_RADIO)
        menu_xlabel.Append(ID_xlabel_2D_custom, "Custom label...", "", wx.ITEM_RADIO)
        menu_xlabel.AppendSeparator()
        menu_xlabel.Append(ID_xlabel_2D_restore, "Restore default", "")

        # Change y-axis label (2D)
        menu_ylabel = wx.Menu()
        menu_ylabel.Append(ID_ylabel_2D_bins, "Drift time (bins)", "", wx.ITEM_RADIO)
        menu_ylabel.Append(ID_ylabel_2D_ms, "Drift time (ms)", "", wx.ITEM_RADIO)
        menu_ylabel.Append(ID_ylabel_2D_ms_arrival, "Arrival time (ms)", "", wx.ITEM_RADIO)
        menu_ylabel.Append(ID_ylabel_2D_ccs, "Collision Cross Section (Å²)", "", wx.ITEM_RADIO)
        menu_ylabel.Append(ID_ylabel_2D_custom, "Custom label...", "", wx.ITEM_RADIO)
        menu_ylabel.AppendSeparator()
        menu_ylabel.Append(ID_ylabel_2D_restore, "Restore default", "")

        #         # Check xy axis labels
        if self._item.is_match("heatmap"):
            # Check what is the current label for this particular dataset
            try:
                item_id_x, item_id_y = self.on_check_xy_labels_heatmap()
                menu_xlabel.FindItemById(item_id_x).Check(True)
                menu_ylabel.FindItemById(item_id_y).Check(True)
            except (UnboundLocalError, TypeError, KeyError):
                LOGGER.warning(f"Failed to setup x/y labels for `{self._item.current}` item`")

        return menu_xlabel, menu_ylabel

    def _get_menu_msdt_label(self):
        # change y-axis label (DT/MS)
        menu_ylabel = wx.Menu()
        menu_ylabel.Append(ID_ylabel_DTMS_bins, "Drift time (bins)", "", wx.ITEM_RADIO)
        menu_ylabel.Append(ID_ylabel_DTMS_ms, "Drift time (ms)", "", wx.ITEM_RADIO)
        menu_ylabel.Append(ID_ylabel_DTMS_ms_arrival, "Arrival time (ms)", "", wx.ITEM_RADIO)
        menu_ylabel.AppendSeparator()
        menu_ylabel.Append(ID_ylabel_DTMS_restore, "Restore default", "")

        # bind events
        if self._item.is_match("msdt"):
            try:
                item_id = self.on_check_xlabels_dtms()
                menu_ylabel.FindItemById(item_id).Check(True)
            except (UnboundLocalError, TypeError, KeyError):
                LOGGER.warning(f"Failed to setup labels for `{self._item.current}` item`")

        return menu_ylabel

    def _set_menu_load_data(self, menu):
        # load custom data sub menu
        load_data_menu = wx.Menu()
        menu_action_load_ms = load_data_menu.Append(wx.ID_ANY, "Import mass spectrum")
        menu_action_load_rt = load_data_menu.Append(wx.ID_ANY, "Import chromatogram")
        menu_action_load_dt = load_data_menu.Append(wx.ID_ANY, "Import mobilogram")
        menu_action_load_heatmap = load_data_menu.Append(wx.ID_ANY, "Import heatmap")
        menu_action_load_matrix = load_data_menu.Append(wx.ID_ANY, "Import matrix")
        load_data_menu.AppendSeparator()
        menu_action_load_other = load_data_menu.Append(wx.ID_ANY, "Import data with metadata...")
        load_data_menu.AppendSeparator()
        menu_action_load_check_existing = load_data_menu.AppendCheckItem(wx.ID_ANY, "Don't check if file exists")
        menu_action_load_check_existing.Check(self.config.import_duplicate_panel_ask)

        # bind events
        self.Bind(wx.EVT_MENU, partial(self.data_handling.on_load_custom_data, "mass_spectra"), menu_action_load_ms)
        self.Bind(wx.EVT_MENU, partial(self.data_handling.on_load_custom_data, "chromatograms"), menu_action_load_rt)
        self.Bind(wx.EVT_MENU, partial(self.data_handling.on_load_custom_data, "mobilograms"), menu_action_load_dt)
        self.Bind(wx.EVT_MENU, partial(self.data_handling.on_load_custom_data, "heatmaps"), menu_action_load_heatmap)
        self.Bind(wx.EVT_MENU, partial(self.data_handling.on_load_custom_data, "matrix"), menu_action_load_matrix)
        self.Bind(wx.EVT_MENU, partial(self.data_handling.on_load_custom_data, "annotated"), menu_action_load_other)
        self.Bind(wx.EVT_MENU, partial(self.on_update_ui, "menu.load.override"), menu_action_load_check_existing)

        menu.Append(wx.ID_ANY, "Import data...", load_data_menu)

    def _set_menu_annotations(self, menu):
        # annotations sub menu

        if self._item.is_dataset:
            _menu = wx.Menu()
        elif self._item.is_annotation:
            _menu = menu
        else:
            return

        annotation_menu_show_annotations_panel = make_menu_item(
            parent=_menu, text="Show annotations panel...", bitmap=self._icons.label
        )
        #         annotation_menu_show_annotations = make_menu_item(
        #             parent=_menu, text="Show annotations on plot", bitmap=self._icons.highlight
        #         )
        annotation_menu_duplicate_annotations = make_menu_item(
            parent=_menu, text="Duplicate annotations...", bitmap=self._icons.duplicate
        )

        _menu.Append(annotation_menu_show_annotations_panel)
        #         _menu.Append(annotation_menu_show_annotations)
        _menu.Append(annotation_menu_duplicate_annotations)

        if self._item.is_dataset:
            menu.AppendSubMenu(_menu, "Annotations...")

        # bind events
        self.Bind(wx.EVT_MENU, self.on_open_annotation_editor, annotation_menu_show_annotations_panel)
        #         self.Bind(wx.EVT_MENU, self.on_show_annotations, annotation_menu_show_annotations)
        self.Bind(wx.EVT_MENU, self.on_duplicate_annotations, annotation_menu_duplicate_annotations)

    def _set_menu_actions(self, menu):
        action_menu = wx.Menu()

        document = self._get_item_document()
        has_ccs_calibration, is_origami_ms = False, False
        can_extract, file_fmt = True, None
        if document:
            has_ccs_calibration = document.has_ccs_calibration()
            is_origami_ms = document.is_origami_ms()
            can_extract, _, file_fmt = document.can_extract()

        if is_origami_ms:
            menu_action_origami_ms = action_menu.Append(
                make_menu_item(parent=action_menu, text="Setup ORIGAMI-MS parameters...")
            )
            self.Bind(wx.EVT_MENU, self.on_action_origami_ms, menu_action_origami_ms)

        if can_extract:
            menu_action_extract_data = action_menu.Append(
                make_menu_item(parent=action_menu, text="Open data extraction panel...")
            )
            self.Bind(wx.EVT_MENU, self.on_open_extract_data, menu_action_extract_data)

            menu_action_extract_dtms = action_menu.Append(
                make_menu_item(parent=action_menu, text="Open DT/MS extraction panel...")
            )
            self.Bind(wx.EVT_MENU, self.on_open_extract_dtms, menu_action_extract_dtms)

        if has_ccs_calibration:
            menu_action_edit_ccs = action_menu.Append(
                make_menu_item(parent=action_menu, text="Edit CCS calibration...")
            )
            self.Bind(wx.EVT_MENU, self.on_open_ccs_editor, menu_action_edit_ccs)

        if file_fmt == "waters":
            menu_action_ccs = action_menu.Append(make_menu_item(parent=action_menu, text="Create CCS calibration..."))
            self.Bind(wx.EVT_MENU, self.on_open_ccs_builder, menu_action_ccs)

        menu.Append(wx.ID_ANY, "Action...", action_menu)

    @staticmethod
    def _get_menu_save():
        # save dataframe
        save_data_submenu = wx.Menu()
        save_data_submenu.Append(ID_saveData_csv, "Save to .csv file")
        save_data_submenu.Append(ID_saveData_pickle, "Save to .pickle file")
        save_data_submenu.Append(ID_saveData_hdf, "Save to .hdf file (slow)")
        save_data_submenu.Append(ID_saveData_excel, "Save to .excel file (v. slow)")

        return save_data_submenu

    def _set_menu_mass_spectrum(self, menu):

        if self._item.indent <= 1:
            return

        # make menu items
        # view actions
        menu_action_show_plot_spectrum = make_menu_item(
            parent=menu, text="Show mass spectrum\tAlt+S", bitmap=self._icons.ms
        )
        self.Bind(wx.EVT_MENU, self.on_show_plot_mass_spectra, menu_action_show_plot_spectrum)

        #         menu_action_show_plot_spectrum_waterfall = make_menu_item(
        #             parent=menu, text="Show mass spectra as waterfall", bitmap=self._icons.ms
        #         )
        #         menu_action_show_plot_spectrum_heatmap = make_menu_item(
        #             parent=menu, text="Show mass spectra as heatmap", bitmap=self._icons.ms
        #         )

        # process actions
        menu_show_peak_picker_panel = make_menu_item(
            parent=menu, text="Open peak picker...", bitmap=self._icons.highlight
        )
        self.Bind(wx.EVT_MENU, self.on_open_peak_picker, menu_show_peak_picker_panel)

        menu_action_process_ms = make_menu_item(parent=menu, text="Process...\tP", bitmap=self._icons.process_ms)
        self.Bind(wx.EVT_MENU, self.on_process_ms, menu_action_process_ms)

        menu_action_process_ms_all = make_menu_item(parent=menu, text="Process all...", bitmap=self._icons.process_ms)
        self.Bind(wx.EVT_MENU, self.on_batch_process_ms, menu_action_process_ms_all)

        menu_show_comparison_panel = make_menu_item(
            parent=menu, text="Compare mass spectra...", bitmap=self._icons.compare_ms
        )
        self.Bind(wx.EVT_MENU, self.on_open_spectrum_comparison_viewer, menu_show_comparison_panel)

        menu_show_unidec_panel = make_menu_item(
            parent=menu, text="Deconvolute using UniDec...", bitmap=self._icons.unidec
        )
        self.Bind(wx.EVT_MENU, self.on_open_unidec, menu_show_unidec_panel)

        # export actions
        menu_action_save_image_as = make_menu_item(parent=menu, text="Save image as...", bitmap=self._icons.png)
        self.Bind(wx.EVT_MENU, partial(self.on_show_plot_mass_spectra, True), menu_action_save_image_as)

        menu_action_save_image_as_all = make_menu_item(
            parent=menu, text="Batch save images as...", bitmap=self._icons.png
        )

        menu_action_save_data_as = make_menu_item(parent=menu, text="Save data as...", bitmap=self._icons.csv)
        self.Bind(wx.EVT_MENU, self.on_save_csv, menu_action_save_data_as)

        menu_action_save_data_as_all = make_menu_item(parent=menu, text="Batch save data as...", bitmap=self._icons.csv)
        self.Bind(wx.EVT_MENU, self.on_batch_export_figures, menu_action_save_image_as_all)

        menu_action_delete_item = make_menu_item(parent=menu, text="Delete item\tDelete", bitmap=self._icons.delete)
        self.Bind(wx.EVT_MENU, self.on_delete_item, menu_action_delete_item)

        menu_action_open_data_directory = make_menu_item(parent=menu, text="Reveal data directory in File Explorer")
        self.Bind(wx.EVT_MENU, self.on_open_data_directory, menu_action_open_data_directory)

        # append menu
        if self._item.indent == 2:
            #             menu.Append(menu_action_show_plot_spectrum_waterfall)
            #             menu.Append(menu_action_show_plot_spectrum_heatmap)
            #             menu.AppendSeparator()
            menu.Append(menu_show_comparison_panel)
            menu.Append(menu_action_process_ms_all)
            menu.AppendSeparator()
            menu.Append(menu_action_save_image_as_all)
            menu.Append(menu_action_save_data_as_all)
            menu.Append(menu_action_delete_item)
        else:
            menu.Append(menu_action_show_plot_spectrum)
            menu.AppendSeparator()
            menu.Append(menu_show_peak_picker_panel)
            menu.Append(menu_show_comparison_panel)
            self._set_menu_annotations(menu)
            menu.Append(menu_action_process_ms)
            menu.Append(menu_action_process_ms_all)
            menu.Append(menu_show_unidec_panel)
            menu.AppendSeparator()
            menu.Append(menu_action_save_image_as)
            menu.Append(menu_action_save_data_as)
            menu.Append(menu_action_delete_item)
            menu.Append(menu_action_open_data_directory)

    def _set_menu_chromatogram(self, menu):

        if self._item.indent <= 1:
            return

        # view actions
        menu_action_show_plot_chromatogram = make_menu_item(
            parent=menu, text="Show chromatogram\tAlt+S", bitmap=self._icons.chromatogram
        )
        self.Bind(wx.EVT_MENU, self.on_show_plot_chromatogram, menu_action_show_plot_chromatogram)

        # export actions
        menu_action_save_chromatogram_image_as = make_menu_item(
            parent=menu, text="Save image as...", bitmap=self._icons.png
        )
        self.Bind(wx.EVT_MENU, partial(self.on_show_plot_chromatogram, True), menu_action_save_chromatogram_image_as)

        menu_action_save_data_as = make_menu_item(parent=menu, text="Save data as...", bitmap=self._icons.csv)
        self.Bind(wx.EVT_MENU, self.on_save_csv, menu_action_save_data_as)

        menu_action_save_image_as_all = make_menu_item(
            parent=menu, text="Batch save images as...", bitmap=self._icons.png
        )
        self.Bind(wx.EVT_MENU, self.on_batch_export_figures, menu_action_save_image_as_all)

        menu_action_save_data_as_all = make_menu_item(parent=menu, text="Batch save data as...", bitmap=self._icons.csv)
        self.Bind(wx.EVT_MENU, self.on_batch_export_data, menu_action_save_data_as_all)

        menu_action_delete_item = make_menu_item(parent=menu, text="Delete item\tDelete", bitmap=self._icons.delete)
        self.Bind(wx.EVT_MENU, self.on_delete_item, menu_action_delete_item)

        menu_action_process_as_origami = make_menu_item(
            parent=menu, text="Apply ORIGAMI-MS parameters", bitmap=self._icons.sum
        )
        self.Bind(wx.EVT_MENU, self.on_apply_origami_ms, menu_action_process_as_origami)

        menu_action_process_as_origami_all = make_menu_item(
            parent=menu, text="Apply ORIGAMI-MS parameters", bitmap=self._icons.sum
        )
        self.Bind(wx.EVT_MENU, self.on_batch_apply_origami_ms, menu_action_process_as_origami_all)

        menu_action_assign_charge = make_menu_item(
            parent=menu, text="Assign charge state...\tAlt+Z", bitmap=self._icons.charge
        )
        self.Bind(wx.EVT_MENU, self.on_assign_charge_state, menu_action_assign_charge)

        menu_action_open_data_directory = make_menu_item(parent=menu, text="Reveal data directory in File Explorer")
        self.Bind(wx.EVT_MENU, self.on_open_data_directory, menu_action_open_data_directory)

        if self._item.indent == 2:
            menu.Append(menu_action_process_as_origami_all)
            menu.Append(menu_action_save_image_as_all)
            menu.Append(menu_action_save_data_as_all)
            menu.Append(menu_action_delete_item)
        else:
            menu_xlabel = self._get_menu_chromatogram_label()

            menu.Append(menu_action_show_plot_chromatogram)
            self._set_menu_annotations(menu)
            menu.AppendSeparator()
            menu.Append(menu_action_assign_charge)
            menu.Append(menu_action_process_as_origami)
            menu.Append(wx.ID_ANY, "Change x-axis to...", menu_xlabel)
            menu.AppendSeparator()
            menu.Append(menu_action_save_chromatogram_image_as)
            menu.Append(menu_action_save_data_as)
            menu.Append(menu_action_delete_item)
            menu.Append(menu_action_open_data_directory)

    def _set_menu_mobilogram(self, menu):

        if self._item.indent <= 1:
            return

        # view actions
        menu_action_show_plot_mobilogram = make_menu_item(
            parent=menu, text="Show mobilogram\tAlt+S", bitmap=self._icons.mobilogram
        )
        self.Bind(wx.EVT_MENU, self.on_show_plot_mobilogram, menu_action_show_plot_mobilogram)

        menu_action_assign_charge = make_menu_item(
            parent=menu, text="Assign charge state...\tAlt+Z", bitmap=self._icons.charge
        )
        self.Bind(wx.EVT_MENU, self.on_assign_charge_state, menu_action_assign_charge)

        menu_action_assign_mz = make_menu_item(parent=menu, text="Assign m/z value...")
        self.Bind(wx.EVT_MENU, self.on_assign_mz, menu_action_assign_mz)

        # process actions
        menu_action_delete_item = make_menu_item(parent=menu, text="Delete item\tDelete", bitmap=self._icons.delete)
        self.Bind(wx.EVT_MENU, self.on_delete_item, menu_action_delete_item)

        menu_action_process_ccs = make_menu_item(parent=menu, text="Apply CCS calibration", bitmap=self._icons.sum)
        self.Bind(wx.EVT_MENU, self.on_apply_ccs_calibration, menu_action_process_ccs)

        menu_action_process_ccs_batch = make_menu_item(
            parent=menu, text="Batch apply CCS calibration", bitmap=self._icons.sum
        )
        self.Bind(wx.EVT_MENU, self.on_batch_apply_ccs_calibration, menu_action_process_ccs_batch)

        menu_action_save_mobilogram_image_as = make_menu_item(
            parent=menu, text="Save image as...", bitmap=self._icons.png
        )
        self.Bind(wx.EVT_MENU, partial(self.on_show_plot_mobilogram, True), menu_action_save_mobilogram_image_as)

        menu_action_save_data_as = make_menu_item(parent=menu, text="Save data as...", bitmap=self._icons.csv)
        self.Bind(wx.EVT_MENU, self.on_save_csv, menu_action_save_data_as)

        menu_action_save_image_as_all = make_menu_item(
            parent=menu, text="Batch save images as...", bitmap=self._icons.png
        )
        self.Bind(wx.EVT_MENU, self.on_batch_export_figures, menu_action_save_image_as_all)

        menu_action_save_data_as_all = make_menu_item(parent=menu, text="Batch save data as...", bitmap=self._icons.csv)
        self.Bind(wx.EVT_MENU, self.on_batch_export_data, menu_action_save_data_as_all)

        menu_action_open_data_directory = make_menu_item(parent=menu, text="Reveal data directory in File Explorer")
        self.Bind(wx.EVT_MENU, self.on_open_data_directory, menu_action_open_data_directory)

        # make menu
        if self._item.indent == 2:
            menu.Append(menu_action_process_ccs_batch)
            menu.AppendSeparator()
            menu.Append(menu_action_save_image_as_all)
            menu.Append(menu_action_save_data_as_all)
            menu.Append(menu_action_delete_item)
        else:
            menu_xlabel = self._get_menu_mobilogram_label()

            menu.Append(menu_action_show_plot_mobilogram)
            self._set_menu_annotations(menu)
            menu.AppendSeparator()
            menu.Append(menu_action_assign_charge)
            menu.Append(menu_action_assign_mz)
            menu.Append(menu_action_process_ccs)
            menu.Append(wx.ID_ANY, "Change x-axis to...", menu_xlabel)
            menu.AppendSeparator()
            menu.Append(menu_action_save_mobilogram_image_as)
            menu.Append(menu_action_save_data_as)
            menu.Append(menu_action_delete_item)
            menu.Append(menu_action_open_data_directory)

    def _set_menu_heatmap(self, menu):

        if self._item.indent <= 1:
            return

        # view actions
        menu_action_show_plot_2d = make_menu_item(parent=menu, text="Show heatmap\tAlt+S", bitmap=self._icons.heatmap)
        self.Bind(wx.EVT_MENU, self.on_show_plot_heatmap, menu_action_show_plot_2d)

        menu_action_show_plot_contour = make_menu_item(parent=menu, text="Show contour", bitmap=self._icons.contour)
        self.Bind(wx.EVT_MENU, self.on_show_plot_heatmap_contour, menu_action_show_plot_contour)

        menu_action_show_plot_as_mobilogram = make_menu_item(
            parent=menu, text="Show mobilogram", bitmap=self._icons.mobilogram
        )
        self.Bind(wx.EVT_MENU, self.on_show_plot_heatmap_mobilogram, menu_action_show_plot_as_mobilogram)

        menu_action_show_plot_as_chromatogram = make_menu_item(
            parent=menu, text="Show chromatogram", bitmap=self._icons.chromatogram
        )
        self.Bind(wx.EVT_MENU, self.on_show_plot_heatmap_chromatogram, menu_action_show_plot_as_chromatogram)

        menu_action_show_plot_violin = make_menu_item(parent=menu, text="Show violin plot", bitmap=self._icons.violin)
        self.Bind(wx.EVT_MENU, self.on_show_plot_heatmap_violin, menu_action_show_plot_violin)

        menu_action_show_plot_waterfall = make_menu_item(
            parent=menu, text="Show waterfall plot", bitmap=self._icons.waterfall
        )
        self.Bind(wx.EVT_MENU, self.on_show_plot_heatmap_waterfall, menu_action_show_plot_waterfall)

        menu_action_show_plot_joint = make_menu_item(parent=menu, text="Show joint plot", bitmap=self._icons.joint)
        self.Bind(wx.EVT_MENU, self.on_show_plot_heatmap_joint, menu_action_show_plot_joint)

        menu_action_show_plot_3d = make_menu_item(parent=menu, text="Show heatmap (3D)", bitmap=self._icons.cube)
        self.Bind(wx.EVT_MENU, self.on_show_plot_heatmap_3d, menu_action_show_plot_3d)

        menu_action_show_highlights = make_menu_item(
            parent=menu, text="Highlight ion in mass spectrum\tAlt+X", bitmap=self._icons.zoom
        )
        self.Bind(wx.EVT_MENU, self.on_show_zoom_on_ion, menu_action_show_highlights)

        menu_action_process_as_origami = make_menu_item(
            parent=menu, text="Apply ORIGAMI-MS parameters", bitmap=self._icons.sum
        )
        self.Bind(wx.EVT_MENU, self.on_apply_origami_ms, menu_action_process_as_origami)

        menu_action_process_as_origami_all = make_menu_item(
            parent=menu, text="Batch apply ORIGAMI-MS parameters", bitmap=self._icons.sum
        )
        self.Bind(wx.EVT_MENU, self.on_batch_apply_origami_ms, menu_action_process_as_origami_all)

        menu_action_process_ccs_batch = make_menu_item(
            parent=menu, text="Batch apply CCS calibration", bitmap=self._icons.sum
        )
        self.Bind(wx.EVT_MENU, self.on_batch_apply_ccs_calibration, menu_action_process_ccs_batch)

        menu_action_process_2d = make_menu_item(parent=menu, text="Process...\tP", bitmap=self._icons.process_heatmap)
        self.Bind(wx.EVT_MENU, self.on_process_heatmap, menu_action_process_2d)

        menu_action_process_2d_all = make_menu_item(
            parent=menu, text="Process all...", bitmap=self._icons.process_heatmap
        )
        self.Bind(wx.EVT_MENU, self.on_batch_process_heatmap, menu_action_process_2d_all)

        menu_action_assign_charge = make_menu_item(
            parent=menu, text="Assign charge state...\tAlt+Z", bitmap=self._icons.charge
        )
        self.Bind(wx.EVT_MENU, self.on_assign_charge_state, menu_action_assign_charge)

        menu_action_assign_mz = make_menu_item(parent=menu, text="Assign m/z value...")
        self.Bind(wx.EVT_MENU, self.on_assign_mz, menu_action_assign_mz)

        menu_action_process_ccs = make_menu_item(parent=menu, text="Apply CCS calibration", bitmap=self._icons.sum)
        self.Bind(wx.EVT_MENU, self.on_apply_ccs_calibration, menu_action_process_ccs)

        menu_action_delete_item = make_menu_item(parent=menu, text="Delete item\tDelete", bitmap=self._icons.delete)
        self.Bind(wx.EVT_MENU, self.on_delete_item, menu_action_delete_item)
        # export actions
        menu_action_save_heatmap_image_as = make_menu_item(parent=menu, text="Save image as...", bitmap=self._icons.png)
        self.Bind(wx.EVT_MENU, partial(self.on_show_plot_heatmap, True), menu_action_save_heatmap_image_as)

        menu_action_save_2d_data_as = make_menu_item(parent=menu, text="Save data as...", bitmap=self._icons.csv)
        self.Bind(wx.EVT_MENU, self.on_save_csv, menu_action_save_2d_data_as)

        menu_action_save_image_as_all = make_menu_item(
            parent=menu, text="Batch save images as...", bitmap=self._icons.png
        )
        self.Bind(wx.EVT_MENU, self.on_batch_export_figures, menu_action_save_image_as_all)

        menu_action_save_data_as_all = make_menu_item(parent=menu, text="Batch save data as...", bitmap=self._icons.csv)
        self.Bind(wx.EVT_MENU, self.on_batch_export_data, menu_action_save_data_as_all)

        menu_action_open_data_directory = make_menu_item(parent=menu, text="Reveal data directory in File Explorer")
        self.Bind(wx.EVT_MENU, self.on_open_data_directory, menu_action_open_data_directory)

        # make menu
        if self._item.indent == 2:
            menu.Append(menu_action_process_ccs_batch)
            menu.Append(menu_action_process_as_origami_all)
            menu.Append(menu_action_process_2d_all)
            menu.AppendSeparator()
            menu.Append(menu_action_save_image_as_all)
            menu.Append(menu_action_save_data_as_all)
            menu.Append(menu_action_delete_item)
        else:
            menu_xlabel, menu_ylabel = self._get_menu_heatmap_label()

            menu.Append(menu_action_show_plot_2d)
            menu.Append(menu_action_show_plot_contour)
            menu.Append(menu_action_show_plot_joint)
            menu.Append(menu_action_show_plot_3d)
            menu.Append(menu_action_show_plot_waterfall)
            menu.Append(menu_action_show_plot_violin)
            menu.Append(menu_action_show_plot_as_mobilogram)
            menu.Append(menu_action_show_plot_as_chromatogram)
            menu.Append(menu_action_show_highlights)
            menu.AppendSeparator()
            menu.Append(menu_action_process_2d)
            menu.AppendSeparator()
            self._set_menu_annotations(menu)
            menu.Append(menu_action_assign_charge)
            menu.Append(menu_action_assign_mz)
            menu.Append(menu_action_process_as_origami)
            menu.Append(menu_action_process_ccs)
            menu.Append(wx.ID_ANY, "Set X-axis label as...", menu_xlabel)
            menu.Append(wx.ID_ANY, "Set Y-axis label as...", menu_ylabel)
            menu.AppendSeparator()
            menu.Append(menu_action_save_heatmap_image_as)
            menu.Append(menu_action_save_2d_data_as)
            menu.Append(menu_action_delete_item)
            menu.Append(menu_action_open_data_directory)

    def _set_menu_msdt(self, menu):

        if self._item.indent <= 1:
            return

        # view actions
        menu_action_show_plot_2d = make_menu_item(parent=menu, text="Show heatmap\tAlt+S", bitmap=self._icons.heatmap)
        self.Bind(wx.EVT_MENU, self.on_show_plot_dtms, menu_action_show_plot_2d)

        menu_action_show_plot_joint = make_menu_item(parent=menu, text="Show joint plot", bitmap=self._icons.joint)
        self.Bind(wx.EVT_MENU, self.on_show_plot_dtms_joint, menu_action_show_plot_joint)

        # process actions
        menu_action_extract = make_menu_item(parent=menu, text="Open DT/MS extraction panel...")
        self.Bind(wx.EVT_MENU, self.on_open_extract_dtms, menu_action_extract)

        menu_action_process_2d = make_menu_item(parent=menu, text="Process...\tP", bitmap=self._icons.process_heatmap)
        self.Bind(wx.EVT_MENU, self.on_process_heatmap, menu_action_process_2d)

        menu_action_process_2d_all = make_menu_item(
            parent=menu, text="Process all...", bitmap=self._icons.process_heatmap
        )
        self.Bind(wx.EVT_MENU, self.on_batch_process_heatmap, menu_action_process_2d_all)

        menu_action_delete_item = make_menu_item(parent=menu, text="Delete item\tDelete", bitmap=self._icons.delete)
        self.Bind(wx.EVT_MENU, self.on_delete_item, menu_action_delete_item)

        # export actions
        menu_action_save_image_as = make_menu_item(parent=menu, text="Save image as...", bitmap=self._icons.png)
        self.Bind(wx.EVT_MENU, partial(self.on_show_plot_dtms, True), menu_action_save_image_as)

        menu_action_save_data_as = make_menu_item(parent=menu, text="Save data as...", bitmap=self._icons.csv)
        self.Bind(wx.EVT_MENU, self.on_save_csv, menu_action_save_data_as)

        menu_action_save_image_as_all = make_menu_item(
            parent=menu, text="Batch save images as...", bitmap=self._icons.png
        )
        self.Bind(wx.EVT_MENU, self.on_batch_export_figures, menu_action_save_image_as_all)

        menu_action_save_data_as_all = make_menu_item(parent=menu, text="Batch save data as...", bitmap=self._icons.csv)
        self.Bind(wx.EVT_MENU, self.on_batch_export_data, menu_action_save_data_as_all)

        menu_action_open_data_directory = make_menu_item(parent=menu, text="Reveal data directory in File Explorer")
        self.Bind(wx.EVT_MENU, self.on_open_data_directory, menu_action_open_data_directory)

        # make menu
        if self._item.indent == 2:
            menu.Append(menu_action_extract)
            menu.Append(menu_action_process_2d_all)
            menu.AppendSeparator()
            menu.Append(menu_action_save_image_as_all)
            menu.Append(menu_action_save_data_as_all)
            menu.Append(menu_action_delete_item)
        else:
            menu_ylabel = self._get_menu_msdt_label()

            menu.Append(menu_action_show_plot_2d)
            menu.Append(menu_action_show_plot_joint)
            menu.AppendSeparator()
            menu.Append(menu_action_extract)
            menu.Append(menu_action_process_2d)
            menu.AppendSeparator()
            menu.Append(wx.ID_ANY, "Set Y-axis label as...", menu_ylabel)
            menu.AppendSeparator()
            menu.Append(menu_action_save_image_as)
            menu.Append(menu_action_save_data_as)
            menu.Append(menu_action_delete_item)
            menu.Append(menu_action_open_data_directory)

    def _set_menu_calibration(self, menu):
        """Set CCS calibration menu"""
        if self._item.indent <= 1:
            return

        # view actions
        menu_action_show_plot = make_menu_item(parent=menu, text="Show calibration", bitmap=self._icons.heatmap)
        self.Bind(wx.EVT_MENU, self.on_show_ccs_calibration, menu_action_show_plot)

        menu_action_delete_item = make_menu_item(parent=menu, text="Delete item\tDelete", bitmap=self._icons.delete)
        self.Bind(wx.EVT_MENU, self.on_delete_item, menu_action_delete_item)

        # export actions
        menu_action_save_data_as = make_menu_item(parent=menu, text="Save data as...", bitmap=self._icons.csv)
        self.Bind(wx.EVT_MENU, self.on_save_csv, menu_action_save_data_as)

        menu_action_save_data_as_all = make_menu_item(parent=menu, text="Batch save data as...", bitmap=self._icons.csv)
        self.Bind(wx.EVT_MENU, self.on_batch_export_data, menu_action_save_data_as_all)

        menu_action_open_data_directory = make_menu_item(parent=menu, text="Reveal data directory in File Explorer")
        self.Bind(wx.EVT_MENU, self.on_open_data_directory, menu_action_open_data_directory)

        # make menu
        if self._item.indent == 2:
            menu.Append(menu_action_save_data_as_all)
            menu.Append(menu_action_delete_item)
        else:
            menu.Append(menu_action_show_plot)
            menu.AppendSeparator()
            menu.Append(menu_action_save_data_as)
            menu.Append(menu_action_delete_item)
            menu.Append(menu_action_open_data_directory)

    @staticmethod
    def _get_menu_overlay(menu):
        # # statistical method
        # elif self._document_type == "Statistical":
        #     # Only if clicked on an item and not header
        #     if self._item_leaf != self._document_type:
        #         menu.Append(menu_action_show_plot_2D)
        #         menu.AppendSeparator()
        #         menu.Append(menu_action_save_image_as)
        #         menu.Append(menu_action_save_data_as)
        #         menu.Append(menu_action_delete_item)
        #         menu.AppendSeparator()
        #         menu.Append(menu_action_rename_item)
        #     # Only if on a header
        #     else:
        #         menu.Append(menu_action_save_data_as)
        #         menu.Append(menu_action_delete_item)
        #
        # # overlay
        # elif self._document_type == "Overlay":
        #     plot_type = self.splitText[0]
        #     if self._document_type != self._item_leaf:
        #         if plot_type in [
        #             "Waterfall (Raw)",
        #             "Waterfall (Processed)",
        #             "Waterfall (Fitted)",
        #             "Waterfall (Deconvoluted MW)",
        #             "Waterfall (Charge states)",
        #         ]:
        #             menu.Append(menu_action_show_plot)
        #             if plot_type in ["Waterfall (Raw)", "Waterfall (Processed)"]:
        #                 menu.Append(menu_show_annotations_panel)
        #         else:
        #             menu.Append(menu_action_show_plot)
        #         menu.AppendSeparator()
        #         if self.splitText[0] in [
        #             "Waterfall (Raw)",
        #             "Waterfall (Processed)",
        #             "Waterfall (Fitted)",
        #             "Waterfall (Deconvoluted MW)",
        #             "Waterfall (Charge states)",
        #         ]:
        #             menu.Append(ID_saveWaterfallImageDoc, "Save image as...")
        #         else:
        #             menu.Append(menu_action_save_image_as)
        #         menu.Append(menu_action_delete_item)
        #         menu.AppendSeparator()
        #         menu.Append(menu_action_rename_item)
        #     else:
        #         menu.Append(menu_action_delete_item)
        return None

    def _set_menu_annotated(self, menu):
        pass
        # # annotated data
        # elif dataset_type == "Annotated data":
        #     if dataset_type == dataset_name:
        #         menu.AppendMenu(wx.ID_ANY, "Import data...", load_data_menu)
        #     else:
        #         menu.Append(menu_action_show_plot)
        #         if dataset_type != dataset_name and any(
        #             [ok_item in dataset_name for ok_item in accepted_annotated_items]
        #         ):
        #             menu.AppendSubMenu(annotation_menu, "Annotations...")
        #         menu.AppendSeparator()
        #         menu.Append(menu_action_save_image_as)
        #         menu.Append(menu_action_delete_item)

    def _set_menu_tandem(self, menu):
        pass
        # # tandem MS
        # elif itemType == "Tandem Mass Spectra" and self._indent == 2:
        #     menu.Append(
        #         make_menu_item(
        #             parent=menu,
        #             evt_id=ID_docTree_add_mzIdentML,
        #             text="Add identification information (.mzIdentML, .mzid, .mzid.gz)",
        #             bitmap=None,
        #         )
        #     )

    def on_right_click_short(self):
        """Right-click menu when clicked on the `Documents` item in the documents tree"""

        menu = wx.Menu()
        menu_delete_all = make_menu_item(parent=menu, text="Close all documents", bitmap=self._icons.bin)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_delete_all_documents, menu_delete_all)

        # make menu
        # menu.Append(menu_save_all)
        menu.Append(menu_delete_all)
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_right_click(self, evt):
        """ Create and show up popup menu"""

        # Get the current text value for selected item
        item_type = self.GetItemText(evt.GetItem())

        # try:
        #     query, subkey = self._get_query_info_based_on_indent(return_subkey=True, evt=evt)
        # except AttributeError:
        #     LOGGER.debug(
        #         "Could not obtain right-click query key. Please first left-click on an item in the document tree",
        #         exc_info=True,
        #     )
        #     return

        if wx.GetKeyState(wx.WXK_CONTROL):
            self.parent.on_right_click(evt)
            return
        elif item_type == "Documents":
            self.on_right_click_short()
            return

        # Bind events
        self._bind_change_label_events()

        # # self.Bind(wx.EVT_MENU, self.onShowSampleInfo, id=ID_showSampleInfo)
        # self.Bind(wx.EVT_MENU, self.view.on_open_interactive_output_panel, id=ID_saveAsInteractive)
        # # self.Bind(wx.EVT_MENU, self.on_process_UVPD, id=ID_docTree_plugin_UVPD)
        # # self.Bind(wx.EVT_MENU, self.on_open_unidec, id=ID_docTree_show_unidec)
        # self.Bind(wx.EVT_MENU, self.data_handling.on_add_mzident_file_fcn, id=ID_docTree_add_mzIdentML)
        # self.Bind(wx.EVT_MENU, self.on_action_origami_ms, id=ID_docTree_action_open_origami_ms)
        # # self.Bind(wx.EVT_MENU, self.on_open_extract_dtms, id=ID_docTree_action_open_extractDTMS)
        # # self.Bind(wx.EVT_MENU, self.on_open_extract_data, id=ID_docTree_action_open_extract)

        menu = wx.Menu()
        if self._item.is_match("spectrum"):
            self._set_menu_mass_spectrum(menu)
        elif self._item.is_match("chromatogram"):
            self._set_menu_chromatogram(menu)
        elif self._item.is_match("mobilogram"):
            self._set_menu_mobilogram(menu)
        elif self._item.is_match("heatmap"):
            self._set_menu_heatmap(menu)
        elif self._item.is_match("msdt"):
            self._set_menu_msdt(menu)
        elif self._item.is_match("calibration"):
            self._set_menu_calibration(menu)

        # elements that are always present
        if menu.GetMenuItemCount() > 0:
            menu.AppendSeparator()
        self._set_menu_actions(menu)
        self._set_menu_load_data(menu)

        menu_action_rename_item = make_menu_item(parent=menu, text="Rename\tF2", bitmap=self._icons.edit)
        menu_action_duplicate_item = make_menu_item(parent=menu, text="Duplicate item", bitmap=self._icons.duplicate)
        # menu_action_show_unidec_results = make_menu_item(
        #     parent=menu, evt_id=ID_docTree_show_unidec, text="Show UniDec results", bitmap=None
        # )

        menu_action_open_directory = make_menu_item(
            parent=menu, text="Reveal Document directory in File Explorer", bitmap=self._icons.explorer
        )
        menu_action_duplicate_document = make_menu_item(
            parent=menu, text="Duplicate document", bitmap=self._icons.duplicate
        )
        menu_action_remove_document = make_menu_item(parent=menu, text="Close document", bitmap=self._icons.close)
        menu_action_remove_document_disk = make_menu_item(
            parent=menu, text="Delete document from disk", bitmap=self._icons.bin
        )
        menu_action_about_dataset = make_menu_item(parent=menu, text="About dataset...", bitmap=self._icons.info)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_duplicate_document, menu_action_duplicate_document)
        self.Bind(wx.EVT_MENU, self.on_remove_document, menu_action_remove_document)
        self.Bind(wx.EVT_MENU, self.on_remove_document_from_disk, menu_action_remove_document_disk)
        self.Bind(wx.EVT_MENU, self.on_open_directory, menu_action_open_directory)
        self.Bind(wx.EVT_MENU, self.on_rename_item, menu_action_rename_item)
        self.Bind(wx.EVT_MENU, self.on_duplicate_item, menu_action_duplicate_item)
        self.Bind(wx.EVT_MENU, self.on_about_dataset, menu_action_about_dataset)

        if self._item.is_dataset:
            menu.AppendSeparator()
            menu.Append(menu_action_rename_item)
            menu.Append(menu_action_duplicate_item)

        # add generic iitems
        if menu.GetMenuItemCount() > 0:
            menu.AppendSeparator()

        menu.Append(menu_action_about_dataset)
        menu.Append(menu_action_open_directory)
        menu.Append(menu_action_duplicate_document)
        menu.Append(menu_action_remove_document)
        menu.Append(menu_action_remove_document_disk)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

        # self.Bind(wx.EVT_MENU, self.on_delete_item, menu_action_delete_item)
        # self.Bind(wx.EVT_MENU, self.on_change_charge_state, menu_action_assign_charge)
        # self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, menu_action_save_image_as)

        # # Sample information
        # elif itemType == "Sample information":
        #     menu.Append(ID_showSampleInfo, "Show sample information")

        #
        #

        #
        # if self._indent == 1:
        #     menu.Append(ID_docTree_show_refresh_document, "Refresh document")
        #     menu.Append(
        #         make_menu_item(
        #             parent=menu,
        #             evt_id=ID_docTree_duplicate_document,
        #             text="Duplicate document\tShift+D",
        #             bitmap=self._icons.duplicate,
        #         )
        #     )
        #     menu.Append(menu_action_rename_item)
        #     menu.AppendSeparator()
        # menu.AppendMenu(wx.ID_ANY, "Action...", action_menu)
        # menu.AppendSeparator()
        # menu.Append(
        #     make_menu_item(
        #         parent=menu,
        #         evt_id=ID_openDocInfo,
        #         text="Notes, Information, Labels...\tCtrl+I",
        #         bitmap=self._icons.info,
        #     )
        # )
        # menu.Append(
        #     make_menu_item(
        #         parent=menu,
        #         evt_id=ID_goToDirectory,
        #         text="Go to folder...\tCtrl+G",
        #         bitmap=self._icons.folder,
        #     )
        # )
        # menu.Append(
        #     make_menu_item(
        #         parent=menu,
        #         evt_id=ID_saveAsInteractive,
        #         text="Open interactive output panel...\tShift+Z",
        #         bitmap=self._icons.bokeh,
        #     )
        # )
        # menu.Append(menu_action_save_document)
        # menu.Append(menu_action_save_document_as)

    def on_change_x_values_and_labels(self, evt):
        """Change xy-axis labels"""
        obj = self._get_item_object()
        to_label = evt.EventObject.GetLabelText(evt.GetId())
        try:
            obj.change_x_label(to_label)
            self.on_show_plot(None)
        except ValueError as err:
            raise MessageError("Error", err)

    def on_change_y_values_and_labels(self, evt):
        """Change xy-axis labels"""
        obj = self._get_item_object()
        to_label = evt.EventObject.GetLabelText(evt.GetId())
        try:
            obj.change_y_label(to_label)
            self.on_show_plot(None)
        except ValueError as err:
            raise MessageError("Error", err)

    def on_open_spectrum_comparison_viewer(self, _evt):
        """Open panel where user can select mas spectra to compare """
        from origami.widgets.comparison.panel_signal_comparison_viewer import PanelSignalComparisonViewer

        if self._item_id is None:
            return

        document_spectrum_dict = QUERY_HANDLER.generate_item_dict_mass_spectra("dataset_list")
        document_list = list(document_spectrum_dict.keys())
        count = sum([len(document_spectrum_dict[_title]) for _title in document_spectrum_dict])

        if count < 2:
            LOGGER.error(f"There must be at least 2 items in the list co compare. Current count: {count}")
            return

        try:
            document_title, _ = self._get_item_info()
        except AttributeError:
            document_title = document_list[0]

        self._compare_panel = PanelSignalComparisonViewer(
            self.view,
            self.presenter,
            self._icons,
            document_title=document_title,
            document_list=document_list,
            document_spectrum_dict=document_spectrum_dict,
        )
        self._compare_panel.Show()

    def on_assign_charge_state(self, _evt):
        """Assign charge state in an object"""
        data_obj = self._get_item_object()
        if not data_obj:
            return

        charge = data_obj.get_metadata("charge", 1)

        charge = DialogNumberAsk(
            "Please specify charge state of the data object", "Specify charge state", charge, -100, 100, self.view
        )
        if charge in ["", None]:
            return
        data_obj.add_metadata("charge", charge, True)
        LOGGER.debug(f"Assigned charge `{charge}` to the data object")

    def on_assign_mz(self, _evt):
        """Assign charge state in an object"""
        data_obj = self._get_item_object()
        if not data_obj:
            return

        mz = data_obj.get_metadata("mz", 0)

        mz = DialogSimpleAsk(
            "Please specify m/z value of the data object", "Specify m/z", str(mz), "floatPos", self.view
        )
        if mz in ["", None]:
            return
        data_obj.add_metadata("mz", mz)
        LOGGER.debug(f"Assigned m/z value `{mz}` to the data object")

    def on_get_ccs_calibration(self, document: DocumentStore):
        """Get CCS calibration from the document"""

        if not document.has_ccs_calibration():
            return

        calibration_name = None
        calibration_list = document.get_ccs_calibration_list()
        if calibration_list:
            if len(calibration_list) > 1:
                # allow the user to make selection
                dlg = wx.SingleChoiceDialog(
                    self,
                    "Calibrations",
                    "There are existing calibrations in the Document."
                    "\nPlease select calibration you would like to restore in the panel",
                    calibration_list,
                )
                if dlg.ShowModal() == wx.ID_CANCEL:
                    LOGGER.debug("Restoration of calibration was cancelled.")
                    return

                calibration_name = dlg.GetStringSelection()
                dlg.Destroy()
            else:
                calibration_name = calibration_list[0]
        if calibration_name:
            return document.get_ccs_calibration(calibration_name)

    def on_apply_ccs_calibration(self, _evt):
        """Apply ORIGAMI-MS settings on the object and create a copy"""
        document_title = ENV.current
        document = ENV.on_get_document(document_title)
        if not document.has_ccs_calibration():
            raise MessageError(
                "Missing CCS calibration",
                "Cannot apply CCS calibration on this document - missing CCS calibration. You can create CCS"
                "\ncalibration using Widgets -> Open CCS Calibration Builder...",
            )

        # get data object
        data_obj = self._get_item_object()
        calibration = self.on_get_ccs_calibration(document)

        # check parameters
        mz, charge = data_obj.get_metadata(["mz", "charge"])
        if mz is None or charge is None:
            raise MessageError(
                "Error", "Cannot apply CCS calibration to the object - missing `m/z` or `charge` information"
            )

        # apply calibration
        data_obj = data_obj.apply_ccs_calibration(calibration, mz, charge)
        if data_obj is not None:
            self.on_update_document(data_obj.DOCUMENT_KEY, data_obj.title, document_title)
        self.panel_plot.on_plot_data_object(data_obj)

    def on_batch_apply_ccs_calibration(self, _evt):
        """Apply CCS calibration to each object"""
        from origami.widgets.ccs.dialog_batch_apply_ccs import DialogBatchApplyCCSCalibration

        document_title = ENV.current
        document = ENV.on_get_document(document_title)
        if not document.has_ccs_calibration():
            raise MessageError(
                "Missing CCS calibration",
                "Cannot apply CCS calibration on this document - missing CCS calibration. You can create CCS"
                "\ncalibration using Widgets -> Open CCS Calibration Builder...",
            )

        # get calibration object
        calibration = self.on_get_ccs_calibration(document)

        # get list of items
        item_list = self.on_get_item_list()
        item_list = item_list[ENV.current]

        # modify list of items to include m/z and charge information
        _item_list = []
        for item in item_list:
            data_obj = document[item[1], True, True]
            mz, charge = data_obj.get_metadata(["mz", "charge"])
            _item_list.append([*item, mz, charge, get_short_hash()])

        dlg = DialogBatchApplyCCSCalibration(
            self.view, _item_list, document_tree=self, document_title=document_title, calibration_obj=calibration
        )
        dlg.ShowModal()

    def on_apply_origami_ms(self, _evt):
        """Apply ORIGAMI-MS settings on the object and create a copy"""
        document_title = ENV.current
        document = ENV.on_get_document(document_title)
        if not document.is_origami_ms(True):
            raise MessageError(
                "Incorrect document type", f"Cannot setup ORIGAMI-MS parameters for {document.data_type} document."
            )

        # get data object
        data_obj = self._get_item_object()

        # apply ORIGAMI-MS settings
        data_obj = data_obj.apply_origami_ms()
        if data_obj is not None:
            self.on_update_document(data_obj.DOCUMENT_KEY, data_obj.title, document_title)
        self.panel_plot.on_plot_data_object(data_obj)

    def on_batch_apply_origami_ms(self, _evt):
        """Apply ORIGAMI-MS settings on the object and create a copy"""
        from origami.widgets.origami_ms.dialog_batch_apply_origami_ms import DialogReviewApplyOrigamiMs

        document_title = ENV.current
        document = ENV.on_get_document(document_title)
        if not document.is_origami_ms(True):
            raise MessageError(
                "Incorrect document type", f"Cannot setup ORIGAMI-MS parameters for {document.data_type} document."
            )

        item_list = self.on_get_item_list()
        dlg = DialogReviewApplyOrigamiMs(
            self.view, item_list[ENV.current], document_tree=self, document_title=document_title
        )
        dlg.ShowModal()

    def on_open_process_heatmap_settings(self, **kwargs):
        """Open heatmap processing settings"""
        from origami.gui_elements.panel_process_heatmap import PanelProcessHeatmap

        panel = PanelProcessHeatmap(self.presenter.view, self.presenter, **kwargs)
        panel.Show()

    def on_process_heatmap(self, _evt):
        """Process clicked heatmap item"""
        document_title, dataset_name = self._get_item_info()
        heatmap_obj = self._get_item_object()
        document = ENV.on_get_document(document_title)

        self.on_open_process_heatmap_settings(
            document=document, document_title=document_title, dataset_name=dataset_name, heatmap_obj=heatmap_obj
        )

    def on_batch_process_heatmap(self, _evt):
        """Process all clicked heatmap items"""
        from origami.gui_elements.dialog_review_editor import DialogReviewProcessHeatmap

        item_list = self.on_get_item_list()
        document_title = ENV.current
        dlg = DialogReviewProcessHeatmap(
            self.view, item_list[ENV.current], document_tree=self, document_title=document_title
        )
        dlg.ShowModal()

    def on_open_process_msdt_settings(self, **kwargs):
        """Open mass spectrum processing settings"""
        from origami.gui_elements.panel_process_msdt import PanelProcessMSDT

        panel = PanelProcessMSDT(self.presenter.view, self.presenter, **kwargs)
        panel.Show()

    def on_open_process_ms_settings(self, **kwargs):
        """Open mass spectrum processing settings"""
        from origami.gui_elements.panel_process_spectrum import PanelProcessMassSpectrum

        panel = PanelProcessMassSpectrum(self.presenter.view, self.presenter, **kwargs)
        panel.Show()

    def on_process_ms(self, _evt):
        """Process clicked mass spectrum item"""
        document_title, dataset_name = self._get_item_info()
        mz_obj = self._get_item_object()
        document = ENV.on_get_document(document_title)

        self.on_open_process_ms_settings(
            document=document, document_title=document_title, dataset_name=dataset_name, mz_obj=mz_obj
        )

    def on_batch_process_ms(self, _evt):
        """Process all clicked mass spectra items"""
        from origami.gui_elements.dialog_review_editor import DialogReviewProcessSpectrum

        item_list = self.on_get_item_list()
        document_title = ENV.current

        dlg = DialogReviewProcessSpectrum(
            self.view, item_list[document_title], document_tree=self, document_title=document_title
        )
        dlg.ShowModal()

    def on_batch_export_figures(self, _evt):
        """Export images in batch"""
        from origami.gui_elements.dialog_review_editor import DialogReviewExportFigures
        from origami.gui_elements.dialog_batch_figure_exporter import DialogExportFigures

        # get information from the user which files should be exported as figures
        item_list = self.on_get_item_list()
        dlg = DialogReviewExportFigures(self.view, item_list[ENV.current], document_tree=self)
        dlg.ShowModal()

        # get list of items that were selected
        output_list = dlg.output_list
        dlg.Destroy()

        if not output_list:
            LOGGER.warning("Output list was empty - cancelled export action.")
            return

        # get information from the user about the image export parameters
        document = ENV.on_get_document()
        dlg = DialogExportFigures(self.view, default_path=document.output_path)
        dlg.ShowModal()

        path = CONFIG.image_folder_path
        if path is None or not os.path.exists(path):
            LOGGER.error("Export path does not exist")
            return

        # iterate over each object in the list and process it while also adding it to the document
        for obj_name in output_list:
            t_start = time.time()
            obj = document[obj_name, True]
            output_path = os.path.join(path, obj_name.split("/")[-1]) + f".{CONFIG.imageFormat}"

            view = self.panel_plot.on_plot_data_object(obj)
            view.save_figure(path=output_path)
            LOGGER.info(f"Saved figure in {report_time(t_start)} (path={output_path})")

    def on_batch_export_data(self, _evt):
        """Export data in batch"""
        from origami.gui_elements.dialog_review_editor import DialogReviewExportFigures
        from origami.gui_elements.dialog_batch_data_exporter import DialogExportData

        # get information from the user which files should be exported as figures
        item_list = self.on_get_item_list()
        dlg = DialogReviewExportFigures(self.view, item_list[ENV.current], document_tree=self)
        dlg.ShowModal()

        # get list of items that were selected
        output_list = dlg.output_list
        dlg.Destroy()

        if not output_list:
            LOGGER.warning("Output list was empty - cancelled export action.")
            return

        # get information from the user about the image export parameters
        document = ENV.on_get_document()
        dlg = DialogExportData(self.view, default_path=document.output_path)
        dlg.ShowModal()

        path = CONFIG.data_folder_path
        if path is None or not os.path.exists(path):
            LOGGER.error("Export path does not exist")
            return

        # iterate over each object in the list and export it to a text file
        for obj_name in output_list:
            t_start = time.time()
            obj = document[obj_name, True]
            output_path = os.path.join(path, obj_name.split("/")[-1]) + CONFIG.saveExtension
            obj.to_csv(
                path=output_path,
                delimiter=CONFIG.saveDelimiter,
                # remove_zeros
            )
            LOGGER.info(f"Saved data in {report_time(t_start)} (path={output_path})")

    def on_get_item_list(self):
        """Return list of items that can be inserted in a review panel"""
        item_dict = {}
        if self._item.is_match("heatmap", True):
            item_dict = QUERY_HANDLER.generate_item_dict_heatmap("document_dataset_list")
        elif self._item.is_match("spectrum", True):
            item_dict = QUERY_HANDLER.generate_item_dict_mass_spectra("document_dataset_list")
        elif self._item.is_match("mobilogram", True):
            item_dict = QUERY_HANDLER.generate_item_dict_mobilogram("document_dataset_list")
        elif self._item.is_match("chromatogram", True):
            item_dict = QUERY_HANDLER.generate_item_dict_chromatogram("document_dataset_list")
        elif self._item.is_match("msdt", True):
            item_dict = QUERY_HANDLER.generate_item_dict_msdt("document_dataset_list")
        return item_dict

    def on_rename_item(self, _evt):
        """Rename item"""
        from origami.gui_elements.dialog_rename import DialogRenameObject

        if not self._item.is_dataset:
            pub.sendMessage("notify.message.error", message="Cannot rename currently selected item!")
            return

        # get item metadata
        document_title, dataset_name = self._get_item_info()
        data_obj = self._get_item_object()

        # get item name
        group_name, item_name = dataset_name.split("/")

        dlg = DialogRenameObject(self.view, item_name)
        dlg.ShowModal()

        # get new name
        new_name = dlg.new_name
        if new_name is None:
            pub.sendMessage("notify.message.warning", message="Action was cancelled or the name was not valid")
            return
        elif new_name == item_name:
            pub.sendMessage("notify.message.warning", message="New name was the same as the old name")
            return
        new_name = f"{group_name}/{new_name}"

        # copy object
        data_obj_renamed = data_obj.rename(new_name)
        # new_name, data_obj_renamed = data_obj.copy(new_name)

        # get handle of the old object item
        item = self.get_item_by_data((document_title, dataset_name))
        if item.IsOk():
            self.Delete(item)

        # add new object to the document tree
        self.on_update_document(data_obj_renamed.DOCUMENT_KEY, new_name, document_title)
        pub.sendMessage("document.rename.item", info=(document_title, dataset_name, new_name))
        pub.sendMessage("notify.message.success", message=f"Renamed item\nNew name={new_name}")

    def on_duplicate_item(self, _evt):
        """Duplicate item"""
        if not self._item.is_dataset:
            pub.sendMessage("notify.message.error", message="Cannot duplicate currently selected item!")
            return

        # get document and a new, valid name
        document_title, dataset_name = self._get_item_info()
        document = ENV.on_get_document(document_title)
        dataset_name = document.get_new_name(dataset_name, "copy")

        # get data object and create a copy
        data_obj = self._get_item_object()
        dataset_name, data_obj_copy = data_obj.copy(dataset_name)
        self.on_update_document(data_obj_copy.DOCUMENT_KEY, dataset_name, document_title)
        pub.sendMessage(
            "notify.message.success", message=f"Duplicated item\nDocument={document_title}\nDataset={dataset_name}"
        )

    def on_open_directory(self, _evt):
        """Go to selected directory"""
        self.data_handling.on_open_directory(None)

    def on_open_data_directory(self, _evt):
        """Open data directory of the currently selected object"""
        data_obj = self._get_item_object()
        if data_obj:
            self.data_handling.on_open_directory(data_obj.path)

    def on_show_zoom_on_ion(self, _evt):
        """Zoom-in on an ion in a mass spectrum window"""
        if self._item.is_match("heatmap", True):
            return

        # get data for selected item
        _, title = self._get_item_info()

        self.on_show_plot_zoom_on_mass_spectrum(title)

    def on_show_plot_zoom_on_mass_spectrum(self, ion_name):
        """Zoom-in on an ion"""
        from origami.utils.labels import get_mz_from_label

        try:
            mz_min, mz_max = get_mz_from_label(ion_name)
        except ValueError:
            LOGGER.warning("Could not parse request")
            return

        self.panel_plot.view_ms.set_xlim(mz_min, mz_max)
        self.panel_plot.set_page("MS")

    def on_show_plot_mass_spectra(self, _evt, save_image=False):
        """Show mass spectrum in the main viewer"""
        if self._item.is_match("spectrum", True):
            return

        # get plot data
        ms_obj = self._get_item_object()
        view = self.panel_plot.on_plot_ms(obj=ms_obj, set_page=True)

        if save_image:
            filename = self._item.get_name("ms")
            view.save_figure(filename=filename)

    def on_show_plot_dtms(self, _evt, save_image=False):
        """Show MS/DT plot as heatmap"""
        if self._item.is_match("msdt", True):
            return

        # get data for selected item
        obj = self._get_item_object()
        view = self.panel_plot.on_plot_dtms(obj=obj, set_page=True)
        if save_image:
            filename = self._item.get_name("dtms")
            view.save_figure(filename=filename)

    def on_show_plot_dtms_joint(self, _evt, save_image=False):
        """Show MS/DT plot as a joint plot"""
        if self._item.is_match("msdt", True):
            return

        # get data for selected item
        obj = self._get_item_object()
        self.panel_plot.view_msdt.plot_joint(obj=obj)
        self.panel_plot.set_page("DT/MS")

        if save_image:
            filename = self._item.get_name("joint")
            self.panel_plot.view_msdt.save_figure(filename=filename)

    def on_show_plot_mobilogram(self, _evt, save_image=False):
        """Show mobilogram"""
        if self._item.is_match("mobilogram", True):
            return

        dt_obj = self._get_item_object()
        view = self.panel_plot.on_plot_1d(obj=dt_obj, set_page=True)

        if save_image:
            filename = self._item.get_name("dt")
            view.save_figure(filename=filename)

    def on_show_plot_chromatogram(self, _evt, save_image=False):
        """Show chromatogram"""
        if self._item.is_match("chromatogram", True):
            return

        # get plot data
        rt_obj = self._get_item_object()
        view = self.panel_plot.on_plot_rt(obj=rt_obj, set_page=True)

        if save_image:
            filename = self._item.get_name("rt")
            view.save_figure(filename=filename)

    def on_show_plot_heatmap(self, _evt, save_image=False):
        """Show heatmap"""
        if self._item.is_match("heatmap", True):
            return

        # get data for selected item
        obj = self._get_item_object()
        view = self.panel_plot.on_plot_2d(obj=obj, set_page=True)

        if save_image:
            filename = self._item.get_name("heatmap")
            view.save_figure(filename=filename)

    def on_show_plot_heatmap_contour(self, _evt, save_image=False):
        """Show heatmap as a contour plot"""
        if self._item.is_match("heatmap", True):
            return

        # get data for selected item
        obj = self._get_item_object()
        self.panel_plot.view_heatmap.plot_contour(obj=obj)
        self.panel_plot.set_page("Heatmap")

        if save_image:
            filename = self._item.get_name("heatmap")
            self.panel_plot.view_heatmap.save_figure(filename=filename)

    def on_show_plot_heatmap_violin(self, _evt, save_image=False):
        """Show heatmap object in a violin plot"""
        if self._item.is_match("heatmap", True):
            return

        # get data for selected item
        obj = self._get_item_object()
        self.panel_plot.view_heatmap.plot_violin(obj=obj)
        self.panel_plot.set_page("Heatmap")

        if save_image:
            filename = self._item.get_name("violin")
            self.panel_plot.view_heatmap.save_figure(filename=filename)

    def on_show_plot_heatmap_joint(self, _evt, save_image=False):
        """Show heatmap object in a joint plot"""
        if self._item.is_match("heatmap", True):
            return

        # get data for selected item
        obj = self._get_item_object()
        self.panel_plot.view_heatmap.plot_joint(obj=obj)
        self.panel_plot.set_page("Heatmap")

        if save_image:
            filename = self._item.get_name("joint")
            self.panel_plot.view_heatmap.save_figure(filename=filename)

    def on_show_plot_heatmap_waterfall(self, _evt, save_image=False):
        """Show heatmap object in a waterfall plot"""
        if self._item.is_match("heatmap", True):
            return

        # get data for selected item
        obj = self._get_item_object()
        self.panel_plot.view_heatmap.plot_waterfall(obj=obj)
        self.panel_plot.set_page("Heatmap")

        if save_image:
            filename = self._item.get_name("waterfall")
            self.panel_plot.view_heatmap.save_figure(filename=filename)

    def on_show_plot_heatmap_3d(self, _evt, save_image=False):
        """Show heatmap object in 3d"""
        if self._item.is_match("heatmap", True):
            return

        # get data for selected item
        obj = self._get_item_object()
        self.panel_plot.view_heatmap_3d.plot(obj=obj)
        self.panel_plot.set_page("Heatmap (3D)")

        if save_image:
            filename = self._item.get_name("heatmap-3d")
            self.panel_plot.view_heatmap_3d.save_figure(filename=filename)

    def on_show_plot_heatmap_chromatogram(self, _evt, save_image=False):
        """Sum heatmap object along one dimension and show it in a chromatogram plot"""
        if self._item.is_match("heatmap", True):
            return

        # get data for selected item
        obj = self._get_item_object()
        obj = obj.as_chromatogram()
        view = self.panel_plot.on_plot_rt(obj=obj, set_page=True)

        if save_image:
            filename = self._item.get_name("heatmap")
            view.save_figure(filename=filename)

    def on_show_plot_heatmap_mobilogram(self, _evt, save_image=False):
        """Sum heatmap object along one dimension and show it in a mobilogram plot"""
        if self._item.is_match("heatmap", True):
            return

        # get data for selected item
        obj = self._get_item_object()
        obj = obj.as_mobilogram()
        view = self.panel_plot.on_plot_1d(obj=obj, set_page=True)

        if save_image:
            filename = self._item.get_name("heatmap")
            view.save_figure(filename=filename)

    def on_show_plot(self, evt, save_image=False):
        """ This will send data, plot and change window"""
        if self._item.is_empty:
            return

        if isinstance(evt, int):
            evt_id = evt
        elif evt is None:
            evt_id = None
        else:
            evt_id = evt.GetId()

        _click_obj = self._item.current  # self._document_type
        # show annotated data
        if _click_obj in "Annotated data":
            # exit early if user clicked on the header
            if self._item.leaf == "Annotated data":
                return

        # show mass spectrum
        elif _click_obj == "Mass Spectra":
            self.on_show_plot_mass_spectra(evt_id, save_image)

        # show mobilogram
        elif _click_obj == "Mobilograms":
            self.on_show_plot_mobilogram(evt_id, save_image)

        # show chromatogram
        elif _click_obj == "Chromatograms":
            self.on_show_plot_chromatogram(evt_id, save_image)

        # show heatmap
        elif _click_obj == "Heatmaps":
            self.on_show_plot_heatmap(evt_id, save_image)

        # show dt/ms plot
        elif _click_obj == "Heatmaps (MS/DT)" or evt_id in [
            ID_ylabel_DTMS_bins,
            ID_ylabel_DTMS_ms,
            ID_ylabel_DTMS_restore,
        ]:
            self.on_show_plot_dtms(save_image)

    def on_save_csv(self, _evt):
        """This function extracts the 1D or 2D data and saves it in a CSV format"""
        obj = self._get_item_object()
        if not hasattr(obj, "to_csv"):
            raise NotImplementedError("Must implement method")

        # get filename
        filename = self._item.get_name("")
        self.data_handling.on_save_data_as_text(obj, None, None, default_name=filename)

    #     def onOpenDocInfo(self, evt):
    #
    #         self.presenter.currentDoc = self.on_enable_document()
    #         document_title = self.on_enable_document()
    #         if self.presenter.currentDoc == "Documents":
    #             return
    #         document = ENV.get(document_title, None)
    #
    #         if document is None:
    #             return
    #
    #         for key in ENV:
    #             print(ENV[key].title)
    #
    #         if self._indent == 2 and any(
    #             self._document_type in itemType for itemType in ["Drift time (2D)", "Drift time (2D, processed)"]
    #         ):
    #             kwargs = {"currentTool": "plot2D", "itemType": self._document_type, "extractData": None}
    #             self.panelInfo = PanelDocumentInformation(self, self.presenter, self.config, self.icons, document,
    #             **kwargs)
    #         elif self._indent == 3 and any(
    #             self._document_type in itemType
    #             for itemType in [
    #                 "Drift time (2D, EIC)",
    #                 "Drift time (2D, combined voltages, EIC)",
    #                 "Drift time (2D, processed, EIC)",
    #                 "Input data",
    #             ]
    #         ):
    #             kwargs = {"currentTool": "plot2D", "itemType": self._document_type, "extractData": self._item_leaf}
    #             self.panelInfo = PanelDocumentInformation(self, self.presenter, self.config, self.icons, document,
    #             **kwargs)
    #         else:
    #
    #             kwargs = {"currentTool": "summary", "itemType": None, "extractData": None}
    #             self.panelInfo = PanelDocumentInformation(self, self.presenter, self.config, self.icons, document,
    #             **kwargs)
    #
    #         self.panelInfo.Show()

    def _add_annotation_to_object(self, data, root_obj, check=False):
        if check:
            child, cookie = self.GetFirstChild(root_obj)
            while child.IsOk():
                if self.GetItemText(child) == "Annotations":
                    self.Delete(child)
                child, cookie = self.GetNextChild(root_obj, cookie)

        # add annotations
        if "annotations" in data and len(data["annotations"]) > 0:
            branch_item = self.AppendItem(root_obj, "Annotations")
            self.SetItemImage(branch_item, self.bullets_dict["annot"])

    def _add_unidec_to_object(self, data, root_obj, check=False):
        if check:
            child, cookie = self.GetFirstChild(root_obj)
            while child.IsOk():
                if self.GetItemText(child) == "UniDec":
                    self.Delete(child)
                child, cookie = self.GetNextChild(root_obj, cookie)

        # add unidec results
        if "unidec" in data:
            branch_item = self.AppendItem(root_obj, "UniDec")
            self.SetItemImage(branch_item, self.bullets_dict["mass_spec"])
            for unidec_name in data["unidec"]:
                leaf_item = self.AppendItem(branch_item, unidec_name)
                self.SetItemData(leaf_item, data["unidec"][unidec_name])
                self.SetItemImage(leaf_item, self.bullets_dict["mass_spec"])

    def _get_group_metadata(self, key):
        parts = key.split("/")
        group_dict = {
            "MassSpectra": {"title": "Mass Spectra", "image": self.bullets_dict["mass_spec"]},
            "Chromatograms": {"title": "Chromatograms", "image": self.bullets_dict["rt"]},
            "Mobilograms": {"title": "Mobilograms", "image": self.bullets_dict["drift_time"]},
            "IonHeatmaps": {"title": "Heatmaps", "image": self.bullets_dict["heatmap"]},
            "MSDTHeatmaps": {"title": "Heatmaps (MS/DT)", "image": self.bullets_dict["heatmap"]},
            "Overlays": {"title": "Overlays", "image": self.bullets_dict["overlay"]},
            "CCSCalibrations": {"title": "Calibration (CCS)", "image": self.bullets_dict["calibration"]},
        }
        return group_dict.get(parts[0]), parts[0], parts[1]

    @staticmethod
    def _get_group_title(key):
        """Return formatted group title"""
        group_dict = {
            "MassSpectra": "MassSpectra",
            "Mass Spectra": "MassSpectra",
            "IonHeatmaps": "IonHeatmaps",
            "Heatmaps": "IonHeatmaps",
            "MSDTHeatmaps": "MSDTHeatmaps",
            "Heatmaps (MS/DT)": "MSDTHeatmaps",
            "Calibration (CCS)": "CCSCalibrations",
            "CCSCalibrations": "CCSCalibrations",
            "Overlays": "Overlays",
        }
        return group_dict.get(key, key)

    def env_update_document(self, evt, metadata):
        """Update document based on event change"""
        print(evt, metadata)
        # def get_document():
        #     item, cookie = self.GetFirstChild(self.GetRootItem())
        #     while item.IsOk():
        #         if self.GetItemText(item) == title:
        #             return item
        #         item, cookie = self.GetNextChild(item, cookie)
        #     return None
        #
        # for title, name in metadata:
        #     pass
        #     # print("item", get_document(), name)

    def add_document(self, document: DocumentStore, expand_item=None, expand_all=False):
        """Add document to the document tree"""
        # check document format
        if not isinstance(document, DocumentStore):
            raise ValueError("Old-style documents are no longer supported - change the method!")

        # Get title for added data
        title = byte2str(document.title)

        if not title:
            title = "Document"
        # Get root
        root = self.GetRootItem()

        item, cookie = self.GetFirstChild(self.GetRootItem())
        while item.IsOk():
            if self.GetItemText(item) == title:
                self.Delete(item)
            item, cookie = self.GetNextChild(root, cookie)

        # Add document
        document_item = self.AppendItem(self.GetRootItem(), title)
        self.SetItemImage(document_item, self.bullets_dict["document_on"])
        self.SetItemData(document_item, (title, ""))
        self.SetFocusedItem(document_item)

        tree_view = document.view()
        for key in tree_view:
            group_metadata, group_key, child_title = self._get_group_metadata(key)

            # expect dictionary with title and image information
            if group_metadata:
                group_item = self.get_item_by_label(group_metadata["title"], document_item)
                if not group_item:
                    group_item = self.AppendItem(document_item, group_metadata["title"])
                    self.SetItemImage(group_item, group_metadata["image"])
                    self.SetItemData(group_item, (title, group_key))

                child_item = self.AppendItem(group_item, child_title)
                self.SetItemImage(child_item, group_metadata["image"])
                self.SetItemData(child_item, (title, key))
        self.on_enable_document(loading_data=True, expand_all=expand_all)

        # If expand_item is not empty, the Tree will expand specified item
        if expand_item is not None:
            try:
                item = self.get_item_by_label(expand_item, document_item)
                if item is not None:
                    self.Expand(item)
            except Exception:
                pass

    def _get_document_item(self, document_title: str):
        """Return the Tree object that is associated with the document"""
        root = self.GetRootItem()
        item, cookie = self.GetFirstChild(self.GetRootItem())
        while item.IsOk():
            if self.GetItemText(item) == document_title:
                return item
            item, cookie = self.GetNextChild(root, cookie)
        return None

    def on_update_document(self, group_name: str, item_name: str, document_title: str, expand_group: bool = True):
        """Update document data without resetting currently expanded items

        Parameters
        ----------
        group_name : str
            name of the group that needs to be updated (e.g. MassSpectra)
        item_name : str
            name of the object that needs to be added to the DocumentTree. The name should not include the group name.
        document_title : str
            name of the document that needs to be updated
        expand_group : bool
            flag to expand the group upon update
        """
        document_item = self._get_document_item(document_title)
        if document_item is None:
            return

        # get proper group title that matches the Document storage options
        _group_name = self._get_group_title(group_name)

        # get key formatter
        if f"{_group_name}/" not in item_name:
            item_name = f"{_group_name}/{item_name}"
        group_metadata, group_key, child_title = self._get_group_metadata(item_name)

        # expect dictionary with title and image information
        group_item, child_item = None, None
        if group_metadata:
            group_item = self.get_item_by_label(group_metadata["title"], document_item)
            # append group item
            if not group_item:
                group_item = self.AppendItem(document_item, group_metadata["title"])
                self.SetItemImage(group_item, group_metadata["image"])
                self.SetItemData(group_item, (document_title, group_key))

            # append item
            child_item = self.get_item_by_label(child_title, group_item)
            if child_item.IsOk():
                self.Delete(child_item)

            # append item
            child_item = self.AppendItem(group_item, child_title)
            self.SetItemImage(child_item, group_metadata["image"])
            self.SetItemData(child_item, (document_title, item_name))

        # If expand_group is not empty, the Tree will expand specified item
        if expand_group:
            if group_item and group_item.IsOk():
                self.Expand(group_item)
            if child_item and child_item.IsOk():
                self.ScrollTo(child_item)
                self.SelectItem(child_item)

    def remove_document(self, document_title: str):
        """Remove document from the document tree

        Parameters
        ----------
        document_title : str
            name of the document that has been removed from the environment
        """
        root = None
        if root is None:
            root = self.GetRootItem()

        # Delete item from the list
        if self.ItemHasChildren(root):
            child, cookie = self.GetFirstChild(self.GetRootItem())
            title = self.GetItemText(child)
            n_iters = 0
            while document_title != title and n_iters < 500:
                child, cookie = self.GetNextChild(self.GetRootItem(), cookie)
                title = self.GetItemText(child)
                n_iters += 1

            if document_title == title:
                if child:
                    self.Delete(child)
                    gc.collect()
                    LOGGER.info(f"Deleted document {document_title}")

                    # notify other GUI elements that need to be informed of document being deleted
                    pub.sendMessage("document.delete.item", info=(document_title, None))

    def on_remove_document(self, _evt):
        """User-driven removal of a document"""
        if self._item.title is not None:
            ENV.remove(self._item.title)
            self.panel_plot.on_clear_all_plots()
            self.on_enable_document()

    def on_remove_document_from_disk(self, _evt):
        """User-driven removal of the document from ORIGAMI and from disk"""
        dlg = DialogBox(
            title="Are you sure?",
            msg=f"Are you sure you would like to delete {self._item.title} from disk?\nThis action is NOT reversible?",
            kind="Question",
        )
        if dlg == wx.ID_NO:
            LOGGER.debug("Delete action was cancelled")
            return

        document = ENV.remove(self._item.title)
        document.delete()
        self.panel_plot.on_clear_all_plots()
        self.on_enable_document()
        pub.sendMessage(
            "notify.message.success",
            message=f"Document `{self._item.title}` was moved to the recycle bin where you can still recover it.",
        )

    def on_about_dataset(self, _evt):
        """Get information about the dataset"""
        from origami.gui_elements.panel_dataset_information import PanelDatasetInformation

        document_title = ENV.current
        dlg = PanelDatasetInformation(self, self._icons, self.presenter, document_title)
        dlg.Show()

    def on_delete_all_documents(self, _evt):
        """ Alternative function to delete documents """
        titles = ENV.titles

        for title in titles:
            dlg = DialogBox("Are you sure?", f"Are you sure you would like to close `{title}`?", kind="Question")
            if dlg == wx.ID_NO:
                continue
            ENV.remove(title)
            self.panel_plot.on_clear_all_plots()
            self.on_enable_document()

    def on_duplicate_document(self, _evt):
        """Duplicate existing document and load it"""
        from origami.utils.path import get_duplicate_name

        document = ENV.on_get_document(self._item.title)

        set_path = ""
        if document is not None:
            set_path = os.path.dirname(document.path)

        path = None
        dlg = wx.DirDialog(self.view, "Choose an output path", defaultPath=set_path)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()

        if path is None:
            return

        title = document.title

        n = 10
        while True or n > 0:
            title = get_duplicate_name(title, ".origami")
            if not os.path.exists(os.path.join(path, title)):
                break
            n -= 1
        path = os.path.join(path, title)
        ENV.duplicate(document.title, path)

    # def on_open_MSMS_viewer(self, evt=None, **kwargs):
    #     from origami.widgets.tandem.panel_tandem_spectra_viewer import PanelTandemSpectraViewer
    #
    #     self.panelTandemSpectra = PanelTandemSpectraViewer(
    #         self.presenter.view, self.presenter, self.config, self.icons, **kwargs
    #     )
    #     self.panelTandemSpectra.Show()
    #
    # def on_process_UVPD(self, evt=None, **kwargs):
    #     from origami.widgets.uvpd.panel_UVPD_editor import PanelUVPDEditor
    #
    #     self.panelUVPD = PanelUVPDEditor(self.presenter.view, self.presenter, self.config, self.icons, **kwargs)
    #     self.panelUVPD.Show()
    #
    def on_open_extract_dtms(self, _evt):
        """Open extraction panel"""
        from origami.gui_elements.panel_process_extract_msdt import PanelProcessExtractMSDT

        document_title, _ = self._get_item_info()
        document = ENV.on_get_document(document_title)
        can_extract, is_multifile, file_fmt = document.can_extract()
        if not can_extract:
            raise MessageError("Error", "Cannot extract data for this document")
        if is_multifile:
            raise MessageError(
                "Error", "Cannot extract MS/DT data for this document as it is composed of multiple raw files"
            )
        if file_fmt != "waters":
            raise MessageError("Error", "Extraction of MS/DT data can only be performed on a Waters-based documents")

        dlg = PanelProcessExtractMSDT(self.view, self.presenter, document_title)
        dlg.Show()

    def on_open_peak_picker(self, _evt, document_title: str = None, dataset_name: str = None):
        """Open peak picker"""
        from origami.widgets.mz_picker.panel_peak_picker import PanelPeakPicker

        # get data and annotations
        if document_title is None or dataset_name is None:
            document_title, dataset_name = self._get_item_info()

        # permit only single instance of the peak-picker
        if self._picker_panel:
            self._picker_panel.SetFocus()
            raise MessageError("Warning", "An instance of a Peak Picking panel is already open")

        # initialize peak picker
        self._picker_panel = PanelPeakPicker(
            self.presenter.view, self.presenter, self._icons, document_title=document_title, dataset_name=dataset_name
        )
        self._picker_panel.Show()

    #
    def on_open_extract_data(self, evt, **kwargs):
        raise NotImplementedError("Must implement method")

    #     from origami.gui_elements.panel_process_extract_data import PanelProcessExtractData
    #
    #     document = self.data_handling.on_get_document()
    #
    #     # initialize data extraction panel
    #     self.PanelProcessExtractData = PanelProcessExtractData(
    #         self.presenter.view,
    #         self.presenter,
    #         self.config,
    #         self.icons,
    #         document=document,
    #         document_title=document.title,
    #     )
    #     self.PanelProcessExtractData.Show()
    #
    def on_open_unidec(self, _evt, document_title: str = None, dataset_name: str = None, mz_obj=None):
        """Open UniDec panel which allows processing and visualisation"""
        from origami.widgets.unidec.panel_process_unidec import PanelProcessUniDec

        if document_title is None or dataset_name is None or mz_obj is None:
            document_title, dataset_name = self._get_item_info()
            mz_obj = self._get_item_object()

        if not self._unidec_panel:
            self._unidec_panel = PanelProcessUniDec(
                self.view, self.presenter, self._icons, document_title, dataset_name, mz_obj
            )
        self._unidec_panel.Show()

    def get_item_image(self, image_type: str):
        """Get bullet image that can be used in the DocumentTree"""
        if image_type in ["main.raw.spectrum", "extracted.spectrum", "main.processed.spectrum", "unidec"]:
            image = self.bullets_dict["mass_spec_on"]
        elif image_type == [
            "ion.heatmap.combined",
            "ion.heatmap.raw",
            "ion.heatmap.processed",
            "main.raw.heatmap",
            "main.processed.heatmap",
            "ion.heatmap.comparison",
        ]:
            image = self.bullets_dict["heatmap_on"]
        elif image_type == ["ion.mobilogram", "ion.mobilogram.raw"]:
            image = self.bullets_dict["drift_time_on"]
        elif image_type in ["main.chromatogram", "extracted.chromatogram", "ion.chromatogram.combined"]:
            image = self.bullets_dict["rt_on"]
        elif image_type in ["annotation"]:
            image = self.bullets_dict["annot"]
        else:
            image = self.bullets_dict["heatmap_on"]

        return image

    def on_update_extracted_patches(self, document_title, data_type, ion_name):
        """
        Remove rectangles/patches from plot area. Triggered upon deletion of item
        from the 'classes' subtree.

        Parameters
        ----------
        document_title: str
            name of document
        data_type: str
            name of dataset
        ion_name: str
            name of item
        """

        # remove all patches
        if data_type == "__all__" or ion_name is None:
            self.panel_plot.on_clear_patches(plot="MS")
        # remove specific patch
        else:
            rect_label = "{};{}".format(document_title, ion_name)
            self.panel_plot.plot_remove_patches_with_labels(rect_label, plot_window="MS")

        self.panel_plot.plot_repaint(plot_window="MS")


def _main_popup():
    from origami.gui_elements._panel import TestPanel  # noqa

    class TestPopup(TestPanel):
        """Test the popup window"""

        def __init__(self, parent):
            super().__init__(parent)

            self.btn_1.Bind(wx.EVT_BUTTON, self.on_popup)

        def on_popup(self, evt):
            """Activate popup"""
            p = PopupDocumentTreeSettings(self)
            p.position_on_event(evt)
            p.Show()

    app = wx.App()

    dlg = TestPopup(None)
    dlg.Show()

    app.MainLoop()


if __name__ == "__main__":
    _main_popup()
