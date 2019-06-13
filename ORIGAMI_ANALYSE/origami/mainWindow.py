# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
#
# 	 GitHub : https://github.com/lukasz-migas/ORIGAMI
# 	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
# 	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or
#    modify it under the condition you cite and credit the authors whenever
#    appropriate.
#    The program is distributed in the hope that it will be useful but is
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

# Load libraries

import os
import sys
import webbrowser
from time import gmtime, sleep, strftime

import numpy as np
import psutil
import wx
import wx.aui
from pubsub import pub

from gui_elements.panel_notifyOpenDocuments import panelNotifyOpenDocuments
from gui_elements.panelAbout import panelAbout
from panelCCScalibration import panelCCScalibration
from panelDocumentTree import panelDocuments
from panelExtraParameters import panelParametersEdit
from panelInteractiveOutput import panelInteractiveOutput as panelInteractive
from panelLinearDriftCell import panelLinearDriftCell
from panelLog import panelLog
from panelMultipleIons import panelMultipleIons
from panelMultipleML import panelMML
from panelMultipleTextFiles import panelMultipleTextFiles
from panelPlot import panelPlot
from panelProcess import panelProcessData
from processing.data_handling import data_handling
from processing.data_processing import data_processing
from readers.io_text_files import check_file_type
from styles import makeMenuItem
from toolbox import (get_latest_version, clean_directory, compare_versions,
                     findPeakMax, getNarrow1Ddata)
from ids import ID_fileMenu_MGF, ID_fileMenu_mzML, \
    ID_fileMenu_openRecent, ID_openDocument, ID_load_origami_masslynx_raw, ID_load_multiple_origami_masslynx_raw, \
    ID_load_multiple_masslynx_raw, ID_addCCScalibrantFile, ID_openLinearDTRawFile, ID_load_masslynx_raw_ms_only, \
    ID_addNewOverlayDoc, ID_addNewInteractiveDoc, ID_load_text_MS, ID_load_text_2D, ID_addNewManualDoc, \
    ID_load_clipboard_spectrum, ID_saveDocument, ID_saveAllDocuments, ID_quit, ID_processSettings_ExtractData, \
    ID_processSettings_ORIGAMI, ID_processSettings_MS, ID_processSettings_2D, ID_processSettings_FindPeaks, \
    ID_processSettings_UniDec, ID_extraSettings_general_plot, ID_extraSettings_plot1D, ID_extraSettings_plot2D, \
    ID_extraSettings_plot3D, ID_extraSettings_colorbar, ID_extraSettings_legend, ID_extraSettings_rmsd, \
    ID_extraSettings_waterfall, ID_extraSettings_violin, ID_extraSettings_general, ID_annotPanel_otherSettings, \
    ID_unidecPanel_otherSettings, ID_plots_showCursorGrid, ID_plots_resetZoom, ID_clearAllPlots, ID_docTree_compareMS, \
    ID_saveAsInteractive, ID_window_documentList, ID_window_ionList, ID_window_textList, ID_window_multipleMLList, \
    ID_window_multiFieldList, ID_window_ccsList, ID_window_logWindow, ID_window_all, ID_windowMaximize, \
    ID_windowMinimize, ID_windowFullscreen, ID_docTree_plugin_UVPD, ID_docTree_plugin_MSMS, ID_saveConfig, \
    ID_saveAsConfig, ID_openConfig, ID_openAsConfig, ID_importAtStart_CCS, ID_openCCScalibrationDatabse, \
    ID_selectCalibrant, ID_importExportSettings_peaklist, ID_importExportSettings_image, ID_importExportSettings_file, \
    ID_checkAtStart_Driftscope, ID_check_Driftscope, ID_setDriftScopeDir, ID_help_UniDecInfo, ID_help_page_dataLoading, \
    ID_help_page_dataExtraction, ID_help_page_UniDec, ID_help_page_ORIGAMI, ID_help_page_multipleFiles, \
    ID_help_page_overlay, ID_help_page_Interactive, ID_help_page_annotatingMassSpectra, ID_help_page_OtherData, \
    ID_helpGuide, ID_helpGuideLocal, ID_helpYoutube, ID_helpNewVersion, ID_helpCite, ID_helpNewFeatures, \
    ID_helpReportBugs, ID_CHECK_VERSION, ID_WHATS_NEW, ID_SHOW_ABOUT, ID_helpAuthor, ID_RESET_ORIGAMI, \
    ID_help_page_gettingStarted, ID_help_page_CCScalibration, ID_help_page_linearDT, ID_openIRRawFile, \
    ID_openIRTextile, ID_saveOverlayImage, ID_saveMSImage, ID_saveMZDTImage, \
    ID_saveRTImage, ID_save1DImage, ID_save2DImage, ID_save3DImage, ID_saveWaterfallImage, ID_saveRMSDImage, \
    ID_saveRMSFImage, ID_saveRMSDmatrixImage, ID_load_multiple_text_2D, ID_textPanel_process_selected, ID_overlayTextFromList, \
    ID_extractDriftVoltagesForEachIon, ID_helpHomepage, ID_helpGitHub, ID_helpHTMLEditor, ID_overlayMZfromList, \
    ID_extractAllIons, ID_showPlotDocument, ID_process2DDocument, ID_combineCEscans, ID_renameItem, \
    ID_showPlotMSDocument, ID_assignChargeState, ID_saveDataCSVDocument, ID_mainPanel_openSourceFiles, \
    ID_load_masslynx_raw, ID_window_controls, ID_documentRecent0, ID_documentRecent1, ID_documentRecent2, \
    ID_documentRecent3, ID_documentRecent4, ID_documentRecent5, ID_documentRecent6, ID_documentRecent7, \
    ID_documentRecent8, ID_documentRecent9, ID_fileMenu_clearRecent, ID_fileMenu_thermoRAW
from gui_elements.panel_notifyNewVersion import panelNotifyNewVersion
from gui_elements.panel_htmlViewer import panelHTMLViewer
from gui_elements.panel_sequenceAnalysis import panelSequenceAnalysis
from gui_elements.panel_exportSettings import panelExportSettings
from gui_elements.misc_dialogs import dlgBox

from utils.random import randomIntegerGenerator
from utils.color import convertRGB255to1, convertRGB1to255
import logging
logger = logging.getLogger("origami")


