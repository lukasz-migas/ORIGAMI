# File containing all IDs for functions

from wx import NewId, ID_EXIT, ID_ABOUT

# Common
ID_quit = ID_EXIT
ID_about = ID_ABOUT
ID_quickDisplayDocument = NewId()

ID_helpGuideLocal = NewId()

ID_saveAllDocuments = NewId()
ID_selectCalibrant = NewId()
ID_selectProtein = NewId()
ID_renameItem = NewId()
ID_windowMinimize = NewId()
ID_windowMaximize = NewId()
ID_assignChargeStateIons = NewId()
ID_assignAlphaMaskIons = NewId()
ID_clearPlot_MZDT = NewId()
ID_saveMZDTImage = NewId()
ID_assignToolsSelected_HTML = NewId()

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
ID_openDocInfo = NewId()

ID_restoreComparisonData = NewId()

ID_documentInfoSummary = NewId()
ID_documentInfoSpectrum = NewId()
ID_documentInfoNotes = NewId()
ID_documentInfoPlotIMS = NewId()
ID_documentInfoCalibration = NewId()
ID_assignChargeState = NewId()

ID_saveImageDocument = NewId()
ID_saveAsImageDocument = NewId()

ID_saveDataCSVDocument1D = NewId()
ID_clearTableText = NewId()
ID_saveRMSDmatrixImage = NewId()



# INTERACTIVE
ID_changeColorInteractive = NewId()
ID_changeColormapInteractive = NewId()
ID_combineCEscansSelectedIons = NewId()
ID_removeFileFromListPopup = NewId() # text
ID_showMSplotIon = NewId()
ID_reBinMSmanual = NewId()
ID_pickMSpeaksDocument = NewId()
ID_clearTableMML = NewId()
ID_clearTableIons = NewId()
ID_removeDuplicatesTable = NewId()
ID_highlightRectAllIons = NewId()
ID_smooth1DdataMS = NewId()
ID_smooth1DdataRT = NewId()
ID_smooth1Ddata1DT = NewId()
ID_useInternalParamsCombinedMenu = NewId()
ID_clearAllPlots = NewId()
ID_clearPlot_MS = NewId()
ID_clearPlot_RT = NewId()
ID_clearPlot_1D = NewId()
ID_clearPlot_2D = NewId()
ID_clearPlot_3D = NewId()
ID_clearPlot_Waterfall = NewId()

ID_clearPlot_Matrix = NewId()
ID_clearPlot_Watefall = NewId()
ID_clearPlot_Calibration = NewId()
ID_clearPlot_Overlay = NewId()
ID_clearPlot_RMSF = NewId()
ID_clearPlot_RMSD = NewId()

ID_duplicateIons = NewId()
ID_checkAllItems_MML = NewId()
ID_checkAllItems_Text = NewId()
ID_checkAllItems_Ions = NewId()


ID_addNewOverlayDoc = NewId()

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
ID_get1DplotIon = NewId()

ID_showIonsMenu = NewId()
ID_showAllIons = NewId()
ID_showSelectedIons = NewId()

ID_addIonsMenu = NewId()
ID_addOneIon = NewId()
ID_addManyIonsCSV = NewId()

ID_RESET_PLOT_ZOOM = NewId()
ID_removeDocument = NewId()
ID_removeAllDocuments = NewId()
ID_removeIonsMenu = NewId()
ID_removeSelectedIon = NewId()
ID_removeAllIons = NewId()
ID_removeSelectedIonPopup = NewId() 

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
ID_showPlot1DDocument = NewId()
ID_showPlotMSDocument = NewId()
ID_saveAsInteractive = NewId()
ID_showSampleInfo = NewId()
ID_getSelectedDocument = NewId()

ID_removeSelectedFile = NewId()
ID_removeSelectedFilePopup = NewId()
ID_removeAllFiles = NewId()
ID_removeFilesMenu = NewId()

ID_save1DAllFiles = NewId()
ID_saveMSAllFiles = NewId()
ID_ExportWindowFiles = NewId()
ID_saveFilesMenu = NewId()

ID_convertSelectedAxisFiles = NewId()
ID_convertAxisFilesPopup = NewId()
ID_convertAllAxisFiles = NewId()

ID_processFilesMenu = NewId()

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
ID_xlabel2Dscans = NewId()
ID_xlabel2DcolVolt = NewId()
ID_xlabel2DlabFrame = NewId()
ID_xlabel2DmassToCharge = NewId()
ID_xlabel2Dmz = NewId()
ID_xlabel2Dwavenumber = NewId()
ID_xlabel2Drestore = NewId()

ID_ylabel2Dbins = NewId()
ID_ylabel2Dms = NewId()
ID_ylabel2Dccs = NewId()
ID_ylabel2Drestore = NewId()

ID_ylabel1Dbins = NewId()
ID_ylabel1Dms = NewId()
ID_ylabel1Dccs = NewId()


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

#===============================================================================
# # Save Bokeh
#===============================================================================
ID_saveBokehTest = NewId()
ID_save2DBokeh2D = NewId()

