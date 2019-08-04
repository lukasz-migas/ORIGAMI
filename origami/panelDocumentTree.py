# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import gc
import logging
import os
import re
import threading
import time
from copy import deepcopy
from operator import itemgetter
from sys import platform

import numpy as np
import pandas as pd
import readers.io_mgf as io_mgf
import readers.io_mzid as io_mzid
import readers.io_mzml as io_mzml
import utils.labels as ut_labels
import wx
from gui_elements.dialog_ask_override import DialogAskOverride
from gui_elements.dialog_rename import DialogRenameObject
from gui_elements.dialog_select_dataset import DialogSelectDataset
from gui_elements.misc_dialogs import DialogBox
from gui_elements.misc_dialogs import DialogSimpleAsk
from ids import ID_assignChargeState
from ids import ID_docTree_action_open_extract
from ids import ID_docTree_action_open_extractDTMS
from ids import ID_docTree_action_open_origami_ms
from ids import ID_docTree_action_open_peak_picker
from ids import ID_docTree_add_2DT_to_interactive
from ids import ID_docTree_add_annotations
from ids import ID_docTree_add_comparison_to_interactive
from ids import ID_docTree_add_DT_to_interactive
from ids import ID_docTree_add_matrix_to_interactive
from ids import ID_docTree_add_MS_to_interactive
from ids import ID_docTree_add_mzIdentML
from ids import ID_docTree_add_other_to_interactive
from ids import ID_docTree_add_RT_to_interactive
from ids import ID_docTree_addInteractiveToTextTable
from ids import ID_docTree_addOneInteractiveToTextTable
from ids import ID_docTree_addOneToMMLTable
from ids import ID_docTree_addOneToTextTable
from ids import ID_docTree_addToMMLTable
from ids import ID_docTree_addToTextTable
from ids import ID_docTree_compareMS
from ids import ID_docTree_duplicate_annotations
from ids import ID_docTree_duplicate_document
from ids import ID_docTree_plugin_UVPD
from ids import ID_docTree_process2D
from ids import ID_docTree_process2D_all
from ids import ID_docTree_processMS
from ids import ID_docTree_processMS_all
from ids import ID_docTree_save_unidec
from ids import ID_docTree_show_annotations
from ids import ID_docTree_show_refresh_document
from ids import ID_docTree_show_unidec
from ids import ID_docTree_showMassSpectra
from ids import ID_docTree_UniDec
from ids import ID_duplicateItem
from ids import ID_getSelectedDocument
from ids import ID_goToDirectory
from ids import ID_openDocInfo
from ids import ID_process2DDocument
from ids import ID_removeAllDocuments
from ids import ID_removeDocument
from ids import ID_removeItemDocument
from ids import ID_renameItem
from ids import ID_restoreComparisonData
from ids import ID_save1DImageDoc
from ids import ID_save2DImageDoc
from ids import ID_save3DImageDoc
from ids import ID_saveAllDocuments
from ids import ID_saveAsDataCSVDocument
from ids import ID_saveAsDataCSVDocument1D
from ids import ID_saveAsInteractive
from ids import ID_saveData_csv
from ids import ID_saveData_excel
from ids import ID_saveData_hdf
from ids import ID_saveData_pickle
from ids import ID_saveDataCSVDocument
from ids import ID_saveDataCSVDocument1D
from ids import ID_saveDocument
from ids import ID_saveMSImage
from ids import ID_saveMSImageDoc
from ids import ID_saveMZDTImage
from ids import ID_saveMZDTImageDoc
from ids import ID_saveOtherImageDoc
from ids import ID_saveOverlayImageDoc
from ids import ID_saveRMSDImageDoc
from ids import ID_saveRMSDmatrixImageDoc
from ids import ID_saveRMSFImageDoc
from ids import ID_saveRTImageDoc
from ids import ID_saveWaterfallImageDoc
from ids import ID_showPlot1DDocument
from ids import ID_showPlotDocument
from ids import ID_showPlotDocument_violin
from ids import ID_showPlotDocument_waterfall
from ids import ID_showPlotMSDocument
from ids import ID_showPlotRTDocument
from ids import ID_showSampleInfo
from ids import ID_window_multipleMLList
from ids import ID_window_textList
from ids import ID_xlabel_1D_bins
from ids import ID_xlabel_1D_ccs
from ids import ID_xlabel_1D_ms
from ids import ID_xlabel_1D_ms_arrival
from ids import ID_xlabel_1D_restore
from ids import ID_xlabel_2D_actLabFrame
from ids import ID_xlabel_2D_actVolt
from ids import ID_xlabel_2D_ccs
from ids import ID_xlabel_2D_charge
from ids import ID_xlabel_2D_colVolt
from ids import ID_xlabel_2D_custom
from ids import ID_xlabel_2D_labFrame
from ids import ID_xlabel_2D_massToCharge
from ids import ID_xlabel_2D_mz
from ids import ID_xlabel_2D_restore
from ids import ID_xlabel_2D_retTime_min
from ids import ID_xlabel_2D_scans
from ids import ID_xlabel_2D_time_min
from ids import ID_xlabel_2D_wavenumber
from ids import ID_xlabel_RT_restore
from ids import ID_xlabel_RT_retTime_min
from ids import ID_xlabel_RT_scans
from ids import ID_xlabel_RT_time_min
from ids import ID_ylabel_2D_bins
from ids import ID_ylabel_2D_ccs
from ids import ID_ylabel_2D_custom
from ids import ID_ylabel_2D_ms
from ids import ID_ylabel_2D_ms_arrival
from ids import ID_ylabel_2D_restore
from ids import ID_ylabel_DTMS_bins
from ids import ID_ylabel_DTMS_ms
from ids import ID_ylabel_DTMS_ms_arrival
from ids import ID_ylabel_DTMS_restore
from natsort import natsorted
from panelInformation import panelDocumentInfo
from readers.io_text_files import text_heatmap_open
from styles import makeMenuItem
from toolbox import merge_two_dicts
from toolbox import saveAsText
from utils.color import convertHEXtoRGB1
from utils.color import convertRGB1to255
from utils.color import convertRGB255to1
from utils.color import determineFontColor
from utils.converters import byte2str
from utils.converters import str2int
from utils.converters import str2num
from utils.exceptions import MessageError
from utils.labels import _replace_labels
from utils.path import clean_filename
from utils.random import get_random_int

# enable on windowsOS only
if platform == "win32":
    import readers.io_thermo_raw as io_thermo

logger = logging.getLogger("origami")


class panelDocuments(wx.Panel):
    """
    Make documents panel to store all information about open files
    """

    def __init__(self, parent, config, icons, presenter):
        wx.Panel.__init__(
            self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.Size(250, -1), style=wx.TAB_TRAVERSAL
        )

        self.parent = parent
        self.config = config
        self.presenter = presenter
        self.icons = icons

        self.makeTreeCtrl()

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.documents, 1, wx.EXPAND, 0)
        self.sizer.Fit(self)
        self.SetSizer(self.sizer)

    def __del__(self):
        pass

    def makeTreeCtrl(self):
        self.documents = documentsTree(self, self.parent, self.presenter, self.icons, self.config, size=(-1, -1))


