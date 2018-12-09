# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas 
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
# 
#	 GitHub : https://github.com/lukasz-migas/ORIGAMI
#	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

# File containing all IDs for functions
from wx import NewId, ID_EXIT, ID_ABOUT

# Common
ID_quit = ID_EXIT
ID_about = ID_ABOUT
ID_SHOW_ABOUT = NewId()
ID_WHATS_NEW = NewId()
ID_CHECK_VERSION = NewId()
ID_RESET_ORIGAMI = NewId()
ID_quickDisplayDocument = NewId()

# Logging window
ID_log_clear_window = NewId()
ID_log_save_log = NewId()
ID_log_go_to_directory = NewId()
ID_extraSettings_logging = NewId()

# Recent documents
ID_documentRecent0 = NewId()
ID_documentRecent1 = NewId()
ID_documentRecent2 = NewId()
ID_documentRecent3 = NewId()
ID_documentRecent4 = NewId()
ID_documentRecent5 = NewId()
ID_documentRecent6 = NewId()
ID_documentRecent7 = NewId()
ID_documentRecent8 = NewId()
ID_documentRecent9 = NewId()

# File menu
ID_fileMenu_openRecent = NewId()
ID_fileMenu_clearRecent = NewId()
ID_fileMenu_MGF = NewId()
ID_fileMenu_mzML = NewId()
ID_fileMenu_mzIdentML = NewId()
ID_fileMenu_thermoRAW = NewId()


# Plots
ID_plots_resetZoom = NewId()
ID_plots_showCursorGrid = NewId()
ID_plots_customisePlot = NewId()
ID_plots_customisePlot_unidec_ms = NewId()
ID_plots_customisePlot_unidec_mw= NewId()
ID_plots_customisePlot_unidec_mz_v_charge = NewId()
ID_plots_customisePlot_unidec_isolated_mz = NewId()
ID_plots_customisePlot_unidec_mw_v_charge = NewId()
ID_plots_customisePlot_unidec_ms_barchart = NewId()
ID_plots_customisePlot_unidec_chargeDist = NewId()
ID_plots_rotate90 = NewId()

ID_plots_saveImage_unidec_ms = NewId()
ID_plots_saveImage_unidec_mw= NewId()
ID_plots_saveImage_unidec_mz_v_charge = NewId()
ID_plots_saveImage_unidec_isolated_mz = NewId()
ID_plots_saveImage_unidec_mw_v_charge = NewId()
ID_plots_saveImage_unidec_ms_barchart = NewId()
ID_plots_saveImage_unidec_chargeDist = NewId() 

# Compare MS 
ID_compareMS_MS_1 = NewId()
ID_compareMS_MS_2 = NewId()

# Interactive settings
ID_interactivePanel_guiMenuTool = NewId()
ID_interactivePanel_table_document = NewId()
ID_interactivePanel_table_type = NewId()
ID_interactivePanel_table_file = NewId()
ID_interactivePanel_table_title = NewId()
ID_interactivePanel_table_header = NewId()
ID_interactivePanel_table_footnote = NewId()
ID_interactivePanel_table_colormap = NewId()
ID_interactivePanel_table_page = NewId()
ID_interactivePanel_table_order = NewId()
ID_interactivePanel_table_hideAll = NewId()
ID_interactivePanel_table_restoreAll = NewId()
ID_interactivePanel_select_item = NewId()
ID_interactivePanel_check_menu = NewId()
ID_interactivePanel_check_all = NewId()
ID_interactivePanel_check_ms = NewId()
ID_interactivePanel_check_dt1D = NewId()
ID_interactivePanel_check_dt2D = NewId()
ID_interactivePanel_check_rt = NewId()
ID_interactivePanel_check_overlay = NewId() 
ID_interactivePanel_check_unidec = NewId()
ID_interactivePanel_check_other = NewId()
ID_interactivePanel_color_markerEdge = NewId()
ID_interactivePanel_color_barEdge = NewId()
ID_interactivePanel_customise_item = NewId()

ID_interactivePanel_copy_all = NewId()
ID_interactivePanel_copy_plot = NewId()
ID_interactivePanel_copy_figure = NewId()
ID_interactivePanel_copy_frame = NewId()
ID_interactivePanel_copy_legend = NewId()
ID_interactivePanel_copy_widgets = NewId()
ID_interactivePanel_copy_annotations = NewId()
ID_interactivePanel_copy_colorbar = NewId()
ID_interactivePanel_copy_tools = NewId()
ID_interactivePanel_copy_overlay = NewId()
ID_interactivePanel_copy_plots = NewId()
ID_interactivePanel_copy_preprocess = NewId()