class MyFrame(wx.Frame):

    def __init__(self, parent, config, helpInfo, icons, id=-1, title='ORIGAMI',
                 pos=wx.DefaultPosition, size=(1200, 600),
                 style=wx.FULL_REPAINT_ON_RESIZE):
        wx.Frame.__init__(self, None, title=title)

        # Extract size of screen
        self.displaysize = wx.GetDisplaySize()
        self.SetDimensions(0, 0, self.displaysize[0], self.displaysize[1] - 50)
        # Setup config container
        self.config = config
        self.icons = icons
        self.help = helpInfo
        self.presenter = parent

        self.plot_data = {}
        self.plot_scale = {}
        self.plot_name = None

        self._fullscreen = False

        file_drop_target = DragAndDrop(self)
        self.SetDropTarget(file_drop_target)

        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(self.icons.iconsLib['origamiLogoDark16'])
        self.SetIcon(icon)

        # View parameters
        self.mode = None
        self.xpos = None
        self.ypos = None
        self.startX = None

        self.config.startTime = (strftime("%H-%M-%S_%d-%m-%Y", gmtime()))

        # Bind commands to events
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)

        # Setup Notebook manager
        self._mgr = wx.aui.AuiManager(self)
        self._mgr.SetDockSizeConstraint(1, 1)

        # Load panels
        self.panelDocuments = panelDocuments(self, self.config, self.icons, self.presenter)

        self.panelPlots = panelPlot(self, self.config, self.presenter)
        self.panelMultipleIons = panelMultipleIons(
            self, self.config, self.icons, self.help, self.presenter)
        self.panelMultipleText = panelMultipleTextFiles(self, self.config, self.icons, self.presenter)
        self.panelMML = panelMML(self, self.config, self.icons, self.presenter)
        self.panelLinearDT = panelLinearDriftCell(self, self.config, self.icons, self.presenter)
        self.panelCCS = panelCCScalibration(self, self.config, self.icons, self.presenter)
        self.panelLog = panelLog(self, self.config, self.icons)

        kwargs = {'window': None}
        self.panelParametersEdit = panelParametersEdit(self, self.presenter, self.config, self.icons, **kwargs)

        # add data processing
        self.data_processing = data_processing(self.presenter, self, self.config)
        self.data_handling = data_handling(self.presenter, self, self.config)

        self.makeToolbar()

        # Panel to store document information
        self._mgr.AddPane(self.panelDocuments, wx.aui.AuiPaneInfo().Left().Caption('Documents')
                          .MinSize((250, 100)).GripperTop().BottomDockable(False).TopDockable(False)
                          .Show(self.config._windowSettings['Documents']['show'])
                          .CloseButton(self.config._windowSettings['Documents']['close_button'])
                          .CaptionVisible(self.config._windowSettings['Documents']['caption'])
                          .Gripper(self.config._windowSettings['Documents']['gripper']))

        self._mgr.AddPane(self.panelPlots, wx.aui.AuiPaneInfo().CenterPane().Caption('Plot')
                          .Show(self.config._windowSettings['Plots']['show'])
                          .CloseButton(self.config._windowSettings['Plots']['close_button'])
                          .CaptionVisible(self.config._windowSettings['Plots']['caption'])
                          .Gripper(self.config._windowSettings['Plots']['gripper'])
                          )

        # Panel to extract multiple ions from ML files
        self._mgr.AddPane(self.panelMultipleIons, wx.aui.AuiPaneInfo().Right().Caption('Peak list')
                          .MinSize((300, -1)).GripperTop().BottomDockable(True).TopDockable(False)
                          .Show(self.config._windowSettings['Peak list']['show'])
                          .CloseButton(self.config._windowSettings['Peak list']['close_button'])
                          .CaptionVisible(self.config._windowSettings['Peak list']['caption'])
                          .Gripper(self.config._windowSettings['Peak list']['gripper'])
                          )

        # Panel to operate on multiple text files
        self._mgr.AddPane(self.panelMultipleText, wx.aui.AuiPaneInfo().Right().Caption('Text files')
                          .MinSize((300, -1)).GripperTop().BottomDockable(True).TopDockable(False)
                          .Show(self.config._windowSettings['Text files']['show'])
                          .CloseButton(self.config._windowSettings['Text files']['close_button'])
                          .CaptionVisible(self.config._windowSettings['Text files']['caption'])
                          .Gripper(self.config._windowSettings['Text files']['gripper'])
                          )

        # Panel to operate on multiple ML files
        self._mgr.AddPane(self.panelMML, wx.aui.AuiPaneInfo().Right().Caption('Multiple files')
                          .MinSize((300, -1)).GripperTop().BottomDockable(True).TopDockable(False)
                          .Show(self.config._windowSettings['Multiple files']['show'])
                          .CloseButton(self.config._windowSettings['Multiple files']['close_button'])
                          .CaptionVisible(self.config._windowSettings['Multiple files']['caption'])
                          .Gripper(self.config._windowSettings['Multiple files']['gripper'])
                          )

        # Panel to analyse linear DT data (Synapt)
        self._mgr.AddPane(self.panelLinearDT, wx.aui.AuiPaneInfo().Right().Caption('Linear Drift Cell')
                          .MinSize((300, -1)).GripperTop().BottomDockable(True).TopDockable(False)
                          .Show(self.config._windowSettings['Linear Drift Cell']['show'])
                          .CloseButton(self.config._windowSettings['Linear Drift Cell']['close_button'])
                          .CaptionVisible(self.config._windowSettings['Linear Drift Cell']['caption'])
                          .Gripper(self.config._windowSettings['Linear Drift Cell']['gripper'])
                          )

        # Panel to perform CCS calibration
        self._mgr.AddPane(self.panelCCS, wx.aui.AuiPaneInfo().Right().Caption('CCS calibration')
                          .MinSize((320, -1)).GripperTop().BottomDockable(True).TopDockable(False)
                          .Show(self.config._windowSettings['CCS calibration']['show'])
                          .CloseButton(self.config._windowSettings['CCS calibration']['close_button'])
                          .CaptionVisible(self.config._windowSettings['CCS calibration']['caption'])
                          .Gripper(self.config._windowSettings['CCS calibration']['gripper'])
                          )

        self._mgr.AddPane(self.panelParametersEdit, wx.aui.AuiPaneInfo().Right()
                          .Caption(self.config._windowSettings['Plot parameters']['title'])
                          .MinSize((320, -1)).GripperTop().BottomDockable(True).TopDockable(False)
                          .Show(self.config._windowSettings['Plot parameters']['show'])
                          .CloseButton(self.config._windowSettings['Plot parameters']['close_button'])
                          .CaptionVisible(self.config._windowSettings['Plot parameters']['caption'])
                          .Gripper(self.config._windowSettings['Plot parameters']['gripper'])
                          )

        self._mgr.AddPane(self.panelLog, wx.aui.AuiPaneInfo().Bottom()
                          .Caption(self.config._windowSettings['Log']['title'])
                          .MinSize((320, -1)).GripperTop().BottomDockable(True).TopDockable(True)
                          .Show(self.config._windowSettings['Log']['show'])
                          .CloseButton(self.config._windowSettings['Log']['close_button'])
                          .CaptionVisible(self.config._windowSettings['Log']['caption'])
                          .Gripper(self.config._windowSettings['Log']['gripper'])
                          .Float()
                          )

        # Setup listeners
        pub.subscribe(self.on_motion, 'motion_xy')
        pub.subscribe(self.motion_range, 'motion_range')
        pub.subscribe(self.on_distance, 'startX')
        pub.subscribe(self.presenter.OnChangedRMSF, 'changedZoom')
        pub.subscribe(self.onMode, 'motion_mode')
        pub.subscribe(self.data_handling.on_update_DTMS_zoom, 'change_zoom_dtms')

        # Load other parts
        self._mgr.Update()
        self.makeBindings()
        self.statusBar()
        self.make_menubar()
        self.SetMenuBar(self.mainMenubar)
        self.makeShortcuts()
        self.Maximize(True)

        # bind events
        self.Bind(wx.aui.EVT_AUI_PANE_CLOSE, self.pageClosed)
        self.Bind(wx.aui.EVT_AUI_PANE_RESTORE, self.pageRestored)

        # Fire up a couple of events
        self._onUpdateWindowSettings()
        self.onPaneOnOff(evt=None)
        self._onToggleOnStart()

    def _onUpdateWindowSettings(self):
        self.config._windowSettings['Documents']['id'] = ID_window_documentList
        self.config._windowSettings['Peak list']['id'] = ID_window_ionList
        self.config._windowSettings['CCS calibration']['id'] = ID_window_ccsList
        self.config._windowSettings['Linear Drift Cell']['id'] = ID_window_multiFieldList
        self.config._windowSettings['Text files']['id'] = ID_window_textList
        self.config._windowSettings['Multiple files']['id'] = ID_window_multipleMLList
        self.config._windowSettings['Log']['id'] = ID_window_logWindow
        return None

    def _onToggleOnStart(self):
        panelDict = {'Documents': ID_window_documentList,
                     'Multiple files': ID_window_multipleMLList,
                     'Peak list': ID_window_ionList,
                     'Text files': ID_window_textList,
                     'CCS calibration': ID_window_ccsList,
                     'Linear Drift Cell': ID_window_multiFieldList,
                     'Log': ID_window_logWindow}

        for panel in [self.panelDocuments,
                      self.panelMML, self.panelLog,
                      self.panelMultipleIons, self.panelMultipleText,
                      self.panelCCS, self.panelLinearDT]:
            if self._mgr.GetPane(panel).IsShown():
                self.onFindToggleBy_ID(find_id=panelDict[self._mgr.GetPane(panel).caption], check=True)

    def _onUpdatePlotData(self, plot_type=None):
        if plot_type == '2D':
            _data = self.presenter._get_replot_data(data_format='2D')
            try:
                yshape, xshape = _data[0].shape
                _yscale = yshape / np.max(_data[2])
                _xscale = xshape / np.max(_data[1])
                self.plot_data['2D'] = _data[0]
                self.plot_scale['2D'] = [_yscale, _xscale]
            except Exception:
                pass
        elif plot_type == 'DT/MS':
            _data = self.presenter._get_replot_data(data_format='DT/MS')
            yshape, xshape = _data[0].shape
            _yscale = yshape / np.max(_data[2])
            _xscale = xshape / np.max(_data[1])
            self.plot_data['DT/MS'] = _data[0]
            self.plot_scale['DT/MS'] = [_yscale, _xscale]
        elif plot_type == 'RMSF':
            _data = self.presenter._get_replot_data(data_format='RMSF')
            yshape, xshape = _data[0].shape
            _yscale = yshape / np.max(_data[2])
            _xscale = xshape / np.max(_data[1])
            self.plot_data['DT/MS'] = _data[0]
            self.plot_scale['DT/MS'] = [_yscale, _xscale]

    def pageClosed(self, evt):
        # Keep track of which window is closed
        self.config._windowSettings[evt.GetPane().caption]['show'] = False
        # fire-up events
        try:
            evtID = self.onCheckToggleID(panel=evt.GetPane().caption)
            self.onPaneOnOff(evt=evtID)
        except Exception:
            pass

    def pageRestored(self, evt):
        # Keep track of which window is restored
        self.config._windowSettings[evt.GetPane().caption]['show'] = True
        evtID = self.onCheckToggleID(panel=evt.GetPane().caption)
        self.onPaneOnOff(evt=evtID)
        # fire-up events

        if evt is not None:
            evt.Skip()

    def makeBindings(self):
        '''
        Collection of all bindings for various functions
        '''
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_multiple_text_2D, id=ID_load_multiple_text_2D)
        self.Bind(wx.EVT_TOOL, self.presenter.onProcessMultipleTextFiles, id=ID_textPanel_process_selected)
        self.Bind(wx.EVT_TOOL, self.presenter.on_overlay_2D, id=ID_overlayTextFromList)
        self.Bind(wx.EVT_TOOL, self.presenter.onExtractDToverMZrangeMultiple, id=ID_extractDriftVoltagesForEachIon)

    def statusBar(self):

        self.mainStatusbar = self.CreateStatusBar(6, wx.STB_SIZEGRIP, wx.ID_ANY)
        # 0 = current x y pos
        # 1 = m/z range
        # 2 = MSMS mass
        # 3 = status information
        # 4 = present working file
        # 5 = tool
        # 6 = process
        self.mainStatusbar.SetStatusWidths([250, 80, 80, 200, -1, 50])
        self.mainStatusbar.SetFont(
            wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

    def onMode(self, dataOut):
        shift, ctrl, alt, add2table, wheel, zoom, dragged = dataOut
        self.mode = ''
        myCursor = wx.StockCursor(wx.CURSOR_ARROW)
        if alt:
            self.mode = 'Measure'
            myCursor = wx.StockCursor(wx.CURSOR_MAGNIFIER)
        elif ctrl:
            self.mode = 'Add data'
            myCursor = wx.StockCursor(wx.CURSOR_CROSS)
        elif add2table:
            self.mode = 'Add data'
            myCursor = wx.StockCursor(wx.CURSOR_CROSS)
        elif shift:
            self.mode = 'Wheel zoom Y'
            myCursor = wx.StockCursor(wx.CURSOR_SIZENS)
        elif wheel:
            self.mode = 'Wheel zoom X'
            myCursor = wx.StockCursor(wx.CURSOR_SIZEWE)
        elif alt and ctrl:
            self.mode = ''
        elif dragged is not None:
            self.mode = 'Dragging'
            myCursor = wx.StockCursor(wx.CURSOR_HAND)
        elif zoom:
            self.mode = 'Zooming'
            myCursor = wx.StockCursor(wx.CURSOR_MAGNIFIER)

        self.SetCursor(myCursor)
        self.SetStatusText("{}".format(self.mode), number=5)

    def make_menubar(self):
        self.mainMenubar = wx.MenuBar()

        # setup recent sub-menu
        self.menuRecent = wx.Menu()
        self.updateRecentFiles()

#         # setup binary sub-menu
#         openBinaryMenu = wx.Menu()
#         openBinaryMenu.Append(ID_openMSFile, 'Open MS from MassLynx file (MS .1dMZ)\tCtrl+M')
#         openBinaryMenu.Append(ID_open1DIMSFile, 'Open 1D IM-MS from MassLynx file (1D IM-MS, .1dDT)')
#         openBinaryMenu.Append(ID_open2DIMSFile, 'Open 2D IM-MS from MassLynx file (2D IM-MS, .2dRTDT)\tCtrl+D')

        openCommunityMenu = wx.Menu()
        openCommunityMenu.Append(ID_fileMenu_MGF, 'Open Mascot Generic Format file (.mgf) [MS/MS]')
        openCommunityMenu.Append(ID_fileMenu_mzML, 'Open mzML (.mzML) [MS/MS]')

        menuFile = wx.Menu()
        menuFile.AppendMenu(ID_fileMenu_openRecent, "Open Recent", self.menuRecent)
        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_openDocument,
                                         text='Open ORIGAMI Document file (.pickle)\tCtrl+Shift+P',
                                         bitmap=self.icons.iconsLib['open_project_16']))
        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_load_origami_masslynx_raw,
                                         text='Open ORIGAMI MassLynx (.raw) file [CIU]\tCtrl+R',
                                         bitmap=self.icons.iconsLib['open_origami_16']))

        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_load_multiple_origami_masslynx_raw,
                                         text='Open multiple ORIGAMI MassLynx (.raw) files [CIU]\tCtrl+Shift+Q',
                                         bitmap=self.icons.iconsLib['open_origamiMany_16']))
        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_addNewManualDoc,
                                         text='Create blank MANUAL document [CIU]',
                                         bitmap=self.icons.iconsLib['guide_16']))
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_load_multiple_masslynx_raw,
                                         text='Open multiple MassLynx (.raw) files [CIU]\tCtrl+Shift+R',
                                         bitmap=self.icons.iconsLib['open_masslynxMany_16']))
        menuFile.AppendSeparator()
        menuFile.Append(ID_addCCScalibrantFile, 'Open MassLynx (.raw) file [Calibration]\tCtrl+C')
        menuFile.Append(ID_openLinearDTRawFile, 'Open MassLynx (.raw) file [Linear DT]\tCtrl+F')
        menuFile.Append(ID_load_masslynx_raw_ms_only, 'Open MassLynx (no IM-MS, .raw) file\tCtrl+Shift+M')
        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_fileMenu_thermoRAW,
                                         text='Open Thermo (.RAW) file\tCtrl+Shift+Y',
                                         bitmap=None))
        menuFile.AppendSeparator()
        menuFile.AppendMenu(wx.ID_ANY, "Open MS/MS files...", openCommunityMenu)
        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_addNewOverlayDoc,
                                         text='Create blank COMPARISON document [CIU]',
                                         bitmap=self.icons.iconsLib['new_document_16']))
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_addNewInteractiveDoc,
                                         text='Create blank INTERACTIVE document',
                                         bitmap=self.icons.iconsLib['bokehLogo_16']))
        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_load_text_MS,
                                         text='Open MS Text file',
                                         bitmap=None))
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_load_text_2D,
                                         text='Open IM-MS Text file [CIU]\tCtrl+T',
                                         bitmap=self.icons.iconsLib['open_text_16']))
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_load_multiple_text_2D,
                                         text='Open multiple IM-MS text files [CIU]\tCtrl+Shift+T',
                                         bitmap=self.icons.iconsLib['open_textMany_16']))
        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_load_clipboard_spectrum,
                                         text='Grab MS spectrum from clipboard\tCtrl+V',
                                         bitmap=self.icons.iconsLib['filelist_16']))

        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_saveDocument,
                                         text='Save document (.pickle)\tCtrl+S',
                                         bitmap=self.icons.iconsLib['save16']))
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_saveAllDocuments,
                                         text='Save all documents (.pickle)',
                                         bitmap=self.icons.iconsLib['pickle_16']))
        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_quit,
                                         text='Quit\tCtrl+Q',
                                         bitmap=self.icons.iconsLib['exit_16']))
        self.mainMenubar.Append(menuFile, '&File')

        # PROCESS
        menuProcess = wx.Menu()
        menuProcess.AppendItem(makeMenuItem(parent=menuProcess, id=ID_processSettings_ExtractData,
                                            text='Settings: &Extract data\tShift+1',
                                            bitmap=self.icons.iconsLib['process_extract_16']))

        menuProcess.AppendItem(makeMenuItem(parent=menuProcess, id=ID_processSettings_ORIGAMI,
                                            text='Settings: &ORIGAMI\tShift+2',
                                            bitmap=self.icons.iconsLib['process_origami_16']))

        menuProcess.AppendItem(makeMenuItem(parent=menuProcess, id=ID_processSettings_MS,
                                            text='Settings: &Process mass spectra\tShift+3',
                                            bitmap=self.icons.iconsLib['process_ms_16']))

        menuProcess.AppendItem(makeMenuItem(parent=menuProcess, id=ID_processSettings_2D,
                                            text='Settings: Process &2D heatmaps\tShift+4',
                                            bitmap=self.icons.iconsLib['process_2d_16']))

        menuProcess.AppendItem(makeMenuItem(parent=menuProcess, id=ID_processSettings_FindPeaks,
                                            text='Settings: Peak &fitting\tShift+5',
                                            bitmap=self.icons.iconsLib['process_fit_16']))

        menuProcess.AppendItem(makeMenuItem(parent=menuProcess, id=ID_processSettings_UniDec,
                                            text='Settings: &UniDec\tShift+6',
                                            bitmap=self.icons.iconsLib['process_unidec_16']))
        self.mainMenubar.Append(menuProcess, '&Process')

        # PLOT
        menuPlot = wx.Menu()
        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_general_plot,
                                         text='Settings: Plot &General',
                                         bitmap=self.icons.iconsLib['panel_plot_general_16']))

        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_plot1D,
                                         text='Settings: Plot &1D',
                                         bitmap=self.icons.iconsLib['panel_plot1D_16']))

        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_plot2D,
                                         text='Settings: Plot &2D',
                                         bitmap=self.icons.iconsLib['panel_plot2D_16']))

        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_plot3D,
                                         text='Settings: Plot &3D',
                                         bitmap=self.icons.iconsLib['panel_plot3D_16']))

        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_colorbar,
                                         text='Settings: &Colorbar',
                                         bitmap=self.icons.iconsLib['panel_colorbar_16']))

        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_legend,
                                         text='Settings: &Legend',
                                         bitmap=self.icons.iconsLib['panel_legend_16']))

        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_rmsd,
                                         text='Settings: &RMSD',
                                         bitmap=self.icons.iconsLib['panel_rmsd_16']))

        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_waterfall,
                                         text='Settings: &Waterfall',
                                         bitmap=self.icons.iconsLib['panel_waterfall_16']))

        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_violin,
                                         text='Settings: &Violin',
                                         bitmap=self.icons.iconsLib['panel_violin_16']))

        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_general,
                                         text='Settings: &Extra',
                                         bitmap=self.icons.iconsLib['panel_general2_16']))

        menuPlot.AppendSeparator()
        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_annotPanel_otherSettings,
                                         text='Settings: Annotation parameters',
                                         bitmap=None))
        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_unidecPanel_otherSettings,
                                         text='Settings: UniDec parameters',
                                         bitmap=None))

        menuPlot.AppendSeparator()
        menuPlot.Append(ID_plots_showCursorGrid, 'Update plot parameters')
        # menuPlot.Append(ID_plots_resetZoom, 'Reset zoom tool\tF12')
        self.mainMenubar.Append(menuPlot, '&Plot settings')

        # VIEW
        menuView = wx.Menu()
        menuView.AppendItem(makeMenuItem(parent=menuView, id=ID_clearAllPlots,
                                         text='&Clear all plots',
                                         bitmap=self.icons.iconsLib['clear_16']))
        menuView.AppendItem(makeMenuItem(parent=menuView, id=ID_docTree_compareMS,
                                         text='Open MS comparison panel...',
                                         bitmap=self.icons.iconsLib['compare_mass_spectra_16']))
        menuView.AppendItem(makeMenuItem(parent=menuView, id=ID_saveAsInteractive,
                                         text='Open &interactive output panel...\tShift+Z',
                                         bitmap=self.icons.iconsLib['bokehLogo_16']))
        menuView.AppendSeparator()
        self.documentsPage = menuView.Append(ID_window_documentList, 'Panel: Documents\tCtrl+1', kind=wx.ITEM_CHECK)
        self.mzTable = menuView.Append(ID_window_ionList, 'Panel: Peak list\tCtrl+3', kind=wx.ITEM_CHECK)
        self.textTable = menuView.Append(ID_window_textList, 'Panel: Text list\tCtrl+4', kind=wx.ITEM_CHECK)
        self.multipleMLTable = menuView.Append(
            ID_window_multipleMLList, 'Panel: Multiple files\tCtrl+5', kind=wx.ITEM_CHECK)
        self.multifieldTable = menuView.Append(
            ID_window_multiFieldList, 'Panel: Linear DT-IMS\tCtrl+6', kind=wx.ITEM_CHECK)
        self.ccsTable = menuView.Append(ID_window_ccsList, 'Panel: CCS calibration\tCtrl+7', kind=wx.ITEM_CHECK)
        self.window_logWindow = menuView.Append(ID_window_logWindow, 'Panel: Log\tCtrl+8', kind=wx.ITEM_CHECK)
        menuView.AppendSeparator()
        menuView.Append(ID_window_all, 'Panel: Restore &all')
        menuView.AppendSeparator()
        menuView.AppendItem(makeMenuItem(parent=menuView, id=ID_windowMaximize,
                                         text='Maximize window',
                                         bitmap=self.icons.iconsLib['maximize_16']))
        menuView.AppendItem(makeMenuItem(parent=menuView, id=ID_windowMinimize,
                                         text='Minimize window',
                                         bitmap=self.icons.iconsLib['minimize_16']))
        menuView.AppendItem(makeMenuItem(parent=menuView, id=ID_windowFullscreen,
                                         text='Toggle fullscreen\tAlt+F11',
                                         bitmap=self.icons.iconsLib['fullscreen_16']))
        self.mainMenubar.Append(menuView, '&View')

        # UTILITIES
        menuPlugins = wx.Menu()
        menuPlugins.AppendItem(makeMenuItem(parent=menuPlugins, id=ID_docTree_plugin_UVPD,
                                            text='UVPD processing window...',
                                            bitmap=None))
        menuPlugins.AppendItem(makeMenuItem(parent=menuPlugins, id=ID_docTree_plugin_MSMS,
                                            text='MS/MS window...',
                                            bitmap=None))
