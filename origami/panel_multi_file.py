"""Panel to load and combine multiple ML files"""
# Standard library imports
import logging
from os.path import splitext

# Third-party imports
import wx
import numpy as np

# Local imports
from origami.ids import ID_mmlPanel_plot_DT
from origami.ids import ID_mmlPanel_plot_MS
from origami.ids import ID_mmlPanel_check_all
from origami.ids import ID_mmlPanel_clear_all
from origami.ids import ID_mmlPanel_overlayMW
from origami.ids import ID_mmlPanel_delete_all
from origami.ids import ID_mmlPanel_preprocess
from origami.ids import ID_mmlPanel_showLegend
from origami.ids import ID_mmlPanel_assignColor
from origami.ids import ID_mmlPanel_add_manualDoc
from origami.ids import ID_mmlPanel_addToDocument
from origami.ids import ID_mmlPanel_batchRunUniDec
from origami.ids import ID_mmlPanel_check_selected
from origami.ids import ID_mmlPanel_clear_selected
from origami.ids import ID_mmlPanel_data_combineMS
from origami.ids import ID_mmlPanel_delete_selected
from origami.ids import ID_mmlPanel_overlayWaterfall
from origami.ids import ID_mmlPanel_plot_combined_MS
from origami.ids import ID_mmlPanel_delete_rightClick
from origami.ids import ID_mmlPanel_overlayFoundPeaks
from origami.ids import ID_mmlPanel_add_files_toNewDoc
from origami.ids import ID_mmlPanel_overlayChargeStates
from origami.ids import ID_mmlPanel_overlayFittedSpectra
from origami.ids import ID_mmlPanel_add_files_toCurrentDoc
from origami.ids import ID_mmlPanel_changeColorBatch_color
from origami.ids import ID_mmlPanel_overlayProcessedSpectra
from origami.ids import ID_mmlPanel_changeColorBatch_palette
from origami.ids import ID_mmlPanel_changeColorBatch_colormap
from origami.styles import make_tooltip
from origami.styles import make_menu_item
from origami.utils.color import get_font_color
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.color import convert_rgb_255_to_1
from origami.config.config import CONFIG
from origami.config.environment import ENV
from origami.processing.spectra import interpolate
from origami.gui_elements.panel_base import PanelBase
from origami.gui_elements.misc_dialogs import DialogBox
from origami.gui_elements.panel_modify_manual_settings import PanelModifyManualFilesSettings

logger = logging.getLogger(__name__)
# TODO: Move opening files to new function and check if files are on a network drive (process locally maybe?)
# TODO: create new import panel where user can select a directory with folders and then all *.raw files will be listed
# with some associated metadata