#===============================================================================
# # Process
#===============================================================================
ID_extractSingleIon = NewId()
ID_combineSingleIon = NewId()
ID_extractMultipleIon = NewId()
ID_combineMultipleIon = NewId()
ID_normalizeMS = NewId()
ID_normalizeIMS = NewId()


#===============================================================================
# # Config Menu
#===============================================================================
# ID_openConfig = NewId()
# ID_saveConfig = NewId()
# ID_saveAsConfig = NewId()

#===============================================================================
# # Centre panel context menu
#===============================================================================
ID_smoothMS = NewId()
ID_annotateMSpeak = NewId()
ID_addCurrentMZtoTable = NewId()
ID_extractCurrentMZ = NewId()
ID_extractCurrent1DT = NewId()
ID_extractCurrentRTDT = NewId()


#===============================================================================
# # Right panel toolbar (multiple ions)
#===============================================================================
ID_openMZList = NewId()
ID_addMZtoList = NewId()
ID_removeMZfromList = NewId()
ID_extractMZfromList = NewId()
ID_combineCEforMZfromList = NewId()
ID_processIons = NewId()
ID_plotMZfromList = NewId()
ID_overlayMZfromList = NewId()
ID_saveMZList = NewId()
ID_selectOverlayMethod = NewId()
ID_removeAllMZfromList = NewId()
#===============================================================================
# # Right panel contect menu (multiple ions)
#===============================================================================
ID_get2DplotIon = NewId()
ID_getDeleteIonItem = NewId()
ID_get2DplotIonWithProcss = NewId()

#===============================================================================
# # Right panel toolbar (multiple text files)
#===============================================================================
ID_openTextFiles = NewId()
ID_openTextFilesMenu = NewId()
ID_addTextFilesToList = NewId()
ID_removeTextFilesFromList = NewId()
ID_processTextFiles = NewId()
ID_plotSelectedTextFile = NewId()
ID_textSelectOverlayMethod = NewId()
ID_overlayTextFromList = NewId()
ID_removeSelectedFilesFromList = NewId()
ID_removeAllFilesFromList = NewId()
ID_removeTextFilesMenu = NewId()
ID_processTextFilesMenu = NewId()
ID_processAllTextFiles = NewId()
ID_saveFileList = NewId()
#===============================================================================
# # Right panel context menu (multiple text files)
#===============================================================================
ID_get2DplotText = NewId()
ID_get2DplotTextWithProcss = NewId()
ID_getDeleteTextItem = NewId()
ID_checkAllItems_HTML = NewId()
ID_changeColorNotationInteractive = NewId()
ID_changeColorBackgroundNotationInteractive = NewId()

ID_addPage_HTML = NewId()
ID_helpHomepage = NewId()
ID_helpGitHub = NewId()
ID_helpCite = NewId()
ID_helpNewVersion = NewId()
ID_helpYoutube = NewId()
ID_helpGuide = NewId()
ID_helpHTMLEditor = NewId()

ID_assignPage_HTML = NewId()
ID_assignPageSelected_HTML = NewId()

ID_extractMSforCVs = NewId()
ID_showPlotRTDocument = NewId()
ID_SHOW_ABOUT = NewId()
ID_RESET_ORIGAMI = NewId()
ID_openIRTextile = NewId()
ID_openIRRawFile = NewId()
ID_changePageForItem = NewId()

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
ID_openMassLynxFiles = NewId()
ID_openMassLynxFilesAsMultiple = NewId()
ID_openMultipleORIGAMIRawFiles = NewId()
ID_addMassLynxFilesToList = NewId()
ID_removeMassLynxFilesFromList = NewId()
ID_combineMassLynxFiles = NewId()
ID_plotSelectedMassLynxFile = NewId()
ID_saveMassLynxFileList = NewId()
ID_removeAllMLFilesFromList = NewId()
ID_massLynxInfo = NewId()
#===============================================================================
# # Right panel contect menu (multiple MassLynx files)
#===============================================================================
ID_getMassSpectrum = NewId()
ID_get1DmobilitySpectrum = NewId()
ID_getDeleteMLItem = NewId()
ID_getCombinedMassSpectrum = NewId()

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

ID_detectMZpeaksCCScalibrant = NewId()
ID_detectATDpeaksCCScalibrant = NewId()
ID_fitGaussiansCCScalibrant = NewId() 
ID_deconvoluteMSccsCalibrant = NewId()
ID_calibranteCCScalibrant = NewId()
ID_prepareCCSCalibrant = NewId()
ID_prepare2DCCSCalibrant = NewId()
ID_calibranteCCScalibrant = NewId()
ID_applyCCScalibrant = NewId()

ID_applyCalibrationOnDataset = NewId()
ID_buildApplyCalibrationDataset = NewId()
ID_detectMZpeaksApplyCCScalibrant = NewId()
ID_detectATDpeaksApplyCCScalibrant = NewId()
ID_processApplyCCScalibrantMenu = NewId()

# PLOT
ID_plotCCScalibrationMenu = NewId()

# MENU
ID_smooth1DCCScalibrantPopup = NewId() 
ID_setProteinCCSCalibrantPopup = NewId() 
ID_removeItemCCSCalibrantPopup = NewId()