#         menuPlugins.AppendItem(makeMenuItem(parent=menuPlugins, id=ID_sequence_openGUI,
#                                               text='Sequence analysis...',
#                                               bitmap=None))
        self.mainMenubar.Append(menuPlugins, '&Plugins')

        # CONFIG
        menuConfig = wx.Menu()
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_saveConfig,
                                           text='Export configuration XML file (default location)\tCtrl+S',
                                           bitmap=self.icons.iconsLib['export_config_16']))
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_saveAsConfig,
                                           text='Export configuration XML file as...\tCtrl+Shift+S',
                                           bitmap=None))
        menuConfig.AppendSeparator()
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_openConfig,
                                           text='Import configuration XML file (default location)\tCtrl+Shift+O',
                                           bitmap=self.icons.iconsLib['import_config_16']))
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_openAsConfig,
                                           text='Import configuration XML file from...',
                                           bitmap=None))
        menuConfig.AppendSeparator()
        self.loadCCSAtStart = menuConfig.Append(ID_importAtStart_CCS, 'Load at start',
                                                kind=wx.ITEM_CHECK)
        self.loadCCSAtStart.Check(self.config.loadCCSAtStart)
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_openCCScalibrationDatabse,
                                           text='Import CCS calibration database\tCtrl+Alt+C',
                                           bitmap=self.icons.iconsLib['filelist_16']))
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_selectCalibrant,
                                           text='Show CCS calibrants\tCtrl+Shift+C',
                                           bitmap=self.icons.iconsLib['ccs_table_16']))
        menuConfig.AppendSeparator()
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_importExportSettings_peaklist,
                                           text='Import parameters: Peaklist',
                                           bitmap=None))
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_importExportSettings_image,
                                           text='Export parameters: Image',
                                           bitmap=None))
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_importExportSettings_file,
                                           text='Export parameters: File',
                                           bitmap=None))
        menuConfig.AppendSeparator()
        self.checkDriftscopeAtStart = menuConfig.Append(ID_checkAtStart_Driftscope,
                                                        'Look for DriftScope at start',
                                                        kind=wx.ITEM_CHECK)
        self.checkDriftscopeAtStart.Check(self.config.checkForDriftscopeAtStart)
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_check_Driftscope,
                                           text='Check DriftScope path',
                                           bitmap=self.icons.iconsLib['check_online_16']))
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_setDriftScopeDir,
                                           text='Set DriftScope path...',
                                           bitmap=self.icons.iconsLib['driftscope_16']))
        self.mainMenubar.Append(menuConfig, '&Configuration')

        otherSoftwareMenu = wx.Menu()
        otherSoftwareMenu.AppendItem(makeMenuItem(parent=otherSoftwareMenu, id=ID_help_UniDecInfo,
                                                  text='About UniDec engine...',
                                                  bitmap=self.icons.iconsLib['process_unidec_16']))
#         otherSoftwareMenu.Append(ID_open1DIMSFile, 'About CIDER...')

        helpPagesMenu = wx.Menu()
        # helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_gettingStarted,
        #                                      text='Learn more: Getting started\tF1+0',
        #                                      bitmap=self.icons.iconsLib['blank_16']))
        # helpPagesMenu.AppendSeparator()
        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_dataLoading,
                                              text='Learn more: Loading data',
                                              bitmap=self.icons.iconsLib['open16']))

        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_dataExtraction,
                                              text='Learn more: Data extraction',
                                              bitmap=self.icons.iconsLib['extract16']))

        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_UniDec,
                                              text='Learn more: MS deconvolution using UniDec',
                                              bitmap=self.icons.iconsLib['process_unidec_16']))

        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_ORIGAMI,
                                              text='Learn more: ORIGAMI-MS (Automated CIU)',
                                              bitmap=self.icons.iconsLib['origamiLogoDark16']))

        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_multipleFiles,
                                              text='Learn more: Multiple files (Manual CIU)',
                                              bitmap=self.icons.iconsLib['panel_mll__16']))

        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_overlay,
                                              text='Learn more: Overlay documents',
                                              bitmap=self.icons.iconsLib['overlay16']))

#         helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_linearDT,
#                                               text='Learn more: Linear Drift-time analysis',
#                                               bitmap=self.icons.iconsLib['panel_dt_16']))
#
#         helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_CCScalibration,
#                                               text='Learn more: CCS calibration',
#                                               bitmap=self.icons.iconsLib['panel_ccs_16']))

        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_Interactive,
                                              text='Learn more: Interactive output',
                                              bitmap=self.icons.iconsLib['bokehLogo_16']))

        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_annotatingMassSpectra,
                                              text='Learn more: Annotating mass spectra',
                                              bitmap=self.icons.iconsLib['annotate16']))

        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_OtherData,
                                              text='Learn more: Annotated data',
                                              bitmap=self.icons.iconsLib['blank_16']))

        # HELP MENU
        menuHelp = wx.Menu()
        menuHelp.AppendMenu(wx.ID_ANY, 'Help pages...', helpPagesMenu)
        menuHelp.AppendSeparator()
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpGuide,
                                         text='Open User Guide... (online)',
                                         bitmap=self.icons.iconsLib['web_access_16']))
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpGuideLocal,
                                         text='Open User Guide... (local)',
                                         bitmap=self.icons.iconsLib['web_access_16']))
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpYoutube,
                                         text='Check out video guides... (online)',
                                         bitmap=self.icons.iconsLib['youtube16'],
                                         help_text=self.help.link_youtube))
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpNewVersion,
                                         text='Check for updates... (online)',
                                         bitmap=self.icons.iconsLib['github16']))
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpCite,
                                         text='Paper to cite... (online)',
                                         bitmap=self.icons.iconsLib['cite_16']))
        menuHelp.AppendSeparator()
        menuHelp.AppendMenu(wx.ID_ANY, 'About other software...', otherSoftwareMenu)
        menuHelp.AppendSeparator()
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpNewFeatures,
                                         text='Request new features... (web)',
                                         bitmap=self.icons.iconsLib['request_16']))
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpReportBugs,
                                         text='Report bugs... (web)',
                                         bitmap=self.icons.iconsLib['bug_16']))
        menuHelp.AppendSeparator()
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_CHECK_VERSION,
                                         text='Check for newest version...',
                                         bitmap=self.icons.iconsLib['check_online_16']))
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_WHATS_NEW,
                                         text='Whats new in v{}'.format(self.config.version),
                                         bitmap=self.icons.iconsLib['blank_16']))
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_SHOW_ABOUT,
                                         text='About ORIGAMI\tCtrl+Shift+A',
                                         bitmap=self.icons.iconsLib['origamiLogoDark16']))
        self.mainMenubar.Append(menuHelp, '&Help')
        self.SetMenuBar(self.mainMenubar)

        # Menu events
        self.Bind(wx.EVT_MENU_HIGHLIGHT_ALL, self.OnMenuHighlight)

        # Bind functions to menu
        # HELP MENU
        self.Bind(wx.EVT_MENU, self.onHelpAbout, id=ID_SHOW_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_check_ORIGAMI_version, id=ID_CHECK_VERSION)
        self.Bind(wx.EVT_MENU, self.on_whats_new, id=ID_WHATS_NEW)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpGuide)
        self.Bind(wx.EVT_MENU, self.onOpenUserGuide, id=ID_helpGuideLocal)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpCite)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpYoutube)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpNewVersion)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpReportBugs)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpNewFeatures)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpAuthor)
        self.Bind(wx.EVT_MENU, self.presenter.onRebootWindow, id=ID_RESET_ORIGAMI)

        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_UniDecInfo)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_gettingStarted)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_dataLoading)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_UniDec)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_ORIGAMI)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_overlay)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_multipleFiles)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_linearDT)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_CCScalibration)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_dataExtraction)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_Interactive)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_OtherData)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_annotatingMassSpectra)

        # FILE MENU
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_text_2D_fcn, id=ID_load_text_2D)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_multiple_text_2D_fcn, id=ID_load_multiple_text_2D)

        self.Bind(wx.EVT_MENU, self.data_handling.on_open_MassLynx_raw_fcn, id=ID_load_origami_masslynx_raw)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_MassLynx_raw_fcn, id=ID_openIRRawFile)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_multiple_MassLynx_raw_fcn,
                  id=ID_load_multiple_origami_masslynx_raw)

        self.Bind(wx.EVT_MENU, self.presenter.onCalibrantRawDirectory, id=ID_addCCScalibrantFile)
        self.Bind(wx.EVT_MENU, self.presenter.onLinearDTirectory, id=ID_openLinearDTRawFile)

        self.Bind(wx.EVT_MENU, self.data_handling.on_open_document_fcn, id=ID_openDocument)
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_save_document, id=ID_saveDocument)
        self.Bind(wx.EVT_MENU, self.data_handling.on_save_all_documents_fcn, id=ID_saveAllDocuments)
        self.Bind(wx.EVT_MENU, self.presenter.onIRTextFile, id=ID_openIRTextile)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_MassLynx_raw_MS_only_fcn,
                  id=ID_load_masslynx_raw_ms_only)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_single_text_MS_fcn, id=ID_load_text_MS)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_single_clipboard_MS, id=ID_load_clipboard_spectrum)
        self.Bind(wx.EVT_MENU, self.OnClose, id=ID_quit)
        self.Bind(wx.EVT_MENU, self.on_add_blank_document_interactive, id=ID_addNewInteractiveDoc)
        self.Bind(wx.EVT_MENU, self.on_add_blank_document_manual, id=ID_addNewManualDoc)
        self.Bind(wx.EVT_MENU, self.on_add_blank_document_overlay, id=ID_addNewOverlayDoc)
        self.Bind(wx.EVT_TOOL, self.on_open_multiple_files, id=ID_load_multiple_masslynx_raw)
        self.Bind(wx.EVT_TOOL, self.on_open_community_file, id=ID_fileMenu_MGF)
        self.Bind(wx.EVT_TOOL, self.on_open_community_file, id=ID_fileMenu_mzML)
        self.Bind(wx.EVT_TOOL, self.on_open_thermo_file, id=ID_fileMenu_thermoRAW)

        # PROCESS MENU
        self.Bind(wx.EVT_MENU, self.onProcessParameters, id=ID_processSettings_ExtractData)
        self.Bind(wx.EVT_MENU, self.onProcessParameters, id=ID_processSettings_ORIGAMI)
        self.Bind(wx.EVT_MENU, self.onProcessParameters, id=ID_processSettings_FindPeaks)
        self.Bind(wx.EVT_MENU, self.onProcessParameters, id=ID_processSettings_MS)
        self.Bind(wx.EVT_MENU, self.onProcessParameters, id=ID_processSettings_2D)
        self.Bind(wx.EVT_MENU, self.onProcessParameters, id=ID_processSettings_UniDec)

        # PLOT
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_general_plot)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_plot1D)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_plot2D)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_plot3D)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_legend)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_colorbar)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_rmsd)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_waterfall)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_violin)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_general)
        # self.Bind(wx.EVT_MENU, self.presenter.onRebootZoom, id=ID_plots_resetZoom)
        self.Bind(wx.EVT_MENU, self.updatePlots, id=ID_plots_showCursorGrid)

        self.Bind(wx.EVT_MENU, self.on_customise_annotation_plot_parameters, id=ID_annotPanel_otherSettings)
        self.Bind(wx.EVT_MENU, self.on_customise_unidec_plot_parameters, id=ID_unidecPanel_otherSettings)

        # OUTPUT
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveOverlayImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveMSImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveMZDTImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveRTImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_save1DImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_save2DImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_save3DImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveWaterfallImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveRMSDImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveRMSFImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveRMSDmatrixImage)
        self.Bind(wx.EVT_MENU, self.openSaveAsDlg, id=ID_saveAsInteractive)

        # UTILITIES
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_process_UVPD,
                  id=ID_docTree_plugin_UVPD)
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_MSMS_viewer,
                  id=ID_docTree_plugin_MSMS)

        # CONFIG MENU
        self.Bind(wx.EVT_MENU, self.on_export_configuration_file, id=ID_saveConfig)
        self.Bind(wx.EVT_MENU, self.on_export_configuration_file, id=ID_saveAsConfig)
        self.Bind(wx.EVT_MENU, self.on_import_configuration_file, id=ID_openConfig)
        self.Bind(wx.EVT_MENU, self.on_import_configuration_file, id=ID_openAsConfig)
        self.Bind(wx.EVT_MENU, self.on_setup_driftscope, id=ID_setDriftScopeDir)
        self.Bind(wx.EVT_MENU, self.on_check_driftscope_path, id=ID_check_Driftscope)
        self.Bind(wx.EVT_MENU, self.presenter.onSelectProtein, id=ID_selectCalibrant)
        self.Bind(wx.EVT_MENU, self.presenter.onImportCCSDatabase, id=ID_openCCScalibrationDatabse)
        self.Bind(wx.EVT_MENU, self.onExportParameters, id=ID_importExportSettings_peaklist)
        self.Bind(wx.EVT_MENU, self.onExportParameters, id=ID_importExportSettings_image)
        self.Bind(wx.EVT_MENU, self.onExportParameters, id=ID_importExportSettings_file)
        self.Bind(wx.EVT_MENU, self.onCheckToggle, id=ID_checkAtStart_Driftscope)
        self.Bind(wx.EVT_MENU, self.onCheckToggle, id=ID_importAtStart_CCS)

        # VIEW MENU
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, id=ID_window_all)
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, self.documentsPage)
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, self.mzTable)
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, self.multifieldTable)
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, self.textTable)
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, self.multipleMLTable)
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, self.ccsTable)
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, id=ID_window_logWindow)
        self.Bind(wx.EVT_MENU, self.onWindowMaximize, id=ID_windowMaximize)
        self.Bind(wx.EVT_MENU, self.onWindowIconize, id=ID_windowMinimize)
        self.Bind(wx.EVT_MENU, self.onWindowFullscreen, id=ID_windowFullscreen)
        self.Bind(wx.EVT_MENU, self.panelPlots.on_clear_all_plots, id=ID_clearAllPlots)
