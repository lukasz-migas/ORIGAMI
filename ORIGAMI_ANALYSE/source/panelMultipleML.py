# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017 Lukasz G. Migas <lukasz.migas@manchester.ac.uk>
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

import wx
from styles import makeTooltip, makeMenuItem
from ids import *
import wx.lib.mixins.listctrl  as  listmix
import dialogs as dialogs
from toolbox import str2num, str2int, removeListDuplicates, convertRGB255to1, convertRGB1to255, isempty, mlen
from operator import itemgetter
from wx import ID_ANY
import numpy as np
from os.path import splitext
from scipy.interpolate import interp1d

"""
Panel to load and combine multiple ML files
"""

class panelMML( wx.Panel ):
    
    def __init__( self, parent, config, icons,  presenter ):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, 
                            size = wx.Size( 300,600 ), style = wx.TAB_TRAVERSAL )

        self.parent = parent
        self.config = config
        self.presenter = presenter
        self.icons = icons
               
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.topP = topPanel(self, self.icons, self.presenter, self.config)
        sizer.Add(self.topP, 1, wx.EXPAND | wx.ALL, 1)
        self.SetSizer(sizer)           
        
    def __del__( self ):
         pass
     
class DragAndDrop(wx.FileDropTarget):
    
    #----------------------------------------------------------------------
    def __init__(self, window):
        """Constructor"""
        wx.FileDropTarget.__init__(self)
        self.window = window

    #----------------------------------------------------------------------
    def OnDropFiles(self, x, y, filenames):
        """
        When files are dropped, write where they were dropped and then
        the file paths themselves
        """
        pathlist = []
        for filename in filenames:
            
            __, file_extension = splitext(filename)
            if file_extension in ['.raw']:
                print("Added {} file to the list".format(filename))
                pathlist.append(filename)
            else:
                print("Dropped file {} is not supported".format(filename))
                
        if len(pathlist) > 0:
            self.window.onOpenFile_DnD(pathlist)
                      
class EditableListCtrl(wx.ListCtrl, listmix.TextEditMixin, listmix.CheckListCtrlMixin,
                       listmix.ColumnSorterMixin):
    """
    Editable list
    """
    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0): 
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.TextEditMixin.__init__(self)
        listmix.CheckListCtrlMixin.__init__(self)

        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginLabelEdit)

    def OnBeginLabelEdit(self, event):
        # Block any attempts to change columns 0 and 1
        if event.m_col == 0 or event.m_col == 2:
            event.Veto()
        else:
            event.Skip()

class topPanel(wx.Panel):
    def __init__(self, parent, icons,  presenter, config):
        wx.Panel.__init__(self, parent=parent)
        self.icons = icons
        self.config = config
        self.presenter = presenter # wx.App
        self.makeToolbar()
        self.makeListCtrl()
        self.currentItem = None
        self.currentXlabels = 'bins'
        self.allChecked = True
        self.preprocessMS = False
        self.showLegend = True
        self.addToDocument = False
        
        panelSizer = wx.BoxSizer( wx.VERTICAL )
        panelSizer.Add(self.toolbar, 0, wx.EXPAND, 0)
        panelSizer.Add(self.filelist, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer( panelSizer )

        self.reverse = False
        self.lastColumn = None
        
        file_drop_target = DragAndDrop(self)
        self.SetDropTarget(file_drop_target)
        
        # add a couple of accelerators
        accelerators = [
            (wx.ACCEL_NORMAL, ord('C'), ID_mmlPanel_assignColor),
            (wx.ACCEL_NORMAL, ord('M'), ID_getMassSpectrum),
            (wx.ACCEL_NORMAL, ord('D'), ID_get1DmobilitySpectrum),
            (wx.ACCEL_NORMAL, ord('X'), ID_checkAllItems_MML),
            (wx.ACCEL_NORMAL, ord('S'), ID_checkItem_MML),
            ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))
         
        wx.EVT_MENU(self, ID_mmlPanel_assignColor, self.OnAssignColor)
        wx.EVT_MENU(self, ID_getMassSpectrum, self.OnListGetMS)
        wx.EVT_MENU(self, ID_get1DmobilitySpectrum, self.OnListGet1DT)
        wx.EVT_MENU(self, ID_checkAllItems_MML, self.OnCheckAllItems)
        wx.EVT_MENU(self, ID_checkItem_MML, self.onItemCheck)
        
    def onItemCheck(self, evt):
        check = not self.filelist.IsChecked(index=self.currentItem)
        self.filelist.CheckItem(self.currentItem, check)
        
    def makeListCtrl(self):
        
        # init table
        self.filelist = EditableListCtrl(self, style=wx.LC_REPORT|wx.LC_VRULES)
        for item in self.config._multipleFilesSettings:
            order = item['order']
            name = item['name']
            if item['show']: 
                width = item['width']
            else: 
                width = 0
            self.filelist.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_LEFT)

        filelistTooltip = makeTooltip(delay=3000, reshow=3000, 
                                      text="""List of files and their respective energy values. This panel is relatively universal and can be used for aIMMS, CIU, SID or any other activation technique where energy was increased for separate files.""")
        self.filelist.SetToolTip(filelistTooltip)
        
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickMenu)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.onStartEditingItem)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.onFinishEditingItem)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)

    def onItemSelected(self, evt):
        self.currentItem = evt.m_itemIndex
    
    def onStartEditingItem(self, evt):
        self.currentItem = evt.m_itemIndex
        
        # unbind shortcuts
        self.SetAcceleratorTable(wx.AcceleratorTable([]))
        
    def _updateTable(self):
        self.onUpdateDocument(None)
        
    def onFinishEditingItem(self, evt):
        wx.CallAfter(self._updateTable)
        
        # bind events
        accelerators = [
            (wx.ACCEL_NORMAL, ord('C'), ID_mmlPanel_assignColor),
            (wx.ACCEL_NORMAL, ord('M'), ID_getMassSpectrum),
            (wx.ACCEL_NORMAL, ord('D'), ID_get1DmobilitySpectrum),
            (wx.ACCEL_NORMAL, ord('X'), ID_checkAllItems_MML),
            (wx.ACCEL_NORMAL, ord('S'), ID_checkItem_MML),
            ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))
         
        wx.EVT_MENU(self, ID_mmlPanel_assignColor, self.OnAssignColor)
        wx.EVT_MENU(self, ID_getMassSpectrum, self.OnListGetMS)
        wx.EVT_MENU(self, ID_get1DmobilitySpectrum, self.OnListGet1DT)
        wx.EVT_MENU(self, ID_checkAllItems_MML, self.OnCheckAllItems)
        wx.EVT_MENU(self, ID_checkItem_MML, self.onItemCheck)

    def makeToolbar(self):
        
        self.Bind(wx.EVT_TOOL, self.onAddTool, id=ID_addFilesMenu)
        self.Bind(wx.EVT_TOOL, self.onRemoveTool, id=ID_removeFilesMenu)
        self.Bind(wx.EVT_TOOL, self.OnCheckAllItems, id=ID_checkAllItems_MML)
        self.Bind(wx.EVT_TOOL, self.onOverlayTool, id=ID_overlayFilesMenu)
        self.Bind(wx.EVT_TOOL, self.onAnnotateTool, id=ID_mmlPanel_annotateTool)
        self.Bind(wx.EVT_TOOL, self.onProcessTool, id=ID_mmlPanel_processTool)
        self.Bind(wx.EVT_TOOL, self.presenter.onOpenMultipleMLFiles, id=ID_openMassLynxFiles)
        
        self.toolbar = wx.ToolBar(self, style=wx.TB_HORIZONTAL | wx.TB_DOCKABLE, id = wx.ID_ANY) 
        self.toolbar.SetToolBitmapSize((16, 16)) 
        self.toolbar.AddTool(ID_checkAllItems_MML, self.icons.iconsLib['check16'] , 
                              shortHelpString="Check all items")
        self.toolbar.AddTool(ID_addFilesMenu, self.icons.iconsLib['add16'],
                             shortHelpString="Add files...") 
        self.toolbar.AddTool(ID_removeFilesMenu, self.icons.iconsLib['remove16'], 
                             shortHelpString="Remove...")
        self.toolbar.AddTool(ID_mmlPanel_annotateTool, self.icons.iconsLib['annotate16'],
                             shortHelpString="Annotate...")
        self.toolbar.AddTool(ID_mmlPanel_processTool, self.icons.iconsLib['process16'],
                             shortHelpString="Process...")
        self.toolbar.AddTool(ID_overlayFilesMenu, self.icons.iconsLib['overlay16'],
                             shortHelpString="Visualise mass spectra...")
        self.toolbar.AddSeparator()
        self.toolbar.Realize()   
            
    def onAnnotateTool(self, evt):
        self.Bind(wx.EVT_MENU, self.onChangeColorBatch, id=ID_mmlPanel_changeColorBatch_palette)
        self.Bind(wx.EVT_MENU, self.onChangeColorBatch, id=ID_mmlPanel_changeColorBatch_colormap)
        
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_changeColorBatch_palette,
                                     text='Colour selected items using color palette', 
                                     bitmap=self.icons.iconsLib['blank_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_changeColorBatch_colormap,
                                     text='Colour selected items using colormap', 
                                     bitmap=self.icons.iconsLib['blank_16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
            
    def onAddTool(self, evt):
        
        self.Bind(wx.EVT_TOOL, self.presenter.onOpenMultipleMLFiles, id=ID_openMassLynxFiles)
        self.Bind(wx.EVT_TOOL, self.presenter.onOpenMultipleMLFiles, id=ID_addNewMassLynxFilesDoc)
        
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_addNewMassLynxFilesDoc,
                                     text='Add files to new document', 
                                     bitmap=self.icons.iconsLib['new_document_16']))
        menu.Append(ID_openMassLynxFiles, "Add files to current document")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()        
          
    def onRemoveTool(self, evt):
        # Make bindings
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeSelectedFile)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeAllFiles)
        self.Bind(wx.EVT_MENU, self.OnClearTable, id=ID_clearTableMML)
        self.Bind(wx.EVT_MENU, self.OnClearTable, id=ID_clearSelectedMML)
        
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearTableMML,
                                     text='Clear table', 
                                     bitmap=self.icons.iconsLib['clear_16']))
        menu.Append(ID_clearSelectedMML, "Clear selected")
        menu.AppendSeparator()
        menu.Append(ID_removeSelectedFile, "Remove selected file")
        menu.Append(ID_removeAllFiles, "Remove all files")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