ID_interactivePanel_apply_all = NewId()
ID_interactivePanel_apply_plot = NewId()
ID_interactivePanel_apply_figure = NewId()
ID_interactivePanel_apply_frame = NewId()
ID_interactivePanel_apply_legend = NewId()
ID_interactivePanel_apply_widgets = NewId()
ID_interactivePanel_apply_annotations = NewId()
ID_interactivePanel_apply_colorbar = NewId()
ID_interactivePanel_apply_tools = NewId()
ID_interactivePanel_apply_overlay = NewId()
ID_interactivePanel_apply_plots = NewId()
ID_interactivePanel_apply_preprocess = NewId()

ID_interactivePanel_apply_batch_all = NewId()
ID_interactivePanel_apply_batch_plot = NewId()
ID_interactivePanel_apply_batch_figure = NewId()
ID_interactivePanel_apply_batch_frame = NewId()
ID_interactivePanel_apply_batch_legend = NewId()
ID_interactivePanel_apply_batch_widgets = NewId()
ID_interactivePanel_apply_batch_annotations = NewId()
ID_interactivePanel_apply_batch_colorbar = NewId()
ID_interactivePanel_apply_batch_tools = NewId()
ID_interactivePanel_apply_batch_overlay = NewId()
ID_interactivePanel_apply_batch_plots = NewId()
ID_interactivePanel_apply_batch_preprocess = NewId()

# Export settings
ID_importExportSettings_image = NewId()
ID_importExportSettings_file = NewId()
ID_importExportSettings_peaklist = NewId()

# Extra settings
ID_extraSettings_autoSaveSettings = NewId()
ID_extraSettings_rmsd = NewId()
ID_extraSettings_waterfall = NewId() 
ID_extraSettings_colorbar = NewId()
ID_extraSettings_violin = NewId()
ID_extraSettings_legend = NewId()
ID_extraSettings_plot1D = NewId()
ID_extraSettings_plot2D = NewId()
ID_extraSettings_plot3D = NewId()
ID_extraSettings_general = NewId()
ID_extraSettings_general_plot = NewId()

ID_extraSettings_lineColor_1D = NewId()
ID_extraSettings_shadeUnderColor_1D = NewId()
ID_extraSettings_markerColor_1D = NewId()
ID_extraSettings_edgeMarkerColor_1D = NewId()
ID_extraSettings_markerColor_3D = NewId()
ID_extraSettings_edgeMarkerColor_3D = NewId()
ID_extraSettings_labelColor_rmsd = NewId()
ID_extraSettings_lineColor_rmsd = NewId()
ID_extraSettings_underlineColor_rmsd = NewId()
ID_extraSettings_lineColour_waterfall = NewId()
ID_extraSettings_zoomCursorColor = NewId()
ID_extraSettings_extractColor = NewId()
ID_extraSettings_horizontalColor = NewId()
ID_extraSettings_verticalColor = NewId()
ID_extraSettings_boxColor = NewId()
ID_extraSettings_lineColour_violin = NewId()
ID_extraSettings_bar_edgeColor = NewId()

ID_extraSettings_instantPlot = NewId()
ID_extraSettings_multiThreading = NewId()
ID_extraSettings_logging = NewId()

# Sequence analysis
ID_sequence_openGUI = NewId()

# Process settings
ID_processSettings_MS = NewId()
ID_processSettings_2D = NewId()
ID_processSettings_ORIGAMI = NewId()
ID_processSettings_FindPeaks = NewId()
ID_processSettings_ExtractData = NewId()
ID_processSettings_replotMS = NewId()
ID_processSettings_processMS = NewId()
ID_processSettings_replot2D = NewId()
ID_processSettings_process2D = NewId()
ID_docTree_plugin_UVPD = NewId() 
ID_docTree_plugin_MSMS = NewId() 
ID_processSettings_restoreIsolatedAll = NewId()


ID_processSettings_UniDec = NewId()
ID_processSettings_preprocessUniDec = NewId()
ID_processSettings_runUniDec = NewId()
ID_processSettings_pickPeaksUniDec = NewId()
ID_processSettings_autoUniDec = NewId()
ID_processSettings_UniDec_info = NewId()
ID_processSettings_loadDataUniDec = NewId()
ID_processSettings_runAll = NewId()
ID_processSettings_replotUniDec = NewId()
ID_processSettings_showZUniDec = NewId()
ID_processSettings_isolateZUniDec = NewId()
ID_processSettings_replotAll = NewId()

# Annotations panel
ID_annotPanel_assignColor_selected = NewId()
ID_annotPanel_assignChargeState_selected = NewId()
ID_annotPanel_deleteSelected_selected = NewId()
ID_annotPanel_addAnnotations = NewId()
ID_annotPanel_assignLabel_selected = NewId()
ID_annotPanel_savePeakList_selected = NewId()
ID_annotPanel_show_charge = NewId() 
ID_annotPanel_show_label = NewId()
ID_annotPanel_show_mzAndIntensity = NewId()
ID_annotPanel_show_labelsAtIntensity = NewId()
ID_annotPanel_show_adjustLabelPosition = NewId()
ID_annotPanel_fixIntensity_selected = NewId()
ID_annotPanel_otherSettings = NewId()

