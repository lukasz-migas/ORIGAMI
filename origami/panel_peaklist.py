# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.ids import ID_extractNewIon
from origami.ids import ID_extractAllIons
from origami.ids import ID_window_ionList
from origami.ids import ID_ionPanel_editItem
from origami.ids import ID_extractSelectedIon
from origami.ids import ID_ionPanel_check_all
from origami.ids import ID_ionPanel_clear_all
from origami.ids import ID_ionPanel_delete_all
from origami.ids import ID_highlightRectAllIons
from origami.ids import ID_ionPanel_assignColor
from origami.ids import ID_ionPanel_show_heatmap
from origami.ids import ID_ionPanel_annotate_mask
from origami.ids import ID_ionPanel_annotate_alpha
from origami.ids import ID_ionPanel_check_selected
from origami.ids import ID_ionPanel_clear_selected
from origami.ids import ID_ionPanel_delete_selected
from origami.ids import ID_ionPanel_show_mobilogram
from origami.ids import ID_ionPanel_show_zoom_in_MS
from origami.ids import ID_ionPanel_automaticExtract
from origami.ids import ID_ionPanel_delete_rightClick
from origami.ids import ID_ionPanel_show_chromatogram
from origami.ids import ID_ionPanel_changeColormapBatch
from origami.ids import ID_ionPanel_show_process_heatmap
from origami.ids import ID_ionPanel_annotate_charge_state
from origami.ids import ID_ionPanel_annotate_max_threshold
from origami.ids import ID_ionPanel_annotate_min_threshold
from origami.ids import ID_ionPanel_changeColorBatch_color
from origami.ids import ID_ionPanel_changeColorBatch_palette
from origami.ids import ID_ionPanel_changeColorBatch_colormap
from origami.styles import make_tooltip
from origami.styles import make_menu_item
from origami.utils.check import isempty
from origami.utils.color import get_font_color
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.color import convert_rgb_255_to_1
from origami.utils.labels import get_ion_name_from_label
from origami.config.config import CONFIG
from origami.utils.exceptions import MessageError
from origami.config.environment import ENV
from origami.gui_elements.dialog_ask import DialogAsk
from origami.gui_elements.panel_base import PanelBase
from origami.gui_elements.misc_dialogs import DialogBox

LOGGER = logging.getLogger(__name__)