#     def onSaveTool(self, evt):
#         menu = wx.Menu()
#         menu.Append(ID_save1DAllFiles, "Export 1D IM-MS to file (all items)")
#         menu.Append(ID_saveMSAllFiles, "Export MS to file (all items)")
#         menu.Append(ID_ExportWindowFiles, "Export... (new window)")
#         self.PopupMenu(menu)
#         menu.Destroy()
#         self.SetFocus()

#     def onProcessTool(self, evt):
#         # Make bindings
#         self.Bind(wx.EVT_MENU, self.presenter.reBinMSdata, id=ID_reBinMSmanual)
# #         self.Bind(wx.EVT_MENU, self.OnListConvertAxis, id=ID_convertSelectedAxisFiles)
# #         self.Bind(wx.EVT_MENU, self.OnListConvertAxis, id=ID_convertAllAxisFiles)
# #         self.Bind(wx.EVT_MENU, self.presenter.onCombineMultipleMLFiles, id=ID_combineMassLynxFiles)
#         
#         menu = wx.Menu()
#         menu.Append(ID_reBinMSmanual, "Re-bin MS of list of MassLynx files")
#         menu.Append(ID_convertSelectedAxisFiles, "Convert 1D/2D IM-MS from bins to ms (selected)")
#         if self.currentXlabels == 'ms':
#             menu.Append(ID_convertAllAxisFiles, "Convert 1D/2D IM-MS from ms to bins (all)")
#         else:
#             menu.Append(ID_convertAllAxisFiles, "Convert 1D/2D IM-MS from bins to ms (all)")
#         menu.Append(ID_combineMassLynxFiles, "Combine 1D DT to form 2D matrix (ascending energy)")
#         self.PopupMenu(menu)
#         menu.Destroy()
#         self.SetFocus()
        
    def onOverlayTool(self, evt):
        
        self.Bind(wx.EVT_TOOL, self.onCheckTool, id=ID_mmlPanel_preprocess)
        self.Bind(wx.EVT_TOOL, self.onCheckTool, id=ID_mmlPanel_addToDocument)
        self.Bind(wx.EVT_TOOL, self.onCheckTool, id=ID_mmlPanel_showLegend)
        self.Bind(wx.EVT_TOOL, self.onOverlayPlot, id=ID_mmlPanel_overlayWaterfall)
        self.Bind(wx.EVT_TOOL, self.onOverlayPlot, id=ID_mmlPanel_overlayChargeStates)
        self.Bind(wx.EVT_TOOL, self.onOverlayPlot, id=ID_mmlPanel_overlayMW)
        self.Bind(wx.EVT_TOOL, self.onOverlayPlot, id=ID_mmlPanel_overlayProcessedSpectra)
        self.Bind(wx.EVT_TOOL, self.onOverlayPlot, id=ID_mmlPanel_overlayFittedSpectra)
        self.Bind(wx.EVT_TOOL, self.onOverlayPlot, id=ID_mmlPanel_overlayFoundPeaks)
        
        
        menu = wx.Menu()
        self.showLegend_check = menu.AppendCheckItem(ID_mmlPanel_showLegend, "Show legend",
                                                     help="Show legend on overlay plots")
        self.showLegend_check.Check(self.showLegend)
        self.addToDocument_check = menu.AppendCheckItem(ID_mmlPanel_addToDocument, "Add overlay plots to document",
                                                        help="Add overlay results to comparison document")
        self.addToDocument_check.Check(self.addToDocument)
        menu.AppendSeparator()
        self.preProcess_check = menu.AppendCheckItem(ID_mmlPanel_preprocess, "Pre-process mass spectra",
                                                     help="Pre-process MS before generating waterfall plot (i.e. linearization, normalisation, smoothing, etc")
        self.preProcess_check.Check(self.preprocessMS)
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_overlayWaterfall,
                                     text='Overlay raw mass spectra', 
                                     bitmap=self.icons.iconsLib['panel_waterfall_16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_overlayProcessedSpectra,
                                     text='Overlay processed spectra', 
                                     bitmap=self.icons.iconsLib['blank_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_overlayFittedSpectra,
                                     text='Overlay fitted spectra', 
                                     bitmap=self.icons.iconsLib['blank_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_overlayMW,
                                     text='Overlay molecular weight distribution', 
                                     bitmap=self.icons.iconsLib['blank_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_overlayChargeStates,
                                     text='Overlay charge state distribution', 
                                     bitmap=self.icons.iconsLib['blank_16']))
#         menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_overlayFoundPeaks,
#                                      text='Overlay isolated species', 
#                                      bitmap=self.icons.iconsLib['blank_16']))
        
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onProcessTool(self, evt):

        self.Bind(wx.EVT_TOOL, self.onAutoUniDec, id=ID_mmlPanel_batchRunUniDec)
        
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_batchRunUniDec,
                                     text='Run UniDec for selected items', 
                                     bitmap=self.icons.iconsLib['process_unidec_16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
    
    def onCheckTool(self, evt):
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
        
    def onChangeColorBatch(self, evt):
        # get number of checked items
        check_count = 0
        for row in range(self.filelist.GetItemCount()):
            if self.filelist.IsChecked(index=row):
                check_count += 1 
        if evt.GetId() == ID_mmlPanel_changeColorBatch_palette:
            colors = self.presenter.view.panelPlots.onChangePalette(None, n_colors=check_count, return_colors=True)
        else:
            colors = self.presenter.view.panelPlots.onGetColormapList(n_colors=check_count)
        for row in range(self.filelist.GetItemCount()):
            if self.filelist.IsChecked(index=row):
                color = colors[row]
                self.filelist.SetItemBackgroundColour(row, convertRGB1to255(color))
          
    def onOverlayPlot(self, evt):
        evtID = evt.GetId()
        
        interpolate = True
        show_legend = self.showLegend_check.IsChecked()
        names, colors, xvals_list, yvals_list = [], [], [], []
        for row in range(self.filelist.GetItemCount()):
            if not self.filelist.IsChecked(index=row): continue
            itemInfo = self.OnGetItemInformation(itemID=row)
            names.append(itemInfo['label'])
            # get mass spectrum information
            document = self.presenter.documentsDict[itemInfo["document"]]
            data = document.multipleMassSpectrum[itemInfo["filename"]]
            
            # check if unidec dataset is present
            if 'unidec' not in data and evtID in [ID_mmlPanel_overlayMW,
                                                  ID_mmlPanel_overlayProcessedSpectra,
                                                  ID_mmlPanel_overlayFittedSpectra,
                                                  ID_mmlPanel_overlayChargeStates,
                                                  ID_mmlPanel_overlayFoundPeaks]:
                print("Selected item {} ({}) does not have UniDec results".format(itemInfo['document'],
                                                                                   itemInfo['filename']))
                continue
            if evtID == ID_mmlPanel_overlayWaterfall:
                interpolate = False
                xvals = document.multipleMassSpectrum[itemInfo["filename"]]['xvals'].copy()
                yvals = document.multipleMassSpectrum[itemInfo["filename"]]['yvals'].copy()
                if self.preprocessMS:
                    xvals, yvals = self.presenter.processMSdata(msX=xvals, 
                                                                msY=yvals, 
                                                                return_data=True)
                    
            elif evtID == ID_mmlPanel_overlayMW:
                xvals = data['unidec']['MW distribution']['xvals']
                yvals = data['unidec']['MW distribution']['yvals']

            elif evtID == ID_mmlPanel_overlayProcessedSpectra:
                xvals = data['unidec']['Processed']['xvals']
                yvals = data['unidec']['Processed']['yvals']
            elif evtID == ID_mmlPanel_overlayFittedSpectra:
                xvals = data['unidec']['Fitted']['xvals'][0]
                yvals = data['unidec']['Fitted']['yvals'][1]
            elif evtID == ID_mmlPanel_overlayChargeStates:
                xvals = data['unidec']['Charge information'][:,0]
                yvals = data['unidec']['Charge information'][:,1]
            elif evtID == ID_mmlPanel_overlayFoundPeaks:
                data['unidec']['m/z with isolated species']
                xvals = []
                yvals = []
                
          
            xvals_list.append(xvals)
            yvals_list.append(yvals)
            colors.append(convertRGB255to1(itemInfo['color']))
        
        if len(xvals_list) == 0:
            print("No data in selected items")
            return
        
        # check that lengths are correct
        if interpolate:
            x_long = max(xvals_list,key=len)
            for i, xlist in enumerate(xvals_list):
                if len(xlist) < len(x_long):
                    xlist_new, ylist_new = self.interpolate(xvals_list[i],
                                                            yvals_list[i],
                                                            x_long)
                    xvals_list[i] = xlist_new
                    yvals_list[i] = ylist_new
        
        # sum mw 
        if evtID == ID_mmlPanel_overlayMW:
            xvals_list.insert(0, np.average(xvals_list, axis=0))
            yvals_list.insert(0, np.average(yvals_list, axis=0))
            colors.insert(0, ((0, 0, 0)))
            names.insert(0, ("Average"))
            
        kwargs = {'show_y_labels':True, 'labels':names, 'add_legend':show_legend}
        if evtID == ID_mmlPanel_overlayWaterfall:
            overlay_type = "Waterfall (Raw)"
            xlabel, ylabel = "m/z", "Offset Intensity"
            self.presenter.view.panelPlots.on_plot_waterfall(xvals_list, yvals_list, None, colors=colors, 
                                                             xlabel=xlabel, ylabel=ylabel, **kwargs)
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Waterfall'])
        if evtID == ID_mmlPanel_overlayMW:
            overlay_type = "Waterfall (Deconvoluted MW)"
            xlabel, ylabel = "Mass (Da)", "Offset Intensity"
            self.presenter.view.panelPlots.on_plot_waterfall(xvals_list, yvals_list, None, colors=colors, 
                                                             xlabel=xlabel, ylabel=ylabel, **kwargs)
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Waterfall'])
        elif evtID == ID_mmlPanel_overlayProcessedSpectra:
            overlay_type = "Waterfall (Processed)"
            xlabel, ylabel = "m/z", "Offset Intensity"
            self.presenter.view.panelPlots.on_plot_waterfall(xvals_list, yvals_list, None, colors=colors, 
                                                             xlabel=xlabel, ylabel=ylabel, **kwargs)
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Waterfall'])
        elif evtID == ID_mmlPanel_overlayFittedSpectra:
            overlay_type = "Waterfall (Fitted)"
            xlabel, ylabel = "m/z", "Offset Intensity"
            self.presenter.view.panelPlots.on_plot_waterfall(xvals_list, yvals_list, None, colors=colors, 
                                                             xlabel=xlabel, ylabel=ylabel, **kwargs)
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Waterfall'])
        elif evtID == ID_mmlPanel_overlayChargeStates:
            overlay_type = "Waterfall (Charge states)"
            xlabel, ylabel = "Charge", "Intensity"
            kwargs = {'show_y_labels':True, 'labels':names, 'increment':0.000001, 'add_legend':show_legend}
            self.presenter.view.panelPlots.on_plot_waterfall(xvals_list, yvals_list, None, colors=colors, 
                                                             xlabel=xlabel, ylabel=ylabel, **kwargs)
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Waterfall'])
            
        if self.addToDocument:
            self.onAddOverlayToDocument(xvals_list, yvals_list, colors, xlabel, ylabel, overlay_type, **kwargs)
            
    
    def onAddOverlayToDocument(self, xvals, yvals, colors, xlabel, ylabel, overlay_type, **kwargs):
        overlay_labels = ", ".join(kwargs['labels'])
        overlay_title = "{}: {}".format(overlay_type, overlay_labels)
        
        document = self.presenter.get_overlay_document()
        document.gotOverlay = True
        document.IMS2DoverlayData[overlay_title] = {'xvals':xvals, 'yvals':yvals,
                                                    'xlabel':xlabel, 'ylabel':ylabel,
                                                    'colors':colors, 'labels':kwargs['labels'],
                                                    'waterfall_kwargs':kwargs}
        
        # update document
        self.presenter.OnUpdateDocument(document, expand_item='overlay',
                                        expant_item_title=overlay_title)

        
    
    def interpolate(self, x_short, y_short, x_long):
         
        fcn = interp1d(x_short, y_short, fill_value=0, bounds_error=False)
        new_y_long = fcn(x_long)
        return  x_long, new_y_long
             
    def onAutoUniDec(self, evt):
        
        for row in range(self.filelist.GetItemCount()):
            if not self.filelist.IsChecked(index=row): continue
            itemInfo = self.OnGetItemInformation(itemID=row)
            
            # get mass spectrum information
            document = self.presenter.documentsDict[itemInfo["document"]]
            
            data = document.multipleMassSpectrum[itemInfo["filename"]]
            xvals = data['xvals']
            yvals = data['yvals'].copy()
            
            # check if unidec data present in the document
            if 'unidec' not in data:
                data['unidec'] = {}
            
            basename = splitext(document.title)[0]
            file_name = "".join([basename, ".txt"])
            folder = document.path
            
            print("Pre-processing mass spectra using m/z range {} - {} with {} bin size".format(self.config.unidec_mzStart,
                                                                                               self.config.unidec_mzEnd,
                                                                                               self.config.unidec_mzBinSize))
            # initilise data    
            self.config.unidec_engine.open_file(file_name=file_name, 
                                                file_directory=folder, 
                                                data_in=np.transpose([xvals, yvals]))
            
            # setup parameters
            self.config.unidec_engine.config.minmz = self.config.unidec_mzStart
            self.config.unidec_engine.config.maxmz = self.config.unidec_mzEnd
            self.config.unidec_engine.config.mzbins = self.config.unidec_mzBinSize
            self.config.unidec_engine.config.smooth = self.config.unidec_gaussianFilter
            self.config.unidec_engine.config.accvol = self.config.unidec_accelerationV
            self.config.unidec_engine.config.linflag = self.config.unidec_linearization_choices[self.config.unidec_linearization]
            self.config.unidec_engine.config.cmap = self.config.currentCmap
            
            # prepare data for deconvolution
            self.config.unidec_engine.process_data()
            
            # add data to document
            raw_data = {'xvals':self.config.unidec_engine.data.data2[:, 0],
                        'yvals':self.config.unidec_engine.data.data2[:, 1],
                        'color':[0,0,0], 'label':"Data", 'xlabels':"m/z", 
                        'ylabels':"Intensity"}
            # add data
            data['unidec']['Processed'] = raw_data
            
            print("Deconvoluting mass spectra in range {} - {} with {} bin size. Charge state range {} - {}".format(self.config.unidec_mwStart,
                                                                                                                    self.config.unidec_mwEnd,
                                                                                                                    self.config.unidec_mwFrequency,
                                                                                                                    self.config.unidec_zStart,
                                                                                                                    self.config.unidec_zEnd))
            # deconvolution parameters    
            self.config.unidec_engine.config.masslb = self.config.unidec_mwStart
            self.config.unidec_engine.config.massub = self.config.unidec_mwEnd
            self.config.unidec_engine.config.massbins = self.config.unidec_mwFrequency
            self.config.unidec_engine.config.startz = self.config.unidec_zStart
            self.config.unidec_engine.config.endz = self.config.unidec_zEnd
            self.config.unidec_engine.config.numz = self.config.unidec_zEnd - self.config.unidec_zStart
            self.config.unidec_engine.config.psfun = self.config.unidec_peakFunction_choices[self.config.unidec_peakFunction]
            if self.config.unidec_peakWidth_auto:
                self.config.unidec_engine.get_auto_peak_width()
            else:
                self.config.unidec_engine.config.mzsig = self.config.unidec_peakWidth

            try:
                self.config.unidec_engine.run_unidec()
            except IndexError:
                dialogs.dlgBox(exceptionTitle="Error",
                               exceptionMsg="Load and pre-process data first", 
                               type="Error")
                return
            except ValueError:
                print("Could not perform task")
                return
            
            fit_data = {'xvals':[self.config.unidec_engine.data.data2[:, 0], 
                                 self.config.unidec_engine.data.data2[:, 0]],
                        'yvals':[self.config.unidec_engine.data.data2[:, 1], 
                                 self.config.unidec_engine.data.fitdat],
                        'colors':[[0,0,0], [1,0,0]], 'labels':['Data', 'Fit Data'],
                        'xlabel':"m/z", 'ylabel':"Intensity", 
                        'xlimits':[np.min(self.config.unidec_engine.data.data2[:, 0]), 
                                   np.max(self.config.unidec_engine.data.data2[:, 0])]}
            
            mw_distribution_data = {'xvals':self.config.unidec_engine.data.massdat[:, 0],
                                    'yvals':self.config.unidec_engine.data.massdat[:, 1],
                                    'color':[0,0,0], 'label':"Data", 'xlabels':"Mass (Da)",
                                    'ylabels':"Intensity"}
            mz_grid_data = {'grid':self.config.unidec_engine.data.mzgrid,
                            'xlabels':" m/z (Da)", 'ylabels':"Charge",
                            'cmap':self.config.unidec_engine.config.cmap}
            mw_v_z_data = {'xvals':self.config.unidec_engine.data.massdat[:, 0],
                           'yvals':self.config.unidec_engine.data.ztab,
                           'zvals':self.config.unidec_engine.data.massgrid,
                           'xlabels':"Mass (Da)", 'ylabels':"Charge",
                           'cmap':self.config.unidec_engine.config.cmap}
            # add data
            data['unidec']['Fitted'] = fit_data
            data['unidec']['MW distribution'] = mw_distribution_data
            data['unidec']['m/z vs Charge'] = mz_grid_data
            data['unidec']['MW vs Charge'] = mw_v_z_data
            
            # peak finding parameters
            self.config.unidec_engine.config.peaknorm = self.config.unidec_peakNormalization_choices[self.config.unidec_peakNormalization]
            self.config.unidec_engine.config.peakwindow = self.config.unidec_peakDetectionWidth
            self.config.unidec_engine.config.peakthresh = self.config.unidec_peakDetectionThreshold
            self.config.unidec_engine.config.separation = self.config.unidec_lineSeparation
            
            try:
                self.config.unidec_engine.pick_peaks()
            except (ValueError, ZeroDivisionError):
                dialogs.dlgBox(exceptionTitle="Error",
                               exceptionMsg="Failed to find peaks. Try increasing the value of Peak detection range (Da)", 
                               type="Error")
                return
            except IndexError:
                dialogs.dlgBox(exceptionTitle="Error",
                               exceptionMsg="Please run UniDec first", 
                               type="Error")
                return
            
            
            try:
                self.config.unidec_engine.convolve_peaks()
            except OverflowError:
                dialogs.dlgBox(exceptionTitle="Error",
                               exceptionMsg="Too many peaks! Try reprocessing your data with larger peak width or larger bin size.", 
                               type="Error")
                return
            
            # individually plotted
            individual_dict, massList, massMax = self.get_unidec_data(data_type="Individual MS")
            barchart_dict = self.get_unidec_data(data_type="Barchart")
            # add data
            data['unidec']['m/z with isolated species'] = individual_dict
            data['unidec']['Barchart'] = barchart_dict
            data['unidec']['Charge information'] = self.config.unidec_engine.get_charge_peaks()
#             massList, massMax = self.get_unidec_data(data_type="MassList")
            individual_dict['_massList_'] = [massList, massMax] 
            
            
            data['temporary_unidec'] = self.config.unidec_engine
            document.multipleMassSpectrum[itemInfo["filename"]] = data

            # update document
            self.presenter.OnUpdateDocument(document, expand_item='mass_spectra',
                                            expant_item_title=itemInfo['filename'])

    def get_unidec_data(self, data_type="Individual MS"):
        if data_type == "Individual MS":   
            stickmax = 1.0
            num = 0
            individual_dict = dict()
            legend_text = [[[0,0,0], "Raw"]]
            colors = []
            labels = []
            mwList, heightList = [], []
            for i in range(0, self.config.unidec_engine.pks.plen):
                p = self.config.unidec_engine.pks.peaks[i]
                if p.ignore == 0:
                    label = "MW: {:.2f} ({:.2f} %)".format(p.mass, p.height)
                    mwList.append(label)
                    heightList.append(p.height)
                    list1, list2 = [], []
                    if (not isempty(p.mztab)) and (not isempty(p.mztab2)):
                        mztab = np.array(p.mztab)
                        mztab2 = np.array(p.mztab2)
                        maxval = np.amax(mztab[:, 1])
                        for k in range(0, len(mztab)):
                            if mztab[k, 1] > self.config.unidec_engine.config.peakplotthresh * maxval:
                                list1.append(mztab2[k, 0])
                                list2.append(mztab2[k, 1])
                                
                        if self.config.unidec_engine.pks.plen <= 16:
                            color=convertRGB255to1(self.config.customColors[i])
                        else:
                            color=p.color
                        colors.append(color)
                        labels.append("MW: {:.2f}".format(p.mass))
                        legend_text.append([color, "MW: {:.2f}".format(p.mass)])
                        individual_dict["MW: {:.2f}".format(p.mass)] = {'scatter_xvals':np.array(list1),
                                                                        'scatter_yvals':np.array(list2),
                                                                        'marker':p.marker, 
                                                                        'color':color,
                                                                        'label':"MW: {:.2f}".format(p.mass),
                                                                        'line_xvals':self.config.unidec_engine.data.data2[:, 0],
                                                                        'line_yvals':np.array(p.stickdat)/stickmax-(num + 1) * self.config.unidec_engine.config.separation
                                                                        }
                        num += 1
            individual_dict['legend_text'] = legend_text
            individual_dict['xvals'] = self.config.unidec_engine.data.data2[:, 0]
            individual_dict['yvals'] = self.config.unidec_engine.data.data2[:, 1]
            individual_dict['xlabel'] = "m/z (Da)"
            individual_dict['ylabel'] = "Intensity"
            individual_dict['colors'] = colors
            individual_dict['labels'] = labels
            return individual_dict, mwList, mwList[heightList.index(np.max(heightList))]
        elif data_type == 'MassList':
            mwList, heightList = [], []
            for i in range(0, self.config.unidec_engine.pks.plen):
                p = self.config.unidec_engine.pks.peaks[i]
                if p.ignore == 0:
                    label = "MW: {:.2f} ({:.2f} %)".format(p.mass, p.height)
                    mwList.append(label)
                    heightList.append(p.height)
            return mwList, mwList[heightList.index(np.max(heightList))]
        elif data_type == 'Barchart':
            if self.config.unidec_engine.pks.plen > 0:
                num = 0
                yvals, colors, labels, legend_text, markers, legend = [], [], [], [], [], []
                for p in self.config.unidec_engine.pks.peaks:
                    if p.ignore == 0:
                        yvals.append(p.height)
                        if self.config.unidec_engine.pks.plen <= 15:
                            color = convertRGB255to1(self.config.customColors[num])
                        else:
                            color = p.color
                        markers.append(p.marker)
                        labels.append(p.label)
                        colors.append(color)
                        legend_text.append([color, "MW: {:.2f}".format(p.mass)])
                        legend.append("MW: {:.2f}".format(p.mass))
                        num += 1
                    xvals = range(0, num)
                    barchart_dict = {'xvals':xvals,
                                     'yvals':yvals,
                                     'labels':labels,
                                     'colors':colors,
                                     'legend':legend,
                                     'legend_text':legend_text,
                                     'markers':markers}
                return barchart_dict
            
    def onRenameItem(self, old_name, new_name, item_type="Document"):
        for row in range(self.filelist.GetItemCount()):
            itemInfo = self.OnGetItemInformation(itemID=row)
            if item_type == "document":
                if itemInfo['document'] == old_name:
                    self.filelist.SetStringItem(index=row,
                                                col=self.config.multipleMLColNames['document'],
                                                label=new_name)
            elif item_type == "filename":
                if itemInfo['filename'] == old_name:
                    self.filelist.SetStringItem(index=row,
                                                col=self.config.multipleMLColNames['filename'],
                                                label=new_name)
#             
    def OnRightClickMenu(self, evt):
        
        self.Bind(wx.EVT_MENU, self.OnListGetMS, id=ID_getMassSpectrum)
        self.Bind(wx.EVT_MENU, self.OnListGet1DT, id=ID_get1DmobilitySpectrum)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeSelectedFilePopup)
        self.Bind(wx.EVT_MENU, self.OnAssignColor, id=ID_mmlPanel_assignColor)
        self.Bind(wx.EVT_MENU, self.OnListGetMS, id=ID_getCombinedMassSpectrum)
        
        
        # Capture which item was clicked
        self.currentItem, flags = self.filelist.HitTest(evt.GetPosition())
        # Create popup menu
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_getMassSpectrum,
                                     text='Show mass spectrum\tM', 
                                     bitmap=self.icons.iconsLib['mass_spectrum_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_get1DmobilitySpectrum,
                                     text='Show mobiligram\tD', 
                                     bitmap=self.icons.iconsLib['mobiligram_16']))
        menu.Append(ID_getCombinedMassSpectrum, "Show mass spectrum (average)")
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_assignColor,
                                     text='Assign new color\tC', 
                                     bitmap=self.icons.iconsLib['color_panel_16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeSelectedFilePopup,
                                     text='Remove item', 
                                     bitmap=self.icons.iconsLib['bin16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def onOpenFile_DnD(self, pathlist):
        self.presenter.onOpenMultipleMLFiles(evt=ID_openMassLynxFiles, pathlist=pathlist)

    def OnListConvertAxis(self, evt):
        """
        Function to convert x and y axis labels to/from bins-ms-ccs
        """
        document = self.getCurrentDocument()
        if document == None: return
        currentItems = self.filelist.GetItemCount()-1
        if evt.GetId() == ID_convertSelectedAxisFiles: pass
        elif evt.GetId() == ID_convertAxisFilesPopup:
            selectedItem = self.filelist.GetItem(self.currentItem,0).GetText()
            xlabel = document.multipleMassSpectrum[selectedItem]['xlabel']
            pusherFreq = document.multipleMassSpectrum[selectedItem]['parameters']['pusherFreq']
            # This should try to use the global pusher!
            if pusherFreq == None: 
                pusherFreq = document.parameters['pusherFreq']
                # If still fails, this should open a pupup for manual
                # TODO: prompt for manual pusher value
                if pusherFreq == None:  return
            if xlabel == 'Drift time(bins)':
                dtX = (document.multipleMassSpectrum[selectedItem]['ims1DX'] * pusherFreq)/1000
                document.multipleMassSpectrum[selectedItem]['ims1DX'] = dtX
                document.multipleMassSpectrum[selectedItem]['xlabel'] = 'Drift time (ms)'
            elif xlabel == 'Drift time (ms)':
                dtX = (document.multipleMassSpectrum[selectedItem]['ims1DX'] / pusherFreq)*1000
                document.multipleMassSpectrum[selectedItem]['ims1DX'] = dtX
                document.multipleMassSpectrum[selectedItem]['xlabel'] = 'Drift time(bins)'    
            # Call and plot that plot
            self.OnListGet1DT(evt)  
        else: 
            while (currentItems >= 0):
                selectedItem = self.filelist.GetItem(currentItems,0).GetText()
                xlabel = document.multipleMassSpectrum[selectedItem]['xlabel']
                pusherFreq = document.multipleMassSpectrum[selectedItem]['parameters']['pusherFreq']
                # This should try to use the global pusher!
                if pusherFreq == None: 
                    pusherFreq = document.parameters['pusherFreq']
                    # If still fails, this should open a pupup for manual
                    # TODO: prompt for manual pusher value
                    if pusherFreq == None:  
                        currentItems-=1
                        continue
                if xlabel == 'Drift time(bins)':
                    self.currentXlabels = "ms"
                    dtX = (document.multipleMassSpectrum[selectedItem]['ims1DX'] * pusherFreq)/1000
                    document.multipleMassSpectrum[selectedItem]['ims1DX'] = dtX
                    document.multipleMassSpectrum[selectedItem]['xlabel'] = 'Drift time (ms)'
                elif xlabel == 'Drift time (ms)':
                    self.currentXlabels = 'bins'
                    dtX = (document.multipleMassSpectrum[selectedItem]['ims1DX'] / pusherFreq)*1000
                    document.multipleMassSpectrum[selectedItem]['ims1DX'] = dtX
                    document.multipleMassSpectrum[selectedItem]['xlabel'] = 'Drift time(bins)'    
                currentItems-=1
        # Update document dictionary and tree
        self.presenter.documentsDict[document.title] = document
        try:
            self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[document.title])
        except KeyError: pass 
        
    def OnListGetMS(self, evt):
        """
        Function to plot selected MS in the mainWindow
        """
        
        title = self.filelist.GetItem(self.currentItem, self.config.multipleMLColNames['document']).GetText()
        document = self.presenter.documentsDict[title]
        if document == None: 
            return
        
        if evt.GetId() == ID_getMassSpectrum:
            itemName = self.filelist.GetItem(self.currentItem,self.config.multipleMLColNames['filename']).GetText()
            try:
                msX = document.multipleMassSpectrum[itemName]['xvals']
                msY = document.multipleMassSpectrum[itemName]['yvals']
            except KeyError: 
                return
            parameters = document.multipleMassSpectrum[itemName].get('parameters', {'startMS':np.min(msX), 
                                                                                    'endMS':np.max(msX)})
            xlimits = [parameters['startMS'],parameters['endMS']]
        elif evt.GetId() == ID_getCombinedMassSpectrum:
            try:
                msX = document.massSpectrum['xvals']
                msY = document.massSpectrum['yvals']
                xlimits = document.massSpectrum['xlimits']
            except KeyError:
                dialogs.dlgBox(exceptionTitle="Error",
                               exceptionMsg="Document does not have averaged mass spectrum", 
                               type="Error")
                return
        
        # Plot data
        self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['MS'])
        self.presenter.view.panelPlots.on_plot_MS(msX, msY, xlimits=xlimits, full_repaint=True)
        
    def OnListGet1DT(self, evt):
        """
        Function to plot selected 1DT in the mainWindow
        """
        title = self.filelist.GetItem(self.currentItem, self.config.multipleMLColNames['document']).GetText()
        document = self.presenter.documentsDict[title]
        
#         document = self.getCurrentDocument()
        if document == None: return
        try:
            itemName = self.filelist.GetItem(self.currentItem,0).GetText()
            dtX = document.multipleMassSpectrum[itemName]['ims1DX']
            dtY = document.multipleMassSpectrum[itemName]['ims1D']
            xlabel = document.multipleMassSpectrum[itemName]['xlabel']
            
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['1D'])
            self.presenter.view.panelPlots.on_plot_1D(dtX, dtY, xlabel, full_repaint=True)
        except KeyError: 
            dialogs.dlgBox(exceptionTitle="Error",
                           exceptionMsg="No mobility data present for selected item", 
                           type="Error")
            return
            
    def OnGetColumnClick(self, evt):
        self.OnSortByColumn(column=evt.GetColumn())
            
    def OnCheckAllItems(self, evt, check=True, override=False):
        """
        Check/uncheck all items in the list
        ===
        Parameters:
        check : boolean, sets items to specified state
        override : boolean, skips settings self.allChecked value
        """
        rows = self.filelist.GetItemCount()
        
        if not override: 
            if self.allChecked:
                self.allChecked = False
                check = True
            else:
                self.allChecked = True
                check = False 
            
        if rows > 0:
            for row in range(rows):
                self.filelist.CheckItem(row, check=check)