# Tandem panel
ID_tandemPanel_otherSettings = NewId()
ID_tandemPanel_showPTMs = NewId()
ID_tandemPanel_peaklist_show_selected = NewId()

# UVPD panel
ID_uvpd_laser_on_show_heatmap = NewId()
ID_uvpd_laser_on_show_waterfall = NewId()
ID_uvpd_laser_on_show_chromatogram = NewId()
ID_uvpd_laser_on_show_mobiligram = NewId()

ID_uvpd_laser_on_save_heatmap = NewId()
ID_uvpd_laser_on_save_chromatogram = NewId()
ID_uvpd_laser_on_save_mobiligram = NewId()

ID_uvpd_laser_off_show_heatmap = NewId()
ID_uvpd_laser_off_show_waterfall = NewId()
ID_uvpd_laser_off_show_chromatogram = NewId()
ID_uvpd_laser_off_show_mobiligram = NewId()

ID_uvpd_laser_off_save_heatmap = NewId()
ID_uvpd_laser_off_save_chromatogram = NewId()
ID_uvpd_laser_off_save_mobiligram = NewId()



ID_uvpd_laser_on_off_mobiligram_show_chromatogram = NewId()
ID_uvpd_laser_on_off_compare_chromatogam = NewId()
ID_uvpd_laser_on_off_compare_mobiligram = NewId()

ID_uvpd_peaklist_remove = NewId()
ID_uvpd_monitor_remove = NewId()


# Multiple files panel
ID_mmlPanel_assignColor = NewId()
ID_mmlPanel_processTool = NewId()
ID_mmlPanel_overlayWaterfall = NewId()
ID_mmlPanel_annotateTool = NewId()
ID_mmlPanel_changeColorBatch_color = NewId()
ID_mmlPanel_changeColorBatch_palette = NewId()
ID_mmlPanel_changeColorBatch_colormap = NewId()
ID_mmlPanel_preprocess = NewId()
ID_mmlPanel_addToDocument = NewId()
ID_mmlPanel_batchRunUniDec = NewId()
ID_mmlPanel_overlayChargeStates = NewId()
ID_mmlPanel_overlayMW = NewId()
ID_mmlPanel_overlayProcessedSpectra = NewId()
ID_mmlPanel_overlayFittedSpectra = NewId()
ID_mmlPanel_overlayFoundPeaks = NewId()
ID_mmlPanel_showLegend = NewId()
ID_mmlPanel_table_filename = NewId()
ID_mmlPanel_table_variable = NewId()
ID_mmlPanel_table_document = NewId()
ID_mmlPanel_table_label = NewId()
ID_mmlPanel_table_hideAll = NewId()
ID_mmlPanel_table_restoreAll = NewId()
ID_mmlPanel_check_all = NewId()
ID_mmlPanel_check_selected = NewId()
ID_mmlPanel_delete_selected = NewId()
ID_mmlPanel_delete_rightClick = NewId()
ID_mmlPanel_delete_all = NewId()
ID_mmlPanel_clear_selected = NewId()
ID_mmlPanel_clear_all = NewId()
ID_mmlPanel_add_manualDoc = NewId()
ID_mmlPanel_add_files_toNewDoc = NewId()
ID_mmlPanel_add_files_toCurrentDoc = NewId()
ID_mmlPanel_data_combineMS = NewId()
ID_mmlPanel_plot_MS = NewId()
ID_mmlPanel_plot_combined_MS = NewId()
ID_mmlPanel_plot_DT = NewId()