class PanelMultiFile(PanelBase):
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
            "name": "filename",
            "tag": "filename",
            "type": "str",
            "order": 1,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 200,
        },
        2: {
            "name": "variable",
            "tag": "energy",
            "type": "float",
            "order": 2,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 50,
        },
        3: {
            "name": "document",
            "tag": "document",
            "type": "str",
            "order": 3,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 80,
        },
        4: {
            "name": "label",
            "tag": "label",
            "type": "str",
            "order": 4,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 100,
        },
        5: {
            "name": "color",
            "tag": "color",
            "type": "color",
            "order": 5,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 0,
            "hidden": True,
        },
    }

    def __init__(self, parent, icons, presenter):
        PanelBase.__init__(self, parent, icons, presenter)
        self.editingItem = None
        self.allChecked = True
        self.preprocessMS = False
        self.showLegend = True
        self.addToDocument = False
        self.reverse = False
        self.lastColumn = None

        file_drop_target = DragAndDrop(self)
        self.SetDropTarget(file_drop_target)

        # add a couple of accelerators
        accelerators = [
            (wx.ACCEL_NORMAL, ord("A"), ID_mmlPanel_addToDocument),
            (wx.ACCEL_NORMAL, ord("C"), ID_mmlPanel_assignColor),
            (wx.ACCEL_NORMAL, ord("D"), ID_mmlPanel_plot_DT),
            (wx.ACCEL_NORMAL, ord("M"), ID_mmlPanel_plot_MS),
            (wx.ACCEL_NORMAL, ord("X"), ID_mmlPanel_check_all),
            (wx.ACCEL_NORMAL, ord("S"), ID_mmlPanel_check_selected),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, ID_mmlPanel_delete_rightClick),
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))

        wx.EVT_MENU(self, ID_mmlPanel_assignColor, self.on_assign_color)
        wx.EVT_MENU(self, ID_mmlPanel_plot_MS, self.on_plot_MS)
        wx.EVT_MENU(self, ID_mmlPanel_plot_DT, self.on_plot_1D)
        wx.EVT_MENU(self, ID_mmlPanel_check_selected, self.on_check_selected)
        wx.EVT_MENU(self, ID_mmlPanel_delete_rightClick, self.on_delete_item)
        wx.EVT_MENU(self, ID_mmlPanel_addToDocument, self.on_check_tool)

    def setup_handling_and_processing(self):
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling

    def on_open_info_panel(self, evt):
        pass

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

        process_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["process16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        process_btn.SetToolTip(make_tooltip("Process..."))

        overlay_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["overlay16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        overlay_btn.SetToolTip(make_tooltip("Visualise mass spectra..."))

        vertical_line_1 = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)

        info_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["info16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        info_btn.SetToolTip(make_tooltip("Information..."))

        # bind events
        self.Bind(wx.EVT_BUTTON, self.menu_add_tools, add_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_remove_tools, remove_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_process_tools, process_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_overlay_tools, overlay_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_annotate_tools, annotate_btn)
        self.Bind(wx.EVT_BUTTON, self.on_open_info_panel, info_btn)

        # button grid
        toolbar = wx.BoxSizer(wx.HORIZONTAL)
        toolbar.Add(add_btn, 0, wx.ALIGN_CENTER)
        toolbar.Add(remove_btn, 0, wx.ALIGN_CENTER)
        toolbar.Add(annotate_btn, 0, wx.ALIGN_CENTER)
        toolbar.Add(process_btn, 0, wx.ALIGN_CENTER)
        toolbar.Add(overlay_btn, 0, wx.ALIGN_CENTER)
        toolbar.AddSpacer(5)
        toolbar.Add(vertical_line_1, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        toolbar.AddSpacer(5)
        toolbar.Add(info_btn, 0, wx.ALIGN_CENTER)

        return toolbar

    def on_double_click_on_item(self, evt):
        if self.peaklist.item_id != -1:
            self.on_open_editor(evt=None)

    def on_menu_item_right_click(self, evt):

        self.Bind(wx.EVT_MENU, self.on_plot_MS, id=ID_mmlPanel_plot_MS)
        self.Bind(wx.EVT_MENU, self.on_plot_1D, id=ID_mmlPanel_plot_DT)
        self.Bind(wx.EVT_MENU, self.on_delete_item, id=ID_mmlPanel_delete_rightClick)
        self.Bind(wx.EVT_MENU, self.on_assign_color, id=ID_mmlPanel_assignColor)
        self.Bind(wx.EVT_MENU, self.on_plot_MS, id=ID_mmlPanel_plot_combined_MS)

        # Capture which item was clicked
        self.peaklist.item_id = evt.GetIndex()
        # Create popup menu
        menu = wx.Menu()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_mmlPanel_plot_MS,
                text="Show mass spectrum\tM",
                bitmap=self.icons.iconsLib["mass_spectrum_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_mmlPanel_plot_DT,
                text="Show mobilogram\tD",
                bitmap=self.icons.iconsLib["mobilogram_16"],
            )
        )
        menu.Append(ID_mmlPanel_plot_combined_MS, "Show mass spectrum (average)")
        menu.AppendSeparator()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_mmlPanel_assignColor,
                text="Assign new color\tC",
                bitmap=self.icons.iconsLib["color_panel_16"],
            )
        )
        menu.AppendSeparator()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_mmlPanel_delete_rightClick,
                text="Remove item\tDelete",
                bitmap=self.icons.iconsLib["bin16"],
            )
        )
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_annotate_tools(self, evt):
        self.Bind(wx.EVT_MENU, self.on_change_item_color_batch, id=ID_mmlPanel_changeColorBatch_color)
        self.Bind(wx.EVT_MENU, self.on_change_item_color_batch, id=ID_mmlPanel_changeColorBatch_palette)
        self.Bind(wx.EVT_MENU, self.on_change_item_color_batch, id=ID_mmlPanel_changeColorBatch_colormap)

        menu = wx.Menu()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_mmlPanel_changeColorBatch_color,
                text="Assign color for selected items",
                bitmap=self.icons.iconsLib["color_panel_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_mmlPanel_changeColorBatch_palette,
                text="Color selected items using color palette",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_mmlPanel_changeColorBatch_colormap,
                text="Color selected items using colormap",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_add_tools(self, evt):

        self.Bind(wx.EVT_TOOL, self.on_open_multiple_files_add, id=ID_mmlPanel_add_files_toCurrentDoc)
        self.Bind(wx.EVT_TOOL, self.on_open_multiple_files_new, id=ID_mmlPanel_add_files_toNewDoc)
        self.Bind(wx.EVT_TOOL, self.on_add_blank_document_manual, id=ID_mmlPanel_add_manualDoc)

        menu = wx.Menu()
        menu.Append(ID_mmlPanel_add_files_toCurrentDoc, "Add files to current MANUAL document")
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_mmlPanel_add_files_toNewDoc,
                text="Add files to blank MANUAL document",
                bitmap=self.icons.iconsLib["new_document_16"],
            )
        )
        menu.AppendSeparator()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_mmlPanel_add_manualDoc,
                text="Create blank MANUAL document",
                bitmap=self.icons.iconsLib["guide_16"],
            )
        )
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_remove_tools(self, evt):
        # Make bindings
        self.Bind(wx.EVT_MENU, self.peaklist.on_clear_table_all, id=ID_mmlPanel_clear_all)
        self.Bind(wx.EVT_MENU, self.peaklist.on_clear_table_selected, id=ID_mmlPanel_clear_selected)

        self.Bind(wx.EVT_MENU, self.on_delete_all, id=ID_mmlPanel_delete_all)
        self.Bind(wx.EVT_MENU, self.on_delete_selected, id=ID_mmlPanel_delete_selected)

        menu = wx.Menu()
        menu.Append(ID_mmlPanel_clear_selected, "Clear selected items")
        menu.AppendItem(
            make_menu_item(
                parent=menu, id=ID_mmlPanel_clear_all, text="Clear all items", bitmap=self.icons.iconsLib["clear_16"]
            )
        )
        menu.AppendSeparator()
        menu.Append(ID_mmlPanel_delete_selected, "Delete selected items")
        menu.Append(ID_mmlPanel_delete_all, "Delete all items")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_overlay_tools(self, evt):

        self.Bind(wx.EVT_TOOL, self.on_check_tool, id=ID_mmlPanel_preprocess)
        self.Bind(wx.EVT_TOOL, self.on_check_tool, id=ID_mmlPanel_addToDocument)
        self.Bind(wx.EVT_TOOL, self.on_check_tool, id=ID_mmlPanel_showLegend)
        self.Bind(wx.EVT_TOOL, self.on_overlay_plots, id=ID_mmlPanel_overlayWaterfall)
        self.Bind(wx.EVT_TOOL, self.on_overlay_plots, id=ID_mmlPanel_overlayChargeStates)
        self.Bind(wx.EVT_TOOL, self.on_overlay_plots, id=ID_mmlPanel_overlayMW)
        self.Bind(wx.EVT_TOOL, self.on_overlay_plots, id=ID_mmlPanel_overlayProcessedSpectra)
        self.Bind(wx.EVT_TOOL, self.on_overlay_plots, id=ID_mmlPanel_overlayFittedSpectra)
        self.Bind(wx.EVT_TOOL, self.on_overlay_plots, id=ID_mmlPanel_overlayFoundPeaks)

        menu = wx.Menu()
        self.showLegend_check = menu.AppendCheckItem(
            ID_mmlPanel_showLegend, "Show legend", help="Show legend on overlay plots"
        )
        self.showLegend_check.Check(self.showLegend)
        self.addToDocument_check = menu.AppendCheckItem(
            ID_mmlPanel_addToDocument,
            "Add overlay plots to document\tA",
            help="Add overlay results to comparison document",
        )
        self.addToDocument_check.Check(self.addToDocument)
        menu.AppendSeparator()
        self.preProcess_check = menu.AppendCheckItem(
            ID_mmlPanel_preprocess,
            "Pre-process mass spectra",
            help="Pre-process MS before generating waterfall plot (i.e. linearization, normalisation, smoothing, etc",
        )
        self.preProcess_check.Check(self.preprocessMS)
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_mmlPanel_overlayWaterfall,
                text="Overlay raw mass spectra",
                bitmap=self.icons.iconsLib["panel_waterfall_16"],
            )
        )
        menu.AppendSeparator()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_mmlPanel_overlayProcessedSpectra,
                text="Overlay processed spectra (UniDec)",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_mmlPanel_overlayFittedSpectra,
                text="Overlay fitted spectra (UniDec)",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_mmlPanel_overlayMW,
                text="Overlay molecular weight distribution (UniDec)",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_mmlPanel_overlayChargeStates,
                text="Overlay charge state distribution (UniDec)",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        #         menu.AppendItem(make_menu_item(parent=menu, id=ID_mmlPanel_overlayFoundPeaks,
        #                                      text='Overlay isolated species',
        #                                      bitmap=self.icons.iconsLib['blank_16']))

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_process_tools(self, evt):
        self.Bind(wx.EVT_TOOL, self.on_combine_mass_spectra, id=ID_mmlPanel_data_combineMS)
        self.Bind(wx.EVT_TOOL, self.onAutoUniDec, id=ID_mmlPanel_batchRunUniDec)

        menu = wx.Menu()
        menu.Append(ID_mmlPanel_data_combineMS, "Average mass spectra (current document)")
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_mmlPanel_batchRunUniDec,
                text="Run UniDec for selected items",
                bitmap=self.icons.iconsLib["process_unidec_16"],
            )
        )
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_check_tool(self, evt):
        evtID = evt.GetId()

        if evtID == ID_mmlPanel_preprocess:
            self.preprocessMS = self.preProcess_check.IsChecked()
            self.preProcess_check.Check(self.preprocessMS)
        elif evtID == ID_mmlPanel_showLegend:
            self.showLegend = self.showLegend_check.IsChecked()
            self.showLegend_check.Check(self.showLegend)
        elif evtID == ID_mmlPanel_addToDocument:
            self.addToDocument = self.addToDocument_check.IsChecked()
            self.addToDocument_check.Check(self.addToDocument)

    def _updateTable(self):
        self.on_update_document(itemID=self.editingItem)

    def on_change_item_color_batch(self, evt):
        # get number of checked items
        check_count = 0
        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(index=row):
                check_count += 1

        if evt.GetId() == ID_mmlPanel_changeColorBatch_palette:
            colors = self.presenter.view.panelPlots.on_change_color_palette(
                None, n_colors=check_count, return_colors=True
            )
        elif evt.GetId() == ID_mmlPanel_changeColorBatch_color:
            color = self.on_get_color(None)
            colors = [color] * check_count
        else:
            colors = self.presenter.view.panelPlots.on_get_colors_from_colormap(n_colors=check_count)

        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(index=row):
                color = colors[row]
                self.peaklist.SetItemBackgroundColour(row, convert_rgb_1_to_255(color))
                self.peaklist.SetItemTextColour(row, get_font_color(convert_rgb_1_to_255(color), return_rgb=True))

    def onAutoUniDec(self, evt):

        for row in range(self.peaklist.GetItemCount()):
            if not self.peaklist.IsChecked(index=row):
                continue
            itemInfo = self.on_get_item_information(row)

            # get mass spectrum information
            document = ENV[itemInfo["document"]]
            dataset = itemInfo["filename"]
            self.data_processing.on_run_unidec(dataset, task="auto_unidec")

            print(
                "Pre-processing mass spectra using m/z range {} - {} with {} bin size".format(
                    CONFIG.unidec_mzStart, CONFIG.unidec_mzEnd, CONFIG.unidec_mzBinSize
                )
            )

    def onRenameItem(self, old_name, new_name, item_type="Document"):
        for row in range(self.peaklist.GetItemCount()):
            itemInfo = self.on_get_item_information(row)
            if item_type == "document":
                if itemInfo["document"] == old_name:
                    self.peaklist.SetStringItem(index=row, col=CONFIG.multipleMLColNames["document"], label=new_name)
            elif item_type == "filename":
                if itemInfo["filename"] == old_name:
                    self.peaklist.SetStringItem(index=row, col=CONFIG.multipleMLColNames["filename"], label=new_name)

    def on_open_file_from_dnd(self, pathlist):
        self.data_handling.on_open_multiple_ML_files_fcn(open_type="multiple_files_add", pathlist=pathlist)

    def on_plot_MS(self, evt):
        """
        Function to plot selected MS in the mainWindow
        """

        itemInfo = self.on_get_item_information(self.peaklist.item_id)
        document = ENV[itemInfo["document"]]
        if document is None:
            return

        if evt.GetId() == ID_mmlPanel_plot_MS:
            itemName = itemInfo["filename"]
            try:
                msX = document.multipleMassSpectrum[itemName]["xvals"]
                msY = document.multipleMassSpectrum[itemName]["yvals"]
            except KeyError:
                return
            parameters = document.multipleMassSpectrum[itemName].get(
                "parameters", {"startMS": np.min(msX), "endMS": np.max(msX)}
            )
            xlimits = [parameters["startMS"], parameters["endMS"]]
            name_kwargs = {"document": itemInfo["document"], "dataset": itemName}

        elif evt.GetId() == ID_mmlPanel_plot_combined_MS:
            try:
                msX = document.massSpectrum["xvals"]
                msY = document.massSpectrum["yvals"]
                xlimits = document.massSpectrum["xlimits"]
                name_kwargs = {"document": itemInfo["document"], "dataset": "Mass Spectrum"}
            except KeyError:
                DialogBox(
                    exceptionTitle="Error", exceptionMsg="Document does not have averaged mass spectrum", type="Error"
                )
                return

        # Plot data
        self.presenter.view.panelPlots.on_plot_MS(
            msX, msY, xlimits=xlimits, full_repaint=True, set_page=True, **name_kwargs
        )

    def on_plot_1D(self, evt):
        """
        Function to plot selected 1DT in the mainWindow
        """
        itemInfo = self.on_get_item_information(self.peaklist.item_id)
        document = ENV[itemInfo["document"]]

        if document is None:
            return
        try:
            itemName = itemInfo["filename"]
            dtX = document.multipleMassSpectrum[itemName]["ims1DX"]
            dtY = document.multipleMassSpectrum[itemName]["ims1D"]
            xlabel = document.multipleMassSpectrum[itemName]["xlabel"]

            self.presenter.view.panelPlots.on_plot_1D(dtX, dtY, xlabel, full_repaint=True, set_page=True)
        except KeyError:
            DialogBox(exceptionTitle="Error", exceptionMsg="No mobility data present for selected item", type="Error")
            return

    def on_update_document(self, itemInfo=None, itemID=None):
        """
        evt : wxPython event
            unused
        itemInfo : dictionary
            dictionary with information about item to annotate
        itemID : int
            number of the item to be annotated
        """

        # get item info
        if itemInfo is None:
            if itemID is None:
                itemInfo = self.on_get_item_information(self.peaklist.item_id)
            else:
                itemInfo = self.on_get_item_information(itemID)

        # get item
        document = self.data_handling.on_get_document(itemInfo["document"])

        keywords = ["color", "energy", "label"]
        for keyword in keywords:
            keyword_name = self.__check_keyword(keyword)
            document.multipleMassSpectrum[itemInfo["filename"]][keyword_name] = itemInfo[keyword]

        self.data_handling.on_update_document(document, "no_refresh")

    def on_overlay_plots(self, evt):
        evtID = evt.GetId()

        _interpolate = True
        show_legend = self.showLegend_check.IsChecked()
        names, colors, xvals_list, yvals_list = [], [], [], []
        for row in range(self.peaklist.GetItemCount()):
            if not self.peaklist.IsChecked(index=row):
                continue
            itemInfo = self.on_get_item_information(row)
            names.append(itemInfo["label"])
            # get mass spectrum information
            document = ENV[itemInfo["document"]]
            data = document.multipleMassSpectrum[itemInfo["filename"]]

            # check if unidec dataset is present
            if "unidec" not in data and evtID in [
                ID_mmlPanel_overlayMW,
                ID_mmlPanel_overlayProcessedSpectra,
                ID_mmlPanel_overlayFittedSpectra,
                ID_mmlPanel_overlayChargeStates,
                ID_mmlPanel_overlayFoundPeaks,
            ]:
                print(
                    "Selected item {} ({}) does not have UniDec results".format(
                        itemInfo["document"], itemInfo["filename"]
                    )
                )
                continue
            if evtID == ID_mmlPanel_overlayWaterfall:
                _interpolate = False
                xvals = document.multipleMassSpectrum[itemInfo["filename"]]["xvals"].copy()
                yvals = document.multipleMassSpectrum[itemInfo["filename"]]["yvals"].copy()
                if self.preprocessMS:
                    xvals, yvals = self.data_processing.on_process_MS(msX=xvals, msY=yvals, return_data=True)

            elif evtID == ID_mmlPanel_overlayMW:
                xvals = data["unidec"]["MW distribution"]["xvals"]
                yvals = data["unidec"]["MW distribution"]["yvals"]

            elif evtID == ID_mmlPanel_overlayProcessedSpectra:
                xvals = data["unidec"]["Processed"]["xvals"]
                yvals = data["unidec"]["Processed"]["yvals"]
            elif evtID == ID_mmlPanel_overlayFittedSpectra:
                xvals = data["unidec"]["Fitted"]["xvals"][0]
                yvals = data["unidec"]["Fitted"]["yvals"][1]
            elif evtID == ID_mmlPanel_overlayChargeStates:
                xvals = data["unidec"]["Charge information"][:, 0]
                yvals = data["unidec"]["Charge information"][:, 1]
            elif evtID == ID_mmlPanel_overlayFoundPeaks:
                data["unidec"]["m/z with isolated species"]
                xvals = []
                yvals = []

            xvals_list.append(xvals)
            yvals_list.append(yvals)
            colors.append(convert_rgb_255_to_1(itemInfo["color"]))

        if len(xvals_list) == 0:
            print("No data in selected items")
            return

        # check that lengths are correct
        if _interpolate:
            x_long = max(xvals_list, key=len)
            for i, xlist in enumerate(xvals_list):
                if len(xlist) < len(x_long):
                    xlist_new, ylist_new = interpolate(xvals_list[i], yvals_list[i], x_long)
                    xvals_list[i] = xlist_new
                    yvals_list[i] = ylist_new

        # sum mw
        if evtID == ID_mmlPanel_overlayMW:
            xvals_list.insert(0, np.average(xvals_list, axis=0))
            yvals_list.insert(0, np.average(yvals_list, axis=0))
            colors.insert(0, ((0, 0, 0)))
            names.insert(0, ("Average"))

        kwargs = {"show_y_labels": True, "labels": names, "add_legend": show_legend}
        if evtID == ID_mmlPanel_overlayWaterfall:
            overlay_type = "Waterfall (Raw)"
            xlabel, ylabel = "m/z", "Offset Intensity"
            self.presenter.view.panelPlots.on_plot_waterfall(
                xvals_list, yvals_list, None, colors=colors, xlabel=xlabel, ylabel=ylabel, **kwargs
            )
        if evtID == ID_mmlPanel_overlayMW:
            overlay_type = "Waterfall (Deconvoluted MW)"
            xlabel, ylabel = "Mass (Da)", "Offset Intensity"
            self.presenter.view.panelPlots.on_plot_waterfall(
                xvals_list, yvals_list, None, colors=colors, xlabel=xlabel, ylabel=ylabel, set_page=True, **kwargs
            )

        elif evtID == ID_mmlPanel_overlayProcessedSpectra:
            overlay_type = "Waterfall (Processed)"
            xlabel, ylabel = "m/z", "Offset Intensity"
            self.presenter.view.panelPlots.on_plot_waterfall(
                xvals_list, yvals_list, None, colors=colors, xlabel=xlabel, ylabel=ylabel, set_page=True, **kwargs
            )
        elif evtID == ID_mmlPanel_overlayFittedSpectra:
            overlay_type = "Waterfall (Fitted)"
            xlabel, ylabel = "m/z", "Offset Intensity"
            self.presenter.view.panelPlots.on_plot_waterfall(
                xvals_list, yvals_list, None, colors=colors, xlabel=xlabel, ylabel=ylabel, set_page=True, **kwargs
            )
        elif evtID == ID_mmlPanel_overlayChargeStates:
            overlay_type = "Waterfall (Charge states)"
            xlabel, ylabel = "Charge", "Intensity"
            kwargs = {"show_y_labels": True, "labels": names, "increment": 0.000001, "add_legend": show_legend}
            self.presenter.view.panelPlots.on_plot_waterfall(
                xvals_list, yvals_list, None, colors=colors, xlabel=xlabel, ylabel=ylabel, set_page=True, **kwargs
            )

        if self.addToDocument:
            self.on_add_overlay_data_to_document(xvals_list, yvals_list, colors, xlabel, ylabel, overlay_type, **kwargs)

    def on_add_overlay_data_to_document(self, xvals, yvals, colors, xlabel, ylabel, overlay_type, **kwargs):
        overlay_labels = ", ".join(kwargs["labels"])
        overlay_title = "{}: {}".format(overlay_type, overlay_labels)

        document = self.data_processing._get_document_of_type("Type: Comparison")
        if document is None:
            self.presenter.onThreading(None, ("No document was selected", 4), action="updateStatusbar")
            return
        document.gotOverlay = True
        document.IMS2DoverlayData[overlay_title] = {
            "xvals": xvals,
            "yvals": yvals,
            "xlabel": xlabel,
            "ylabel": ylabel,
            "colors": colors,
            "labels": kwargs["labels"],
            "waterfall_kwargs": kwargs,
        }

        # update document
        self.data_handling.on_update_document(document, expand_item="overlay", expand_item_title=overlay_title)

    def on_add_blank_document_manual(self, evt):
        self.presenter.onAddBlankDocument(evt=None, document_type="manual")

    def on_open_multiple_files_new(self, evt):
        self.data_handling.on_open_multiple_ML_files_fcn(open_type="multiple_files_new_document")

    def on_open_multiple_files_add(self, evt):
        self.data_handling.on_open_multiple_ML_files_fcn(open_type="multiple_files_add")

    def on_combine_mass_spectra(self, evt, document_name=None):
        self.data_handling.on_combine_mass_spectra(document_name=document_name)

    def _check_item_in_table(self, add_dict):
        count = self.peaklist.GetItemCount()
        for row in range(count):
            item_info = self.on_get_item_information(row)
            if add_dict["filename"] == item_info["filename"] and add_dict["document"] == item_info["document"]:
                return True

        return False

    def on_open_editor(self, evt):
        information = self.on_get_item_information(self.peaklist.item_id)

        dlg = PanelModifyManualFilesSettings(self, self.presenter, CONFIG, **information)
        dlg.Show()

    def on_update_value_in_peaklist(self, item_id, value_type, value):

        if value_type == "check":
            self.peaklist.CheckItem(item_id, value)
        elif value_type == "filename":
            self.peaklist.SetStringItem(item_id, CONFIG.multipleMLColNames["filename"], str(value))
        elif value_type == "energy":
            self.peaklist.SetStringItem(item_id, CONFIG.multipleMLColNames["energy"], str(value))
        elif value_type == "color":
            color_255, color_1, font_color = value
            self.peaklist.SetItemBackgroundColour(item_id, color_255)
            self.peaklist.SetItemTextColour(item_id, font_color)
        elif value_type == "color_text":
            self.peaklist.SetItemBackgroundColour(item_id, value)
            self.peaklist.SetItemTextColour(item_id, get_font_color(value, return_rgb=True))
        elif value_type == "label":
            self.peaklist.SetStringItem(item_id, CONFIG.multipleMLColNames["label"], str(value))
        elif value_type == "document":
            self.peaklist.SetStringItem(item_id, CONFIG.multipleMLColNames["filename"], str(value))

    @staticmethod
    def __check_keyword(keyword_name):
        if keyword_name == "energy":
            keyword_name = "trap"
        return keyword_name


class DragAndDrop(wx.FileDropTarget):

    # ----------------------------------------------------------------------
    def __init__(self, window):
        """Constructor"""
        wx.FileDropTarget.__init__(self)
        self.window = window

    # ----------------------------------------------------------------------

    def OnDropFiles(self, x, y, filenames):
        """
        When files are dropped, write where they were dropped and then
        the file paths themselves
        """
        pathlist = []
        for filename in filenames:

            __, file_extension = splitext(filename)
            if file_extension in [".raw"]:
                print("Added {} file to the list".format(filename))
                pathlist.append(filename)
            else:
                print("Dropped file {} is not supported".format(filename))

        if len(pathlist) > 0:
            self.window.on_open_file_from_dnd(pathlist)