class documentsTree(wx.TreeCtrl):
    """
    Documents tree
    """

    def __init__(
        self,
        parent,
        mainParent,
        presenter,
        icons,
        config,
        size=(-1, -1),
        style=wx.TR_TWIST_BUTTONS | wx.TR_HAS_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT,
    ):
        wx.TreeCtrl.__init__(self, parent, size=size, style=style)

        self.parent = parent
        self.view = mainParent
        self.presenter = presenter
        self.icons = icons
        self.config = config

        self._document_data = None  # itemData
        self._item_id = None  # currentItem
        self._indent = None  # indent
        self._document_type = None  # itemType
        self._item_leaf = None  # extractData
        self._item_branch = None  # extractParent
        self._item_root = None  # extractGrandparent

        self.annotateDlg = None

        # set font and colour
        self.SetFont(wx.SMALL_FONT)

        # init bullets
        self.bullets = wx.ImageList(13, 12)
        self.SetImageList(self.bullets)
        self.reset_document_tree_bullets()

        # add root
        root = self.AddRoot("Documents")
        self.SetItemImage(root, 0, wx.TreeItemIcon_Normal)

        # Add bindings
        self.Bind(wx.EVT_TREE_KEY_DOWN, self.on_keyboard_event, id=wx.ID_ANY)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_enable_document, id=wx.ID_ANY)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_enable_document, id=wx.ID_ANY)
        self.Bind(wx.EVT_TREE_ITEM_MENU, self.on_right_click, id=wx.ID_ANY)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click)

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_enable_document, id=wx.ID_ANY)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onItemSelection, id=wx.ID_ANY)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_keyboard_event, id=wx.ID_ANY)

        if self.config.quickDisplay:
            self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onChangePlot, id=wx.ID_ANY)

    def _setup_handling_and_processing(self):
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling

        self.panel_plot = self.view.panelPlots

        self.ionPanel = self.view.panelMultipleIons
        self.ionList = self.ionPanel.peaklist

        self.textPanel = self.view.panelMultipleText
        self.textList = self.textPanel.peaklist

        self.filesPanel = self.view.panelMML
        self.filesList = self.filesPanel.peaklist

    def on_keyboard_event(self, evt):
        """ Shortcut to navigate through Document Tree """
        key = evt.GetKeyCode()
        # detelete item
        if key == 127:
            item = self.GetSelection()
            indent = self.get_item_indent(item)
            if indent == 0:
                self.on_delete_all_documents(evt=None)
            else:
                self.on_delete_item(evt=None)
        elif key == 80:
            if self._document_type in ["Drift time (2D)", "Drift time (2D, processed)"]:
                self.on_process_2D(evt=None)
            elif self._document_type in [
                "Drift time (2D, EIC)",
                "Drift time (2D, combined voltages, EIC)",
                "Drift time (2D, processed, EIC)",
                "Input data",
                "Statistical",
            ] and self._item_leaf not in [
                "Drift time (2D, EIC)",
                "Drift time (2D, combined voltages, EIC)",
                "Drift time (2D, processed, EIC)",
                "Input data",
                "Statistical",
            ]:
                self.on_process_2D(evt=None)
            elif (
                self._document_type in ["Mass Spectrum", "Mass Spectrum (processed)", "Mass Spectra"]
                and self._item_leaf != "Mass Spectra"
            ):
                self.on_process_MS(evt=None)
        elif key == 341:  # F2
            self.onRenameItem(None)

    def on_double_click(self, evt):

        tstart = time.clock()
        # Get selected item
        item = self.GetSelection()
        self._item_id = item

        # Get the current text value for selected item
        itemType = self.GetItemText(item)
        if itemType == "Documents":
            menu = wx.Menu()
            menu.AppendItem(
                makeMenuItem(
                    parent=menu,
                    id=ID_saveAllDocuments,
                    text="Save all documents",
                    bitmap=self.icons.iconsLib["save_multiple_16"],
                )
            )
            menu.AppendItem(
                makeMenuItem(
                    parent=menu,
                    id=ID_removeAllDocuments,
                    text="Delete all documents",
                    bitmap=self.icons.iconsLib["bin16"],
                )
            )
            self.PopupMenu(menu)
            menu.Destroy()
            self.SetFocus()
            return

        # Get indent level for selected item
        self._indent = self.get_item_indent(item)
        if self._indent > 1:
            extract = item  # Specific Ion/file name
            item = self.getParentItem(item, 2)  # Item type
            itemType = self.GetItemText(item)
        else:
            extract = None

        # split
        try:
            self.splitText = re.split(r"-|,|:|__| \(", self._item_leaf)
        except Exception:
            self.splitText = []
        # Get the ion/file name from deeper indent
        if extract is None:
            self._item_leaf = None
            self._item_branch = None
            self._item_root = None
        else:
            self._item_leaf = self.GetItemText(extract)
            self._item_branch = self.GetItemText(self.GetItemParent(extract))
            self._item_root = self.GetItemText(self.GetItemParent(self.GetItemParent(extract)))

        self.title = self._document_data.title

        if self._indent == 1 and self._item_leaf is None:
            self.on_refresh_document()
        elif self._document_type == "Mass Spectra" and self._item_leaf == "Mass Spectra":
            self.onCompareMS(evt=None)
        elif self._document_type in ["Mass Spectrum", "Mass Spectrum (processed)", "Mass Spectra"]:
            if (
                self._item_leaf in ["Mass Spectrum", "Mass Spectrum (processed)", "Mass Spectra"]
                or self._item_branch == "Mass Spectra"
            ):
                self.on_show_plot(evt=ID_showPlotDocument)
            elif self._item_leaf == "UniDec":
                self.on_open_UniDec(None)
            elif self._item_branch == "UniDec":
                self.on_open_UniDec(None)
            elif self._item_leaf == "Annotations":
                self.on_add_annotation(None)
        elif self._document_type in [
            "Chromatogram",
            "Chromatograms (EIC)",
            "Annotated data",
            "Drift time (1D)",
            "Drift time (1D, EIC, DT-IMS)",
            "Drift time (1D, EIC)",
            "Chromatograms (combined voltages, EIC)",
            "Drift time (2D)",
            "Drift time (2D, processed)",
            "Drift time (2D, EIC)",
            "Drift time (2D, combined voltages, EIC)",
            "Drift time (2D, processed, EIC)",
            "Input data",
            "Statistical",
            "Overlay",
            "DT/MS",
            "Tandem Mass Spectra",
        ]:
            self.on_show_plot(evt=None)
        elif self._document_type == "Sample information":
            self.onShowSampleInfo(evt=None)
        elif self._indent == 1:
            self.onOpenDocInfo(evt=None)

        tend = time.clock()
        print("It took: %s seconds to process double-click." % str(np.round((tend - tstart), 4)))

    def onThreading(self, evt, args, action):
        if action == "add_mzidentml_annotations":
            th = threading.Thread(target=self.on_add_mzID_file, args=(evt,))
        elif action == "load_mgf":
            th = threading.Thread(target=self.on_open_MGF_file, args=(evt,))
        elif action == "load_mzML":
            th = threading.Thread(target=self.on_open_mzML_file, args=(evt,))
        elif action == "load_thermo_RAW":
            th = threading.Thread(target=self.on_open_thermo_file, args=(evt,))

        # Start thread
        try:
            th.start()
        except Exception:
            print("Failed to execute the '{}' operation in threaded mode. Consider switching it off?".format(action))

    def toggle_quick_display(self, evt):
        """
        Function to either allow or disallow quick plotting selection of datasets
        """

        if self.config.quickDisplay:
            self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onChangePlot, id=wx.ID_ANY)
        else:
            self.Unbind(wx.EVT_TREE_SEL_CHANGED, id=wx.ID_ANY)

        if evt is not None:
            evt.Skip()

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

        self.bulets_dict = {
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

    def on_save_as_document(self, evt):
        """
        Save current document. With asking for path.
        """
        document_title = self._document_data.title
        self.data_handling.on_save_document_fcn(document_title)

    def on_save_document(self, evt):
        """
        Save current document. Without asking for path.
        """
        if self._document_data is not None:
            document_title = self._document_data.title
            wx.CallAfter(self.data_handling.on_save_document_fcn, document_title, save_as=False)

    def on_refresh_document(self, evt=None):
        document = self.presenter.documentsDict.get(self.title, None)
        if document is None:
            return

        # set what to plot
        mass_spectrum, chromatogram, mobiligram, heatmap = False, False, False, False
        # check document
        if document.dataType == "Type: ORIGAMI":
            mass_spectrum, chromatogram, mobiligram, heatmap = True, True, True, True
            go_to_page = self.config.panelNames["MS"]
        elif document.dataType == "Type: MANUAL":
            mass_spectrum = True
            go_to_page = self.config.panelNames["MS"]
        elif document.dataType == "Type: Multifield Linear DT":
            mass_spectrum, chromatogram, mobiligram, heatmap = True, True, True, True
            go_to_page = self.config.panelNames["MS"]
        elif document.dataType == "Type: 2D IM-MS":
            heatmap = True
            go_to_page = self.config.panelNames["2D"]
        else:
            return

        # clear all plots
        self.panel_plot.on_clear_all_plots()

        if mass_spectrum:
            try:
                msX = document.massSpectrum["xvals"]
                msY = document.massSpectrum["yvals"]
                try:
                    xlimits = document.massSpectrum["xlimits"]
                except KeyError:
                    xlimits = [document.parameters["startMS"], document.parameters["endMS"]]
                name_kwargs = {"document": document.title, "dataset": "Mass Spectrum"}
                self.panel_plot.on_plot_MS(msX, msY, xlimits=xlimits, set_page=False, **name_kwargs)
            except Exception:
                pass

        if chromatogram:
            try:
                rtX = document.RT["xvals"]
                rtY = document.RT["yvals"]
                xlabel = document.RT["xlabels"]
                self.panel_plot.on_plot_RT(rtX, rtY, xlabel, set_page=False)
            except Exception:
                pass

        if mobiligram:
            try:
                dtX = document.DT["xvals"]
                dtY = document.DT["yvals"]
                if len(dtY) >= 1:
                    try:
                        dtY = document.DT["yvalsSum"]
                    except KeyError:
                        pass
                xlabel = document.DT["xlabels"]
                self.panel_plot.on_plot_1D(dtX, dtY, xlabel, set_page=False)
            except Exception:
                pass

        if heatmap:
            try:
                zvals = document.IMS2D["zvals"]
                xvals = document.IMS2D["xvals"]
                yvals = document.IMS2D["yvals"]
                xlabel = document.IMS2D["xlabels"]
                ylabel = document.IMS2D["ylabels"]
                self.panel_plot.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, override=True)
            except Exception:
                pass

        # go to page
        self.panel_plot._set_page(go_to_page)

    def on_check_xlabels_RT(self):
        """Check label of the chromatogram dataset"""

        data = self.GetPyData(self._item_id)
        xlabel = data["xlabels"]

        xlabel_evt_dict = {
            "Scans": ID_xlabel_RT_scans,
            "Time (min)": ID_xlabel_RT_time_min,
            "Retention time (min)": ID_xlabel_RT_retTime_min,
        }

        return xlabel_evt_dict.get(xlabel, None)

    def on_check_xylabels_2D(self):
        """Check label of the 2D datasets"""

        xlabel_evt_dict = {
            "Scans": ID_xlabel_2D_scans,
            "Time (min)": ID_xlabel_2D_time_min,
            "Retention time (min)": ID_xlabel_2D_retTime_min,
            "Collision Voltage (V)": ID_xlabel_2D_colVolt,
            "Activation Voltage (V)": ID_xlabel_2D_actVolt,
            "Lab Frame Energy (eV)": ID_xlabel_2D_labFrame,
            "Activation Energy (eV)": ID_xlabel_2D_actLabFrame,
            "Mass-to-charge (Da)": ID_xlabel_2D_massToCharge,
            "m/z (Da)": ID_xlabel_2D_mz,
            "Wavenumber (cm⁻¹)": ID_xlabel_2D_wavenumber,
            "Charge": ID_xlabel_2D_charge,
            "Collision Cross Section (Å²)": ID_xlabel_2D_ccs,
        }

        ylabel_evt_dict = {
            "Drift time (bins)": ID_ylabel_2D_bins,
            "Drift time (ms)": ID_ylabel_2D_ms,
            "Arrival time (ms)": ID_ylabel_2D_ms_arrival,
            "Collision Cross Section (Å²)": ID_ylabel_2D_ccs,
        }

        # Select dataset
        if self._document_type == "Drift time (2D)":
            data = self._document_data.IMS2D
        elif self._document_type == "Drift time (2D, processed)":
            data = self._document_data.IMS2Dprocess
        elif self._document_type == "Drift time (2D, EIC)":
            if self._item_leaf == "Drift time (2D, EIC)":
                return None, None
            data = self._document_data.IMS2Dions[self._item_leaf]
        elif self._document_type == "Drift time (2D, combined voltages, EIC)":
            if self._item_leaf == "Drift time (2D, combined voltages, EIC)":
                return None, None
            data = self._document_data.IMS2DCombIons[self._item_leaf]
        elif self._document_type == "Drift time (2D, processed, EIC)":
            if self._item_leaf == "Drift time (2D, processed, EIC)":
                return None, None
            data = self._document_data.IMS2DionsProcess[self._item_leaf]
        elif self._document_type == "Input data":
            if self._item_leaf == "Input data":
                return None, None
            data = self._document_data.IMS2DcompData[self._item_leaf]

        # Get labels
        xlabel = data.get("xlabels", None)
        ylabel = data.get("ylabels", None)

        return xlabel_evt_dict.get(xlabel, ID_xlabel_2D_custom), ylabel_evt_dict.get(ylabel, ID_ylabel_2D_custom)

    def on_check_xlabels_1D(self):
        """Check labels of the mobilogram dataset"""
        data = self.GetPyData(self._item_id)

        # Get labels
        xlabel = data["xlabels"]

        xlabel_evt_dict = {
            "Drift time (bins)": ID_xlabel_1D_bins,
            "Drift time (ms)": ID_xlabel_1D_ms,
            "Arrival time (ms)": ID_xlabel_1D_ms_arrival,
            "Collision Cross Section (Å²)": ID_xlabel_1D_ccs,
        }

        return xlabel_evt_dict.get(xlabel, ID_ylabel_2D_bins)

    def on_check_xlabels_DTMS(self):
        """Check labels of the DT/MS dataset"""
        if self._document_type == "DT/MS":
            data = self._document_data.DTMZ

        # Get labels
        ylabel = data["ylabels"]

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

        # Check that the user hasn't selected the header
        if self._document_type in [
            "Drift time (2D, EIC)",
            "Drift time (2D, combined voltages, EIC)",
            "Drift time (2D, processed, EIC)",
            "Input data",
        ] and self._item_leaf in [
            "Drift time (2D, EIC)",
            "Drift time (2D, combined voltages, EIC)",
            "Drift time (2D, processed, EIC)",
            "Input data",
        ]:
            raise MessageError("Incorrect data type", "Please select a single ion in the Document panel.\n\n\n")

        __, data, __ = self._on_event_get_mobility_chromatogram_data()
        current_charge = data.get("charge", None)

        charge = DialogSimpleAsk("Type in new charge state", defaultValue=str(current_charge))

        charge = str2int(charge)

        if charge in ["", "None", None]:
            logger.warning(f"The defined value `{charge}` is not correct")
            return

        query_info = self._on_event_get_mobility_chromatogram_query()
        document = self.data_handling.set_mobility_chromatographic_keyword_data(query_info, charge=charge)

        # update data in side panel
        self.ionPanel.on_find_and_update_values(query_info[2], charge=charge)

        # update document
        self.data_handling.on_update_document(document, "no_refresh")

    def _on_event_get_mass_spectrum(self, **kwargs):

        if "document_title" not in kwargs and "dataset_name" not in kwargs:
            document_title = self._document_data.title
            if self._document_type == "Mass Spectrum":
                dataset_name = "Mass Spectrum"
            elif self._document_type == "Mass Spectrum (processed)":
                dataset_name = "Mass Spectrum (processed)"
            elif self._document_type == "Mass Spectra":
                dataset_name = self._item_leaf
        else:
            document_title = kwargs.pop("document_name")
            dataset_name = kwargs.pop("dataset_name")

        # form query
        query = [document_title, dataset_name]
        # get dat and document
        document, data = self.data_handling.get_spectrum_data(query)

        return document, data, dataset_name

    def _on_event_get_mobility_chromatogram_query(self, **kwargs):
        if "document_title" not in kwargs and "dataset_type" not in kwargs and "dataset_name" not in kwargs:
            document_title = self._document_data.title
            dataset_name = None
            dataset_type = self._document_type
            if self._document_type in [
                "Drift time (2D, EIC)",
                "Drift time (2D, combined voltages, EIC)",
                "Drift time (2D, processed, EIC)",
                "Input data",
                "Chromatograms (combined voltages, EIC)",
                "Drift time (1D, EIC)",
                "Drift time (1D, EIC, DT-IMS)",
            ]:
                dataset_name = self._item_leaf
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

    def on_load_custom_data(self, evt):
        """
        Load data into interactive document
        """

        # get document
        document = self._document_data
        evtID = evt.GetId()
        wildcard = "Text file (*.txt, *.csv, *.tab)| *.txt;*.csv;*.tab"
        dlg = wx.FileDialog(
            self.presenter.view,
            "Choose data [MS, RT, DT]...",
            wildcard=wildcard,
            style=wx.FD_MULTIPLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            pathlist = dlg.GetPaths()
            filenames = dlg.GetFilenames()
            for path, fname in zip(pathlist, filenames):
                if evtID == ID_docTree_add_MS_to_interactive:
                    msDataX, msDataY, __, xlimits, extension = self.data_handling._get_text_spectrum_data(path=path)
                    document.gotMultipleMS = True
                    data = {
                        "xvals": msDataX,
                        "yvals": msDataY,
                        "xlabels": "m/z (Da)",
                        "xlimits": xlimits,
                        "file_path": path,
                        "file_extension": extension,
                    }

                    if fname in document.multipleMassSpectrum:
                        if not self.config.import_duplicate_ask:
                            msg = "{} already exists in the document. What would you like to do about it?".format(fname)
                            dlg = DialogAskOverride(self, self.config, msg)
                            dlg.ShowModal()
                        if self.config.import_duplicate_action == "merge":
                            # retrieve and merge
                            old_data = document.multipleMassSpectrum[fname]
                            data = merge_two_dicts(old_data, data)
                        elif self.config.import_duplicate_action == "duplicate":
                            title = "{} (2)".format(fname)

                    document.multipleMassSpectrum[fname] = data

                elif evtID == ID_docTree_add_RT_to_interactive:
                    rtDataX, rtDataY, __, xlimits, extension = self.data_handling._get_text_spectrum_data(path=path)
                    document.gotMultipleRT = True
                    data = {
                        "xvals": rtDataX,
                        "yvals": rtDataY,
                        "xlabels": "Scans",
                        "ylabels": "Intensity",
                        "xlimits": xlimits,
                        "file_path": path,
                        "file_extension": extension,
                    }

                    if fname in document.multipleRT:
                        if not self.config.import_duplicate_ask:
                            msg = "{} already exists in the document. What would you like to do about it?".format(fname)
                            dlg = DialogAskOverride(self, self.config, msg)
                            dlg.ShowModal()
                        if self.config.import_duplicate_action == "merge":
                            # retrieve and merge
                            old_data = document.multipleRT[fname]
                            data = merge_two_dicts(old_data, data)
                        elif self.config.import_duplicate_action == "duplicate":
                            title = "{} (2)".format(fname)

                    document.multipleRT[fname] = data

                elif evtID == ID_docTree_add_DT_to_interactive:
                    dtDataX, dtDataY, __, xlimits, extension = self.data_handling._get_text_spectrum_data(path=path)
                    data = {
                        "xvals": dtDataX,
                        "yvals": dtDataY,
                        "xlabels": "Drift time (bins)",
                        "ylabels": "Intensity",
                        "xlimits": xlimits,
                        "file_path": path,
                        "file_extension": extension,
                    }

                    if fname in document.multipleDT:
                        if not self.config.import_duplicate_ask:
                            msg = "{} already exists in the document. What would you like to do about it?".format(fname)
                            dlg = DialogAskOverride(self, self.config, msg)
                            dlg.ShowModal()
                        if self.config.import_duplicate_action == "merge":
                            # retrieve and merge
                            old_data = document.multipleDT[fname]
                            data = merge_two_dicts(old_data, data)
                        elif self.config.import_duplicate_action == "duplicate":
                            title = "{} (2)".format(fname)

                    document.multipleDT[fname] = data

                elif evtID == ID_docTree_add_2DT_to_interactive:
                    imsData2D, xAxisLabels, yAxisLabels = text_heatmap_open(path=path)
                    imsData1D = np.sum(imsData2D, axis=1).T
                    rtDataY = np.sum(imsData2D, axis=0)
                    color = convertRGB255to1(self.config.customColors[get_random_int(0, 15)])
                    document.gotExtractedIons = True
                    data = {
                        "zvals": imsData2D,
                        "xvals": xAxisLabels,
                        "xlabels": "Scans",
                        "yvals": yAxisLabels,
                        "ylabels": "Drift time (bins)",
                        "yvals1D": imsData1D,
                        "yvalsRT": rtDataY,
                        "cmap": self.config.currentCmap,
                        "mask": self.config.overlay_defaultMask,
                        "alpha": self.config.overlay_defaultAlpha,
                        "min_threshold": 0,
                        "max_threshold": 1,
                        "color": color,
                    }
                    if fname in document.IMS2Dions:
                        if not self.config.import_duplicate_ask:
                            msg = "{} already exists in the document. What would you like to do about it?".format(fname)
                            dlg = DialogAskOverride(self, self.config, msg)
                            dlg.ShowModal()
                        if self.config.import_duplicate_action == "merge":
                            # retrieve and merge
                            old_data = document.IMS2Dions[fname]
                            data = merge_two_dicts(old_data, data)
                        elif self.config.import_duplicate_action == "duplicate":
                            title = "{} (2)".format(fname)

                    document.IMS2Dions[fname] = data

                elif evtID == ID_docTree_add_other_to_interactive:
                    try:
                        title, data = self.onLoadOtherData(path)
                        if title is None or data is None:
                            return
                        if title in document.other_data:
                            if not self.config.import_duplicate_ask:
                                msg = "{} already exists in the document. What would you like to do about it?".format(
                                    title
                                )
                                dlg = DialogAskOverride(self, self.config, msg)
                                dlg.ShowModal()

                            if self.config.import_duplicate_action == "merge":
                                # retrieve and merge
                                old_data = document.other_data[title]
                                data = merge_two_dicts(old_data, data)
                            elif self.config.import_duplicate_action == "duplicate":
                                title = "{} (2)".format(title)

                        document.other_data[title] = data
                    except Exception as e:
                        print(e)
                        self.presenter.onThreading(
                            None, ("Failed to load data for: {}".format(path), 4, 5), action="updateStatusbar"
                        )

                elif evtID == ID_docTree_add_matrix_to_interactive:
                    df = pd.read_csv(fname, sep="\t|,", engine="python", header=None)
                    labels = list(df.iloc[:, 0].dropna())
                    zvals = df.iloc[1::, 1::].astype("float32").as_matrix()

                    title = "Matrix: {}".format(os.path.basename(fname))
                    data = {
                        "plot_type": "matrix",
                        "zvals": zvals,
                        "cmap": self.config.currentCmap,
                        "matrixLabels": labels,
                        "path": fname,
                        "plot_modifiers": {},
                    }
                    if title in document.other_data:
                        if not self.config.import_duplicate_ask:
                            msg = "{} already exists in the document. What would you like to do about it?".format(title)
                            dlg = DialogAskOverride(self, self.config, msg)
                            dlg.ShowModal()

                        if self.config.import_duplicate_action == "merge":
                            # retrieve and merge
                            old_data = document.other_data[title]
                            data = merge_two_dicts(old_data, data)
                        elif self.config.import_duplicate_action == "duplicate":
                            title = "{} (2)".format(title)

                    document.other_data[title] = data

                elif evtID == ID_docTree_add_comparison_to_interactive:
                    print("Load comparison")

        dlg.Destroy()

        self.data_handling.on_update_document(document, "document")

    def onLoadOtherData(self, fname):
        if fname.endswith(".csv"):
            df = pd.read_csv(fname, sep=",", engine="python", header=None)
        elif fname.endswith(".txt"):
            df = pd.read_csv(fname, sep="\t", engine="python", header=None)

        title = os.path.basename(fname)
        plot_type = "multi-line"
        plot_modifiers = {}
        if "title" in list(df.iloc[:, 0]):
            idx = list(df.iloc[:, 0]).index("title")
            title = list(df.iloc[idx, 1::])[0]

        row_labels = list(df.iloc[:, 0])
        if "plot_type" in row_labels:
            idx = row_labels.index("plot_type")
            plot_type = list(df.iloc[idx, 1::])[0]

        if "x_label" in row_labels:
            idx = row_labels.index("x_label")
            x_label = list(df.iloc[idx, 1::])[0]
        else:
            x_label = ""

        if "y_label" in row_labels:
            idx = row_labels.index("y_label")
            y_label = list(df.iloc[idx, 1::])[0]
        else:
            y_label = ""

        if "x_unit" in row_labels:
            idx = row_labels.index("x_unit")
            x_unit = list(df.iloc[idx, 1::])[0]
        else:
            x_unit = ""

        if "y_unit" in row_labels:
            idx = row_labels.index("y_unit")
            y_unit = list(df.iloc[idx, 1::])[0]
        else:
            y_unit = ""

        if "order" in row_labels:
            idx = row_labels.index("order")
            order = list(df.iloc[idx, 1::])
        else:
            order = []

        if "label" in row_labels:
            idx = row_labels.index("label")
            labels = list(df.iloc[idx, 1::].dropna())
        elif "labels" in row_labels:
            idx = row_labels.index("labels")
            labels = list(df.iloc[idx, 1::].dropna())
        else:
            labels = []

        if "x_labels" in row_labels:
            idx = row_labels.index("x_labels")
            x_labels = list(df.iloc[idx, 1::].dropna())
        else:
            x_labels = []

        if "y_labels" in row_labels:
            idx = row_labels.index("y_labels")
            y_labels = list(df.iloc[idx, 1::].dropna())
        else:
            y_labels = []

        if "xlimits" in row_labels:
            idx = row_labels.index("xlimits")
            xlimits = list(df.iloc[idx, 1:3].dropna().astype("float32"))
        else:
            xlimits = [None, None]

        if "ylimits" in row_labels:
            idx = row_labels.index("ylimits")
            ylimits = list(df.iloc[idx, 1:3].dropna().astype("float32"))
        else:
            ylimits = [None, None]

        if "color" in row_labels:
            idx = row_labels.index("color")
            colors = list(df.iloc[idx, 1::].dropna())
        elif "colors" in row_labels:
            idx = row_labels.index("colors")
            colors = list(df.iloc[idx, 1::].dropna())
        else:
            colors = []

        if "column_type" in row_labels:
            idx = row_labels.index("column_type")
            column_types = list(df.iloc[idx, 1::].dropna())
        else:
            column_types = []

        if "legend_labels" in row_labels:
            idx = row_labels.index("legend_labels")
            legend_labels = list(df.iloc[idx, 1::].dropna())
        else:
            legend_labels = []

        if "legend_colors" in row_labels:
            idx = row_labels.index("legend_colors")
            legend_colors = list(df.iloc[idx, 1::].dropna())
        else:
            legend_colors = []

        if "hover_labels" in row_labels:
            idx = row_labels.index("hover_labels")
            hover_labels = list(df.iloc[idx, 1::].dropna())
        else:
            hover_labels = []

        plot_modifiers.update(
            legend_labels=legend_labels, legend_colors=legend_colors, xlimits=xlimits, ylimits=ylimits
        )
        xvals, yvals, zvals, xvalsErr, yvalsErr, itemColors, itemLabels = [], [], [], [], [], [], []
        xyvals, urls = [], []
        axis_y_min, axis_y_max, axis_note = [], [], []
        xy_labels = []

        # get first index
        first_num_idx = pd.to_numeric(df.iloc[:, 0], errors="coerce").notnull().idxmax()

        # check if axis labels have been provided
        for xy_axis in [
            "axis_x",
            "axis_y",
            "axis_xerr",
            "axis_yerr",
            "axis_color",
            "axis_colors",
            "axis_label",
            "axis_labels",
            "axis_y_min",
            "axis_y_max",
            "axis_xy",
            "axis_url",
        ]:
            if xy_axis in row_labels:
                idx = row_labels.index(xy_axis)
                xy_labels = list(df.iloc[idx, :])

        if len(xy_labels) == df.shape[1]:
            df = df.iloc[first_num_idx:, :]  # [pd.to_numeric(df.iloc[:,0], errors='coerce').notnull()]
            for i, xy_label in enumerate(xy_labels):
                if xy_label == "axis_x":
                    xvals.append(np.asarray(df.iloc[:, i].dropna().astype("float32")))
                if xy_label == "axis_y":
                    yvals.append(np.asarray(df.iloc[:, i].dropna().astype("float32")))
                if xy_label == "axis_xerr":
                    xvalsErr.append(np.asarray(df.iloc[:, i].dropna().astype("float32")))
                if xy_label == "axis_yerr":
                    yvalsErr.append(np.asarray(df.iloc[:, i].dropna().astype("float32")))
                if xy_label == "axis_y_min":
                    axis_y_min.append(np.asarray(df.iloc[:, i].dropna().astype("float32")))
                if xy_label == "axis_y_max":
                    axis_y_max.append(np.asarray(df.iloc[:, i].dropna().astype("float32")))
                if xy_label in ["axis_xy", "axis_yx"]:
                    xyvals.append(np.asarray(df.iloc[:, i].dropna().astype("float32")))
                if xy_label in ["axis_color", "axis_colors"]:
                    _colors = list(df.iloc[:, i].dropna().astype("str"))
                    _colorsRGB = []
                    for _color in _colors:
                        _colorsRGB.append(convertHEXtoRGB1(str(_color)))
                    itemColors.append(_colorsRGB)
                    plot_modifiers["color_items"] = True
                if xy_label in ["axis_label", "axis_labels"]:
                    itemLabels.append(list(df.iloc[:, i].replace(np.nan, "", regex=True).astype("str")))
                    plot_modifiers["label_items"] = True
                if xy_label == "axis_note":
                    axis_note.append(np.asarray(df.iloc[:, i].replace(np.nan, "", regex=True).astype("str")))
                if xy_label == "axis_url":
                    urls.append(np.asarray(df.iloc[:, i].astype("str")))
        else:
            # drop all other non-numeric rows
            df = df[pd.to_numeric(df.iloc[:, 0], errors="coerce").notnull()]
            df = df.astype("float32")

            # extract x, y and zvals
            if df.shape[1] >= 2:
                xvals = list(df.iloc[:, 0])
            else:
                return None, None

            if df.shape[1] == 2:
                yvals = list(df.iloc[:, 1])

            if df.shape[1] > 2:
                zvals = df.iloc[:, 1::].as_matrix()

            if plot_type in ["multi-line", "waterfall", "scatter", "grid-line", "grid-scatter"]:
                yvals_new = []
                for item in range(zvals.shape[1]):
                    yvals_new.append(zvals[:, item])

                # replace
                xvals = [xvals]
                yvals = yvals_new
                zvals = []
                if len(labels) != len(yvals):
                    labels = [""] * len(yvals)

        # create combination of x y columns
        if len(xyvals) > 0:
            from itertools import product

            xyproduct = list(product(xyvals, xyvals))
            xvals, yvals = [], []
            for iprod in xyproduct:
                xvals.append(iprod[0])
                yvals.append(iprod[1])
            if len(x_labels) == len(xyvals) and len(y_labels) == len(xyvals):
                xyproduct = list(product(x_labels, y_labels))
                x_labels, y_labels = [], []
                for iprod in xyproduct:
                    x_labels.append(iprod[0])
                    y_labels.append(iprod[1])

        if plot_type in ["grid-line", "grid-scatter", "grid-mixed"]:
            n_xvals = len(xvals)
            n_yvals = len(yvals)
            n_grid = max([n_xvals, n_yvals])
            if n_grid in [2]:
                n_rows, n_cols = 1, 2
            elif n_grid in [3, 4]:
                n_rows, n_cols = 2, 2
            elif n_grid in [5, 6]:
                n_rows, n_cols = 2, 3
            elif n_grid in [7, 8, 9]:
                n_rows, n_cols = 3, 3
            elif n_grid in [10, 11, 12]:
                n_rows, n_cols = 3, 4
            elif n_grid in [13, 14, 15, 16]:
                n_rows, n_cols = 4, 4
            elif n_grid in [17, 18, 19, 20, 21, 22, 23, 24, 25]:
                n_rows, n_cols = 5, 5
            else:
                DialogBox(
                    exceptionTitle="Error",
                    exceptionMsg="Cannot plot grid larger than 5 x 5 (25 cells). You have selected {}".format(n_grid),
                    type="Error",
                    exceptionPrint=True,
                )
                return
            plot_modifiers.update(n_grid=n_grid, n_rows=n_rows, n_cols=n_cols)

        # check if we need to add any metadata
        if len(colors) == 0 or len(colors) < len(yvals):
            colors = self.panel_plot.on_change_color_palette(None, n_colors=len(yvals), return_colors=True)

        if len(labels) != len(yvals):
            labels = [""] * len(yvals)

        msg = "Item {} has: x-columns ({}), x-errors ({}), y-columns ({}), x-errors ({}), ".format(
            os.path.basename(fname), len(xvals), len(xvalsErr), len(yvals), len(yvalsErr)
        ) + "labels ({}), colors ({})".format(len(labels), len(colors))
        print(msg)

        # update title
        _plot_types = {
            "multi-line": "Multi-line",
            "scatter": "Scatter",
            "line": "Line",
            "waterfall": "Waterfall",
            "grid-line": "Grid-line",
            "grid-scatter": "Grid-scatter",
            "vertical-bar": "V-bar",
            "horizontal-bar": "H-bar",
        }

        title = "{}: {}".format(_plot_types[plot_type], title)
        other_data = {
            "plot_type": plot_type,
            "xvals": xvals,
            "yvals": yvals,
            "zvals": zvals,
            "xvalsErr": xvalsErr,
            "yvalsErr": yvalsErr,
            "yvals_min": axis_y_min,
            "yvals_max": axis_y_max,
            "itemColors": itemColors,
            "itemLabels": itemLabels,
            "xlabel": _replace_labels(x_label),
            "ylabel": _replace_labels(y_label),
            "xlimits": xlimits,
            "ylimits": ylimits,
            "xlabels": x_labels,
            "ylabels": y_labels,
            "hover_labels": hover_labels,
            "x_unit": x_unit,
            "y_unit": y_unit,
            "colors": colors,
            "labels": labels,
            "urls": urls,
            "column_types": column_types,
            "column_order": order,
            "path": fname,
            "plot_modifiers": plot_modifiers,
        }

        return title, other_data

    def onChangePlot(self, evt):

        # Get selected item
        item = self.GetSelection()
        self._item_id = item
        # Get the current text value for selected item
        itemType = self.GetItemText(item)
        if itemType == "Documents":
            return

        # Get indent level for selected item
        indent = self.get_item_indent(item)
        if indent > 1:
            parent = self.getParentItem(item, 1)  # File name
            extract = item  # Specific Ion/file name
            item = self.getParentItem(item, 2)  # Item type
            itemType = self.GetItemText(item)
        else:
            extract = None
            parent = item

        # Get the ion/file name from deeper indent
        if extract is None:
            pass
        else:
            self._item_leaf = self.GetItemText(extract)

        # Check item
        if not item:
            return
        # Get item data for specified item
        self._document_data = self.GetPyData(parent)
        self._document_type = itemType

        self.on_show_plot(evt=None)

        if evt is not None:
            evt.Skip()

    def on_delete_item(self, evt):
        """
        Delete selected item from document
        ---
        This function is not efficient. At the moment, it deletes the item from
        document dictionary and then adds each document (and all children)
        afterwards - we should be directly deleting an item AND then removing
        the item from the dictionary
        """

        try:
            currentDoc = self._document_data.title
        except Exception:
            print("Please select document in the document tree. Sometimes you might have to right-click on it.")
            return
        document_title = byte2str(self._document_data.title)
        document = self.presenter.documentsDict[document_title]
        delete_outcome = False
        docExpandItem = None

        # Check what is going to be deleted
        # MS
        if self._document_type == "Mass Spectrum":
            # remove annotations
            if "Annotations" in self._item_leaf and self._item_branch == "Mass Spectrum":
                del self.presenter.documentsDict[currentDoc].massSpectrum["annotations"]
            elif self._item_branch == "Annotations":
                del self.presenter.documentsDict[currentDoc].massSpectrum["annotations"][self._item_leaf]
            # remove unidec data
            elif "UniDec" in self._item_leaf and self._item_branch == "Mass Spectrum":
                del self.presenter.documentsDict[currentDoc].massSpectrum["unidec"]
            elif self._item_branch == "UniDec":
                del self.presenter.documentsDict[currentDoc].massSpectrum["unidec"][self._item_leaf]
            # remove mass spectrum
            else:
                self.presenter.documentsDict[currentDoc].massSpectrum = {}
                self.presenter.documentsDict[currentDoc].gotMS = False

        if self._document_type == "Mass Spectrum (processed)":
            # remove annotations
            if "Annotations" in self._item_leaf and self._item_branch == "Mass Spectrum (processed)":
                del self.presenter.documentsDict[currentDoc].smoothMS["annotations"]
            elif self._item_branch == "Annotations":
                del self.presenter.documentsDict[currentDoc].smoothMS["annotations"][self._item_leaf]
            # remove unidec data
            elif "UniDec" in self._item_leaf and self._item_branch == "Mass Spectrum (processed)":
                del self.presenter.documentsDict[currentDoc].smoothMS["unidec"]
            elif self._item_branch == "UniDec":
                del self.presenter.documentsDict[currentDoc].smoothMS["unidec"][self._item_leaf]
            # remove mass spectrum
            else:
                self.presenter.documentsDict[currentDoc].smoothMS = {}

        if self._document_type == "Mass Spectra":
            docExpandItem = document.multipleMassSpectrum
            # remove unidec data
            if self._item_leaf == "UniDec" and self._indent == 4:
                del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[self._item_branch]["unidec"]
            elif self._item_branch == "UniDec" and self._indent == 5:
                del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[self._item_root]["unidec"][
                    self._item_leaf
                ]
            # remove annotations
            elif "Annotations" in self._item_leaf and self._indent == 4:
                del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[self._item_branch]["annotations"]
            elif "Annotations" in self._item_branch and self._indent == 5:
                del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[self._item_root]["annotations"][
                    self._item_leaf
                ]
            # remove mass spectra
            elif self._item_branch == "Mass Spectra":
                document, delete_outcome = self.on_delete_data__mass_spectra(
                    document,
                    document_title,
                    delete_type="spectrum.one",
                    spectrum_name=self._item_leaf,
                    confirm_deletion=True,
                )
            elif self._item_leaf == "Mass Spectra":
                document, delete_outcome = self.on_delete_data__mass_spectra(
                    document, document_title, delete_type="spectrum.all", confirm_deletion=True
                )

        # MS/DT
        if self._document_type == "DT/MS":
            self.presenter.documentsDict[currentDoc].DTMZ = {}
            self.presenter.documentsDict[currentDoc].gotDTMZ = False

        if self._document_type == "UniDec":
            del self.presenter.documentsDict[currentDoc].massSpectrum["unidec"]
            try:
                del self.presenter.documentsDict[currentDoc].multipleMassSpectrum["temporary_unidec"]
            except Exception:
                pass

        # DT
        elif self._document_type == "Drift time (1D)":
            self.presenter.documentsDict[currentDoc].DT = {}
            self.presenter.documentsDict[currentDoc].got1DT = False

        elif self._document_type == "Drift time (1D, EIC, DT-IMS)":
            if self._item_leaf == "Drift time (1D, EIC, DT-IMS)":
                self.presenter.documentsDict[currentDoc].IMS1DdriftTimes = {}
                self.presenter.documentsDict[currentDoc].gotExtractedDriftTimes = False
            else:
                del self.presenter.documentsDict[currentDoc].IMS1DdriftTimes[self._item_leaf]
                if len(self.presenter.documentsDict[currentDoc].IMS1DdriftTimes) == 0:
                    self.presenter.documentsDict[currentDoc].gotExtractedDriftTimes = False

        elif self._document_type == "Drift time (1D, EIC)":
            if self._item_leaf == "Drift time (1D, EIC)":
                self.presenter.documentsDict[currentDoc].multipleDT = {}
                self.presenter.documentsDict[currentDoc].gotMultipleDT = False
            else:
                del self.presenter.documentsDict[currentDoc].multipleDT[self._item_leaf]
                if len(self.presenter.documentsDict[currentDoc].multipleDT) == 0:
                    self.presenter.documentsDict[currentDoc].gotMultipleDT = False

        elif self._document_type == "Annotated data":
            # remove annotations
            if "Annotations" in self._item_leaf and self._indent == 4:
                del self.presenter.documentsDict[currentDoc].other_data[self._item_branch]["annotations"]
            elif "Annotations" in self._item_branch and self._indent == 5:
                del self.presenter.documentsDict[currentDoc].other_data[self._item_root]["annotations"][self._item_leaf]
            elif self._item_leaf == "Annotated data":
                self.presenter.documentsDict[currentDoc].other_data = {}
            else:
                del self.presenter.documentsDict[currentDoc].other_data[self._item_leaf]

        # RT
        elif self._document_type == "Chromatogram":
            self.presenter.documentsDict[currentDoc].RT = {}
            self.presenter.documentsDict[currentDoc].got1RT = False

        elif self._document_type == "Chromatograms (combined voltages, EIC)":
            if self._item_leaf == "Chromatograms (combined voltages, EIC)":
                document, delete_outcome = self.on_delete_data__heatmap(
                    document, document_title, delete_type="heatmap.rt.all"
                )
            else:
                document, delete_outcome = self.on_delete_data__heatmap(
                    document, document_title, delete_type="heatmap.rt.one", ion_name=self._item_leaf
                )

        elif self._item_branch == "Chromatograms (EIC)":
            document, delete_outcome = self.on_delete_data__chromatograms(
                document,
                document_title,
                delete_type="chromatogram.one",
                spectrum_name=self._item_leaf,
                confirm_deletion=True,
            )
        elif self._item_leaf == "Chromatograms (EIC)":
            document, delete_outcome = self.on_delete_data__chromatograms(
                document, document_title, delete_type="chromatogram.all", confirm_deletion=True
            )

        # 2D
        elif self._document_type == "Drift time (2D)":
            self.presenter.documentsDict[currentDoc].IMS2D = {}
            self.presenter.documentsDict[currentDoc].got2DIMS = False

        elif self._document_type == "Drift time (2D, processed)":
            self.presenter.documentsDict[currentDoc].IMS2Dprocess = {}
            self.presenter.documentsDict[currentDoc].got2Dprocess = False

        elif self._document_type == "Drift time (2D, EIC)":
            if self._item_leaf == "Drift time (2D, EIC)":
                document, delete_outcome = self.on_delete_data__heatmap(
                    document, document_title, delete_type="heatmap.raw.all"
                )
            else:
                document, delete_outcome = self.on_delete_data__heatmap(
                    document, document_title, delete_type="heatmap.raw.one", ion_name=self._item_leaf
                )

        elif self._document_type == "Drift time (2D, combined voltages, EIC)":
            if self._item_leaf == "Drift time (2D, combined voltages, EIC)":
                document, delete_outcome = self.on_delete_data__heatmap(
                    document, document_title, delete_type="heatmap.combined.all"
                )
            else:
                document, delete_outcome = self.on_delete_data__heatmap(
                    document, document_title, delete_type="heatmap.combined.one", ion_name=self._item_leaf
                )

        elif self._document_type == "Drift time (2D, processed, EIC)":
            if self._item_leaf == "Drift time (2D, processed, EIC)":
                document, delete_outcome = self.on_delete_data__heatmap(
                    document, document_title, delete_type="heatmap.processed.all"
                )
            else:
                document, delete_outcome = self.on_delete_data__heatmap(
                    document, document_title, delete_type="heatmap.processed.one", ion_name=self._item_leaf
                )

        elif self._document_type == "Input data":
            if self._item_leaf == "Input data":
                self.presenter.documentsDict[currentDoc].IMS2DcompData = {}
                self.presenter.documentsDict[currentDoc].gotComparisonData = False
            else:
                del self.presenter.documentsDict[currentDoc].IMS2DcompData[self._item_leaf]
                if len(self.presenter.documentsDict[currentDoc].IMS2DcompData) == 0:
                    self.presenter.documentsDict[currentDoc].gotComparisonData = False

        elif self._document_type == "Statistical":
            if self._item_leaf == "Statistical":
                self.presenter.documentsDict[currentDoc].IMS2DstatsData = {}
                self.presenter.documentsDict[currentDoc].gotStatsData = False
            else:
                del self.presenter.documentsDict[currentDoc].IMS2DstatsData[self._item_leaf]
                if len(self.presenter.documentsDict[currentDoc].IMS2DstatsData) == 0:
                    self.presenter.documentsDict[currentDoc].gotStatsData = False

        elif self._document_type == "Overlay":
            if self._item_leaf == "Overlay":
                self.presenter.documentsDict[currentDoc].IMS2DoverlayData = {}
                self.presenter.documentsDict[currentDoc].gotOverlay = False
            else:
                del self.presenter.documentsDict[currentDoc].IMS2DoverlayData[self._item_leaf]
                if len(self.presenter.documentsDict[currentDoc].IMS2DoverlayData) == 0:
                    self.presenter.documentsDict[currentDoc].gotOverlay = False

        # Calibration
        elif self._document_type == "Calibration peaks":
            if self._item_leaf == "Calibration peaks":
                self.presenter.documentsDict[currentDoc].calibration = {}
                self.presenter.documentsDict[currentDoc].gotCalibration = False
            else:
                del self.presenter.documentsDict[currentDoc].calibration[self._item_leaf]
                if len(self.presenter.documentsDict[currentDoc].calibration) == 0:
                    self.presenter.documentsDict[currentDoc].gotCalibration = False

        elif self._document_type == "Calibrants":
            if self._item_leaf == "Calibrants":
                self.presenter.documentsDict[currentDoc].calibrationDataset = {}
                self.presenter.documentsDict[currentDoc].gotCalibrationDataset = False
            else:
                del self.presenter.documentsDict[currentDoc].calibrationDataset[self._item_leaf]
                if len(self.presenter.documentsDict[currentDoc].calibrationDataset) == 0:
                    self.presenter.documentsDict[currentDoc].gotCalibrationDataset = False

        # Update documents tree
        if not delete_outcome:
            self.add_document(docData=document, expandItem=docExpandItem)
            self.presenter.documentsDict[document_title] = document
        else:
            self.data_handling.on_update_document(document, "no_refresh")

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
            docItem = self.getItemByData(document_old)
        except Exception:
            docItem = False

        if docItem is not False:
            try:
                self.SetPyData(docItem, document_new)
            except Exception:
                self.data_handling.on_update_document(document_new, "document")
        else:
            self.data_handling.on_update_document(document_new, "document")

    def on_delete_all_documents(self, evt):
        """ Alternative function to delete documents """

        dlg = DialogBox(
            exceptionTitle="Are you sure?",
            exceptionMsg="".join(["Are you sure you would like to delete ALL documents?"]),
            type="Question",
        )
        if dlg == wx.ID_NO:
            self.presenter.onThreading(None, ("Cancelled operation", 4, 5), action="updateStatusbar")
            return
        else:
            self.panel_plot.on_clear_all_plots()
            doc_keys = list(self.presenter.documentsDict.keys())
            for document in doc_keys:
                try:
                    self.removeDocument(evt=None, deleteItem=document, ask_permission=False)
                except Exception:
                    pass

    def onItemSelection(self, evt):
        # Get selected item
        item = self.GetSelection()
        self._item_id = item

        # Get the current text value for selected item
        itemType = self.GetItemText(item)

        # Get indent level for selected item
        self._indent = self.get_item_indent(item)
        if self._indent > 1:
            parent = self.getParentItem(item, 1)  # File name
            extract = item  # Specific Ion/file name
            item = self.getParentItem(item, 2)  # Item type
            itemType = self.GetItemText(item)
        else:
            extract = None
            parent = item

        # Get the ion/file name from deeper indent
        if extract is None:
            self._item_leaf = None
            self._item_branch = None
            self._item_root = None
        else:
            self._item_branch = self.GetItemText(self.GetItemParent(extract))
            self._item_leaf = self.GetItemText(extract)
            self._item_root = self.GetItemText(self.GetItemParent(self.GetItemParent(extract)))

        # Check item
        if not item:
            return
        # Get item data for specified item
        self._document_data = self.GetPyData(parent)
        self._document_type = itemType

        if evt is not None:
            evt.Skip()

    def on_add_annotation(self, evt):
        from gui_elements.panel_peak_annotation_editor import PanelPeakAnnotationEditor

        data = self.GetPyData(self._item_id)

        document = self._document_data.title
        dataset = self._item_leaf

        if data is None:
            if self._document_type == "Mass Spectrum":
                data = self._document_data.massSpectrum
                dataset = "Mass Spectrum"
            elif self._document_type == "Mass Spectrum (processed)":
                data = self._document_data.smoothMS
                dataset = "Mass Spectrum (processed)"
            elif self._document_type == "Mass Spectra" and self._item_leaf == "Annotations":
                data = self._document_data.multipleMassSpectrum[self._item_branch]
                dataset = self._item_branch
            elif "Annotated data" in self._document_type and self._item_leaf == "Annotations":
                data = self._document_data.other_data[self._item_branch]
                dataset = self._item_branch

        if "annotations" in data:
            annotations = data["annotations"]
        else:
            annotations = {}

        if self.annotateDlg is not None:
            msg = "An instance of annotation window is already open. Please close it first."
            args = (msg, 4, 5)
            self.presenter.onThreading(None, args, action="updateStatusbar")
            DialogBox(exceptionTitle="Window already open", exceptionMsg=msg, type="Error")
            return

        # waterfall plot
        if "Waterfall (Raw):" in self._item_leaf:
            data = None
            plot = self.panel_plot.plot_waterfall
        # Annotated data
        elif (
            "Multi-line: " in self._item_leaf
            or "Multi-line: " in self._item_branch
            or "V-bar: " in self._item_leaf
            or "V-bar: " in self._item_branch
            or "H-bar: " in self._item_leaf
            or "H-bar: " in self._item_branch
            or "Scatter: " in self._item_leaf
            or "Scatter: " in self._item_branch
            or "Waterfall: " in self._item_leaf
            or "Waterfall: " in self._item_branch
            or "Line: " in self._item_leaf
            or "Line: " in self._item_branch
        ):
            data = None
            plot = self.panel_plot.plotOther
        # mass spectra
        else:
            data = np.transpose([data["xvals"], data["yvals"]])
            plot = self.panel_plot.plot1

        _plot_types = {
            "multi-line": "Multi-line",
            "scatter": "Scatter",
            "line": "Line",
            "waterfall": "Waterfall",
            "grid-line": "Grid-line",
            "grid-scatter": "Grid-scatter",
            "vertical-bar": "V-bar",
            "horizontal-bar": "H-bar",
        }

        kwargs = {"document": document, "dataset": dataset, "data": data, "plot": plot, "annotations": annotations}

        self.annotateDlg = PanelPeakAnnotationEditor(self.parent, self, self.config, self.icons, **kwargs)
        self.annotateDlg.Show()

    def on_get_annotation_dataset(self, document, dataset):
        document = self.presenter.documentsDict[document]
        annotations = None
        if dataset == "Mass Spectrum":
            annotations = document.massSpectrum["annotations"]
        elif dataset == "Mass Spectrum (processed)":
            annotations = document.smoothMS["annotations"]
        elif "Waterfall (Raw):" in dataset:
            annotations = document.IMS2DoverlayData[dataset]["annotations"]
        elif (
            "Multi-line: " in dataset
            or "V-bar: " in dataset
            or "H-bar: " in dataset
            or "Scatter: " in dataset
            or "Waterfall: " in dataset
            or "Line: " in dataset
        ):
            annotations = document.other_data[dataset]["annotations"]
        else:
            annotations = document.multipleMassSpectrum[dataset]["annotations"]

        return document, annotations

    def on_update_annotation(self, annotations, document, dataset, set_data_only=False):
        """
        Update annotations in specified document/dataset
        ----------
        Parameters
        ----------
        annotations : dict
            dictionary with annotations
        document : str
            name of the document
        dataset : str
            name of the dataset
        set_data_only : bool
            specify whether all annotations should be removed and readded or if
            we it should simply set data
        """

        document = self.presenter.documentsDict[document]
        item = False
        docItem = False
        if dataset == "Mass Spectrum":
            item = self.getItemByData(document.massSpectrum)
            document.massSpectrum["annotations"] = annotations
            annotation_data = document.massSpectrum["annotations"]
        elif dataset == "Mass Spectrum (processed)":
            item = self.getItemByData(document.smoothMS)
            document.smoothMS["annotations"] = annotations
            annotation_data = document.smoothMS["annotations"]
        elif "Waterfall (Raw):" in dataset:
            item = self.getItemByData(document.IMS2DoverlayData[dataset])
            document.IMS2DoverlayData[dataset]["annotations"] = annotations
            annotation_data = document.IMS2DoverlayData[dataset]["annotations"]
        elif (
            "Multi-line: " in dataset
            or "V-bar: " in dataset
            or "H-bar: " in dataset
            or "Scatter: " in dataset
            or "Waterfall: " in dataset
            or "Line: " in dataset
        ):
            item = self.getItemByData(document.other_data[dataset])
            document.other_data[dataset]["annotations"] = annotations
            annotation_data = document.other_data[dataset]["annotations"]
        else:
            item = self.getItemByData(document.multipleMassSpectrum[dataset])
            document.multipleMassSpectrum[dataset]["annotations"] = annotations
            annotation_data = document.multipleMassSpectrum[dataset]["annotations"]

        if item is not False and not set_data_only:
            self.append_annotation(item, annotation_data)
            self.data_handling.on_update_document(document, "no_refresh")
        else:
            try:
                docItem = self.getItemByData(document)
            except Exception:
                docItem = False
            if docItem is not False:
                self.SetPyData(docItem, document)
                self.presenter.documentsDict[document.title] = document
            else:
                self.data_handling.on_update_document(document, "document")

    def append_annotation(self, item, annotation_data, expand=True):
        """
        Update annotations in the document tree
        ----------
        Parameters
        ----------
        item : wxPython document tree item
            item in the document tree that should be cleared and re-filled
        annotation_data : dict
            dictionary with annotations
        expand : bool
            specify if tree item should be expanded

        """
        child, cookie = self.GetFirstChild(item)
        while child.IsOk():
            if self.GetItemText(child) == "Annotations":
                self.Delete(child)
            child, cookie = self.GetNextChild(item, cookie)

        if len(annotation_data) == 0:
            return

        annotation_item = self.AppendItem(item, "Annotations")
        self.SetItemImage(annotation_item, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)
        for key in annotation_data:
            itemAnnotIndividual = self.AppendItem(annotation_item, key)
            self.SetPyData(itemAnnotIndividual, annotation_data[key])
            self.SetItemImage(itemAnnotIndividual, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)

        if expand:
            self.Expand(annotation_item)

    def on_duplicate_annotations(self, evt):
        """
        Duplicate annotations from one spectrum to another
        ----------
        Parameters
        ----------
        evt : wxPython event
            unused
        """

        # get document and annotations
        document = self.presenter.documentsDict[self._document_data.title]
        if self._document_type == "Mass Spectrum":
            annotations = deepcopy(document.massSpectrum.get("annotations", None))
        elif self._document_type == "Mass Spectrum (processed)":
            annotations = deepcopy(document.smoothMS.get("annotations", None))
        else:
            annotations = deepcopy(document.multipleMassSpectrum[self._item_leaf].get("annotations", None))

        if annotations is None or len(annotations) == 0:
            raise MessageError("Annotations were not found", "This item has no annotations to duplicate.\n\n\n")

        # ask which document to add it to
        document_list, document_spectrum_list = [], {}
        for document_title in self.presenter.documentsDict:
            document_spectrum_list[document_title] = []
            if self.presenter.documentsDict[document_title].gotMultipleMS:
                document_spectrum_list[document_title].extend(
                    list(self.presenter.documentsDict[document_title].multipleMassSpectrum.keys())
                )
            if len(self.presenter.documentsDict[document_title].massSpectrum) > 0:
                document_spectrum_list[document_title].append("Mass Spectrum")
            if len(self.presenter.documentsDict[document_title].smoothMS) > 0:
                document_spectrum_list[document_title].append("Mass Spectrum (processed)")
            if len(self.presenter.documentsDict[document_title].IMS2DoverlayData) > 0:
                for key in self.presenter.documentsDict[document_title].IMS2DoverlayData:
                    if "Waterfall (Raw):" in key:
                        document_spectrum_list[document_title].append(key)

            if len(document_spectrum_list[document_title]) > 0:
                document_list.append(document_title)

        kwargs = dict(set_document=document.title)
        duplicateDlg = DialogSelectDataset(self.presenter.view, self, document_list, document_spectrum_list, **kwargs)
        if duplicateDlg.ShowModal() == wx.ID_OK:
            pass

        duplicate_document = duplicateDlg.document
        duplicate_dataset = duplicateDlg.dataset

        if duplicate_document is None or duplicate_dataset is None:
            self.presenter.onThreading(None, ("Operation was cancelled.", 4, 5), action="updateStatusbar")
            return

        item = False
        # add annotations to document
        duplicate_document = self.presenter.documentsDict[duplicate_document]
        if duplicate_dataset == "Mass Spectrum":
            item = self.getItemByData(duplicate_document.massSpectrum)
            duplicate_document.massSpectrum["annotations"] = annotations
            annotation_data = duplicate_document.massSpectrum["annotations"]
        elif duplicate_dataset == "Mass Spectrum (processed)":
            item = self.getItemByData(duplicate_document.massSpectrum)
            duplicate_document.smoothMS["annotations"] = annotations
            annotation_data = duplicate_document.smoothMS["annotations"]
        elif "Waterfall (Raw):" in duplicate_dataset:
            item = self.getItemByData(duplicate_document.IMS2DoverlayData[duplicate_dataset])
            duplicate_document.IMS2DoverlayData[duplicate_dataset]["annotations"] = annotations
            annotation_data = duplicate_document.IMS2DoverlayData[duplicate_dataset]["annotations"]
        else:
            item = self.getItemByData(duplicate_document.multipleMassSpectrum[duplicate_dataset])
            duplicate_document.multipleMassSpectrum[duplicate_dataset]["annotations"] = annotations
            annotation_data = duplicate_document.multipleMassSpectrum[duplicate_dataset]["annotations"]

        if item is not False:
            self.append_annotation(item, annotation_data)
            self.data_handling.on_update_document(duplicate_document, "no_refresh")
        else:
            self.data_handling.on_update_document(duplicate_document, "document")

        msg = "Duplicated annotations to {} - {}".format(duplicate_document.title, duplicate_dataset)
        self.presenter.onThreading(None, (msg, 4, 5), action="updateStatusbar")

    def on_show_annotations(self, evt):
        """
        Show annotations in the currently shown mass spectrum
        ----------
        Parameters
        ----------
        evt : wxPython event
            unused
        """
        document = self.presenter.documentsDict[self._document_data.title]
        plot_obj = self.panel_plot.plot1
        if self._document_type == "Mass Spectrum":
            annotations = document.massSpectrum["annotations"]
        elif self._document_type == "Mass Spectrum (processed)":
            annotations = document.smoothMS["annotations"]
        elif self._document_type == "Mass Spectra":
            annotations = document.multipleMassSpectrum[self._item_branch]["annotations"]
        elif self._document_type == "Annotated data" and (
            "Waterfall: " in self._item_branch
            or "Multi-line: " in self._item_branch
            or "V-bar: " in self._item_branch
            or "H-bar: " in self._item_branch
            or "Scatter: " in self._item_branch
            or "Line: " in self._item_branch
        ):
            annotations = document.other_data[self._item_branch]["annotations"]
            plot_obj = self.panel_plot.plotOther

        plot_obj.plot_remove_text_and_lines()
        _ymax = []

        label_kwargs = self.panel_plot._buildPlotParameters(plotType="label")
        for key in annotations:
            annotation = annotations[key]
            intensity = str2num(annotation["intensity"])
            charge = annotation["charge"]
            min_x_value = annotation["min"]
            max_x_value = annotation["max"]
            color_value = annotation.get("color", self.config.interactive_ms_annotations_color)
            add_arrow = annotation.get("add_arrow", False)
            show_label = annotation["label"]

            if "isotopic_x" in annotation:
                mz_value = annotation["isotopic_x"]
                if mz_value in ["", 0] or mz_value < min_x_value:
                    mz_value = max_x_value - ((max_x_value - min_x_value) / 2)
            else:
                mz_value = max_x_value - ((max_x_value - min_x_value) / 2)

            label_x_position = annotation.get("position_label_x", mz_value)
            label_y_position = annotation.get("position_label_y", intensity)

            if show_label == "":
                show_label = "{}, {}\nz={}".format(round(mz_value, 4), intensity, charge)

            # add  custom name tag
            try:
                obj_name_tag = "{}|-|{}|-|{} - {}|-|{}".format(
                    self._document_data.title, self._item_branch, min_x_value, max_x_value, "annotation"
                )
                label_kwargs["text_name"] = obj_name_tag
            except Exception:
                pass

            if add_arrow:
                arrow_x_position = label_x_position
                label_x_position = annotation.get("position_label_x", label_x_position)
                arrow_dx = label_x_position - arrow_x_position
                arrow_y_position = label_y_position
                label_y_position = annotation.get("position_label_y", label_y_position)
                arrow_dy = label_y_position - arrow_y_position

            plot_obj.plot_add_text_and_lines(
                xpos=label_x_position,
                yval=label_y_position,
                label=show_label,
                vline=False,
                stick_to_intensity=True,
                yoffset=self.config.annotation_label_y_offset,
                color=color_value,
                **label_kwargs,
            )

            _ymax.append(label_y_position)
            if add_arrow:
                arrow_list = [arrow_x_position, arrow_y_position, arrow_dx, arrow_dy]
                plot_obj.plot_add_arrow(arrow_list, stick_to_intensity=True)

        if self.config.annotation_zoom_y:
            try:
                plot_obj.on_zoom_y_axis(endY=np.amax(_ymax) * self.config.annotation_zoom_y_multiplier)
            except TypeError:
                pass

        plot_obj.repaint()

    def on_action_ORIGAMI_MS(self, evt, document_title=None):
        from gui_elements.dialog_customise_origami import DialogCustomiseORIGAMI

        dlg = DialogCustomiseORIGAMI(self, self.presenter, self.config, document_title=document_title)
        dlg.ShowModal()

    def _bind_change_label_events(self):
        for xID in [
            ID_xlabel_2D_scans,
            ID_xlabel_2D_colVolt,
            ID_xlabel_2D_actVolt,
            ID_xlabel_2D_labFrame,
            ID_xlabel_2D_actLabFrame,
            ID_xlabel_2D_massToCharge,
            ID_xlabel_2D_mz,
            ID_xlabel_2D_wavenumber,
            ID_xlabel_2D_restore,
            ID_xlabel_2D_ccs,
            ID_xlabel_2D_charge,
            ID_xlabel_2D_custom,
            ID_xlabel_2D_time_min,
            ID_xlabel_2D_retTime_min,
        ]:
            self.Bind(wx.EVT_MENU, self.on_change_xy_values_and_labels, id=xID)

        for yID in [
            ID_ylabel_2D_bins,
            ID_ylabel_2D_ms,
            ID_ylabel_2D_ms_arrival,
            ID_ylabel_2D_ccs,
            ID_ylabel_2D_restore,
            ID_ylabel_2D_custom,
        ]:
            self.Bind(wx.EVT_MENU, self.on_change_xy_values_and_labels, id=yID)

        # 1D
        for yID in [
            ID_xlabel_1D_bins,
            ID_xlabel_1D_ms,
            ID_xlabel_1D_ms_arrival,
            ID_xlabel_1D_ccs,
            ID_xlabel_1D_restore,
        ]:
            self.Bind(wx.EVT_MENU, self.on_change_xy_values_and_labels, id=yID)

        # RT
        for yID in [ID_xlabel_RT_scans, ID_xlabel_RT_time_min, ID_xlabel_RT_retTime_min, ID_xlabel_RT_restore]:
            self.Bind(wx.EVT_MENU, self.on_change_xy_values_and_labels, id=yID)

        # DT/MS
        for yID in [ID_ylabel_DTMS_bins, ID_ylabel_DTMS_ms, ID_ylabel_DTMS_ms_arrival, ID_ylabel_DTMS_restore]:
            self.Bind(wx.EVT_MENU, self.on_change_xy_values_and_labels, id=yID)

    def on_right_click(self, evt):
        """ Create and show up popup menu"""

        # Make some bindings
        #         self.Bind(wx.EVT_MENU, self.on_save_all_documents, id=ID_saveAllDocuments)
        self.Bind(wx.EVT_MENU, self.data_handling.on_save_all_documents_fcn, id=ID_saveAllDocuments)
        self.Bind(wx.EVT_MENU, self.on_delete_all_documents, id=ID_removeAllDocuments)

        # Get selected item
        item = self.GetSelection()
        self._item_id = item
        # Get the current text value for selected item
        itemType = self.GetItemText(item)
        if itemType == "Documents":
            menu = wx.Menu()
            menu.AppendItem(
                makeMenuItem(
                    parent=menu,
                    id=ID_saveAllDocuments,
                    text="Save all documents",
                    bitmap=self.icons.iconsLib["save_multiple_16"],
                )
            )
            menu.AppendItem(
                makeMenuItem(
                    parent=menu,
                    id=ID_removeAllDocuments,
                    text="Delete all documents",
                    bitmap=self.icons.iconsLib["bin16"],
                )
            )
            self.PopupMenu(menu)
            menu.Destroy()
            self.SetFocus()
            return

        # Get indent level for selected item
        self._indent = self.get_item_indent(item)
        if self._indent > 1:
            parent = self.getParentItem(item, 1)  # File name
            extract = item  # Specific Ion/file name
            item = self.getParentItem(item, 2)  # Item type
            itemType = self.GetItemText(item)
        else:
            extract = None
            parent = item

        # Get the ion/file name from deeper indent
        if extract is None:
            self._item_leaf = None
            self._item_branch = None
            self._item_root = None
        else:
            self._item_branch = self.GetItemText(self.GetItemParent(extract))
            self._item_leaf = self.GetItemText(extract)
            self._item_root = self.GetItemText(self.GetItemParent(self.GetItemParent(extract)))

        try:
            self.title = self._document_data.title
        except Exception:
            self.title = None

        # split
        try:
            self.splitText = re.split("-|,|:|__", self._item_leaf)
        except Exception:
            self.splitText = []

        # Check item
        if not item:
            return

        # Get item data for specified item
        self._document_data = self.GetPyData(parent)
        self._document_type = itemType
        try:
            self.currentData = self.GetPyData(self._item_id)
        except Exception:
            self.currentData = None

        if self.config.debug:
            msg = (
                f"DEBUG: _document_type: {self._document_type} | _item_leaf: {self._item_leaf} | "
                + f"_item_branch: {self._item_branch} | _item_root: {self._item_root} | _indent: {self._indent}"
            )
            print(msg)

        # load data
        load_data_menu = wx.Menu()
        load_data_menu.Append(ID_docTree_add_MS_to_interactive, "Import mass spectrum")
        load_data_menu.Append(ID_docTree_add_RT_to_interactive, "Import chromatogram")
        load_data_menu.Append(ID_docTree_add_DT_to_interactive, "Import mobiligram")
        load_data_menu.Append(ID_docTree_add_2DT_to_interactive, "Import heatmap")
        load_data_menu.Append(ID_docTree_add_matrix_to_interactive, "Import matrix")
        load_data_menu.Append(ID_docTree_add_comparison_to_interactive, "Import comparison")
        load_data_menu.AppendSeparator()
        load_data_menu.Append(ID_docTree_add_other_to_interactive, "Import data with metadata...")

        # Change x-axis label (2D)
        xlabel_2D_menu = wx.Menu()
        xlabel_2D_menu.Append(ID_xlabel_2D_scans, "Scans", "", wx.ITEM_RADIO)
        xlabel_2D_menu.Append(ID_xlabel_2D_time_min, "Time (min)", "", wx.ITEM_RADIO)
        xlabel_2D_menu.Append(ID_xlabel_2D_retTime_min, "Retention time (min)", "", wx.ITEM_RADIO)
        xlabel_2D_menu.Append(ID_xlabel_2D_colVolt, "Collision Voltage (V)", "", wx.ITEM_RADIO)
        xlabel_2D_menu.Append(ID_xlabel_2D_actVolt, "Activation Energy (V)", "", wx.ITEM_RADIO)
        xlabel_2D_menu.Append(ID_xlabel_2D_labFrame, "Lab Frame Energy (eV)", "", wx.ITEM_RADIO)
        xlabel_2D_menu.Append(ID_xlabel_2D_actLabFrame, "Activation Energy (eV)", "", wx.ITEM_RADIO)
        xlabel_2D_menu.Append(ID_xlabel_2D_massToCharge, "Mass-to-charge (Da)", "", wx.ITEM_RADIO)
        xlabel_2D_menu.Append(ID_xlabel_2D_mz, "m/z (Da)", "", wx.ITEM_RADIO)
        xlabel_2D_menu.Append(ID_xlabel_2D_wavenumber, "Wavenumber (cm⁻¹)", "", wx.ITEM_RADIO)
        xlabel_2D_menu.Append(ID_xlabel_2D_charge, "Charge", "", wx.ITEM_RADIO)
        xlabel_2D_menu.Append(ID_xlabel_2D_ccs, "Collision Cross Section (Å²)", "", wx.ITEM_RADIO)
        xlabel_2D_menu.Append(ID_xlabel_2D_custom, "Custom label...", "", wx.ITEM_RADIO)
        xlabel_2D_menu.AppendSeparator()
        xlabel_2D_menu.Append(ID_xlabel_2D_restore, "Restore default", "")

        # Change y-axis label (2D)
        ylabel_2D_menu = wx.Menu()
        ylabel_2D_menu.Append(ID_ylabel_2D_bins, "Drift time (bins)", "", wx.ITEM_RADIO)
        ylabel_2D_menu.Append(ID_ylabel_2D_ms, "Drift time (ms)", "", wx.ITEM_RADIO)
        ylabel_2D_menu.Append(ID_ylabel_2D_ms_arrival, "Arrival time (ms)", "", wx.ITEM_RADIO)
        ylabel_2D_menu.Append(ID_ylabel_2D_ccs, "Collision Cross Section (Å²)", "", wx.ITEM_RADIO)
        ylabel_2D_menu.Append(ID_ylabel_2D_custom, "Custom label...", "", wx.ITEM_RADIO)
        ylabel_2D_menu.AppendSeparator()
        ylabel_2D_menu.Append(ID_ylabel_2D_restore, "Restore default", "")

        # Check xy axis labels
        if self._document_type in [
            "Drift time (2D)",
            "Drift time (2D, processed)",
            "Drift time (2D, EIC)",
            "Drift time (2D, combined voltages, EIC)",
            "Drift time (2D, processed, EIC)",
            "Input data",
        ]:

            # Check what is the current label for this particular dataset
            try:
                idX, idY = self.on_check_xylabels_2D()
                xlabel_2D_menu.FindItemById(idX).Check(True)
                ylabel_2D_menu.FindItemById(idY).Check(True)
            except (UnboundLocalError, TypeError, KeyError):
                logger.warning(f"Failed to setup x/y labels for `{self._document_type}` item`")

        # Change x-axis label (1D)
        xlabel_1D_menu = wx.Menu()
        xlabel_1D_menu.Append(ID_xlabel_1D_bins, "Drift time (bins)", "", wx.ITEM_RADIO)
        xlabel_1D_menu.Append(ID_xlabel_1D_ms, "Drift time (ms)", "", wx.ITEM_RADIO)
        xlabel_1D_menu.Append(ID_xlabel_1D_ms_arrival, "Arrival time (ms)", "", wx.ITEM_RADIO)
        xlabel_1D_menu.Append(ID_xlabel_1D_ccs, "Collision Cross Section (Å²)", "", wx.ITEM_RADIO)
        xlabel_1D_menu.AppendSeparator()
        xlabel_1D_menu.Append(ID_xlabel_1D_restore, "Restore default", "")

        if self._document_type in ["Drift time (1D)", "Drift time (1D, EIC)"]:
            try:
                idX = self.on_check_xlabels_1D()
                xlabel_1D_menu.FindItemById(idX).Check(True)
            except (UnboundLocalError, TypeError, KeyError):
                logger.warning(f"Failed to setup labels for `{self._document_type}` item`")

        # Change x-axis label (RT)
        xlabel_RT_menu = wx.Menu()
        xlabel_RT_menu.Append(ID_xlabel_RT_scans, "Scans", "", wx.ITEM_RADIO)
        xlabel_RT_menu.Append(ID_xlabel_RT_time_min, "Time (min)", "", wx.ITEM_RADIO)
        xlabel_RT_menu.Append(ID_xlabel_RT_retTime_min, "Retention time (min)", "", wx.ITEM_RADIO)
        xlabel_RT_menu.AppendSeparator()
        xlabel_RT_menu.Append(ID_xlabel_RT_restore, "Restore default", "")

        if (self._document_type in ["Chromatogram"] and self._indent == 2) or (
            self._document_type in ["Chromatograms (EIC)", "Chromatograms (combined voltages, EIC)"]
            and self._indent > 2
        ):
            try:
                idX = self.on_check_xlabels_RT()
                xlabel_RT_menu.FindItemById(idX).Check(True)
            except (UnboundLocalError, TypeError, KeyError):
                logger.warning(f"Failed to setup labels for `{self._document_type}` item`")

        # change y-axis label (DT/MS)
        ylabel_DTMS_menu = wx.Menu()
        ylabel_DTMS_menu.Append(ID_ylabel_DTMS_bins, "Drift time (bins)", "", wx.ITEM_RADIO)
        ylabel_DTMS_menu.Append(ID_ylabel_DTMS_ms, "Drift time (ms)", "", wx.ITEM_RADIO)
        ylabel_DTMS_menu.Append(ID_ylabel_DTMS_ms_arrival, "Arrival time (ms)", "", wx.ITEM_RADIO)
        ylabel_DTMS_menu.AppendSeparator()
        ylabel_DTMS_menu.Append(ID_ylabel_DTMS_restore, "Restore default", "")

        if self._document_type == "DT/MS":
            try:
                idX = self.on_check_xlabels_DTMS()
                ylabel_DTMS_menu.FindItemById(idX).Check(True)
            except (UnboundLocalError, TypeError, KeyError):
                logger.warning(f"Failed to setup labels for `{self._document_type}` item`")

        action_menu = wx.Menu()
        action_menu.Append(ID_docTree_action_open_origami_ms, "Setup ORIGAMI-MS parameters...")
        action_menu.Append(ID_docTree_action_open_extract, "Open data extraction panel...")
        action_menu.Append(ID_docTree_action_open_extractDTMS, "Open DT/MS dataset settings...")

        # save dataframe
        save_data_submenu = wx.Menu()
        save_data_submenu.Append(ID_saveData_csv, "Save to .csv file")
        save_data_submenu.Append(ID_saveData_pickle, "Save to .pickle file")
        save_data_submenu.Append(ID_saveData_hdf, "Save to .hdf file (slow)")
        save_data_submenu.Append(ID_saveData_excel, "Save to .excel file (v. slow)")

        # Bind events
        self._bind_change_label_events()

        self.Bind(wx.EVT_MENU, self.on_show_plot, id=ID_showPlotDocument)
        self.Bind(wx.EVT_MENU, self.on_show_plot, id=ID_showPlotDocument_violin)
        self.Bind(wx.EVT_MENU, self.on_show_plot, id=ID_showPlotDocument_waterfall)
        self.Bind(wx.EVT_MENU, self.on_show_plot, id=ID_showPlot1DDocument)
        self.Bind(wx.EVT_MENU, self.on_show_plot, id=ID_showPlotRTDocument)
        self.Bind(wx.EVT_MENU, self.on_show_plot, id=ID_showPlotMSDocument)
        self.Bind(wx.EVT_MENU, self.onProcess, id=ID_process2DDocument)
        self.Bind(wx.EVT_MENU, self.on_change_charge_state, id=ID_assignChargeState)
        self.Bind(wx.EVT_MENU, self.onGoToDirectory, id=ID_goToDirectory)
        self.Bind(wx.EVT_MENU, self.onSaveCSV, id=ID_saveDataCSVDocument)
        self.Bind(wx.EVT_MENU, self.onSaveCSV, id=ID_saveDataCSVDocument1D)
        self.Bind(wx.EVT_MENU, self.onSaveCSV, id=ID_saveAsDataCSVDocument)
        self.Bind(wx.EVT_MENU, self.onSaveCSV, id=ID_saveAsDataCSVDocument1D)
        self.Bind(wx.EVT_MENU, self.onRenameItem, id=ID_renameItem)
        self.Bind(wx.EVT_MENU, self.onDuplicateItem, id=ID_duplicateItem)
        self.Bind(wx.EVT_MENU, self.on_save_document, id=ID_saveDocument)
        self.Bind(wx.EVT_MENU, self.onShowSampleInfo, id=ID_showSampleInfo)
        self.Bind(wx.EVT_MENU, self.view.openSaveAsDlg, id=ID_saveAsInteractive)
        self.Bind(wx.EVT_MENU, self.presenter.restoreComparisonToList, id=ID_restoreComparisonData)
        self.Bind(wx.EVT_MENU, self.onCompareMS, id=ID_docTree_compareMS)
        self.Bind(wx.EVT_MENU, self.onShowMassSpectra, id=ID_docTree_showMassSpectra)
        self.Bind(wx.EVT_MENU, self.on_process_MS, id=ID_docTree_processMS)
        self.Bind(wx.EVT_MENU, self.on_process_MS_all, id=ID_docTree_processMS_all)
        self.Bind(wx.EVT_MENU, self.on_process_2D, id=ID_docTree_process2D)
        self.Bind(wx.EVT_MENU, self.on_process_all_2D, id=ID_docTree_process2D_all)
        self.Bind(wx.EVT_MENU, self.onAddToTable, id=ID_docTree_addToMMLTable)
        self.Bind(wx.EVT_MENU, self.onAddToTable, id=ID_docTree_addOneToMMLTable)
        self.Bind(wx.EVT_MENU, self.onAddToTable, id=ID_docTree_addToTextTable)
        self.Bind(wx.EVT_MENU, self.onAddToTable, id=ID_docTree_addOneToTextTable)
        self.Bind(wx.EVT_MENU, self.onAddToTable, id=ID_docTree_addInteractiveToTextTable)
        self.Bind(wx.EVT_MENU, self.onAddToTable, id=ID_docTree_addOneInteractiveToTextTable)
        self.Bind(wx.EVT_MENU, self.on_add_annotation, id=ID_docTree_add_annotations)
        self.Bind(wx.EVT_MENU, self.on_show_annotations, id=ID_docTree_show_annotations)
        self.Bind(wx.EVT_MENU, self.on_duplicate_annotations, id=ID_docTree_duplicate_annotations)
        self.Bind(wx.EVT_MENU, self.onDuplicateItem, id=ID_docTree_duplicate_document)
        self.Bind(wx.EVT_MENU, self.on_refresh_document, id=ID_docTree_show_refresh_document)
        self.Bind(wx.EVT_MENU, self.on_delete_item, id=ID_removeItemDocument)
        self.Bind(wx.EVT_MENU, self.removeDocument, id=ID_removeDocument)
        self.Bind(wx.EVT_MENU, self.onOpenDocInfo, id=ID_openDocInfo)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveMSImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveRTImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_save1DImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_save2DImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveMZDTImage)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_save3DImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveRMSDImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveRMSFImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveOverlayImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveWaterfallImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveRMSDmatrixImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveOtherImageDoc)
        self.Bind(wx.EVT_MENU, self.on_process_UVPD, id=ID_docTree_plugin_UVPD)
        self.Bind(wx.EVT_MENU, self.on_load_custom_data, id=ID_docTree_add_MS_to_interactive)
        self.Bind(wx.EVT_MENU, self.on_load_custom_data, id=ID_docTree_add_RT_to_interactive)
        self.Bind(wx.EVT_MENU, self.on_load_custom_data, id=ID_docTree_add_DT_to_interactive)
        self.Bind(wx.EVT_MENU, self.on_load_custom_data, id=ID_docTree_add_2DT_to_interactive)
        self.Bind(wx.EVT_MENU, self.on_load_custom_data, id=ID_docTree_add_other_to_interactive)
        self.Bind(wx.EVT_MENU, self.on_load_custom_data, id=ID_docTree_add_matrix_to_interactive)
        self.Bind(wx.EVT_MENU, self.on_load_custom_data, id=ID_docTree_add_comparison_to_interactive)
        self.Bind(wx.EVT_MENU, self.onSaveDF, id=ID_saveData_csv)
        self.Bind(wx.EVT_MENU, self.onSaveDF, id=ID_saveData_pickle)
        self.Bind(wx.EVT_MENU, self.onSaveDF, id=ID_saveData_excel)
        self.Bind(wx.EVT_MENU, self.onSaveDF, id=ID_saveData_hdf)
        self.Bind(wx.EVT_MENU, self.on_open_UniDec, id=ID_docTree_show_unidec)
        self.Bind(wx.EVT_MENU, self.on_save_unidec_results, id=ID_docTree_save_unidec)
        self.Bind(wx.EVT_MENU, self.on_add_mzID_file_fcn, id=ID_docTree_add_mzIdentML)
        self.Bind(wx.EVT_MENU, self.on_action_ORIGAMI_MS, id=ID_docTree_action_open_origami_ms)
        self.Bind(wx.EVT_MENU, self.on_open_extract_DTMS, id=ID_docTree_action_open_extractDTMS)
        self.Bind(wx.EVT_MENU, self.on_open_peak_picker, id=ID_docTree_action_open_peak_picker)
        self.Bind(wx.EVT_MENU, self.on_open_extract_data, id=ID_docTree_action_open_extract)
        self.Bind(wx.EVT_MENU, self.on_open_UniDec, id=ID_docTree_UniDec)

        # Get label
        if self._item_leaf is not None:
            try:
                plotLabel = self._item_leaf.split(":")
            except AttributeError:
                pass
        menu = wx.Menu()

        menu_show_annotations_panel = makeMenuItem(
            parent=menu,
            id=ID_docTree_add_annotations,
            text="Show annotations panel...",
            bitmap=self.icons.iconsLib["annotate16"],
        )
        menu_show_comparison_panel = makeMenuItem(
            parent=menu,
            id=ID_docTree_compareMS,
            text="Compare mass spectra...",
            bitmap=self.icons.iconsLib["compare_mass_spectra_16"],
        )
        menu_show_peak_picker_panel = makeMenuItem(
            parent=menu,
            id=ID_docTree_action_open_peak_picker,
            text="Open peak picker...",
            bitmap=self.icons.iconsLib["highlight_16"],
        )
        menu_action_delete_item = makeMenuItem(
            parent=menu, id=ID_removeItemDocument, text="Delete item\tDelete", bitmap=self.icons.iconsLib["clear_16"]
        )
        menu_action_show_annotations = makeMenuItem(
            parent=menu,
            id=ID_docTree_show_annotations,
            text="Show annotations on plot",
            bitmap=self.icons.iconsLib["highlight_16"],
        )
        menu_action_show_highlights = makeMenuItem(
            parent=menu,
            id=ID_showPlotMSDocument,
            text="Highlight ion in mass spectrum\tAlt+X",
            bitmap=self.icons.iconsLib["zoom_16"],
        )

        menu_action_show_plot = makeMenuItem(
            parent=menu, id=ID_showPlotDocument, text="Show plot\tAlt+S", bitmap=self.icons.iconsLib["blank_16"]
        )
        menu_action_show_plot_spectrum = makeMenuItem(
            parent=menu,
            id=ID_showPlotDocument,
            text="Show mass spectrum\tAlt+S",
            bitmap=self.icons.iconsLib["mass_spectrum_16"],
        )
        menu_action_show_plot_spectrum_waterfall = makeMenuItem(
            parent=menu, id=ID_docTree_showMassSpectra, text="Show mass spectra (waterfall)", bitmap=None
        )
        menu_action_show_plot_mobilogram = makeMenuItem(
            parent=menu,
            id=ID_showPlotDocument,
            text="Show mobiligram\tAlt+S",
            bitmap=self.icons.iconsLib["mobiligram_16"],
        )
        menu_action_show_plot_chromatogram = makeMenuItem(
            parent=menu,
            id=ID_showPlotDocument,
            text="Show chromatogram\tAlt+S",
            bitmap=self.icons.iconsLib["chromatogram_16"],
        )
        menu_action_show_plot_2D = makeMenuItem(
            parent=menu, id=ID_showPlotDocument, text="Show heatmap\tAlt+S", bitmap=self.icons.iconsLib["heatmap_16"]
        )
        menu_action_show_plot_violin = makeMenuItem(
            parent=menu,
            id=ID_showPlotDocument_violin,
            text="Show violin plot",
            bitmap=self.icons.iconsLib["panel_violin_16"],
        )
        menu_action_show_plot_waterfall = makeMenuItem(
            parent=menu,
            id=ID_showPlotDocument_waterfall,
            text="Show waterfall plot",
            bitmap=self.icons.iconsLib["panel_waterfall_16"],
        )

        menu_action_show_plot_as_mobiligram = makeMenuItem(
            parent=menu, id=ID_showPlot1DDocument, text="Show mobiligram", bitmap=self.icons.iconsLib["mobiligram_16"]
        )

        menu_action_show_plot_as_chromatogram = makeMenuItem(
            parent=menu,
            id=ID_showPlotRTDocument,
            text="Show chromatogram",
            bitmap=self.icons.iconsLib["chromatogram_16"],
        )

        menu_action_rename_item = makeMenuItem(
            parent=menu, id=ID_renameItem, text="Rename\tF2", bitmap=self.icons.iconsLib["rename_16"]
        )

        menu_action_duplicate_annotations = makeMenuItem(
            parent=menu,
            id=ID_docTree_duplicate_annotations,
            text="Duplicate annotations...",
            bitmap=self.icons.iconsLib["duplicate_item_16"],
        )

        menu_action_process_ms = makeMenuItem(
            parent=menu, id=ID_docTree_processMS, text="Process...\tP", bitmap=self.icons.iconsLib["process_ms_16"]
        )
        menu_action_process_ms_all = makeMenuItem(
            parent=menu, id=ID_docTree_processMS_all, text="Process all...", bitmap=self.icons.iconsLib["process_ms_16"]
        )
        menu_action_process_2D = makeMenuItem(
            parent=menu, id=ID_docTree_process2D, text="Process...\tP", bitmap=self.icons.iconsLib["process_2d_16"]
        )
        menu_action_process_2D_all = makeMenuItem(
            parent=menu,
            id=ID_docTree_process2D_all,
            text="Process all...\tP",
            bitmap=self.icons.iconsLib["process_2d_16"],
        )

        menu_action_assign_charge = makeMenuItem(
            parent=menu,
            id=ID_assignChargeState,
            text="Assign charge state...\tAlt+Z",
            bitmap=self.icons.iconsLib["assign_charge_16"],
        )
        menu_show_unidec_panel = makeMenuItem(
            parent=menu,
            id=ID_docTree_UniDec,
            text="Deconvolute using UniDec...",
            bitmap=self.icons.iconsLib["process_unidec_16"],
        )
        menu_action_add_spectrum_to_panel = makeMenuItem(
            parent=menu, id=ID_docTree_addOneToMMLTable, text="Add spectrum to multiple files panel", bitmap=None
        )
        menu_action_show_unidec_results = makeMenuItem(
            parent=menu, id=ID_docTree_show_unidec, text="Show UniDec results", bitmap=None
        )
        menu_action_save_mobilogram_image_as = makeMenuItem(
            parent=menu, id=ID_save1DImageDoc, text="Save image as...", bitmap=self.icons.iconsLib["file_png_16"]
        )

        menu_action_save_heatmap_image_as = makeMenuItem(
            parent=menu, id=ID_save2DImageDoc, text="Save image as...", bitmap=self.icons.iconsLib["file_png_16"]
        )

        menu_action_save_other_image_as = makeMenuItem(
            parent=menu, id=ID_saveOtherImageDoc, text="Save image as...", bitmap=self.icons.iconsLib["file_png_16"]
        )

        menu_action_save_spectrum_image_as = makeMenuItem(
            parent=menu, id=ID_saveMSImageDoc, text="Save image as...", bitmap=self.icons.iconsLib["file_csv_16"]
        )

        menu_action_save_data_as = makeMenuItem(
            parent=menu, id=ID_saveDataCSVDocument, text="Save data as...", bitmap=self.icons.iconsLib["file_csv_16"]
        )

        menu_action_save_1D_data_as = makeMenuItem(
            parent=menu,
            id=ID_saveDataCSVDocument1D,
            text="Save 1D data as...",
            bitmap=self.icons.iconsLib["file_csv_16"],
        )

        menu_action_save_2D_data_as = makeMenuItem(
            parent=menu, id=ID_saveDataCSVDocument, text="Save 2D data as...", bitmap=self.icons.iconsLib["file_csv_16"]
        )
        menu_action_save_chromatogram_image_as = makeMenuItem(
            parent=menu, id=ID_saveRTImageDoc, text="Save image as...", bitmap=self.icons.iconsLib["file_png_16"]
        )

        # INTERACTIVE DATASET ONLY
        if self._document_data.dataType == "Type: Interactive":
            if self._document_type == "Annotated data" and self._item_leaf != self._document_type:
                if self._item_leaf == "Annotations":
                    menu.AppendItem(menu_show_annotations_panel)
                    menu.AppendItem(menu_action_show_annotations)
                else:
                    menu.AppendItem(menu_action_show_plot)

                if (
                    "Multi-line: " in self._item_leaf
                    or "V-bar: " in self._item_leaf
                    or "H-bar: " in self._item_leaf
                    or "Scatter: " in self._item_leaf
                    or "Waterfall: " in self._item_leaf
                    or "Line: " in self._item_leaf
                ):
                    menu.AppendItem(menu_show_annotations_panel)
                menu.AppendSeparator()
                menu.AppendItem(menu_action_save_other_image_as)
                menu.AppendItem(menu_action_delete_item)
            if self._document_type in ["Drift time (2D)", "Drift time (2D, processed)"] or (
                self._document_type == "Drift time (2D, EIC)" and self._item_leaf != self._document_type
            ):
                menu.AppendItem(menu_action_show_plot_2D)
                menu.AppendItem(menu_action_show_plot_violin)
                menu.AppendItem(menu_action_show_plot_waterfall)
                menu.AppendItem(menu_action_process_2D)
                menu.AppendSeparator()
                menu.AppendItem(menu_action_rename_item)
                menu.AppendItem(menu_action_assign_charge)
                menu.AppendMenu(wx.ID_ANY, "Set X-axis label as...", xlabel_2D_menu)
                menu.AppendMenu(wx.ID_ANY, "Set Y-axis label as...", ylabel_2D_menu)
                menu.AppendSeparator()
                menu.AppendItem(menu_action_save_heatmap_image_as)
                menu.AppendItem(menu_action_save_1D_data_as)
                menu.AppendItem(menu_action_save_2D_data_as)
                menu.AppendItem(menu_action_delete_item)
                if itemType not in ["Drift time (2D)", "Drift time (2D, processed)"]:
                    menu.PrependItem(menu_action_show_plot_as_mobiligram)
                    menu.PrependItem(menu_action_show_plot_as_chromatogram)
            elif self._document_type == "Drift time (2D, EIC)" and self._item_leaf == self._document_type:
                menu.AppendItem(
                    makeMenuItem(parent=menu, id=ID_docTree_addInteractiveToTextTable, text="Add to text file table")
                )
            elif self._document_type in ["Mass Spectra"]:
                if self._item_leaf == "Annotations":
                    menu.AppendItem(menu_show_annotations_panel)
                    menu.AppendItem(menu_action_show_annotations)
                    menu.AppendItem(menu_action_delete_item)
                elif (self._document_type in ["Mass Spectra"]) and self._item_leaf == "UniDec":
                    menu.AppendItem(menu_action_show_unidec_results)
                    menu.AppendItem(
                        makeMenuItem(
                            parent=menu,
                            id=ID_docTree_save_unidec,
                            text="Save UniDec results ({})".format(self.config.saveExtension),
                        )
                    )
                    menu.AppendItem(menu_action_delete_item)
                elif (self._document_type in ["Mass Spectra"]) and self._item_branch == "UniDec":
                    menu.AppendItem(
                        makeMenuItem(
                            parent=menu, id=ID_docTree_show_unidec, text="Show plot - {}".format(self._item_leaf)
                        )
                    )
                    menu.AppendItem(
                        makeMenuItem(
                            parent=menu,
                            id=ID_docTree_save_unidec,
                            text=f"Save results - {self._item_leaf} ({self.config.saveExtension})",
                        )
                    )
                    menu.AppendItem(menu_action_delete_item)
                elif self._document_type in ["Mass Spectrum" "Mass Spectrum (processed)"]:
                    menu.AppendItem(menu_action_show_plot_spectrum)
                    menu.AppendItem(menu_show_annotations_panel)
                    menu.AppendItem(menu_action_duplicate_annotations)
                    # check if deconvolution results exist
                    if "unidec" in self.currentData:
                        menu.AppendItem(menu_action_show_unidec_results)
                        menu.AppendItem(
                            makeMenuItem(
                                parent=menu,
                                id=ID_docTree_save_unidec,
                                text=f"Save UniDec results ({self.config.saveExtension})",
                                bitmap=None,
                            )
                        )
                    menu.AppendItem(menu_action_process_ms)
                    menu.AppendItem(menu_show_unidec_panel)
                    menu.AppendSeparator()
                    menu.AppendItem(menu_action_save_spectrum_image_as)
                    menu.AppendItem(menu_action_save_data_as)
                    menu.AppendItem(menu_action_delete_item)
                else:
                    if self._item_leaf == "Mass Spectra":
                        menu.AppendItem(menu_show_comparison_panel)
                        menu.AppendItem(menu_action_show_plot_spectrum_waterfall)
                        menu.AppendItem(
                            makeMenuItem(
                                parent=menu,
                                id=ID_docTree_addToMMLTable,
                                text="Add spectra to multiple files panel",
                                bitmap=None,
                            )
                        )
                        menu.AppendSeparator()
                        menu.AppendItem(menu_action_save_data_as)
                        menu.AppendMenu(wx.ID_ANY, "Save to file...", save_data_submenu)
                    elif self._item_leaf != "Mass Spectra" and "UniDec (" not in self._item_leaf and self._indent < 4:
                        menu.AppendItem(menu_action_show_plot_spectrum)
                        menu.AppendItem(menu_show_annotations_panel)
                        menu.AppendItem(menu_action_duplicate_annotations)
                        menu.AppendItem(menu_action_process_ms)
                        menu.AppendItem(menu_show_unidec_panel)
                        menu.AppendSeparator()
                        menu.AppendItem(menu_action_add_spectrum_to_panel)
                        menu.Append(ID_duplicateItem, "Duplicate item")
                        menu.AppendItem(menu_action_rename_item)
                        menu.AppendSeparator()
                        menu.AppendItem(menu_action_save_spectrum_image_as)
                        menu.AppendItem(menu_action_save_data_as)
                    elif self._item_leaf != "Mass Spectra" and "UniDec (" in self._item_leaf:
                        menu.AppendItem(menu_action_show_unidec_results)
                        menu.AppendItem(
                            makeMenuItem(
                                parent=menu,
                                id=ID_docTree_save_unidec,
                                text="Save UniDec results ({})".format(self.config.saveExtension),
                                bitmap=None,
                            )
                        )
                    elif self._item_leaf != "Mass Spectra" and "UniDec (" in self._item_branch:
                        menu.AppendItem(
                            makeMenuItem(
                                parent=menu,
                                id=ID_docTree_save_unidec,
                                text="Save UniDec results ({})".format(self.config.saveExtension),
                                bitmap=None,
                            )
                        )
                    menu.AppendItem(menu_action_delete_item)
            elif itemType == "UniDec" or itemType == "UniDec (processed)":
                menu.AppendItem(menu_action_show_unidec_results)
                menu.AppendItem(
                    makeMenuItem(
                        parent=menu,
                        id=ID_docTree_save_unidec,
                        text="Save UniDec results ({})".format(self.config.saveExtension),
                        bitmap=None,
                    )
                )
                menu.AppendSeparator()
                menu.AppendItem(menu_action_delete_item)
            elif itemType in ["Chromatogram", "Chromatograms (EIC)"]:
                menu.AppendItem(menu_action_show_plot_chromatogram)
                menu.AppendSeparator()
                menu.AppendMenu(wx.ID_ANY, "Set X-axis label as...", xlabel_RT_menu)
                menu.AppendSeparator()
                menu.AppendItem(menu_action_save_chromatogram_image_as)
                menu.AppendItem(menu_action_save_data_as)
                menu.AppendItem(menu_action_delete_item)
            elif itemType in ["Drift time (1D)", "Drift time (1D, EIC)"]:
                menu.AppendItem(menu_action_show_plot_mobilogram)
                menu.AppendSeparator()
                menu.AppendMenu(wx.ID_ANY, "Change x-axis to...", xlabel_1D_menu)
                menu.AppendItem(menu_action_save_mobilogram_image_as)
                menu.AppendItem(menu_action_save_data_as)
                menu.AppendItem(menu_action_delete_item)
            if menu.MenuItemCount > 0:
                menu.AppendSeparator()
            menu.AppendMenu(wx.ID_ANY, "Import data...", load_data_menu)

        # ALL OTHER DATASETS
        elif self._document_type in ["Mass Spectrum", "Mass Spectrum (processed)", "Mass Spectra"]:
            if (
                self._document_type in ["Mass Spectrum", "Mass Spectrum (processed)", "Mass Spectra"]
            ) and self._item_leaf == "Annotations":
                menu.AppendItem(menu_show_annotations_panel)
                menu.AppendItem(menu_action_show_annotations)
                menu.AppendItem(menu_action_delete_item)
            elif (
                self._document_type in ["Mass Spectrum", "Mass Spectrum (processed)", "Mass Spectra"]
            ) and self._item_leaf == "UniDec":
                menu.AppendItem(menu_action_show_unidec_results)
                menu.AppendItem(
                    makeMenuItem(
                        parent=menu,
                        id=ID_docTree_save_unidec,
                        text="Save UniDec results ({})".format(self.config.saveExtension),
                        bitmap=None,
                    )
                )
                menu.AppendItem(menu_action_delete_item)
            elif (
                self._document_type in ["Mass Spectrum", "Mass Spectrum (processed)", "Mass Spectra"]
            ) and self._item_branch == "UniDec":
                menu.AppendItem(
                    makeMenuItem(
                        parent=menu,
                        id=ID_docTree_show_unidec,
                        text="Show plot - {}".format(self._item_leaf),
                        bitmap=None,
                    )
                )
                menu.AppendItem(
                    makeMenuItem(
                        parent=menu,
                        id=ID_docTree_save_unidec,
                        text="Save results - {} ({})".format(self._item_leaf, self.config.saveExtension),
                        bitmap=None,
                    )
                )
                menu.AppendItem(menu_action_delete_item)
            elif self._document_type in ["Mass Spectrum", "Mass Spectrum (processed)"] and self._indent == 2:
                menu.AppendItem(menu_action_show_plot_spectrum)
                menu.AppendItem(menu_show_annotations_panel)
                menu.AppendItem(menu_action_duplicate_annotations)
                menu.AppendItem(menu_show_peak_picker_panel)
                menu.AppendItem(menu_action_process_ms)

                # check if deconvolution results are present
                try:
                    if "unidec" in self.currentData:
                        menu.AppendSeparator()
                        menu.AppendItem(menu_action_show_unidec_results)

                        menu.AppendItem(
                            makeMenuItem(
                                parent=menu,
                                id=ID_docTree_save_unidec,
                                text="Save UniDec results ({})".format(self.config.saveExtension),
                                bitmap=None,
                            )
                        )
                except Exception:
                    pass
                menu.AppendItem(menu_show_unidec_panel)
                menu.AppendSeparator()
                menu.AppendItem(menu_action_save_spectrum_image_as)
                menu.AppendItem(menu_action_save_data_as)
                menu.AppendItem(menu_action_delete_item)
            elif self._item_branch == "Annotations" and self._indent in [4, 5]:
                menu.AppendItem(menu_action_delete_item)
            else:
                if self._item_leaf == "Mass Spectra":
                    menu.AppendItem(menu_show_comparison_panel)
                    menu.AppendItem(menu_action_show_plot_spectrum_waterfall)
                    menu.AppendItem(
                        makeMenuItem(
                            parent=menu,
                            id=ID_docTree_addToMMLTable,
                            text="Add spectra to multiple files panel",
                            bitmap=None,
                        )
                    )
                    menu.AppendItem(menu_action_process_ms_all)
                    menu.AppendSeparator()
                    menu.AppendItem(menu_action_save_data_as)
                    menu.AppendMenu(wx.ID_ANY, "Save to file...", save_data_submenu)
                elif self._item_leaf != "Mass Spectra" and "UniDec (" not in self._item_leaf and self._indent != 4:
                    menu.AppendItem(menu_action_show_plot_spectrum)
                    menu.AppendItem(menu_show_annotations_panel)
                    menu.AppendItem(menu_action_duplicate_annotations)
                    menu.AppendItem(menu_show_peak_picker_panel)
                    menu.AppendItem(menu_action_process_ms)
                    menu.AppendItem(menu_show_unidec_panel)
                    menu.AppendSeparator()
                    menu.AppendItem(menu_action_add_spectrum_to_panel)
                    menu.Append(ID_duplicateItem, "Duplicate item")
                    menu.AppendItem(menu_action_rename_item)
                    menu.AppendSeparator()
                    menu.AppendItem(menu_action_save_spectrum_image_as)
                    menu.AppendItem(menu_action_save_data_as)
                menu.AppendItem(menu_action_delete_item)

        # tandem MS
        elif itemType == "Tandem Mass Spectra" and self._indent == 2:
            menu.AppendItem(
                makeMenuItem(
                    parent=menu,
                    id=ID_docTree_add_mzIdentML,
                    text="Add identification information (.mzIdentML, .mzid, .mzid.gz)",
                    bitmap=None,
                )
            )
        # Sample information
        elif itemType == "Sample information":
            menu.Append(ID_showSampleInfo, "Show sample information")
        # Chromatogram
        elif itemType in ["Chromatogram", "Chromatograms (EIC)"]:
            menu.AppendItem(menu_action_show_plot_chromatogram)
            menu.AppendSeparator()
            menu.AppendMenu(wx.ID_ANY, "Change x-axis to...", xlabel_RT_menu)
            menu.AppendSeparator()
            menu.AppendItem(menu_action_save_chromatogram_image_as)
            menu.AppendItem(menu_action_save_data_as)
            menu.AppendItem(menu_action_delete_item)
        # Drift time (1D)
        elif itemType == "Drift time (1D)":
            menu.AppendItem(menu_action_show_plot_mobilogram)
            menu.AppendSeparator()
            menu.AppendMenu(wx.ID_ANY, "Change x-axis to...", xlabel_1D_menu)
            menu.AppendSeparator()
            menu.AppendItem(menu_action_save_mobilogram_image_as)
            menu.AppendItem(menu_action_save_data_as)
            menu.AppendItem(menu_action_delete_item)
        # Drift time (2D)
        elif itemType in [
            "Drift time (2D)",
            "Drift time (2D, processed)",
            "Drift time (2D, EIC)",
            "Drift time (2D, combined voltages, EIC)",
            "Drift time (2D, processed, EIC)",
        ]:
            # Only if clicked on an item and not header
            if (
                self._document_type in ["Drift time (2D)", "Drift time (2D, processed)"]
                or (self._document_type == "Drift time (2D, EIC)" and self._item_leaf != self._document_type)
                or (
                    self._document_type == "Drift time (2D, combined voltages, EIC)"
                    and self._item_leaf != self._document_type
                )
                or (self._document_type == "Drift time (2D, processed, EIC)" and self._item_leaf != self._document_type)
            ):
                menu.AppendItem(menu_action_show_plot_2D)
                menu.AppendItem(menu_action_show_plot_violin)
                menu.AppendItem(menu_action_show_plot_waterfall)
                menu.AppendItem(menu_action_process_2D)
                menu.AppendSeparator()
                menu.AppendItem(menu_action_assign_charge)
                menu.AppendMenu(wx.ID_ANY, "Set X-axis label as...", xlabel_2D_menu)
                menu.AppendMenu(wx.ID_ANY, "Set Y-axis label as...", ylabel_2D_menu)
                menu.AppendSeparator()
                menu.AppendItem(menu_action_save_heatmap_image_as)
                menu.AppendItem(menu_action_save_1D_data_as)
                menu.AppendItem(menu_action_save_2D_data_as)
                menu.AppendItem(menu_action_delete_item)
                if self._document_type not in ["Drift time (2D)", "Drift time (2D, processed)"]:
                    menu.PrependItem(menu_action_show_plot_as_mobiligram)
                    menu.PrependItem(menu_action_show_plot_as_chromatogram)
                    menu.PrependItem(menu_action_show_highlights)
            # Only if clicked on a header
            else:
                menu.AppendItem(menu_action_process_2D_all)
                menu.AppendSeparator()
                menu.AppendItem(menu_action_save_1D_data_as)
                menu.AppendItem(menu_action_save_2D_data_as)
                menu.AppendItem(menu_action_delete_item)
        # Input data
        elif self._document_type == "Input data":
            if self._document_type == "Input data" and self._item_leaf != self._document_type:
                menu.AppendItem(menu_action_show_plot_2D)
                menu.AppendItem(menu_action_process_2D)
                menu.AppendSeparator()
                menu.AppendMenu(wx.ID_ANY, "Set X-axis label as...", xlabel_2D_menu)
                menu.AppendMenu(wx.ID_ANY, "Set Y-axis label as...", ylabel_2D_menu)
                menu.AppendItem(menu_action_save_heatmap_image_as)
                menu.AppendItem(menu_action_save_data_as)
                menu.AppendItem(menu_action_delete_item)
            # Only if clicked on a header
            else:
                menu.AppendItem(
                    makeMenuItem(parent=menu, id=ID_docTree_addToTextTable, text="Add to text file table", bitmap=None)
                )
                menu.AppendItem(menu_action_save_data_as)
                menu.AppendItem(menu_action_delete_item)
        # Statistical method
        elif self._document_type == "Statistical":
            # Only if clicked on an item and not header
            if self._item_leaf != self._document_type:
                menu.AppendItem(menu_action_show_plot_2D)
                menu.AppendSeparator()
                if plotLabel[0] == "RMSF":
                    menu.Append(ID_saveRMSFImageDoc, "Save image as...")
                elif plotLabel[0] == "RMSD Matrix":
                    menu.Append(ID_saveRMSDmatrixImageDoc, "Save image as...")
                else:
                    menu.AppendItem(menu_action_save_heatmap_image_as)
                menu.AppendItem(menu_action_save_data_as)
                menu.AppendItem(menu_action_delete_item)
                menu.AppendSeparator()
                menu.AppendItem(menu_action_rename_item)
            # Only if on a header
            else:
                menu.AppendItem(menu_action_save_data_as)
                menu.AppendItem(menu_action_delete_item)

        # Drift time (1D) (batch)
        elif itemType in ["Drift time (1D, EIC, DT-IMS)", "Drift time (1D, EIC)"]:
            # Only if clicked on an item and not header
            if self._item_leaf != "Drift time (1D, EIC, DT-IMS)" and itemType != "Drift time (1D, EIC)":
                menu.AppendItem(menu_action_show_highlights)

            if self._item_leaf not in ["Drift time (1D, EIC)", "Drift time (1D, EIC, DT-IMS)"]:
                menu.AppendItem(menu_action_show_plot_mobilogram)
                menu.AppendSeparator()
                menu.AppendMenu(wx.ID_ANY, "Change x-axis to...", xlabel_1D_menu)
                menu.AppendItem(menu_action_assign_charge)
                menu.AppendSeparator()
                menu.AppendItem(menu_action_save_mobilogram_image_as)
                menu.AppendItem(menu_action_save_data_as)
                menu.AppendItem(menu_action_delete_item)
            # Only if on a header
            else:
                menu.AppendItem(menu_action_save_data_as)
                menu.AppendItem(menu_action_delete_item)
        elif itemType == "Chromatograms (combined voltages, EIC)":
            # Only if clicked on an item and not header
            if not self._item_leaf == "Chromatograms (combined voltages, EIC)":
                menu.AppendItem(menu_action_show_plot_chromatogram)
                menu.AppendSeparator()
                menu.AppendItem(menu_action_assign_charge)
                menu.AppendSeparator()
                menu.Append(ID_saveRTImageDoc, "Save image as...")
                menu.AppendItem(menu_action_save_data_as)
                menu.AppendItem(menu_action_delete_item)
            # Only if on a header
            else:
                menu.AppendItem(menu_action_save_data_as)
                menu.AppendItem(menu_action_delete_item)
        elif itemType == "Calibration Parameters":
            menu.AppendItem(menu_action_save_data_as)
            menu.AppendItem(menu_action_delete_item)
        elif itemType == "Calibration peaks" or itemType == "Calibrants":
            if self._document_type != self._item_leaf:
                menu.Append(menu_action_show_plot)
                menu.AppendSeparator()
                menu.AppendItem(menu_action_delete_item)
        elif itemType == "Overlay":
            if self._document_type != self._item_leaf:
                if self.splitText[0] in [
                    "Waterfall (Raw)",
                    "Waterfall (Processed)",
                    "Waterfall (Fitted)",
                    "Waterfall (Deconvoluted MW)",
                    "Waterfall (Charge states)",
                ]:
                    menu.AppendItem(menu_action_show_plot)
                    if self.splitText[0] in ["Waterfall (Raw)", "Waterfall (Processed)"]:
                        menu.AppendItem(menu_show_annotations_panel)
                elif self.splitText[0] not in ["1D", "RT"]:
                    menu.AppendItem(menu_action_show_plot_2D)
                else:
                    menu.AppendItem(menu_action_show_plot)
                # Depending which plot is being saved, different event ID is used
                if self.splitText[0] == "RMSF":
                    menu.Append(ID_saveRMSFImageDoc, "Save image as...")
                elif self.splitText[0] == "1D":
                    menu.AppendItem(menu_action_save_mobilogram_image_as)
                elif self.splitText[0] == "RT":
                    menu.Append(ID_saveRTImageDoc, "Save image as...")
                elif self.splitText[0] == "Mask" or plotLabel[0] == "Transparent":
                    menu.Append(ID_saveOverlayImageDoc, "Save image as...")
                elif self.splitText[0] in [
                    "Waterfall (Raw)",
                    "Waterfall (Processed)",
                    "Waterfall (Fitted)",
                    "Waterfall (Deconvoluted MW)",
                    "Waterfall (Charge states)",
                ]:
                    menu.Append(ID_saveWaterfallImageDoc, "Save image as...")
                else:
                    menu.AppendItem(menu_action_save_heatmap_image_as)
                menu.AppendItem(menu_action_delete_item)
                menu.AppendSeparator()
                menu.AppendItem(menu_action_rename_item)
            # Header only
            else:
                menu.AppendSeparator()
                menu.AppendItem(menu_action_delete_item)
        elif itemType == "DT/MS":
            menu.AppendItem(menu_action_show_plot_2D)
            menu.AppendItem(menu_action_process_2D)
            menu.AppendSeparator()
            menu.AppendItem(
                makeMenuItem(
                    parent=menu,
                    id=ID_docTree_action_open_extractDTMS,
                    text="Open DT/MS extraction panel...",
                    bitmap=None,
                )
            )

            menu.AppendSeparator()
            menu.AppendMenu(wx.ID_ANY, "Set Y-axis label as...", ylabel_DTMS_menu)
            menu.AppendSeparator()
            menu.Append(ID_saveMZDTImage, "Save image as...")
            menu.AppendItem(menu_action_save_data_as)
        else:
            menu.Append(ID_docTree_add_MS_to_interactive, "Add mass spectra")
            menu.Append(ID_docTree_add_other_to_interactive, "Add other...")

        if menu.MenuItemCount > 0:
            menu.AppendSeparator()

        if self._indent == 1:
            menu.Append(ID_docTree_show_refresh_document, "Refresh document")
            menu.AppendItem(
                makeMenuItem(
                    parent=menu,
                    id=ID_docTree_duplicate_document,
                    text="Duplicate document\tShift+D",
                    bitmap=self.icons.iconsLib["duplicate_16"],
                )
            )
            menu.AppendItem(menu_action_rename_item)
            menu.AppendSeparator()

        menu.AppendMenu(wx.ID_ANY, "Action...", action_menu)
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_openDocInfo,
                text="Notes, Information, Labels...\tCtrl+I",
                bitmap=self.icons.iconsLib["info16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_goToDirectory,
                text="Go to folder...\tCtrl+G",
                bitmap=self.icons.iconsLib["folder_path_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_saveAsInteractive,
                text="Open interactive output panel...\tShift+Z",
                bitmap=self.icons.iconsLib["bokehLogo_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_saveDocument,
                text="Save document to file\tCtrl+P",
                bitmap=self.icons.iconsLib["pickle_16"],
            )
        )
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(parent=menu, id=ID_removeDocument, text="Delete document", bitmap=self.icons.iconsLib["bin16"])
        )
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    # TODO: FIXME
    def on_change_xy_values_and_labels(self, evt):
        """
        Change xy-axis labels
        """

        # Get current document info
        document_title, selectedItem, selectedText = self.on_enable_document(getSelected=True)
        indent = self.get_item_indent(selectedItem)
        selectedItemParentText = None
        if indent > 2:
            __, selectedItemParentText = self.getParentItem(selectedItem, 2, getSelected=True)
        else:
            pass
        document = self.presenter.documentsDict[document_title]

        # get event
        evtID = evt.GetId()

        # Determine which dataset is used
        if selectedText is None:
            data = document.IMS2D
        elif selectedText == "Drift time (2D)":
            data = document.IMS2D
        elif selectedText == "Drift time (2D, processed)":
            data = document.IMS2Dprocess
        elif selectedItemParentText == "Drift time (2D, EIC)" and selectedText is not None:
            data = document.IMS2Dions[selectedText]
        elif selectedItemParentText == "Drift time (2D, combined voltages, EIC)" and selectedText is not None:
            data = document.IMS2DCombIons[selectedText]
        elif selectedItemParentText == "Drift time (2D, processed, EIC)" and selectedText is not None:
            data = document.IMS2DionsProcess[selectedText]
        elif selectedItemParentText == "Input data" and selectedText is not None:
            data = document.IMS2DcompData[selectedText]

        # 1D data
        elif selectedText == "Drift time (1D)":
            data = document.DT
        elif selectedItemParentText == "Drift time (1D, EIC)" and selectedText is not None:
            data = document.multipleDT[selectedText]

        # chromatograms
        elif selectedText == "Chromatogram":
            data = document.RT
        elif selectedItemParentText == "Chromatograms (EIC)" and selectedText is not None:
            data = document.multipleRT[selectedText]
        elif selectedItemParentText == "Chromatograms (combined voltages, EIC)" and selectedText is not None:
            data = document.IMSRTCombIons[selectedText]

        # DTMS
        elif selectedText == "DT/MS":
            data = document.DTMZ

        # try to get dataset object
        try:
            docItem = self.getItemByData(data)
        except Exception:
            docItem = False

        # Add default values
        if "defaultX" not in data:
            data["defaultX"] = {"xlabels": data["xlabels"], "xvals": data["xvals"]}
        if "defaultY" not in data:
            data["defaultY"] = {"ylabels": data.get("ylabels", "Intensity"), "yvals": data["yvals"]}

        # If either label is none, then ignore it
        newXlabel, newYlabel = None, None
        restoreX, restoreY = False, False

        # Determine what the new label should be
        if evtID in [
            ID_xlabel_2D_scans,
            ID_xlabel_2D_colVolt,
            ID_xlabel_2D_actVolt,
            ID_xlabel_2D_labFrame,
            ID_xlabel_2D_massToCharge,
            ID_xlabel_2D_actLabFrame,
            ID_xlabel_2D_massToCharge,
            ID_xlabel_2D_mz,
            ID_xlabel_2D_wavenumber,
            ID_xlabel_2D_wavenumber,
            ID_xlabel_2D_custom,
            ID_xlabel_2D_charge,
            ID_xlabel_2D_ccs,
            ID_xlabel_2D_retTime_min,
            ID_xlabel_2D_time_min,
            ID_xlabel_2D_restore,
        ]:

            # If changing X-labels
            newXlabel = "Scans"
            restoreX = False
            if evtID == ID_xlabel_2D_scans:
                newXlabel = "Scans"
            elif evtID == ID_xlabel_2D_time_min:
                newXlabel = "Time (min)"
            elif evtID == ID_xlabel_2D_retTime_min:
                newXlabel = "Retention time (min)"
            elif evtID == ID_xlabel_2D_colVolt:
                newXlabel = "Collision Voltage (V)"
            elif evtID == ID_xlabel_2D_actVolt:
                newXlabel = "Activation Voltage (V)"
            elif evtID == ID_xlabel_2D_labFrame:
                newXlabel = "Lab Frame Energy (eV)"
            elif evtID == ID_xlabel_2D_actLabFrame:
                newXlabel = "Activation Energy (eV)"
            elif evtID == ID_xlabel_2D_massToCharge:
                newXlabel = "Mass-to-charge (Da)"
            elif evtID == ID_xlabel_2D_mz:
                newXlabel = "m/z (Da)"
            elif evtID == ID_xlabel_2D_wavenumber:
                newXlabel = "Wavenumber (cm⁻¹)"
            elif evtID == ID_xlabel_2D_charge:
                newXlabel = "Charge"
            elif evtID == ID_xlabel_2D_ccs:
                newXlabel = "Collision Cross Section (Å²)"
            elif evtID == ID_xlabel_2D_custom:
                newXlabel = DialogSimpleAsk("Please type in your new label...")
            elif evtID == ID_xlabel_2D_restore:
                newXlabel = data["defaultX"]["xlabels"]
                restoreX = True
            elif newXlabel == "" or newXlabel is None:
                newXlabel = "Scans"

        if evtID in [
            ID_ylabel_2D_bins,
            ID_ylabel_2D_ms,
            ID_ylabel_2D_ms_arrival,
            ID_ylabel_2D_ccs,
            ID_ylabel_2D_restore,
            ID_ylabel_2D_custom,
        ]:
            # If changing Y-labels
            newYlabel = "Drift time (bins)"
            restoreY = False
            if evtID == ID_ylabel_2D_bins:
                newYlabel = "Drift time (bins)"
            elif evtID == ID_ylabel_2D_ms:
                newYlabel = "Drift time (ms)"
            elif evtID == ID_ylabel_2D_ms_arrival:
                newYlabel = "Arrival time (ms)"
            elif evtID == ID_ylabel_2D_ccs:
                newYlabel = "Collision Cross Section (Å²)"
            elif evtID == ID_ylabel_2D_custom:
                newYlabel = DialogSimpleAsk("Please type in your new label...")
            elif evtID == ID_ylabel_2D_restore:
                newYlabel = data["defaultY"]["ylabels"]
                restoreY = True
            elif newYlabel == "" or newYlabel is None:
                newYlabel = "Drift time (bins)"

        # 1D data
        if evtID in [
            ID_xlabel_1D_bins,
            ID_xlabel_1D_ms,
            ID_xlabel_1D_ms_arrival,
            ID_xlabel_1D_ccs,
            ID_xlabel_1D_restore,
        ]:
            newXlabel = "Drift time (bins)"
            restoreX = False
            if evtID == ID_xlabel_1D_bins:
                newXlabel = "Drift time (bins)"
            elif evtID == ID_xlabel_1D_ms:
                newXlabel = "Drift time (ms)"
            elif evtID == ID_xlabel_1D_ms_arrival:
                newXlabel = "Arrival time (ms)"
            elif evtID == ID_xlabel_1D_ccs:
                newXlabel = "Collision Cross Section (Å²)"
            elif evtID == ID_xlabel_1D_restore:
                newXlabel = data["defaultX"]["xlabels"]
                restoreX = True

        # 1D data
        if evtID in [ID_xlabel_RT_scans, ID_xlabel_RT_time_min, ID_xlabel_RT_retTime_min, ID_xlabel_RT_restore]:
            newXlabel = "Drift time (bins)"
            restoreX = False
            if evtID == ID_xlabel_RT_scans:
                newXlabel = "Scans"
            elif evtID == ID_xlabel_RT_time_min:
                newXlabel = "Time (min)"
            elif evtID == ID_xlabel_RT_retTime_min:
                newXlabel = "Retention time (min)"
            elif evtID == ID_xlabel_RT_restore:
                newXlabel = data["defaultX"]["xlabels"]
                restoreX = True

        # DT/MS
        if evtID in [ID_ylabel_DTMS_bins, ID_ylabel_DTMS_ms, ID_ylabel_DTMS_ms_arrival, ID_ylabel_DTMS_restore]:
            newYlabel = "Drift time (bins)"
            restoreX = False
            if evtID == ID_ylabel_DTMS_bins:
                newYlabel = "Drift time (bins)"
            elif evtID == ID_ylabel_DTMS_ms:
                newYlabel = "Drift time (ms)"
            elif evtID == ID_ylabel_DTMS_ms_arrival:
                newYlabel = "Arrival time (ms)"
            elif evtID == ID_ylabel_DTMS_restore:
                newYlabel = data["defaultY"]["ylabels"]
                restoreY = True
            elif newYlabel == "" or newYlabel is None:
                newYlabel = "Drift time (bins)"

        if restoreX:
            newXvals = data["defaultX"]["xvals"]
            data["xvals"] = newXvals
            data["xlabels"] = newXlabel

        if restoreY:
            newYvals = data["defaultY"]["yvals"]
            data["yvals"] = newYvals
            data["ylabels"] = newYlabel

        # Change labels
        if newXlabel is not None:
            oldXLabel = data["xlabels"]
            data["xlabels"] = newXlabel  # Set new x-label
            newXvals = self.on_change_xy_axis(
                data["xvals"],
                oldXLabel,
                newXlabel,
                charge=data.get("charge", 1),
                pusherFreq=document.parameters.get("pusherFreq", 1000),
                scanTime=document.parameters.get("scanTime", 1.0),
                defaults=data["defaultX"],
            )
            data["xvals"] = newXvals  # Set new x-values

        if newYlabel is not None:
            oldYLabel = data["ylabels"]
            data["ylabels"] = newYlabel
            newYvals = self.on_change_xy_axis(
                data["yvals"],
                oldYLabel,
                newYlabel,
                pusherFreq=document.parameters.get("pusherFreq", 1000),
                scanTime=document.parameters.get("scanTime", 1.0),
                defaults=data["defaultY"],
            )
            data["yvals"] = newYvals

        expand_item = "document"
        expand_item_title = None
        replotID = evtID
        # Replace data in the dictionary
        if selectedText is None:
            document.IMS2D = data
            replotID = ID_showPlotDocument
        elif selectedText == "Drift time (2D)":
            document.IMS2D = data
            replotID = ID_showPlotDocument
        elif selectedText == "Drift time (2D, processed)":
            document.IMS2Dprocess = data
            replotID = ID_showPlotDocument
        elif selectedItemParentText == "Drift time (2D, EIC)" and selectedText is not None:
            document.IMS2Dions[selectedText] = data
            expand_item, expand_item_title = "ions", selectedText
            replotID = ID_showPlotDocument
        elif selectedItemParentText == "Drift time (2D, combined voltages, EIC)" and selectedText is not None:
            document.IMS2DCombIons[selectedText] = data
            expand_item, expand_item_title = "combined_ions", selectedText
            replotID = ID_showPlotDocument
        elif selectedItemParentText == "Drift time (2D, processed, EIC)" and selectedText is not None:
            document.IMS2DionsProcess[selectedText] = data
            expand_item, expand_item_title = "processed_ions", selectedText
            replotID = ID_showPlotDocument
        elif selectedItemParentText == "Input data" and selectedText is not None:
            document.IMS2DcompData[selectedText] = data
            expand_item_title = selectedText
            replotID = ID_showPlotDocument

        # 1D data
        elif selectedText == "Drift time (1D)":
            document.DT = data
        elif selectedItemParentText == "Drift time (1D, EIC)" and selectedText is not None:
            document.multipleDT[selectedText] = data
            expand_item, expand_item_title = "ions_1D", selectedText

        # Chromatograms
        elif selectedText == "Chromatogram":
            document.RT = data
            replotID = ID_showPlotDocument
        elif selectedItemParentText == "Chromatograms (EIC)" and selectedText is not None:
            data = document.multipleRT[selectedText] = data
        elif selectedItemParentText == "Chromatograms (combined voltages, EIC)" and selectedText is not None:
            data = document.IMSRTCombIons[selectedText] = data

        # DT/MS
        elif selectedText == "DT/MS":
            document.DTMZ = data
        else:
            document.IMS2D

        # update document
        if docItem is not False:
            try:
                self.SetPyData(docItem, data)
                self.presenter.documentsDict[document.title] = document
            except Exception:
                self.data_handling.on_update_document(document, expand_item, expand_item_title=expand_item_title)
        else:
            self.data_handling.on_update_document(document, expand_item, expand_item_title=expand_item_title)

        # Try to plot that data
        try:
            self.on_show_plot(evt=replotID)
        except Exception:
            pass

    def on_change_xy_axis(self, data, oldLabel, newLabel, charge=1, pusherFreq=1000, scanTime=1.0, defaults=None):
        """
        This function changes the X and Y axis labels
        Parameters
        ----------
        data : array/list, 1D array of old X/Y-axis labels
        oldLabel : string, old X/Y-axis labels
        newLabel : string, new X/Y-axis labels
        charge : integer, charge of the ion
        pusherFreq : float, pusher frequency
        mode : string, 1D/2D modes available
        Returns
        -------
        newVals : array/list, 1D array of new X/Y-axis labels
        """

        # Make sure we have charge and pusher values
        if charge == "None" or charge == "":
            charge = 1
        else:
            charge = str2int(charge)

        if pusherFreq == "None" or pusherFreq == "":
            pusherFreq = 1000
        else:
            pusherFreq = str2num(pusherFreq)

        msg = "Currently just changing label. Proper conversion will be coming soon"
        # Check whether labels were changed
        if oldLabel != newLabel:
            # Convert Y-axis labels
            if oldLabel == "Drift time (bins)" and newLabel in ["Drift time (ms)", "Arrival time (ms)"]:
                newVals = (data * pusherFreq) / 1000
                return newVals
            elif oldLabel in ["Drift time (ms)", "Arrival time (ms)"] and newLabel == "Drift time (bins)":
                newVals = (data / pusherFreq) * 1000
                return newVals
            elif oldLabel in ["Drift time (ms)", "Arrival time (ms)"] and newLabel == "Collision Cross Section (Å²)":
                self.presenter.onThreading(None, (msg, 4, 7), action="updateStatusbar")
                newVals = data
            elif oldLabel == "Collision Cross Section (Å²)" and newLabel in ["Drift time (ms)", "Arrival time (ms)"]:
                self.presenter.onThreading(None, (msg, 4, 7), action="updateStatusbar")
                newVals = data
            elif oldLabel == "Drift time (bins)" and newLabel == "Collision Cross Section (Å²)":
                self.presenter.onThreading(None, (msg, 4, 7), action="updateStatusbar")
                newVals = data
            elif oldLabel == "Collision Cross Section (Å²)" and newLabel == "Drift time (bins)":
                self.presenter.onThreading(None, (msg, 4, 7), action="updateStatusbar")
                newVals = data
            elif (
                oldLabel == "Drift time (ms)"
                and newLabel == "Arrival time (ms)"
                or oldLabel == "Arrival time (ms)"
                and newLabel == "Drift time (ms)"
            ):
                newVals = data
            else:
                newVals = data

            # Convert X-axis labels
            # Convert CV --> LFE
            if oldLabel in ["Collision Voltage (V)", "Activation Energy (V)"] and newLabel in [
                "Lab Frame Energy (eV)",
                "Activation Energy (eV)",
            ]:
                if isinstance(data, list):
                    newVals = [value * charge for value in data]
                else:
                    newVals = data * charge
            # If labels involve no conversion
            elif (
                (oldLabel == "Activation Energy (V)" and newLabel == "Collision Voltage (V)")
                or (oldLabel == "Collision Voltage (V)" and newLabel == "Activation Energy (V)")
                or (oldLabel == "Lab Frame Energy (eV)" and newLabel == "Activation Energy (eV)")
                or (oldLabel == "Activation Energy (eV)" and newLabel == "Lab Frame Energy (eV)")
            ):
                if isinstance(data, list):
                    newVals = [value for value in data]
                else:
                    newVals = data
            # Convert Lab frame energy --> collision voltage
            elif newLabel in ["Collision Voltage (V)", "Activation Energy (V)"] and oldLabel in [
                "Lab Frame Energy (eV)",
                "Activation Energy (eV)",
            ]:
                if isinstance(data, list):
                    newVals = [value / charge for value in data]
                else:
                    newVals = data / charge
            # Convert LFE/CV --> scans
            elif newLabel == "Scans" and oldLabel in [
                "Lab Frame Energy (eV)",
                "Collision Voltage (V)",
                "Activation Energy (eV)",
                "Activation Energy (V)",
            ]:
                newVals = 1 + np.arange(len(data))
            # Convert Scans --> LFE/CV
            elif oldLabel == "Scans" and newLabel in [
                "Lab Frame Energy (eV)",
                "Collision Voltage (V)",
                "Activation Energy (eV)",
                "Activation Energy (V)",
            ]:
                # Check if defaults were provided
                if defaults is None:
                    newVals = data
                else:
                    if defaults["xlabels"] == "Lab Frame Energy (eV)" or defaults["xlabels"] == "Collision Voltage (V)":
                        newVals = defaults["xvals"]
                    else:
                        newVals = data
            # Convert Scans -> Time
            elif newLabel in ["Retention time (min)", "Time (min)"] and oldLabel == "Scans":
                newVals = (data * scanTime) / 60
                return newVals
            elif oldLabel in ["Retention time (min)", "Time (min)"] and newLabel == "Scans":
                newVals = (data / scanTime) * 60
                return newVals
            elif oldLabel in ["Retention time (min)", "Time (min)"] and newLabel == [
                "Retention time (min)",
                "Time (min)",
            ]:
                return data

            else:
                newVals = data

            # Return new values
            return newVals
        # labels were not changed
        else:
            return data

    def onAddToTable(self, evt):
        evtID = evt.GetId()

        filelist = self.presenter.view.panelMML.peaklist
        textlist = self.presenter.view.panelMultipleText.peaklist
        if evtID == ID_docTree_addToMMLTable:
            data = self._document_data.multipleMassSpectrum
            document_title = self._document_data.title
            n_rows = len(data)
            colors = self.panel_plot.on_change_color_palette(None, n_colors=n_rows, return_colors=True)
            for i, key in enumerate(data):
                count = filelist.GetItemCount()
                label = data[key].get("label", os.path.splitext(key)[0])
                color = data[key].get("color", colors[i])
                if np.sum(color) > 4:
                    color = convertRGB255to1(color)
                filelist.Append([key, data[key].get("trap", 0), document_title, label])
                color = convertRGB1to255(color)
                filelist.SetItemBackgroundColour(count, color)
                filelist.SetItemTextColour(count, determineFontColor(color, return_rgb=True))

        elif evtID == ID_docTree_addOneToMMLTable:
            data = self._document_data.multipleMassSpectrum
            count = filelist.GetItemCount()
            colors = self.panel_plot.on_change_color_palette(None, n_colors=count + 1, return_colors=True)
            key = self._item_leaf
            document_title = self._document_data.title
            label = data.get("label", key)
            color = data[key].get("color", colors[-1])
            if np.sum(color) > 4:
                color = convertRGB255to1(color)
            filelist.Append([key, data[key].get("trap", 0), document_title, label])
            color = convertRGB1to255(color)
            filelist.SetItemBackgroundColour(count, color)
            filelist.SetItemTextColour(count, determineFontColor(color, return_rgb=True))

        elif evtID == ID_docTree_addToTextTable:
            data = self._document_data.IMS2DcompData
            document_title = self._document_data.title
            n_rows = len(data)
            colors = self.panel_plot.on_change_color_palette(None, n_colors=n_rows, return_colors=True)
            for i, key in enumerate(data):
                count = textlist.GetItemCount()
                label = data[key].get("label", os.path.splitext(key)[0])
                color = data[key].get("color", colors[i])
                if np.sum(color) > 4:
                    color = convertRGB255to1(color)
                minCE, maxCE = np.min(data[key]["xvals"]), np.max(data[key]["xvals"])
                document_label = "{}: {}".format(document_title, key)
                textlist.Append(
                    [
                        minCE,
                        maxCE,
                        data[key]["charge"],
                        color,
                        data[key]["cmap"],
                        data[key]["alpha"],
                        data[key]["mask"],
                        label,
                        data[key]["zvals"].shape,
                        document_label,
                    ]
                )
                color = convertRGB1to255(color)
                textlist.SetItemBackgroundColour(count, color)
                textlist.SetItemTextColour(count, determineFontColor(color, return_rgb=True))

        elif evtID == ID_docTree_addInteractiveToTextTable:
            data = self._document_data.IMS2Dions
            document_title = self._document_data.title
            n_rows = len(data)
            colors = self.panel_plot.on_change_color_palette(None, n_colors=n_rows, return_colors=True)
            for i, key in enumerate(data):
                count = textlist.GetItemCount()
                label = data[key].get("label", os.path.splitext(key)[0])
                color = data[key].get("color", colors[i])
                if np.sum(color) > 4:
                    color = convertRGB255to1(color)
                minCE, maxCE = np.min(data[key]["xvals"]), np.max(data[key]["xvals"])
                document_label = "{}: {}".format(document_title, key)
                textlist.Append(
                    [
                        "",
                        minCE,
                        maxCE,
                        data[key].get("charge", ""),
                        color,
                        data[key]["cmap"],
                        data[key]["alpha"],
                        data[key]["mask"],
                        label,
                        data[key]["zvals"].shape,
                        document_label,
                    ]
                )
            color = convertRGB1to255(color)
            textlist.SetItemBackgroundColour(count, color)
            textlist.SetItemTextColour(count, determineFontColor(color, return_rgb=True))

        if evtID in [ID_docTree_addToMMLTable, ID_docTree_addOneToMMLTable]:
            # sort items
            self.presenter.view.panelMML.OnSortByColumn(column=1, overrideReverse=True)
            self.presenter.view.panelMML.onRemoveDuplicates(None)
            self.presenter.view.on_toggle_panel(evt=ID_window_multipleMLList, check=True)

        elif evtID in [ID_docTree_addToTextTable, ID_docTree_addOneToTextTable, ID_docTree_addInteractiveToTextTable]:
            # sort items
            self.presenter.view.panelMultipleText.onRemoveDuplicates(None)
            self.presenter.view.on_toggle_panel(evt=ID_window_textList, check=True)

    def onShowMassSpectra(self, evt):

        data = self._document_data.multipleMassSpectrum
        spectra_count = len(list(data.keys()))
        if spectra_count > 50:
            dlg = DialogBox(
                exceptionTitle="Would you like to continue?",
                exceptionMsg="There are {} mass spectra in this document. Would you like to continue?".format(
                    spectra_count
                ),
                type="Question",
            )
            if dlg == wx.ID_NO:
                msg = "Cancelled was operation"
                self.presenter.view.SetStatusText(msg, 3)
                return

        # Check for energy
        energy_name = []
        for key in data:
            energy_name.append([key, data[key].get("trap", 0)])
        # sort
        energy_name.sort(key=itemgetter(1))

        names, xvals_list, yvals_list = [], [], []
        for row in energy_name:
            key = row[0]
            xvals_list.append(data[key]["xvals"])
            yvals_list.append(data[key]["yvals"])
            names.append(key)

        kwargs = {"show_y_labels": True, "labels": names}
        self.panel_plot.on_plot_waterfall(
            xvals_list, yvals_list, None, colors=[], xlabel="m/z", ylabel="", set_page=True, **kwargs
        )

    def _collect_mass_spectra_info(self):
        document_list, document_spectrum_list = [], {}
        count = 0
        for document_title in self.presenter.documentsDict:
            document_spectrum_list[document_title] = []
            if self.presenter.documentsDict[document_title].gotMultipleMS:
                for key in self.presenter.documentsDict[document_title].multipleMassSpectrum:
                    document_spectrum_list[document_title].append(key)
                    count += 1
            if self.presenter.documentsDict[document_title].gotMS:
                document_spectrum_list[document_title].append("Mass Spectrum")
                count += 1
            if self.presenter.documentsDict[document_title].smoothMS:
                document_spectrum_list[document_title].append("Mass Spectrum (processed)")
                count += 1

            # clean anything that is empty from the list
            if len(document_spectrum_list[document_title]) > 0:
                document_list.append(document_title)
            else:
                del document_spectrum_list[document_title]

        return count, document_list, document_spectrum_list

    def onCompareMS(self, evt):
        """ Open panel where user can select mas spectra to compare """
        from widgets.panel_signal_comparison_viewer import PanelSignalComparisonViewer

        if self._item_id is None:
            return

        count, document_list, document_spectrum_list = self._collect_mass_spectra_info()

        if count < 2:
            msg = "There must be at least two mass spectra to compare!"
            self.presenter.onThreading(None, (msg, 4, 5), action="updateStatusbar")
            return

        try:
            document_title = self._document_data.title
        except AttributeError:
            document_title = document_list[0]

        kwargs = {
            "current_document": document_title,
            "document_list": document_list,
            "document_spectrum_list": document_spectrum_list,
        }

        self.compareMSDlg = PanelSignalComparisonViewer(self.parent, self.presenter, self.config, self.icons, **kwargs)
        self.compareMSDlg.Show()

    def on_process_2D(self, evt):
        """Process clicked heatmap item"""

        document, data, query = self._on_event_get_mobility_chromatogram_data()

        self.on_open_process_2D_settings(
            data=data, document=document, document_title=document.title, dataset_type=query[1], dataset_name=query[2]
        )

    def on_process_all_2D(self, evt):
        """Process all clicked heatmap items"""

        document, data, query = self._on_event_get_mobility_chromatogram_data()
        self.on_open_process_2D_settings(
            data=data,
            document=document,
            document_title=document.title,
            dataset_type=query[1],
            dataset_name=query[2],
            disable_plot=True,
            disable_process=False,
            process_all=True,
        )

    def on_open_process_2D_settings(self, **kwargs):
        """Open heatmap processing settings"""
        from gui_elements.panel_process_heatmap import PanelProcessHeatmap

        panel = PanelProcessHeatmap(self.presenter.view, self.presenter, self.config, self.icons, **kwargs)
        panel.Show()

    def on_process_MS(self, evt, **kwargs):
        """Process clicked mass spectrum item"""
        document, data, dataset = self._on_event_get_mass_spectrum(**kwargs)
        self.on_open_process_MS_settings(
            mz_data=data, document=document, document_title=document.title, dataset_name=dataset
        )

    def on_process_MS_all(self, evt, **kwargs):
        """Process all clicked mass spectra items"""
        document, data, dataset = self._on_event_get_mass_spectrum(**kwargs)
        self.on_open_process_MS_settings(
            mz_data=data,
            document=document,
            document_title=document.title,
            dataset_name=dataset,
            disable_plot=True,
            disable_process=False,
            process_all=True,
        )

    def on_open_process_MS_settings(self, **kwargs):
        """Open mass spectrum processing settings"""
        from gui_elements.panel_process_spectrum import PanelProcessMassSpectrum

        panel = PanelProcessMassSpectrum(self.presenter.view, self.presenter, self.config, self.icons, **kwargs)
        panel.Show()

    def onProcess(self, evt=None):
        if self._document_data is None:
            return

        # TODO: This function needs to be fixed before next release

    #         if self._document_type == 'Mass Spectrum': pass
    #         elif any(self._document_type in itemType for itemType in ['Drift time (2D)', 'Drift time (2D, processed)',
    #                                                             'Drift time (2D, EIC)',
    #                                                             'Drift time (2D, combined voltages, EIC)',
    #                                                             'Drift time (2D, processed, EIC)',
    #                                                             'Input data', 'Statistical']):
    #             self.presenter.process2Ddata2()
    #             self_set_pageSetSelection(self.config.panelNames['2D'])
    #
    #         elif self._document_type == 'DT/MS':
    #             self.presenter.process2Ddata2(mode='MSDT')
    #             self.panel_plot._set_page(self.config.panelNames['MZDT'])

    def onShow_and_SavePlot(self, evt):
        """
        This function replots selected item and subsequently saves said item to
        figure
        """

        # Show plot first
        self.on_show_plot(evt=None, save_image=True)

    def onDuplicateItem(self, evt):
        evtID = evt.GetId()
        if evtID == ID_duplicateItem:
            if self._document_type == "Mass Spectra" and self._item_leaf != "Mass Spectra":
                # Change document tree
                title = self._document_data.title
                docItem = self.getItemByData(self.presenter.documentsDict[title].multipleMassSpectrum[self._item_leaf])
                copy_name = "{} - copy".format(self._item_leaf)
                # Change dictionary key
                self.presenter.documentsDict[title].multipleMassSpectrum[copy_name] = (
                    self.presenter.documentsDict[self.title].multipleMassSpectrum[self._item_leaf].copy()
                )
                document = self.presenter.documentsDict[title]
                self.data_handling.on_update_document(document, "document")
                self.Expand(docItem)
        # duplicate document
        elif evtID == ID_docTree_duplicate_document:
            document = self.data_handling.on_duplicate_document()
            document.title = "{} - copy".format(document.title)
            self.data_handling._load_document_data(document)

    #             self.data_handling.on_update_document(document, "document")

    # TODO: should restore items to various side panels

    def onRenameItem(self, evt):

        if self._document_data is None:
            return

        current_name = None
        prepend_name = False
        if self._indent == 1 and self._item_leaf is None:
            prepend_name = False
        elif self._document_type == "Statistical" and self._item_leaf != "Statistical":
            prepend_name = True
        elif self._document_type == "Overlay" and self._item_leaf != "Overlay":
            prepend_name = True
        elif self._document_type == "Mass Spectra" and self._item_leaf != "Mass Spectra":
            current_name = self._item_leaf
        elif self._document_data.dataType == "Type: Interactive":
            if self._document_type not in ["Drift time (2D, EIC)"]:
                return
            current_name = self._item_leaf
        else:
            return

        if current_name is None:
            try:
                current_name = re.split("-|,|:|__", self._item_leaf.replace(" ", ""))[0]
            except AttributeError:
                current_name = self._document_data.title

        if current_name == "Grid(nxn)":
            current_name = "Grid (n x n)"
        elif current_name == "Grid(2":
            current_name = "Grid (2->1)"
        elif current_name == "RMSDMatrix":
            current_name = "RMSD Matrix"
        elif current_name == "Waterfall(Raw)":
            current_name = "Waterfall (Raw)"
        elif current_name == "Waterfall(Processed)":
            current_name = "Waterfall (Processed)"
        elif current_name == "Waterfall(Fitted)":
            current_name = "Waterfall (Fitted)"
        elif current_name == "Waterfall(DeconvolutedMW)":
            current_name = "Waterfall (Deconvoluted MW)"
        elif current_name == "Waterfalloverlay":
            current_name = "Waterfall overlay"

        kwargs = {"current_name": current_name, "prepend_name": prepend_name}
        renameDlg = DialogRenameObject(self, self.presenter, self.title, **kwargs)
        renameDlg.CentreOnScreen()
        renameDlg.ShowModal()
        new_name = renameDlg.new_name

        if new_name == current_name:
            print("Names are the same - ignoring")
        elif new_name == "" or new_name is None:
            print("Incorrect name")
        else:
            # Actual new name, prepended
            if self._indent == 1:
                # Change document tree
                docItem = self.getItemByData(self.presenter.documentsDict[current_name])
                document = self.presenter.documentsDict[current_name]
                document.title = new_name
                docItem.title = new_name
                parent = self.GetItemParent(docItem)
                del self.presenter.documentsDict[current_name]
                self.SetItemText(docItem, new_name)
                # Change dictionary key
                self.data_handling.on_update_document(document, "document")
                self.Expand(docItem)

                # check if item is in other panels
                # TODO: implement for other panels
                try:
                    self.presenter.view.panelMML.onRenameItem(current_name, new_name, item_type="document")
                except Exception:
                    pass
                try:
                    self.presenter.view.panelMultipleIons.onRenameItem(current_name, new_name, item_type="document")
                except Exception:
                    pass
            #                 try: self.presenter.view.panelMultipleText.on_remove_deleted_item(title)
            #                 except Exception: pass
            #                 try: self.presenter.view.panelMML.on_remove_deleted_item(title)
            #                 except Exception: pass
            #                 try: self.presenter.view.panelLinearDT.topP.on_remove_deleted_item(title)
            #                 except Exception: pass
            #                 try: self.presenter.view.panelLinearDT.bottomP.on_remove_deleted_item(title)
            #                 except Exception: pass

            elif self._document_type == "Statistical":
                # Change document tree
                docItem = self.getItemByData(self.presenter.documentsDict[self.title].IMS2DstatsData[self._item_leaf])
                parent = self.GetItemParent(docItem)
                self.SetItemText(docItem, new_name)
                # Change dictionary key
                self.presenter.documentsDict[self.title].IMS2DstatsData[new_name] = self.presenter.documentsDict[
                    self.title
                ].IMS2DstatsData.pop(self._item_leaf)
                self.Expand(docItem)
            elif self._document_type == "Overlay":
                # Change document tree
                docItem = self.getItemByData(self.presenter.documentsDict[self.title].IMS2DoverlayData[self._item_leaf])
                parent = self.GetItemParent(docItem)
                self.SetItemText(docItem, new_name)
                # Change dictionary key
                self.presenter.documentsDict[self.title].IMS2DoverlayData[new_name] = self.presenter.documentsDict[
                    self.title
                ].IMS2DoverlayData.pop(self._item_leaf)
                self.Expand(docItem)
            elif self._document_type == "Mass Spectra":
                # Change document tree
                docItem = self.getItemByData(
                    self.presenter.documentsDict[self.title].multipleMassSpectrum[self._item_leaf]
                )
                parent = self.GetItemParent(docItem)
                self.SetItemText(docItem, new_name)
                # Change dictionary key
                self.presenter.documentsDict[self.title].multipleMassSpectrum[new_name] = self.presenter.documentsDict[
                    self.title
                ].multipleMassSpectrum.pop(self._item_leaf)
                self.Expand(docItem)
                # check if item is in other panels
                try:
                    self.presenter.view.panelMML.onRenameItem(current_name, new_name, item_type="filename")
                except Exception:
                    pass
            elif self._document_type == "Drift time (2D, EIC)":
                new_name = new_name.replace(": ", " : ")
                # Change document tree
                docItem = self.getItemByData(self.presenter.documentsDict[self.title].IMS2Dions[self._item_leaf])
                parent = self.GetItemParent(docItem)
                self.SetItemText(docItem, new_name)
                # check if ":" found in the new name

                # TODO: check if iterm is in the peaklist
                # Change dictionary key
                self.presenter.documentsDict[self.title].IMS2Dions[new_name] = self.presenter.documentsDict[
                    self.title
                ].IMS2Dions.pop(self._item_leaf)
                self.Expand(docItem)
            else:
                return

            # just a msg
            args = ("Renamed {} to {}".format(current_name, new_name), 4)
            self.presenter.onThreading(None, args, action="updateStatusbar")

            # Expand parent
            try:
                self.Expand(parent)
            except Exception:
                pass

            self.SetFocus()

    def onGoToDirectory(self, evt=None):
        """
        Go to selected directory
        """
        self.presenter.on_open_directory()

    def on_save_unidec_results(self, evt, data_type="all"):
        basename = os.path.splitext(self._document_data.title)[0]

        if (self._document_type == "Mass Spectrum" and self._item_leaf == "UniDec") or (
            self._document_type == "UniDec" and self._indent == 2
        ):
            unidec_engine_data = self._document_data.massSpectrum["unidec"]
            data_type = "all"
        elif self._document_type == "Mass Spectrum" and self._item_branch == "UniDec" and self._indent == 4:
            unidec_engine_data = self._document_data.massSpectrum["unidec"]
            data_type = self._item_leaf
        elif self._document_type == "Mass Spectra" and self._item_leaf == "UniDec":
            unidec_engine_data = self._document_data.multipleMassSpectrum[self._item_branch]["unidec"]
            data_type = "all"
        elif self._document_type == "Mass Spectra" and self._item_branch == "UniDec":
            unidec_engine_data = self._document_data.multipleMassSpectrum[self._item_root]["unidec"]
            data_type = self._item_leaf

        #         try:
        if data_type in ["all", "MW distribution"]:
            data_type_name = "MW distribution"
            defaultValue = "unidec_MW_{}{}".format(basename, self.config.saveExtension)

            data = unidec_engine_data[data_type_name]
            kwargs = {"default_name": defaultValue}
            data = [data["xvals"], data["yvals"]]
            labels = ["MW(Da)", "Intensity"]
            self.data_handling.on_save_data_as_text(data=data, labels=labels, data_format="%.4f", **kwargs)
        #         except Exception:
        #             print('Failed to save MW distributions')

        try:
            if data_type in ["all", "m/z with isolated species"]:
                data_type_name = "m/z with isolated species"
                defaultValue = "unidec_mz_species_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]

                i, save_data, labels = 0, [], ["m/z"]
                for key in data:
                    if key.split(" ")[0] != "MW:":
                        continue
                    xvals = data[key]["line_xvals"]
                    if i == 0:
                        save_data.append(xvals)
                    yvals = data[key]["line_yvals"]
                    save_data.append(yvals)
                    labels.append(key)
                    i = +1
                save_data = np.column_stack(save_data).T

                kwargs = {"default_name": defaultValue}
                self.data_handling.on_save_data_as_text(data=save_data, labels=labels, data_format="%.4f", **kwargs)
        except Exception:
            pass

        try:
            if data_type in ["all", "Fitted"]:
                data_type_name = "Fitted"
                defaultValue = "unidec_fitted_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]

                kwargs = {"default_name": defaultValue}
                data = [data["xvals"][0], data["yvals"][0], data["yvals"][1]]
                labels = ["m/z(Da)", "Intensity(raw)", "Intensity(fitted)"]
                self.data_handling.on_save_data_as_text(data=data, labels=labels, data_format="%.4f", **kwargs)
        except Exception:
            pass

        try:
            if data_type in ["all", "Processed"]:
                data_type_name = "Processed"
                defaultValue = "unidec_processed_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]

                kwargs = {"default_name": defaultValue}
                data = [data["xvals"], data["yvals"]]
                labels = ["m/z(Da)", "Intensity"]
                self.data_handling.on_save_data_as_text(data=data, labels=labels, data_format="%.4f", **kwargs)
        except Exception:
            pass

        try:
            if data_type in ["all", "m/z vs Charge"]:
                data_type_name = "m/z vs Charge"
                defaultValue = "unidec_mzVcharge_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]["grid"]

                zvals = data[:, 2]
                xvals = np.unique(data[:, 0])
                yvals = np.unique(data[:, 1])

                # reshape data
                xlen = len(xvals)
                ylen = len(yvals)
                zvals = np.reshape(zvals, (xlen, ylen))

                # Combine x-axis with data
                save_data = np.column_stack((xvals, zvals)).T
                yvals = list(map(str, yvals.tolist()))
                labels = ["m/z(Da)"]
                for label in yvals:
                    labels.append(label)

                kwargs = {"default_name": defaultValue}
                self.data_handling.on_save_data_as_text(data=save_data, labels=labels, data_format="%.4f", **kwargs)
        except Exception:
            pass

        try:
            if data_type in ["all", "MW vs Charge"]:
                data_type_name = "MW vs Charge"
                defaultValue = "unidec_MWvCharge_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]

                xvals = data["xvals"]
                yvals = data["yvals"]
                zvals = data["zvals"]
                # reshape data
                xlen = len(xvals)
                ylen = len(yvals)
                zvals = np.reshape(zvals, (xlen, ylen))

                # Combine x-axis with data
                save_data = np.column_stack((xvals, zvals)).T
                yvals = list(map(str, yvals.tolist()))
                labels = ["MW(Da)"]
                for label in yvals:
                    labels.append(label)

                kwargs = {"default_name": defaultValue}
                self.data_handling.on_save_data_as_text(data=save_data, labels=labels, data_format="%.4f", **kwargs)
        except Exception:
            pass

        try:
            if data_type in ["all", "Barchart"]:
                data_type_name = "Barchart"
                defaultValue = "unidec_Barchart_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]

                xvals = data["xvals"]
                yvals = data["yvals"]
                legend_text = data["legend_text"]

                # get labels from legend
                labels = []
                for item in legend_text:
                    labels.append(item[1])

                save_data = [xvals, yvals, labels]

                kwargs = {"default_name": defaultValue}
                self.data_hafndling.on_save_data_as_text(
                    data=save_data, labels=["position", "intensity", "label"], data_format="%s", **kwargs
                )
        except Exception:
            pass

        try:
            if data_type in ["all", "Charge information"]:
                data_type_name = "Charge information"
                defaultValue = "unidec_ChargeInformation_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]

                save_data = [data[:, 0], data[:, 1]]

                kwargs = {"default_name": defaultValue}
                self.data_handling.on_save_data_as_text(
                    data=save_data, labels=["charge", "intensity"], data_format="%s", **kwargs
                )
        except Exception:
            pass

    def on_show_unidec_results(self, evt, plot_type="all"):
        logger.error("This function was depracated")

    def on_show_plot(self, evt, save_image=False):
        """ This will send data, plot and change window"""
        if self._document_data is None:
            return

        if isinstance(evt, int):
            evtID = evt
        elif evt is None:
            evtID = None
        else:
            evtID = evt.GetId()

        self.presenter.currentDoc = self._document_data.title
        basename = os.path.splitext(self._document_data.title)[0]
        defaultValue, save_kwargs = None, {}
        if self._document_type in "Annotated data":
            if self._item_leaf == "Annotated data":
                return
            if self._item_leaf == "Annotations":
                self.on_add_annotation(None)
                return
            data = deepcopy(self.GetPyData(self._item_id))
            try:
                plot_type = data["plot_type"]
            except KeyError:
                return
            if plot_type in [
                "scatter",
                "waterfall",
                "line",
                "multi-line",
                "grid-scatter",
                "grid-line",
                "vertical-bar",
                "horizontal-bar",
            ]:
                xlabel = data["xlabel"]
                ylabel = data["ylabel"]
                labels = data["labels"]
                colors = data["colors"]
                xvals = data["xvals"]
                yvals = data["yvals"]
                zvals = data["zvals"]

                kwargs = {
                    "plot_modifiers": data["plot_modifiers"],
                    "item_colors": data["itemColors"],
                    "item_labels": data["itemLabels"],
                    "xerrors": data["xvalsErr"],
                    "yerrors": data["yvalsErr"],
                    "xlabels": data["xlabels"],
                    "ylabels": data["ylabels"],
                }

            if plot_type == "scatter":
                self.panel_plot.on_plot_other_scatter(
                    xvals, yvals, zvals, xlabel, ylabel, colors, labels, set_page=True, **kwargs
                )
            elif plot_type == "waterfall":
                kwargs = {"labels": labels}
                self.panel_plot.on_plot_other_waterfall(
                    xvals, yvals, None, xlabel, ylabel, colors=colors, set_page=True, **kwargs
                )
            elif plot_type == "multi-line":
                self.panel_plot.on_plot_other_overlay(
                    xvals, yvals, xlabel, ylabel, colors=colors, set_page=True, labels=labels
                )
            elif plot_type == "line":
                kwargs = {
                    "line_color": colors[0],
                    "shade_under_color": colors[0],
                    "plot_modifiers": data["plot_modifiers"],
                }
                self.panel_plot.on_plot_other_1D(xvals, yvals, xlabel, ylabel, **kwargs)
            elif plot_type == "grid-line":
                self.panel_plot.on_plot_other_grid_1D(
                    xvals, yvals, xlabel, ylabel, colors=colors, labels=labels, set_page=True, **kwargs
                )
            elif plot_type == "grid-scatter":
                self.panel_plot.on_plot_other_grid_scatter(
                    xvals, yvals, xlabel, ylabel, colors=colors, labels=labels, set_page=True, **kwargs
                )

            elif plot_type in ["vertical-bar", "horizontal-bar"]:
                kwargs.update(orientation=plot_type)
                self.panel_plot.on_plot_other_bars(
                    xvals, data["yvals_min"], data["yvals_max"], xlabel, ylabel, colors, set_page=True, **kwargs
                )
            elif plot_type in ["matrix"]:
                zvals, yxlabels, cmap = self.presenter.get2DdataFromDictionary(
                    dictionary=data, plotType="Matrix", compact=False
                )
                self.panel_plot.on_plot_matrix(zvals=zvals, xylabels=yxlabels, cmap=cmap, set_page=True)
            else:
                msg = (
                    "Plot: {} is not supported yet. Please contact Lukasz Migas \n".format(plot_type)
                    + "if you would like to include a new plot type in ORIGAMI. Currently \n"
                    + "supported plots include: line, multi-line, waterfall, scatter and grid."
                )
                DialogBox(exceptionTitle="Plot type not supported", exceptionMsg=msg, type="Error")

            if save_image:
                defaultValue = (
                    "Custom_{}_{}".format(basename, os.path.splitext(self._item_leaf)[0])
                    .replace(":", "")
                    .replace(" ", "")
                )
                save_kwargs = {"image_name": defaultValue}
                self.panel_plot.save_images(evt=ID_saveOtherImageDoc, **save_kwargs)

        elif self._document_type == "Tandem Mass Spectra":
            if self._item_leaf == "Tandem Mass Spectra":
                data = self._document_data.tandem_spectra
                kwargs = {"document": self._document_data.title, "tandem_spectra": data}
                self.on_open_MSMS_viewer(**kwargs)
                return

            data = self.GetPyData(self._item_id)
            title = "Precursor: {:.4f} [{}]".format(
                data["scan_info"]["precursor_mz"], data["scan_info"]["precursor_charge"]
            )

            self.panel_plot.on_plot_centroid_MS(data["xvals"], data["yvals"], title=title)
        elif any(
            self._document_type in itemType
            for itemType in ["Mass Spectrum", "Mass Spectra", "Mass Spectrum (processed)"]
        ):
            # Select dataset
            if self._item_leaf == "Mass Spectra":
                return
            data = self.GetPyData(self._item_id)
            try:
                msX = data["xvals"]
                msY = data["yvals"]
            except TypeError:
                return

            try:
                xlimits = data["xlimits"]
            except KeyError:
                xlimits = [self._document_data.parameters["startMS"], self._document_data.parameters["endMS"]]

            # setup kwargs
            if self._document_type in ["Mass Spectrum"]:
                name_kwargs = {"document": self._document_data.title, "dataset": "Mass Spectrum"}
            elif self._document_type in ["Mass Spectrum (processed)"]:
                name_kwargs = {"document": self._document_data.title, "dataset": "Mass Spectrum (processed)"}
            elif self._document_type == "Mass Spectra" and self._item_leaf != self._document_type:
                name_kwargs = {"document": self._document_data.title, "dataset": self._item_leaf}

            # plot
            if self._document_data.dataType != "Type: CALIBRANT":
                self.panel_plot.on_plot_MS(msX, msY, xlimits=xlimits, set_page=True, **name_kwargs)
                if save_image:
                    if self._document_type == "Mass Spectrum":
                        defaultValue = "MS_{}".format(basename)
                    elif self._document_type == "Mass Spectrum (processed)":
                        defaultValue = "MS_processed_{}".format(basename)
                    elif self._document_type == "Mass Spectra" and self._item_leaf != self._document_type:
                        defaultValue = "MS_{}_{}".format(basename, os.path.splitext(self._item_leaf)[0]).replace(
                            ":", ""
                        )
                    save_kwargs = {"image_name": defaultValue}
                    self.panel_plot.save_images(evt=ID_saveMSImage, **save_kwargs)
            else:
                self.panel_plot.on_plot_MS_DT_calibration(
                    msX=msX, msY=msY, xlimits=xlimits, plotType="MS", set_page=True
                )
        elif any(
            self._document_type in itemType
            for itemType in [
                "Drift time (1D)",
                "Drift time (1D, EIC, DT-IMS)",
                "Drift time (1D, EIC)",
                "Calibration peaks",
                "Calibrants",
            ]
        ):
            if self._document_type == "Drift time (1D)":
                data = self._document_data.DT
                defaultValue = "DT_1D_{}".format(basename)
            elif self._document_type == "Drift time (1D, EIC, DT-IMS)":
                if self._item_leaf == "Drift time (1D, EIC, DT-IMS)":
                    return
                data = self._document_data.IMS1DdriftTimes[self._item_leaf]
                defaultValue = "DTIMS_1D_{}_{}".format(basename, self._item_leaf)
            elif self._document_type == "Drift time (1D, EIC)":
                if self._item_leaf == "Drift time (1D, EIC)":
                    return
                data = self._document_data.multipleDT[self._item_leaf]
                defaultValue = "DT_1D_{}_{}".format(basename, self._item_leaf)
            elif self._document_type == "Calibration peaks":
                if self._item_leaf == "Calibration peaks":
                    return
                data = self._document_data.calibration[self._item_leaf]
                defaultValue = "DT_calibrantPeaks_{}_{}".format(basename, self._item_leaf)
            elif self._document_type == "Calibrants":
                if self._item_leaf == "Calibrants":
                    return
                data = self._document_data.calibrationDataset[self._item_leaf]["data"]
                defaultValue = "DT_calibrants_{}_{}".format(basename, self._item_leaf)

            # triggered when clicked on the 1D plot but asking for the MS
            if evtID == ID_showPlotMSDocument and self._document_type == "Drift time (1D, EIC, DT-IMS)":
                mz_min, mz_max = ut_labels.get_ion_name_from_label(self._item_leaf)
                try:
                    mz_min = str2num(mz_min) - self.config.zoomWindowX
                    mz_max = str2num(mz_max) + self.config.zoomWindowX
                except:
                    mz_min = data["xylimits"][0] - self.config.zoomWindowX
                    mz_max = data["xylimits"][1] + self.config.zoomWindowX

                self.panel_plot.on_zoom_1D_x_axis(mz_min, mz_max, set_page=True, plot="MS")
                return
            # extract x/y axis values
            dtX = data["xvals"]
            dtY = data["yvals"]
            if len(dtY) >= 1:
                try:
                    dtY = data["yvalsSum"]
                except KeyError:
                    pass
            xlabel = data["xlabels"]
            if self._document_data.dataType != "Type: CALIBRANT":
                self.panel_plot.on_plot_1D(dtX, dtY, xlabel, set_page=True)
                if save_image:
                    save_kwargs = {"image_name": defaultValue}
                    self.panel_plot.save_images(evt=ID_save1DImageDoc, **save_kwargs)
            else:
                self.panel_plot.on_plot_MS_DT_calibration(
                    dtX=dtX, dtY=dtY, xlabelDT=xlabel, plotType="1DT", set_page=True
                )
                self.panel_plot.on_add_marker(
                    xvals=data["peak"][0],
                    yvals=data["peak"][1],
                    color=self.config.annotColor,
                    marker=self.config.markerShape,
                    size=self.config.markerSize,
                    plot="CalibrationDT",
                )
        elif any(
            self._document_type in itemType
            for itemType in ["Chromatogram", "Chromatograms (EIC)", "Chromatograms (combined voltages, EIC)"]
        ):
            # Select dataset
            if self._document_type == "Chromatogram":
                data = self.GetPyData(self._item_id)
                defaultValue = "RT_{}".format(basename)
            elif self._document_type == "Chromatograms (combined voltages, EIC)":
                if self._item_leaf == "Chromatograms (combined voltages, EIC)":
                    return
                data = self.GetPyData(self._item_id)
                defaultValue = "RT_CV_{}_{}".format(basename, self._item_leaf)
            elif self._document_type == "Chromatograms (EIC)":
                if self._item_leaf == "Chromatograms (EIC)":
                    return
                data = self.GetPyData(self._item_id)
                defaultValue = "RT_{}_{}".format(basename, self._item_leaf)
            # Unpack data
            rtX = data["xvals"]
            rtY = data["yvals"]
            xlabel = data["xlabels"]
            # Change panel and plot
            self.panel_plot.on_plot_RT(rtX, rtY, xlabel, set_page=True)
            if save_image:
                save_kwargs = {"image_name": defaultValue}
                self.panel_plot.save_images(evt=ID_saveRTImageDoc, **save_kwargs)
        elif any(
            self._document_type in itemType
            for itemType in [
                "Drift time (2D)",
                "Drift time (2D, processed)",
                "Drift time (2D, EIC)",
                "Drift time (2D, combined voltages, EIC)",
                "Drift time (2D, processed, EIC)",
                "Input data",
            ]
        ):
            # check appropriate data is selected
            if self._document_type == "Drift time (2D, EIC)":
                if self._item_leaf == "Drift time (2D, EIC)":
                    return
                defaultValue = "DT_2D_{}_{}".format(basename, self._item_leaf)
            elif self._document_type == "Drift time (2D, combined voltages, EIC)":
                if self._item_leaf == "Drift time (2D, combined voltages, EIC)":
                    return
                defaultValue = "DT_2D_CV_{}_{}".format(basename, self._item_leaf)
            elif self._document_type == "Drift time (2D, processed, EIC)":
                if self._item_leaf == "Drift time (2D, processed, EIC)":
                    return
                defaultValue = "DT_2D_processed_{}_{}".format(basename, self._item_leaf)
            elif self._document_type == "Input data":
                if self._item_leaf == "Input data":
                    return
                defaultValue = "DT_2D_{}_{}".format(basename, self._item_leaf)
            elif self._document_type == "Statistical":
                if self._item_leaf == "Statistical":
                    return
                defaultValue = "DT_2D_{}_{}".format(basename, self._item_leaf)
            elif self._document_type == "Drift time (2D)":
                defaultValue = "DT_2D_{}".format(basename)
            elif self._document_type == "Drift time (2D, processed)":
                defaultValue = "DT_2D_processed_{}".format(basename)
            else:
                self.presenter.view.SetStatusText("No data found", 3)
                return

            # get data for selected item
            data = self.GetPyData(self._item_id)
            if evtID == ID_showPlotMSDocument:
                mz_min, mz_max = ut_labels.get_ion_name_from_label(self._item_leaf)
                try:
                    mz_min = str2num(mz_min) - self.config.zoomWindowX
                    mz_max = str2num(mz_max) + self.config.zoomWindowX
                except:
                    mz_min = data["xylimits"][0] - self.config.zoomWindowX
                    mz_max = data["xylimits"][1] + self.config.zoomWindowX

                self.panel_plot.on_zoom_1D_x_axis(mz_min, mz_max, set_page=True, plot="MS")
                return
            elif evtID == ID_showPlot1DDocument:
                self.panel_plot.on_plot_1D(
                    data["yvals"],  # normally this would be the y-axis
                    data["yvals1D"],
                    data["ylabels"],  # data was rotated so using ylabel for xlabel
                    set_page=True,
                )
                return
            elif evtID == ID_showPlotRTDocument:
                self.panel_plot.on_plot_RT(data["xvals"], data["yvalsRT"], data["xlabels"], set_page=True)
                return
            elif evtID == ID_showPlotDocument_violin:
                dataOut = self.presenter.get2DdataFromDictionary(dictionary=data, dataType="plot", compact=True)
                self.panel_plot.on_plot_violin(data=dataOut, set_page=True)
                return
            elif evtID == ID_showPlotDocument_waterfall:
                zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(
                    dictionary=data, dataType="plot", compact=False
                )
                if len(xvals) > 500:
                    msg = (
                        f"There are {len(xvals)} scans in this dataset (this could be slow...). "
                        + "Would you like to continue?"
                    )
                    dlg = DialogBox("Would you like to continue?", msg, type="Question")
                    if dlg == wx.ID_NO:
                        return

                self.panel_plot.on_plot_waterfall(
                    yvals=xvals, xvals=yvals, zvals=zvals, xlabel=xlabel, ylabel=ylabel, set_page=True
                )
                return
            else:
                pass
            # Unpack data
            if len(data) == 0:
                return

            dataOut = self.presenter.get2DdataFromDictionary(dictionary=data, dataType="plot", compact=True)
            # Change panel and plot data
            self.panel_plot.on_plot_2D_data(data=dataOut)
            if not self.config.waterfall:
                self.panel_plot._set_page(self.config.panelNames["2D"])
            if save_image:
                save_kwargs = {"image_name": defaultValue}
                self.panel_plot.save_images(evt=ID_save2DImageDoc, **save_kwargs)
        # =======================================================================
        #  OVERLAY PLOTS
        # =======================================================================
        elif self._document_type == "Overlay":
            if self._item_leaf == "Overlay":
                return
            # Determine type
            out = re.split("-|,|__|:", self._item_leaf)
            data = self._document_data.IMS2DoverlayData.get(self._item_leaf, {})
            if len(data) == 0:
                keys = list(self._document_data.IMS2DoverlayData.keys())
                for key in keys:
                    if self._item_leaf in key:
                        self._item_leaf = key
                        data = self._document_data.IMS2DoverlayData.get(self._item_leaf, {})
            if out[0] == "Grid (n x n)":
                defaultValue = "Overlay_Grid_NxN_{}".format(basename)
                self.panel_plot.on_plot_n_grid(
                    data["zvals_list"],
                    data["cmap_list"],
                    data["title_list"],
                    data["xvals"],
                    data["yvals"],
                    data["xlabels"],
                    data["ylabels"],
                    set_page=True,
                )
                if save_image:
                    save_kwargs = {"image_name": defaultValue}
                    self.panel_plot.save_images(evt=ID_saveOverlayImageDoc, **save_kwargs)
            elif out[0] == "Grid (2":
                defaultValue = "Overlay_Grid_2to1_{}".format(basename)
                self.panel_plot.on_plot_grid(
                    data["zvals_1"],
                    data["zvals_2"],
                    data["zvals_cum"],
                    data["xvals"],
                    data["yvals"],
                    data["xlabels"],
                    data["ylabels"],
                    data["cmap_1"],
                    data["cmap_2"],
                    set_page=True,
                )

                # Add RMSD label
                rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=data["xvals"], ylist=data["yvals"])
                if rmsdXpos is not None and rmsdYpos is not None:
                    self.presenter.addTextRMSD(rmsdXpos, rmsdYpos, data["rmsdLabel"], 0, plot="Grid")

                if save_image:
                    save_kwargs = {"image_name": defaultValue}
                    self.panel_plot.save_images(evt=ID_saveOverlayImageDoc, **save_kwargs)
            elif out[0] == "Mask" or out[0] == "Transparent":
                (
                    zvals1,
                    zvals2,
                    cmap1,
                    cmap2,
                    alpha1,
                    alpha2,
                    __,
                    __,
                    xvals,
                    yvals,
                    xlabels,
                    ylabels,
                ) = self.presenter.getOverlayDataFromDictionary(dictionary=data, dataType="plot", compact=False)
                if out[0] == "Mask":
                    defaultValue = "Overlay_mask_{}".format(basename)
                    self.panel_plot.on_plot_overlay_2D(
                        zvalsIon1=zvals1,
                        cmapIon1=cmap1,
                        alphaIon1=1,
                        zvalsIon2=zvals2,
                        cmapIon2=cmap2,
                        alphaIon2=1,
                        xvals=xvals,
                        yvals=yvals,
                        xlabel=xlabels,
                        ylabel=ylabels,
                        flag="Text",
                        set_page=True,
                    )
                elif out[0] == "Transparent":
                    defaultValue = "Overlay_transparent_{}".format(basename)
                    self.panel_plot.on_plot_overlay_2D(
                        zvalsIon1=zvals1,
                        cmapIon1=cmap1,
                        alphaIon1=alpha1,
                        zvalsIon2=zvals2,
                        cmapIon2=cmap2,
                        alphaIon2=alpha2,
                        xvals=xvals,
                        yvals=yvals,
                        xlabel=xlabels,
                        ylabel=ylabels,
                        flag="Text",
                        set_page=True,
                    )
                # Change window view
                if save_image:
                    save_kwargs = {"image_name": defaultValue}
                    self.panel_plot.save_images(evt=ID_saveOverlayImageDoc, **save_kwargs)

            elif out[0] == "RMSF":
                (
                    zvals,
                    yvalsRMSF,
                    xvals,
                    yvals,
                    xlabelRMSD,
                    ylabelRMSD,
                    ylabelRMSF,
                    color,
                    cmap,
                    rmsdLabel,
                ) = self.presenter.get2DdataFromDictionary(dictionary=data, plotType="RMSF", compact=True)
                defaultValue = "Overlay_RMSF_{}".format(basename)
                self.panel_plot.on_plot_RMSDF(
                    yvalsRMSF=yvalsRMSF,
                    zvals=zvals,
                    xvals=xvals,
                    yvals=yvals,
                    xlabelRMSD=xlabelRMSD,
                    ylabelRMSD=ylabelRMSD,
                    ylabelRMSF=ylabelRMSF,
                    color=color,
                    cmap=cmap,
                    plotType="RMSD",
                    set_page=True,
                )
                # Add RMSD label
                rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xvals, ylist=yvals)
                if rmsdXpos is not None and rmsdYpos is not None:
                    self.presenter.addTextRMSD(rmsdXpos, rmsdYpos, rmsdLabel, 0, plot="RMSF")

                if save_image:
                    save_kwargs = {"image_name": defaultValue}
                    self.panel_plot.save_images(evt=ID_saveRMSFImageDoc, **save_kwargs)

            elif out[0] == "RGB":
                defaultValue = "Overlay_RGB_{}".format(basename)
                data = self.GetPyData(self._item_id)
                rgb_plot, xAxisLabels, xlabel, yAxisLabels, ylabel, __ = self.presenter.get2DdataFromDictionary(
                    dictionary=data, plotType="2D", compact=False
                )
                legend_text = data["legend_text"]
                self.panel_plot.on_plot_rgb(
                    rgb_plot, xAxisLabels, yAxisLabels, xlabel, ylabel, legend_text, set_page=True
                )
                if save_image:
                    save_kwargs = {"image_name": defaultValue}
                    self.panel_plot.save_images(evt=ID_save2DImageDoc, **save_kwargs)

            elif out[0] == "RMSD":
                defaultValue = "Overlay_RMSD_{}".format(basename)
                (
                    zvals,
                    xaxisLabels,
                    xlabel,
                    yaxisLabels,
                    ylabel,
                    rmsdLabel,
                    cmap,
                ) = self.presenter.get2DdataFromDictionary(dictionary=data, plotType="RMSD", compact=True)
                self.panel_plot.on_plot_RMSD(
                    zvals, xaxisLabels, yaxisLabels, xlabel, ylabel, cmap, plotType="RMSD", set_page=True
                )
                self.panel_plot.on_plot_3D(
                    zvals=zvals,
                    labelsX=xaxisLabels,
                    labelsY=yaxisLabels,
                    xlabel=xlabel,
                    ylabel=ylabel,
                    zlabel="Intensity",
                    cmap=cmap,
                )
                # Add RMSD label
                rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xaxisLabels, ylist=yaxisLabels)
                if rmsdXpos is not None and rmsdYpos is not None:
                    self.presenter.addTextRMSD(rmsdXpos, rmsdYpos, rmsdLabel, 0, plot="RMSD")

                if save_image:
                    save_kwargs = {"image_name": defaultValue}
                    self.panel_plot.save_images(evt=ID_saveRMSDImageDoc, **save_kwargs)

            elif out[0] in [
                "Waterfall (Raw)",
                "Waterfall (Processed)",
                "Waterfall (Fitted)",
                "Waterfall (Deconvoluted MW)",
                "Waterfall (Charge states)",
            ]:
                if out[0] == "Waterfall (Raw)":
                    defaultValue = "MS_Waterfall_raw_{}".format(basename)
                elif out[0] == "Waterfall (Processed)":
                    defaultValue = "MS_Waterfall_processed_{}".format(basename)
                elif out[0] == "Waterfall (Fitted)":
                    defaultValue = "MS_Waterfall_fitted_{}".format(basename)
                elif out[0] == "Waterfall (Deconvoluted MW)":
                    defaultValue = "MS_Waterfall_deconvolutedMW_{}".format(basename)
                elif out[0] == "Waterfall (Charge states)":
                    defaultValue = "MS_Waterfall_charges_{}".format(basename)

                self.panel_plot.on_plot_waterfall(
                    data["xvals"],
                    data["yvals"],
                    None,
                    colors=data["colors"],
                    xlabel=data["xlabel"],
                    ylabel=data["ylabel"],
                    set_page=True,
                    **data["waterfall_kwargs"],
                )
                if save_image:
                    save_kwargs = {"image_name": defaultValue}
                    self.panel_plot.save_images(evt=ID_saveWaterfallImageDoc, **save_kwargs)

            elif out[0] == "Waterfall overlay":
                self.panel_plot.on_plot_waterfall_overlay(
                    data["xvals"],
                    data["yvals"],
                    data["zvals"],
                    data["colors"],
                    data["xlabel"],
                    data["ylabel"],
                    data["labels"],
                    set_page=True,
                )
                if save_image:
                    defaultValue = "Waterfall_overlay_{}".format(basename)
                    save_kwargs = {"image_name": defaultValue}
                    self.panel_plot.save_images(evt=ID_saveWaterfallImageDoc, **save_kwargs)

            # Overlayed 1D data
            elif out[0] == "1D" or out[0] == "RT":
                xvals, yvals, xlabels, colors, labels, xlimits = self.presenter.get2DdataFromDictionary(
                    dictionary=data, plotType="Overlay1D", compact=True
                )
                if out[0] == "1D":
                    defaultValue = "Overlay_DT_1D_{}".format(basename)
                    self.panel_plot.on_plot_overlay_DT(
                        xvals=xvals,
                        yvals=yvals,
                        xlabel=xlabels,
                        colors=colors,
                        xlimits=xlimits,
                        labels=labels,
                        set_page=True,
                    )
                    if save_image:
                        save_kwargs = {"image_name": defaultValue}
                        self.panel_plot.save_images(evt=ID_save1DImageDoc, **save_kwargs)
                elif out[0] == "RT":
                    defaultValue = "Overlay_RT_{}".format(basename)
                    self.panel_plot.on_plot_overlay_RT(
                        xvals=xvals,
                        yvals=yvals,
                        xlabel=xlabels,
                        colors=colors,
                        xlimits=xlimits,
                        labels=labels,
                        set_page=True,
                    )
                    if save_image:
                        save_kwargs = {"image_name": defaultValue}
                        self.panel_plot.save_images(evt=ID_saveRTImageDoc, **save_kwargs)

        elif self._document_type == "Statistical":
            if self._item_leaf == "Statistical":
                return

            out = self._item_leaf.split(":")
            data = self._document_data.IMS2DstatsData[self._item_leaf]
            # Variance, Mean, Std Dev are of the same format
            if out[0] in ["Variance", "Mean", "Standard Deviation"]:
                if out[0] == "Variance":
                    defaultValue = "Overlay_variance_{}".format(basename)
                elif out[0] == "Mean":
                    defaultValue = "Overlay_mean_{}".format(basename)
                elif out[0] == "Standard Deviation":
                    defaultValue = "Overlay_std_{}".format(basename)

                # Unpack data
                dataOut = self.presenter.get2DdataFromDictionary(dictionary=data, dataType="plot", compact=True)
                # Change panel and plot data
                self.panel_plot.on_plot_2D_data(data=dataOut)
                self.panel_plot._set_page(self.config.panelNames["2D"])
                if save_image:
                    save_kwargs = {"image_name": defaultValue}
                    self.panel_plot.save_images(evt=ID_save2DImageDoc, **save_kwargs)

            elif out[0] == "RMSD Matrix":
                defaultValue = "Overlay_matrix_{}".format(basename)
                zvals, yxlabels, cmap = self.presenter.get2DdataFromDictionary(
                    dictionary=data, plotType="Matrix", compact=False
                )
                self.panel_plot.on_plot_matrix(zvals=zvals, xylabels=yxlabels, cmap=cmap, set_page=True)
                if save_image:
                    save_kwargs = {"image_name": defaultValue}
                    self.panel_plot.save_images(evt=ID_saveRMSDmatrixImageDoc, **save_kwargs)
        elif self._document_type == "DT/MS" or evtID in [
            ID_ylabel_DTMS_bins,
            ID_ylabel_DTMS_ms,
            ID_ylabel_DTMS_restore,
        ]:
            defaultValue = "DTMS_{}".format(basename)
            data = self.GetPyData(self._item_id)
            xvals = data["xvals"]
            zvals = data["zvals"]
            xvals, zvals = self.data_processing.downsample_array(xvals, zvals)
            self.panel_plot.on_plot_MSDT(
                zvals,
                xvals,
                data["yvals"],
                data["xlabels"],
                data["ylabels"],
                set_page=True,
                full_data=dict(zvals=data["zvals"], xvals=data["xvals"]),
            )
            if save_image:
                self.panel_plot.save_images(evt=ID_saveMZDTImageDoc, **save_kwargs)
        else:
            return

    def onSaveDF(self, evt):

        print("Saving dataframe...")
        tstart = time.time()

        if self._document_type == "Mass Spectra" and self._item_leaf == "Mass Spectra":
            dataframe = self._document_data.massSpectraSave
            if len(self._document_data.massSpectraSave) == 0:
                msFilenames = ["m/z"]
                for i, key in enumerate(self._document_data.multipleMassSpectrum):
                    msY = self._document_data.multipleMassSpectrum[key]["yvals"]
                    if self.config.normalizeMultipleMS:
                        msY = msY / max(msY)
                    msFilenames.append(key)
                    if i == 0:
                        tempArray = msY
                    else:
                        tempArray = np.concatenate((tempArray, msY), axis=0)
                try:
                    # Form pandas dataframe
                    msX = self._document_data.multipleMassSpectrum[key]["xvals"]
                    combMSOut = np.concatenate((msX, tempArray), axis=0)
                    combMSOut = combMSOut.reshape((len(msY), int(i + 2)), order="F")
                    dataframe = pd.DataFrame(data=combMSOut, columns=msFilenames)
                except Exception:
                    self.presenter.view.SetStatusText(
                        "Mass spectra are not of the same size. Please export each item separately", 3
                    )
            try:
                # Save data
                if evt.GetId() == ID_saveData_csv:
                    filename = self.presenter.getImageFilename(
                        defaultValue="MS_multiple", withPath=True, extension=self.config.saveExtension
                    )
                    if filename is None:
                        return
                    dataframe.to_csv(path_or_buf=filename, sep=self.config.saveDelimiter, header=True, index=True)
                elif evt.GetId() == ID_saveData_pickle:
                    filename = self.presenter.getImageFilename(
                        defaultValue="MS_multiple", withPath=True, extension=".pickle"
                    )
                    if filename is None:
                        return
                    dataframe.to_pickle(path=filename, protocol=2)
                elif evt.GetId() == ID_saveData_excel:
                    filename = self.presenter.getImageFilename(
                        defaultValue="MS_multiple", withPath=True, extension=".xlsx"
                    )
                    if filename is None:
                        return
                    dataframe.to_excel(excel_writer=filename, sheet_name="data")
                elif evt.GetId() == ID_saveData_hdf:
                    filename = self.presenter.getImageFilename(
                        defaultValue="MS_multiple", withPath=True, extension=".h5"
                    )
                    if filename is None:
                        return
                    dataframe.to_hdf(path_or_buf=filename, key="data")

                print(
                    "Dataframe was saved in {}. It took: {} s.".format(filename, str(np.round(time.time() - tstart, 4)))
                )
            except AttributeError:
                args = (
                    "This document does not have correctly formatted MS data. Please export each item separately",
                    4,
                )
                self.presenter.onThreading(None, args, action="updateStatusbar")

    def onSaveData(self, data=None, labels=None, data_format="%.4f", **kwargs):
        """
        Helper function to save data in consistent manner
        """
        wildcard = (
            "CSV (Comma delimited) (*.csv)|*.csv|"
            + "Text (Tab delimited) (*.txt)|*.txt|"
            + "Text (Space delimited (*.txt)|*.txt"
        )

        wildcard_dict = {",": 0, "\t": 1, " ": 2}

        if kwargs.get("ask_permission", False):
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        else:
            style = wx.FD_SAVE

        dlg = wx.FileDialog(
            self.presenter.view, "Please select a name for the file", "", "", wildcard=wildcard, style=style
        )
        dlg.CentreOnParent()

        if "default_name" in kwargs:
            defaultName = kwargs.pop("default_name")
        else:
            defaultName = ""
        defaultName = (
            defaultName.replace(" ", "")
            .replace(":", "")
            .replace(" ", "")
            .replace(".csv", "")
            .replace(".txt", "")
            .replace(".raw", "")
            .replace(".d", "")
            .replace(".", "_")
        )

        dlg.SetFilename(defaultName)

        try:
            dlg.SetFilterIndex(wildcard_dict[self.config.saveDelimiter])
        except Exception:
            pass

        if not kwargs.get("return_filename", False):
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                __, extension = os.path.splitext(filename)
                self.config.saveExtension = extension
                self.config.saveDelimiter = list(wildcard_dict.keys())[
                    list(wildcard_dict.values()).index(dlg.GetFilterIndex())
                ]
                saveAsText(
                    filename=filename,
                    data=data,
                    format=data_format,
                    delimiter=self.config.saveDelimiter,
                    header=self.config.saveDelimiter.join(labels),
                )
            else:
                self.presenter.onThreading(None, ("Cancelled operation", 4, 5), action="updateStatusbar")
        else:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                basename, extension = os.path.splitext(filename)

                return filename, basename, extension
            else:
                return None, None, None

    def onSaveCSV(self, evt):
        """
        This function extracts the 1D or 2D data and saves it in a CSV format
        """
        if self._document_data is None:
            return

        saveFileName = None
        basename = os.path.splitext(self._document_data.title)[0]
        # Save MS - single
        if (
            self._document_type == "Mass Spectrum"
            or self._document_type == "Mass Spectrum (processed)"
            or self._document_type == "Mass Spectra"
            and self.extractData != self._document_type
        ):
            # Default name
            defaultValue = "MSout"
            # Saves MS to file. Automatically removes values with 0s from the array
            # Get data
            if self._document_type == "Mass Spectrum":
                data = self._document_data.massSpectrum
                defaultValue = "MS_{}{}".format(basename, self.config.saveExtension)
            elif self._document_type == "Mass Spectrum (processed)":
                data = self._document_data.smoothMS
                defaultValue = "MS_processed_{}{}".format(basename, self.config.saveExtension)
            elif self._document_type == "Mass Spectra" and self._item_leaf != self._document_type:
                data = self._document_data.multipleMassSpectrum[self._item_leaf]
                extractBasename = os.path.splitext(self._item_leaf)[0]
                defaultValue = "MS_{}_{}{}".format(basename, extractBasename, self.config.saveExtension).replace(
                    ":", ""
                )

            # Extract MS and find where items are equal to 0 = to reduce filesize
            msX = data["xvals"]
            msXzero = np.where(msX == 0)[0]
            msY = data["yvals"]
            msYzero = np.where(msY == 0)[0]
            # Find which index to use for removal
            removeIdx = np.concatenate((msXzero, msYzero), axis=0)
            msXnew = np.delete(msX, removeIdx)
            msYnew = np.delete(msY, removeIdx)

            kwargs = {"default_name": defaultValue}
            data = [msXnew, msYnew]
            labels = ["m/z", "Intensity"]
            self.data_handling.on_save_data_as_text(data=data, labels=labels, data_format="%.4f", **kwargs)

        # Save MS - multiple MassLynx fiels
        elif self._document_type == "Mass Spectra" and self._item_leaf == "Mass Spectra":
            for key in self._document_data.multipleMassSpectrum:
                stripped_key_name = clean_filename(key)
                defaultValue = "MS_{}_{}{}".format(basename, stripped_key_name, self.config.saveExtension)
                msX = self._document_data.multipleMassSpectrum[key]["xvals"]
                msY = self._document_data.multipleMassSpectrum[key]["yvals"]
                # Extract MS and find where items are equal to 0 = to reduce filesize
                msXzero = np.where(msX == 0)[0]
                msYzero = np.where(msY == 0)[0]
                # Find which index to use for removal
                removeIdx = np.concatenate((msXzero, msYzero), axis=0)
                msXnew = np.delete(msX, removeIdx)
                msYnew = np.delete(msY, removeIdx)
                xlabel = "m/z(Da)"
                data = [msXnew, msYnew]
                kwargs = {"default_name": defaultValue}
                self.data_handling.on_save_data_as_text(
                    data=data, labels=[xlabel, "Intensity"], data_format="%.4f", **kwargs
                )

        # Save calibration parameters - single
        elif self._document_type == "Calibration Parameters":
            if evt.GetId() == ID_saveDataCSVDocument:
                saveFileName = self.presenter.getImageFilename(prefix=True, csv=True, defaultValue="calibrationTable")
                if saveFileName == "" or saveFileName is None:
                    saveFileName = "calibrationTable"

            filename = "".join([self._document_data.path, "\\", saveFileName, self.config.saveExtension])

            df = self._document_data.calibrationParameters["dataframe"]
            df.to_csv(path_or_buf=filename, sep=self.config.saveDelimiter)

        # Save RT - single
        elif self._document_type == "Chromatogram":
            if evt.GetId() == ID_saveDataCSVDocument:
                defaultValue = "RT_{}{}".format(basename, self.config.saveExtension)
                rtX = self._document_data.RT["xvals"]
                rtY = self._document_data.RT["yvals"]
                xlabel = self._document_data.RT["xlabels"]
                kwargs = {"default_name": defaultValue}
                self.data_handling.on_save_data_as_text(
                    data=[rtX, rtY], labels=[xlabel, "Intensity"], data_format="%.4f", **kwargs
                )

        # Save 1D - single
        elif self._document_type == "Drift time (1D)":
            if evt.GetId() == ID_saveDataCSVDocument:
                defaultValue = "DT_1D_{}{}".format(basename, self.config.saveExtension)
                dtX = self._document_data.DT["xvals"]
                dtY = self._document_data.DT["yvals"]
                ylabel = self._document_data.DT["xlabels"]
                kwargs = {"default_name": defaultValue}
                self.data_handling.on_save_data_as_text(
                    data=[dtX, dtY], labels=[ylabel, "Intensity"], data_format="%.2f", **kwargs
                )

        # Save RT (combined voltages) - batch + single
        elif self._document_type == "Chromatograms (combined voltages, EIC)":
            # Batch mode
            if self._item_leaf == "Chromatograms (combined voltages, EIC)":
                for key in self._document_data.IMSRTCombIons:
                    stripped_key_name = key.replace(" ", "")
                    defaultValue = "RT_{}_{}{}".format(basename, stripped_key_name, self.config.saveExtension)
                    rtX = self._document_data.IMSRTCombIons[key]["xvals"]
                    rtY = self._document_data.IMSRTCombIons[key]["yvals"]
                    xlabel = self._document_data.IMSRTCombIons[key]["xlabels"]
                    kwargs = {"default_name": defaultValue}
                    self.data_handling.on_save_data_as_text(
                        data=[rtX, rtY], labels=[xlabel, "Intensity"], data_format="%.4f", **kwargs
                    )
            #             # Single mode
            else:
                defaultValue = "RT_{}_{}{}".format(basename, self._item_leaf, self.config.saveExtension)
                rtX = self._document_data.IMSRTCombIons[self._item_leaf]["xvals"]
                rtY = self._document_data.IMSRTCombIons[self._item_leaf]["yvals"]
                xlabel = self._document_data.IMSRTCombIons[self._item_leaf]["xlabels"]
                kwargs = {"default_name": defaultValue}
                self.data_handling.on_save_data_as_text(
                    data=[rtX, rtY], labels=[xlabel, "Intensity"], data_format="%.4f", **kwargs
                )

        # Save 1D - batch + single
        elif self._document_type == "Drift time (1D, EIC, DT-IMS)":
            if evt.GetId() == ID_saveDataCSVDocument:
                saveFileName = self.presenter.getImageFilename(prefix=True, csv=True, defaultValue="DT_1D_")
                if saveFileName == "" or saveFileName is None:
                    saveFileName = "DT_1D_"
            # Batch mode
            if self._item_leaf == "Drift time (1D, EIC, DT-IMS)":
                for key in self._document_data.IMS1DdriftTimes:
                    if self._document_data.dataType == "Type: MANUAL":
                        name = re.split(", File: |.raw", key)
                        filename = "".join(
                            [
                                self._document_data.path,
                                "\\",
                                saveFileName,
                                name[0],
                                "_",
                                name[1],
                                self.config.saveExtension,
                            ]
                        )
                        dtX = self._document_data.IMS1DdriftTimes[key]["xvals"]
                        dtY = self._document_data.IMS1DdriftTimes[key]["yvals"]
                        xlabel = self._document_data.IMS1DdriftTimes[key]["xlabels"]
                        saveAsText(
                            filename=filename,
                            data=[dtX, dtY],
                            format="%.4f",
                            delimiter=self.config.saveDelimiter,
                            header=self.config.saveDelimiter.join([xlabel, "Intensity"]),
                        )
                    else:
                        filename = "".join(
                            [self._document_data.path, "\\", saveFileName, key, self.config.saveExtension]
                        )
                        zvals = self._document_data.IMS1DdriftTimes[key]["yvals"]
                        yvals = self._document_data.IMS1DdriftTimes[key]["xvals"]
                        xvals = np.asarray(self._document_data.IMS1DdriftTimes[key]["driftVoltage"])
                        # Y-axis labels need a value for [0,0]
                        yvals = np.insert(yvals, 0, 0)  # array, index, value
                        # Combine x-axis with data
                        saveData = np.vstack((xvals, zvals.T))
                        saveData = np.vstack((yvals, saveData.T))
                        # Save data
                        saveAsText(
                            filename=filename,
                            data=saveData,
                            format="%.2f",
                            delimiter=self.config.saveDelimiter,
                            header="",
                        )

            # Single mode
            else:
                if self._document_data.dataType == "Type: MANUAL":
                    name = re.split(", File: |.raw", self._item_leaf)
                    filename = "".join(
                        [self._document_data.path, "\\", saveFileName, name[0], "_", name[1], self.config.saveExtension]
                    )
                    dtX = self._document_data.IMS1DdriftTimes[self._item_leaf]["xvals"]
                    dtY = self._document_data.IMS1DdriftTimes[self._item_leaf]["yvals"]
                    xlabel = self._document_data.IMS1DdriftTimes[self._item_leaf]["xlabels"]
                    saveAsText(
                        filename=filename,
                        data=[dtX, dtY],
                        format="%.4f",
                        delimiter=self.config.saveDelimiter,
                        header=self.config.saveDelimiter.join([xlabel, "Intensity"]),
                    )
                else:
                    filename = "".join(
                        [self._document_data.path, "\\", saveFileName, self._item_leaf, self.config.saveExtension]
                    )
                    zvals = self._document_data.IMS1DdriftTimes[self._item_leaf]["yvals"]
                    yvals = self._document_data.IMS1DdriftTimes[self._item_leaf]["xvals"]
                    xvals = np.asarray(self._document_data.IMS1DdriftTimes[self._item_leaf].get("driftVoltage", " "))
                    # Y-axis labels need a value for [0,0]
                    yvals = np.insert(yvals, 0, 0)  # array, index, value
                    # Combine x-axis with data
                    saveData = np.vstack((xvals, zvals.T))
                    saveData = np.vstack((yvals, saveData.T))
                    saveAsText(
                        filename=filename, data=saveData, format="%.2f", delimiter=self.config.saveDelimiter, header=""
                    )
        # Save DT/MS
        elif self._document_type == "DT/MS":
            data = self.GetPyData(self._item_id)
            zvals = data["zvals"]
            xvals = data["xvals"]
            yvals = data["yvals"]

            if evt.GetId() == ID_saveDataCSVDocument:
                defaultValue = "MSDT_{}{}".format(basename, self.config.saveExtension)
                saveData = np.vstack((xvals, zvals))
                xvals = list(map(str, xvals.tolist()))
                labels = ["DT"]
                labels.extend(yvals)
                fmts = ["%.4f"] + ["%i"] * len(yvals)
                # Save 2D array
                kwargs = {"default_name": defaultValue}
                self.data_handling.on_save_data_as_text(data=[saveData], labels=labels, data_format=fmts, **kwargs)

        # Save 1D/2D - batch + single
        elif any(
            self._document_type in itemType
            for itemType in [
                "Drift time (2D)",
                "Drift time (2D, processed)",
                "Drift time (2D, EIC)",
                "Drift time (2D, combined voltages, EIC)",
                "Drift time (2D, processed, EIC)",
                "Input data",
                "Statistical",
            ]
        ):
            # Select dataset
            if self._document_type in ["Drift time (2D)", "Drift time (2D, processed)"]:
                if self._document_type == "Drift time (2D)":
                    data = self._document_data.IMS2D
                    defaultValue = "DT_2D_raw_{}{}".format(basename, self.config.saveExtension)

                elif self._document_type == "Drift time (2D, processed)":
                    data = self._document_data.IMS2Dprocess
                    defaultValue = "DT_2D_processed_{}{}".format(basename, self.config.saveExtension)

                # Save 2D
                if evt.GetId() == ID_saveDataCSVDocument:
                    # Prepare data for saving
                    zvals, xvals, xlabel, yvals, ylabel, __ = self.presenter.get2DdataFromDictionary(
                        dictionary=data, dataType="plot", compact=False
                    )
                    saveData = np.vstack((yvals, zvals.T))
                    xvals = list(map(str, xvals.tolist()))
                    labels = ["DT"]
                    for label in xvals:
                        labels.append(label)
                    # Save 2D array
                    kwargs = {"default_name": defaultValue}
                    self.data_handling.on_save_data_as_text(
                        data=[saveData], labels=labels, data_format="%.2f", **kwargs
                    )

                # Save 1D
                elif evt.GetId() == ID_saveDataCSVDocument1D:
                    if self._document_type == "Drift time (2D)":
                        defaultValue = "DT_1D_raw_{}{}".format(basename, self.config.saveExtension)

                    elif self._document_type == "Drift time (2D, processed)":
                        defaultValue = "DT_1D_processed_{}{}".format(basename, self.config.saveExtension)
                    # Get data from the document
                    dtX = data["yvals"]
                    ylabel = data["xlabels"]
                    try:
                        dtY = data["yvals1D"]
                    except KeyError:
                        msg = "Missing data. Cancelling operation."
                        self.presenter.view.SetStatusText(msg, 3)
                        return
                    kwargs = {"default_name": defaultValue}
                    self.data_handling.on_save_data_as_text(
                        data=[dtX, dtY], labels=[ylabel, "Intensity"], data_format="%.4f", **kwargs
                    )

            # Save 1D/2D - single + batch
            elif any(
                self._document_type in itemType
                for itemType in [
                    "Drift time (2D, EIC)",
                    "Drift time (2D, combined voltages, EIC)",
                    "Drift time (2D, processed, EIC)",
                    "Input data",
                    "Statistical",
                ]
            ):
                # Save 1D/2D - batch
                if any(
                    self._item_leaf in extractData
                    for extractData in [
                        "Drift time (2D, EIC)",
                        "Drift time (2D, combined voltages, EIC)",
                        "Drift time (2D, processed, EIC)",
                        "Input data",
                        "Statistical",
                    ]
                ):
                    name_modifier = ""
                    if self._document_type == "Drift time (2D, EIC)":
                        data = self._document_data.IMS2Dions
                    elif self._document_type == "Drift time (2D, combined voltages, EIC)":
                        data = self._document_data.IMS2DCombIons
                        name_modifier = "_CV_"
                    elif self._document_type == "Drift time (2D, processed, EIC)":
                        data = self._document_data.IMS2DionsProcess
                    elif self._document_type == "Input data":
                        data = self._document_data.IMS2DcompData
                    elif self._document_type == "Statistical":
                        data = self._document_data.IMS2DstatsData

                    # 2D - batch
                    if evt.GetId() == ID_saveDataCSVDocument:
                        # Iterate over dictionary
                        for key in data:
                            stripped_key_name = key.replace(" ", "")
                            defaultValue = "DT_2D_{}_{}{}{}".format(
                                basename, name_modifier, stripped_key_name, self.config.saveExtension
                            )
                            # Prepare data for saving
                            zvals, xvals, xlabel, yvals, ylabel, __ = self.presenter.get2DdataFromDictionary(
                                dictionary=data[key], dataType="plot", compact=False
                            )
                            saveData = np.vstack((yvals, zvals.T))
                            xvals = list(map(str, xvals.tolist()))
                            labels = ["DT"]
                            for label in xvals:
                                labels.append(label)
                            # Save 2D array
                            kwargs = {"default_name": defaultValue}
                            self.data_handling.on_save_data_as_text(
                                data=[saveData], labels=labels, data_format="%.2f", **kwargs
                            )
                    # 1D - batch
                    elif evt.GetId() == ID_saveDataCSVDocument1D:
                        if not (self._document_type == "Input data" or self._document_type == "Statistical"):
                            for key in data:
                                stripped_key_name = key.replace(" ", "")
                                defaultValue = "DT_1D_{}_{}{}{}".format(
                                    basename, name_modifier, stripped_key_name, self.config.saveExtension
                                )
                                # Get data from the document
                                dtX = data[key]["yvals"]
                                ylabel = data[key]["xlabels"]
                                try:
                                    dtY = data[key]["yvals1D"]
                                except KeyError:
                                    msg = "Missing data. Cancelling operation."
                                    self.presenter.view.SetStatusText(msg, 3)
                                    continue
                                kwargs = {"default_name": defaultValue}
                                self.data_handling.on_save_data_as_text(
                                    data=[dtX, dtY], labels=[ylabel, "Intensity"], data_format="%.4f", **kwargs
                                )

                # Save 1D/2D - single
                else:
                    name_modifier = ""
                    if self._document_type == "Drift time (2D, EIC)":
                        data = self._document_data.IMS2Dions
                    elif self._document_type == "Drift time (2D, combined voltages, EIC)":
                        data = self._document_data.IMS2DCombIons
                        name_modifier = "_CV_"
                    elif self._document_type == "Drift time (2D, processed, EIC)":
                        data = self._document_data.IMS2DionsProcess
                    elif self._document_type == "Input data":
                        data = self._document_data.IMS2DcompData
                    elif self._document_type == "Statistical":
                        data = self._document_data.IMS2DstatsData
                    # Save RMSD matrix
                    out = self._item_leaf.split(":")
                    if out[0] == "RMSD Matrix":
                        if evt.GetId() == ID_saveDataCSVDocument:
                            saveFileName = self.presenter.getImageFilename(prefix=True, csv=True, defaultValue="DT_")
                        if saveFileName == "" or saveFileName is None:
                            saveFileName = "DT_"

                        # Its a bit easier to save data with text labels using pandas df,
                        # so data is reshuffled to pandas dataframe and then saved
                        # in a standard .csv format
                        filename = "".join(
                            [self._document_data.path, "\\", saveFileName, self._item_leaf, self.config.saveExtension]
                        )
                        zvals, xylabels, __ = self.presenter.get2DdataFromDictionary(
                            dictionary=data[self._item_leaf], plotType="Matrix", compact=False
                        )
                        saveData = pd.DataFrame(data=zvals, index=xylabels, columns=xylabels)
                        saveData.to_csv(path_or_buf=filename, sep=self.config.saveDelimiter, header=True, index=True)
                    # Save 2D - single
                    elif self._item_leaf != "RMSD Matrix" and evt.GetId() == ID_saveDataCSVDocument:
                        defaultValue = "DT_2D_{}_{}{}{}".format(
                            basename, name_modifier, self._item_leaf, self.config.saveExtension
                        )

                        zvals, xvals, xlabel, yvals, ylabel, __ = self.presenter.get2DdataFromDictionary(
                            dictionary=data[self._item_leaf], dataType="plot", compact=False
                        )
                        saveData = np.vstack((yvals, zvals.T))
                        try:
                            xvals = list(map(str, xvals.tolist()))
                        except AttributeError:
                            xvals = list(map(str, xvals))
                        labels = ["DT"]
                        for label in xvals:
                            labels.append(label)
                        # Save 2D array
                        kwargs = {"default_name": defaultValue}
                        self.data_handling.on_save_data_as_text(
                            data=[saveData], labels=labels, data_format="%.2f", **kwargs
                        )
                    # Save 1D - single
                    elif self._item_leaf != "RMSD Matrix" and evt.GetId() == ID_saveDataCSVDocument1D:
                        defaultValue = "DT_1D_{}_{}{}{}".format(
                            basename, name_modifier, self._item_leaf, self.config.saveExtension
                        )

                        # Get data from the document
                        dtX = data[self._item_leaf]["yvals"]
                        ylabel = data[self._item_leaf]["xlabels"]
                        try:
                            dtY = data[self._item_leaf]["yvals1D"]
                        except KeyError:
                            msg = "Missing data. Cancelling operation."
                            self.presenter.view.SetStatusText(msg, 3)
                            return
                        kwargs = {"default_name": defaultValue}
                        self.data_handling.on_save_data_as_text(
                            data=[dtX, dtY], labels=[ylabel, "Intensity"], data_format="%.4f", **kwargs
                        )
        else:
            return

    def onOpenDocInfo(self, evt):

        self.presenter.currentDoc = self.on_enable_document()
        document_title = self.on_enable_document()
        if self.presenter.currentDoc == "Documents":
            return
        document = self.presenter.documentsDict.get(document_title, None)

        if document is None:
            return

        for key in self.presenter.documentsDict:
            print(self.presenter.documentsDict[key].title)

        if self._indent == 2 and any(
            self._document_type in itemType for itemType in ["Drift time (2D)", "Drift time (2D, processed)"]
        ):
            kwargs = {"currentTool": "plot2D", "itemType": self._document_type, "extractData": None}
            self.panelInfo = panelDocumentInfo(self, self.presenter, self.config, self.icons, document, **kwargs)
        elif self._indent == 3 and any(
            self._document_type in itemType
            for itemType in [
                "Drift time (2D, EIC)",
                "Drift time (2D, combined voltages, EIC)",
                "Drift time (2D, processed, EIC)",
                "Input data",
            ]
        ):
            kwargs = {"currentTool": "plot2D", "itemType": self._document_type, "extractData": self._item_leaf}
            self.panelInfo = panelDocumentInfo(self, self.presenter, self.config, self.icons, document, **kwargs)
        else:

            kwargs = {"currentTool": "summary", "itemType": None, "extractData": None}
            self.panelInfo = panelDocumentInfo(self, self.presenter, self.config, self.icons, document, **kwargs)

        self.panelInfo.Show()

    def add_document(self, docData, expandAll=False, expandItem=None):
        """
        Append document to tree
        expandItem : object data, to expand specified item
        """
        # Get title for added data
        title = byte2str(docData.title)

        if not title:
            title = "Document"
        # Get root
        root = self.GetRootItem()

        item, cookie = self.GetFirstChild(self.GetRootItem())
        while item.IsOk():
            if self.GetItemText(item) == title:
                self.Delete(item)
            item, cookie = self.GetNextChild(root, cookie)

        # update document with new attributes
        if not hasattr(docData, "other_data"):
            setattr(docData, "other_data", {})
            print("Added missing attributute ('other_data') to document")

        if not hasattr(docData, "tandem_spectra"):
            setattr(docData, "tandem_spectra", {})
            print("Added missing attributute ('tandem_spectra') to document")

        if not hasattr(docData, "file_reader"):
            setattr(docData, "file_reader", {})
            print("Added missing attributute ('file_reader') to document")

        if not hasattr(docData, "app_data"):
            setattr(docData, "app_data", {})
            print("Added missing attributute ('app_data') to document")

        if not hasattr(docData, "last_saved"):
            setattr(docData, "last_saved", {})
            print("Added missing attributute ('last_saved') to document")

        if not hasattr(docData, "metadata"):
            setattr(docData, "metadata", {})
            print("Added missing attributute ('app_data') to document")

        # update document to latest version

        # Add document
        docItem = self.AppendItem(self.GetRootItem(), title)
        self.SetFocusedItem(docItem)
        self.SetItemImage(docItem, self.bulets_dict["document_on"], wx.TreeItemIcon_Normal)
        self.title = title
        self.SetPyData(docItem, docData)

        # Add annotations to document tree
        if hasattr(docData, "dataType"):
            annotsItem = self.AppendItem(docItem, docData.dataType)
            self.SetItemImage(annotsItem, self.bulets_dict["annot_on"], wx.TreeItemIcon_Normal)
            self.SetPyData(annotsItem, docData.dataType)

        if hasattr(docData, "fileFormat"):
            annotsItem = self.AppendItem(docItem, docData.fileFormat)
            self.SetItemImage(annotsItem, self.bulets_dict["annot_on"], wx.TreeItemIcon_Normal)
            self.SetPyData(annotsItem, docData.fileFormat)

        if hasattr(docData, "fileInformation"):
            if docData.fileInformation is not None:
                annotsItem = self.AppendItem(docItem, "Sample information")
                self.SetPyData(annotsItem, docData.fileInformation)
                self.SetItemImage(annotsItem, self.bulets_dict["annot_on"], wx.TreeItemIcon_Normal)

        if docData.gotMS:
            annotsItemParent = self.AppendItem(docItem, "Mass Spectrum")
            self.SetPyData(annotsItemParent, docData.massSpectrum)
            self.SetItemImage(annotsItemParent, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)

            # add unidec results
            if "unidec" in docData.massSpectrum:
                docIonItem = self.AppendItem(annotsItemParent, "UniDec")
                self.SetItemImage(docIonItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
                for annotData in docData.massSpectrum["unidec"]:
                    annotsItem = self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.massSpectrum["unidec"][annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)

            # add annotations
            if "annotations" in docData.massSpectrum and len(docData.massSpectrum["annotations"]) > 0:
                docIonItem = self.AppendItem(annotsItemParent, "Annotations")
                self.SetItemImage(docIonItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)
                for annotData in docData.massSpectrum["annotations"]:
                    annotsItem = self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.massSpectrum["annotations"][annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)

        if docData.smoothMS:
            annotsItemParent = self.AppendItem(docItem, "Mass Spectrum (processed)")
            self.SetItemImage(annotsItemParent, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
            self.SetPyData(annotsItemParent, docData.smoothMS)
            # add unidec results
            if "unidec" in docData.smoothMS:
                docIonItem = self.AppendItem(annotsItemParent, "UniDec")
                self.SetItemImage(docIonItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
                for annotData in docData.smoothMS["unidec"]:
                    annotsItem = self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.smoothMS["unidec"][annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)

            # add annotations
            if "annotations" in docData.smoothMS and len(docData.smoothMS["annotations"]) > 0:
                docIonItem = self.AppendItem(annotsItemParent, "Annotations")
                self.SetItemImage(docIonItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)
                for annotData in docData.smoothMS["annotations"]:
                    annotsItem = self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.smoothMS["annotations"][annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)

        if docData.gotMultipleMS:
            docIonItem = self.AppendItem(docItem, "Mass Spectra")
            self.SetItemImage(docIonItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
            self.SetPyData(docIonItem, docData.multipleMassSpectrum)
            for annotData in docData.multipleMassSpectrum:
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.multipleMassSpectrum[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["mass_spec_on"], wx.TreeItemIcon_Normal)

                # add unidec results
                if "unidec" in docData.multipleMassSpectrum[annotData]:
                    docIonItemInner = self.AppendItem(annotsItem, "UniDec")
                    self.SetItemImage(docIonItemInner, self.bulets_dict["mass_spec_on"], wx.TreeItemIcon_Normal)
                    for annotDataInner in docData.multipleMassSpectrum[annotData]["unidec"]:
                        annotsItemInner = self.AppendItem(docIonItemInner, annotDataInner)
                        self.SetPyData(
                            annotsItemInner, docData.multipleMassSpectrum[annotData]["unidec"][annotDataInner]
                        )
                        self.SetItemImage(annotsItemInner, self.bulets_dict["mass_spec_on"], wx.TreeItemIcon_Normal)

                # add annotations
                if (
                    "annotations" in docData.multipleMassSpectrum[annotData]
                    and len(docData.multipleMassSpectrum[annotData]["annotations"]) > 0
                ):
                    docIonAnnotItem = self.AppendItem(annotsItem, "Annotations")
                    self.SetItemImage(docIonAnnotItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)
                    for annotNameData in docData.multipleMassSpectrum[annotData]["annotations"]:
                        annotsAnnotItem = self.AppendItem(docIonAnnotItem, annotNameData)
                        self.SetPyData(
                            annotsAnnotItem, docData.multipleMassSpectrum[annotData]["annotations"][annotNameData]
                        )
                        self.SetItemImage(annotsAnnotItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)

        if len(docData.tandem_spectra) > 0:
            docIonItem = self.AppendItem(docItem, "Tandem Mass Spectra")
            self.SetItemImage(docIonItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
            self.SetPyData(docIonItem, docData.tandem_spectra)

        if docData.got1RT:
            annotsItem = self.AppendItem(docItem, "Chromatogram")
            self.SetPyData(annotsItem, docData.RT)
            self.SetItemImage(annotsItem, self.bulets_dict["rt"], wx.TreeItemIcon_Normal)

        if hasattr(docData, "gotMultipleRT"):
            if docData.gotMultipleRT:
                docIonItem = self.AppendItem(docItem, "Chromatograms (EIC)")
                self.SetItemImage(docIonItem, self.bulets_dict["rt"], wx.TreeItemIcon_Normal)
                self.SetPyData(docIonItem, docData.multipleRT)
                for annotData, __ in natsorted(list(docData.multipleRT.items())):
                    annotsItem = self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.multipleRT[annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["rt_on"], wx.TreeItemIcon_Normal)

        if docData.got1DT:
            annotsItem = self.AppendItem(docItem, "Drift time (1D)")
            self.SetPyData(annotsItem, docData.DT)
            self.SetItemImage(annotsItem, self.bulets_dict["drift_time"], wx.TreeItemIcon_Normal)

        if hasattr(docData, "gotMultipleDT"):
            if docData.gotMultipleDT:
                docIonItem = self.AppendItem(docItem, "Drift time (1D, EIC)")
                self.SetItemImage(docIonItem, self.bulets_dict["drift_time"], wx.TreeItemIcon_Normal)
                self.SetPyData(docIonItem, docData.multipleDT)
                for annotData, __ in natsorted(list(docData.multipleDT.items())):
                    annotsItem = self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.multipleDT[annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["drift_time_on"], wx.TreeItemIcon_Normal)

        if docData.gotExtractedDriftTimes:
            docIonItem = self.AppendItem(docItem, "Drift time (1D, EIC, DT-IMS)")
            self.SetItemImage(docIonItem, self.bulets_dict["drift_time"], wx.TreeItemIcon_Normal)
            self.SetPyData(docIonItem, docData.IMS1DdriftTimes)
            for annotData, __ in natsorted(list(docData.IMS1DdriftTimes.items())):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS1DdriftTimes[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["drift_time_on"], wx.TreeItemIcon_Normal)

        if docData.got2DIMS:
            annotsItem = self.AppendItem(docItem, "Drift time (2D)")
            self.SetPyData(annotsItem, docData.IMS2D)
            self.SetItemImage(annotsItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)

        if docData.got2Dprocess or len(docData.IMS2Dprocess) > 0:
            annotsItem = self.AppendItem(docItem, "Drift time (2D, processed)")
            self.SetPyData(annotsItem, docData.IMS2Dprocess)
            self.SetItemImage(annotsItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)

        if docData.gotExtractedIons:
            docIonItem = self.AppendItem(docItem, "Drift time (2D, EIC)")
            self.SetItemImage(docIonItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)
            self.SetPyData(docIonItem, docData.IMS2Dions)
            for annotData, __ in natsorted(list(docData.IMS2Dions.items())):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2Dions[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)

        if docData.gotCombinedExtractedIons:
            docIonItem = self.AppendItem(docItem, "Drift time (2D, combined voltages, EIC)")
            self.SetItemImage(docIonItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)
            self.SetPyData(docIonItem, docData.IMS2DCombIons)
            for annotData, __ in natsorted(list(docData.IMS2DCombIons.items())):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2DCombIons[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)

        if docData.gotCombinedExtractedIonsRT:
            docIonItem = self.AppendItem(docItem, "Chromatograms (combined voltages, EIC)")
            self.SetItemImage(docIonItem, self.bulets_dict["rt"], wx.TreeItemIcon_Normal)
            self.SetPyData(docIonItem, docData.IMSRTCombIons)
            for annotData, __ in natsorted(list(docData.IMSRTCombIons.items())):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMSRTCombIons[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["rt_on"], wx.TreeItemIcon_Normal)

        if docData.got2DprocessIons:
            docIonItem = self.AppendItem(docItem, "Drift time (2D, processed, EIC)")
            self.SetItemImage(docIonItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)
            self.SetPyData(docIonItem, docData.IMS2DionsProcess)
            for annotData, __ in natsorted(list(docData.IMS2DionsProcess.items())):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2DionsProcess[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)

        if docData.gotCalibration:
            docIonItem = self.AppendItem(docItem, "Calibration peaks")
            self.SetItemImage(docIonItem, self.bulets_dict["calibration"], wx.TreeItemIcon_Normal)
            for annotData, __ in natsorted(list(docData.calibration.items())):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.calibration[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["dots_on"], wx.TreeItemIcon_Normal)

        if docData.gotCalibrationDataset:
            docIonItem = self.AppendItem(docItem, "Calibrants")
            self.SetItemImage(docIonItem, self.bulets_dict["calibration_on"], wx.TreeItemIcon_Normal)
            for annotData in docData.calibrationDataset:
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.calibrationDataset[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["dots_on"], wx.TreeItemIcon_Normal)

        if docData.gotCalibrationParameters:
            annotsItem = self.AppendItem(docItem, "Calibration parameters")
            self.SetPyData(annotsItem, docData.calibrationParameters)
            self.SetItemImage(annotsItem, self.bulets_dict["calibration"], wx.TreeItemIcon_Normal)

        if docData.gotComparisonData:
            docIonItem = self.AppendItem(docItem, "Input data")
            self.SetItemImage(docIonItem, self.bulets_dict["overlay"], wx.TreeItemIcon_Normal)
            for annotData, __ in natsorted(list(docData.IMS2DcompData.items())):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2DcompData[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)

        if docData.gotOverlay or len(docData.IMS2DoverlayData) > 0:
            docIonItem = self.AppendItem(docItem, "Overlay")
            self.SetItemImage(docIonItem, self.bulets_dict["overlay"], wx.TreeItemIcon_Normal)
            self.SetPyData(docIonItem, docData.IMS2DoverlayData)
            for annotData, __ in natsorted(list(docData.IMS2DoverlayData.items())):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2DoverlayData[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)

        if docData.gotStatsData:
            docIonItem = self.AppendItem(docItem, "Statistical")
            self.SetItemImage(docIonItem, self.bulets_dict["overlay"], wx.TreeItemIcon_Normal)
            self.SetPyData(docIonItem, docData.IMS2DstatsData)
            for annotData, __ in natsorted(list(docData.IMS2DstatsData.items())):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2DstatsData[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)

        if hasattr(docData, "DTMZ"):
            if docData.gotDTMZ:
                annotsItem = self.AppendItem(docItem, "DT/MS")
                self.SetPyData(annotsItem, docData.DTMZ)
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)

        if len(docData.other_data) > 0:
            docIonItem = self.AppendItem(docItem, "Annotated data")
            self.SetItemImage(docIonItem, self.bulets_dict["calibration"], wx.TreeItemIcon_Normal)
            self.SetPyData(docIonItem, docData.other_data)
            for annotData, __ in natsorted(list(docData.other_data.items())):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.other_data[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["calibration_on"], wx.TreeItemIcon_Normal)

                # add annotations
                if (
                    "annotations" in docData.other_data[annotData]
                    and len(docData.other_data[annotData]["annotations"]) > 0
                ):
                    docIonAnnotItem = self.AppendItem(annotsItem, "Annotations")
                    self.SetItemImage(docIonAnnotItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)
                    for annotNameData in docData.other_data[annotData]["annotations"]:
                        annotsAnnotItem = self.AppendItem(docIonAnnotItem, annotNameData)
                        self.SetPyData(annotsAnnotItem, docData.other_data[annotData]["annotations"][annotNameData])
                        self.SetItemImage(annotsAnnotItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)

        # Recursively check currently selected document
        self.on_enable_document(loadingData=True, expandAll=expandAll, evt=None)

        # If expandItem is not empty, the Tree will expand specified item
        if expandItem is not None:
            # Change document tree
            try:
                docItem = self.getItemByData(expandItem)
                parent = self.GetItemParent(docItem)
                self.Expand(parent)
            except Exception:
                pass

    def removeDocument(self, evt, deleteItem="", ask_permission=True):
        """
        Remove selected document from the document tree
        """
        # Find the root first
        root = None
        if root is None:
            root = self.GetRootItem()

        try:
            evtID = evt.GetId()
        except AttributeError:
            evtID = None

        if evtID == ID_removeDocument or (evtID is None and deleteItem == ""):
            __, cookie = self.GetFirstChild(self.GetRootItem())

            if ask_permission:
                dlg = DialogBox(
                    exceptionTitle="Are you sure?",
                    exceptionMsg="".join(["Are you sure you would like to delete: ", self._document_data.title, "?"]),
                    type="Question",
                )
                if dlg == wx.ID_NO:
                    self.presenter.onThreading(None, ("Cancelled operation", 4, 5), action="updateStatusbar")
                    return
                else:
                    deleteItem = self._document_data.title

            # Clear all plotsf
            if self.presenter.currentDoc == deleteItem:
                self.panel_plot.on_clear_all_plots()
                self.presenter.currentDoc = None

        if deleteItem == "":
            return

        # Delete item from the list
        if self.ItemHasChildren(root):
            child, cookie = self.GetFirstChild(self.GetRootItem())
            title = self.GetItemText(child)
            iters = 0
            while deleteItem != title and iters < 500:
                child, cookie = self.GetNextChild(self.GetRootItem(), cookie)
                try:
                    title = self.GetItemText(child)
                    iters += 1
                except Exception:
                    pass

            if deleteItem == title:
                if child:
                    print("Deleted {}".format(deleteItem))
                    self.Delete(child)
                    # Remove data from dictionary if removing whole document
                    if evtID == ID_removeDocument or evtID is None:
                        # make sure to clean-up various tables
                        try:
                            self.presenter.view.panelMultipleIons.on_remove_deleted_item(title)
                        except Exception:
                            pass
                        try:
                            self.presenter.view.panelMultipleText.on_remove_deleted_item(title)
                        except Exception:
                            pass
                        try:
                            self.presenter.view.panelMML.on_remove_deleted_item(title)
                        except Exception:
                            pass
                        try:
                            self.presenter.view.panelLinearDT.topP.on_remove_deleted_item(title)
                        except Exception:
                            pass
                        try:
                            self.presenter.view.panelLinearDT.bottomP.on_remove_deleted_item(title)
                        except Exception:
                            pass

                        # delete document
                        del self.presenter.documentsDict[title]
                        self.presenter.currentDoc = None
                        # go to the next document
                        if len(self.presenter.documentsDict) > 0:
                            self.presenter.currentDoc = list(self.presenter.documentsDict.keys())[0]
                            self.on_enable_document()
                        # collect garbage
                        gc.collect()

                    return True
            else:
                return False

    def getItemIDbyName(self, root, title):
        item, cookie = self.GetFirstChild(root)

        while item.IsOk():
            text = self.GetItemText(item)
            if text == title:
                return item
            if self.ItemHasChildren(item):
                match = self.getItemIDbyName(item, title)
                if match.IsOk():
                    return match
            item, cookie = self.GetNextChild(root, cookie)

        return wx.TreeItemId()

    def setAsCurrentDocument(self, title):
        #         docItem = self.AppendItem(self.GetRootItem(), title)

        docItem = self.getItemIDbyName(self.GetRootItem(), title)
        self.SetFocusedItem(docItem)

    def getCurrentDocument(self, e=None):
        item = self.GetSelection()
        if not item:
            return
        while self.GetItemParent(item):
            text = self.GetItemText(item)
            return text

    def onShowSampleInfo(self, evt=None):

        try:
            sample_information = self._document_data.fileInformation.get("SampleDescription", "None")
        except AttributeError:
            sample_information = "N/A"

        kwargs = {"title": "Sample information...", "information": sample_information}

        from gui_elements.panel_fileInformation import panelInformation

        info = panelInformation(self, **kwargs)
        info.Show()

    def on_enable_document(
        self,
        getSelected=False,
        loadingData=False,
        highlightSelected=False,
        expandAll=False,
        expandSelected=None,
        evt=None,
    ):
        """
        Highlights and returns currently selected document
        ---
        Parameters
        ----------
        getSelected
        loadingData: booleat, flag to tell the function that we are loading data
        highlightSelected
        expandAll : boolean, flag to expand or not of the tree
        expandSelected : string, name of item to expand
        """
        root = self.GetRootItem()
        selected = self.GetSelection()
        item, cookie = self.GetFirstChild(root)

        try:
            evtID = evt.GetId()
        except AttributeError:
            evtID = None
        while item.IsOk():
            self.SetItemBold(item, False)
            if loadingData:
                self.CollapseAllChildren(item)
            item, cookie = self.GetNextChild(root, cookie)

        # Select parent document
        if selected is not None:
            item = self.getParentItem(selected, 1)
            try:
                self.SetItemBold(item, True)
            except wx._core.PyAssertionError:
                pass
            if loadingData or evtID == ID_getSelectedDocument:
                self.Expand(item)  # Parent item
                if expandAll:
                    self.ExpandAllChildren(item)

            # window label
            try:
                text = self.GetItemText(item)
                if text != "Documents":
                    #                     try: self.setCurrentDocument(text)
                    #                     except Exception: pass
                    self.presenter.currentDoc = text
                    self.view.SetTitle(
                        "ORIGAMI - v{} - {} ({})".format(self.config.version, text, self._document_data.dataType)
                    )
            except Exception:
                self.view.SetTitle("ORIGAMI - v{}".format(self.config.version))

            # status text
            try:
                parameters = self._document_data.parameters
                msg = "{}-{}".format(parameters.get("startMS", ""), parameters.get("endMS", ""))
                if msg == "-":
                    msg = ""
                self.presenter.view.SetStatusText(msg, 1)
                msg = "MSMS: {}".format(parameters.get("setMS", ""))
                if msg == "MSMS: ":
                    msg = ""
                self.presenter.view.SetStatusText(msg, 2)
            except Exception:
                pass

            # In case we also interested in selected item
            if getSelected:
                selectedText = self.GetItemText(selected)
                if highlightSelected:
                    self.SetItemBold(selected, True)
                return text, selected, selectedText
            else:
                return text

        if evt is not None:
            evt.Skip()

    def enableCurrentDocument(
        self,
        getSelected=False,
        loadingData=False,
        highlightSelected=False,
        expandAll=False,
        expandSelected=None,
        evt=None,
    ):
        """
        Highlights and returns currently selected document
        ---
        Parameters
        ----------
        getSelected
        loadingData: booleat, flag to tell the function that we are loading data
        highlightSelected
        expandAll : boolean, flag to expand or not of the tree
        expandSelected : string, name of item to expand
        """
        root = self.GetRootItem()
        selected = self.GetSelection()
        item, cookie = self.GetFirstChild(root)

        try:
            evtID = evt.GetId()
        except AttributeError:
            evtID = None
        while item.IsOk():
            self.SetItemBold(item, False)
            if loadingData:
                self.CollapseAllChildren(item)
            item, cookie = self.GetNextChild(root, cookie)

        # Select parent document
        if selected is not None:
            item = self.getParentItem(selected, 1)
            try:
                self.SetItemBold(item, True)
            except wx._core.PyAssertionError:
                pass
            if loadingData or evtID == ID_getSelectedDocument:
                self.Expand(item)  # Parent item
                if expandAll:
                    self.ExpandAllChildren(item)

            # window label
            try:
                text = self.GetItemText(item)
                if text != "Documents":
                    #                     try: self.setCurrentDocument(text)
                    #                     except Exception: pass
                    self.presenter.currentDoc = text
                    self.view.SetTitle(
                        "ORIGAMI - {} - {} ({})".format(self.config.version, text, self._document_data.dataType)
                    )
            except Exception:
                self.view.SetTitle(" - ".join(["ORIGAMI", self.config.version]))

            # In case we also interested in selected item
            if getSelected:
                selectedText = self.GetItemText(selected)
                if highlightSelected:
                    self.SetItemBold(selected, True)
                return text, selected, selectedText
            else:
                return text

        if evt is not None:
            evt.Skip()

    def onExpandItem(self, item, evt):
        """ function to expand selected item """
        pass

    def setCurrentDocument(self, docTitle, e=None):
        """ Highlight currently selected document from tables """
        root = None
        if root is None:
            root = self.GetRootItem()
        if self.ItemHasChildren(root):
            firstchild, cookie = self.GetFirstChild(self.GetRootItem())
            title = self.GetItemText(firstchild)
            if title == docTitle:
                self.SetItemBold(firstchild, True)
                self.presenter.currentDoc = docTitle

        self._document_data = self.presenter.documentsDict[docTitle]
        print(self._document_data)

    def get_item_indent(self, item):
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

    def getParentItem(self, item, level, getSelected=False):
        """ Get parent item for selected item and level"""
        # Get item
        for x in range(level, self.get_item_indent(item)):
            item = self.GetItemParent(item)

        if getSelected:
            itemText = self.GetItemText(item)
            return item, itemText
        else:
            return item

    def getItemByData(self, data, root=None, cookie=0):
        """Get item by its data."""

        # get root
        if root is None:
            root = self.GetRootItem()

        # check children
        if self.ItemHasChildren(root):
            firstchild, cookie = self.GetFirstChild(root)
            if self.GetPyData(firstchild) is data:
                return firstchild
            matchedItem = self.getItemByData(data, firstchild, cookie)
            if matchedItem:
                return matchedItem

        # check siblings
        child = self.GetNextSibling(root)
        if child and child.IsOk():
            if self.GetPyData(child) is data:
                return child
            matchedItem = self.getItemByData(data, child, cookie)
            if matchedItem:
                return matchedItem

        # no such item found
        return False

    def on_open_MGF_file(self, evt=None):
        dlg = wx.FileDialog(
            self.presenter.view, "Open MGF file", wildcard="*.mgf; *.MGF", style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR
        )
        if dlg.ShowModal() == wx.ID_OK:
            tstart = time.time()
            path = dlg.GetPath()
            print("Opening {}...".format(path))
            reader = io_mgf.MGFreader(filename=path)
            print("Created file reader. Loading scans...")

            basename = os.path.basename(path)
            data = reader.get_n_scans(n_scans=50000)
            kwargs = {"data_type": "Type: MS/MS", "file_format": "Format: .mgf"}
            document = self.presenter.on_create_document(basename, path, **kwargs)

            # add data to document
            document.tandem_spectra = data
            document.file_reader = {"data_reader": reader}

            title = "Precursor: {:.4f} [{}]".format(
                data["Scan 1"]["scan_info"]["precursor_mz"], data["Scan 1"]["scan_info"]["precursor_charge"]
            )
            self.panel_plot.on_plot_centroid_MS(data["Scan 1"]["xvals"], data["Scan 1"]["yvals"], title=title)

            self.data_handling.on_update_document(document, "document")
            print("It took {:.4f} seconds to load {}".format(time.time() - tstart, basename))

    def on_open_MGF_file_fcn(self, evt):

        if not self.config.threading:
            self.on_open_MGF_file(evt)
        else:
            self.onThreading(evt, (evt,), action="load_mgf")

    def on_open_mzML_file(self, evt=None):
        dlg = wx.FileDialog(
            self.presenter.view,
            "Open mzML file",
            wildcard="*.mzML; *.MZML",
            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            tstart = time.time()
            path = dlg.GetPath()
            print("Opening {}...".format(path))
            reader = io_mzml.mzMLreader(filename=path)
            print("Created file reader. Loading scans...")

            basename = os.path.basename(path)
            data = reader.get_n_scans(n_scans=999999)
            kwargs = {"data_type": "Type: MS/MS", "file_format": "Format: .mzML"}
            document = self.presenter.on_create_document(basename, path, **kwargs)

            # add data to document
            document.tandem_spectra = data
            document.file_reader = {"data_reader": reader}

            title = "Precursor: {:.4f} [{}]".format(
                data["Scan 1"]["scan_info"]["precursor_mz"], data["Scan 1"]["scan_info"]["precursor_charge"]
            )
            self.panel_plot.on_plot_centroid_MS(data["Scan 1"]["xvals"], data["Scan 1"]["yvals"], title=title)

            self.data_handling.on_update_document(document, "document")
            print("It took {:.4f} seconds to load {}".format(time.time() - tstart, basename))

    def on_open_mzML_file_fcn(self, evt):

        if not self.config.threading:
            self.on_open_mzML_file(evt)
        else:
            self.onThreading(evt, (evt,), action="load_mzML")

    def on_open_MSMS_viewer(self, evt=None, **kwargs):
        from widgets.panel_tandem_spectra_viewer import PanelTandemSpectraViewer

        self.panelTandemSpectra = PanelTandemSpectraViewer(
            self.presenter.view, self.presenter, self.config, self.icons, **kwargs
        )
        self.panelTandemSpectra.Show()

    def on_process_UVPD(self, evt=None, **kwargs):
        from widgets.panel_UVPD_editor import PanelUVPDEditor

        self.panelUVPD = PanelUVPDEditor(self.presenter.view, self.presenter, self.config, self.icons, **kwargs)
        self.panelUVPD.Show()

    def on_open_extract_DTMS(self, evt):
        from gui_elements.panel_process_extract_DTMS import PanelProcessExtractDTMS

        self.PanelProcessExtractDTMS = PanelProcessExtractDTMS(
            self.presenter.view, self.presenter, self.config, self.icons
        )
        self.PanelProcessExtractDTMS.Show()

    def on_open_peak_picker(self, evt, **kwargs):
        """Open peak picker"""
        from gui_elements.panel_peak_picker import panel_peak_picker

        # get data
        document, data, dataset = self._on_event_get_mass_spectrum(**kwargs)

        # initilize peak picker
        panel_peak_picker = panel_peak_picker(
            self.presenter.view,
            self.presenter,
            self.config,
            self.icons,
            document=document,
            mz_data=data,
            dataset_name=dataset,
            document_title=document.title,
        )
        panel_peak_picker.Show()

    def on_open_extract_data(self, evt, **kwargs):
        from gui_elements.panel_process_extract_data import PanelProcessExtractData

        document = self.data_handling._on_get_document()

        # initilize data extraction panel
        self.PanelProcessExtractData = PanelProcessExtractData(
            self.presenter.view,
            self.presenter,
            self.config,
            self.icons,
            document=document,
            document_title=document.title,
        )
        self.PanelProcessExtractData.Show()

    def on_open_UniDec(self, evt, **kwargs):
        """Open UniDec panel which allows processing and visualisation"""
        from widgets.UniDec.panel_process_UniDec import PanelProcessUniDec

        document, data, dataset = self._on_event_get_mass_spectrum(**kwargs)

        try:
            if self.PanelProcessUniDec.document_title == document.title:
                logger.warning("Panel is already open")
                self.PanelProcessUniDec.SetFocus()
                return
        except (AttributeError, RuntimeError):
            pass

        # initilize data extraction panel
        self.PanelProcessUniDec = PanelProcessUniDec(
            self.presenter.view,
            self.presenter,
            self.config,
            self.icons,
            document=document,
            mz_data=data,
            dataset_name=dataset,
            document_title=document.title,
            **kwargs,
        )
        self.PanelProcessUniDec.Show()

    def on_add_mzID_file(self, evt):
        document = self.data_handling._on_get_document()

        dlg = wx.FileDialog(
            self.presenter.view,
            "Open mzIdentML file",
            wildcard="*.mzid; *.mzid.gz; *mzid.zip",
            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            print("Adding identification information to {}".format(document.title))
            tstart = time.time()
            path = dlg.GetPath()
            reader = io_mzid.MZIdentReader(filename=path)

            # check if data reader is present
            try:
                index_dict = document.file_reader["data_reader"].create_title_map(document.tandem_spectra)
            except KeyError:
                print("Missing file reader. Creating a new instance of the reader...")
                if document.fileFormat == "Format: .mgf":
                    document.file_reader["data_reader"] = io_mgf.MGFreader(filename=document.path)
                elif document.fileFormat == "Format: .mzML":
                    document.file_reader["data_reader"] = io_mzml.mzMLreader(filename=document.path)
                else:
                    DialogBox(
                        exceptionTitle="Error",
                        exceptionMsg="{} not supported yet!".format(document.fileFormat),
                        type="Error",
                        exceptionPrint=True,
                    )
                    return
                try:
                    index_dict = document.file_reader["data_reader"].create_title_map(document.tandem_spectra)
                except AttributeError:
                    DialogBox(
                        exceptionTitle="Error",
                        exceptionMsg="Cannot add identification information to {} yet!".format(document.fileFormat),
                        type="Error",
                        exceptionPrint=True,
                    )
                    return

            tandem_spectra = reader.match_identification_with_peaklist(
                peaklist=deepcopy(document.tandem_spectra), index_dict=index_dict
            )

            document.tandem_spectra = tandem_spectra

            self.data_handling.on_update_document(document, "document")
            print("It took {:.4f} seconds to annotate {}".format(time.time() - tstart, document.title))

    def on_add_mzID_file_fcn(self, evt):

        if not self.config.threading:
            self.on_add_mzID_file(evt)
        else:
            self.onThreading(evt, (evt,), action="add_mzidentml_annotations")

    def on_open_thermo_file_fcn(self, evt):

        if not self.config.threading:
            self.on_open_thermo_file(evt)
        else:
            self.onThreading(evt, (evt,), action="load_thermo_RAW")

    def on_open_thermo_file(self, evt):
        dlg = wx.FileDialog(
            self.presenter.view,
            "Open Thermo file",
            wildcard="*.raw; *.RAW",
            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            tstart = time.time()
            path = dlg.GetPath()
            print("Opening {}...".format(path))
            reader = io_thermo.thermoRAWreader(filename=path)
            print("Created file reader. Loading scans...")

            # get info
            info = reader.get_scan_info()

            # get chromatogram
            rtX, rtY = reader.get_tic()
            self.panel_plot.on_plot_RT(rtX, rtY, "Time (min)", set_page=False)

            mass_spectra = reader.get_spectrum_for_each_filter()
            chromatograms = reader.get_chromatogram_for_each_filter()
            #             rtX, rtY = reader._stitch_chromatograms(chromatograms)

            # get average mass spectrum
            msX, msY = reader.get_average_spectrum()
            xlimits = [np.min(msX), np.max(msX)]
            name_kwargs = {"document": None, "dataset": None}
            self.panel_plot.on_plot_MS(msX, msY, xlimits=xlimits, set_page=True, **name_kwargs)

            basename = os.path.basename(path)
            kwargs = {"data_type": "Type: MS", "file_format": "Format: Thermo (.RAW)"}
            document = self.presenter.on_create_document(basename, path, **kwargs)

            # add data to document
            document.got1RT = True
            document.RT = {"xvals": rtX, "yvals": rtY, "xlabels": "Time (min)"}

            document.gotMS = True
            document.massSpectrum = {"xvals": msX, "yvals": msY, "xlabels": "m/z (Da)", "xlimits": xlimits}

            document.gotMultipleMS = True
            document.multipleMassSpectrum = mass_spectra

            document.gotMultipleRT = True
            document.multipleRT = chromatograms

            document.file_reader = {"data_reader": reader}

            self.data_handling.on_update_document(document, "document")
            print("It took {:.4f} seconds to load {}".format(time.time() - tstart, document.title))

    def on_delete_data__ions(self, document, document_title, delete_type, ion_name=None, confirm_deletion=False):
        """
        Delete data from document tree and document

        Parameters
        ----------
        document: py object
            document object
        document_title: str
            name of the document - also found in document.title
        delete_type: str
            type of deletion. Accepted: `ions.all`, `ions.one`
        ion_name: str
            name of the EIC item to be deleted
        confirm_deletion: bool
            check whether all items should be deleted before performing the task


        Returns
        -------
        document: py object
            updated document object
        outcome: bool
            result of positive/negative deletion of document tree object
        """

        if confirm_deletion:
            msg = "Are you sure you want to continue with this action?" + "\nThis action cannot be undone."
            dlg = DialogBox(exceptionMsg=msg, type="Question")
            if dlg == wx.ID_NO:
                logger.info("The operation was cancelled")
                return document, True

        docItem = False
        main_docItem = self.getItemByData(document.ion2Dmaps)
        # delete all ions
        if delete_type == "ions.all":
            docItem = self.getItemByData(document.ion2Dmaps)
            self.ionPanel.on_remove_deleted_item(list(document.ion2Dmaps.keys()), document_title)
            document.ion2Dmaps = {}
            document.gotIon2Dmaps = False
        # delete one ion
        elif delete_type == "ions.one":
            self.ionPanel.on_remove_deleted_item([ion_name], document_title)
            docItem = self.getItemByData(document.ion2Dmaps[ion_name])
            try:
                del document.ion2Dmaps[ion_name]
            except KeyError:
                msg = (
                    "Failed to delete {} from  2D (EIC) dictionary. ".format(ion_name)
                    + "You probably have reselect it in the document tree"
                )
                logger.warning(msg)

        if len(document.ion2Dmaps) == 0:
            document.gotIon2Dmaps = False
            try:
                self.Delete(main_docItem)
            except Exception:
                logger.warning("Failed to delete item: 2D (EIC) from the document tree")

        if docItem is False:
            return document, False
        else:
            self.Delete(docItem)
            return document, True

    def on_delete_data__text(self, document, document_title, delete_type, ion_name=None, confirm_deletion=False):
        """
        Delete data from document tree and document

        Parameters
        ----------
        document: py object
            document object
        document_title: str
            name of the document - also found in document.title
        delete_type: str
            type of deletion. Accepted: `ions.all`, `ions.one`
        ion_name: str
            name of the EIC item to be deleted
        confirm_deletion: bool
            check whether all items should be deleted before performing the task


        Returns
        -------
        document: py object
            updated document object
        outcome: bool
            result of positive/negative deletion of document tree object
        """

        if confirm_deletion:
            msg = "Are you sure you want to continue with this action?" + "\nThis action cannot be undone."
            dlg = DialogBox(exceptionMsg=msg, type="Question")
            if dlg == wx.ID_NO:
                logger.info("The operation was cancelled")
                return document, True

        docItem = False
        main_docItem = self.getItemByData(document.ion2Dmaps)
        # delete all ions
        if delete_type == "text.all":
            docItem = self.getItemByData(document.ion2Dmaps)
            self.ionPanel.on_remove_deleted_item(list(document.ion2Dmaps.keys()), document_title)
            document.ion2Dmaps = {}
            document.gotIon2Dmaps = False
        # delete one ion
        elif delete_type == "text.one":
            self.ionPanel.on_remove_deleted_item([ion_name], document_title)
            docItem = self.getItemByData(document.ion2Dmaps[ion_name])
            try:
                del document.ion2Dmaps[ion_name]
            except KeyError:
                msg = (
                    "Failed to delete {} from  2D (EIC) dictionary. ".format(ion_name)
                    + "You probably have reselect it in the document tree"
                )
                logger.warning(msg)

        if len(document.ion2Dmaps) == 0:
            document.gotIon2Dmaps = False
            try:
                self.Delete(main_docItem)
            except Exception:
                logger.warning("Failed to delete item: 2D (EIC) from the document tree")

        if docItem is False:
            return document, False
        else:
            self.Delete(docItem)
            return document, True

    def on_delete_data__document(self, document_title, ask_permission=True):
        """
        Remove selected document from the document tree
        """
        document = self.data_handling._on_get_document(document_title)

        if ask_permission:
            dlg = DialogBox(
                exceptionTitle="Are you sure?",
                exceptionMsg="Are you sure you would like to delete {}".format(document_title),
                type="Question",
            )
            if dlg == wx.ID_NO:
                self.presenter.onThreading(None, ("Cancelled operation", 4, 5), action="updateStatusbar")
                return

        main_docItem = self.getItemByData(document)

        # Delete item from the list
        if self.ItemHasChildren(main_docItem):
            child, cookie = self.GetFirstChild(self.GetRootItem())
            title = self.GetItemText(child)
            iters = 0
            while document_title != title and iters < 500:
                child, cookie = self.GetNextChild(self.GetRootItem(), cookie)
                try:
                    title = self.GetItemText(child)
                    iters += 1
                except Exception:
                    pass

            if document_title == title:
                if child:
                    print("Deleted {}".format(document_title))
                    self.Delete(child)
                    # make sure to clean-up various tables
                    try:
                        self.presenter.view.panelMultipleIons.on_remove_deleted_item(title)
                    except Exception:
                        pass
                    try:
                        self.presenter.view.panelMultipleText.on_remove_deleted_item(title)
                    except Exception:
                        pass
                    try:
                        self.presenter.view.panelMML.on_remove_deleted_item(title)
                    except Exception:
                        pass
                    try:
                        self.presenter.view.panelLinearDT.topP.on_remove_deleted_item(title)
                    except Exception:
                        pass
                    try:
                        self.presenter.view.panelLinearDT.bottomP.on_remove_deleted_item(title)
                    except Exception:
                        pass

                    # delete document
                    del self.presenter.documentsDict[document_title]
                    self.presenter.currentDoc = None

                    # go to the next document
                    if len(self.presenter.documentsDict) > 0:
                        self.presenter.currentDoc = list(self.presenter.documentsDict.keys())[0]
                        self.on_enable_document()

                    # collect garbage
                    gc.collect()

    def on_delete_data__heatmap(self, document, document_title, delete_type, ion_name=None, confirm_deletion=False):
        """
        Delete data from document tree and document

        Parameters
        ----------
        document: py object
            document object
        document_title: str
            name of the document - also found in document.title
        delete_type: str
            type of deletion. Accepted: `file.all`, `file.one`
        ion_name: str
            name of the unsupervised item to be deleted
        confirm_deletion: bool
            check whether all items should be deleted before performing the task


        Returns
        -------
        document: py object
            updated document object
        outcome: bool
            result of positive/negative deletion of document tree object
        """

        if confirm_deletion:
            msg = "Are you sure you want to continue with this action?" + "\nThis action cannot be undone."
            dlg = DialogBox(exceptionMsg=msg, type="Question")
            if dlg == wx.ID_NO:
                logger.info("The operation was cancelled")
                return document, True

        docItem = False
        if delete_type == "heatmap.all.one":
            delete_types = [
                "heatmap.raw.one",
                "heatmap.raw.one.processed",
                "heatmap.processed.one",
                "heatmap.combined.one",
                "heatmap.rt.one",
            ]
        elif delete_type == "heatmap.all.all":
            delete_types = ["heatmap.raw.all", "heatmap.processed.all", "heatmap.combined.all", "heatmap.rt.all"]
        else:
            delete_types = [delete_type]

        if document is None:
            return None, False

        # delete all classes
        if delete_type.endswith(".all"):
            for delete_type in delete_types:
                if delete_type == "heatmap.raw.all":
                    docItem = self.getItemByData(document.IMS2Dions)
                    document.IMS2Dions = {}
                    document.gotExtractedIons = False
                if delete_type == "heatmap.processed.all":
                    docItem = self.getItemByData(document.IMS2DionsProcess)
                    document.IMS2DionsProcess = {}
                    document.got2DprocessIons = False
                if delete_type == "heatmap.rt.all":
                    docItem = self.getItemByData(document.IMSRTCombIons)
                    document.IMSRTCombIons = {}
                    document.gotCombinedExtractedIonsRT = False
                if delete_type == "heatmap.combined.all":
                    docItem = self.getItemByData(document.IMS2DCombIons)
                    document.IMS2DCombIons = {}
                    document.gotCombinedExtractedIons = False

                try:
                    self.Delete(docItem)
                except Exception:
                    logger.warning("Failed to delete: {}".format(delete_type))

                if delete_type.startswith("heatmap.raw"):
                    self.ionPanel.delete_row_from_table(delete_item_name=None, delete_document_title=document_title)
                    self.on_update_extracted_patches(document.title, "__all__", None)

        elif delete_type.endswith(".one"):
            for delete_type in delete_types:
                if delete_type == "heatmap.raw.one":
                    main_docItem = self.getItemByData(document.IMS2Dions)
                    docItem = self.getItemByData(document.IMS2Dions.get(ion_name, "N/A"))
                    if docItem not in ["N/A", None, False]:
                        try:
                            del document.IMS2Dions[ion_name]
                        except KeyError:
                            logger.warning(
                                "Failed to delete {}: {} from {}.".format(delete_type, ion_name, document_title)
                            )
                        if len(document.IMS2Dions) == 0:
                            document.gotExtractedIons = False
                            try:
                                self.Delete(main_docItem)
                            except Exception:
                                pass
                if delete_type == "heatmap.raw.one.processed":
                    ion_name_processed = f"{ion_name} (processed)"
                    main_docItem = self.getItemByData(document.IMS2Dions)
                    docItem = self.getItemByData(document.IMS2Dions.get(ion_name_processed, "N/A"))
                    if docItem not in ["N/A", None, False]:
                        try:
                            del document.IMS2Dions[ion_name_processed]
                        except KeyError:
                            logger.warning(
                                "Failed to delete {}: {} from {}.".format(
                                    delete_type, ion_name_processed, document_title
                                )
                            )
                        if len(document.IMS2Dions) == 0:
                            document.gotExtractedIons = False
                            try:
                                self.Delete(main_docItem)
                            except Exception:
                                pass
                if delete_type == "heatmap.processed.one":
                    main_docItem = self.getItemByData(document.IMS2DionsProcess)
                    docItem = self.getItemByData(document.IMS2DionsProcess.get(ion_name, "N/A"))
                    if docItem not in ["N/A", None, False]:
                        try:
                            del document.IMS2DionsProcess[ion_name]
                        except KeyError:
                            logger.warning(
                                "Failed to delete {}: {} from {}.".format(delete_type, ion_name, document_title)
                            )
                        if len(document.IMS2DionsProcess) == 0:
                            document.got2DprocessIons = False
                            try:
                                self.Delete(main_docItem)
                            except Exception:
                                pass
                if delete_type == "heatmap.rt.one":
                    main_docItem = self.getItemByData(document.IMSRTCombIons)
                    docItem = self.getItemByData(document.IMSRTCombIons.get(ion_name, "N/A"))
                    if docItem not in ["N/A", None, False]:
                        try:
                            del document.IMSRTCombIons[ion_name]
                        except KeyError:
                            logger.warning(
                                "Failed to delete {}: {} from {}.".format(delete_type, ion_name, document_title)
                            )
                        if len(document.IMSRTCombIons) == 0:
                            document.gotCombinedExtractedIonsRT = False
                            try:
                                self.Delete(main_docItem)
                            except Exception:
                                pass
                if delete_type == "heatmap.combined.one":
                    main_docItem = self.getItemByData(document.IMS2DCombIons)
                    docItem = self.getItemByData(document.IMS2DCombIons.get(ion_name, "N/A"))
                    if docItem not in ["N/A", None, False]:
                        try:
                            del document.IMS2DCombIons[ion_name]
                        except KeyError:
                            logger.warning(
                                "Failed to delete {}: {} from {}.".format(delete_type, ion_name, document_title)
                            )
                        if len(document.IMS2DCombIons) == 0:
                            document.gotCombinedExtractedIons = False
                            try:
                                self.Delete(main_docItem)
                            except Exception:
                                pass

                try:
                    self.Delete(docItem)
                    docItem = False
                except Exception:
                    pass

                if delete_type.startswith("heatmap.raw"):
                    self.ionPanel.delete_row_from_table(delete_item_name=ion_name, delete_document_title=document_title)
                    self.on_update_extracted_patches(document.title, None, ion_name)

        return document, True

    def on_delete_data__mass_spectra(
        self, document, document_title, delete_type, spectrum_name=None, confirm_deletion=False
    ):
        """
        Delete data from document tree and document

        Parameters
        ----------
        document: py object
            document object
        document_title: str
            name of the document - also found in document.title
        delete_type: str
            type of deletion. Accepted: `file.all`, `file.one`
        spectrum_name: str
            name of the unsupervised item to be deleted
        confirm_deletion: bool
            check whether all items should be deleted before performing the task


        Returns
        -------
        document: py object
            updated document object
        outcome: bool
            result of positive/negative deletion of document tree object
        """

        if confirm_deletion:
            msg = "Are you sure you want to continue with this action?" + "\nThis action cannot be undone."
            dlg = DialogBox(exceptionMsg=msg, type="Question")
            if dlg == wx.ID_NO:
                logger.info("The operation was cancelled")
                return document, True

        docItem = False
        main_docItem = self.getItemByData(document.multipleMassSpectrum)
        # delete all classes
        if delete_type == "spectrum.all":
            docItem = self.getItemByData(document.multipleMassSpectrum)
            document.multipleMassSpectrum = {}
            document.gotMultipleMS = False
            self.filesPanel.delete_row_from_table(delete_item_name=None, delete_document_title=document_title)
        elif delete_type == "spectrum.one":
            docItem = self.getItemByData(document.multipleMassSpectrum[spectrum_name])
            try:
                del document.multipleMassSpectrum[spectrum_name]
            except KeyError:
                msg = (
                    "Failed to delete {} from Fits (Supervised) dictionary. ".format(spectrum_name)
                    + "You probably have reselect it in the document tree"
                )
                logger.warning(msg)
            self.filesPanel.delete_row_from_table(delete_item_name=spectrum_name, delete_document_title=document_title)

        if len(document.multipleMassSpectrum) == 0:
            document.gotMultipleMS = False
            try:
                self.Delete(main_docItem)
            except Exception:
                logger.warning("Failed to delete item: Mass Spectra from the document tree")

        if docItem is False:
            return document, False
        else:
            self.Delete(docItem)
            return document, True

    def on_delete_data__chromatograms(
        self, document, document_title, delete_type, spectrum_name=None, confirm_deletion=False
    ):
        """
        Delete data from document tree and document

        Parameters
        ----------
        document: py object
            document object
        document_title: str
            name of the document - also found in document.title
        delete_type: str
            type of deletion. Accepted: `file.all`, `file.one`
        spectrum_name: str
            name of the unsupervised item to be deleted
        confirm_deletion: bool
            check whether all items should be deleted before performing the task


        Returns
        -------
        document: py object
            updated document object
        outcome: bool
            result of positive/negative deletion of document tree object
        """

        if confirm_deletion:
            msg = "Are you sure you want to continue with this action?" + "\nThis action cannot be undone."
            dlg = DialogBox(exceptionMsg=msg, type="Question")
            if dlg == wx.ID_NO:
                logger.info("The operation was cancelled")
                return document, True

        docItem = False
        main_docItem = self.getItemByData(document.multipleRT)
        # delete all classes
        if delete_type == "chromatogram.all":
            docItem = self.getItemByData(document.multipleRT)
            document.multipleMassSpectrum = {}
            document.gotMultipleMS = False
        elif delete_type == "chromatogram.one":
            docItem = self.getItemByData(document.multipleRT[spectrum_name])
            try:
                del document.multipleRT[spectrum_name]
            except KeyError:
                msg = (
                    "Failed to delete {} from Fits (Supervised) dictionary. ".format(spectrum_name)
                    + "You probably have reselect it in the document tree"
                )
                logger.warning(msg)

        if len(document.multipleRT) == 0:
            document.gotMultipleRT = False
            try:
                self.Delete(main_docItem)
            except Exception:
                logger.warning("Failed to delete item: Mass Spectra from the document tree")

        if docItem is False:
            return document, False
        else:
            self.Delete(docItem)
            return document, True

    def on_update_unidec(self, unidec_data, document_title, dataset, set_data_only=False):
        """
        Update annotations in specified document/dataset
        ----------
        Parameters
        ----------
        annotations : dict
            dictionary with annotations
        document : str
            name of the document
        dataset : str
            name of the dataset
        set_data_only : bool
            specify whether all annotations should be removed and readded or if
            we it should simply set data
        """

        document = self.data_handling._on_get_document(document_title)
        item = False
        docItem = False
        if dataset == "Mass Spectrum":
            item = self.getItemByData(document.massSpectrum)
            document.massSpectrum["unidec"] = unidec_data
        elif dataset == "Mass Spectrum (processed)":
            item = self.getItemByData(document.smoothMS)
            document.smoothMS["unidec"] = unidec_data
        else:
            item = self.getItemByData(document.multipleMassSpectrum[dataset])
            document.multipleMassSpectrum[dataset]["unidec"] = unidec_data

        if item is not False and not set_data_only:
            self.append_unidec(item, unidec_data)
            self.data_handling.on_update_document(document, "no_refresh")
        else:
            try:
                docItem = self.getItemByData(document)
            except Exception:
                docItem = False
            if docItem is not False:
                self.SetPyData(docItem, document)
                self.presenter.documentsDict[document.title] = document
            else:
                self.data_handling.on_update_document(document, "document")

    def append_unidec(self, item, unidec_data, expand=True):
        """
        Update annotations in the document tree
        ----------
        Parameters
        ----------
        item : wxPython document tree item
            item in the document tree that should be cleared and re-filled
        unidec_data : dict
            dictionary with UniDec data
        expand : bool
            specify if tree item should be expanded

        """
        image = self.get_item_image("unidec")

        child, cookie = self.GetFirstChild(item)
        i = 0
        while child.IsOk():
            #             print("child", i, self.GetItemText(child))
            if self.GetItemText(child) == "UniDec":
                self.Delete(child)
            child, cookie = self.GetNextChild(item, cookie)
            i += 1

        if len(unidec_data) == 0:
            return

        unidec_item = self.AppendItem(item, "UniDec")
        self.SetPyData(unidec_item, unidec_data)
        self.SetItemImage(unidec_item, image, wx.TreeItemIcon_Normal)

        for key in unidec_data:
            unidec_item_individual = self.AppendItem(unidec_item, key)
            self.SetPyData(unidec_item_individual, unidec_data[key])
            self.SetItemImage(unidec_item_individual, image, wx.TreeItemIcon_Normal)

        if expand:
            self.Expand(unidec_item)

    def on_update_data(self, item_data, item_name, document, data_type, set_data_only=False):
        """Update document data

        Parameters
        ----------
        item_data: list
            new data to be added to document
        item_name: str
            name of the EIC
        item_type : str
            which type of data is provided
        document: py object
            document object
        set_data_only: bool
            specify whether data should be added with full refresh or just set
        """
        # spectrum
        if data_type == "main.spectrum":
            item = self.getItemByData(document.massSpectrum)
            document.gotMS = True
            document.massSpectrum = item_data

        elif data_type == "main.spectrum.unidec":
            item = self.getItemByData(document.massSpectrum["unidec"])
            document.gotMS = True
            document.massSpectrum["unidec"] = item_data

        elif data_type == "processed.spectrum":
            item = self.getItemByData(document.smoothMS)
            document.gotSmoothMS = True
            document.smoothMS = item_data

        elif data_type == "extracted.spectrum":
            item = self.getItemByData(document.multipleMassSpectrum)
            document.gotMultipleMS = True
            document.multipleMassSpectrum[item_name] = item_data

        # mobiligram
        elif data_type == "main.mobiligram":
            item = self.getItemByData(document.DT)
            document.got1DT = True
            document.DT = item_data

        elif data_type == "ion.mobiligram":
            item = self.getItemByData(document.IMS1DdriftTimes)
            document.gotExtractedDriftTimes = True
            document.IMS1DdriftTimes[item_name] = item_data

        elif data_type == "ion.mobiligram.raw":
            item = self.getItemByData(document.multipleDT)
            document.gotMultipleDT = True
            document.multipleDT[item_name] = item_data

        # chromatogram
        elif data_type == "main.chromatogram":
            item = self.getItemByData(document.RT)
            document.got1RT = True
            document.RT = item_data

        elif data_type == "extracted.chromatogram":
            item = self.getItemByData(document.multipleRT)
            document.gotMultipleRT = True
            document.multipleRT[item_name] = item_data

        elif data_type == "ion.chromatogram.combined":
            item = self.getItemByData(document.IMSRTCombIons)
            document.gotCombinedExtractedIonsRT = True
            document.IMSRTCombIons[item_name] = item_data

        # heatmap
        elif data_type == "main.heatmap":
            item = self.getItemByData(document.IMS2D)
            document.got2DIMS = True
            document.IMS2D = item_data

        elif data_type == "processed.heatmap":
            item = self.getItemByData(document.IMS2Dprocess)
            document.got2Dprocess = True
            document.IMS2Dprocess = item_data

        elif data_type == "ion.heatmap.raw":
            item = self.getItemByData(document.IMS2Dions)
            document.gotExtractedIons = True
            document.IMS2Dions[item_name] = item_data

        elif data_type == "ion.heatmap.combined":
            item = self.getItemByData(document.IMS2DCombIons)
            document.gotCombinedExtractedIons = True
            document.IMS2DCombIons[item_name] = item_data

        elif data_type == "ion.heatmap.processed":
            item = self.getItemByData(document.IMS2DionsProcess)
            document.got2DprocessIons = True
            document.IMS2DionsProcess[item_name] = item_data

        elif data_type == "ion.heatmap.comparison":
            item = self.getItemByData(document.IMS2DcompData)
            document.gotComparisonData = True
            document.IMS2DcompData[item_name] = item_data

        if item is not False and not set_data_only:
            # add main spectrum
            if data_type == "main.spectrum":
                self.update_one_item(item, document.massSpectrum, image=data_type)
            elif data_type == "main.spectrum.unidec":
                self.update_one_item(item, document.massSpectrum, image=data_type)
            elif data_type == "processed.spectrum":
                self.update_one_item(item, document.smoothMS, image=data_type)
            # add base heatmap
            elif data_type == "main.heatmap":
                self.update_one_item(item, document.IMS2D, image=data_type)
            elif data_type == "processed.heatmap":
                self.update_one_item(item, document.IMS2Dprocess, image=data_type)
            # add extracted spectrum
            elif data_type == "extracted.spectrum":
                self.add_one_to_group(item, document.multipleMassSpectrum[item_name], item_name, image=data_type)
            # add extracted spectrum
            elif data_type == "extracted.chromatogram":
                self.add_one_to_group(item, document.multipleRT[item_name], item_name, image=data_type)
            elif data_type == "ion.chromatogram.combined":
                self.add_one_to_group(item, document.IMSRTCombIons[item_name], item_name, image=data_type)
            # add mobiligram data
            elif data_type == "ion.mobiligram":
                self.add_one_to_group(item, document.IMS1DdriftTimes[item_name], item_name, image=data_type)
            elif data_type == "ion.mobiligram.raw":
                self.add_one_to_group(item, document.multipleDT[item_name], item_name, image=data_type)
            # add heatmap-raw data
            elif data_type == "ion.heatmap.raw":
                self.add_one_to_group(item, document.IMS2Dions[item_name], item_name, image=data_type)
            # add CIU-style data
            elif data_type == "ion.heatmap.combined":
                self.add_one_to_group(item, document.IMS2DCombIons[item_name], item_name, image=data_type)
            elif data_type == "ion.heatmap.processed":
                self.add_one_to_group(item, document.IMS2DionsProcess[item_name], item_name, image=data_type)
            elif data_type == "ion.heatmap.comparison":
                self.add_one_to_group(item, document.IMS2DcompData[item_name], item_name, image=data_type)
            # add data to document without updating it
            self.data_handling.on_update_document(document, "no_refresh")
        else:
            self.data_handling.on_update_document(document, "document")

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
        if data_type == "__all__":
            self.panel_plot.on_clear_patches(plot="MS")
        # remove specific patch
        else:
            rect_label = "{};{}".format(document_title, ion_name)
            self.panel_plot.plot_remove_patches_with_labels(rect_label, plot_window="MS")

        self.panel_plot.plot_repaint(plot_window="MS")

    def get_item_image(self, image_type):
        if image_type in ["main.spectrum", "extracted.spectrum", "processed.spectrum", "unidec"]:
            image = self.bulets_dict["mass_spec_on"]
        elif image_type == [
            "ion.heatmap.combined",
            "ion.heatmap.raw",
            "ion.heatmap.processed",
            "main.heatmap",
            "processed.heatmap",
            "ion.heatmap.comparison",
        ]:
            image = self.bulets_dict["heatmap_on"]
        elif image_type == ["ion.mobiligram", "ion.mobiligram.raw"]:
            image = self.bulets_dict["drift_time_on"]
        elif image_type in ["main.chromatogram", "extracted.chromatogram", "ion.chromatogram.combined"]:
            image = self.bulets_dict["rt_on"]
        else:
            image = self.bulets_dict["heatmap_on"]

        return image

    def add_one_to_group(self, item, data, name, image, expand=True):
        """
        Append data to the docoument
        ----------
        Parameters
        ----------
        item : wxPython document tree item
            item in the document tree that should be cleared and re-filled
        data : dict
            dictionary with annotations
        name : str
            name of the classifier
        expand : bool
            specify if tree item should be expanded
        """
        image = self.get_item_image(image)
        child, cookie = self.GetFirstChild(item)
        while child.IsOk():
            if self.GetItemText(child) == name:
                self.Delete(child)
            child, cookie = self.GetNextChild(item, cookie)

        if len(data) == 0:
            return

        itemClass = self.AppendItem(item, name)
        self.SetPyData(itemClass, data)
        self.SetItemImage(itemClass, image, wx.TreeItemIcon_Normal)

        if expand:
            self.Expand(itemClass)

    def update_one_item(self, item, data, image):
        image = self.get_item_image(image)
        self.SetPyData(item, data)
        self.SetItemImage(item, image, wx.TreeItemIcon_Normal)