# Ion panel
ID_ionPanel_guiMenuTool = NewId()
ID_ionPanel_assignColor = NewId()
ID_ionPanel_editItem = NewId()
ID_ionPanel_edit_selected = NewId()
ID_ionPanel_edit_all = NewId()
ID_ionPanel_table_startMS = NewId()
ID_ionPanel_table_endMS = NewId()
ID_ionPanel_table_charge = NewId()
ID_ionPanel_table_intensity = NewId()
ID_ionPanel_table_color = NewId()
ID_ionPanel_table_colormap = NewId()
ID_ionPanel_table_alpha = NewId()
ID_ionPanel_table_mask = NewId()
ID_ionPanel_table_label = NewId()
ID_ionPanel_table_method = NewId()
ID_ionPanel_table_document = NewId()
ID_ionPanel_table_hideAll = NewId()
ID_ionPanel_table_restoreAll = NewId()
ID_ionPanel_changeColorBatch_color = NewId()
ID_ionPanel_changeColorBatch_palette = NewId()
ID_ionPanel_changeColorBatch_colormap = NewId()
ID_ionPanel_changeColormapBatch = NewId()
ID_ionPanel_addToDocument = NewId()
ID_ionPanel_normalize1D = NewId()
ID_ionPanel_automaticExtract = NewId()
ID_ionPanel_automaticOverlay = NewId()
ID_ionPanel_show_mobiligram = NewId()
ID_ionPanel_show_chromatogram = NewId()
ID_ionPanel_show_heatmap = NewId()
ID_ionPanel_show_process_heatmap = NewId()
ID_ionPanel_show_zoom_in_MS = NewId()
ID_ionPanel_check_all = NewId()
ID_ionPanel_check_selected = NewId()
ID_ionPanel_delete_selected = NewId()
ID_ionPanel_delete_rightClick = NewId()
ID_ionPanel_delete_all = NewId()
ID_ionPanel_clear_selected = NewId()
ID_ionPanel_clear_all = NewId()

# UniDec panel
ID_unidecPanel_fitLineColor = NewId()
ID_unidecPanel_barEdgeColor = NewId()

# interactive

# Plot panel
ID_plotPanel_binMS = NewId()
ID_plotPanel_lockPlot = NewId()
ID_plotPanel_resize = NewId()

# Main panel
ID_mainPanel_openSourceFiles = NewId()
ID_mainPanel_textFiles = NewId()

# Text panel
ID_textPanel_guiMenuTool = NewId()
ID_textPanel_assignColor = NewId()
ID_textPanel_editItem = NewId()
ID_textPanel_edit_selected = NewId()
ID_textPanel_edit_all = NewId()
ID_textPanel_changeColorBatch_color = NewId()
ID_textPanel_changeColorBatch_palette = NewId()
ID_textPanel_changeColorBatch_colormap = NewId()
ID_textPanel_changeColormapBatch = NewId()
ID_textPanel_table_startCE = NewId()
ID_textPanel_table_endCE = NewId()
ID_textPanel_table_charge = NewId()
ID_textPanel_table_color = NewId()
ID_textPanel_table_colormap = NewId()
ID_textPanel_table_alpha = NewId()
ID_textPanel_table_mask = NewId()
ID_textPanel_table_label = NewId()
ID_textPanel_table_shape = NewId()
ID_textPanel_table_document = NewId()
ID_textPanel_table_hideAll = NewId()
ID_textPanel_table_restoreAll = NewId()
ID_textPanel_addToDocument = NewId()
ID_textPanel_normalize1D = NewId()
ID_textPanel_automaticOverlay = NewId()
ID_textPanel_show_mobiligram = NewId()
ID_textPanel_show_chromatogram = NewId()
ID_textPanel_show_heatmap = NewId()
ID_textPanel_show_process_heatmap = NewId()
ID_textPanel_check_all = NewId()
ID_textPanel_check_selected = NewId()
ID_textPanel_delete_selected = NewId()
ID_textPanel_delete_rightClick = NewId()
ID_textPanel_delete_all = NewId()
ID_textPanel_clear_selected = NewId()
ID_textPanel_clear_all = NewId()

# Document tree
ID_docTree_compareMS = NewId()
ID_docTree_showMassSpectra = NewId()
ID_docTree_processMS = NewId()
ID_docTree_process2D = NewId()
ID_docTree_extractDTMS = NewId()
ID_docTree_UniDec = NewId()
ID_docTree_addToMMLTable = NewId()
ID_docTree_addOneToMMLTable = NewId()
ID_docTree_addToTextTable = NewId()
ID_docTree_addOneToTextTable = NewId()
ID_docTree_addInteractiveToTextTable = NewId()
ID_docTree_addOneInteractiveToTextTable = NewId()
ID_docTree_add_annotations = NewId()
ID_docTree_show_annotations = NewId()
ID_docTree_load_annotations = NewId()
ID_docTree_duplicate_annotations = NewId()
ID_docTree_show_unidec = NewId()
ID_docTree_save_unidec = NewId()
ID_docTree_duplicate_document = NewId()
ID_docTree_show_refresh_document = NewId()

ID_docTree_add_MS_to_interactive = NewId()
ID_docTree_add_RT_to_interactive = NewId()
ID_docTree_add_DT_to_interactive = NewId()
ID_docTree_add_2DT_to_interactive = NewId()
ID_docTree_add_other_to_interactive = NewId()
ID_docTree_add_matrix_to_interactive = NewId()
ID_docTree_add_comparison_to_interactive = NewId()

ID_docTree_add_mzIdentML = NewId()