#         self.Bind(wx.EVT_MENU, self.onToolbarPosition, id=ID_toolbar_top)
#         self.Bind(wx.EVT_MENU, self.onToolbarPosition, id=ID_toolbar_bottom)
#         self.Bind(wx.EVT_MENU, self.onToolbarPosition, id=ID_toolbar_left)
#         self.Bind(wx.EVT_MENU, self.onToolbarPosition, id=ID_toolbar_right)
        self.Bind(wx.EVT_MENU, self.on_open_compare_MS_window, id=ID_docTree_compareMS)

    def on_customise_annotation_plot_parameters(self, evt):
        from gui_elements.dialog_customiseUserAnnotations import panelCustomiseParameters as panelCustomiseParameters_annotations

        dlg = panelCustomiseParameters_annotations(self, self.config)
        dlg.ShowModal()

    def on_customise_unidec_plot_parameters(self, evt):
        from gui_elements.dialog_customiseUniDecPlots import panelCustomiseParameters as panelCustomiseParameters_unidec

        dlg = panelCustomiseParameters_unidec(self, self.config, self.icons)
        dlg.ShowModal()

    def on_add_blank_document_manual(self, evt):
        self.presenter.onAddBlankDocument(evt=None, document_type='manual')

    def on_add_blank_document_interactive(self, evt):
        self.presenter.onAddBlankDocument(evt=None, document_type='interactive')

    def on_add_blank_document_overlay(self, evt):
        self.presenter.onAddBlankDocument(evt=None, document_type='overlay')

    def on_open_multiple_files(self, evt):
        self.data_handling.on_open_multiple_ML_files_fcn(open_type="multiple_files_new_document")

    def on_open_community_file(self, evt):
        evtID = evt.GetId()

        if evtID == ID_fileMenu_MGF:
            self.panelDocuments.documents.on_open_MGF_file_fcn(None)
        elif evtID == ID_fileMenu_mzML:
            self.panelDocuments.documents.on_open_mzML_file_fcn(None)

    def on_open_thermo_file(self, evt):
        self.panelDocuments.documents.on_open_thermo_file_fcn(None)

    def on_open_compare_MS_window(self, evt):
        self.panelDocuments.documents.onCompareMS(None)

    def on_import_configuration_file(self, evt, onStart=False):
        """
        This function imports configuration file
        """
        if not onStart:
            if evt.GetId() == ID_openConfig:
                config_path = os.path.join(self.config.cwd, 'configOut.xml')
                self.presenter.onThreading(
                    None, ("Imported configuration file: {}".format(config_path), 4), action='updateStatusbar')
                self.config.loadConfigXML(path=config_path, evt=None)
                self.updateRecentFiles()
                return
            elif evt.GetId() == ID_openAsConfig:
                dlg = wx.FileDialog(self, "Open Configuration File", wildcard="*.xml",
                                    style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
                if dlg.ShowModal() == wx.ID_OK:
                    fileName = dlg.GetPath()
                    self.config.loadConfigXML(path=fileName, evt=None)
                    self.updateRecentFiles()
        else:
            self.config.loadConfigXML(path='configOut.xml', evt=None)
            return

    def on_export_configuration_file(self, evt, verbose=True):
        if isinstance(evt, int):
            evtID = evt
        else:
            evtID = evt.GetId()

        if evtID == ID_saveConfig:
            try:
                save_dir = os.path.join(self.config.cwd, 'configOut.xml')
            except TypeError:
                return
            if self.config.threading:
                args = (save_dir, None, verbose)
                self.presenter.onThreading(None, args, action='export_settings')
            else:
                try:
                    self.config.saveConfigXML(path=save_dir, evt=None, verbose=verbose)
                except TypeError:
                    pass
        elif evtID == ID_saveAsConfig:
            dlg = wx.FileDialog(self, "Save As Configuration File", wildcard="*.xml",
                                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            dlg.SetFilename('configOut.xml')
            if dlg.ShowModal() == wx.ID_OK:
                fileName = dlg.GetPath()
                self.config.saveConfigXML(path=fileName, evt=None, verbose=verbose)

    def on_open_link(self, evt):
        """Open selected webpage."""

        if isinstance(evt, int):
            evtID = evt
        else:
            evtID = evt.GetId()

        # set link
        links = {ID_helpHomepage: 'home',
                 ID_helpGitHub: 'github',
                 ID_helpCite: 'cite',
                 ID_helpNewVersion: 'newVersion',
                 ID_helpYoutube: 'youtube',
                 ID_helpGuide: 'guide',
                 ID_helpHTMLEditor: 'htmlEditor',
                 ID_helpNewFeatures: 'newFeatures',
                 ID_helpReportBugs: 'reportBugs',
                 ID_helpAuthor: 'about-author'}

        link = self.config.links[links[evtID]]

        # open webpage
        try:
            self.presenter.onThreading(None, ("Opening a link in your default internet browser", 4),
                                       action='updateStatusbar')
            webbrowser.open(link, autoraise=1)
        except Exception:
            pass

    def on_check_ORIGAMI_version(self, evt=None):
        """
        Simple function to check whether this is the newest version available
        """
        try:
            newVersion = get_latest_version(link=self.config.links['newVersion'])
            update = compare_versions(newVersion, self.config.version)
            if not update:
                try:
                    if evt.GetId() == ID_CHECK_VERSION:
                        dlgBox(exceptionTitle='ORIGAMI',
                               exceptionMsg='You are using the most up to date version {}.'.format(
                                   self.config.version),
                               type="Info")
                except Exception:
                    pass
            else:
                webpage = get_latest_version(get_webpage=True)
                wx.Bell()
                message = "Version {} is now available for download.\nYou are currently using version {}.".format(
                    newVersion, self.config.version)
                self.presenter.onThreading(None, (message, 4),
                                           action='updateStatusbar')
                msgDialog = panelNotifyNewVersion(self, self.presenter, webpage)
                msgDialog.ShowModal()
        except Exception as e:
            self.presenter.onThreading(None, ('Could not check version number', 4),
                                       action='updateStatusbar')
            logger.error(e)

    def on_whats_new(self, evt):
        try:
            webpage = get_latest_version(get_webpage=True)
            msgDialog = panelNotifyNewVersion(self, self.presenter, webpage)
            msgDialog.ShowModal()
        except Exception:
            pass

    def onOpenUserGuide(self, evt):
        """
        Opens PDF viewer
        """
#         try:
#             os.startfile('UserGuide_ANALYSE.pdf')
#         except:
#             return
        link = os.path.join(os.getcwd(), "docs\index.html")
        try:
            self.presenter.onThreading(None, ("Opening local documentation in your browser...", 4),
                                       action='updateStatusbar')
            webbrowser.open(link, autoraise=1)
        except Exception:
            pass

    def on_open_HTML_guide(self, evt):
        from help_documentation import HTMLHelp as htmlPages

        htmlPages = htmlPages()
        evtID = evt.GetId()
        link, kwargs = None, {}
        if evtID == ID_help_UniDecInfo:
            kwargs = htmlPages.page_UniDec_info

        elif evtID == ID_help_page_dataLoading:
            link = os.path.join(os.getcwd(), "docs\\user-guide\loading-data.html")
            # kwargs = htmlPages.page_data_loading_info

        elif evtID == ID_help_page_gettingStarted:
            link = os.path.join(os.getcwd(), "docs\\user-guide\example-files.html")
            # kwargs = htmlPages.page_data_getting_started

        elif evtID == ID_help_page_UniDec:
            link = os.path.join(os.getcwd(), "docs\\user-guide\deconvolution\\unidec-deconvolution.html")
            # kwargs = htmlPages.page_deconvolution_info

        elif evtID == ID_help_page_ORIGAMI:
            link = os.path.join(os.getcwd(), "docs\\user-guide\data-handling\automated-ciu.html")
            # kwargs = htmlPages.page_origami_info

        elif evtID == ID_help_page_overlay:
            kwargs = htmlPages.page_overlay_info

        elif evtID == ID_help_page_multipleFiles:
            link = os.path.join(os.getcwd(), "docs\\user-guide\data-handling\manual-ciu.html")
            # kwargs = htmlPages.page_multiple_files_info

        elif evtID == ID_help_page_linearDT:
            kwargs = htmlPages.page_linear_dt_info

        elif evtID == ID_help_page_CCScalibration:
            kwargs = htmlPages.page_ccs_calibration_info

        elif evtID == ID_help_page_dataExtraction:
            link = os.path.join(os.getcwd(), "docs\\user-guide\data-handling\ms-and-imms-files.html")
            # kwargs = htmlPages.page_data_extraction_info

        elif evtID == ID_help_page_Interactive:
            link = os.path.join(os.getcwd(), "docs\\user-guide\interactive-output\simple-output.html")
            # kwargs = htmlPages.page_interactive_output_info

        elif evtID == ID_help_page_OtherData:
            kwargs = htmlPages.page_other_data_info

        elif evtID == ID_help_page_annotatingMassSpectra:
            kwargs = htmlPages.page_annotating_mass_spectra

        if link is None:
            htmlViewer = panelHTMLViewer(self, self.config, **kwargs)
            htmlViewer.Show()
        else:
            try:
                self.presenter.onThreading(None, ("Opening local documentation in your browser...", 4),
                                           action='updateStatusbar')
                webbrowser.open(link, autoraise=1)
            except Exception:
                pass

    def onCheckToggle(self, evt):
        evtID = evt.GetId()

        if evtID == ID_checkAtStart_Driftscope:
            check_value = not self.config.checkForDriftscopeAtStart
            self.config.checkForDriftscopeAtStart = check_value
            self.checkDriftscopeAtStart.Check(check_value)

        if evtID == ID_importAtStart_CCS:
            check_value = not self.config.loadCCSAtStart
            self.config.loadCCSAtStart = check_value
            self.loadCCSAtStart.Check(check_value)

    def OnMenuHighlight(self, evt):
        # Show how to get menu item info from this event handler
        itemID = evt.GetId()
        try:
            msg = self.GetMenuBar().FindItemById(itemID).GetHelp()
            self.SetStatusText(msg, number=4)
        except Exception:
            self.SetStatusText("", number=4)

    def onWindowMaximize(self, evt):
        """Maximize app."""
        self.Maximize()
    # ----

    def onWindowIconize(self, evt):
        """Iconize app."""
        self.Iconize()
    # ----

    def onWindowFullscreen(self, evt):
        """Fullscreen app."""
        self._fullscreen = not self._fullscreen
        self.ShowFullScreen(self._fullscreen, style=wx.FULLSCREEN_ALL & ~
                            (wx.FULLSCREEN_NOMENUBAR | wx.FULLSCREEN_NOSTATUSBAR))
    # ----

    def onHelpAbout(self, evt):
        """Show About mMass panel."""

        about = panelAbout(self, self.presenter,
                           'About ORIGAMI',
                           self.config,
                           self.icons)
        about.Centre()
        about.Show()
        about.SetFocus()

    def makeShortcuts(self):
        """
        Setup shortcuts for the GUI application
        """
        # Setup shortcuts. Format: 'KEY', 'FUNCTION', 'MODIFIER'
        ctrlkeys = [
            ["I", self.panelDocuments.documents.onOpenDocInfo, wx.ACCEL_CTRL],
            ["W", self.data_handling.on_open_multiple_text_2D, wx.ACCEL_CTRL],
            ["L", self.presenter.onOpenPeakListCSV, wx.ACCEL_CTRL],
            ["Z", self.openSaveAsDlg, wx.ACCEL_SHIFT],
            ["G", self.presenter.on_open_directory, wx.ACCEL_CTRL],
        ]
        keyIDs = [wx.NewId() for a in ctrlkeys]
        ctrllist = []
        for i, k in enumerate(ctrlkeys):
            self.Bind(wx.EVT_MENU, k[1], id=keyIDs[i])
            ctrllist.append((k[2], ord(k[0]), keyIDs[i]))

        # Add more shortcuts with known IDs
        extraKeys = [
            ["E", self.presenter.on_extract_2D_from_mass_range_threaded, wx.ACCEL_ALT, ID_extractAllIons],
            ["Q", self.presenter.on_overlay_2D, wx.ACCEL_ALT, ID_overlayMZfromList],
            ["W", self.presenter.on_overlay_2D, wx.ACCEL_ALT, ID_overlayTextFromList],
            ["S", self.panelDocuments.documents.onShowPlot, wx.ACCEL_ALT, ID_showPlotDocument],
            ["P", self.panelDocuments.documents.onProcess, wx.ACCEL_ALT, ID_process2DDocument],
            ["C", self.presenter.onCombineCEvoltagesMultiple, wx.ACCEL_ALT, ID_combineCEscans],
            ["R", self.panelDocuments.documents.onRenameItem, wx.ACCEL_ALT, ID_renameItem],
            ["X", self.panelDocuments.documents.onShowPlot, wx.ACCEL_ALT, ID_showPlotMSDocument],
            ["Z", self.presenter.onChangeChargeState, wx.ACCEL_ALT, ID_assignChargeState],
            ["V", self.panelDocuments.documents.onSaveCSV, wx.ACCEL_ALT, ID_saveDataCSVDocument],
        ]

        for item in extraKeys:
            self.Bind(wx.EVT_MENU, item[1], id=item[3])
            ctrllist.append((item[2], ord(item[0]), item[3]))

        self.SetAcceleratorTable(wx.AcceleratorTable(ctrllist))
        pass

    def on_open_source_menu(self, evt):
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_fileMenu_MGF,
                                     text='Open Mascot Generic Format file (.mgf) [MS/MS]',
                                     bitmap=self.icons.iconsLib['blank_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_fileMenu_mzML,
                                     text='Open mzML (.mzML) [MS/MS]',
                                     bitmap=self.icons.iconsLib['blank_16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def makeToolbar(self):

        # Bind events
        #         self.Bind(wx.EVT_TOOL, self.presenter.onOrigamiRawDirectory, id=ID_load_origami_masslynx_raw)
        #         self.Bind(wx.EVT_TOOL, self.data_handling.on_open_text_2D_fcn, id=ID_load_text_2D)
        #         self.Bind(wx.EVT_TOOL, self.presenter.onOrigamiRawDirectory, id=ID_load_masslynx_raw)
        #         self.Bind(wx.EVT_TOOL, self.on_open_source_menu, id=ID_mainPanel_openSourceFiles)

        # Create toolbar
        self.mainToolbar_horizontal = self.CreateToolBar((wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT))
        self.mainToolbar_horizontal.SetToolBitmapSize((12, 12))

        self.mainToolbar_horizontal.AddLabelTool(
            ID_openDocument, "", self.icons.iconsLib['open_project_16'],
            shortHelp="Open project file")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_saveDocument, "", self.icons.iconsLib['save16'],
            shortHelp="Save project file")
        self.mainToolbar_horizontal.AddSeparator()
        self.mainToolbar_horizontal.AddLabelTool(
            ID_load_origami_masslynx_raw, "", self.icons.iconsLib['open_origami_16'],
            shortHelp="Open MassLynx file (.raw)")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_load_origami_masslynx_raw, "", self.icons.iconsLib['open_masslynx_16'],
            shortHelp="Open MassLynx file (IM-MS)")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_load_multiple_masslynx_raw, "", self.icons.iconsLib['open_masslynxMany_16'],
            shortHelp="Open multiple MassLynx files (e.g. CIU/SID)")
        self.mainToolbar_horizontal.AddSeparator()
        self.mainToolbar_horizontal.AddLabelTool(
            ID_load_text_2D, "", self.icons.iconsLib['open_text_16'],
            shortHelp="Open text files (2D)")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_load_multiple_text_2D, "", self.icons.iconsLib['open_textMany_16'],
            shortHelp="Open multiple text files (2D)")
        self.mainToolbar_horizontal.AddSeparator()
        self.mainToolbar_horizontal.AddLabelTool(
            ID_mainPanel_openSourceFiles, "", self.icons.iconsLib['ms16'],
            shortHelp="Open MS/MS files...")
        self.mainToolbar_horizontal.AddSeparator()
        self.mainToolbar_horizontal.AddCheckTool(
            ID_window_documentList, "", self.icons.iconsLib['panel_doc_16'],
            shortHelp="Enable/Disable documents panel")
        self.mainToolbar_horizontal.AddCheckTool(
            ID_window_ionList, "", self.icons.iconsLib['panel_ion_16'],
            shortHelp="Enable/Disable multi ion panel")
        self.mainToolbar_horizontal.AddCheckTool(
            ID_window_textList, "", self.icons.iconsLib['panel_text_16'],
            shortHelp="Enable/Disable multi text panel")
        self.mainToolbar_horizontal.AddCheckTool(
            ID_window_multipleMLList, "", self.icons.iconsLib['panel_mll__16'],
            shortHelp="Enable/Disable multi MassLynx panel")
        self.mainToolbar_horizontal.AddCheckTool(
            ID_window_multiFieldList, "", self.icons.iconsLib['panel_dt_16'],
            shortHelp="Enable/Disable linear DT panel")
        self.mainToolbar_horizontal.AddCheckTool(
            ID_window_ccsList, "", self.icons.iconsLib['panel_ccs_16'],
            shortHelp="Enable/Disable CCS calibration panel")
        self.mainToolbar_horizontal.AddCheckTool(
            ID_window_logWindow, "", self.icons.iconsLib['panel_log_16'],
            shortHelp="Enable/Disable Log panel")
        self.mainToolbar_horizontal.AddSeparator()
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_general_plot, "", self.icons.iconsLib['panel_plot_general_16'],
            shortHelp="Settings: General plot")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_plot1D, "", self.icons.iconsLib['panel_plot1D_16'],
            shortHelp="Settings: Plot 1D panel")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_plot2D, "", self.icons.iconsLib['panel_plot2D_16'],
            shortHelp="Settings: Plot 2D panel")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_plot3D, "", self.icons.iconsLib['panel_plot3D_16'],
            shortHelp="Settings: Plot 3D panel")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_colorbar, "", self.icons.iconsLib['panel_colorbar_16'],
            shortHelp="Settings: Colorbar panel")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_legend, "", self.icons.iconsLib['panel_legend_16'],
            shortHelp="Settings: Legend panel")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_rmsd, "", self.icons.iconsLib['panel_rmsd_16'],
            shortHelp="Settings: RMSD panel")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_waterfall, "", self.icons.iconsLib['panel_waterfall_16'],
            shortHelp="Settings: Waterfall panel")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_violin, "", self.icons.iconsLib['panel_violin_16'],
            shortHelp="Settings: Violin panel")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_general, "", self.icons.iconsLib['panel_general2_16'],
            shortHelp="Settings: Extra panel")
        self.mainToolbar_horizontal.AddSeparator()
        self.mainToolbar_horizontal.AddLabelTool(
            ID_processSettings_ExtractData, "", self.icons.iconsLib['process_extract_16'],
            shortHelp="Settings: &Extract data\tShift+1")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_processSettings_ORIGAMI, "", self.icons.iconsLib['process_origami_16'],
            shortHelp="Settings: &ORIGAMI\tShift+2")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_processSettings_MS, "", self.icons.iconsLib['process_ms_16'],
            shortHelp="Settings: &Process mass spectra\tShift+3")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_processSettings_2D, "", self.icons.iconsLib['process_2d_16'],
            shortHelp="Settings: Process &2D heatmaps\tShift+4")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_processSettings_FindPeaks, "", self.icons.iconsLib['process_fit_16'],
            shortHelp="Settings: Peak &fitting\tShift+5")
        self.mainToolbar_horizontal.AddLabelTool(
            ID_processSettings_UniDec, "", self.icons.iconsLib['process_unidec_16'],
            shortHelp="Settings: &UniDec\tShift+6")
        self.mainToolbar_horizontal.AddSeparator()
        self.mainToolbar_horizontal.AddLabelTool(
            ID_saveAsInteractive, "", self.icons.iconsLib['bokehLogo_16'],
            shortHelp="Open interactive output panel")

        # Actually realise the toolbar
        self.mainToolbar_horizontal.Realize()

    def checkIfWindowsAreShown(self, evt):
        """ Check which windows are currently shown in the GUI"""

        if not self.panelDocuments.IsShown():
            self.documentsPage.Check(False)
        if not self.panelMultipleIons.IsShown():
            self.mzTable.Check(False)
        if not self.panelLinearDT.IsShown():
            self.multifieldTable.Check(False)
        if not self.panelMultipleText.IsShown():
            self.textTable.Check(False)
        if not self.panelMML.IsShown():
            self.multipleMLTable.Check(False)
        if not self.panelCCS.IsShown():
            self.ccsTable.Check(False)

        if evt is not None:
            evt.Skip()

    def onPaneOnOff(self, evt, check=None):

        if isinstance(evt, int):
            evtID = evt
        elif isinstance(evt, str):
            if evt == "document":
                evtID = ID_window_documentList
            elif evt == "ion":
                evtID = ID_window_ionList
            elif evt == "text":
                evtID = ID_window_textList
            elif evt == "ccs":
                evtID = ID_window_ccsList
            elif evt == "mass_spectra":
                evtID = ID_window_multipleMLList
            elif evt == "dt":
                evtID = ID_window_multiFieldList
            elif evt == "log":
                evtID = ID_window_logWindow

        elif evt is not None:
            evtID = evt.GetId()
        else:
            evtID = None

        if evtID is not None:
            if evtID == ID_window_documentList:
                if not self.panelDocuments.IsShown() or not self.documentsPage.IsChecked():
                    self._mgr.GetPane(self.panelDocuments).Show()
                    self.config._windowSettings['Documents']['show'] = True
                else:
                    self._mgr.GetPane(self.panelDocuments).Hide()
                    self.config._windowSettings['Documents']['show'] = False
                self.documentsPage.Check(self.config._windowSettings['Documents']['show'])
                self.onFindToggleBy_ID(find_id=evtID, check=self.config._windowSettings['Documents']['show'])
            elif evtID == ID_window_ccsList:
                if not self.panelCCS.IsShown() or check or not self.ccsTable.IsChecked():
                    self._mgr.GetPane(self.panelCCS).Show()
                    self.config._windowSettings['CCS calibration']['show'] = True
                else:
                    self._mgr.GetPane(self.panelCCS).Hide()
                    self.config._windowSettings['CCS calibration']['show'] = False
                self.ccsTable.Check(self.config._windowSettings['CCS calibration']['show'])
                self.onFindToggleBy_ID(find_id=evtID, check=self.config._windowSettings['CCS calibration']['show'])
            elif evtID == ID_window_ionList:
                if not self.panelMultipleIons.IsShown() or check or not self.mzTable.IsChecked():
                    self._mgr.GetPane(self.panelMultipleIons).Show()
                    self.config._windowSettings['Peak list']['show'] = True
                else:
                    self._mgr.GetPane(self.panelMultipleIons).Hide()
                    self.config._windowSettings['Peak list']['show'] = False
                self.mzTable.Check(self.config._windowSettings['Peak list']['show'])
                self.onFindToggleBy_ID(find_id=evtID, check=self.config._windowSettings['Peak list']['show'])
            elif evtID == ID_window_multipleMLList:
                if not self.panelMML.IsShown() or check or not self.multipleMLTable.IsChecked():
                    self._mgr.GetPane(self.panelMML).Show()
                    self.config._windowSettings['Multiple files']['show'] = True
                else:
                    self._mgr.GetPane(self.panelMML).Hide()
                    self.config._windowSettings['Multiple files']['show'] = False
                self.multipleMLTable.Check(self.config._windowSettings['Multiple files']['show'])
                self.onFindToggleBy_ID(find_id=evtID, check=self.config._windowSettings['Multiple files']['show'])
            elif evtID == ID_window_textList:
                if not self.panelMultipleText.IsShown() or check or not self.textTable.IsChecked():
                    self._mgr.GetPane(self.panelMultipleText).Show()
                    self.config._windowSettings['Text files']['show'] = True
                else:
                    self._mgr.GetPane(self.panelMultipleText).Hide()
                    self.config._windowSettings['Text files']['show'] = False
                self.textTable.Check(self.config._windowSettings['Text files']['show'])
                self.onFindToggleBy_ID(find_id=evtID, check=self.config._windowSettings['Text files']['show'])
            elif evtID == ID_window_multiFieldList:
                if not self.panelLinearDT.IsShown() or check or not self.multifieldTable.IsChecked():
                    self._mgr.GetPane(self.panelLinearDT).Show()
                    self.config._windowSettings['Linear Drift Cell']['show'] = True
                else:
                    self._mgr.GetPane(self.panelLinearDT).Hide()
                    self.config._windowSettings['Linear Drift Cell']['show'] = False
                self.multifieldTable.Check(self.config._windowSettings['Linear Drift Cell']['show'])
                self.onFindToggleBy_ID(find_id=evtID, check=self.config._windowSettings['Linear Drift Cell']['show'])
            elif evtID == ID_window_logWindow:
                if not self.panelLog.IsShown() or not self.window_logWindow.IsChecked():
                    self.panelLog.Show()
                    self._mgr.GetPane(self.panelLog).Show()
                    self.config._windowSettings['Log']['show'] = True
                else:
                    self._mgr.GetPane(self.panelLog).Hide()
                    self.panelLog.Hide()
                    self.config._windowSettings['Log']['show'] = False
                self.window_logWindow.Check(self.config._windowSettings['Log']['show'])
                self.onFindToggleBy_ID(find_id=evtID, check=self.config._windowSettings['Log']['show'])
            elif evtID == ID_window_all:
                for key in self.config._windowSettings:
                    self.config._windowSettings[key]['show'] = True

                self.onFindToggleBy_ID(check_all=True)

                for panel in [self.panelDocuments, self.panelMML,
                              self.panelMultipleIons, self.panelMultipleText,
                              self.panelCCS, self.panelLinearDT]:
                    self._mgr.GetPane(panel).Show()

                self.documentsPage.Check(self.config._windowSettings['Documents']['show'])
                self.mzTable.Check(self.config._windowSettings['Peak list']['show'])
                self.ccsTable.Check(self.config._windowSettings['CCS calibration']['show'])
                self.multifieldTable.Check(self.config._windowSettings['Linear Drift Cell']['show'])
                self.textTable.Check(self.config._windowSettings['Text files']['show'])
                self.multipleMLTable.Check(self.config._windowSettings['Multiple files']['show'])
                self.window_logWindow.Check(self.config._windowSettings['Log']['show'])

        # Checking at start of program
        else:
            if not self.panelDocuments.IsShown():
                self.config._windowSettings['Documents']['show'] = False
            if not self.panelMML.IsShown():
                self.config._windowSettings['Multiple files']['show'] = False
            if not self.panelMultipleIons.IsShown():
                self.config._windowSettings['Peak list']['show'] = False
            if not self.panelCCS.IsShown():
                self.config._windowSettings['CCS calibration']['show'] = False
            if not self.panelLinearDT.IsShown():
                self.config._windowSettings['Linear Drift Cell']['show'] = False
            if not self.panelMultipleText.IsShown():
                self.config._windowSettings['Text files']['show'] = False
            if not self.panelLog.IsShown():
                self.config._windowSettings['Log']['show'] = False

            self.documentsPage.Check(self.config._windowSettings['Documents']['show'])
            self.mzTable.Check(self.config._windowSettings['Peak list']['show'])
            self.ccsTable.Check(self.config._windowSettings['CCS calibration']['show'])
            self.multifieldTable.Check(self.config._windowSettings['Linear Drift Cell']['show'])
            self.textTable.Check(self.config._windowSettings['Text files']['show'])
            self.multipleMLTable.Check(self.config._windowSettings['Multiple files']['show'])
            self.window_logWindow.Check(self.config._windowSettings['Log']['show'])

        self._mgr.Update()

    def onFindToggleBy_ID(self, find_id=None, check=None, check_all=False):
        """
        Find toggle item by id in either horizontal/vertiacal toolbar
        """
        idList = [ID_window_documentList, ID_window_controls, ID_window_ccsList,
                  ID_window_ionList, ID_window_multipleMLList, ID_window_textList,
                  ID_window_multiFieldList, ID_window_logWindow]
        for itemID in idList:
            if check_all:
                self.mainToolbar_horizontal.ToggleTool(toolId=itemID, toggle=True)
            elif itemID == find_id:
                self.mainToolbar_horizontal.ToggleTool(toolId=find_id, toggle=check)
        if find_id == ID_window_all:
            self.mainToolbar_horizontal.ToggleTool(toolId=id, toggle=True)

    def onCheckToggleID(self, panel):
        panelDict = {'Documents': ID_window_documentList,
                     'Controls': ID_window_controls,
                     'Multiple files': ID_window_multipleMLList,
                     'Peak list': ID_window_ionList,
                     'Text files': ID_window_textList,
                     'CCS calibration': ID_window_ccsList,
                     'Linear Drift Cell': ID_window_multiFieldList,
                     'Log': ID_window_logWindow}
        return panelDict[panel]

    def OnClose(self, event):

        if len(self.presenter.documentsDict) > 0:
            if len(self.presenter.documentsDict) == 1:
                verb_form = "is"
            else:
                verb_form = "are"
            message = "There {} {} document(s) open.\n".format(verb_form, len(self.presenter.documentsDict)) + \
                "Are you sure you want to continue?"
            msgDialog = panelNotifyOpenDocuments(self, self.presenter, message)
            dlg = msgDialog.ShowModal()

            if dlg == wx.ID_NO:
                print('Cancelled operation')
                return
            else:
                pass

        # Try saving configuration file
        try:
            path = os.path.join(self.config.cwd, 'configOut.xml')
            self.config.saveConfigXML(path=path, evt=None)
        except Exception:
            print("Could not save configuration file")
            pass

        # Try unsubscribing events
        try:
            self.publisherOff()
        except Exception:
            print("Could not disable publisher")
            pass

        # Try killing window manager
        try:
            self._mgr.UnInit()
        except Exception:
            print("Could not uninitilize window manager")
            pass

        # Clear-up dictionary
        try:
            for title in self.presenter.documentsDict:
                del self.presenter.documentsDict[title]
                print(("Deleted {}".format(title)))
        except Exception:
            pass

        # Clear-up temporary data directory
        try:
            if self.config.temporary_data is not None:
                clean_directory(self.config.temporary_data)
                print(("Cleared {} from temporary files.".format(self.config.temporary_data)))
        except Exception as err:
            print(err)
            pass

        # Aggressive way to kill the ORIGAMI process (grrr)
        try:
            p = psutil.Process(self.config._processID)
            p.terminate()
        except Exception:
            pass

        self.Destroy()

    def publisherOff(self):
        """ Unsubscribe from all events """
        pub.unsubscribe(self.on_motion, 'motion_xy')
        pub.unsubscribe(self.motion_range, 'motion_range')
        pub.unsubscribe(self.on_distance, 'startX')
        pub.unsubscribe(self.presenter.OnChangedRMSF, 'changedZoom')

    def on_distance(self, startX):
        # Simple way of setting the start point
        self.startX = startX

    def on_motion(self, xpos, ypos, plotname):
        """
        Triggered by pubsub from plot windows. Reports text in Status Bar.
        :param xpos: x position fed from event
        :param ypos: y position fed from event
        :return: None
        """

        self.plot_name = plotname

        if xpos is not None and ypos is not None:
            # If measuring distance, additional fields are used to help user
            # make observations
            if self.startX is not None:
                range = np.absolute(self.startX - xpos)
                charge = np.round(1.0 / range, 1)
                mass = (xpos + charge) * charge
                # If inside a plot area with MS, give out charge state
                if self.mode == 'Measure' and self.panelPlots.currentPage in ["MS", "DT/MS"]:
                    self.SetStatusText("m/z=%.2f int=%.2f Δm/z=%.2f z=%.1f mw=%.1f" %
                                       (xpos, ypos, range, charge, mass), number=0)
                else:
                    if self.panelPlots.currentPage in ['MS']:
                        self.SetStatusText("m/z=%.4f int=%.4f Δm/z=%.2f" % (xpos, ypos, range), number=0)
                    elif self.panelPlots.currentPage in ['DT/MS']:
                        self.SetStatusText("m/z=%.4f dt=%.4f Δm/z=%.2f" % (xpos, ypos, range), number=0)
                    elif self.panelPlots.currentPage in ['RT']:
                        self.SetStatusText("scan=%.0f int=%.4f Δscans=%.2f" % (xpos, ypos, range), number=0)
                    elif self.panelPlots.currentPage in ['1D']:
                        self.SetStatusText("dt=%.2f int=%.4f Δdt=%.2f" % (xpos, ypos, range), number=0)
                    elif self.panelPlots.currentPage in ['2D']:
                        self.SetStatusText("x=%.4f dt=%.4f Δx=%.2f" % (xpos, ypos, range), number=0)
                    else:
                        self.SetStatusText("x=%.4f y=%.4f Δx=%.2f" % (xpos, ypos, range), number=0)
            else:
                if self.panelPlots.currentPage in ['MS']:
                    self.SetStatusText("m/z=%.4f int=%.4f" % (xpos, ypos), number=0)
                elif self.panelPlots.currentPage in ['DT/MS']:
                    if self.plot_data['DT/MS'] is not None and len(self.plot_scale['DT/MS']) == 2:
                        try:
                            yIdx = int(ypos * self.plot_scale['DT/MS'][0]) - 1
                            xIdx = int(xpos * self.plot_scale['DT/MS'][1]) - 1
                            int_value = self.plot_data['DT/MS'][yIdx, xIdx]
                        except Exception:
                            int_value = 0.
                        self.SetStatusText("m/z={:.4f} dt={:.4f} int={:.2f}".format(xpos, ypos, int_value), number=0)
                    else:
                        self.SetStatusText("m/z=%.4f dt=%.4f" % (xpos, ypos), number=0)
                elif self.panelPlots.currentPage in ['RT']:
                    self.SetStatusText("scan=%.0f int=%.2f" % (xpos, ypos), number=0)
                elif self.panelPlots.currentPage in ['1D']:
                    self.SetStatusText("dt=%.2f int=%.2f" % (xpos, ypos), number=0)
                elif self.panelPlots.currentPage in ['2D']:
                    try:
                        if self.plot_data['2D'] is not None and len(self.plot_scale['2D']) == 2:
                            try:
                                yIdx = int(ypos * self.plot_scale['2D'][0]) - 1
                                xIdx = int(xpos * self.plot_scale['2D'][1]) - 1
                                int_value = self.plot_data['2D'][yIdx, xIdx]
                            except Exception:
                                int_value = ""
                            self.SetStatusText("x=%.2f dt=%.2f int=%.2f" % (xpos, ypos, int_value), number=0)
                        else:
                            self.SetStatusText("x=%.2f dt=%.2f" % (xpos, ypos), number=0)
                    except Exception:
                        self.SetStatusText("x=%.2f dt=%.2f" % (xpos, ypos), number=0)
                elif plotname == "zGrid":
                    self.SetStatusText("x=%.2f charge=%.0f" % (xpos, ypos), number=0)
                elif plotname == "mwDistribution":
                    self.SetStatusText("MW=%.2f intensity=%.2f" % (xpos, ypos), number=0)
                else:
                    self.SetStatusText("x=%.2f y=%.2f" % (xpos, ypos), number=0)

        pass

    def motion_range(self, dataOut):
        minx, maxx, miny, maxy = dataOut
        if self.mode == 'Add data':
            self.SetStatusText("Range X=%.2f-%.2f Y=%.2f-%.2f" % (minx, maxx, miny, maxy), number=4)
        else:
            self.SetStatusText("", number=4)

    def OnSize(self, event):
        self.resized = True  # set dirty

    def OnIdle(self, event):
        if self.resized:
            # take action if the dirty flag is set
            self.resized = False  # reset the flag

    def getYvalue(self, msList, mzStart, mzEnd):
        """
        This helper function determines the maximum value of X-axis
        """
        msList = getNarrow1Ddata(data=msList, mzRange=(mzStart, mzEnd))
        mzYMax = np.round(findPeakMax(data=msList) * 100, 1)
        return mzYMax

    def extract_from_plot_2D(self, dataOut):
        self.currentPage = self.panelPlots.mainBook.GetPageText(self.panelPlots.mainBook.GetSelection())

        if self.currentPage == "DT/MS":
            xlabel = self.panelPlots.plotMZDT.plot_labels.get("xlabel", "m/z")
            ylabel = self.panelPlots.plotMZDT.plot_labels.get("ylabel", "Drift time (bins)")
        elif self.currentPage == "2D":
            xlabel = self.panelPlots.plot2D.plot_labels.get("xlabel", "Scans")
            ylabel = self.panelPlots.plot2D.plot_labels.get("ylabel", "Drift time (bins)")

        xmin, xmax, ymin, ymax = dataOut
        if xmin is None or xmax is None or ymin is None or ymax is None:
            self.SetStatusText("Extraction range was from outside of the plot area. Try again", number=4)
            return

        xmin = np.round(xmin, 2)
        xmax = np.round(xmax, 2)

        if ylabel == "Drift time (bins)":
            ymin = int(np.round(ymin, 0))
            ymax = int(np.round(ymax, 0))
        elif ylabel in ["Drift time (ms)", "Arrival time (ms)"]:
            ymin, ymax = ymin, ymax
        else:
            return

        if xlabel == "Scans":
            xmin = np.ceil(xmin).astype(int)
            xmax = np.floor(xmax).astype(int)
        elif xlabel in ['Retention time (min)', 'Time (min)', 'm/z']:
            xmin, xmax = xmin, xmax
        else:
            return

        # Reverse values if they are in the wrong order
        if xmax < xmin:
            xmax, xmin = xmin, xmax
        if ymax < ymin:
            ymax, ymin = ymin, ymax

        # Extract data
        if self.currentPage == "DT/MS":
            self.presenter.on_extract_RT_from_mzdt(xmin, xmax, ymin, ymax,
                                                   units_x=xlabel, units_y=ylabel)
        elif self.currentPage == "2D":
            self.presenter.on_extract_MS_from_heatmap(xmin, xmax, ymin, ymax,
                                                      units_x=xlabel, units_y=ylabel)
        self.SetStatusText("", number=4)

    def extract_from_plot_1D(self, xvalsMin, xvalsMax, yvalsMax, currentView=None, currentDoc=""):
        self.currentPage = self.panelPlots.mainBook.GetPageText(self.panelPlots.mainBook.GetSelection())
        self.SetStatusText("", number=4)

        # get current document
        if currentDoc == "":
            currentDoc = self.presenter.currentDoc

        # Get current document
        currentDocument = self.presenter.view.panelDocuments.documents.on_enable_document()
        if currentDocument == "Current documents":
            return

        document = self.presenter.documentsDict[currentDocument]

        if self.currentPage in ['RT', 'MS', '1D', '2D'] and document.dataType == 'Type: Interactive':
            args = ("Cannot extract data from Interactive document", 4)
            self.presenter.onThreading(None, args, action='updateStatusbar')
            return

        # Extract mass spectrum from mobiligram window
        elif self.currentPage == '1D':
            dt_label = self.panelPlots.plot1D.plot_labels.get("xlabel", "Drift time (bins)")

            if xvalsMin is None or xvalsMax is None:
                args = ('Your extraction range was outside the window. Please try again', 4)
                self.presenter.onThreading(None, args, action='updateStatusbar')
                return

            if dt_label == "Drift time (bins)":
                dtStart = np.ceil(xvalsMin).astype(int)
                dtEnd = np.floor(xvalsMax).astype(int)
            else:
                dtStart = xvalsMin
                dtEnd = xvalsMax

            # Check that values are in correct order
            if dtEnd < dtStart:
                dtEnd, dtStart = dtStart, dtEnd

            self.presenter.on_extract_MS_from_mobiligram(dtStart=dtStart, dtEnd=dtEnd, units=dt_label)

        # Extract heatmap from mass spectrum window
        elif self.currentPage == "MS" or currentView == "MS":
            if xvalsMin is None or xvalsMax is None:
                self.SetStatusText('Your extraction range was outside the window. Please try again', 3)
                return

            if document.fileFormat == "Format: Thermo (.RAW)":
                return

            mzStart = np.round(xvalsMin, 2)
            mzEnd = np.round(xvalsMax, 2)

            mzYMax = np.round(yvalsMax * 100, 1)
            # Check that values are in correct order
            if mzEnd < mzStart:
                mzEnd, mzStart = mzStart, mzEnd

            # Make sure the document has MS in first place (i.e. Text)
            if not self.presenter.documentsDict[currentDoc].gotMS:
                return
            # Get MS data for specified region and extract Y-axis maximum
            ms = self.presenter.documentsDict[currentDoc].massSpectrum
            ms = np.transpose([ms['xvals'], ms['yvals']])
            mzYMax = self.getYvalue(msList=ms, mzStart=mzStart, mzEnd=mzEnd)

            # predict charge state
            charge = self.data_processing.predict_charge_state(ms[:, 0], ms[:, 1], (mzStart, mzEnd))
            color = self.panelMultipleIons.on_check_duplicate_colors(
                self.config.customColors[randomIntegerGenerator(0, 15)])
            color = convertRGB255to1(color)

            if (document.dataType == 'Type: ORIGAMI' or
                document.dataType == 'Type: MANUAL' or
                    document.dataType == 'Type: Infrared'):
                self.onPaneOnOff(evt=ID_window_ionList, check=True)
                # Check if value already present
                outcome = self.panelMultipleIons.onCheckForDuplicates(mzStart=str(mzStart),
                                                                      mzEnd=str(mzEnd))
                if outcome:
                    self.SetStatusText('Selected range already in the table', 3)
                    if currentView == "MS":
                        return outcome
                    return

                _add_to_table = {"mz_start": mzStart,
                                 "mz_end": mzEnd,
                                 "charge": charge,
                                 "mz_ymax": mzYMax,
                                 "color": convertRGB1to255(color),
                                 "colormap": self.config.overlay_cmaps[randomIntegerGenerator(0,
                                                                                              len(self.config.overlay_cmaps) - 1)],
                                 "alpha": self.config.overlay_defaultAlpha,
                                 "mask": self.config.overlay_defaultMask,
                                 "document": currentDoc}
                self.panelMultipleIons.on_add_to_table(_add_to_table, check_color=False)

                if self.config.showRectanges:
                    self.panelPlots.on_plot_patches(mzStart, 0, (mzEnd - mzStart), 100000000000,
                                                    color=color, alpha=self.config.markerTransparency_1D,
                                                    repaint=True)

                if self.panelMultipleIons.extractAutomatically:
                    self.presenter.on_extract_2D_from_mass_range_threaded(None, extract_type="new")

            elif document.dataType == 'Type: Multifield Linear DT':
                self.onPaneOnOff(evt=ID_window_multiFieldList, check=True)
                # Check if value already present
                outcome = self.panelLinearDT.bottomP.onCheckForDuplicates(mzStart=str(mzStart),
                                                                          mzEnd=str(mzEnd))
                if outcome:
                    return
                self.panelLinearDT.bottomP.peaklist.Append([mzStart, mzEnd,
                                                            mzYMax, "",
                                                            self.presenter.currentDoc])

                if self.config.showRectanges:
                    self.panelPlots.on_plot_patches(mzStart, 0, (mzEnd - mzStart), 100000000000,
                                                    color=self.config.annotColor,
                                                    alpha=self.config.markerTransparency_1D,
                                                    repaint=True)

        # # Extract data from calibration window
        # if self.currentPage == "Calibration":
        #     # Check whether the current document is of correct type!
        #     if (document.fileFormat != 'Format: MassLynx (.raw)' or document.dataType != 'Type: CALIBRANT'):
        #         print('Please select the correct document file in document window!')
        #         return
        #     mzVal = np.round((xvalsMax + xvalsMin) / 2, 2)
        #     # prevents extraction if value is below 50. This assumes (wrongly!)
        #     # that the m/z range will never be below 50.
        #     if xvalsMax < 50:
        #         self.SetStatusText('Make sure you are extracting in the MS window.', 3)
        #         return
        #     # Check if value already present
        #     outcome = self.panelCCS.topP.onCheckForDuplicates(mzCentre=str(mzVal))
        #     if outcome:
        #         return
        #     self._mgr.GetPane(self.panelCCS).Show()
        #     self.ccsTable.Check(True)
        #     self._mgr.Update()
        #     if yvalsMax <= 1:
        #         tD = self.presenter.onAddCalibrant(path=document.path,
        #                                            mzCentre=mzVal,
        #                                            mzStart=np.round(xvalsMin, 2),
        #                                            mzEnd=np.round(xvalsMax, 2),
        #                                            pusherFreq=document.parameters['pusherFreq'],
        #                                            tDout=True)

        #         self.panelCCS.topP.peaklist.Append([currentDocument,
        #                                             np.round(xvalsMin, 2),
        #                                             np.round(xvalsMax, 2),
        #                                             "", "", "", str(tD)])
        #         if self.config.showRectanges:
        #             self.presenter.addRectMS(xvalsMin, 0, (xvalsMax - xvalsMin), 1.0,
        #                                      color=self.config.annotColor,
        #                                      alpha=(self.config.annotTransparency / 100),
        #                                      repaint=True, plot='CalibrationMS')

        # Extract mass spectrum from chromatogram window - Linear DT files
        elif self.currentPage == "RT" and document.dataType == 'Type: Multifield Linear DT':
            self._mgr.GetPane(self.panelLinearDT).Show()
            self.multifieldTable.Check(True)
            self._mgr.Update()
            xvalsMin = np.ceil(xvalsMin).astype(int)
            xvalsMax = np.floor(xvalsMax).astype(int)
            # Check that values are in correct order
            if xvalsMax < xvalsMin:
                xvalsMax, xvalsMin = xvalsMin, xvalsMax

            # Check if value already present
            outcome = self.panelLinearDT.topP.onCheckForDuplicates(rtStart=str(xvalsMin),
                                                                   rtEnd=str(xvalsMax))
            if outcome:
                return
            xvalDiff = xvalsMax - xvalsMin.astype(int)
            self.panelLinearDT.topP.peaklist.Append([xvalsMin, xvalsMax,
                                                     xvalDiff, "",
                                                     self.presenter.currentDoc])

            self.panelPlots.on_add_patch(xvalsMin, 0, (xvalsMax - xvalsMin), 100000000000,
                                         color=self.config.annotColor,
                                         alpha=(self.config.annotTransparency / 100),
                                         repaint=True, plot="RT")

        # Extract mass spectrum from chromatogram window
        elif self.currentPage == 'RT' and document.dataType != 'Type: Multifield Linear DT':
            rt_label = self.panelPlots.plotRT.plot_labels.get("xlabel", "Scans")

            # Get values
            if xvalsMin is None or xvalsMax is None:
                self.SetStatusText("Extraction range was from outside of the plot area. Try again",
                                   number=4)
                return
            if rt_label == "Scans":
                xvalsMin = np.ceil(xvalsMin).astype(int)
                xvalsMax = np.floor(xvalsMax).astype(int)

            # Check that values are in correct order
            if xvalsMax < xvalsMin:
                xvalsMax, xvalsMin = xvalsMin, xvalsMax

            # Check if difference between the two values is large enough
            if (xvalsMax - xvalsMin) < 1 and rt_label == "Scans":
                self.SetStatusText('The scan range you selected was too small. Please choose wider range', 3)
                return
            # Extract data
            if document.fileFormat == "Format: Thermo (.RAW)":
                return
            else:
                self.presenter.on_extract_MS_from_chromatogram(startScan=xvalsMin, endScan=xvalsMax, units=rt_label)

        else:
            return

    def onAnnotatePanel(self, evt):
        pass