#         if evt != None:
#             evt.Skip()
             
    def OnSortByColumn(self, column, overrideReverse=False):
        """
        Sort data in filelist based on pressed column
        """
        
        # Override reverse
        if overrideReverse:
            self.reverse = True
        
        # Check if it should be reversed
        if self.lastColumn == None:
            self.lastColumn = column
        elif self.lastColumn == column:
            if self.reverse == True:
                self.reverse = False
            else:
                self.reverse = True
        else:
            self.reverse = False
            self.lastColumn = column
        
        columns = self.filelist.GetColumnCount()
        rows = self.filelist.GetItemCount()
        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.filelist.GetItem(itemId=row, col=col)
                #  We want to make sure the first 3 columns are numbers
                if col==1:
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempRow.append(self.filelist.IsChecked(index=row))
            tempRow.append(self.filelist.GetItemBackgroundColour(row))
            tempData.append(tempRow)

        # Sort data (always by document + another variable
        tempData.sort(key = itemgetter(2, column), reverse=self.reverse)
        # Clear table and reinsert data
        self.filelist.DeleteAllItems()

        checkData, rgbData = [], []
        for check in tempData:
            rgbData.append(check[-1])
            del check[-1]
            checkData.append(check[-1])
            del check[-1]
        
        rowList = np.arange(len(tempData))
        for row, check, rgb in zip(rowList, checkData, rgbData):
            self.filelist.Append(tempData[row])
            self.filelist.CheckItem(row, check)
            self.filelist.SetItemBackgroundColour(row, rgb)
        
        # Now insert it into the document
        for row in range(rows):
            itemName = self.filelist.GetItem(itemId=row, 
                                             col=self.config.multipleMLColNames['filename']).GetText()
            docName = self.filelist.GetItem(itemId=row, 
                                            col=self.config.multipleMLColNames['document']).GetText()
            trapCV = str2num(self.filelist.GetItem(itemId=row, 
                                                   col=self.config.multipleMLColNames['energy']).GetText())
            
            self.presenter.documentsDict[docName].multipleMassSpectrum[itemName]['trap'] = trapCV

    def getCurrentDocument(self, docNameOnly=False):
        """
        Determines what is the currently selected document
        Gives an 'None' error when wrong document has been selected
        """
        # Now insert it into the document
        try:
            currentDoc = self.presenter.view.panelDocuments.topP.documents.enableCurrentDocument()
        except: 
            return None
        
        if currentDoc == 'Current documents':
            msg = 'There are no documents in the tree'
            self.presenter.view.SetStatusText(msg, 3)
            return currentDoc
        document = self.presenter.documentsDict[currentDoc]
        if document.dataType != 'Type: MANUAL': 
            msg = 'Make sure you select the correct dataset - MANUAL'
            self.presenter.view.SetStatusText(msg, 3)
            return None
        if docNameOnly: return currentDoc
        else: return document
        
    def OnDeleteAll(self, evt, ticked=False, selected=False, itemID=None):
        """ 
        This function removes selected or all MassLynx files from the 
        combined document
        """
        