ID_docTree_batch_x_2D_custom = NewId()
ID_docTree_batch_x_2D_scans = NewId()
ID_docTree_batch_x_2D_colVolt = NewId()
ID_docTree_batch_x_2D_actVolt = NewId()
ID_docTree_batch_x_2D_labFrame = NewId()
ID_docTree_batch_x_2D_actlabFrame = NewId()
ID_docTree_batch_x_2D_massToCharge = NewId()
ID_docTree_batch_x_2D_mz = NewId()
ID_docTree_batch_x_2D_wavenumber = NewId()
ID_docTree_batch_x_2D_charge = NewId()
ID_docTree_batch_x_2D_ccs = NewId()
ID_docTree_batch_MS_MSda = NewId()
ID_docTree_batch_MS_kda = NewId()
ID_docTree_batch_y_2D_custom = NewId()
ID_docTree_batch_y_2D_bins = NewId()
ID_docTree_batch_y_2D_ms = NewId()
ID_docTree_batch_y_2D_ms_arrival = NewId()
ID_docTree_batch_y_2D_ccs = NewId()

ID_saveData_csv = NewId()
ID_saveData_pickle = NewId()
ID_saveData_excel = NewId()
ID_saveData_hdf = NewId()

# Menu
ID_window_all = NewId()
ID_window_documentList = NewId()
ID_window_controls = NewId()
ID_window_ccsList = NewId()
ID_window_ionList = NewId()
ID_window_multipleMLList = NewId()
ID_window_textList = NewId()
ID_window_multiFieldList = NewId()
ID_window_logWindow = NewId()

# Toolbar
ID_toolbar_top = NewId()
ID_toolbar_bottom = NewId()
ID_toolbar_left = NewId()
ID_toolbar_right = NewId()

ID_helpGuideLocal = NewId()

ID_saveAllDocuments = NewId()
ID_selectCalibrant = NewId()
ID_selectProtein = NewId()
ID_renameItem = NewId()
ID_duplicateItem = NewId()
ID_windowMinimize = NewId()
ID_windowMaximize = NewId()
ID_windowFullscreen = NewId()
ID_assignChargeStateIons = NewId()
ID_assignAlphaIons = NewId()
ID_assignMaskIons = NewId()
ID_assignMinThresholdIons = NewId()
ID_assignMaxThresholdIons = NewId()

ID_clearPlot_MZDT = NewId()
ID_saveMZDTImage = NewId()
ID_assignToolsSelected_HTML = NewId()
ID_assignColormapSelected_HTML = NewId()

ID_openMassLynxFile = NewId()

ID_OnOff_ccsView = NewId()
ID_OnOff_dtView = NewId()
ID_OnOff_textView = NewId()
ID_OnOff_mlynxView = NewId()
ID_OnOff_ionView = NewId()
ID_OnOff_settingsView = NewId()
ID_OnOff_docView = NewId()

# Config Menu 
ID_saveConfig = NewId()
ID_saveAsConfig = NewId()
ID_openConfig = NewId()
ID_openAsConfig = NewId()
ID_setDriftScopeDir = NewId()
ID_check_Driftscope = NewId() 
ID_checkAtStart_Driftscope = NewId()
ID_openDocInfo = NewId()
ID_importAtStart_CCS = NewId()

ID_restoreComparisonData = NewId()

ID_documentInfoSummary = NewId()
ID_documentInfoSpectrum = NewId()
ID_documentInfoNotes = NewId()
ID_documentInfoPlotIMS = NewId()
ID_documentInfoCalibration = NewId()
ID_assignChargeState = NewId()

ID_saveImageDocument = NewId()

ID_saveDataCSVDocument1D = NewId()
ID_assignChargeStateText = NewId()
ID_assignAlphaText = NewId()
ID_assignMaskText = NewId()
ID_assignMinThresholdText = NewId()
ID_assignMaxThresholdText = NewId()

ID_saveRMSDmatrixImage = NewId()
ID_annotateTextFilesMenu = NewId()