class PanelPeaklist(PanelBase):
    KEYWORD_ALIAS = {"colormap": "cmap"}

    TABLE_DICT = {
        0: {
            "name": "",
            "tag": "check",
            "type": "bool",
            "order": 0,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 25,
            "hidden": True,
        },
        1: {
            "name": "ion name",
            "tag": "ion_name",
            "type": "str",
            "order": 1,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 130,
        },
        2: {"name": "z", "tag": "charge", "type": "int", "order": 2, "id": wx.NewIdRef(), "show": True, "width": 25},
        3: {
            "name": "int",
            "tag": "intensity",
            "type": "float",
            "order": 3,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 60,
        },
        4: {
            "name": "color",
            "tag": "color",
            "type": "color",
            "order": 4,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 60,
        },
        5: {
            "name": "colormap",
            "tag": "colormap",
            "type": "str",
            "order": 5,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 70,
        },
        6: {
            "name": "\N{GREEK SMALL LETTER ALPHA}",
            "tag": "alpha",
            "type": "float",
            "order": 6,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 35,
        },
        7: {"name": "mask", "tag": "mask", "type": "float", "order": 7, "id": wx.NewIdRef(), "show": True, "width": 40},
        8: {"name": "label", "tag": "label", "type": "str", "order": 8, "id": wx.NewIdRef(), "show": True, "width": 50},
        9: {
            "name": "method",
            "tag": "method",
            "type": "str",
            "order": 8,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 50,
        },
        10: {
            "name": "document",
            "tag": "document",
            "type": "str",
            "order": 9,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 100,
        },
        11: {
            "name": "key",
            "tag": "key",
            "type": "str",
            "order": 11,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 0,
            "hidden": True,
        },
    }

    def __init__(self, parent, icons, presenter):
        PanelBase.__init__(self, parent, icons, presenter)

        self.allChecked = True
        self.override = CONFIG.overrideCombine
        self.addToDocument = False
        self.normalize1D = False
        self.extractAutomatically = False
        self.plotAutomatically = True

        self.item_editor = None
        self.onSelectingItem = True
        self.ask_value = None
        self.flag = False  # flag to either show or hide annotation panel
        self.process = False

        # add a couple of accelerators
        accelerators = [
            (wx.ACCEL_NORMAL, ord("C"), ID_ionPanel_assignColor),
            (wx.ACCEL_NORMAL, ord("E"), ID_ionPanel_editItem),
            (wx.ACCEL_NORMAL, ord("H"), ID_highlightRectAllIons),
            (wx.ACCEL_NORMAL, ord("M"), ID_ionPanel_show_mobilogram),
            (wx.ACCEL_NORMAL, ord("S"), ID_ionPanel_check_selected),
            (wx.ACCEL_NORMAL, ord("X"), ID_ionPanel_check_all),
            (wx.ACCEL_NORMAL, ord("Z"), ID_ionPanel_show_zoom_in_MS),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, ID_ionPanel_delete_rightClick),
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))

        wx.EVT_MENU(self, ID_ionPanel_editItem, self.on_open_editor)
        wx.EVT_MENU(self, ID_ionPanel_assignColor, self.on_assign_color)
        wx.EVT_MENU(self, ID_ionPanel_show_zoom_in_MS, self.on_plot)
        wx.EVT_MENU(self, ID_ionPanel_show_mobilogram, self.on_plot)
        wx.EVT_MENU(self, ID_ionPanel_check_selected, self.on_check_selected)
        wx.EVT_MENU(self, ID_ionPanel_delete_rightClick, self.on_delete_item)

    def setup_handling_and_processing(self):
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling
        self.data_visualisation = self.view.data_visualisation
        self.document_tree = self.presenter.view.panelDocuments.documents

    def on_open_info_panel(self, evt):
        LOGGER.error("This function is not implemented yet")

    # noinspection DuplicatedCode
    def make_toolbar(self):

        add_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["add16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        add_btn.SetToolTip(make_tooltip("Add..."))

        remove_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["remove16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        remove_btn.SetToolTip(make_tooltip("Remove..."))

        annotate_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["annotate16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        annotate_btn.SetToolTip(make_tooltip("Annotate..."))

        extract_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["extract16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        extract_btn.SetToolTip(make_tooltip("Extract..."))

        process_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["process16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        process_btn.SetToolTip(make_tooltip("Process..."))

        save_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["save16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        save_btn.SetToolTip(make_tooltip("Save..."))

        vertical_line_1 = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)

        info_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["info16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        info_btn.SetToolTip(make_tooltip("Information..."))

        # bind events
        self.Bind(wx.EVT_BUTTON, self.menu_add_tools, add_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_remove_tools, remove_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_extract_tools, extract_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_process_tools, process_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_save_tools, save_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_annotate_tools, annotate_btn)
        self.Bind(wx.EVT_BUTTON, self.on_open_info_panel, info_btn)

        # button grid
        toolbar = wx.BoxSizer(wx.HORIZONTAL)
        toolbar.Add(add_btn, 0, wx.ALIGN_CENTER)
        toolbar.Add(remove_btn, 0, wx.ALIGN_CENTER)
        toolbar.Add(annotate_btn, 0, wx.ALIGN_CENTER)
        toolbar.Add(process_btn, 0, wx.ALIGN_CENTER)
        toolbar.Add(save_btn, 0, wx.ALIGN_CENTER)
        toolbar.AddSpacer(5)
        toolbar.Add(vertical_line_1, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        toolbar.AddSpacer(5)
        toolbar.Add(info_btn, 0, wx.ALIGN_CENTER)

        return toolbar

    def on_double_click_on_item(self, evt):
        """Create annotation for activated peak."""

        if self.peaklist.item_id != -1:
            if not self.item_editor:
                self.on_open_editor(evt=None)
            else:
                self.item_editor.on_update_gui(self.on_get_item_information(self.peaklist.item_id))

    def onRenameItem(self, old_name, new_name, item_type="Document"):
        for row in range(self.peaklist.GetItemCount()):
            itemInfo = self.on_get_item_information(itemID=row)
            if item_type == "document":
                if itemInfo["document"] == old_name:
                    self.peaklist.SetStringItem(row, CONFIG.peaklistColNames["filename"], new_name)

    def on_menu_item_right_click(self, evt):

        self.peaklist.item_id = evt.GetIndex()
        menu = wx.Menu()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_show_zoom_in_MS,
                text="Zoom in on the ion\tZ",
                bitmap=self.icons.iconsLib["zoom_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_show_chromatogram,
                text="Show chromatogram",
                bitmap=self.icons.iconsLib["chromatogram_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_show_mobilogram,
                text="Show mobilogram\tM",
                bitmap=self.icons.iconsLib["mobilogram_16"],
            )
        )
        menu_action_show_heatmap = make_menu_item(
            parent=menu, id=ID_ionPanel_show_heatmap, text="Show heatmap", bitmap=self.icons.iconsLib["heatmap_16"]
        )
        menu.AppendItem(menu_action_show_heatmap)

        menu_action_process_heatmap = make_menu_item(
            parent=menu, id=ID_ionPanel_show_heatmap, text="Process heatmap..."
        )
        menu.AppendItem(menu_action_process_heatmap)
        menu.AppendSeparator()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_assignColor,
                text="Assign new color\tC",
                bitmap=self.icons.iconsLib["color_panel_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_editItem,
                text="Edit ion information\tE",
                bitmap=self.icons.iconsLib["info16"],
            )
        )
        menu.AppendSeparator()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_delete_rightClick,
                text="Remove item\tDelete",
                bitmap=self.icons.iconsLib["bin16"],
            )
        )

        # bind events
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_zoom_in_MS)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_mobilogram)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_heatmap)
        self.Bind(wx.EVT_MENU, self.on_plot, menu_action_process_heatmap, id=ID_ionPanel_show_process_heatmap)
        self.Bind(wx.EVT_MENU, self.on_open_editor, id=ID_ionPanel_editItem)
        self.Bind(wx.EVT_MENU, self.on_assign_color, id=ID_ionPanel_assignColor)
        self.Bind(wx.EVT_MENU, self.on_delete_item, id=ID_ionPanel_delete_rightClick)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_annotate_tools(self, evt):
        self.Bind(wx.EVT_MENU, self.data_handling.on_highlight_selected_ions, id=ID_highlightRectAllIons)
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_ionPanel_annotate_charge_state)
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_ionPanel_annotate_alpha)
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_ionPanel_annotate_mask)
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_ionPanel_annotate_min_threshold)
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_ionPanel_annotate_max_threshold)
        self.Bind(wx.EVT_MENU, self.on_change_item_color_batch, id=ID_ionPanel_changeColorBatch_color)
        self.Bind(wx.EVT_MENU, self.on_change_item_color_batch, id=ID_ionPanel_changeColorBatch_palette)
        self.Bind(wx.EVT_MENU, self.on_change_item_color_batch, id=ID_ionPanel_changeColorBatch_colormap)
        self.Bind(wx.EVT_MENU, self.on_change_item_colormap, id=ID_ionPanel_changeColormapBatch)

        menu = wx.Menu()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_highlightRectAllIons,
                text="Highlight extracted items on MS plot (all)\tH",
                bitmap=self.icons.iconsLib["highlight_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_annotate_charge_state,
                text="Assign charge state (selected)",
                bitmap=self.icons.iconsLib["assign_charge_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_annotate_alpha,
                text="Assign transparency value (selected)",
                bitmap=self.icons.iconsLib["transparency_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_annotate_mask,
                text="Assign mask value (selected)",
                bitmap=self.icons.iconsLib["mask_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_annotate_min_threshold,
                text="Assign minimum threshold (selected)",
                bitmap=self.icons.iconsLib["min_threshold_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_annotate_max_threshold,
                text="Assign maximum threshold (selected)",
                bitmap=self.icons.iconsLib["max_threshold_16"],
            )
        )
        menu.AppendSeparator()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_changeColorBatch_color,
                text="Assign new color using color picker (selected)",
                bitmap=self.icons.iconsLib["color_panel_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_changeColorBatch_palette,
                text="Assign new color using color palette (selected)",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_changeColorBatch_colormap,
                text="Assign new color using colormap (selected)",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_changeColormapBatch,
                text="Assign new colormap (selected)",
                bitmap=self.icons.iconsLib["randomize_16"],
            )
        )

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_add_tools(self, evt):
        menu = wx.Menu()
        menu_action_load_peaklist = make_menu_item(
            parent=menu,
            text="Add list of ions (.csv/.txt)",
            bitmap=self.icons.iconsLib["filelist_16"],
            help_text="Format: mz_start, mz_end, charge (optional), label (optional), color (optional)...",
        )
        menu.AppendItem(menu_action_load_peaklist)
        menu.AppendSeparator()
        menu_action_restore_peaklist = make_menu_item(
            parent=menu,
            text="Restore items to peaklist",
            help_text="Restore items for selected document to the peaklist",
        )
        menu.AppendItem(menu_action_restore_peaklist)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_load_peaklist, menu_action_load_peaklist)
        self.Bind(wx.EVT_MENU, self.on_restore_to_peaklist, menu_action_restore_peaklist)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_extract_tools(self, evt):
        # TODO: add Extract chromatographic data only
        # TODO: add extract mobilogram data only

        self.Bind(wx.EVT_MENU, self.on_check_tool, id=ID_ionPanel_automaticExtract)
        self.Bind(wx.EVT_MENU, self.on_extract_all, id=ID_extractAllIons)
        self.Bind(wx.EVT_MENU, self.on_extract_selected, id=ID_extractSelectedIon)
        self.Bind(wx.EVT_MENU, self.on_extract_new, id=ID_extractNewIon)

        menu = wx.Menu()
        self.automaticExtract_check = menu.AppendCheckItem(
            ID_ionPanel_automaticExtract,
            "Automatically extract data",
            help="Data will be automatically extracted as its added to the peaklist",
        )
        self.automaticExtract_check.Check(self.extractAutomatically)
        menu.AppendSeparator()
        menu.Append(ID_extractNewIon, "Extract heatmap data (new)")
        menu.Append(ID_extractSelectedIon, "Extract heatmap data (selected)")
        menu.Append(ID_extractAllIons, "Extract heatmap data (all)\tAlt+E")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_remove_tools(self, evt):
        # Make bindings
        self.Bind(wx.EVT_MENU, self.on_delete_selected, id=ID_ionPanel_delete_selected)
        self.Bind(wx.EVT_MENU, self.on_delete_all, id=ID_ionPanel_delete_all)
        self.Bind(wx.EVT_MENU, self.peaklist.on_clear_table_all, id=ID_ionPanel_clear_all)
        self.Bind(wx.EVT_MENU, self.peaklist.on_clear_table_selected, id=ID_ionPanel_clear_selected)

        menu = wx.Menu()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_clear_selected,
                text="Remove from list (selected)",
                bitmap=self.icons.iconsLib["clear_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_clear_all,
                text="Remove from list (all)",
                bitmap=self.icons.iconsLib["clear_16"],
            )
        )

        menu.AppendSeparator()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_delete_selected,
                text="Remove from file (selected)",
                bitmap=self.icons.iconsLib["bin16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_ionPanel_delete_all,
                text="Remove from file (all)",
                bitmap=self.icons.iconsLib["bin16"],
            )
        )
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_process_tools(self, evt):
        menu = wx.Menu()
        menu_action_process_heatmap = make_menu_item(parent=menu, text="Process heatmap data (selected)")
        menu.AppendItem(menu_action_process_heatmap)

        menu.AppendSeparator()
        menu_action_setup_origami_parameters = make_menu_item(parent=menu, text="ORIGAMI-MS: Setup parameters..")
        menu.AppendItem(menu_action_setup_origami_parameters)

        menu_action_combine_voltages = make_menu_item(
            parent=menu, text="ORIGAMI-MS: Combine collision voltages (selected)"
        )
        menu.AppendItem(menu_action_combine_voltages)

        menu_action_extract_spectrum = make_menu_item(
            parent=menu, text="ORIGAMI-MS: Extract mass spectra for each collision voltage..."
        )
        menu.AppendItem(menu_action_extract_spectrum)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_process_heatmap_selected, menu_action_process_heatmap)
        self.Bind(wx.EVT_MENU, self.data_processing.on_combine_origami_collision_voltages, menu_action_combine_voltages)
        self.Bind(wx.EVT_MENU, self.on_open_ORIGAMI_MS_panel, menu_action_setup_origami_parameters)
        self.Bind(wx.EVT_MENU, self.on_open_ORIGAMI_MS_panel, menu_action_extract_spectrum)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_save_tools(self, evt):

        menu = wx.Menu()
        menu_action_save_peaklist = make_menu_item(parent=menu, text="Export peak list to file...")
        menu.AppendItem(menu_action_save_peaklist)

        menu.AppendSeparator()
        menu_action_save_chromatogram = make_menu_item(parent=menu, text="Save figure(s) as chromatogram (selected)")
        menu.AppendItem(menu_action_save_chromatogram)

        menu_action_save_mobilogram = make_menu_item(parent=menu, text="Save figure(s) as mobilogram (selected)")
        menu.AppendItem(menu_action_save_mobilogram)

        menu_action_save_heatmap = make_menu_item(parent=menu, text="Save figure(s) as heatmap (selected)")
        menu.AppendItem(menu_action_save_heatmap)

        menu_action_save_waterfall = make_menu_item(parent=menu, text="Save figure(s) as waterfall (selected)")
        menu.AppendItem(menu_action_save_waterfall)

        menu.AppendSeparator()
        menu_action_save_data_chromatogram = make_menu_item(parent=menu, text="Save chromatographic data (selected)")
        menu.AppendItem(menu_action_save_data_chromatogram)

        menu_action_save_data_mobilogram = make_menu_item(parent=menu, text="Save mobilogram data (selected)")
        menu.AppendItem(menu_action_save_data_mobilogram)

        menu_action_save_data_heatmap = make_menu_item(parent=menu, text="Save heatmap data (selected)")
        menu.AppendItem(menu_action_save_data_heatmap)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_save_peaklist, menu_action_save_peaklist)

        self.Bind(wx.EVT_MENU, self.on_save_figures_chromatogram, menu_action_save_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_save_figures_mobilogram, menu_action_save_mobilogram)
        self.Bind(wx.EVT_MENU, self.on_save_figures_heatmap, menu_action_save_heatmap)
        self.Bind(wx.EVT_MENU, self.on_save_figures_waterfall, menu_action_save_waterfall)

        self.Bind(wx.EVT_MENU, self.on_save_data_chromatogram, menu_action_save_data_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_save_data_mobilogram, menu_action_save_data_mobilogram)
        self.Bind(wx.EVT_MENU, self.on_save_data_heatmap, menu_action_save_data_heatmap)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_check_tool(self, evt):
        """ Check/uncheck menu item """

        evtID = evt.GetId()

        if evtID == ID_ionPanel_automaticExtract:
            self.extractAutomatically = not self.extractAutomatically
            args = ("Automatic extraction was set to: {}".format(self.extractAutomatically), 4)
            self.presenter.onThreading(evt, args, action="updateStatusbar")

    def on_change_item_parameter(self, evt):
        """ Iterate over list to assign charge state """

        rows = self.peaklist.GetItemCount()
        if rows == 0:
            return

        if evt.GetId() == ID_ionPanel_annotate_charge_state:
            ask_kwargs = {
                "static_text": "Assign charge state to selected items.",
                "value_text": "",
                "validator": "integer",
                "keyword": "charge",
            }
        elif evt.GetId() == ID_ionPanel_annotate_alpha:
            static_text = (
                "Assign new transparency value to selected items \nTypical transparency values: 0.5" + "\nRange 0-1"
            )
            ask_kwargs = {"static_text": static_text, "value_text": 0.5, "validator": "float", "keyword": "alpha"}
        elif evt.GetId() == ID_ionPanel_annotate_mask:
            ask_kwargs = {
                "static_text": "Assign new mask value to selected items \nTypical mask values: 0.25\nRange 0-1",
                "value_text": 0.25,
                "validator": "float",
                "keyword": "mask",
            }
        elif evt.GetId() == ID_ionPanel_annotate_min_threshold:
            ask_kwargs = {
                "static_text": "Assign minimum threshold value to selected items \nTypical mask values: 0.0\nRange 0-1",
                "value_text": 0.0,
                "validator": "float",
                "keyword": "min_threshold",
            }
        elif evt.GetId() == ID_ionPanel_annotate_max_threshold:
            ask_kwargs = {
                "static_text": "Assign maximum threshold value to selected items \nTypical mask values: 1.0\nRange 0-1",
                "value_text": 1.0,
                "validator": "float",
                "keyword": "max_threshold",
            }
        else:
            raise ValueError("Not sure what to do...")

        ask = DialogAsk(self, **ask_kwargs)
        ask.ShowModal()

        if self.ask_value is None:
            LOGGER.info("Action was cancelled")
            return

        for row in range(rows):
            if self.peaklist.IsChecked(index=row):
                itemInfo = self.on_get_item_information(row)
                filename = itemInfo["document"]
                selectedText = itemInfo["ionName"]
                document = ENV[filename]
                if not ask_kwargs["keyword"] in ["min_threshold", "max_threshold"]:
                    self.peaklist.SetStringItem(
                        row, CONFIG.peaklistColNames[ask_kwargs["keyword"]], str(self.ask_value)
                    )

                if selectedText in document.IMS2Dions:
                    document.IMS2Dions[selectedText][ask_kwargs["keyword"]] = self.ask_value
                if selectedText in document.IMS2DCombIons:
                    document.IMS2DCombIons[selectedText][ask_kwargs["keyword"]] = self.ask_value
                if selectedText in document.IMS2DionsProcess:
                    document.IMS2DionsProcess[selectedText][ask_kwargs["keyword"]] = self.ask_value
                if selectedText in document.IMSRTCombIons:
                    document.IMSRTCombIons[selectedText][ask_kwargs["keyword"]] = self.ask_value

                # Update document
                self.data_handling.on_update_document(document, "no_refresh")

    def on_check_duplicate(self, ion_name, document):
        """Check whether ion name exist in table"""
        rows = self.peaklist.GetItemCount()

        for row in range(rows):
            ion_name_in_table = self.peaklist.GetItem(row, CONFIG.peaklistColNames["ion_name"]).GetText()
            document_in_table = self.peaklist.GetItem(row, CONFIG.peaklistColNames["filename"]).GetText()
            if (ion_name_in_table == ion_name) and (document_in_table == document):
                return True
        return False

    def get_selected_items(self):
        all_eic_datasets = [
            "Drift time (2D, EIC)",
            "Drift time (2D, processed, EIC)",
            "Drift time (2D, combined voltages, EIC)",
            "Input data",
        ]

        item_count = self.peaklist.GetItemCount()

        # generate list of document_title and dataset_name
        process_list = []
        for item_id in range(item_count):
            information = self.on_get_item_information(item_id)
            if information["select"]:
                for dataset_type in all_eic_datasets:
                    document_title = information["document"]
                    ion_name = information["ion_name"]
                    if document_title not in ["", None]:
                        # append raw
                        process_item = [document_title, dataset_type, ion_name]
                        process_list.append(process_item)

                        # append processed
                        process_item = [document_title, dataset_type, f"{ion_name} (processed)"]
                        process_list.append(process_item)

        return process_list

    def on_process_heatmap_selected(self, evt):
        """Collect list of titles and dataset names and open processing panel"""
        process_list = self.get_selected_items()

        n_items = len(process_list)
        if n_items > 0:
            # open-up panel
            self.document_tree.on_open_process_2D_settings(
                process_all=True, process_list=True, data=process_list, disable_plot=True, disable_process=False
            )

    def on_plot(self, evt, itemID=None):
        """Plot data"""
        if itemID is not None:
            self.peaklist.item_id = itemID
        if self.peaklist.item_id is None:
            return

        itemInfo = self.on_get_item_information(self.peaklist.item_id)
        document_title = itemInfo["document"]
        rangeName = itemInfo["ionName"]

        # Check if data was extracted
        if document_title == "":
            raise MessageError("Error", "Please extract data first.")

        # Get data from dictionary
        document = self.data_handling.on_get_document(document_title)

        # Preset empty
        data, zvals, xvals, xlabel, yvals, ylabel = None, None, None, None, None, None
        # Check whether its ORIGAMI or MANUAL data type
        if document.dataType == "Type: ORIGAMI":
            if document.gotCombinedExtractedIons:
                data = document.IMS2DCombIons
            elif document.gotExtractedIons:
                data = document.IMS2Dions
        elif document.dataType == "Type: MANUAL":
            if document.gotCombinedExtractedIons:
                data = document.IMS2DCombIons
        else:
            return

        if data is None:
            raise MessageError("No data", "Could not find data for this ion")

        evtID = evt if evt is None else evt.GetId()

        if evtID == ID_ionPanel_show_mobilogram:
            xvals = data[rangeName]["yvals"]  # normally this would be the y-axis
            yvals = data[rangeName]["yvals1D"]
            xlabels = data[rangeName]["ylabels"]  # normally this would be x-axis label
            self.view.panelPlots.on_plot_1D(xvals, yvals, xlabels, set_page=True)

        elif evtID == ID_ionPanel_show_chromatogram:
            xvals = data[rangeName]["xvals"]
            yvals = data[rangeName]["yvalsRT"]
            xlabels = data[rangeName]["xlabels"]  # normally this would be x-axis label
            self.view.panelPlots.on_plot_RT(xvals, yvals, xlabels, set_page=True)

        elif evtID == ID_ionPanel_show_zoom_in_MS:
            mz_start, mz_end = get_ion_name_from_label(rangeName, as_num=True)
            mz_start = mz_start - CONFIG.zoomWindowX
            mz_end = mz_end + CONFIG.zoomWindowX

            try:
                self.view.panelPlots.on_zoom_1D_x_axis(startX=mz_start, endX=mz_end, set_page=True, plot="MS")
            except AttributeError:
                LOGGER.error("Failed to zoom-in on an ion - most likely because there is no mass spectrum present")
                return
        else:
            # Unpack data
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(
                dictionary=data[rangeName], dataType="plot", compact=False
            )

            # Warning in case  there is missing data
            if isempty(xvals) or isempty(yvals) or xvals == "" or yvals == "":
                msg = "Missing x/y-axis labels. Cannot continue! \nAdd x/y-axis labels to each file before continuing."
                print(msg)
                DialogBox(exceptionTitle="Missing data", exceptionMsg=msg, type="Error")
                return
            # Process data
            if evtID == ID_ionPanel_show_process_heatmap:
                xvals, yvals, zvals = self.data_processing.on_process_2D(xvals, yvals, zvals, return_data=True)
            # Plot data
            self.view.panelPlots.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, cmap, override=True, set_page=True)

    def on_save_figures(self, plot_type):
        """Save figure(s) for selected item(s)

        Parameters
        ----------
        plot_type : str
            type of plot to be plotted
        """
        process_list = self.get_selected_items()
        self.data_handling.on_save_heatmap_figures(plot_type, process_list)

    def on_save_figures_chromatogram(self, evt):
        self.on_save_figures("chromatogram")

    def on_save_figures_mobilogram(self, evt):
        self.on_save_figures("mobilogram")

    def on_save_figures_heatmap(self, evt):
        self.on_save_figures("heatmap")

    def on_save_figures_waterfall(self, evt):
        self.on_save_figures("waterfall")

    def on_save_data(self, data_type):
        """Save figure(s) for selected item(s)

        Parameters
        ----------
        data_type : str
            type of data to be saved
        """
        process_list = self.get_selected_items()
        self.data_handling.on_save_heatmap_data(data_type, process_list)

    def on_save_data_chromatogram(self, evt):
        self.on_save_data("chromatogram")

    def on_save_data_mobilogram(self, evt):
        self.on_save_data("mobilogram")

    def on_save_data_heatmap(self, evt):
        self.on_save_data("heatmap")

    def on_save_peaklist(self, evt):
        """Save data in CSV format"""
        from origami.utils.color import convert_rgb_255_to_hex

        rows = self.peaklist.GetItemCount()
        if rows == 0:
            return

        data = []
        # Iterate over row and columns to get data
        for row in range(rows):
            information = self.on_get_item_information(row)
            ion_name = information["ion_name"]
            mz_start, mz_end = get_ion_name_from_label(ion_name, as_num=True)
            charge = information["charge"]
            intensity = information["intensity"]
            color = convert_rgb_255_to_hex(information["color"])
            colormap = information["colormap"]
            alpha = information["alpha"]
            mask = information["mask"]
            label = information["label"]
            method = information["method"]
            document = information["document"]
            data.append(
                [ion_name, mz_start, mz_end, charge, intensity, color, colormap, alpha, mask, label, method, document]
            )
        fmt = ["%s", "%.4f", "%.4f", "%i", "%.4f", "%s", "%s", "%.2f", "%.2f", "%s", "%s", "%s"]
        header = [
            "ion_name",
            "mz_start",
            "mz_end",
            "charge",
            "intensity",
            "color",
            "colormap",
            "alpha",
            "mask",
            "label",
            "method",
            "document",
        ]

        self.data_handling.on_save_data_as_text(data, header, fmt, as_object=True)

    def on_find_item(self, ion_name, filename):
        """Find index of item with the provided parameters"""
        item_count = self.peaklist.GetItemCount()

        for item_id in range(item_count):
            information = self.on_get_item_information(item_id)
            if ion_name == information["ionName"] and filename == information["document"]:
                return item_id

    def on_get_item_information(self, itemID, return_list=False):
        information = self.peaklist.on_get_item_information(itemID)

        # add additional data
        information["ionName"] = information["ion_name"]
        information["color_255to1"] = convert_rgb_255_to_1(information["color"], decimals=3)

        # get document
        document = self.data_handling.on_get_document(information["document"])

        # check whether the ion has any previous information
        min_threshold, max_threshold = 0, 1
        try:
            if information["ionName"] in document.IMS2Dions:
                min_threshold = document.IMS2Dions[information["ionName"]].get("min_threshold", 0)
                max_threshold = document.IMS2Dions[information["ionName"]].get("max_threshold", 1)
        except AttributeError:
            pass

        datasets = []
        if information["ionName"] in document.IMS2Dions:
            datasets.append("Drift time (2D, EIC)")
        if information["ionName"] in document.IMS2DionsProcess:
            datasets.append("Drift time (2D, processed, EIC)")
        if information["ionName"] in document.IMS2DCombIons:
            datasets.append("Drift time (2D, combined voltages, EIC)")

        if not datasets:
            datasets = ["Not extracted yet"]

        information["min_threshold"] = min_threshold
        information["max_threshold"] = max_threshold
        information["datasets"] = datasets

        # Check whether the ion has combined ions
        parameters = None
        try:
            parameters = document.IMS2DCombIons[information["ionName"]].get("parameters", None)
        except (KeyError, AttributeError):
            pass
        information["parameters"] = parameters

        return information

    # def on_get_value(self, value_type="color"):
    #     information = self.on_get_item_information(self.peaklist.item_id)
    #
    #     if value_type == "ion_name":
    #         return information["ion_name"]
    #     elif value_type == "color":
    #         return information["color"]
    #     elif value_type == "charge":
    #         return information["charge"]
    #     elif value_type == "colormap":
    #         return information["colormap"]
    #     elif value_type == "intensity":
    #         return information["intensity"]
    #     elif value_type == "mask":
    #         return information["mask"]
    #     elif value_type == "method":
    #         return information["method"]
    #     elif value_type == "document":
    #         return information["document"]
    #     elif value_type == "label":
    #         return information["label"]
    #     elif value_type == "ionName":
    #         return information["ionName"]

    def on_find_and_update_values(self, ion_name, **kwargs):
        item_count = self.peaklist.GetItemCount()

        for item_id in range(item_count):
            information = self.on_get_item_information(item_id)
            if ion_name == information["ionName"]:
                for keyword in kwargs:
                    self.on_update_value_in_peaklist(item_id, keyword, kwargs[keyword])

    def on_update_value_in_peaklist(self, item_id, value_type, value):

        if value_type == "ion_name":
            self.peaklist.SetStringItem(item_id, CONFIG.peaklistColNames["ion_name"], str(value))
        elif value_type == "charge":
            self.peaklist.SetStringItem(item_id, CONFIG.peaklistColNames["charge"], str(value))
        elif value_type == "intensity":
            self.peaklist.SetStringItem(item_id, CONFIG.peaklistColNames["intensity"], str(value))
        elif value_type == "color":
            color_255, color_1, font_color = value
            self.peaklist.SetItemBackgroundColour(item_id, color_255)
            self.peaklist.SetStringItem(item_id, CONFIG.peaklistColNames["color"], str(color_1))
            self.peaklist.SetItemTextColour(item_id, font_color)
        elif value_type == "color_text":
            self.peaklist.SetItemBackgroundColour(item_id, value)
            self.peaklist.SetStringItem(item_id, CONFIG.peaklistColNames["color"], str(convert_rgb_255_to_1(value)))
            self.peaklist.SetItemTextColour(item_id, get_font_color(value, return_rgb=True))
        elif value_type == "colormap":
            self.peaklist.SetStringItem(item_id, CONFIG.peaklistColNames["colormap"], str(value))
        elif value_type == "alpha":
            self.peaklist.SetStringItem(item_id, CONFIG.peaklistColNames["alpha"], str(value))
        elif value_type == "mask":
            self.peaklist.SetStringItem(item_id, CONFIG.peaklistColNames["mask"], str(value))
        elif value_type == "label":
            self.peaklist.SetStringItem(item_id, CONFIG.peaklistColNames["label"], str(value))
        elif value_type == "method":
            self.peaklist.SetStringItem(item_id, CONFIG.peaklistColNames["method"], str(value))
        elif value_type == "document":
            self.peaklist.SetStringItem(item_id, CONFIG.peaklistColNames["filename"], str(value))

    def on_open_editor(self, evt):
        from origami.gui_elements.panel_modify_item_settings import PanelModifyItemSettings

        if self.peaklist.item_id is None:
            LOGGER.warning("Please select an item")
            return

        if self.peaklist.item_id < 0:
            print("Please select item in the table first.")
            return

        information = self.on_get_item_information(self.peaklist.item_id)

        self.item_editor = PanelModifyItemSettings(self, self.presenter, CONFIG, **information)
        self.item_editor.Centre()
        self.item_editor.Show()

    def on_change_item_colormap(self, evt):
        # get number of checked items
        check_count = 0
        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(index=row):
                check_count += 1

        if check_count > len(CONFIG.narrowCmapList):
            colormaps = CONFIG.narrowCmapList
        else:
            colormaps = CONFIG.narrowCmapList + CONFIG.cmaps2

        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(index=row):
                self.peaklist.item_id = row
                colormap = colormaps[row]
                self.peaklist.SetStringItem(row, CONFIG.peaklistColNames["colormap"], str(colormap))

                # update document
                try:
                    self.on_update_document(evt=None)
                except TypeError:
                    print("Please select item")

    def on_change_item_color_batch(self, evt):
        # get number of checked items
        check_count = 0
        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(index=row):
                check_count += 1

        if evt.GetId() == ID_ionPanel_changeColorBatch_palette:
            colors = self.view.panelPlots.on_change_color_palette(None, n_colors=check_count, return_colors=True)
        elif evt.GetId() == ID_ionPanel_changeColorBatch_color:
            __, color_1, __ = self.on_get_color(None)
            if color_1 is None:
                return
            colors = [color_1] * check_count
        else:
            colors = self.view.panelPlots.on_get_colors_from_colormap(n_colors=check_count)

        check_count = 0
        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(index=row):
                self.peaklist.item_id = row
                color_255 = convert_rgb_1_to_255(colors[check_count])
                self.on_update_value_in_peaklist(row, "color_text", color_255)
                check_count += 1

            # update document
            try:
                self.on_update_document(evt=None)
            except TypeError:
                print("Please select an item")

    def on_update_document(self, evt, itemInfo=None):
        """Update document data"""

        # get item info
        if itemInfo is None:
            itemInfo = self.on_get_item_information(self.peaklist.item_id)

        # get item
        document = self.data_handling.on_get_document(itemInfo["document"])

        processed_name = "{} (processed)".format(itemInfo["ionName"])
        keywords = ["color", "colormap", "alpha", "mask", "label", "min_threshold", "max_threshold", "charge"]

        if itemInfo["ionName"] in document.IMS2Dions:
            for keyword in keywords:
                keyword_name = self.KEYWORD_ALIAS.get(keyword, keyword)
                document.IMS2Dions[itemInfo["ionName"]][keyword_name] = itemInfo[keyword]
                if processed_name in document.IMS2Dions:
                    document.IMS2Dions[processed_name][keyword_name] = itemInfo[keyword]

        if f"{itemInfo['ionName']} (processed)" in document.IMS2Dions:
            for keyword in keywords:
                keyword_name = self.KEYWORD_ALIAS.get(keyword, keyword)
                document.IMS2Dions[itemInfo["ionName"]][keyword_name] = itemInfo[keyword]
                if processed_name in document.IMS2Dions:
                    document.IMS2Dions[processed_name][keyword_name] = itemInfo[keyword]

        if itemInfo["ionName"] in document.IMS2DCombIons:
            for keyword in keywords:
                keyword_name = self.KEYWORD_ALIAS.get(keyword, keyword)
                document.IMS2DCombIons[itemInfo["ionName"]][keyword_name] = itemInfo[keyword]
                if processed_name in document.IMS2DCombIons:
                    document.IMS2DCombIons[processed_name][keyword_name] = itemInfo[keyword]

        if itemInfo["ionName"] in document.IMS2DionsProcess:
            for keyword in keywords:
                keyword_name = self.KEYWORD_ALIAS.get(keyword, keyword)
                document.IMS2DionsProcess[itemInfo["ionName"]][keyword_name] = itemInfo[keyword]
                if processed_name in document.IMS2DionsProcess:
                    document.IMS2DionsProcess[processed_name][keyword_name] = itemInfo[keyword]

        if itemInfo["ionName"] in document.IMSRTCombIons:
            for keyword in keywords:
                keyword_name = self.KEYWORD_ALIAS.get(keyword, keyword)
                document.IMSRTCombIons[itemInfo["ionName"]][keyword_name] = itemInfo[keyword]
                if processed_name in document.IMSRTCombIons:
                    document.IMSRTCombIons[processed_name][keyword_name] = itemInfo[keyword]

        # Update document
        self.data_handling.on_update_document(document, "no_refresh")

    def on_open_ORIGAMI_MS_panel(self, evt):
        document = self.data_handling._get_document_of_type(["Type: ORIGAMI"], allow_creation=False)
        if document is None:
            raise MessageError("Error", "Please create/load ORIGAMI document first")

        self.document_tree.on_action_ORIGAMI_MS(None, document.title)

    def on_load_peaklist(self, evt):
        """This function opens a formatted CSV file with peaks"""

        document = self.data_handling._get_document_of_type(
            ["Type: MANUAL", "Type: ORIGAMI", "Type: Infrared"], allow_creation=False
        )
        if document is None:
            raise MessageError("Error", "Please load/create a document before loading peaklist")

        document_title = document.title
        peaklist = self.data_handling.on_load_user_list_fcn(data_type="peaklist")

        for add_dict in peaklist:
            add_dict["document"] = document_title
            self.on_add_to_table(add_dict, check_color=False)
        self.peaklist.on_remove_duplicates()
        self.view.on_toggle_panel(evt=ID_window_ionList, check=True)

    def on_restore_to_peaklist(self, evt):
        document = self.data_handling._get_document_of_type(
            ["Type: MANUAL", "Type: ORIGAMI", "Type: Infrared"], allow_creation=False
        )
        if document is not None:
            self.data_handling._load_document_data_peaklist(document)

    def on_extract_all(self, evt):
        self.data_handling.on_extract_2D_from_mass_range_fcn(None, extract_type="all")

    def on_extract_selected(self, evt):
        self.data_handling.on_extract_2D_from_mass_range_fcn(None, extract_type="selected")

    def on_extract_new(self, evt):
        self.data_handling.on_extract_2D_from_mass_range_fcn(None, extract_type="new")