#         currentDoc = self.getCurrentDocument(docNameOnly=True)
#         if currentDoc == None: return
        
        try:
            itemInfo = self.OnGetItemInformation(self.currentItem)
            currentDoc = itemInfo['document']
        except TypeError:
            pass
        currentItems = self.filelist.GetItemCount()-1
        if evt.GetId() == ID_removeSelectedFile:
            while (currentItems >= 0):
                item = self.filelist.IsChecked(index=currentItems)
                if item == True:
                    selectedItem = self.filelist.GetItem(currentItems, 0).GetText()
                    print(''.join(["Deleting ",selectedItem, " from ", currentDoc]))
                    try: 
                        del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[selectedItem]
                        if len(self.presenter.documentsDict[currentDoc].multipleMassSpectrum.keys()) == 0: 
                            self.presenter.documentsDict[currentDoc].gotMultipleMS = False
                    except KeyError: pass
                    self.filelist.DeleteItem(currentItems)
                    currentItems-=1
                else:
                    currentItems-=1
            try:
                self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[currentDoc])
            except KeyError: pass  
        elif evt.GetId() == ID_removeSelectedFilePopup:
            selectedItem = self.filelist.GetItem(self.currentItem,0).GetText()
            print(''.join(["Deleting ",selectedItem, " from ", currentDoc]))
            try: 
                del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[selectedItem]
                if len(self.presenter.documentsDict[currentDoc].multipleMassSpectrum.keys()) == 0: 
                    self.presenter.documentsDict[currentDoc].gotMultipleMS = False
            except KeyError: pass
            self.filelist.DeleteItem(self.currentItem)
            try:
                self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[currentDoc])
            except KeyError: pass  
        else:
            # Ask if you want to delete all items
            dlg = dialogs.dlgBox(exceptionTitle='Are you sure?', 
                                 exceptionMsg= "Are you sure you would like to delete ALL MassLynx files from the document?",
                                 type="Question")
            if dlg == wx.ID_NO:
                msg = 'Cancelled deletion operation'
                self.presenter.view.SetStatusText(msg, 3)
                return
            # Iterate over all items
            while (currentItems >= 0):
                itemInfo = self.OnGetItemInformation(currentItems)
                selectedItem = itemInfo['filename']
                currentDoc = itemInfo['document']
                print(''.join(["Deleting ",selectedItem, " from ", currentDoc]))
                try: 
                    del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[selectedItem]
                    if len(self.presenter.documentsDict[currentDoc].multipleMassSpectrum.keys()) == 0: 
                        self.presenter.documentsDict[currentDoc].gotMultipleMS = False
                except KeyError: pass
                self.filelist.DeleteItem(currentItems)
                currentItems-=1
            # Update tree with new document
            try:
                self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[currentDoc])
            except KeyError: pass  

    def OnClearTable(self, evt):
        """
        This function clears the table without deleting any items from the document tree
        """
        # Ask if you want to delete all items
        evtID = evt.GetId()
        
        if evtID == ID_clearSelectedMML:
            row = self.filelist.GetItemCount() - 1
            while (row >= 0):
                if self.filelist.IsChecked(index=row):
                    self.filelist.DeleteItem(row)
                row-=1
        else:
            dlg = dialogs.dlgBox(exceptionTitle='Are you sure?', 
                                 exceptionMsg= "Are you sure you would like to clear the table??",
                                 type="Question")
            if dlg == wx.ID_NO:
                msg = 'Cancelled clearing operation'
                self.presenter.view.SetStatusText(msg, 3)
                return
            self.filelist.DeleteAllItems()
        
    def onRemoveDuplicates(self, evt, limitCols=False):
        """
        This function removes duplicates from the list
        Its not very efficient!
        """
        
        columns = self.filelist.GetColumnCount()
        rows = self.filelist.GetItemCount()

        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.filelist.GetItem(itemId=row, col=col)
                
                #  We want to make sure certain columns are numbers
                if col in [1]:
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempRow.append(self.filelist.IsChecked(index=row))
            tempRow.append(self.filelist.GetItemBackgroundColour(row))
            tempData.append(tempRow)
        
        # Remove duplicates
        tempData = removeListDuplicates(input=tempData,
                                        columnsIn=['filename', 'energy', 'document', 'label', 'check', 'rgb'],
                                        limitedCols=['filename', 'document'])     
        rows = len(tempData)
        # Clear table
        self.filelist.DeleteAllItems()
        
        checkData, rgbData = [], []
        for check in tempData:
            rgbData.append(check[-1])
            del check[-1]
            checkData.append(check[-1])
            del check[-1]
        
        # Reinstate data
        rowList = np.arange(len(tempData))
        for row, check, rgb in zip(rowList, checkData, rgbData):
            self.filelist.Append(tempData[row])
            self.filelist.CheckItem(row, check)
            self.filelist.SetItemBackgroundColour(row, rgb)
            
        if evt is None: return
        else:
            evt.Skip()
           
    def OnGetItemInformation(self, itemID, return_list=False):
        # get item information
        information = {'filename':self.filelist.GetItem(itemID, self.config.multipleMLColNames['filename']).GetText(),
                       'energy':str2num(self.filelist.GetItem(itemID, self.config.multipleMLColNames['energy']).GetText()),
                       'document':self.filelist.GetItem(itemID, self.config.multipleMLColNames['document']).GetText(),
                       'label':self.filelist.GetItem(itemID, self.config.multipleMLColNames['label']).GetText(),
                       'color':self.filelist.GetItemBackgroundColour(item=itemID),
                       }
           
        if return_list:
            filename = information['filename']
            energy = information['energy']
            document = information['document']
            label = information['label']
            color = information['color']
            return filename, energy, document, label, color
            
        return information
    
    def onClearItems(self, document):
        """
        @param document: title of the document to be removed from the list
        """
        row = self.filelist.GetItemCount() - 1
        while (row >= 0):
            info = self.OnGetItemInformation(itemID=row)
            if info['document'] == document:
                self.filelist.DeleteItem(row)
                row-=1
            else:
                row-=1
        
    def OnAssignColor(self, evt):
        """
        @param itemID (int): value for item in table
        @param give_value (bool): should/not return color
        """ 
            
        # Restore custom colors
        custom = wx.ColourData()
        for key in self.config.customColors:
            custom.SetCustomColour(key, self.config.customColors[key])
        dlg = wx.ColourDialog(self, custom)
        dlg.Centre()
        dlg.GetColourData().SetChooseFull(True)
        
        # Show dialog and get new colour
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            newColour = list(data.GetColour().Get())
            dlg.Destroy()
            # Assign color
            self.filelist.SetItemBackgroundColour(self.currentItem, newColour)
            # Retrieve custom colors
            for i in xrange(15): 
                self.config.customColors[i] = data.GetCustomColour(i)
            
            # update document
            self.onUpdateDocument(evt=None)

    def onUpdateDocument(self, evt, itemInfo=None):
        
        # get item info
        if itemInfo == None:
            itemInfo = self.OnGetItemInformation(self.currentItem)
        
        # get item
        document = self.presenter.documentsDict[itemInfo['document']]
        
        keywords = ['color', 'energy', 'label']
        for keyword in keywords:
            if keyword == 'energy': keyword_name = 'trap'
            else: keyword_name = keyword
            document.multipleMassSpectrum[itemInfo['filename']][keyword_name] = itemInfo[keyword] 
        
        # Update file list
        self.presenter.OnUpdateDocument(document, expand_item='mass_spectra',
                                        expant_item_title=itemInfo['filename'])
        