# INTERACTIVE
ID_changeColorInteractive = NewId()
ID_changeColormapInteractive = NewId()
ID_combineCEscansSelectedIons = NewId()
ID_pickMSpeaksDocument = NewId()
ID_removeDuplicatesTable = NewId()
ID_highlightRectAllIons = NewId()
ID_smooth1DdataMS = NewId()
ID_smooth1DdataRT = NewId()
ID_smooth1Ddata1DT = NewId()
ID_useInternalParamsCombinedMenu = NewId()
ID_useProcessedCombinedMenu = NewId()
ID_combinedCV_binMSCombinedMenu = NewId()
ID_clearAllPlots = NewId()
ID_clearPlot_MS = NewId()
ID_clearPlot_RT = NewId()
ID_clearPlot_RT_MS = NewId()
ID_clearPlot_1D = NewId()
ID_clearPlot_1D_MS = NewId()
ID_clearPlot_2D = NewId()
ID_clearPlot_3D = NewId()
ID_clearPlot_Waterfall = NewId()
ID_clearPlot_Matrix = NewId()
ID_clearPlot_Watefall = NewId()
ID_clearPlot_Calibration = NewId()
ID_clearPlot_Overlay = NewId()
ID_clearPlot_RMSF = NewId()
ID_clearPlot_RMSD = NewId()
ID_clearPlot_UniDec_all = NewId()
ID_clearPlot_UniDec_MS = NewId()
ID_clearPlot_UniDec_mwDistribution = NewId()
ID_clearPlot_UniDec_mzGrid = NewId()
ID_clearPlot_UniDec_mwGrid = NewId()
ID_clearPlot_UniDec_pickedPeaks = NewId()
ID_clearPlot_UniDec_barchart = NewId()
ID_clearPlot_UniDec_chargeDistribution = NewId()
ID_clearPlot_other = NewId()

ID_saveUniDecAll = NewId()

ID_duplicateIons = NewId()

ID_addNewOverlayDoc = NewId()
ID_addNewInteractiveDoc = NewId()
ID_addNewManualDoc = NewId()

ID_clearSelectedDT = NewId()
ID_clearTableDT = NewId()
ID_removeAllFilesDT = NewId()
ID_removeSelectedFileDT = NewId()
ID_removeSelectedPopupDT = NewId()
ID_removeFilesMenuDT = NewId()

ID_addFilesMenuDT = NewId()
ID_addIonListDT = NewId()

ID_saveFilesMenuDT = NewId()
ID_saveIonListDT = NewId()
ID_saveAllIon1D_DT = NewId()
ID_saveSelectedIon1D_DT = NewId()

ID_removeFilesMenuDT_RT = NewId()
ID_removeSelectedPopupDT_RT = NewId()
ID_removeSelectedFileDT_RT = NewId()
ID_removeAllFilesDT_RT = NewId()
ID_clearTableDT_RT = NewId()


#===============================================================================
# # DocumentTree
#===============================================================================
# PLOT
ID_saveDocument = NewId()

ID_showIonsMenu = NewId()
ID_showAllIons = NewId()
ID_showSelectedIons = NewId()

ID_addIonsMenu = NewId()
ID_addOneIon = NewId()
ID_addManyIonsCSV = NewId()

ID_removeDocument = NewId()
ID_removeAllDocuments = NewId()
ID_removeIonsMenu = NewId()

ID_extractNewIon = NewId()
ID_extractSelectedIon = NewId()
ID_extractAllIons = NewId()
ID_extractIonsMenu  = NewId()

ID_combineCEscans = NewId()
ID_processSelectedIons = NewId()
ID_processAllIons = NewId()
ID_processIonsMenu = NewId()

ID_saveIonsMenu = NewId()
ID_saveIonListCSV = NewId()
ID_saveSelectIonListCSV = NewId()

ID_openDocument = NewId()
ID_showPlotDocument = NewId()
ID_showPlotDocument_violin = NewId()
ID_showPlotDocument_waterfall = NewId()
ID_showPlot1DDocument = NewId()
ID_showPlotMSDocument = NewId()
ID_saveAsInteractive = NewId()
ID_showSampleInfo = NewId()
ID_getSelectedDocument = NewId()
ID_showDeconvolutionResults = NewId()

ID_addFilesMenu = NewId()
ID_removeFilesMenu = NewId()
ID_overlayFilesMenu = NewId()

ID_save1DAllFiles = NewId()
ID_saveMSAllFiles = NewId()
ID_ExportWindowFiles = NewId()
ID_saveFilesMenu = NewId()

ID_convertSelectedAxisFiles = NewId()
ID_convertAxisFilesPopup = NewId()
ID_convertAllAxisFiles = NewId()

# SAVE
ID_saveDataCSVDocument = NewId()
ID_saveAsDataCSVDocument = NewId()
ID_saveAsDataCSVDocument1D = NewId()

ID_save2DhtmlDocument = NewId()
ID_save2DhtmlDocumentImage = NewId()
ID_save2DhtmlDocumentHeatmap = NewId()

# OTHER
ID_getNewColour = NewId()
ID_process2DDocument = NewId()
ID_add2CCStable1DDocument = NewId()
ID_add2CCStable2DDocument = NewId()

ID_goToDirectory = NewId()

# Styles
ID_xlabel_2D_custom = NewId()
ID_xlabel_2D_scans = NewId()
ID_xlabel_2D_time_min = NewId()
ID_xlabel_2D_retTime_min = NewId()
ID_xlabel_2D_colVolt = NewId()
ID_xlabel_2D_actVolt = NewId()
ID_xlabel_2D_labFrame = NewId()
ID_xlabel_2D_actLabFrame = NewId()
ID_xlabel_2D_massToCharge = NewId()
ID_xlabel_2D_mz = NewId()
ID_xlabel_2D_wavenumber = NewId()
ID_xlabel_2D_charge = NewId()
ID_xlabel_2D_ccs = NewId()
ID_xlabel_2D_restore = NewId()