#         if not self.panelParametersEdit.IsShown()

    def onPlotParameters(self, evt):
        if evt.GetId() == ID_extraSettings_colorbar:
            kwargs = {'window': 'Colorbar'}
        elif evt.GetId() == ID_extraSettings_legend:
            kwargs = {'window': 'Legend'}
        elif evt.GetId() == ID_extraSettings_plot1D:
            kwargs = {'window': 'Plot 1D'}
        elif evt.GetId() == ID_extraSettings_plot2D:
            kwargs = {'window': 'Plot 2D'}
        elif evt.GetId() == ID_extraSettings_plot3D:
            kwargs = {'window': 'Plot 3D'}
        elif evt.GetId() == ID_extraSettings_rmsd:
            kwargs = {'window': 'RMSD'}
        elif evt.GetId() == ID_extraSettings_waterfall:
            kwargs = {'window': 'Waterfall'}
        elif evt.GetId() == ID_extraSettings_violin:
            kwargs = {'window': 'Violin'}
        elif evt.GetId() == ID_extraSettings_general:
            kwargs = {'window': 'Extra'}
        elif evt.GetId() == ID_extraSettings_general_plot:
            kwargs = {'window': 'General'}

        if not self.panelParametersEdit.IsShown() or not self.config._windowSettings['Plot parameters']['show']:
            if self.config._windowSettings['Plot parameters']['floating']:
                self._mgr.GetPane(self.panelParametersEdit).Float()

            self._mgr.GetPane(self.panelParametersEdit).Show()
            self.config._windowSettings['Plot parameters']['show'] = True
            self.panelParametersEdit.onSetPage(**kwargs)
            self._mgr.Update()
        else:
            args = ("An instance of this panel is already open - changing page to: %s" % kwargs['window'], 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
            self.panelParametersEdit.onSetPage(**kwargs)
            return

    def onProcessParameters(self, evt, **pKwargs):

        # get evt id
        if isinstance(evt, int):
            evtID = evt
        else:
            evtID = evt.GetId()

        if evtID == ID_processSettings_ExtractData:
            kwargs = {'window': 'Extract'}
        elif evtID == ID_processSettings_MS:
            kwargs = {'window': 'MS'}
        elif evtID == ID_processSettings_2D:
            kwargs = {'window': '2D'}
        elif evtID == ID_processSettings_ORIGAMI:
            kwargs = {'window': 'ORIGAMI'}
        elif evtID == ID_processSettings_FindPeaks:
            kwargs = {'window': 'Peak fitting'}
        elif evtID == ID_processSettings_UniDec:
            kwargs = {'window': 'UniDec'}

        kwargs['processKwargs'] = pKwargs

        if self.config.processParamsWindow_on_off:
            args = ("An instance of this panel is already open - changing page to: %s" % kwargs['window'], 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
            self.panelProcessData.onSetPage(**kwargs)
            return

        try:
            self.config.processParamsWindow_on_off = True
            self.panelProcessData = panelProcessData(self,
                                                     self.presenter,
                                                     self.config,
                                                     self.icons,
                                                     **kwargs)
            self.panelProcessData.Show()
        except (ValueError, AttributeError, TypeError, KeyError, wx._core.PyAssertionError) as e:
            self.config.processParamsWindow_on_off = False
            dlgBox(exceptionTitle='Failed to open panel',
                   exceptionMsg=str(e),
                   type="Error")
            return

    def onExportParameters(self, evt):
        if evt.GetId() == ID_importExportSettings_image:
            kwargs = {'window': 'Image'}
        elif evt.GetId() == ID_importExportSettings_file:
            kwargs = {'window': 'Files'}
        elif evt.GetId() == ID_importExportSettings_peaklist:
            kwargs = {'window': 'Peaklist'}

        if self.config.importExportParamsWindow_on_off:
            args = ("An instance of this panel is already open - changing page to: %s" % kwargs['window'], 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
            self.panelImportExportParameters.onSetPage(**kwargs)
            return

        self.SetStatusText("", 4)

        try:
            self.config.importExportParamsWindow_on_off = True
            self.panelImportExportParameters = panelExportSettings(self,
                                                                   self.presenter,
                                                                   self.config,
                                                                   self.icons,
                                                                   **kwargs)
            self.panelImportExportParameters.Show()
        except (ValueError, AttributeError, TypeError, KeyError) as e:
            self.config.importExportParamsWindow_on_off = False
            dlgBox(exceptionTitle='Failed to open panel',
                   exceptionMsg=str(e),
                   type="Error")
            return

    def onSequenceEditor(self, evt):
        self.panelSequenceAnalysis = panelSequenceAnalysis(self,
                                                           self.presenter,
                                                           self.config,
                                                           self.icons)
        self.panelSequenceAnalysis.Show()

    def openSaveAsDlg(self, evt):
        try:
            if self.config.interactiveParamsWindow_on_off:
                self.interactivePanel.onUpdateList()
                args = ("An instance of this panel is already open", 4)
                self.presenter.onThreading(evt, args, action='updateStatusbar')
                return
        except Exception:
            pass

#         try:
        self.config.interactiveParamsWindow_on_off = True
        self.interactivePanel = panelInteractive(self, self.icons, self.presenter, self.config)
        self.interactivePanel.Show()
#         except (ValueError, AttributeError, TypeError, KeyError, NameError) as e:
#             self.config.interactiveParamsWindow_on_off = False
#             dlgBox(exceptionTitle='Failed to open panel',
#                    exceptionMsg=str(e),
#                    type="Error")
#             return

    def updateRecentFiles(self, path=None):
        """
        path = dictionary {'file_path': path, 'file_type': file type}
        """

        if path:
            if path in self.config.previousFiles:
                del self.config.previousFiles[self.config.previousFiles.index(path)]
            self.config.previousFiles.insert(0, path)
            # make sure only 10 items are present in the list
            while len(self.config.previousFiles) > 10:
                del self.config.previousFiles[-1]

        # clear menu
        for item in self.menuRecent.GetMenuItems():
            self.menuRecent.Delete(item.GetId())

        # populate menu
        for i, __ in enumerate(self.config.previousFiles):
            ID = eval('ID_documentRecent' + str(i))
            path = self.config.previousFiles[i]['file_path']
            self.menuRecent.Insert(i, ID, path, "Open Document")
            self.Bind(wx.EVT_MENU, self.onDocumentRecent, id=ID)
            if not os.path.exists(path):
                self.menuRecent.Enable(ID, False)

        # append clear
        if len(self.config.previousFiles) > 0:
            self.menuRecent.AppendSeparator()

        self.menuRecent.Append(ID_fileMenu_clearRecent, "Clear Menu", "Clear recent items")
        self.Bind(wx.EVT_MENU, self.onDocumentClearRecent, id=ID_fileMenu_clearRecent)

        if self.config.autoSaveSettings:
            self.on_export_configuration_file(evt=ID_saveConfig, verbose=False)

    def onDocumentClearRecent(self, evt):
        """Clear recent items."""

        self.config.previousFiles = []
        self.updateRecentFiles()

    def onDocumentRecent(self, evt):
        """Open recent document."""

        # get index
        indexes = {ID_documentRecent0: 0, ID_documentRecent1: 1, ID_documentRecent2: 2,
                   ID_documentRecent3: 3, ID_documentRecent4: 4, ID_documentRecent5: 5,
                   ID_documentRecent6: 6, ID_documentRecent7: 7, ID_documentRecent8: 8,
                   ID_documentRecent9: 9}

        # get file information
        documentID = indexes[evt.GetId()]
        file_path = self.config.previousFiles[documentID]['file_path']
        file_type = self.config.previousFiles[documentID]['file_type']

        # open file
        if file_type == 'pickle':
            self.data_handling.on_open_document_fcn(file_path=file_path, evt=None)
        elif file_type == 'MassLynx':
            self.data_handling.on_open_MassLynx_raw_fcn(path=file_path, evt=ID_load_masslynx_raw)
        elif file_type == 'ORIGAMI':
            self.data_handling.on_open_MassLynx_raw_fcn(path=file_path, evt=ID_load_origami_masslynx_raw)
        elif file_type == 'Infrared':
            self.data_handling.on_open_MassLynx_raw_fcn(path=file_path, evt=ID_openIRRawFile)
        elif file_type == 'Text':
            self.data_handling.__on_add_text_2D(None, file_path)
        elif file_type == 'Text_MS':
            self.data_handling.on_open_single_text_MS(path=file_path)

    def onOpenFile_DnD(self, file_path, file_extension):
        # open file
        if file_extension in ['.pickle', '.pkl']:
            self.data_handling.on_open_document_fcn(file_path=file_path, evt=None)
        elif file_extension == '.raw':
            self.data_handling.on_open_MassLynx_raw_fcn(path=file_path, evt=ID_load_origami_masslynx_raw)
        elif file_extension in ['.txt', '.csv', '.tab']:
            file_format = check_file_type(path=file_path)
            if file_format == "2D":
                self.data_handling.__on_add_text_2D(None, file_path)
            else:
                self.data_handling.__on_add_text_MS(path=file_path)

    def updateStatusbar(self, msg, position, delay=3, modify_msg=True, print_msg=True):
        """
        Out of thread statusbar display

        Parameters
        ----------
        msg: str
            message to be displayed for specified amount of time
        position: int
            which statusbar box the msg should be displayed in
        delay: int
            number of seconds for which the msg should be displayed for
        modify_msg: bool
            determines whether text should be wrapped between >> TEXT <<
        print_msg: bool
            determines whether message should be printed to console
        """
        # modify message
        if modify_msg:
            msg = ">> %s <<" % msg

        if print_msg:
            logger.info(msg)

        try:
            self.SetStatusText(msg, number=position)
            sleep(delay)
            self.SetStatusText("", number=position)
        except Exception as e:
            logger.warning("Could not update statusbar :: {}".format(e))

    def updatePlots(self, evt):
        """
        build and update parameters in the zoom function
        """
        plot_parameters = {'grid_show': self.config._plots_grid_show,
                           'grid_color': self.config._plots_grid_color,
                           'grid_line_width': self.config._plots_grid_line_width,
                           'extract_color': self.config._plots_extract_color,
                           'extract_line_width': self.config._plots_extract_line_width,
                           'extract_crossover_sensitivity_1D': self.config._plots_extract_crossover_1D,
                           'extract_crossover_sensitivity_2D': self.config._plots_extract_crossover_2D,
                           'zoom_color_vertical': self.config._plots_zoom_vertical_color,
                           'zoom_color_horizontal': self.config._plots_zoom_horizontal_color,
                           'zoom_color_box': self.config._plots_zoom_box_color,
                           'zoom_line_width': self.config._plots_zoom_line_width,
                           'zoom_crossover_sensitivity': self.config._plots_zoom_crossover
                           }
        pub.sendMessage('plot_parameters', plot_parameters=plot_parameters)

        if evt is not None:
            evt.Skip()

    def onEnableDisableLogging(self, evt, show_msg=True):

        self.config.logging = False
        if show_msg:
            msg = "Logging to file was temporarily disabled as there is a persistent bug that prevents it correct operation. Apologies, LM"
            dlgBox(exceptionTitle="Error",
                   exceptionMsg=msg,
                   type="Error")
        return

        log_directory = os.path.join(self.config.cwd, "logs")
        if not os.path.exists(log_directory):
            print(("Directory logs did not exist - created a new one in %s" % log_directory))
            os.makedirs(log_directory)

        # Generate filename
        if self.config.loggingFile_path is None:
            file_path = "ORIGAMI_%s.log" % self.config.startTime
            self.config.loggingFile_path = os.path.join(log_directory, file_path)
            # logging.basicConfig(filename=self.config.loggingFile_path,level=logging.DEBUG)
            if self.config.logging:
                print(('\nGenerated log filename: %s' % self.config.loggingFile_path))

        if self.config.logging:
            sys.stdin = self.panelLog.log
            sys.stdout = self.panelLog.log
            sys.stderr = self.panelLog.log
        else:
            sys.stdin = self.config.stdin
            sys.stdout = self.config.stdout
            sys.stderr = self.config.stderr

        if evt is not None:
            evt.Skip()

    def onEnableDisableThreading(self, evt):

        if self.config.threading:
            dlgBox(
                exceptionTitle="Warning",
                exceptionMsg="Multi-threading is only an experimental feature for now! It might occasionally crash ORIGAMI, in which case you will lose your processed data!",
                type="Warning")
        if evt is not None:
            evt.Skip()

    def on_setup_driftscope(self, evt):
        """
        This function sets the Driftscope directory
        """
        dlg = wx.DirDialog(self.view, "Choose Driftscope path. Usually at C:\DriftScope\lib",
                           style=wx.DD_DEFAULT_STYLE)
        try:
            if os.path.isdir(self.config.driftscopePath):
                dlg.SetPath(self.config.driftscopePath)
        except Exception:            pass

        if dlg.ShowModal() == wx.ID_OK:
            if os.path.basename(dlg.GetPath()) == "lib":
                path = dlg.GetPath()
            elif os.path.basename(dlg.GetPath()) == "DriftScope":
                path = os.path.join(dlg.GetPath(), "lib")
            else:
                path = dlg.GetPath()

            self.config.driftscopePath = path

            self.onThreading(None, ("Driftscope path was set to {}".format(
                self.config.driftscopePath), 4), action='updateStatusbar')

            # Check if driftscope exists
            if not os.path.isdir(self.config.driftscopePath):
                print('Could not find Driftscope path')
                msg = "Could not localise Driftscope directory. Please setup path to Dritscope lib folder. It usually exists under C:\DriftScope\lib"
                dlgBox(exceptionTitle='Could not find Driftscope',
                       exceptionMsg=msg, type="Warning")

            if not os.path.isfile(self.config.driftscopePath + "\imextract.exe"):
                print('Could not find imextract.exe')
                msg = "Could not localise Driftscope imextract.exe program. Please setup path to Dritscope lib folder. It usually exists under C:\DriftScope\lib"
                dlgBox(exceptionTitle='Could not find Driftscope',
                       exceptionMsg=msg, type="Warning")
        evt.Skip()

    def on_check_driftscope_path(self, evt=None):
        check = self.config.initlizePaths(return_check=True)
        if check:
            wx.Bell()
            dlgBox(exceptionTitle='DriftScope path looks good',
                   exceptionMsg="Found DriftScope on your PC. You are good to go.",
                   type="Info")
            return


class DragAndDrop(wx.FileDropTarget):

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
        for filename in filenames:
            print(("Opening {} file...".format(filename)))
            __, file_extension = os.path.splitext(filename)
            if file_extension in ['.raw', '.pickle', '.pkl', '.txt', '.csv', '.tab']:
                try:
                    self.window.onOpenFile_DnD(filename, file_extension)
                except Exception:
                    print(("Failed to open {}".format(filename)))
                    continue
            else:
                print("Dropped file is not supported")
                continue