ID_ylabel_2D_custom = NewId()
ID_ylabel_2D_bins = NewId()
ID_ylabel_2D_ms = NewId()
ID_ylabel_2D_ms_arrival = NewId()
ID_ylabel_2D_ccs = NewId()
ID_ylabel_2D_restore = NewId()

ID_xlabel_MS_da = NewId()
ID_xlabel_MS_kda = NewId()

ID_xlabel_1D_custom = NewId()
ID_xlabel_1D_bins = NewId()
ID_xlabel_1D_ms = NewId()
ID_xlabel_1D_ms_arrival = NewId()
ID_xlabel_1D_ccs = NewId()
ID_xlabel_1D_restore = NewId()

ID_ylabel_DTMS_bins = NewId()
ID_ylabel_DTMS_ms = NewId()
ID_ylabel_DTMS_ms_arrival = NewId()
ID_ylabel_DTMS_restore = NewId()

ID_xlabel_RT_scans = NewId()
ID_xlabel_RT_time_min = NewId()
ID_xlabel_RT_retTime_min = NewId()
ID_xlabel_RT_restore = NewId()

#===============================================================================
# # File Menu
#===============================================================================
# From MassLynx file
ID_openMSFile = NewId()
ID_open1DIMSFile = NewId()
ID_open2DIMSFile = NewId()
#===============================================================================
# # From binary file
#===============================================================================
ID_openMSbinFile = NewId()
ID_open1DbinFile = NewId()
ID_open2DbinFile = NewId()
#===============================================================================
# # Other
#===============================================================================
ID_openORIGAMIRawFile = NewId()
ID_openMassLynxRawFile = NewId()
ID_openLinearDTRawFile = NewId()
ID_openRawFile = NewId()
ID_openMStxtFile = NewId()
ID_openIMStxtFile = NewId()

#===============================================================================
# # Save
#===============================================================================
ID_save2D = NewId()

#===============================================================================
# # Save images
#===============================================================================

ID_saveMSImage = NewId()
ID_saveRTImage = NewId()
ID_save1DImage = NewId()
ID_save2DImage = NewId()
ID_save3DImage = NewId()
ID_saveRMSDImage = NewId()
ID_saveRMSFImage = NewId()
ID_saveOverlayImage = NewId()
ID_saveWaterfallImage = NewId()
ID_saveRMSDmatrixImage = NewId()
ID_saveOtherImage = NewId()
ID_saveCompareMSImage = NewId()

ID_saveAllImages = NewId()
ID_saveFiguresAs = NewId()

ID_saveMSImageDoc = NewId()
ID_saveRTImageDoc = NewId()
ID_save1DImageDoc = NewId()
ID_save2DImageDoc = NewId()
ID_save3DImageDoc = NewId()
ID_saveRMSDImageDoc = NewId()
ID_saveRMSFImageDoc = NewId()
ID_saveOverlayImageDoc = NewId()
ID_saveWaterfallImageDoc = NewId()
ID_saveRMSDmatrixImageDoc = NewId()
ID_saveMZDTImageDoc = NewId()
ID_saveOtherImageDoc = NewId()

#===============================================================================
# # Right panel toolbar (multiple ions)
#===============================================================================
ID_processIons = NewId()
ID_overlayMZfromList = NewId()
ID_saveMZList = NewId()
ID_selectOverlayMethod = NewId()
ID_removeAllMZfromList = NewId()

#===============================================================================
# # Right panel toolbar (multiple text files)
#===============================================================================
ID_openTextFiles = NewId()
ID_getSpectrumFromClipboard = NewId()
ID_openTextFilesMenu = NewId()
ID_addTextFilesToList = NewId()
ID_processTextFiles = NewId()
ID_textSelectOverlayMethod = NewId()
ID_overlayTextFromList = NewId()
ID_removeTextFilesMenu = NewId()
ID_processTextFilesMenu = NewId()
ID_processAllTextFiles = NewId()
ID_overlayTextFilesMenu = NewId()
ID_overlayTextfromList1D = NewId()
ID_overlayTextfromListRT = NewId()
ID_overlayTextfromListWaterfall = NewId()
#===============================================================================
# # Right panel context menu (multiple text files)
#===============================================================================
ID_changeColorNotationInteractive = NewId()
ID_changeColorBackgroundNotationInteractive = NewId()
ID_changeColorGridLabelInteractive = NewId()
ID_changeColorAnnotLabelInteractive = NewId()
ID_changeColorGridLineInteractive = NewId()
ID_changeColorBackgroundInteractive = NewId()


ID_addPage_HTML = NewId()
ID_helpAuthor = NewId()
ID_helpHomepage = NewId()
ID_helpGitHub = NewId()
ID_helpCite = NewId()
ID_helpNewVersion = NewId()
ID_helpYoutube = NewId()
ID_helpGuide = NewId()
ID_helpHTMLEditor = NewId()
ID_helpNewFeatures = NewId()
ID_helpReportBugs = NewId()
ID_help_UniDecInfo = NewId()

ID_help_page_dataLoading = NewId()
ID_help_page_gettingStarted = NewId()
ID_help_page_UniDec = NewId()
ID_help_page_ORIGAMI = NewId()
ID_help_page_overlay = NewId()
ID_help_page_multipleFiles = NewId()
ID_help_page_linearDT = NewId()
ID_help_page_CCScalibration = NewId()
ID_help_page_dataExtraction = NewId()
ID_help_page_Interactive = NewId()
ID_help_page_OtherData = NewId()
ID_help_page_annotatingMassSpectra = NewId()

ID_assignPage_HTML = NewId()
ID_assignPageSelected_HTML = NewId()

ID_extractMSforCVs = NewId()
ID_showPlotRTDocument = NewId()
ID_openIRTextile = NewId()
ID_openIRRawFile = NewId()

ID_overlayMZfromList1D = NewId()
ID_overlayMZfromListRT = NewId()
ID_overlayIonsMenu = NewId()
ID_removeItemDocument = NewId()
ID_recalculateORIGAMI = NewId()
ID_processSaveMenu = NewId()
ID_exportAllAsCSV_ion = NewId()
ID_exportAllAsImage_ion = NewId()
ID_exportSelectedAsCSV_ion = NewId()
ID_exportSeletedAsImage_ion = NewId()

#===============================================================================
# # Right panel toolbar (multiple MassLynx files)
#===============================================================================
ID_openMultipleORIGAMIRawFiles = NewId()
ID_combineMassLynxFiles = NewId()
ID_openMassLynxFiles = NewId()
#===============================================================================
# # Right panel toolbar (multifield MassLynx linear file)
#===============================================================================
ID_extractDriftVoltagesForEachIon = NewId()

#===============================================================================
# # Right panel toolbar (CCS calibration)
#===============================================================================
# ADD
ID_checkAllItems_caliMS = NewId()
ID_clearTableCaliMS = NewId()
ID_calibration_changeTD = NewId()
ID_calibrationPlot1D = NewId()
ID_showHideListCCSMenu = NewId()
ID_addNewCalibrationDoc = NewId()
ID_overrideCombinedMenu = NewId()
ID_changeParams_multiIon = NewId()

ID_checkAllItems_caliApply = NewId()

ID_addCCScalibrantMenu = NewId()
ID_addCCScalibrantFile = NewId()
ID_addCCScalibrantFiles = NewId()
ID_addCCScalibrantFilelist = NewId()
ID_openCCScalibration = NewId()
ID_openCCScalibrationDatabse = NewId()

# REMOVE
ID_saveDataCCSCalibrantDocument = NewId()
ID_removeCCScalibrantMenu = NewId()
ID_removeCCScalibrantFile = NewId()
ID_removeCCScalibrantFiles = NewId()

ID_removeCCScalibrantBottomPanel = NewId()
ID_removeCCScalibrantBottomPanelPopup = NewId()
ID_removeApplyCCScalibrantMenu = NewId()
# SAVE
ID_saveCCScalibrantMenu = NewId()
ID_saveCCScalibrantFilelist = NewId()
ID_saveCCScalibration = NewId()
ID_saveCCScalibrationCSV = NewId()
# EXTRACT
ID_extractCCScalibrantMenu = NewId()
ID_extractCCScalibrantSelected = NewId()
ID_extractCCScalibrantAll = NewId()
# PROCESS
ID_buildCalibrationDataset = NewId()
ID_processCCScalibrantMenu = NewId()

ID_showHidePanelCCSMenu = NewId()

ID_calibranteCCScalibrant = NewId()
ID_prepareCCSCalibrant = NewId()
ID_prepare2DCCSCalibrant = NewId()
ID_calibranteCCScalibrant = NewId()

ID_applyCalibrationOnDataset = NewId()
ID_buildApplyCalibrationDataset = NewId()
ID_detectMZpeaksApplyCCScalibrant = NewId()
ID_detectATDpeaksApplyCCScalibrant = NewId()
ID_processApplyCCScalibrantMenu = NewId()

# PLOT
ID_plotCCScalibrationMenu = NewId()

# MENU
ID_removeItemCCSCalibrantPopup = NewId()
