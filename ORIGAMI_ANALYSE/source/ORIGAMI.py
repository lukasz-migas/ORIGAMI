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

# Import libraries
import wx.py as py
import wx
import numpy as np
import os
import sys
import time
from _codecs import encode
from numpy.ma import masked_array
from wx.lib.pubsub import setuparg1
import wx.lib.agw.multidirdialog as MDD
from collections import OrderedDict
from copy import deepcopy
import path
import pandas as pd
from ids import *
from math import sqrt, log, pow
from scipy.stats import linregress
from matplotlib.cm import cmap_d
import random
import threading
import re

# needed to avoid annoying warnings to be printed on console
import warnings
warnings.filterwarnings("ignore",category=DeprecationWarning)
warnings.filterwarnings("ignore",category=RuntimeWarning)
warnings.filterwarnings("ignore",category=UserWarning)
warnings.filterwarnings("ignore",category=FutureWarning)

# Import libraries used for Interactive Plots
from bokeh.plotting import figure, show, save, ColumnDataSource, Column 
from bokeh.models import HoverTool, LinearColorMapper
import matplotlib.colors as colors
import matplotlib.cm as cm
import bokeh.core.templates
import webbrowser


# Import ORIGAMI libraries
import mainWindow as mainWindow
import origamiConfig
from origamiConfig import document as doc
import massLynxFcns as ml
import analysisFcns as af
from toolbox import * 
import dialogs as dialogs

from dialogs import panelSelectDocument, panelCompareMS, panelCalibrantDB

    
class ORIGAMI(object):
    def __init__(self, *args, **kwargs):
        self.__wx_app = wx.App(redirect=False, filename='ORIGAMI')
        self.view = None
        self.init(*args, **kwargs)
        
    def start(self):
        self.view.Show()
        self.__wx_app.MainLoop()
        
    def onRebootWindow(self, evt):
        """
        Reset window
        """
        self.view.Destroy()
        self.view = None
        self.view = mainWindow.MyFrame(self, config = self.config, 
                                       icons = self.icons, 
                                       title="ORIGAMI")
        self.view.Show()

    def quit(self):
        # TODO Export config to file
        self.__wx_app.ProcessIdle()
        self.__wx_app.ExitMainLoop()
        self.view.Destroy()
        return True
    
    def endSession(self):
        wx.CallAfter(self.quit, force=True)
    
    def init(self, *args, **kwargs):
        self.config = origamiConfig.OrigamiConfig()
        self.icons = origamiConfig.IconContainer()
        self.docs = origamiConfig.document()
        
        # Setup variables
        self.makeVariables()
        title =  "ORIGAMI - %s "% self.config.version 
        self.view = mainWindow.MyFrame(self, config = self.config, 
                                       icons = self.icons, title=title)
        self.__wx_app.SetTopWindow(self.view)
        self.__wx_app.SetAppName(title)
        self.__wx_app.SetVendorName("Lukasz G Migas, University of Manchester")
                
        # Assign standard input/output to variable
        self.config.stdin = sys.stdin
        self.config.stdout = sys.stdout
        self.config.stderr = sys.stderr 
                
        # Set current style
        self.onChangePlotStyle(evt=None)
        
        # Load configuration file
        self.onImportConfig(evt=None, onStart=True)
        self.logging = self.config.logging
        
        # Load protein/CCS database
        self.onImportCCSDatabase(evt=None, onStart=True)
        self.onCheckVersion(evt=None)
        
        # Log all events to 
        if self.logging == True:
            sys.stdin = self.view.panelPlots.log
            sys.stdout = self.view.panelPlots.log
            sys.stderr = self.view.panelPlots.log
      
    def makeVariables(self):
        """
        Pre-set variables
        """
        self.docsText = {}
        self.documents = []
        self.documentsDict = {}
        self.currentDoc = None
        self.currentCalibrationParams = []
        self.currentPath = None
        
    def onMSDirectory(self, e=None):
        dlg = wx.DirDialog(self.view, "Choose a MassLynx file:",
                           style=wx.DD_DEFAULT_STYLE)
            
        if dlg.ShowModal() == wx.ID_OK:
            print "You chose %s" % dlg.GetPath()
            # Check whether appropriate calibration file was selected
            path = self.checkIfRawFile(dlg.GetPath())
            if path is None: 
                msg = "Are you sure this was a MassLynx (.raw) file? Please load file in correct file format"
                dialogs.dlgBox(exceptionTitle='Please load MassLynx (.raw) file', 
                               exceptionMsg= msg,
                               type="Error")
                return
            # Update statusbar      
            self.view.SetStatusText(dlg.GetPath(), number = 4)
            # Get experimental parameters
            parameters = self.config.importMassLynxInfFile(path=dlg.GetPath())
            # Extract MS file
            ml.rawExtractMSdata(fileNameLocation=dlg.GetPath(), 
                                driftscopeLocation=self.config.driftscopePath)
            # Load MS data
            msDataX, msDataY = ml.rawOpenMSdata(path=dlg.GetPath())
            xlimits = [parameters['startMS'],parameters['endMS']]
            # Update status bar with MS range
            txt = ''.join(["MS range: ", num2str(parameters['startMS']), "-", 
                           num2str(parameters['endMS'])])
            self.view.SetStatusText(txt, 1)
            txt = ''.join(['MSMS: ', num2str(parameters['setMS'])])
            self.view.SetStatusText(txt, 2)
            
            # Add data to document 
            temp, idName = os.path.split(dlg.GetPath())
            idName = (''.join([idName])).encode('ascii', 'replace')   
            
            self.docs.title = idName
            self.currentDoc = idName # Currently plotted document
            self.docs.path = dlg.GetPath()
            self.docs.parameters = parameters
            self.docs.userParameters = self.config.userParameters
            self.docs.userParameters['date'] = getTime()
            self.docs.dataType = 'Type: MS'
            self.docs.fileFormat = 'Format: Waters (.raw)'
            self.docs.gotMS = True
            self.docs.massSpectrum = {'xvals':msDataX,
                                      'yvals':msDataY,
                                      'xlabels':'m/z (Da)',
                                      'xlimits':xlimits}

            # Plot 
            self.onPlotMS2(msDataX, msDataY, self.docs.lineColour, self.docs.style, 
                           xlimits=xlimits)

            # Append to list
            self.documentsDict[idName] = self.docs
            
            # Update documents tree
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
        dlg.Destroy()
        return None
    
    def onOpenMS(self, e=None):
        """ open MS file (without IMS) """
                
        dlg = wx.DirDialog(self.view, "Choose a MassLynx file:",
                           style=wx.DD_DEFAULT_STYLE)
             
        if dlg.ShowModal() == wx.ID_OK:
            print "You chose %s" % dlg.GetPath()     
            # Check whether appropriate calibration file was selected
            path = self.checkIfRawFile(dlg.GetPath())
            if path is None: 
                msg = "Are you sure this was a MassLynx (.raw) file? Please load file in correct file format"
                dialogs.dlgBox(exceptionTitle='Please load MassLynx (.raw) file', 
                               exceptionMsg= msg,
                               type="Error")
                return
            # Update statusbar      
            self.view.SetStatusText(dlg.GetPath(), number = 4)
             
            # Get experimental parameters
            parameters = self.config.importMassLynxInfFile(path=dlg.GetPath())
            xlimits = [parameters['startMS'],parameters['endMS']]
            # Extract MS data
            msDict = ml.extractMSdata(filename=str(dlg.GetPath()), 
                                      function=1, binData=True, 
                                      mzStart=self.config.binMSstart, 
                                      mzEnd=self.config.binMSend, 
                                      binsize=self.config.binMSbinsize)
             
            # Sum MS data
            msX, msY = af.sumMSdata(ydict=msDict)
            # Sum MS to get RT data
            rtX, rtY = af.sumMSdata2RT(ydict=msDict)
             
            # Add data to document 
            temp, idName = os.path.split(dlg.GetPath())
            idName = (''.join([idName])).encode('ascii', 'replace')   
             
            self.docs.title = idName
            self.currentDoc = idName # Currently plotted document
            self.docs.path = dlg.GetPath()
            self.docs.parameters = parameters
            self.docs.userParameters = self.config.userParameters
            self.docs.userParameters['date'] = getTime()
            self.docs.dataType = 'Type: MS'
            self.docs.fileFormat = 'Format: Waters (.raw)'
            self.docs.gotMS = True
            self.docs.massSpectrum = {'xvals':msX,
                                      'yvals':msY,
                                      'xlabels':'m/z (Da)',
                                      'xlimits':xlimits}
            self.docs.got1RT = True
            self.docs.RT = {'xvals':rtX, 
                            'yvals':rtY,
                            'xlabels':'Scans'}
 
            # Plot 
            self.onPlotMS2(msX, msY, self.docs.lineColour, self.docs.style, 
                           xlimits=xlimits)
 
            self.onPlotRT2(rtX, rtY, 'Scans', self.docs.lineColour, self.docs.style)
             
            # Append to list
            self.documentsDict[idName] = self.docs
             
            # Update documents tree
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)

        dlg.Destroy()
        return None
        
    def on1DIMSDirectory(self, e=None):

        # FIXME this function doesnt take into account normalization
        dlg = wx.DirDialog(self.view, "Choose a MassLynx file:",
                           style=wx.DD_DEFAULT_STYLE)
            
        if dlg.ShowModal() == wx.ID_OK:
            print "You chose %s" % dlg.GetPath()     
            # Check whether appropriate calibration file was selected
            path = self.checkIfRawFile(dlg.GetPath())
            if path is None: 
                msg = "Are you sure this was a MassLynx (.raw) file? Please load file in correct file format"
                dialogs.dlgBox(exceptionTitle='Please load MassLynx (.raw) file', 
                               exceptionMsg= msg,
                               type="Error")
                return
            # Update statusbar      
            self.view.SetStatusText(dlg.GetPath(), number = 4)
            # Get experimental parameters
            parameters = self.config.importMassLynxInfFile(path=dlg.GetPath())
            # Extract 1D IMS data
            ml.rawExtract1DIMSdata(fileNameLocation=dlg.GetPath(), 
                                   driftscopeLocation=self.config.driftscopePath)
            # Load 1D IMS data, normalized by default
            imsData1D =  ml.rawOpen1DRTdata(path=dlg.GetPath(), norm=True)
            xvalsDT = np.arange(1,len(imsData1D)+1)
            
            # Add data to document 
            temp, idName = os.path.split(dlg.GetPath())
            idName = (''.join([idName])).encode('ascii', 'replace')   
            
            self.docs.title = idName
            self.currentDoc = idName # Currently plotted document
            self.docs.path = dlg.GetPath()
            self.docs.parameters = parameters
            self.docs.userParameters = self.config.userParameters
            self.docs.userParameters['date'] = getTime()
            self.docs.dataType = 'Type: 1D IM-MS'
            self.docs.fileFormat = 'Format: Waters (.raw)'
            self.docs.got1DT = True
            self.docs.DT = {'xvals':xvalsDT, 
                            'yvals':imsData1D,
                            'xlabels':'Drift time (bins)',
                            'ylabels':'Intensity'}

            
            # Plot 
            self.onPlot1DIMS2(xvalsDT, imsData1D, 'Drift time (bins)', self.docs.lineColour, self.docs.style)
        
            # Append to list
            self.documentsDict[idName] = self.docs
            
            # Update documents tree
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
            dlg.Destroy()
            return None    
        
    def on2DIMSDirectory(self, e=None):
        dlg = wx.DirDialog(self.view, "Choose a MassLynx file:",
                           style=wx.DD_DEFAULT_STYLE)
        if self.config.dirname == '':
            pass
        else:
            dlg.SetPath(self.config.dirname)
            
        if dlg.ShowModal() == wx.ID_OK:
            print "You chose %s" % dlg.GetPath()
            # Check whether appropriate calibration file was selected
            path = self.checkIfRawFile(dlg.GetPath())
            if path is None: 
                msg = "Are you sure this was a MassLynx (.raw) file? Please load file in correct file format"
                dialogs.dlgBox(exceptionTitle='Please load MassLynx (.raw) file', 
                               exceptionMsg= msg,
                               type="Error")
                return
            # Update statusbar      
            self.view.SetStatusText(dlg.GetPath(), number = 4)
            # Get experimental parameters
            parameters = self.config.importMassLynxInfFile(path=dlg.GetPath())
            # Extract 2D arrays
            ml.rawExtract2DIMSdata(fileNameLocation=dlg.GetPath(),
                                   driftscopeLocation=self.config.driftscopePath)
            imsData2D = ml.rawOpen2DIMSdata(path=dlg.GetPath(), norm=False)
            xlabels = 1+np.arange(len(imsData2D[1,:]))
            ylabels = 1+np.arange(len(imsData2D[:,1]))
            
            # Add data to document 
            temp, idName = os.path.split(dlg.GetPath())
            idName = (''.join([idName])).encode('ascii', 'replace')   
            self.docs.title = idName
            self.currentDoc = idName # Currently plotted document
            self.docs.path = os.path.dirname(dlg.GetPath())
            self.docs.parameters = parameters
            self.docs.userParameters = self.config.userParameters
            self.docs.userParameters['date'] = getTime()
            self.docs.dataType = 'Type: 2D IM-MS'
            self.docs.fileFormat = 'Format: Waters (.raw)'
            self.docs.got2DIMS = True
            self.docs.IMS2D = {'zvals':imsData2D,
                                'xvals':xlabels,
                                'xlabels':'Scans',
                                'yvals':ylabels,
#                                 'yvals1D':imsData1D,
                                'ylabels':'Drift time (bins)',
                                'cmap':self.docs.colormap}
            
            # Append to list
            self.documentsDict[idName] = self.docs
            
            # Plot
            self.onPlot2DIMS2(imsData2D, xlabels, ylabels, 'Scans', 'Drift time (bins)', 
                              cmap=self.docs.colormap)
            
            # Update documents tree
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
        dlg.Destroy()
        return None
    
    def onThreading(self, evt, args, action='loadOrigami'):
        # Setup thread
        if action == 'loadOrigami':
            th = threading.Thread(target=self.onLoadOrigamiDataThreaded, args=(args,evt))
            
        elif action == 'saveFigs':
            target, path, kwargs = args
            th = threading.Thread(target=target.saveFigure2, args=(path,), kwargs=kwargs) 
            
        elif action == 'extractIons':
            th = threading.Thread(target=self.onExtract2DimsOverMZrangeMultipleThreaded, args=(evt,)) 
        
        # Start thread
        try:
            th.start()
        except:
            print('exception')
            
    def onOrigamiRawDirectory(self, evt):
        self.config.ciuMode = 'ORIGAMI'
        self.config.extractMode = 'singleIon'
         
        # Reset arrays
        dlg = wx.DirDialog(self.view, "Choose a MassLynx file:",
                           style=wx.DD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            if not self.config.threading:
                self.onLoadOrigamiDataThreaded(dlg.GetPath(), evt)
            else:
                args = dlg.GetPath()
                self.onThreading(evt, args, action='loadOrigami')


        dlg.Destroy()
        return None
    
    def onLoadOrigamiDataThreaded(self, path, evt, mode=None):
        """ Load data = threaded """
        tstart = time.clock()

        # Assign datatype. Have to do it here otherwise the evt value is incorrect for some unknown reason!
        if evt.GetId() == ID_openORIGAMIRawFile: dataType = 'Type: ORIGAMI'
        elif evt.GetId() == ID_openMassLynxRawFile: dataType = 'Type: MassLynx'
        elif evt.GetId() == ID_openIRRawFile: dataType = 'Type: Infrared'
        else: dataType = 'Type: ORIGAMI'    
        
        if mode != None: dataType = mode
        
        path = self.checkIfRawFile(path)
        if path is None: 
            msg = "Are you sure this was a MassLynx (.raw) file? Please load file in correct file format"
            dialogs.dlgBox(exceptionTitle='Please load MassLynx (.raw) file', 
                           exceptionMsg= msg,
                           type="Error")
            return
        print "You chose %s" % path   
        # Update statusbar      
        self.view.SetStatusText(path, number = 4)
        # Get experimental parameters
        parameters = self.config.importMassLynxInfFile(path=path)
        fileInfo = self.config.importMassLynxHeaderFile(path=path)
        
        # Get origami parameters
        oriParameters = self.config.importOrigamiConfFile(path=path)
        self.view.panelControls.onPopulateOrigamiVars(parameters=oriParameters)
        
        # Mass spectra
        ml.rawExtractMSdata(fileNameLocation=path, 
                            driftscopeLocation=self.config.driftscopePath)
        msDataX, msDataY = ml.rawOpenMSdata(path=path)
        xlimits = [parameters['startMS'],parameters['endMS']]
        
        # RT
        ml.rawExtractRTdata(fileNameLocation=path, 
                            driftscopeLocation=self.config.driftscopePath)
        rtDataY,rtDataYnorm = ml.rawOpenRTdata(path=path, 
                                               norm=True)   
        xvalsRT = np.arange(1,len(rtDataY)+1)
        
        # DT
        ml.rawExtract1DIMSdata(fileNameLocation=path, 
                               driftscopeLocation=self.config.driftscopePath)
        imsData1D =  ml.rawOpen1DRTdata(path=path,
                                                norm=self.config.normalize)
        xvalsDT = np.arange(1,len(imsData1D)+1)
        
        # 2D
        ml.rawExtract2DIMSdata(fileNameLocation=path,
                               driftscopeLocation=self.config.driftscopePath)
        imsData2D = ml.rawOpen2DIMSdata(path=path, norm=False)
        xlabels = 1+np.arange(len(imsData2D[1,:]))
        ylabels = 1+np.arange(len(imsData2D[:,1]))
        
        # Plot MZ vs DT
        if self.config.showMZDT:
            # m/z spacing, default is 1 Da
            nPoints = int((parameters['endMS'] - parameters['startMS'])/self.config.binSizeMZDT)
            # Extract and load data
            ml.rawExtractMZDTdata(fileNameLocation=path,
                                   driftscopeLocation=self.config.driftscopePath,
                                   mzStart=parameters['startMS'],
                                   mzEnd=parameters['endMS'],
                                   nPoints=nPoints)
            
            imsDataMZDT = ml.rawOpenMZDTdata(path=path, norm=False)
            # Get x/y axis 
            xlabelsMZDT = np.linspace(parameters['startMS'],parameters['endMS'], 
                                      nPoints, endpoint=True)
            ylabelsMZDT = 1+np.arange(len(imsDataMZDT[:,1]))
            # Plot
            self.onPlotMZDT(imsDataMZDT,xlabelsMZDT,ylabelsMZDT,'m/z',
                            'Drift time (bins)', self.docs.colormap)
        
        
        # Update status bar with MS range
        txt = ''.join(["MS range: ", num2str(parameters['startMS']), "-", 
                       num2str(parameters['endMS'])])
        self.view.SetStatusText(txt, 1)
        txt = ''.join(['MSMS: ', num2str(parameters['setMS'])])
        self.view.SetStatusText(txt, 2)
        tend= time.clock()
        self.view.SetStatusText('Total time to open file: %.2gs' % (tend-tstart), 3)
             

        # Add info to document and data to file
        temp, idName = os.path.split(path)
        idName = (''.join([idName])).encode('ascii', 'replace')   
        self.docs = doc()             
        self.docs.title = idName
        self.currentDoc = idName # Currently plotted document
        self.docs.path = path
        self.docs.dataType = dataType
        self.docs.fileFormat = 'Format: Waters (.raw)'
        self.docs.fileInformation = fileInfo
        self.docs.parameters = parameters
        self.docs.userParameters = self.config.userParameters
        self.docs.userParameters['date'] = getTime()
        self.docs.gotMS = True
        self.docs.massSpectrum = {'xvals':msDataX,
                                  'yvals':msDataY,
                                  'xlabels':'m/z (Da)',
                                  'xlimits':xlimits}
        self.docs.got1RT = True
        self.docs.RT = {'xvals':xvalsRT, 
                        'yvals':rtDataYnorm,
                        'xlabels':'Scans'}
        self.docs.got1DT = True
        self.docs.DT = {'xvals':xvalsDT, 
                        'yvals':imsData1D,
                        'xlabels':'Drift time (bins)',
                        'ylabels':'Intensity'}
        self.docs.got2DIMS = True
        self.docs.IMS2D = {'zvals':imsData2D,
                           'xvals':xlabels,
                           'xlabels':'Scans',
                           'yvals':ylabels,
                           'yvals1D':imsData1D,
                           'ylabels':'Drift time (bins)',
                           'cmap':self.docs.colormap,
                           'charge':1}
        if self.config.showMZDT:
            self.docs.gotDTMZ = True
            self.docs.DTMZ = {'zvals':imsDataMZDT,
                              'xvals':xlabelsMZDT,
                              'yvals':ylabelsMZDT,
                              'xlabels':'m/z',
                              'ylabels':'Drift time (bins)',
                              'cmap':self.docs.colormap}

        # Plot 
        self.onPlotMS2(msDataX, msDataY, self.docs.lineColour, self.docs.style, 
                       xlimits=xlimits)
        self.onPlot1DIMS2(xvalsDT, imsData1D, 'Drift time (bins)', self.docs.lineColour, self.docs.style)
        self.onPlotRT2(xvalsRT, rtDataYnorm, 'Scans', self.docs.lineColour, self.docs.style)
        self.plot2Ddata2(data=[imsData2D,xlabels,'Scans',ylabels,'Drift time (bins)', self.docs.colormap])
        
#             if self.config.showMZDT:
#                 self.plot2Ddata2(data=[imsData2D,xlabels,'Scans',ylabels,'Drift time (bins)', self.docs.colormap])
        
        # Append to list
        self.documentsDict[idName] = self.docs
        # Update documents tree
        self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)

    def onMSbinaryFile(self, e):
        dlg = wx.FileDialog(self.view, "Choose a binary MS file:", wildcard = "*.1dMZ" ,
                           style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            print "You chose %s" % dlg.GetPath()
            # For now this is read as TRUE - need to add other normalization methods
            msDataX, msDataY = ml.rawOpenMSdata(fileNameLocation=dlg.GetPath(),
                                                                norm=True)
            # Update status bar with MS range
            self.config.msStart = np.min(msDataX)
            self.config.msEnd = np.max(msDataX)
            txt = ''.join(["MS range: ", num2str(self.config.msStart), " - ", 
                           num2str(self.config.msEnd)])
            self.view.SetStatusText(txt, 1)
            self.view.SetStatusText(self.config.rawName, number = 4)
            
            # Add data to document 
            temp, idName = os.path.split(dlg.GetPath())
            idName = (''.join([idName])).encode('ascii', 'replace')   
            self.docs = doc() 
            self.docs.title = idName
            self.currentDoc = idName # Currently plotted document
            self.docs.userParameters = self.config.userParameters
            self.docs.userParameters['date'] = getTime()
            self.docs.path = os.path.dirname(dlg.GetPath())
            self.docs.dataType = 'Type: MS'
            self.docs.fileFormat = 'Format: Waters Binary File (.1dMZ)'
            self.docs.gotMS = True
            self.docs.massSpectrum = {'xvals':msDataX,
                                      'yvals':msDataY,
                                      'xlabels':'m/z (Da)',
                                      'xlimits':xlimits}
            
            # Append to list
            self.documentsDict[idName] = self.docs
            
            # Plot 
            self.onPlotMS2(msDataX, msDataY, self.docs.lineColour, self.docs.style, 
                           xlimits=xlimits)
            
            # Update documents tree
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
            
        dlg.Destroy()
        
    def on1DbinaryFile(self, e):
        dlg = wx.FileDialog(self.view, "Choose a binary MS file:", wildcard = "*.1dDT" ,
                           style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            print "You chose %s" % dlg.GetPath()      
            imsData1D =  ml.rawOpen1DRTdata(fileNameLocation=dlg.GetPath(),
                                                    norm=self.config.normalize)  
            xvalsDT = np.arange(1,len(imsData1D)+1)
            # Update statusbar      
            self.view.SetStatusText(dlg.GetPath(), number = 4)
            # Add data to document 
            temp, idName = os.path.split(dlg.GetPath())
            idName = (''.join([idName])).encode('ascii', 'replace')   
            self.docs = doc() 
            self.docs.title = idName
            self.currentDoc = idName # Currently plotted document
            self.docs.userParameters = self.config.userParameters
            self.docs.userParameters['date'] = getTime()
            self.docs.path = os.path.dirname(dlg.GetPath())
            self.docs.dataType = 'Type: 1D IM-MS'
            self.docs.fileFormat = 'Format: Waters Binary File (.1dDT)'
            self.docs.got1DT = True
            self.docs.DT = {'xvals':xvalsDT, 
                            'yvals':imsData1D,
                            'xlabels':'Drift time (bins)',
                            'ylabels':'Intensity'}
            # Append to listef getImageFilename
            self.documentsDict[idName] = self.docs
            
            self.onPlot1DIMS2(xvalsDT, imsData1D, 'Drift time (bins)', self.docs.lineColour, self.docs.style)

            # Update documents tree
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
            dlg.Destroy()
        dlg.Destroy()
        
    def on2DbinaryFile(self, e):
        dlg = wx.FileDialog(self.view, "Choose a binary MS file:", wildcard = "*.2dRTDT" ,
                           style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            print "You chose %s" % dlg.GetPath()   
            imsData2D = ml.rawOpen2DIMSdata(fileNameLocation=dlg.GetPath(), norm=False)
            xlabels = 1+np.arange(len(imsData2D[1,:]))
            ylabels = 1+np.arange(len(imsData2D[:,1]))
            # Pre-set data for other calculations
            self.plot2Ddata2(data=[imsData2D,xlabels,'Scans',ylabels,'Drift time (bins)'])
            # Update statusbar      
            self.view.SetStatusText(dlg.GetPath(), number = 4)
            
            # Add data to document 
            temp, idName = os.path.split(dlg.GetPath())
            idName = (''.join([idName])).encode('ascii', 'replace')   
            self.docs = doc() 
            self.docs.title = idName
            self.currentDoc = idName # Currently plotted document
            self.docs.userParameters = self.config.userParameters
            self.docs.userParameters['date'] = getTime()
            self.docs.path = os.path.dirname(dlg.GetPath())
            self.docs.dataType = 'Type: 2D IM-MS'
            self.docs.fileFormat = 'Format: Waters Binary File (.2dRTDT)'
            self.docs.got2DIMS = True
            self.docs.IMS2D = {'zvals':imsData2D,
                                'xvals':xlabels,
                                'xlabels':'Scans',
                                'yvals':ylabels,
                                'ylabels':'Drift time (bins)',
                                'cmap':self.docs.colormap}
            # Append to list
            self.documentsDict[idName] = self.docs
            
            # Update documents tree
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
            
        dlg.Destroy()
   
    def onExtract2DimsOverMZrangeMultipleThreaded(self, evt):
        """ extract multiple ions = threaded """
        
        evtID = evt.GetId()
        if evtID == ID_extractNewIon:
            event = 'new'
        elif evtID == ID_extractSelectedIon:
            event = 'selected'
        else:
            event = 'all'
        
        self.config.extractMode = 'multipleIons'
        tempList = self.view.panelMultipleIons.topP.peaklist # shortcut
        for row in range(tempList.GetItemCount()):
            filename = tempList.GetItem(row, self.config.peaklistColNames['filename']).GetText().encode('ascii', 'replace')
            # Check if the ion has been assigned a filename
            if filename == '': 
                self.view.SetStatusText('File name column was empty. Using the current document name instead', 3)
                tempList.SetStringItem(index=row, col=5, label=self.currentDoc)
                filename = self.currentDoc
            else: pass
            self.docs = self.documentsDict[filename]
            # Extract information from the table
            mzStart= str2num(tempList.GetItem(row,).GetText())
            mzEnd = str2num(tempList.GetItem(row,1).GetText())
            label = tempList.GetItem(row,8).GetText()
            charge = str2num(tempList.GetItem(row,2).GetText())
            
            if charge == None: charge = 'None'
            path = self.docs.path
            
            # Create range name
            rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
            # Reverse values in case they are wrong way round
            if mzEnd < mzStart:
                tempList.SetStringItem(index=row, col=0, label=num2str(mzEnd))
                tempList.SetStringItem(index=row, col=1, label=nun2str(mzStart))
                # Now get those values
                mzStart= str2num(tempList.GetItem(row,0).GetText())
                mzEnd = str2num(tempList.GetItem(row,1).GetText())
                
            # Check that the mzStart/mzEnd are above the acquire MZ value 
            if mzStart < min(self.docs.massSpectrum['xvals']): 
                tempList.ToggleItem(index=row)
                msg = ''.join(["Ion: ", rangeName, " was below the minimum value in the mass spectrum. Consider removing it from the list"])
                self.view.SetStatusText(msg, 3)
                continue
            # Check whether this ion was already extracted
            if (evt.GetId() == ID_extractNewIon or event == 'new') and self.docs.gotExtractedIons:
                try:
                    if self.docs.IMS2Dions[rangeName]:
                        msg = ''.join(["Data was already extracted for the : ", rangeName, " ion"])
                        print(msg)
                        continue
                except KeyError: pass
            elif (evt.GetId() == ID_extractNewIon or event == 'new') and self.docs.gotCombinedExtractedIons:
                try:
                    if self.docs.IMS2DCombIons[rangeName]:
                        msg = ''.join(["Data was already extracted for the : ", rangeName, " ion"])
                        print(msg)
                        continue
                except KeyError: pass
            
            # Extract selected ions
            if (evt.GetId() == ID_extractSelectedIon  or event == 'selected') and not tempList.IsChecked(index=row):
                continue
                
            msg = ''.join(['Extracted: ',str(row+1), "/",str(tempList.GetItemCount())])

            if self.docs.dataType == 'Type: ORIGAMI':
                # 1D 
                ml.rawExtract1DIMSdata(fileNameLocation=path, driftscopeLocation=self.config.driftscopePath,
                                       mzStart=mzStart, mzEnd=mzEnd)
                try:
                    imsData1D =  ml.rawOpen1DRTdata(path=path, norm=False)
                except IOError:
                    dialogs.dlgBox(exceptionTitle='Missing folder', 
                                   exceptionMsg= "Failed to open the file - most likely because this file does not exist.",
                                   type="Error")
                    return
                # RT 
                ml.rawExtractRTdata(fileNameLocation=path, driftscopeLocation=self.config.driftscopePath,
                                    mzStart=mzStart, mzEnd=mzEnd)
                rtDataY = ml.rawOpenRTdata(path=path, norm=False)    
                # 2D
                ml.rawExtract2DIMSdata(fileNameLocation=path, driftscopeLocation=self.config.driftscopePath,
                                       mzStart=mzStart, mzEnd=mzEnd)
                imsData2D = None
                imsData2D = ml.rawOpen2DIMSdata(path=path, norm=False)
                xlabels = 1+np.arange(len(imsData2D[1,:]))
                ylabels = 1+np.arange(len(imsData2D[:,1]))
                # Update limits
                self.setXYlimitsRMSD2D(xlabels, ylabels)
                
                # Get height of the peak
                ms = self.docs.massSpectrum
                ms = np.flipud(np.rot90(np.array([ms['xvals'], ms['yvals']])))
                mzYMax = self.view.getYvalue(msList=ms, mzStart=mzStart, mzEnd=mzEnd)
                tempList.SetStringItem(index=row, col=7, label=str(mzYMax))
                # Add data to document object
                self.docs.gotExtractedIons = True
                self.docs.IMS2Dions[rangeName] = {'zvals':imsData2D,
                                                  'xvals':xlabels,
                                                  'xlabels':'Scans',
                                                  'yvals':ylabels,
                                                  'ylabels':'Drift time (bins)',
                                                  'cmap':self.docs.colormap,
                                                  'yvals1D':imsData1D,
                                                  'yvalsRT':rtDataY,
                                                  'title':label,
                                                  'label':label,
                                                  'charge':charge,
                                                  'xylimits':[mzStart,mzEnd,mzYMax]}
                # Update file list
                self.documentsDict[filename] = self.docs
                self.view.panelDocuments.topP.documents.addDocument(docData = self.docs,
                                                                    expandItem=self.documentsDict[self.docs.title].IMS2Dions[rangeName])
                 
            # Check if manual dataset
            elif self.docs.dataType == 'Type: MANUAL':
                # Shortcut to the file list
                nameList = self.view.panelMML.topP.filelist # List with MassLynx file information
                # Sort data regardless of what user did  
                self.view.panelMML.topP.OnSortByColumn(column=1, overrideReverse=True)
                tempDict = {}
                for item in xrange(nameList.GetItemCount()):
                    # Determine whether the title of the document matches the title of the item in the table
                    # if it does not, skip the row
                    docValue = nameList.GetItem(item,2).GetText()
                    if docValue != self.docs.title: continue
                    
                    nameValue = nameList.GetItem(item,0).GetText()
                    pathValue = self.docs.multipleMassSpectrum[nameValue]['path']
    
                    ml.rawExtract1DIMSdata(fileNameLocation=pathValue, driftscopeLocation=self.config.driftscopePath,
                                           mzStart=mzStart, mzEnd=mzEnd)
                    imsData1D =  ml.rawOpen1DRTdata(path=pathValue, norm=self.config.normalize)
                    # Get height of the peak
                    ms = self.docs.massSpectrum
                    ms = np.flipud(np.rot90(np.array([ms['xvals'], ms['yvals']])))
                    mzYMax = self.view.getYvalue(msList=ms, mzStart=mzStart, mzEnd=mzEnd)
                    tempList.SetStringItem(index=row, col=self.config.peaklistColNames['intensity'], 
                                           label=str(mzYMax))
                    tempList.SetStringItem(index=row, col=self.config.peaklistColNames['method'], 
                                           label='Manual')
                    # Create temporary dictionary for all IMS data
                    tempDict[nameValue] = [imsData1D]
                    # Add 1D data to 1D data container
                    newName = ''.join([rangeName,', File: ',nameValue])
                    self.docs.gotExtractedDriftTimes = True
                    labelX1D = 'Drift time (bins)'
                    xvals1D = 1+np.arange(len(imsData1D))
                    self.docs.IMS1DdriftTimes[newName] = {'xvals':xvals1D,
                                                          'yvals':imsData1D,
                                                          'xlabels':labelX1D,
                                                          'ylabels':'Intensity',
                                                          'charge':charge,
                                                          'xylimits':[mzStart,mzEnd,mzYMax],
                                                          'filename':nameValue}
                    
                # Combine the contents in the dictionary - assumes they are ordered!
                counter = 0 # needed to start off
                xlabelsActual = []
                for item in xrange(nameList.GetItemCount()):
                    # Determine whether the title of the document matches the title of the item in the table
                    # if it does not, skip the row
                    docValue = nameList.GetItem(item,2).GetText()
                    if docValue != self.docs.title: continue
                    key = nameList.GetItem(item,0).GetText()
                    if counter == 0:
                        tempArray = tempDict[key][0]
                        xLabelLow = self.docs.multipleMassSpectrum[key]['trap'] # first iteration so first value
                        xlabelsActual.append(self.docs.multipleMassSpectrum[key]['trap'])
                        counter += 1
                    else:
                        imsList = tempDict[key][0]
                        tempArray = np.concatenate((tempArray, imsList), axis=0)
                        xlabelsActual.append(self.docs.multipleMassSpectrum[key]['trap'])
                        counter += 1
                        
                # Reshape data to form a 2D array of size 200 x number of files
                imsData2D = None
                imsData2D = tempArray.reshape((200, int(counter)), order='F')
                # Combine 2D array into 1D 
                rtDataY = np.sum(imsData2D, axis=0)
                imsData1D = np.sum(imsData2D, axis=1).T
                # Get the x-axis labels
                xLabelHigh = self.docs.multipleMassSpectrum[key]['trap'] # after the loop has finished, so last value
                xlabels = np.linspace(xLabelLow, xLabelHigh, num=counter)
                ylabels = 1+np.arange(len(imsData2D[:,1]))
                # Update limits
                self.setXYlimitsRMSD2D(xlabels, ylabels)
                # Add data to the document
                self.docs.gotCombinedExtractedIons = True               
                self.docs.IMS2DCombIons[rangeName] = {'zvals':imsData2D,
                                                       'xvals':xlabels,
                                                       'xlabels':'Collision Voltage (V)',
                                                       'yvals':ylabels,
                                                       'ylabels':'Drift time (bins)',
                                                       'yvals1D':imsData1D,
                                                       'yvalsRT':rtDataY,
                                                       'cmap':self.docs.colormap,
                                                       'title':label,
                                                       'label':label,
                                                       'charge':charge,
                                                       'xylimits':[mzStart,mzEnd,mzYMax]}
    
                # Update file list
                self.documentsDict[filename] = self.docs
                self.view.panelDocuments.topP.documents.addDocument(docData = self.docs,
                                                                    expandItem=self.documentsDict[self.docs.title].IMS2DCombIons[rangeName])
            elif self.docs.dataType == 'Type: Infrared':
                # 2D
                ml.rawExtract2DIMSdata(fileNameLocation=path, driftscopeLocation=self.config.driftscopePath,
                                       mzStart=mzStart, mzEnd=mzEnd)
                
                imsData2D = ml.rawOpen2DIMSdata(path=path, norm=False)
                dataSplit, xAxisLabels, yAxisLabels, dataRT, data1DT  = af.combineIRdata(inputData=imsData2D, 
                                                                                         threshold=2000, noiseLevel=500)

                # Get height of the peak
                ms = self.docs.massSpectrum
                ms = np.flipud(np.rot90(np.array([ms['xvals'], ms['yvals']])))
                mzYMax = self.view.getYvalue(msList=ms, mzStart=mzStart, mzEnd=mzEnd)
                tempList.SetStringItem(index=row, col=7, label=str(mzYMax))
                # Add data to document object
                self.docs.gotExtractedIons = True
                self.docs.IMS2Dions[rangeName] = {'zvals':dataSplit,
                                                  'xvals':xAxisLabels,
                                                  'xlabels':u'Wavenumber (cm⁻¹)',
                                                  'yvals':yAxisLabels,
                                                  'ylabels':'Drift time (bins)',
                                                  'cmap':self.docs.colormap,
                                                  'yvals1D':data1DT,
                                                  'yvalsRT':dataRT,
                                                  'title':label,
                                                  'label':label,
                                                  'charge':charge,
                                                  'xylimits':[mzStart,mzEnd,mzYMax]}
                # Update file list
                self.documentsDict[filename] = self.docs
                self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
            else: return
            self.view.SetStatusText(msg, 4)
        self.view.SetStatusText("", 4)
    
    def onExtract2DimsOverMZrangeMultiple(self, evt):
        """
        Extract 2D array for each m/z range specified in the table
        """
      
        if not self.config.threading:
            self.onExtract2DimsOverMZrangeMultipleThreaded(evt)
        else:
            args = ()
            self.onThreading(evt, args, action='extractIons')
            
    def onExtractRTforMZDTrange(self, mzStart, mzEnd, dtStart, dtEnd):
        """ Function to extract RT data for specified MZ/DT region """
        
        self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        if self.currentDoc == 'Current documents': return
        self.docs = self.documentsDict[self.currentDoc]
        
        # Extract data
        ml.rawExtractRTdata(fileNameLocation=str(self.docs.path), 
                            driftscopeLocation=self.config.driftscopePath,
                            mzStart=mzStart, mzEnd=mzEnd, dtStart=dtStart, dtEnd=dtEnd)
        # Load data
        rtDataY = ml.rawOpenRTdata(path=str(self.docs.path), norm=False)
        rtDataX = np.arange(1,len(rtDataY)+1)  
        self.onPlotRT2(rtDataX, rtDataY, 'Scans', self.docs.lineColour, self.docs.style)
        
        msg = ''.join(['Extracted RT data for m/z: ', str(mzStart),'-',str(mzEnd),
                       ' | dt: ',str(dtStart), '-',str(dtEnd)])
        self.view.SetStatusText(msg, 3)
               
    def onExtractMSforRTrange(self, startScan=None, endScan=None, evt=None):
        """ Function to extract MS data for specified RT region """
        
        self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        if self.currentDoc == 'Current documents': return
        self.docs = self.documentsDict[self.currentDoc]
        
        try:
            scantime = self.docs.parameters['scanTime']
        except: 
            scantime = None
            
        itemName = ''.join(['Scans: ',str(startScan),'-',str(endScan)])
        
        if not self.config.binMSfromRT and scantime != None:
            rtStart = round(startScan*(scantime/60),2)
            rtEnd = round(endScan*(scantime/60),2)
            # Mass spectra
            ml.rawExtractMSdata(fileNameLocation=str(self.docs.path), 
                                driftscopeLocation=self.config.driftscopePath,
                                rtStart=rtStart,
                                rtEnd=rtEnd)
            msX, msY = ml.rawOpenMSdata(path=str(self.docs.path))
            xlimits = [self.docs.parameters['startMS'], self.docs.parameters['endMS']]
        else:
            msDict = ml.extractMSdata(filename=str(self.docs.path), 
                                      startScan=startScan, endScan=endScan, 
                                      function=1, binData=True, 
                                      mzStart=self.config.binMSstart, 
                                      mzEnd=self.config.binMSend, 
                                      binsize=self.config.binMSbinsize)
            
            msX, msY = af.sumMSdata(ydict=msDict)
            xlimits = [self.config.binMSstart, self.config.binMSend]
            
#         if scantime != None:
#             rtStart = round(startScan*(scantime/60),2)
#             rtEnd = round(endScan*(scantime/60),2)
#             # Also extract 1D for specified region
#             ml.rawExtract1DIMSdata(fileNameLocation=self.docs.path, 
#                                    driftscopeLocation=self.config.driftscopePath,
#                                    rtStart=rtStart, rtEnd=rtEnd)
#             imsData1D =  ml.rawOpen1DRTdata(path=self.docs.path,
#                                             norm=self.config.normalize)
#             xvalsDT = np.arange(1,len(imsData1D)+1)
#             
# #             newName = ''.join([rangeName,', File: ',nameValue])
#             labelX1D = 'Drift time (bins)'
#             self.docs.gotExtractedDriftTimes = True
#             self.docs.IMS1DdriftTimes[itemName] = {'xvals':xvalsDT,
#                                                    'yvals':imsData1D,
#                                                    'xlabels':labelX1D,
#                                                    'ylabels':'Intensity'}
# #                                                    'charge':charge,
# #                                                   'xylimits':[mzStart,mzEnd,mzYMax],
# #                                                     'filename':nameValue
                                                    
                        
        # Add data to dictionary
        self.docs.gotMultipleMS = True
        self.docs.multipleMassSpectrum[itemName] = {'xvals':msX, 
                                                    'yvals':msY,
                                                    'range':[startScan,endScan],
                                                    'xlabels':'m/z (Da)',
                                                    'xlimits':xlimits}
        self.documentsDict[self.docs.title] = self.docs
        self.view.panelDocuments.topP.documents.addDocument(docData = self.docs, 
                                                            expandItem=self.documentsDict[self.docs.title].multipleMassSpectrum[itemName])   

        # Plot MS
        self.onPlotMS2(msX, msY, self.docs.lineColour, self.docs.style, 
                       xlimits=xlimits)
        # Set status
        msg = ''.join(['Extracted MS data for rt: ', str(startScan),'-',str(endScan)])
        self.view.SetStatusText(msg, 3)
                
    def onCombineCEvoltagesMultiple(self, evt):
        self.config.extractMode = 'multipleIons'
        
        # Get event ID
        if evt != None:
            if evt.GetId() == ID_combineCEscansSelectedIons:
                combMode = 'selected'
            elif evt.GetId() == ID_combineCEscans:
                combMode = 'all'
        
        # Shortcut to ion table
        tempList = self.view.panelMultipleIons.topP.peaklist 
        documentList = []
        
        # Make a list of current documents
        for row in range(tempList.GetItemCount()):
            
            # Check which mode was selected
            if evt.GetId() == ID_combineCEscans: pass
            elif evt.GetId() == ID_combineCEscansSelectedIons:
                if not tempList.IsChecked(index=row): 
                    continue 

            self.currentDoc = tempList.GetItem(itemId=row, 
                                               col=self.config.peaklistColNames['filename']).GetText()
            # Check that data was extracted first
            if self.currentDoc == '':
                msg = "Please extract data first"
                dialogs.dlgBox(exceptionTitle='Extract data first', 
                               exceptionMsg= msg,
                               type="Warning")
                continue
            # Get document
            self.docs = self.documentsDict[self.currentDoc]
            
            # Check that this data was opened in ORIGAMI mode and has extracted data
            if self.docs.dataType == 'Type: ORIGAMI' and self.docs.gotExtractedIons == True:
                zvals = self.docs.IMS2Dions
            else: 
                msg = "Data was not extracted yet. Please extract before continuing."
                dialogs.dlgBox(exceptionTitle='Missing data', 
                               exceptionMsg= msg,
                               type="Error")
                continue        

                
            # Extract ion name
            mzStart = tempList.GetItem(itemId=row, col=0).GetText()
            mzEnd = tempList.GetItem(itemId=row, col=1).GetText()
            selectedItem = ''.join([str(mzStart),'-',str(mzEnd)])
            
        # Combine data
        # LINEAR METHOD
            if self.config.acqMode == 'Linear':
                # Check that the user filled in appropriate parameters
                if ((evt.GetId() == ID_recalculateORIGAMI or self.config.useInternalParamsCombine)
                     and self.docs.gotCombinedExtractedIons):
                    self.config.startScan = self.docs.IMS2DCombIons[selectedItem]['parameters']['firstVoltage']
                    self.config.startVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['startV']
                    self.config.endVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['endV']
                    self.config.stepVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['stepV']
                    self.config.scansPerVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['spv']
                # Ensure that config is not missing variabels
                elif not any([self.config.startScan,self.config.startVoltage,self.config.endVoltage,
                        self.config.stepVoltage,self.config.scansPerVoltage]):
                    self.view.SetStatusText('Cannot perform action. Missing fields in the ORIGAMI parameters panel', 3)
                    return
                
                # Check if ion/file has specified ORIGAMI method
                if tempList.GetItem(itemId=row, col=6).GetText() == '':
                    tempList.SetStringItem(index=row, col=6, label=self.config.acqMode)
                elif (tempList.GetItem(itemId=row, col=6).GetText() == self.config.acqMode and 
                      self.config.overrideCombine):
                    pass
                # Check if using internal parameters and item is checked
                elif self.config.useInternalParamsCombine and tempList.IsChecked(index=row):
                    pass
                else: continue # skip
                # Combine data
                imsData2D, scanList, parameters = af.combineCEscansLinear(imsDataInput=zvals[selectedItem]['zvals'], 
                                                              firstVoltage=self.config.startScan,
                                                              startVoltage=self.config.startVoltage, 
                                                              endVoltage=self.config.endVoltage,
                                                              stepVoltage=self.config.stepVoltage, 
                                                              scansPerVoltage=self.config.scansPerVoltage)
            # EXPONENTIAL METHOD
            elif self.config.acqMode == 'Exponential': 
                # Check that the user filled in appropriate parameters
                if ((evt.GetId() == ID_recalculateORIGAMI or self.config.useInternalParamsCombine)
                     and self.docs.gotCombinedExtractedIons):
                    self.config.startScan = self.docs.IMS2DCombIons[selectedItem]['parameters']['firstVoltage']
                    self.config.startVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['startV']
                    self.config.endVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['endV']
                    self.config.stepVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['stepV']
                    self.config.scansPerVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['spv']
                    self.config.expIncrement = self.docs.IMS2DCombIons[selectedItem]['parameters']['expIncrement']
                    self.config.expPercentage = self.docs.IMS2DCombIons[selectedItem]['parameters']['expPercent']
                # Ensure that config is not missing variabels
                elif not any([self.config.startScan,self.config.startVoltage,self.config.endVoltage,
                        self.config.stepVoltage,self.config.scansPerVoltage,self.config.expIncrement,
                        self.config.expPercentage]):
                    self.view.SetStatusText('Cannot perform action. Missing fields in the ORIGAMI parameters panel', 3)
                    return
                
                # Check if ion/file has specified ORIGAMI method
                if tempList.GetItem(itemId=row, col=6).GetText() == '':
                    tempList.SetStringItem(index=row, col=6, label=self.config.acqMode)
                elif (tempList.GetItem(itemId=row, col=6).GetText() == self.config.acqMode and 
                      self.config.overrideCombine):
                    pass
                # Check if using internal parameters and item is checked
                elif self.config.useInternalParamsCombine and tempList.IsChecked(index=row):
                    pass
                else: continue # skip
                imsData2D, scanList, parameters = af.combineCEscansExponential(imsDataInput=zvals[selectedItem]['zvals'], 
                                                                firstVoltage=self.config.startScan,
                                                                startVoltage=self.config.startVoltage, 
                                                                endVoltage=self.config.endVoltage,
                                                                stepVoltage=self.config.stepVoltage, 
                                                                scansPerVoltage=self.config.scansPerVoltage,
                                                                expIncrement=self.config.expIncrement,
                                                                expPercentage=self.config.expPercentage)
            # FITTED/BOLTZMANN METHOD
            elif self.config.acqMode == 'Fitted': 
                # Check that the user filled in appropriate parameters
                if ((evt.GetId() == ID_recalculateORIGAMI or self.config.useInternalParamsCombine)
                     and self.docs.gotCombinedExtractedIons):
                    self.config.startScan = self.docs.IMS2DCombIons[selectedItem]['parameters']['firstVoltage']
                    self.config.startVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['startV']
                    self.config.endVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['endV']
                    self.config.stepVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['stepV']
                    self.config.scansPerVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['spv']
                    self.config.fittedScale = self.docs.IMS2DCombIons[selectedItem]['parameters']['dx']
                # Ensure that config is not missing variabels
                elif not any([self.config.startScan,self.config.startVoltage,self.config.endVoltage,
                        self.config.stepVoltage,self.config .scansPerVoltage,self.config.fittedScale]):
                    self.view.SetStatusText('Cannot perform action. Missing fields in the ORIGAMI parameters panel', 3)
                    return
                
                # Check if ion/file has specified ORIGAMI method
                if tempList.GetItem(itemId=row, col=6).GetText() == '':
                    tempList.SetStringItem(index=row, col=6, label=self.config.acqMode)
                elif (tempList.GetItem(itemId=row, col=6).GetText() == self.config.acqMode and 
                      self.config.overrideCombine):
                    pass
                # Check if using internal parameters and item is checked
                elif self.config.useInternalParamsCombine and tempList.IsChecked(index=row):
                    pass
                else: continue # skip
                imsData2D, scanList, parameters = af.combineCEscansFitted(imsDataInput=zvals[selectedItem]['zvals'], 
                                                           firstVoltage=self.config.startScan,
                                                           startVoltage=self.config.startVoltage, 
                                                           endVoltage=self.config.endVoltage,
                                                           stepVoltage=self.config.stepVoltage, 
                                                           scansPerVoltage=self.config.scansPerVoltage,
                                                           dx=self.config.fittedScale)
            # USER-DEFINED/LIST METHOD
            elif self.config.acqMode == 'User-defined':
                # Check that the user filled in appropriate parameters
                if evt.GetId() == ID_recalculateORIGAMI or self.config.useInternalParamsCombine:
                    self.config.startScan = self.docs.IMS2DCombIons[selectedItem]['parameters']['firstVoltage']
                    self.config.origamiList = self.docs.IMS2DCombIons[selectedItem]['parameters']['inputList']
                # Ensure that config is not missing variabels
                elif (len(self.config.origamiList) == 0 or 
                    (self.config.origamiList[:,0].shape != self.config.origamiList[:,1].shape) or 
                    not self.config.startScan):
                    self.view.SetStatusText('Cannot perform action. Missing fields in the ORIGAMI parameters panel', 3)
                    return 
                
                # Check if ion/file has specified ORIGAMI method
                if tempList.GetItem(itemId=row, col=6).GetText() == '':
                    tempList.SetStringItem(index=row, col=6, label=self.config.acqMode)
                elif (tempList.GetItem(itemId=row, col=6).GetText() == self.config.acqMode and 
                      self.config.overrideCombine):
                    pass
                # Check if using internal parameters and item is checked
                elif self.config.useInternalParamsCombine and tempList.IsChecked(index=row):
                    pass
                else: continue # skip
                imsData2D, xlabels, scanList, parameters = af.combineCEscansUserDefined(imsDataInput=zvals[selectedItem]['zvals'], 
                                                                   firstVoltage=self.config.startScan, 
                                                                   inputList=self.config.origamiList)
            else:
                print('TODO: add other methods')
                
                return
            if imsData2D[0] is None:
                msg1 = "With your current input, there would be too many scans in your file!"
                msg2 = ''.join(["There are: ", str(imsData2D[2]),
                                 " scans in your file and your settings suggest there should be: ", 
                                 str(int(imsData2D[1]))])
                msg = ''.join([msg1, " ", msg2])
                dialogs.dlgBox(exceptionTitle='Are your settings correct?', exceptionMsg= msg,
                               type="Warning")
                continue
                
            # Add x-axis and y-axis labels
            if self.config.acqMode != 'User-defined':
                xlabels = np.arange(self.config.startVoltage, 
                                    (self.config.endVoltage+self.config.stepVoltage), 
                                    self.config.stepVoltage)
            # Y-axis is bins by default
            ylabels = np.arange(1,201,1)
            # Combine 2D array into 1D 
            imsData1D = np.sum(imsData2D, axis=1).T
            yvalsRT = np.sum(imsData2D, axis=0)
            # Check if item has labels, alpha, charge
            charge = zvals[selectedItem].get('charge', None)
            cmap = zvals[selectedItem].get('cmap', self.docs.colormap)
            label = zvals[selectedItem].get('label', None)
            alpha = zvals[selectedItem].get('alpha', None)

            # Add 2D data to document object
            self.docs.gotCombinedExtractedIons = True            
            self.docs.IMS2DCombIons[selectedItem] = {'zvals':imsData2D,
                                                     'xvals':xlabels,
                                                     'xlabels':'Collision Voltage (V)',
                                                     'yvals':ylabels,
                                                     'ylabels':'Drift time (bins)',
                                                     'yvals1D':imsData1D,
                                                     'yvalsRT':yvalsRT,
                                                     'cmap':cmap,
                                                     'xylimits':zvals[selectedItem]['xylimits'],
                                                     'charge':charge,
                                                     'label':label, 
                                                     'alpha':alpha, 
                                                     'scanList':scanList,
                                                     'parameters':parameters}
            self.docs.combineIonsList = scanList
            # Add 1D data to document object
            self.docs.gotCombinedExtractedIonsRT = True            
            self.docs.IMSRTCombIons[selectedItem] = {'xvals':xlabels,
                                                     'yvals':np.sum(imsData2D, axis=0),
                                                     'xlabels':'Collision Voltage (V)'}
            
            # Update file list
            self.documentsDict[self.currentDoc] = self.docs
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
            self.view.SetStatusText('', 3)
            
    def onExtractMSforEachCollVoltage(self, evt):
        """
        This function extracts 'binned' msX and msY values for each collision
        voltage. The values are extracted for each scan range for particular 
        CV, binned and then summed together. These are then stored in the 
        document dictionary
        """
        self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        if self.currentDoc == 'Current documents': return
        self.docs = self.documentsDict[self.currentDoc]
        
        # Make sure the document is of correct type. 
        if not self.docs.dataType == 'Type: ORIGAMI': 
            self.view.SetStatusText('Please select correct document type - ORIGAMI', 3)
            return
        # Check that the user combined scans already
        if not self.docs.gotCombinedExtractedIons: 
            self.view.SetStatusText('Please combine collision voltages first', 3)
            return
        # Check that appropriate alues were filled in
        if (self.config.binMSstart == None or self.config.binMSend == None 
            or self.config.binCVdata == None):
            self.view.SetStatusText('Please fill in appopriate fields: MS start, MS end and MS bin size', 3)
            return
        # Do actual work
        splitlist = self.docs.combineIonsList
        msList = []
        
        msFilenames = ["m/z"]
        self.docs.gotMultipleMS = True
        for counter, item in enumerate(splitlist):
            msDict = ml.extractMSdata(filename=str(self.docs.path), startScan=item[0], 
                                      endScan=item[1], function=1, binData=True, 
                                      mzStart=self.config.binMSstart, 
                                      mzEnd=self.config.binMSend, 
                                      binsize=self.config.binMSbinsize)
            msX, msY = af.sumMSdata(ydict=msDict)
#             msList.append([msX, msY])item[0]
            itemName = ''.join(['Scans: ',str(item[0]),'-',str(item[1]-1),
                                 ' | CV: ',str(item[2])])
            self.docs.multipleMassSpectrum[itemName] = {'trap':item[2],
                                                        'xvals':msX,
                                                        'yvals':msY,
                                                        'xlabels':'m/z (Da)'}
            msFilenames.append(str(item[2]))
            if counter == 0:
                tempArray = msY
            else: 
                tempArray = np.concatenate((tempArray, msY), axis=0)

        # Form pandas dataframe
        combMSOut = np.concatenate((msX, tempArray), axis=0)
        combMSOut = combMSOut.reshape((len(msY), int(counter+2)), order='F') 
   
        msSaveData = pd.DataFrame(data=combMSOut, columns=msFilenames)
        self.docs.gotMSSaveData = True
        self.docs.massSpectraSave = msSaveData # pandas dataframe that can be exported as csv
        
        # Add data to dictionary
        self.documentsDict[self.docs.title] = self.docs
        self.view.panelDocuments.topP.documents.addDocument(docData = self.docs,
                                                            expandItem=self.documentsDict[self.docs.title].multipleMassSpectrum[itemName])
            
    def onExtract2DimsOverMZrange(self, e):
        self.config.extractMode = 'singleIon'
        self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        if self.currentDoc == 'Current documents': return
        self.docs = self.documentsDict[self.currentDoc]
        dataType = self.docs.dataType
        path = self.docs.path
        mzStart= str2num(self.config.mzStart)
        mzEnd = str2num(self.config.mzEnd)
        if isempty(path) or isempty(mzStart) or isempty(mzEnd):
            self.view.SetStatusText('Please enter correct mass range', 3)
            return 
        if mzEnd < mzStart:
            mzEnd_copy = mzStart
            mzStart = mzEnd
            mzEnd = mzEnd_copy
            self.config.mzStart = mzStart
            self.config.mzEnd = mzEnd
            self.view.panelControls.onUpdateParams()
        else:
            tstart = time.clock()
            # Add to table and show the window 
            # Check if this data is already present - if so it stops here
            outcome = self.view.Add2Table(xvalsMin=mzStart, xvalsMax=mzEnd, yvalsMax=0, 
                                          currentView='MS', currentDoc=self.currentDoc)
            if outcome: return
            # 1D IMMS
            ml.rawExtract1DIMSdata(fileNameLocation=path, driftscopeLocation=self.config.driftscopePath,
                                   mzStart=mzStart, mzEnd=mzEnd)
            imsData1D =  ml.rawOpen1DRTdata(path=path,norm=self.config.normalize)  
            
            # RT 
            ml.rawExtractRTdata(fileNameLocation=path, driftscopeLocation=self.config.driftscopePath,
                                mzStart=mzStart, mzEnd=mzEnd)
            rtDataY, rtDataYnorm = ml.rawOpenRTdata(path=path, norm=True)   
            
            # 2D IMMS
            ml.rawExtract2DIMSdata(fileNameLocation=path, driftscopeLocation=self.config.driftscopePath,
                                   mzStart=mzStart, mzEnd=mzEnd)
            imsData2D = ml.rawOpen2DIMSdata(path=path, norm=False)
            xlabels = 1+np.arange(len(imsData2D[1,:]))
            ylabels = 1+np.arange(len(imsData2D[:,1]))
            imsData1D = np.sum(imsData2D, axis=1).T # 'yvals1D':imsData1D,
            self.plot2Ddata2(data=[imsData2D,xlabels,'Scans',ylabels,'Drift time (bins)', self.docs.colormap])
            tend = time.clock()
            self.view.SetStatusText('Total time to extract ion: %.2gs' % (tend-tstart), 3)
            
            # Update limits
            self.setXYlimitsRMSD2D(xlabels, ylabels)
            # Add data to document object
            self.docs.gotExtractedIons = True
            rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
            self.docs.currentExtractRange = rangeName
            self.docs.IMS2Dions[rangeName] = {'zvals':imsData2D,
                                               'xvals':xlabels,
                                               'xlabels':'Scans',
                                               'yvals':ylabels,
                                               'yvals1D':imsData1D,
                                               'yvalsRT':rtDataY,
                                               'ylabels':'Drift time (bins)',
                                               'cmap':self.docs.colormap,
                                               'charge':"None"}
            
        # Update file list
        self.documentsDict[self.currentDoc] = self.docs
        self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)        
    
    def onOverlayMultipleIons1D(self, evt):
        """ 
        This function enables overlaying of multiple ions together - 1D and RT
        """
        # Check what is the ID
        if (evt.GetId() == ID_overlayMZfromList1D or 
            evt.GetId() == ID_overlayMZfromListRT):
            tempList = self.view.panelMultipleIons.topP.peaklist
        tempAccumulator = 0 # Keeps count of how many items are ticked
        try:
            self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        except: return
        if self.currentDoc == "Current documents": return
        
        # Check if current document is a comparison document
        # If so, it will be used 
        if self.documentsDict[self.currentDoc].dataType == 'Type: Comparison':
            self.docs = self.documentsDict[self.currentDoc]
            self.view.SetStatusText('Using document: ' + self.docs.title.encode('ascii', 'replace'), 3)
        else:
            docList = self.checkIfAnyDocumentsAreOfType(type='Type: Comparison')
            if len(docList) == 0:
                print('Did not find appropriate document.')
                dlg =  wx.FileDialog(self.view, "Please select a name for the comparison document", 
                                     "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                if dlg.ShowModal() == wx.ID_OK:
                    path, idName = os.path.split(dlg.GetPath()) 
                else: return
                # Create document
                self.docs = doc()
                self.docs.title = idName
                self.docs.path = path
                self.docs.userParameters = self.config.userParameters
                self.docs.userParameters['date'] = getTime()
                self.docs.dataType = 'Type: Comparison'
                self.docs.fileFormat = 'Format: ORIGAMI'
            else:
                self.selectDocDlg = panelSelectDocument(self.view, self, docList)
                if self.selectDocDlg.ShowModal() == wx.ID_OK: 
                    pass
                
                # Check that document exists
                if self.currentDoc == None: 
                    self.view.SetStatusText('Please select comparison document', 3)
                    return
                self.docs = self.documentsDict[self.currentDoc]
                self.view.SetStatusText('Using document: ' + self.docs.title.encode('ascii', 'replace'), 3)
        
        # Empty lists
        xlist, ylist, colorlist, legend = [], [], [], []
        # Get data for the dataset
        for row in range(tempList.GetItemCount()):
            if tempList.IsChecked(index=row):
                if (evt.GetId() == ID_overlayMZfromList1D or 
                    evt.GetId() == ID_overlayMZfromListRT):
                    # Get current document
                    self.currentDoc = tempList.GetItem(itemId=row, 
                                                       col=self.config.peaklistColNames['filename']).GetText()
                    # Check that data was extracted first
                    if self.currentDoc == '':
                        self.view.SetStatusText('Please extract data first', 3)
                        continue
                    document = self.documentsDict[self.currentDoc]
                    dataType = document.dataType
                    if ((dataType == 'Type: ORIGAMI' and document.gotCombinedExtractedIons == True) or 
                        (dataType == 'Type: Infrared' and document.gotCombinedExtractedIons == True)): 
                        if document.got2DprocessIons == True:
                            data = document.IMS2DionsProcess
                        else:
                            print('Using combined data')
                            data = document.IMS2DCombIons
                    elif ((dataType == 'Type: ORIGAMI' and document.gotExtractedIons == True) or 
                          (dataType == 'Type: Infrared' and document.gotExtractedIons == True)):
                        if document.got2DprocessIons == True:
                            data = document.IMS2DionsProcess
                        else:
                            print('Using extracted data')
                            data = document.IMS2Dions
                    elif dataType == 'Type: MANUAL' and document.gotCombinedExtractedIons == True:
                        if document.got2DprocessIons == True:
                            data = document.IMS2DionsProcess
                        else:
                            data = document.IMS2DCombIons            
                    else:
                        return  

                    # Get data for each ion
                    mzStart = tempList.GetItem(itemId=row, 
                                               col=self.config.peaklistColNames['start']).GetText()
                    mzEnd = tempList.GetItem(itemId=row, 
                                             col=self.config.peaklistColNames['end']).GetText()
                    selectedItem = ''.join([str(mzStart),'-',str(mzEnd)]) # ion name
                    label = tempList.GetItem(itemId=row, 
                                             col=self.config.peaklistColNames['label']).GetText()
                    # Add depending which event was triggered
                    if evt.GetId() == ID_overlayMZfromList1D:
                        xvals = data[selectedItem]['yvals'] # normally this would be the y-axis
                        yvals = data[selectedItem]['yvals1D']
                        yvals = af.smooth1D(data=yvals, 
                                            sigma=self.config.smoothOverlay1DRT)
                        yvals = af.normalizeMS(inputData=yvals)
                        xlabels = data[selectedItem]['ylabels'] # data was rotated so using ylabel for xlabel 
                        idName = ''.join('1D')
                    elif evt.GetId() == ID_overlayMZfromListRT:
                        xvals = data[selectedItem]['xvals']
                        yvals = data[selectedItem]['yvalsRT']
                        yvals = af.smooth1D(data=yvals, 
                                            sigma=self.config.smoothOverlay1DRT)
                        yvals = af.normalizeMS(inputData=yvals)
                        xlabels = data[selectedItem]['xlabels']
                        idName = ''.join('RT')

                    # Append data to list
                    xlist.append(xvals)
                    ylist.append(yvals)
                    colorlist.append(self.randomColorGenerator())
                    if label == "": label = selectedItem
                    legend.append(label)

        # Modify the name to include ion tags
        idNames = legend
        idNames.insert(0, idName)
        idName = '__'.join(idNames)
        # Determine x-axis limits for the zoom function
        xlimits = [min(xvals), max(xvals)]

        del legend[0]
        # Add data to dictionary
        self.docs.gotOverlay = True
        self.docs.IMS2DoverlayData[idName] = {'xvals':xlist,
                                              'yvals':ylist,
                                              'xlabel':xlabels,
                                              'colors':colorlist,
                                              'xlimits':xlimits,
                                              'labels':legend}
        self.currentDoc = document.title
        self.documentsDict[self.docs.title] = self.docs
        self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
        
        # Plot
        if evt.GetId() == ID_overlayMZfromList1D:
            self.onOverlayDT(xvals=xlist, yvals=ylist, xlabel=xlabels, colors=colorlist,
                             xlimits=xlimits, labels=legend)
            self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['1D'])
        elif evt.GetId() == ID_overlayMZfromListRT:
            self.onOverlayRT(xvals=xlist, yvals=ylist, xlabel=xlabels, colors=colorlist,
                             xlimits=xlimits, labels=legend)
            self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['RT'])
            
    def randomColorGenerator(self):
        colorGen = ''.join([random.choice('0123456789ABCDEF') for x in range(6)])
        return ''.join(["#",colorGen])
    
    def onOverlayMultipleIons(self, evt):
        """
        This function enables overlaying multiple ions from the same CIU datasets together
        """
        # Check what is the ID
        if evt.GetId() == ID_overlayMZfromList:
            tempList = self.view.panelMultipleIons.topP.peaklist
        elif evt.GetId() == ID_overlayTextFromList:
            tempList = self.view.panelMultipleText.topP.filelist
        
        tempAccumulator = 0 # Keeps count of how many items are ticked
        try:
            self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        except: return
        if self.currentDoc == "Current documents": return
        
        # Check if current document is a comparison document
        # If so, it will be used 
        if self.documentsDict[self.currentDoc].dataType == 'Type: Comparison':
            self.docs = self.documentsDict[self.currentDoc]
            self.view.SetStatusText('Using document: ' + self.docs.title.encode('ascii', 'replace'), 3)
            if self.docs.gotComparisonData:
                compDict = self.docs.IMS2DcompData
                compList = []
                for key in self.docs.IMS2DcompData:
                    compList.append(key)
            else:
                compDict, compList = {}, []
        else:
            print('Checking if there is a comparison document')
            docList = self.checkIfAnyDocumentsAreOfType(type='Type: Comparison')
            if len(docList) == 0:
                print('Did not find appropriate document.')
                dlg =  wx.FileDialog(self.view, "Please select a name for the comparison document", 
                                     "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                if dlg.ShowModal() == wx.ID_OK:
                    path, idName = os.path.split(dlg.GetPath()) 
                else: return
                    
                # Create document
                self.docs = doc()
                self.docs.title = idName
                self.docs.path = path
                self.docs.userParameters = self.config.userParameters
                self.docs.userParameters['date'] = getTime()
                self.docs.dataType = 'Type: Comparison'
                self.docs.fileFormat = 'Format: ORIGAMI'
                # Initiate empty list and dictionary
                compDict, compList = {}, []
            else:
                self.selectDocDlg = panelSelectDocument(self.view, self, docList)
                if self.selectDocDlg.ShowModal() == wx.ID_OK: 
                    pass
                
                # Check that document exists
                if self.currentDoc == None: 
                    self.view.SetStatusText('Please select comparison document', 3)
                    return
                
                self.docs = self.documentsDict[self.currentDoc]
                self.view.SetStatusText('Using document: ' + self.docs.title.encode('ascii', 'replace'), 3)
                if self.docs.gotComparisonData:
                    compDict = self.docs.IMS2DcompData
                    compList = []
                    for key in self.docs.IMS2DcompData:
                        compList.append(key)
                else:
                    compDict, compList = {}, []

        # Get data for the dataset
        for row in range(tempList.GetItemCount()):
            if tempList.IsChecked(index=row):
                if evt.GetId() == ID_overlayMZfromList:
                    # Get current document
                    self.currentDoc = tempList.GetItem(itemId=row, col=5).GetText()
                    # Check that data was extracted first
                    if self.currentDoc == '':
                        self.view.SetStatusText('Please extract data first', 3)
                        continue
                    document = self.documentsDict[self.currentDoc]
                    dataType = document.dataType
                    if ((dataType == 'Type: ORIGAMI' and document.gotCombinedExtractedIons == True) or 
                        (dataType == 'Type: Infrared' and document.gotCombinedExtractedIons == True)): 
                        if document.got2DprocessIons == True:
                            print('Using processed data')
                            tempData = document.IMS2DionsProcess
                        else:
                            print('Using combined data')
                            tempData = document.IMS2DCombIons
                    elif ((dataType == 'Type: ORIGAMI' and document.gotExtractedIons == True) or 
                          (dataType == 'Type: Infrared' and document.gotExtractedIons == True)):
                        if document.got2DprocessIons == True:
                            print('Using processed data')
                            tempData = document.IMS2DionsProcess
                        else:
                            print('Using extracted data')
                            tempData = document.IMS2Dions
                    elif dataType == 'Type: MANUAL' and document.gotCombinedExtractedIons == True:
                        print('Using manual data')
                        if document.got2DprocessIons == True:
                            print('Using processed data')
                            tempData = document.IMS2DionsProcess
                        else:
                            tempData = document.IMS2DCombIons            
                    else: return  

                    # Get data for each ion
                    mzStart = tempList.GetItem(itemId=row, col=0).GetText()
                    # TODO fix so it allows duplicates of the same ions !
                    # should be easy - just append filename with an underscore and then strip it everytime the key is called
                    mzEnd = tempList.GetItem(itemId=row, col=1).GetText()
                    selectedItem = ''.join([str(mzStart),'-',str(mzEnd)]) # ion name
                    selectedItemUnique = ''.join([selectedItem, "__", self.currentDoc])
                    zvals, xaxisLabels, xlabel, yaxisLabels, ylabel, cmap = self.get2DdataFromDictionary(dictionary=tempData[selectedItem],
                                                                                                         dataType='plot',compact=False)
                    # Extract additional information for each ion
                    tempAccumulator = tempAccumulator+1
                    tempCmap = tempList.GetItem(itemId=row, col=3).GetText().encode('ascii', 'replace') 
                    tempAlpha = tempList.GetItem(itemId=row, col=4).GetText().encode('ascii', 'replace')
                    label = tempList.GetItem(itemId=row, col=8).GetText()
                
                elif evt.GetId() == ID_overlayTextFromList:
                    tempAccumulator += 1
                    comparisonFlag = False # used only in case the user reloaded comparison document
                    # Extract data from dictionary
                    filename = tempList.GetItem(row,self.config.textlistColNames['filename']).GetText()
                    tag = tempList.GetItem(row,self.config.textlistColNames['tag']).GetText() 
                    document = self.documentsDict[filename]
                    # Determine whether the file has been pre-processed
                    if document.got2Dprocess == True:
                        print('Using processed data')
                        tempData = document.IMS2Dprocess
                    elif document.got2DIMS == True:
                        print('Using raw data')
                        tempData = document.IMS2D
                    elif document.gotComparisonData and document.dataType == 'Type: Comparison':
                        print('Using comparison data')
                        comparisonFlag = True
                        tempData = document.IMS2DcompData[tag] 
                    else:
                        self.view.SetStatusText('No data for selected file', 3)
                        return
                    zvals = tempData['zvals']
                    xaxisLabels = tempData['xvals']
                    xlabel = tempData['xlabels']
                    yaxisLabels = tempData['yvals']
                    ylabel = tempData['ylabels']
                    cmap = tempData['cmap']
                    # Populate x-axis labels
                    if type(xaxisLabels) is list: pass
                    elif xaxisLabels is "": 
                        startX = tempList.GetItem(itemId=row, col=1).GetText().encode('ascii', 'replace')
                        endX = tempList.GetItem(itemId=row, col=2).GetText().encode('ascii', 'replace')
                        stepsX = len(zvals[0])
                        if startX == "" or endX == "": pass
                        else:
                            xaxisLabels = self.onPopulateXaxisTextLabels(startVal=str2num(startX), 
                                                                         endVal=str2num(endX), 
                                                                         shapeVal=stepsX)
                            document.IMS2D['xvals'] = xaxisLabels
                    # Populate y-axis labels
                    if type(yaxisLabels) is list: pass
                    else:
                        stepsY = len(zvals)
                        yaxisLabels = range(stepsY)
                        yaxisLabels = [y+1 for y in yaxisLabels]
                        document.IMS2D[3] = yaxisLabels
                    # Get current colormap + alpha/mask value
                    tempCmap = tempList.GetItem(itemId=row, col=3).GetText().encode('ascii', 'replace') 
                    tempAlpha = tempList.GetItem(itemId=row, col=4).GetText().encode('ascii', 'replace')
                    label = tempList.GetItem(itemId=row, col=5).GetText()
                    if not comparisonFlag: selectedItemUnique = filename
                    else: selectedItemUnique = tag
                if label == '' or label == None:
                    label = ""
                compList.insert(0, selectedItemUnique)
                # Check if exists. We need to extract labels (header...) 
                checkExist = compDict.get(selectedItemUnique, None)
                if checkExist is not None: 
                    title = compDict[selectedItemUnique].get('header', "")
                    header = compDict[selectedItemUnique].get('header', "")
                    footnote = compDict[selectedItemUnique].get('footnote', "")
                else: title, header, footnote = "", "", ""
                compDict[selectedItemUnique] = {'zvals':zvals, 
                                                'cmap':tempCmap,
                                                'alpha':str2num(tempAlpha), # alpha/mask use the same field
                                                'xvals':xaxisLabels, 
                                                'xlabels':xlabel, 
                                                'yvals':yaxisLabels, 
                                                'ylabels':ylabel,
                                                'index':row,
                                                'shape':zvals.shape,
                                                'label':label,
                                                'title':title,
                                                'header':header,
                                                'footnote':footnote}

            
        # Check whether the user selected at least two files (and no more than 2 for certain functions)
        if tempAccumulator < 2:
            self.view.SetStatusText('Please select at least two files', 3)
            return
        
        # Remove duplicates from list
        compList = removeDuplicates(compList)
        
        zvalsIon1plot=compDict[compList[0]]['zvals']
        zvalsIon2plot=compDict[compList[1]]['zvals']
        name1 = compList[0]
        name2 = compList[1]
        print(''.join(["Comparing ions: ",name1, " and ", name2]))
        # Check if text files are of identical size
        if not zvalsIon1plot.shape == zvalsIon2plot.shape: 
            msg = ''.join(["Comparing ions: ",name1, " and ", name2,". These files are NOT of identical shape"])
            self.view.SetStatusText(msg, 3)
            return
         
        defaultVals = ['Reds', 'Greens']
        ylabelRMSF = 'RMSD (%)'
        # Check if the table has information about colormap
        if compDict[compList[0]]['cmap'] == '': 
            cmapIon1= defaultVals[0] # change here
            compDict[compList[0]]['cmap'] = cmapIon1
            tempList.SetStringItem(index=compDict[compList[0]]['index'],
                                   col=3, label=cmapIon1)
        else:
            cmapIon1 = compDict[compList[0]]['cmap']
            
        if compDict[compList[1]]['cmap'] == '':
            cmapIon2=defaultVals[1]
            compDict[compList[1]]['cmap'] = cmapIon1
            tempList.SetStringItem(index=compDict[compList[1]]['index'],
                                   col=3, label=cmapIon2)
        else:
            cmapIon2 = compDict[compList[1]]['cmap'] 

        # Defaults for alpha/cutoff
        if self.config.overlayMethod == "Transparent":
            defaultVals = [1, 0.5]
        elif self.config.overlayMethod == "Mask":
            defaultVals = [0.25, 0.25]
        else: 
            defaultVals = ['','']
        # Check if the user set value of transparency (alpha)            
        if compDict[compList[0]]['alpha'] == '' or compDict[compList[0]]['alpha'] == None:
            alphaIon1=defaultVals[0]
            compDict[compList[0]]['alpha'] = alphaIon1
            tempList.SetStringItem(index=compDict[compList[0]]['index'],
                                   col=4, label=str(alphaIon1))
        else:
            alphaIon1=str2num(compDict[compList[0]]['alpha'])
             
        if compDict[compList[1]]['alpha'] == '' or compDict[compList[1]]['alpha'] == None:
            alphaIon2=defaultVals[1]
            compDict[compList[1]]['alpha'] = alphaIon2
            tempList.SetStringItem(index=compDict[compList[1]]['index'],
                                   col=4, label=str(alphaIon2))
        else:
            alphaIon2=str2num(compDict[compList[1]]['alpha'])       

        # Various comparison plots
        if any(self.config.overlayMethod in method for method in ["Transparent", "Mask",
                                                                         "RMSD", "RMSF"]):
            
            if self.config.overlayMethod == "Transparent":
                # Check how many items were selected 
                if tempAccumulator > 2:
                    msg1 = 'Currently only supporting an overlay of two ions. '
                    msg2 = 'Comparing: '+ compList[0] + ' and ' + compList[1]
                    msg3 = ''.join([msg1, msg2])
                    print(msg3)
                    
                self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Overlay'])
                # Overlay plot of two species to see whether there is a difference between
                self.onPlotOverlayMultipleIons2(zvalsIon1=zvalsIon1plot,
                                                cmapIon1=cmapIon1, 
                                                alphaIon1=alphaIon1, 
                                                zvalsIon2=zvalsIon2plot,
                                                cmapIon2=cmapIon2,
                                                alphaIon2=alphaIon2, 
                                                xvals=xaxisLabels,
                                                yvals=yaxisLabels,
                                                xlabel=xlabel,
                                                ylabel=ylabel,
                                                flag='Text')    
            
            elif self.config.overlayMethod == "Mask":
                # In this case, the values are not transparency but a threshold cutoff! Values between 0-1
                cutoffIon1 = alphaIon1
                cutoffIon2 = alphaIon2
                # Based on the value in alpha/cutoff, data will be cleared up        
                zvalsIon1plotMask = masked_array(zvalsIon1plot, zvalsIon1plot<cutoffIon1)
                zvalsIon1plot = zvalsIon1plotMask
                zvalsIon2plotMask = masked_array(zvalsIon2plot, zvalsIon2plot<cutoffIon2)
                zvalsIon2plot = zvalsIon2plotMask
                self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Overlay'])
                self.onPlotOverlayMultipleIons2(zvalsIon1=zvalsIon1plotMask,
                                                cmapIon1=cmapIon1, 
                                                alphaIon1=1, 
                                                zvalsIon2=zvalsIon2plotMask,
                                                cmapIon2=cmapIon2,
                                                alphaIon2=1, 
                                                xvals=xaxisLabels,
                                                yvals=yaxisLabels,
                                                xlabel=xlabel,
                                                ylabel=ylabel,
                                                flag='Text')  
            


            elif self.config.overlayMethod == "RMSD":
                """ Compute RMSD of two selected files """
                # Check whether we should be restricting the RMSD range
                if self.config.restrictXYrangeRMSD:
                    zvalsIon1plot, xvals, yvals = self.restrictRMSDrange(zvalsIon1plot, xaxisLabels, 
                                                                         yaxisLabels, self.config.xyLimitsRMSD)
                    
                    zvalsIon2plot, xvals, yvals = self.restrictRMSDrange(zvalsIon2plot, xaxisLabels, 
                                                                         yaxisLabels, self.config.xyLimitsRMSD)
                    xaxisLabels, yaxisLabels = xvals, yvals
                    
                pRMSD, tempArray = af.computeRMSD(inputData1=zvalsIon1plot,
                                                  inputData2=zvalsIon2plot)
                rmsdLabel = u"RMSD: %2.2f" % pRMSD 
                self.view.SetStatusText("RMSD: %2.2f" % pRMSD, 3)
                
                self.setXYlimitsRMSD2D(xaxisLabels, 
                                       yaxisLabels)
                
                self.onPlot2DIMS2(tempArray, xaxisLabels, yaxisLabels, xlabel, ylabel, 
                                  self.docs.colormap, plotType='RMSD')
                self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
                self.onPlot3DIMS(zvals=tempArray, labelsX=xaxisLabels, labelsY=yaxisLabels, 
                                 xlabel=xlabel, ylabel=ylabel, zlabel='Intensity', 
                                 cmap=self.docs.colormap)
                
                # Add RMSD label
                rmsdXpos, rmsdYpos = self.onCalculateRMSDposition(xlist=xaxisLabels,
                                                                  ylist=yaxisLabels)
                if rmsdXpos != None and rmsdYpos != None:
                    self.addTextRMSD(rmsdXpos,rmsdYpos, rmsdLabel, 0)
                
            elif self.config.overlayMethod == "RMSF":
                """ Compute RMSF of two selected files """
                self.rmsdfFlag = True
                
                if self.config.restrictXYrangeRMSD:
                    zvalsIon1plot, xvals, yvals = self.restrictRMSDrange(zvalsIon1plot, xaxisLabels, 
                                                                         yaxisLabels, self.config.xyLimitsRMSD)
                    
                    zvalsIon2plot, xvals, yvals = self.restrictRMSDrange(zvalsIon2plot, xaxisLabels, 
                                                                         yaxisLabels, self.config.xyLimitsRMSD)
                    xaxisLabels, yaxisLabels = xvals, yvals
                    
                pRMSFlist = af.computeRMSF(inputData1=zvalsIon1plot,
                                           inputData2=zvalsIon2plot)
                
                pRMSD, tempArray = af.computeRMSD(inputData1=zvalsIon1plot,
                                                  inputData2=zvalsIon2plot)
                rmsdLabel = u"RMSD: %2.2f" % pRMSD 
                self.view.SetStatusText("RMSD: %2.2f" % pRMSD, 3)
                xLabel = compDict[compList[0]]['xlabels'] 
                yLabel = compDict[compList[0]]['ylabels'] 
                pRMSFlist = af.smoothDataGaussian(inputData=pRMSFlist, sigma=1)
                
                self.setXYlimitsRMSD2D(xaxisLabels, 
                                       yaxisLabels)
                
                self.onPlotRMSDF(yvalsRMSF=pRMSFlist, 
                                 zvals=tempArray, 
                                 xvals=xaxisLabels, 
                                 yvals=yaxisLabels, 
                                 xlabelRMSD=xLabel, 
                                 ylabelRMSD=yLabel,
                                 ylabelRMSF=ylabelRMSF,
                                 color=document.lineColour,
                                 cmap=document.colormap)
                self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['RMSF'])
                # Add RMSD label
                rmsdXpos, rmsdYpos = self.onCalculateRMSDposition(xlist=xaxisLabels,
                                                                  ylist=yaxisLabels)
                if rmsdXpos != None and rmsdYpos != None:
                    self.addTextRMSD(rmsdXpos,rmsdYpos, rmsdLabel, 0, plot='RMSF')
                
            # Add data to the dictionary (overlay data)
            self.docs.gotOverlay = True
            # Need to be a better system for naming - for now use the name
            if ((not compDict[compList[0]]['label'] == '' and not compDict[compList[0]]['label'] == '')
                or compDict[compList[0]]['label'] != compDict[compList[1]]['label']):
                idName = ''.join([compDict[compList[0]]['label'],'-',compDict[compList[1]]['label']])
            else:
                idName = ''.join([compList[0],'-',compList[1]])
            
            idName = self.config.overlayMethod + '__' + idName # new name
            # Add to the name to includ the method
            # Check if exists. We need to extract labels (header...) 
            checkExist = self.docs.IMS2DoverlayData.get(idName, None)
            if checkExist is not None: 
                title = self.docs.IMS2DoverlayData[idName].get('header', "")
                header = self.docs.IMS2DoverlayData[idName].get('header', "")
                footnote = self.docs.IMS2DoverlayData[idName].get('footnote', "")
            else: title, header, footnote = "", "", ""        
            # Add data to dictionary
            if (self.config.overlayMethod == "Mask" 
                or self.config.overlayMethod == "Transparent"): 
                self.docs.IMS2DoverlayData[idName] = {'zvals1':zvalsIon1plot, 
                                                      'zvals2':zvalsIon2plot,
                                                      'cmap1':cmapIon1, 
                                                      'cmap2':cmapIon2,
                                                      'alpha1':alphaIon1, 
                                                      'alpha2':alphaIon2,
                                                      'xvals':xaxisLabels, 
                                                      'xlabels':xlabel,
                                                      'yvals':yaxisLabels,
                                                      'ylabels':ylabel,
                                                      'file1':compList[0], 
                                                      'file2':compList[1],
                                                      'label1':compDict[compList[0]]['label'],
                                                      'label2':compDict[compList[1]]['label'],
                                                      'title':title,
                                                      'header':header,
                                                      'footnote':footnote}
            elif (self.config.overlayMethod == "RMSF"): 
                self.docs.IMS2DoverlayData[idName] = {'yvalsRMSF':pRMSFlist,
                                                      'zvals':tempArray,
                                                      'xvals':xaxisLabels, 
                                                      'yvals':yaxisLabels,
                                                      'ylabelRMSF':ylabelRMSF,
                                                      'xlabelRMSD':xLabel,
                                                      'ylabelRMSD':yLabel,
                                                      'rmsdLabel':rmsdLabel,
                                                      'colorRMSF':document.lineColour,
                                                      'cmapRMSF':document.colormap,
                                                      'title':title,
                                                      'header':header,
                                                      'footnote':footnote}
            elif (self.config.overlayMethod == "RMSD"): 
                self.docs.IMS2DoverlayData[idName] = {'zvals':tempArray,
                                                      'xvals':xaxisLabels, 
                                                      'yvals':yaxisLabels,
                                                      'xlabel':xlabel,
                                                      'ylabel':ylabel,
                                                      'rmsdLabel':rmsdLabel,
                                                      'cmap':document.colormap,
                                                      'title':title,
                                                      'header':header,
                                                      'footnote':footnote}
            
                
        elif any(self.config.overlayMethod in method for method in ["Mean", "Standard Deviation", "Variance"] ):
            meanData = []
            for row in range(tempAccumulator):
                key = compList[row]
                meanData.append(compDict[key]['zvals'])

            xAxisLabels = compDict[key]['xvals']
            xlabel = compDict[key]['xlabels']
            yAxisLabels = compDict[key]['yvals']
            ylabel = compDict[key]['ylabels']
            msg = ''.join(["Computing ", self.config.textOverlayMethod, " for ", str(len(meanData)), " files."])
            self.view.SetStatusText(msg, 3)
            if self.config.overlayMethod == "Mean":
                """ Computes mean of selected files """
                self.view.SetStatusText('Mean', 3)
                zvals = af.computeMean(inputData=meanData)
            elif self.config.overlayMethod == "Standard Deviation":
                """ Computes standard deviation of selected files """
                self.view.SetStatusText('Standard Deviation', 3)
                zvals = af.computeStdDev(inputData=meanData)
            elif self.config.overlayMethod == "Variance":
                """ Computes variance of selected files """
                self.view.SetStatusText('Variance', 3)
                zvals = af.computeVariance(inputData=meanData)
            # Plot
            self.plot2Ddata2(data=[zvals, xAxisLabels,xlabel, yAxisLabels, ylabel, document.colormap])
            self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
            self.docs.gotStatsData = True 
            # Check if exists. We need to extract labels (header...) 
            checkExist = self.docs.IMS2DstatsData.get(self.config.overlayMethod, None)
            if checkExist is not None: 
                title = self.docs.IMS2DstatsData[self.config.overlayMethod].get('header', "")
                header = self.docs.IMS2DstatsData[self.config.overlayMethod].get('header', "")
                footnote = self.docs.IMS2DstatsData[self.config.overlayMethod].get('footnote', "")
            else: title, header, footnote = "", "", ""           
            
            self.docs.IMS2DstatsData[self.config.overlayMethod] = {'zvals':zvals,
                                                                   'xvals':xAxisLabels,
                                                                   'xlabels':xlabel,
                                                                   'yvals':yAxisLabels,
                                                                   'ylabels':ylabel,
                                                                   'cmap':self.docs.colormap,
                                                                   'title':title,
                                                                   'header':header,
                                                                   'footnote':footnote}
        elif self.config.overlayMethod == "RMSD Matrix":
            """ Compute RMSD matrix for selected files """
            zvals = np.zeros([tempAccumulator,tempAccumulator])
            tickLabels = []
            for row in range(tempAccumulator):
                key = compList[row]
                # Extract text labels from table
                tickLabels.append(compDict[key]['label'])
                # Compute pairwise RMSD
                for row2 in range(row+1,tempAccumulator):
                    zvalsIon1plot = compDict[compList[row]]['zvals']
                    zvalsIon2plot = compDict[compList[row2]]['zvals']
                    pRMSD, tempArray = af.computeRMSD(inputData1=zvalsIon1plot,
                                                      inputData2=zvalsIon2plot)
                    zvals[row,row2] = np.round(pRMSD,2)
            self.onPlotRMSDmatrix(zvals=zvals, xylabels=tickLabels, cmap=self.docs.colormap)
            self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Comparison'])
            self.docs.gotStatsData = True 
            
            # Check if exists. We need to extract labels (header...) 
            checkExist = self.docs.IMS2DstatsData.get(self.config.overlayMethod, None)
            if checkExist is not None: 
                title = self.docs.IMS2DstatsData[self.config.overlayMethod].get('header', "")
                header = self.docs.IMS2DstatsData[self.config.overlayMethod].get('header', "")
                footnote = self.docs.IMS2DstatsData[self.config.overlayMethod].get('footnote', "")
            else: title, header, footnote = "", "", ""    
            self.docs.IMS2DstatsData[self.config.overlayMethod] = {'zvals':zvals,
                                                                   'cmap':self.docs.colormap,
                                                                   'matrixLabels':tickLabels,
                                                                   'title':title,
                                                                   'header':header,
                                                                   'footnote':footnote}

        # Add data to document
        self.docs.gotComparisonData = True
        self.docs.IMS2DcompData = compDict
        self.currentDoc = self.docs.title
        self.documentsDict[self.docs.title] = self.docs
        self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)

    def restrictRMSDrange(self, zvals, xvals, yvals, limits):
        """
        This function adjusts the size of the RMSD array to match the selected
        sizes from the GUI
        """
        # Get limits
        xmin, xmax, ymin, ymax = limits
        
        if xmin > xmax:
            xmin_temp = xmax
            xmax = xmin
            xmin = xmin_temp
            
        if ymin > ymax:
            ymin_temp = ymax
            ymax = ymin
            ymin = ymin_temp

        print(xmin, xmax, ymin, ymax)
            
        if xmin == None:
            xmin = xvals[0]
        if xmax == None:
            xmax = xvals[-1]
        if ymin == None:
            ymin = xvals[0]
        if ymax == None:
            ymax = xvals[-1]

        
        # Find nearest values
        value, idxXmin = find_nearest(np.array(xvals), xmin)
        value, idxXmax = find_nearest(np.array(xvals), xmax)
        value, idxYmin = find_nearest(np.array(yvals), ymin)
        value, idxYmax = find_nearest(np.array(yvals), ymax) 
        
        # in case index is returned as 0, return original value
        msg = ''.join([""])
        if idxXmax == 0:
            msg = 'Your Xmax value is too small - reseting to maximum'
            idxXmax = len(xvals)
        if idxXmin == idxXmax:
            msg = 'Your X-axis values are too close together - reseting to original view'
            idxXmin = 0
            idxXmax = len(xvals)
            
        if idxYmax == 0:
            msg = 'Your Ymax value is too small - reseting to maximum'
            idxYmax = len(yvals)
        if idxYmin == idxYmax:
            msg = 'Your Y-axis values are too close together - reseting to original view'
            idxYmin = 0
            idxYmax = len(yvals)
            
        zvals = zvals[idxYmin:idxYmax, idxXmin:idxXmax]
        xvals = xvals[idxXmin:idxXmax]
        yvals = yvals[idxYmin:idxYmax]
        
        self.view.SetStatusText(msg, 4)
        
        return zvals, xvals, yvals

    def restoreComparisonToList(self, evt=None):
        """ 
        Once comparison document was made and has been pickled, the data is not 
        easily accesible (apart from replotting). This function is to help retreive
        the input data and restore it to the file list - in this case text panel
        """
        try:
            self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        except: return
        if self.currentDoc == "Current documents": return
        
        # Make sure the document is of comparison type
        if self.documentsDict[self.currentDoc].dataType == 'Type: Comparison':
            # Enable text panel
            self.view.textView = False
            self.view.mainToolbar.ToggleTool(id=ID_OnOff_textView, toggle=True)
            self.view._mgr.GetPane(self.view.panelMultipleText).Show()
            self.view._mgr.Update()
            tempList = self.view.panelMultipleText.topP.filelist
            document = self.documentsDict[self.currentDoc]
            if document.gotComparisonData:
                filename = document.title
                for key in document.IMS2DcompData:
                    xvals = document.IMS2DcompData[key]['xvals']
                    shape = document.IMS2DcompData[key]['shape']
                    label = document.IMS2DcompData[key]['label']
                    cmap = document.IMS2DcompData[key]['cmap']
                    alpha = document.IMS2DcompData[key]['alpha']
                    print(filename, key, xvals[0], xvals[-1], label, cmap, alpha, shape)
                    tempList.Append([filename, 
                                     xvals[0], xvals[-1], 
                                     cmap, str(alpha),
                                     label, shape, 
                                     key])
                    
    def onCalculateRMSDposition(self,xlist,ylist):
        """
        This function calculates the X and Y position of the RMSD label
        """
        
        # First determine whether we need label at all
        if self.config.rmsdLoc == "None":
            return None, None
        # Get values
        xMultiplier, yMultiplier = self.config.rmsdLocPos
        xMin = np.min(xlist)
        xMax = np.max(xlist)
        yMin = np.min(ylist)
        yMax = np.max(ylist)

        # Calculate RMSD positions
        rmsdXpos = xMin+((xMax-xMin)*xMultiplier)/100
        rmsdYpos = yMin+((yMax-yMin)*yMultiplier)/100
        
        msg = ''.join(["Adding RMSD label at: ", str(rmsdXpos),' ',str(rmsdYpos), ' position'])
        self.view.SetStatusText(msg, 3)
        return rmsdXpos, rmsdYpos

    def onCombineMultipleMLFiles(self, e=None):
        """
        This function takes the multiple ML dictionary, sorts it and combines it 
        to form a 2D IM-MS map
        """
        try:
            self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        except: return
        self.docs = self.documentsDict[self.currentDoc]
        if self.docs.dataType != 'Type: MANUAL': 
            msg = 'Make sure you select the correct dataset - MANUAL'
            self.view.SetStatusText(msg, 3)
            return
        
        # Sort data in the dictionary first - if returns False then it hasn't done it!
        sorted = self.view.panelMML.topP.OnSortByColumn(column=1)
        tempList = self.view.panelMML.topP.filelist
        if sorted == False: return
        else: 
            counter = 0
            for item in xrange(tempList.GetItemCount()):
                key = tempList.GetItem(item,0).GetText()
#                 trapCV = str2num(tempList.GetItem(item,1).GetText())
                if counter == 0:
                    tempArray = self.docs.multipleMassSpectrum[key]['ims1D']
                    xLabelLow = self.docs.multipleMassSpectrum[key]['trap'] # first iteration so first value
                    counter = counter+1
                else:
                    imsList = self.docs.multipleMassSpectrum[key]['ims1D']
                    tempArray = np.concatenate((tempArray, imsList), axis=0)
                    counter = counter+1
                    
            # Reshape data to form a 2D array of size 200 x number of files
            imsData2D = tempArray.reshape((200, int(counter)), order='F')
            # Get the x-axis labels
            xLabelHigh = self.docs.multipleMassSpectrum[key]['trap'] # after the loop has finished, so last value
            xlabels = np.linspace(xLabelLow, xLabelHigh, num=counter)
            ylabels = 1+np.arange(len(ims2Ddata[:,1]))
            self.plot2Ddata2(data=[imsData2D,
                                   xlabels,
                                   'Collision Voltage (V)',
                                   ylabels,
                                   'Drift time (bins)',
                                   self.docs.colormap])

            self.docs.got2DIMS = True
            self.docs.IMS2D = {'zvals':imsData2D,
                               'xvals':xlabels,
                               'xlabels':'Collision Voltage (V)',
                               'yvals':ylabels,
                               'ylabels':'Drift time (bins)',
                               'cmap':self.docs.colormap}
            
            # Append to list
            self.documentsDict[self.docs.title] = self.docs
            
            # Update documents tree
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)               
                        
    def checkIfRawFile(self, path):
        """
        Checks whether the selected directory is a MassLynx file i.e. ends with .raw
        """
        if path.rstrip('/')[-4:] == ".raw":
            return path

    def onProcessMultipleIonsIons(self, evt):
        """
        This function processes the 2D array data from multiple ions MULTIFILE or ORIGAMI
        """
        # Shortcut to table
        tempList = self.view.panelMultipleIons.topP.peaklist
        # Make a list of current documents
        for row in range(tempList.GetItemCount()):
            self.currentDoc = tempList.GetItem(itemId=row, col=5).GetText()
            # Check that data was extracted first
            if self.currentDoc == '':
                self.view.SetStatusText('Please extract data first', 3)
                continue
            if evt.GetId() == ID_processAllIons: pass
            elif evt.GetId() == ID_processSelectedIons:
                if not tempList.IsChecked(index=row): continue               
            # Extract ion name
            mzStart = tempList.GetItem(itemId=row, col=0).GetText()
            mzEnd = tempList.GetItem(itemId=row, col=1).GetText()
            selectedItem = ''.join([str(mzStart),'-',str(mzEnd)])
            # Select document
            self.docs = self.documentsDict[self.currentDoc]
            dataType = self.docs.dataType
            print(self.docs.title, dataType)
            if ((dataType == 'Type: ORIGAMI' and self.docs.gotCombinedExtractedIons == True) or 
                (dataType == 'Type: Infrared' and self.docs.gotCombinedExtractedIons == True)):     
                tempData = self.docs.IMS2DCombIons
            elif ((dataType == 'Type: ORIGAMI' and self.docs.gotExtractedIons == True) or 
                  (dataType == 'Type: Infrared' and self.docs.gotExtractedIons == True)):
                tempData = self.docs.IMS2Dions
            elif dataType == 'Type: MANUAL' and self.docs.gotCombinedExtractedIons == True:
                print('manual, combined')
                tempData = self.docs.IMS2DCombIons
            
            # Process data
            imsData2D = self.process2Ddata(zvals=tempData[selectedItem]['zvals'])
            imsData1D = np.sum(imsData2D, axis=1).T
            rtDataY = np.sum(imsData2D, axis=0)
            self.docs.got2DprocessIons = True
            self.docs.IMS2DionsProcess[selectedItem] = {'zvals':imsData2D,
                                                        'xvals':tempData[selectedItem]['xvals'],
                                                        'xlabels':tempData[selectedItem]['xlabels'],
                                                        'yvals':tempData[selectedItem]['yvals'],
                                                        'ylabels':tempData[selectedItem]['ylabels'],
                                                        'yvals1D':imsData1D,
                                                        'yvalsRT':rtDataY,
                                                        'cmap':tempData[selectedItem].get('cmap', self.docs.colormap),
                                                        'xylimits':tempData[selectedItem]['xylimits'],
                                                        'charge':tempData[selectedItem].get('charge', None),
                                                        'label':tempData[selectedItem].get('label', None),
                                                        'alpha':tempData[selectedItem].get('alpha', None)}
            # Update file list
            self.documentsDict[self.currentDoc] = self.docs
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
      
    def onOpenMultipleOrigamiFiles(self, evt):
        
        self.config.ciuMode = 'ORIGAMI'
        wildcard = "Open MassLynx files (*.raw)| ;*.raw"
        
        if self.config.lastDir == None or not os.path.isdir(self.config.lastDir):
            self.config.lastDir = os.getcwd()
            
        print(self.config.lastDir)
        dlg = MDD.MultiDirDialog(self.view, title="Choose MassLynx files to open:", 
                                 defaultPath = self.config.lastDir, 
                                 agwStyle=MDD.DD_MULTIPLE|MDD.DD_DIR_MUST_EXIST)
        
        if dlg.ShowModal() == wx.ID_OK:
            pathlist = dlg.GetPaths()

            for file in pathlist:
                path = self.checkIfRawFile(file)
                if path is None: pass
                else:
                    pathSplit = path.encode('ascii', 'replace').split(':)')
                    start = pathSplit[0].split('(')
                    start = start[-1]
                    path = ''.join([start,':',pathSplit[1]])
                    temp, rawfile = os.path.split(path)
                    # Update lastDir with current path
                    self.config.lastDir = path
                    self.onLoadOrigamiDataThreaded(path, evt=evt, mode='Type: ORIGAMI')
      
    def onOpenMultipleMLFiles(self, evt):
        # http://stackoverflow.com/questions/1252481/sort-dictionary-by-another-dictionary
        # http://stackoverflow.com/questions/22520739/python-sort-a-dict-by-values-producing-a-list-how-to-sort-this-from-largest-to
        
#         # Figure out what event was used:
#         if evt.GetId() == ID_openMassLynxFiles:
#             mode = 'asOne' # when dealing with CIU style file
#         elif evt.GetId() == ID_openMassLynxFilesAsMultiple:
#             mode = 'asMultiple' # when dealing with seperate style file
        
        
        self.config.ciuMode = 'MANUAL'
        wildcard = "Open MassLynx files (*.raw)| ;*.raw"
        tempList = self.view.panelMML.topP.filelist
        
        if self.config.lastDir == None or not os.path.isdir(self.config.lastDir):
            print(self.config.lastDir)
            self.config.lastDir = os.getcwd()
            
        tstart = time.clock()
        dlg = MDD.MultiDirDialog(self.view, title="Choose MassLynx files to open:", 
                                 defaultPath = self.config.lastDir, 
                                 agwStyle=MDD.DD_MULTIPLE|MDD.DD_DIR_MUST_EXIST)
        
        if dlg.ShowModal() == wx.ID_OK:
            pathlist = dlg.GetPaths()
            dlg =  wx.FileDialog(self.view, "Please select a name and path for the Manual dataset", 
                                 "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            if dlg.ShowModal() == wx.ID_OK:
                itemPath, idName = os.path.split(dlg.GetPath()) 
            else: return
            
            self.docs = doc()             
            self.docs.title = idName
            self.docs.path = itemPath
            self.docs.userParameters = self.config.userParameters
            self.docs.userParameters['date'] = getTime()
            self.currentDoc = idName # Currently plotted document
            self.docs.gotMultipleMS = True
            
            for file in pathlist:
                path = self.checkIfRawFile(file)
                if path is None: pass
                else:
                    pathSplit = path.encode('ascii', 'replace').split(':)')
                    start = pathSplit[0].split('(')
                    start = start[-1]
                    path = ''.join([start,':',pathSplit[1]])
                    temp, rawfile = os.path.split(path)
                    # Update lastDir with current path
                    self.config.lastDir = path
                    parameters = self.config.importMassLynxInfFile(path=path, manual=True)
                    ml.rawExtractMSdata(fileNameLocation=path, 
                                        driftscopeLocation=self.config.driftscopePath)
                    msDataX, msDataY = ml.rawOpenMSdata(path=path)
                    ml.rawExtract1DIMSdata(fileNameLocation=path, 
                                           driftscopeLocation=self.config.driftscopePath)
                    imsData1D =  ml.rawOpen1DRTdata(path=path, norm=self.config.normalize)
                    xvalsDT = np.arange(1,len(imsData1D)+1)
                    tempList.Append([rawfile, str(parameters['trapCE']), self.docs.title])
                    self.docs.multipleMassSpectrum[rawfile] = {'trap':parameters['trapCE'],
                                                               'xvals':msDataX,
                                                               'yvals':msDataY,
                                                               'ims1D':imsData1D,
                                                               'ims1DX':xvalsDT,
                                                               'xlabel':'Drift time (bins)',
                                                               'xlabels':'m/z (Da)',
                                                               'path': path,
                                                               'parameters':parameters}
            # Sum all mass spectra into one
            counter = 0
            # Bin MS data
            if self.config.binOnLoad:
                binsize = self.config.binMSbinsize
                msBinList = np.arange(parameters['startMS'], parameters['endMS']+binsize, binsize)
                msCentre = msBinList[:-1]+(binsize/2)
                msDataX = msCentre
            else: pass
            
            msFilenames = ["m/z"]
            for key in self.docs.multipleMassSpectrum:
                msFilenames.append(key)
                if counter == 0:
                    if self.config.binOnLoad:
                        tempArray = af.binMSdata(x=self.docs.multipleMassSpectrum[key]['xvals'],
                                                 y=self.docs.multipleMassSpectrum[key]['yvals'],
                                                 bins=msBinList)
                    else:
                        tempArray = self.docs.multipleMassSpectrum[key]['yvals']
                    counter = counter+1
                    msList = tempArray
                else:
                    if self.config.binOnLoad:
                        msList = af.binMSdata(x=self.docs.multipleMassSpectrum[key]['xvals'],
                                              y=self.docs.multipleMassSpectrum[key]['yvals'],
                                              bins=msBinList)
                    else:
                        msList = self.docs.multipleMassSpectrum[key]['yvals']
                    tempArray = np.concatenate((tempArray, msList), axis=0)
                    counter = counter+1
            
            # Reshape the list 
            combMS = tempArray.reshape((len(msList), int(counter)), order='F') 
            
            # Sum y-axis data
            msDataY = np.sum(combMS, axis=1)
            msDataY = af.normalizeMS(inputData = msDataY)
            xlimits = [parameters['startMS'],parameters['endMS']]
            
            # Form pandas dataframe
            combMSOut = np.concatenate((msDataX, tempArray), axis=0)
            combMSOut = combMSOut.reshape((len(msList), int(counter+1)), order='F') 
            
            msSaveData = pd.DataFrame(data=combMSOut, columns=msFilenames)
             
            # Update status bar with MS range
            txt = ''.join(["MS range: ", num2str(parameters['startMS']), "-", 
                           num2str(parameters['endMS'])])
            self.view.SetStatusText(txt, 1)
            txt = ''.join(['MSMS: ', num2str(parameters['setMS'])])
            self.view.SetStatusText(txt, 2)     
              
            # Add info to document 
            self.docs.parameters = parameters
            self.docs.dataType = 'Type: MANUAL'
            self.docs.fileFormat = 'Format: MassLynx (.raw)'
            # Add data
            self.docs.gotMSSaveData = True
            self.docs.massSpectraSave = msSaveData # pandas dataframe that can be exported as csv
            
            self.docs.gotMS = True
            self.docs.massSpectrum = {'xvals':msDataX,
                                      'yvals':msDataY,
                                      'xlabels':'m/z (Da)',
                                      'xlimits':xlimits}
            self.documentsDict[idName] = self.docs
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
            # Plot 
            self.onPlotMS2(msDataX, msDataY, self.docs.lineColour, self.docs.style, 
                           xlimits=xlimits)
            # Show panel
            self.view.multipleMLTable.Check(True)
            tempList = self.view.panelMML.topP.filelist
            self.view._mgr.GetPane(self.view.panelMML).Show()
            self.view._mgr.Update()
        else:
            self.view.SetStatusText('Please select some files', 3)    
            return  
        dlg.Destroy() 
        tend = time.clock()        
        self.view.SetStatusText('Total time to extract %d files was: %.3gs' % (len(pathlist),tend-tstart), 3)

    def reBinMSdata(self, evt):
        self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        self.docs = self.documentsDict[self.currentDoc]
        
        if self.docs.dataType == 'Type: MANUAL' and self.docs.gotMultipleMS:
            # Sum all mass spectra into one
            counter = 0
            # Bin MS data
            binsize = self.config.binMSbinsize
            msBinList = np.arange(self.docs.parameters['startMS'], 
                                  self.docs.parameters['endMS']+binsize, 
                                  binsize)
            
            msCentre = msBinList[:-1]+(binsize/2)
            for key in self.docs.multipleMassSpectrum:
                if counter == 0:
                    tempArray = af.binMSdata(x=self.docs.multipleMassSpectrum[key]['xvals'],
                                             y=self.docs.multipleMassSpectrum[key]['yvals'],
                                             bins=msBinList)
                    counter = counter+1
                else:
                    msList = af.binMSdata(x=self.docs.multipleMassSpectrum[key]['xvals'],
                                          y=self.docs.multipleMassSpectrum[key]['yvals'],
                                          bins=msBinList)
                    tempArray = np.concatenate((tempArray, msList), axis=0)
                    counter = counter+1
            # Reshape the list 
            combMS = tempArray.reshape((len(msList), int(counter)), order='F') 
            # Sum y-axis data
            msDataY = np.sum(combMS, axis=1)
            msDataY = af.normalizeMS(inputData = msDataY)
            xlimits = self.docs.massSpectrum['xlimits']
            # Add info to document 
            self.docs.massSpectrum = {'xvals':msCentre,
                                      'yvals':msDataY,
                                      'xlabels':'m/z (Da)',
                                      'xlimits':xlimits}
            self.documentsDict[self.docs.title] = self.docs
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
            # Plot 
            self.onPlotMS2(msCentre, msDataY, self.docs.lineColour, self.docs.style, 
                           xlimits=xlimits)
        evt.Skip()

#===============================================================================
#  INTERACTIVE FUNCTIONS
#===============================================================================

    def onPickPeaks(self, evt):
        """
        This function finds peaks from 1D array
        """
        self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        if self.currentDoc == 'Current documents': return     
        self.docs = self.documentsDict[self.currentDoc]
        
        # Shortcut to mz list
        if (self.docs.dataType == 'Type: ORIGAMI' or 
            self.docs.dataType == 'Type: MANUAL' or 
            self.docs.dataType == 'Type: Infrared' or
            self.docs.dataType == 'Type: MassLynx'):
            tempList = self.view.panelMultipleIons.topP.peaklist
            dataPlot = self.view.panelPlots.plot1
            pageID = self.config.panelNames['MS']
            markerPlot = 'MS'
            listLinks = self.config.peaklistColNames
        elif self.docs.dataType == 'Type: Multifield Linear DT':
            tempList = self.view.panelLinearDT.bottomP.peaklist
            rtTemptList = self.view.panelLinearDT.topP.peaklist
            dataPlot = self.view.panelPlots.plot1
            pageID = self.config.panelNames['MS']
            markerPlot = 'MS'
            listLinks = self.config.driftTopColNames
        elif self.docs.dataType == 'Type: CALIBRANT':
            tempList = self.view.panelCCS.topP.peaklist
            dtTempList = self.view.panelCCS.bottomP.peaklist
            dataPlot = self.view.panelPlots.topPlotMS
            pageID = self.config.panelNames['Calibration']
            markerPlot = 'CalibrationMS'
            listLinks = self.config.ccsTopColNames
        else:
            msg = "%s is not supported yet." % self.docs.dataType
            self.view.SetStatusText(msg, number = 3)
            return
        # A couple of constants
        ymin = 0
        height = 1.0
        
        if self.config.currentPeakFit == "RT" or self.config.currentPeakFit == "MS/RT": 
            if (self.docs.dataType == 'Type: Multifield Linear DT' or 
                self.docs.dataType == 'Type: Infrared'): 
                # TO ADD: current view only, smooth
                    # Prepare data first
                    xvals = self.docs.RT['xvals']
                    yvals = self.docs.RT['yvals']
                    rtList = np.array(zip(xvals,yvals))
                    # Detect peaks
                    peakList, tablelist = detectPeaksRT(rtList, self.config.peakThreshold)
                    msg = "".join(["Found: ", num2str(len(peakList)), " peaks."])
                    self.view.SetStatusText(msg, number = 3)
                    
                    if len(peakList) > 0:
                        self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['RT'])
                        self.onPlotRT2(self.docs.RT['xvals'], 
                                       self.docs.RT['yvals'],
                                       self.docs.RT['xlabels'],
                                       self.docs.lineColour,
                                       self.docs.style)
                        # Add rectangles (if checked)
                        if self.config.showRectanges:
                            self.addMarkerMS(xvals=peakList[:,0],yvals=peakList[:,1],
                                             color=self.config.annotColor, 
                                             marker=self.config.markerShape,
                                             size=self.config.markerSize,
                                             plot='RT')
                            # Iterate over list and add rectangles
                            last = len(tablelist)-1
                            for i, rt in enumerate(tablelist):
                                xmin = rt[0]
                                if xmin == 1: pass
                                else: xmin = xmin-1
                                width = rt[1]-xmin+1
                                if i == last:
                                    width = width-1
                                    self.addRectRT(xmin, ymin, width, height, color=self.config.annotColor, 
                                                   alpha=(self.config.annotTransparency/100),
                                                   repaint=True)
                                else:
                                    self.addRectRT(xmin, ymin, width, height, color=self.config.annotColor, 
                                                   alpha=(self.config.annotTransparency/100),
                                                   repaint=False)
                                    
                            # Add items to table (if checked)
                            if self.config.autoAddToTable:
                                if self.docs.dataType == 'Type: Multifield Linear DT':
                                    self.view._mgr.GetPane(self.view.panelLinearDT).Show()
                                    self.view.multifieldTable.Check(True)
                                    self.view._mgr.Update()
                                    for rt in tablelist:
                                        xmin = rt[0]
                                        xmax = rt[1]
                                        xdiff = xmax-xmin
                                        rtTemptList.Append([xmin,xmax,xdiff,"",self.currentDoc])
                                    # Removing duplicates
                                    self.view.panelLinearDT.topP.onRemoveDuplicates(evt=None)

        if self.config.currentPeakFit == "MS" or self.config.currentPeakFit == "MS/RT":
            if self.docs.gotMS == True:
                if self.config.smoothFitting:
                    msX = self.docs.massSpectrum['xvals']
                    msY = self.docs.massSpectrum['yvals']
                    # Smooth data
                    msY = af.smooth1D(data=msY, sigma=self.config.sigmaMS)
                    msY = af.normalizeMS(inputData=msY)
                else:
                    msX = self.docs.massSpectrum['xvals']
                    msY = self.docs.massSpectrum['yvals']
                msList = np.rot90(np.array([msX, msY]))
                if self.config.currentRangePeak:
                    # Get current m/z range
                    mzRange = dataPlot.onGetXYvals(axes='x') # using shortcut
                    msList = getNarrow1Ddata(data=msList, mzRange=mzRange) # get index of that m/z range
                
                # Findpeaks 
                peakList = detectPeaks1D(data=msList, window=self.config.peakWindow, 
                                         threshold=self.config.peakThreshold)
                msg = "".join(["Found: ", num2str(len(peakList)), " peaks."])
                self.view.SetStatusText(msg, number = 3)
                if len(peakList) > 0:
                    self.view.panelPlots.mainBook.SetSelection(pageID) # using shortcut
                    # Plotting smoothed (or not) MS
                    if self.docs.dataType == 'Type: CALIBRANT':
                        self.onPlotMSDTCalibration(msX=msX, 
                                                   msY=msY, 
                                                   xlimits=self.docs.massSpectrum['xlimits'],
                                                   color=self.docs.lineColour, plotType='MS')
                    else:
                        self.onPlotMS2(msX, msY, self.docs.lineColour,
                                       xlimits=self.docs.massSpectrum['xlimits'], 
                                       style=None)
                    # Add rectangles (if checked)
                    if self.config.showRectanges:
                        self.addMarkerMS(xvals=peakList[:,0],yvals=peakList[:,1],
                                         color=self.config.annotColor, 
                                         marker=self.config.markerShape,
                                         size=self.config.markerSize,
                                         plot=markerPlot) # using shortcut
                        # Iterate over list and add rectangles
                        last = len(peakList)-1
                        for i, mz in enumerate(peakList):
                            peak = mz[0]
                            # New in 1.0.4: Added slightly assymetric character to the peak envelope
                            xmin = peak-(self.config.peakWidth*0.75)
                            width = (self.config.peakWidth*2)
                            if i == last:
                                self.addRectMS(xmin, ymin, width, height, 
                                               color=self.config.annotColor, 
                                               alpha=(self.config.annotTransparency/100),
                                               repaint=True, plot=markerPlot)
                            else:
                                self.addRectMS(xmin, ymin, width, height, 
                                               color=self.config.annotColor, 
                                               alpha=(self.config.annotTransparency/100),
                                               repaint=False, plot=markerPlot)
                                
                        # Need to check whether there were any ions in the table already
                        last = tempList.GetItemCount()-1
                        for item in xrange(tempList.GetItemCount()):
                            if self.config.autoAddToTable:
                                if self.docs.dataType == 'Type: ORIGAMI' or self.docs.dataType == 'Type: MANUAL':
                                    filename = tempList.GetItem(item,self.config.peaklistColNames['filename']).GetText()
                                elif self.docs.dataType == 'Type: Multifield Linear DT':
                                    filename = tempList.GetItem(item,self.config.driftTopColNames['filename']).GetText()
                                elif self.docs.dataType == 'Type: CALIBRANT':
                                    filename = tempList.GetItem(item,self.config.ccsTopColNames['filename']).GetText()
                            
                                if filename != self.currentDoc: continue
                                xmin = str2num(tempList.GetItem(item,listLinks['start']).GetText())
                                width = str2num(tempList.GetItem(item,listLinks['end']).GetText())-xmin
                                if item == last:
                                    self.addRectMS(xmin, ymin, width, height, 
                                                   color=self.config.annotColor, 
                                                   alpha=(self.config.annotTransparency/100),
                                                   repaint=True, plot=markerPlot)
                                else:
                                    self.addRectMS(xmin, ymin, width, height, 
                                                   color=self.config.annotColor, 
                                                   alpha=(self.config.annotTransparency/100),
                                                   repaint=False, plot=markerPlot)
                    
                    # Attempt to assign charge state
                    if self.config.peakFittingHighRes:
                        # Extend peaklist with empty column
                        peakList = np.c_[peakList, np.zeros(len(peakList))]
                        # Iterate over the peaklist
                        for i, peak in enumerate(peakList):
                            mzStart = peak[0]-self.config.peakWidthAssign
                            mzEnd = peak[0]+self.config.peakWidthAssign
                            mzNarrow = getNarrow1Ddata(data=msList, mzRange=(mzStart, mzEnd))
                            if len(mzNarrow) > 0:
                                highResPeaks = detectPeaks1D(data=mzNarrow, 
                                                             window=self.config.peakWindowAssign, 
                                                             threshold=self.config.peakThresholdAssign)
                                peakDiffs = np.diff(highResPeaks[:,0])
                                if len(peakDiffs) > 0:
                                    charge = int(np.round(1/np.round(np.average(peakDiffs),4),0))
                                else:
                                    continue
                                # Assumes positive mode
                                peakList[i,2] = np.abs(charge)
                                if self.config.showIsotopes:
                                    self.addMarkerMS(xvals=highResPeaks[:,0],yvals=highResPeaks[:,1],
                                                     color=(1,0,0), marker='o',
                                                     size=3.5, plot=markerPlot) # using shortcut
                                                
                    # Add items to table (if checked)
                    if self.config.autoAddToTable:
                        if self.docs.dataType == 'Type: ORIGAMI' or self.docs.dataType == 'Type: MANUAL':
                            self.view._mgr.GetPane(self.view.panelMultipleIons).Show()
                            self.view.mzTable.Check(True)
                            self.view._mgr.Update()
                            for mz in peakList:
                                # New in 1.0.4: Added slightly assymetric envelope to the peak
                                xmin = np.round(mz[0]-(self.config.peakWidth*0.75), 2)
                                xmax = np.round(mz[0]+(self.config.peakWidth*1.25), 2)
                                try: charge = str(int(mz[2]))
                                except: charge = ""
                                intensity = np.round(mz[1]*100, 1)
                                tempList.Append([xmin, xmax, charge,"","", 
                                                 self.currentDoc, "", intensity])
                            # Removing duplicates
                            self.view.panelMultipleIons.topP.onRemoveDuplicates(evt=None)
                                            
                        elif self.docs.dataType == 'Type: Multifield Linear DT':
                            self.view._mgr.GetPane(self.view.panelLinearDT).Show()
                            self.view.multifieldTable.Check(True)
                            self.view._mgr.Update()
                            for mz in peakList:
                                xmin = np.round(mz[0]-(self.config.peakWidth*0.75), 2)
                                xmax = np.round(mz[0]+(self.config.peakWidth*1.25), 2)
                                try: charge = str(int(mz[2]))
                                except: charge = ""
                                intensity = np.round(mz[1]*100, 1)
                                tempList.Append([xmin,xmax,intensity,charge,self.currentDoc])
                            # Removing duplicates
                            self.view.panelLinearDT.bottomP.onRemoveDuplicates(evt=None)
                        elif self.docs.dataType == 'Type: CALIBRANT':
                            self.view._mgr.GetPane(self.view.panelCCS).Show()
                            self.view.ccsTable.Check(True)
                            self.view._mgr.Update()
                            for mz in peakList:
                                xmin = np.round(mz[0]-(self.config.peakWidth*0.75), 2)
                                xmax = np.round(mz[0]+(self.config.peakWidth*1.25), 2)
                                try: charge = str(int(mz[2]))
                                except: charge = ""
                                intensity = np.round(mz[1]*100, 1)
                                tempList.Append([self.currentDoc, xmin, xmax,"", charge])
                            # Removing duplicates
                            self.view.panelCCS.topP.onRemoveDuplicates(evt=None)
                            
            # Restore zoom (if fitting to narrow range)
            if self.config.currentRangePeak:
                self.onZoomMS(startX=mzRange[0],endX=mzRange[1], endY=1.05, 
                              plot=markerPlot)
        
    def onShowExtractedIons(self, evt):
        """
        This function adds rectanges and markers to the m/z window
        """
        self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        if self.currentDoc == 'Current documents': return     
        # Shortcut to mz list
        self.docs = self.documentsDict[self.currentDoc]
        if self.docs.dataType == 'Type: ORIGAMI' or self.docs.dataType == 'Type: MANUAL':
            tempList = self.view.panelMultipleIons.topP.peaklist
        elif self.docs.dataType == 'Type: Multifield Linear DT':
            tempList = self.view.panelLinearDT.bottomP.peaklist
        else: return
        
        if not self.docs.gotMS: return
        
        # Lets clear MS first
        self.onPlotMS2(self.docs.massSpectrum['xvals'], 
                       self.docs.massSpectrum['yvals'],
                       self.docs.lineColour, 
                       xlimits=self.docs.massSpectrum['xlimits'], 
                       style=None)
        # Show rectangles
        # Need to check whether there were any ions in the table already
        last = tempList.GetItemCount()-1
        ymin = 0
        height = 1.0
        for item in xrange(tempList.GetItemCount()):
            filename = tempList.GetItem(item,5).GetText()
            if filename != self.currentDoc: continue
            xmin = str2num(tempList.GetItem(item,0).GetText())
            width = str2num(tempList.GetItem(item,1).GetText())-xmin
#             self.addTextMS(xmin,0.5, str(item), 0)
            if item == last:
                self.addRectMS(xmin, ymin, width, height, color=self.config.annotColor, 
                               alpha=(self.config.annotTransparency/100),
                               repaint=True)
            else:
                self.addRectMS(xmin, ymin, width, height, color=self.config.annotColor, 
                               alpha=(self.config.annotTransparency/100),
                               repaint=True)
                                

        
        # Shortcut to mz list
        tempList = self.view.panelMultipleIons.topP.peaklist

    def onSmooth1Ddata(self, evt):
        
        self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        if self.currentDoc is None or self.currentDoc == "Current documents": return
        self.docs = self.documentsDict[self.currentDoc] 
        
        sigma = dialogs.dlgAsk('Gaussian smoothing. Select sigma', defaultValue='')
        if sigma == '': sigma = 1
        
        if evt.GetId() == ID_smooth1DdataMS:
            if self.docs.gotMS:
                msX = self.docs.massSpectrum['xvals']
                msY = self.docs.massSpectrum['yvals']
                # Smooth data
                msY = af.smooth1D(data=msY, sigma=str2num(sigma))
                msY = af.normalizeMS(inputData=msY)
                self.docs.gotSmoothMS = True
                self.docs.smoothMS = {'xvals':msX, 
                                      'yvals':msY, 
                                      'smoothSigma':sigma}
                # Plot smoothed MS
                self.onPlotMS2(msX, msY, self.docs.lineColour, 
                               xlimits=self.docs.massSpectrum['xlimits'], 
                               style=None)
                # Append to list
                self.documentsDict[self.currentDoc] = self.docs
                # Update documents tree
                self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
                
        elif evt.GetId() == ID_smooth1Ddata1DT:
            if self.docs.got1DT:
                dtX = self.docs.DT['xvals']
                dtY = self.docs.DT['yvals']
                xlabel = self.docs.DT['xlabels']
                # Smooth data
                dtY = af.smooth1D(data=dtY, sigma=str2num(sigma))
                dtY = af.normalizeMS(inputData=dtY)
                # Plot smoothed MS
                self.onPlot1DIMS2(dtX, dtY, xlabel, color=self.docs.lineColour, 
                                  style=None)
        elif evt.GetId() == ID_smooth1DdataRT:
            if self.docs.got1RT:
                rtX = self.docs.RT['xvals']
                rtY = self.docs.RT['yvals']
                xlabel = self.docs.RT['xlabels']
                # Smooth data
                rtY = af.smooth1D(data=rtY, sigma=str2num(sigma))
                rtY = af.normalizeMS(inputData=rtY)
                self.onPlotRT2(rtX, rtY, xlabel, color=self.docs.lineColour, 
                                         style=None)
                            
    def onAddBlankDocument(self, evt):

        dlg =  wx.FileDialog(self.view, "Please select a name and path for the dataset", 
                             "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            itemPath, idName = os.path.split(dlg.GetPath()) 
        else: return  
        
        self.docs = doc()             
        self.docs.title = idName
        self.docs.path = itemPath
        self.currentDoc = idName
        self.docs.userParameters = self.config.userParameters
        self.docs.userParameters['date'] = getTime()
        # Add method specific parameters
        if evt.GetId() == ID_addNewOverlayDoc:
            self.docs.dataType = 'Type: Comparison'
            self.docs.fileFormat = 'Format: ORIGAMI'
                
        elif evt.GetId() == ID_addNewCalibrationDoc:
            self.docs.dataType = 'Type: CALIBRANT'
            self.docs.fileFormat = 'Format: DataFrame'

        self.documentsDict[idName] = self.docs
        self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
            
    def save2DHTML(self, path, zvals, xvals, yvals, xlabel, ylabel, cmap, label,
                   plotType='image', openFile=False):
        """ 
        This function generates a 2D plot of the 2D data array selected in the document window
        """
        
        # Generate name for output
        if label == None: filename = ''.join([path,'\\bokeh2D.html'])
        else: filename = ''.join([path,'\\bokeh2D_', label, '.html'])
        # Get colormap
        colormap =cm.get_cmap(cmap) #choose any matplotlib colormap here
        bokehpalette = [colors.rgb2hex(m) for m in colormap(np.arange(colormap.N))]
        # Create custom tooltip
        # TODO: currently it interpolates points
        # (i.e. doesn't use the exact datapoints from the figure!)
        if plotType == 'image':
            hoverTool = HoverTool(tooltips = [(xlabel, '$x{0}'),
                                              (ylabel, '$y{0}')],
                                 point_policy = 'follow_mouse')
            TOOLS = [hoverTool,"save,pan,box_zoom,wheel_zoom, resize, crosshair, reset"]
            # Figure
            r = figure(x_range=(min(xvals), max(xvals)), y_range=(min(yvals), max(yvals)),
                       tools=TOOLS, active_drag="box_zoom", plot_width=600, 
                       plot_height=600, title=label,toolbar_location='above')
            # Add plots
            r.image(image=[zvals], x=min(xvals), y=min(yvals), dw=max(xvals), dh=max(yvals), palette=bokehpalette)
            r.quad(top=max(yvals), bottom=min(yvals), left=min(xvals), right=max(xvals), alpha=0)
            # Labels
            r.xaxis.axis_label = xlabel
            r.xaxis.axis_label_text_font_size = "16pt"
            r.xaxis.axis_label_text_font_style = 'bold'
            r.xaxis.major_label_text_font_size = "12pt"
            r.yaxis.axis_label = ylabel
            r.yaxis.axis_label_text_font_size = "16pt"
            r.yaxis.axis_label_text_font_style = 'bold'
            r.yaxis.major_label_text_font_size = "12pt"
        elif plotType == 'heatmap':
            # Flatted data to list format
            zvalsFlat = zvals.ravel(order='F')
            yvalsLong = ([yvals]*len(xvals))
            xvalsFlat = np.repeat(xvals, len(yvals))
            yvalsFlat = [item for sublist in yvalsLong for item in sublist]
            # Create dataframe
            dff = pd.DataFrame({'xvals': xvalsFlat,
                                'yvals': yvalsFlat,
                                'zvals': zvalsFlat})
            source = ColumnDataSource(dff)
            # Colormapper
            mapper = LinearColorMapper(palette=bokehpalette, 
                                       low=dff.zvals.min(), 
                                       high=dff.zvals.max())
            # New tool
            hoverTool = HoverTool(tooltips = [(xlabel, '@xvals{2}'),
                                              (ylabel, '@yvals{2}')],
                                 point_policy = 'follow_mouse')
            TOOLS = [hoverTool,"save,pan,box_zoom,wheel_zoom, resize, crosshair, reset"]
            # Create figure
            r = figure(x_range=(min(xvals), max(xvals)), 
                       y_range=(min(yvals), max(yvals)),
                       tools=TOOLS, active_drag="box_zoom", 
                       plot_width=600, 
                       plot_height=600,
                       title=label, 
                       toolbar_location='above')
            xspace = xvals[2]-xvals[1]
            yspace = yvals[2]-yvals[1]
            r.rect(x="xvals", y="yvals", 
                   width=xspace, 
                   height=yspace,
                   fill_color={'field': 'zvals', 'transform': mapper},
                   source=source,line_color=None)
            r.select_one(HoverTool)
            r.grid.grid_line_color = None
            r.axis.axis_line_color = None
            r.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
            r.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks    
            r.axis.major_tick_line_color = None
            r.yaxis.major_tick_line_color = None  # turn off y-axis major ticks
            r.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks
            r.xaxis.major_label_text_color = None  # turn off x-axis tick labels leaving space
            r.yaxis.major_label_text_color = None  # turn off y-axis tick labels leaving space 
            # Add border 
            r.outline_line_width = 2
            r.outline_line_alpha = 1
            r.outline_line_color = "black"
            # Labels
            r.xaxis.axis_label = xlabel
            r.xaxis.axis_label_text_font_size = "16pt"
            r.xaxis.axis_label_text_font_style = 'bold'
            r.xaxis.major_label_text_font_size = "12pt"
            r.yaxis.axis_label = ylabel
            r.yaxis.axis_label_text_font_size = "16pt"
            r.yaxis.axis_label_text_font_style = 'bold'
            r.yaxis.major_label_text_font_size = "12pt"
        
        save(obj=r, filename=filename, title='2D data')
        # Open file in browser
        if openFile:
            webbrowser.open(filename)        
                    
    def getImageFilename(self, prefix=False, csv=False, defaultValue='', withPath=False):
        """
        Set-up a new filename for saved images
        """
        
        if withPath:
            fileType = "Text file|*%s" % self.config.saveExtension
            dlg =  wx.FileDialog(self.view, "Save data to file...", "", "", fileType,
                                    wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            dlg.SetFilename(defaultValue)
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                return filename
            else:
                return None
        elif not prefix:
            saveFileName = dialogs.dlgAsk('Please enter a new filename for the images. Names will be appended with the item keyword.', 
                                          defaultValue=defaultValue)
        else:
            if not csv:
                saveFileName = dialogs.dlgAsk('Please enter a new prefix for the images. Names will be appended with the item keyword.', 
                                              defaultValue=defaultValue)
            else:
                saveFileName = dialogs.dlgAsk('Please enter a new prefix for the output file. Names will be appended with the item keyword.', 
                                              defaultValue=defaultValue)

            
            
        return saveFileName
    
    def onUpdateXYaxisLabels(self, evt):
        """ 
        Change xy-axis labels
        """
        
        # TODO Currently doesn't work for manual dataset (i.e. extracted/combined ions!)
        # Get current document info
        self.currentDoc, selectedItem, selectedText = self.view.panelDocuments.topP.documents.enableCurrentDocument(getSelected=True)
        indent = self.view.panelDocuments.topP.documents.getItemIndent(selectedItem)
        selectedItemParentText = None
        if indent > 2:
            selectedItemParent, selectedItemParentText = self.view.panelDocuments.topP.documents.getParentItem(selectedItem,2, 
                                                                                                               getSelected=True)
        else: pass
        self.document = self.documentsDict[self.currentDoc]
        
        # Determine which dataset is used
        if selectedText == None: 
            data = self.document.IMS2D
        elif selectedText == '2D drift time':
            data = self.document.IMS2D
        elif selectedText == 'Processed 2D IM-MS':
            data = self.document.IMS2Dprocess
        elif selectedItemParentText == 'Extracted 2D IM-MS (multiple ions)' and selectedText != None:
            data = self.document.IMS2Dions[selectedText]
        elif selectedItemParentText == 'Combined CV 2D IM-MS (multiple ions)' and selectedText != None:
            data = self.document.IMS2DCombIons[selectedText]
        elif selectedItemParentText == 'Processed 2D IM-MS (multiple ions)' and selectedText != None:
            data = self.document.IMS2DionsProcess[selectedText]
        elif selectedItemParentText == 'Input data' and selectedText != None:
            data = self.document.IMS2DcompData[selectedText]
        # 1D data
        elif selectedText == '1D drift time':
            data = self.document.DT
        else: 
            data = self.document.IMS2D
        
        # Add default values
        if 'defaultX' not in data:
            data['defaultX'] =  {'xlabels': data['xlabels'],
                                 'xvals': data['xvals']}
        if 'defaultY' not in data:
            data['defaultY'] =  {'ylabels': data.get('ylabels','Intensity'),
                                 'yvals': data['yvals']}
        
        
        # If either label is none, then ignore it
        newXlabel, newYlabel = None, None
        restoreX, restoreY = False, False
        
        # Determine what the new label should be
        if evt.GetId() in [ID_xlabel2Dscans, ID_xlabel2DcolVolt,
                           ID_xlabel2DlabFrame, ID_xlabel2DmassToCharge,
                           ID_xlabel2DmassToCharge, ID_xlabel2Dmz,
                           ID_xlabel2Dwavenumber, ID_xlabel2Dwavenumber,
                           ID_xlabel2Drestore]:
            
            # If changing X-labels
            newXlabel = 'Scans'
            restoreX = False
            if evt.GetId() == ID_xlabel2Dscans: newXlabel = 'Scans'
            elif evt.GetId() == ID_xlabel2DcolVolt: newXlabel = 'Collision Voltage (V)'
            elif evt.GetId() == ID_xlabel2DlabFrame: newXlabel = 'Lab Frame Energy (eV)'
            elif evt.GetId() == ID_xlabel2DmassToCharge: newXlabel = 'Mass-to-charge (Da)'
            elif evt.GetId() == ID_xlabel2Dmz: newXlabel = 'm/z (Da)'
            elif evt.GetId() == ID_xlabel2Dwavenumber: newXlabel =  u'Wavenumber (cm⁻¹)'
            elif evt.GetId() == ID_xlabel2Drestore:
                newXlabel = data['defaultX']['xlabels']
                restoreX = True
            elif newXlabel == "" or newXlabel == None: 
                newXlabel = 'Scans'
        
        
        if evt.GetId() in [ID_ylabel2Dbins, ID_ylabel2Dms,
                           ID_ylabel2Dccs, ID_ylabel2Drestore]:
            # If changing Y-labels
            restoreY = False
            newYlabel = 'Drift time (bins)'
            if evt.GetId() == ID_ylabel2Dbins: newYlabel = 'Drift time (bins)'
            elif evt.GetId() == ID_ylabel2Dms: newYlabel = 'Drift time (ms)'
            elif evt.GetId() == ID_ylabel2Dccs: newYlabel = u'Collision Cross Section (Å²)'
            elif evt.GetId() == ID_ylabel2Drestore: 
                newYlabel = data['defaultY']['ylabels'] #Drift time (bins)'
                restoreY = True
            elif newYlabel == "" or newYlabel == None: newYlabel = 'Drift time (bins)'
            
        # 1D data
        if evt.GetId() in [ID_ylabel1Dbins, ID_ylabel1Dms, ID_ylabel1Dccs]:
            newXlabel = 'Drift time (bins)'
            restoreX = False
            if evt.GetId() == ID_ylabel1Dbins: newXlabel = 'Drift time (bins)'
            elif evt.GetId() == ID_ylabel1Dms: newXlabel = 'Drift time (ms)'
            elif evt.GetId() == ID_ylabel1Dccs: newXlabel = u'Collision Cross Section (Å²)'
                
        if restoreX: 
            newXvals = data['defaultX']['xvals'] 
            data['xvals'] = newXvals
            data['xlabels'] = newXlabel
            
        if restoreY: 
            newYvals = data['defaultY']['yvals']
            data['yvals'] = newYvals
            data['ylabels'] = newYlabel
        
        # Change labels
        if newXlabel != None:
            oldXLabel = data['xlabels']
            data['xlabels'] = newXlabel # Set new x-label
            newXvals= self.onChangeAxes2D(data['xvals'], 
                                          oldXLabel, 
                                          newXlabel, 
                                          charge=data.get('charge',1),
                                          pusherFreq=self.document.parameters.get('pusherFreq',1000),
                                          defaults=data['defaultX'])
            data['xvals'] = newXvals # Set new x-values
        
        if newYlabel != None:
            oldYLabel = data['ylabels']
            data['ylabels'] = newYlabel
            newYvals= self.onChangeAxes2D(data['yvals'], 
                                          oldYLabel, 
                                          newYlabel,
                                          pusherFreq=self.document.parameters.get('pusherFreq',1000),
                                          defaults=data['defaultY'])
            data['yvals'] = newYvals
                    
        # Replace data in the dictionary
        if selectedText == None: 
            self.document.IMS2D = data
        elif selectedText == '2D drift time':
            self.document.IMS2D = data
        elif selectedText == 'Processed 2D IM-MS':
            self.document.IMS2Dprocess = data
        elif selectedItemParentText == 'Extracted 2D IM-MS (multiple ions)' and selectedText != None:
            self.document.IMS2Dions[selectedText] = data
        elif selectedItemParentText == 'Combined CV 2D IM-MS (multiple ions)' and selectedText != None:
            self.document.IMS2DCombIons[selectedText] = data
        elif selectedItemParentText == 'Processed 2D IM-MS (multiple ions)' and selectedText != None:
            self.document.IMS2DionsProcess[selectedText] = data
        elif selectedItemParentText == 'Input data' and selectedText != None:
            self.document.IMS2DcompData[selectedText] = data
        # 1D data
        elif selectedText == '1D drift time':
            self.document.DT = data
        else: 
            self.document.IMS2D
            
        # Append to list
        self.documentsDict[self.document.title] = self.document
        
        # Try to plot that data
        try:
            self.view.panelDocuments.topP.documents.onShowPlot(evt=None)
        except: pass
        
# ---

    def onChangeChargeState(self, evt):

        self.currentDoc, selectedItem, selectedText = self.view.panelDocuments.topP.documents.enableCurrentDocument(getSelected=True)
        if self.currentDoc is None or self.currentDoc == "Current documents": return
        indent = self.view.panelDocuments.topP.documents.getItemIndent(selectedItem)
        selectedItemParentText = ''
        if indent > 2:
            selectedItemParent, selectedItemParentText = self.view.panelDocuments.topP.documents.getParentItem(selectedItem,2, 
                                                                                                               getSelected=True)
        else: pass

        self.document = self.documentsDict[self.currentDoc]
        
        # Check that the user hasn't selected the header
        if (selectedText == 'Extracted 2D IM-MS (multiple ions)' or
            selectedText == 'Combined CV 2D IM-MS (multiple ions)' or 
            selectedText == 'Processed 2D IM-MS (multiple ions)' or 
            selectedText == 'Input data'):
            # Give an error
            dialogs.dlgBox(exceptionTitle='Error', 
                           exceptionMsg= "Please select an ion in the Document Panel to assign a charge state",
                           type="Error")
            return
        
        currentCharge = self.view.panelDocuments.topP.documents.onGetItemData(dataType='charge')
        
        charge = dialogs.dlgAsk('Assign charge state to selected item.',
                                defaultValue=str(currentCharge))
        
        if charge == '' or charge == 'None':
            return 
            
        # Replace data in the dictionary
        if selectedText == None: 
            self.document.IMS2D['charge'] = str2int(charge)
        elif selectedText == '2D drift time':
            self.document.IMS2D['charge'] = str2int(charge)
        elif selectedText == 'Processed 2D IM-MS':
            self.document.IMS2Dprocess['charge'] = str2int(charge)
        elif selectedItemParentText == 'Extracted 2D IM-MS (multiple ions)' and selectedText != None:
            self.document.IMS2Dions[selectedText]['charge'] = str2int(charge)
        elif selectedItemParentText == 'Combined CV 2D IM-MS (multiple ions)' and selectedText != None:
            self.document.IMS2DCombIons[selectedText]['charge'] = str2int(charge)
        elif selectedItemParentText == 'Processed 2D IM-MS (multiple ions)' and selectedText != None:
            self.document.IMS2DionsProcess[selectedText]['charge'] = str2int(charge)
        elif selectedItemParentText == 'Input data' and selectedText != None:
            self.document.IMS2DcompData[selectedText]['charge'] = str2int(charge)
        elif selectedItemParentText == 'Combined CV RT IM-MS (multiple ions)' and selectedText != None:
            self.document.IMSRTCombIons[selectedText]['charge'] = str2int(charge)
        elif selectedItemParentText == 'Extracted 1D IM-MS (multiple ions)' and selectedText != None:
            self.document.IMS1DdriftTimes[selectedText]['charge'] = str2int(charge)
        else: 
            self.document.IMS2D
            
        # Since charge state is inherent to the m/z range, it needs to be
        # changed iteratively for each dataset
        if any(selectedItemParentText in type for type in ['Extracted 2D IM-MS (multiple ions)',
                                                           'Combined CV 2D IM-MS (multiple ions)',
                                                           'Processed 2D IM-MS (multiple ions)',
                                                           'Combined CV RT IM-MS (multiple ions)',
                                                           'Extracted 1D IM-MS (multiple ions)']):
            if selectedText in self.document.IMS2Dions:
                self.document.IMS2Dions[selectedText]['charge'] = str2int(charge)
            if selectedText in self.document.IMS2DCombIons:
                self.document.IMS2DCombIons[selectedText]['charge'] = str2int(charge)
            if selectedText in self.document.IMS2DionsProcess:
                self.document.IMS2DionsProcess[selectedText]['charge'] = str2int(charge)
            if selectedText in self.document.IMSRTCombIons:
                self.document.IMSRTCombIons[selectedText]['charge'] = str2int(charge)
            if selectedText in self.document.IMS1DdriftTimes:
                self.document.IMS1DdriftTimes[selectedText]['charge'] = str2int(charge)
            # Only to MANUAL data type
            for key in self.document.IMS1DdriftTimes:
                splitText = re.split('-| |,|', key)
                if '-'.join([splitText[0],splitText[1]]) == selectedText:
                    self.document.IMS1DdriftTimes[key]['charge'] = str2int(charge)

                
            # We also have to check if there is data in the table
            if self.document.dataType == 'Type: ORIGAMI' or self.document.dataType == 'Type: MANUAL':
                splitText = re.split('-| |,|', selectedText)
                row = self.view.panelMultipleIons.topP.findItem(splitText[0],splitText[1], self.currentDoc)
                if row != None:
                    self.view.panelMultipleIons.topP.peaklist.SetStringItem(index=row, 
                                                col=self.config.peaklistColNames['charge'], 
                                                label=str(charge))

        
            
        # Append to list
        self.documentsDict[self.document.title] = self.document
                
    def onChangeAxes2D(self, data, oldLabel, newLabel, charge=1, 
                       pusherFreq=1000, defaults=None):
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
        if charge == "None" or charge == "": charge = 1
        else: charge = str2int(charge)
        
        if pusherFreq == "None" or pusherFreq == "": pusherFreq = 1000
        else: pusherFreq = str2num(pusherFreq)

        msg = 'Currently just changing label. Proper conversion will be coming soon'
        # Check whether labels were changed
        if oldLabel != newLabel:
            
            # Convert Y-axis labels
            if oldLabel == 'Drift time (bins)' and newLabel == 'Drift time (ms)':
                newVals = (data*pusherFreq)/1000
                return newVals
            elif newLabel == 'Drift time (bins)' and oldLabel == 'Drift time (ms)':
                newVals = (data/pusherFreq)*1000
                return newVals
            elif newLabel == u'Collision Cross Section (Å²)' and oldLabel == 'Drift time (ms)':
                self.view.SetStatusText(msg, number = 3)
                newVals = data
            elif oldLabel == u'Collision Cross Section (Å²)' and newLabel == 'Drift time (ms)':
                self.view.SetStatusText(msg, number = 3)
                newVals = data
            elif newLabel == u'Collision Cross Section (Å²)' and oldLabel == 'Drift time (bins)':
                self.view.SetStatusText(msg, number = 3)
                newVals = data
            elif oldLabel == u'Collision Cross Section (Å²)' and newLabel == 'Drift time (bins)':
                self.view.SetStatusText(msg, number = 3)
                newVals = data
            else: newVals = data

            # Convert X-axis labels
            # Convert CV --> LFE
            if oldLabel == 'Collision Voltage (V)' and newLabel == 'Lab Frame Energy (eV)':
                if isinstance(data, list):
                    newVals = [value * charge for value in data]
                else:
                    newVals = data*charge
            # Convert Lab frame energy --> collision voltage
            elif newLabel == 'Collision Voltage (V)' and oldLabel == 'Lab Frame Energy (eV)':
                if isinstance(data, list):
                    newVals = [value / charge for value in data]
                else:
                    newVals = data/charge
            # Convert LFE/CV --> scans
            elif newLabel == 'Scans' and (oldLabel == 'Lab Frame Energy (eV)' or 
                                          oldLabel == 'Collision Voltage (V)'):
                newVals = 1+np.arange(len(data))
            # Convert Scans --> LFE/CV 
            elif oldLabel == 'Scans' and (newLabel == 'Lab Frame Energy (eV)' or 
                                          newLabel == 'Collision Voltage (V)'):
                # Check if defaults were provided
                if defaults is None: newVals = data
                else:
                    if (defaults['xlabels'] == 'Lab Frame Energy (eV)' or
                        defaults['xlabels'] == 'Collision Voltage (V)'):
                        newVals = defaults['xvals']
                    else: newVals = data   
            else: newVals = data
            # Return new values
            return newVals
        # labels were not changed
        else: 
            return data

    def onCmapNormalization(self, data, min=0, mid=50, max=100):
        """
        This function alters the colormap intensities
        """
        # Determine what are normalization values
        # Convert from % to number
        cmapMin = (np.max(data)*min)/100
        cmapMid = (np.max(data)*mid)/100
        cmapMax = (np.max(data)*max)/100

        cmapNormalization = MidpointNormalize(midpoint=cmapMid, 
                                              vmin=cmapMin, 
                                              vmax=cmapMax, clip=False)
        return cmapNormalization
          

#===============================================================================
#  INTERACTIVE PLOTS FUNCTIONS
#===============================================================================

    def onOpenPeakListCSV(self, evt):
        """
        This function opens a formatted CSV file with peaks
        """
        dlg = wx.FileDialog(self.view, "Choose a text file (m/z, window size, charge):", 
                            wildcard = "*.csv;*.txt",
                           style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_CANCEL: return
        else:
            # Create shortcut                
            tempList = self.view.panelMultipleIons.topP.peaklist
            delimiter, trash = checkExtension(input=dlg.GetPath().encode('ascii', 'replace') )
            peaklist = pd.read_csv(dlg.GetPath(), delimiter=delimiter)
            try:
                peaklist['m/z']
            except KeyError:
                msg = "Please make sure your file contains headers. i.e. m/z | window | z (optional)"
                dialogs.dlgBox(exceptionTitle='Incorrect input', 
                               exceptionMsg= msg,
                               type="Error")
                return
            for peak in xrange(len(peaklist)):
                
                # Determine window size
                if self.config.useInternalMZwindow:
                    mzAdd = self.config.mzWindowSize
                else:
                    try:
                        mzAdd = peaklist['window'][peak]
                    except KeyError:
                        msg = "Please make sure your file contains headers. i.e. m/z | window | z (optional)"
                        dialogs.dlgBox(exceptionTitle='Incorrect input', 
                                       exceptionMsg= msg,
                                       type="Error")
                        return
                # Generate mz start/end
                mzMin = np.round((peaklist['m/z'][peak]-mzAdd),2)
                mzMax = np.round((peaklist['m/z'][peak]+mzAdd),2)
                # Get charge of ion
                try:
                    charge = peaklist['z'][peak]
                except KeyError: charge = ''
                # Get label of the ion
                try:
                    label = peaklist['label'][peak]
                except KeyError: label = ''
                tempList.Append([str(mzMin), str(mzMax), str(charge), '','','','','',str(label)])
                
        self.view.mzTable.Check(True)
        self.view._mgr.GetPane(self.view.panelMultipleIons).Show()
        self.view._mgr.Update()
        dlg.Destroy()

    def onUpdateColormap(self, evt=None):
        """
        Updates colormap for current document
        """
        self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        if not self.currentDoc: 
            document = None
        elif self.currentDoc == 'Current documents': return
        else:
            document = self.documentsDict[self.currentDoc]
        # Return
        return document

    def testXYmaxVals(self,values=None):
        """
        This function checks whether the x/y axis labels should be adjusted (divided)
        to adjust their size
        """
        if not hasattr(values, "__len__"):
            if 10000 < values <= 1000000: divider = 1000
            elif values > 1000000: divider = 1000000
            else: divider = 1
        elif 10000 < max(values) <= 1000000: divider = 1000
        elif  max(values) > 1000000: divider = 1000000
        else: divider = 1
        return divider    

    def config2memory(self, e=None):
        """
        This function loads all values from the GUI into memory (config container)
        """
        self.view.panelControls.exportToConfig()

    def onDocumentColour(self, evt):
        """Get new colour"""
        try:
            self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        except: return None
        if self.currentDoc == 'Current documents': return
        
        document = self.documentsDict[self.currentDoc]
        # Check document
        if not self.documentsDict: 
            wx.Bell()
            return
        
        # Show dialog and get new colour
        dlg = wx.ColourDialog(self.view)
        dlg.GetColourData().SetChooseFull(True)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            newColour = list(data.GetColour().Get())
            document.lineColour = list([np.float(newColour[0])/255,
                                        np.float(newColour[1])/255,
                                        np.float(newColour[2])/255])
            dlg.Destroy()
        else:
            return
        
        self.view.panelControls.colorBtn.SetBackgroundColour(newColour)
        # Update plot
        self.view.panelDocuments.topP.documents.onShowPlot()
        
    def onSelectProtein(self, evt):
        if evt.GetId() == ID_selectCalibrant: 
            mode = 'calibrants'
        else: 
            mode = 'proteins'
        
        self.selectProteinDlg = panelCalibrantDB(self.view, self, self.config, mode)
        self.selectProteinDlg.Show()

    def onCalibrantRawDirectory(self, e=None):
        """
        This function opens calibrant file
        """
        
        # Reset arrays
        dlg = wx.DirDialog(self.view, "Choose a MassLynx file:",
                           style=wx.DD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            tstart = time.clock()
            # Check whether appropriate calibration file was selected
            path = self.checkIfRawFile(dlg.GetPath())
            if path is None: 
                msg = "Are you sure this was a MassLynx (.raw) file? Please load file in correct file format."
                dialogs.dlgBox(exceptionTitle='Please load MassLynx (.raw) file', 
                               exceptionMsg= msg,
                               type="Error")
                return
            print "You chose %s" % dlg.GetPath()   
            # Update statusbar      
            self.view.SetStatusText(dlg.GetPath(), number = 4)
            # Get experimental parameters
            parameters = self.config.importMassLynxInfFile(path=dlg.GetPath())
            # Mass spectra
            ml.rawExtractMSdata(fileNameLocation=dlg.GetPath(), 
                                driftscopeLocation=self.config.driftscopePath)
            msDataX, msDataY = ml.rawOpenMSdata(path=dlg.GetPath())
            xlimits = [parameters['startMS'],parameters['endMS']]
            # RT
            ml.rawExtractRTdata(fileNameLocation=dlg.GetPath(), 
                                driftscopeLocation=self.config.driftscopePath)
            rtDataY, rtDataYnorm = ml.rawOpenRTdata(path=dlg.GetPath(), 
                                                    norm=True)   
            xvalsRT = np.arange(1,len(rtDataY)+1)
            
            # DT
            ml.rawExtract1DIMSdata(fileNameLocation=dlg.GetPath(), 
                                   driftscopeLocation=self.config.driftscopePath)
            imsData1D =  ml.rawOpen1DRTdata(path=dlg.GetPath(),
                                                    norm=self.config.normalize)
            xvalsDT = np.arange(1,len(imsData1D)+1)
            
            # Update status bar with MS range
            txt = ''.join(["MS range: ", num2str(parameters['startMS']), "-", 
                           num2str(parameters['endMS'])])
            self.view.SetStatusText(txt, 1)
            txt = ''.join(['MSMS: ', num2str(parameters['setMS'])])
            self.view.SetStatusText(txt, 2)
            tend= time.clock()
            self.view.SetStatusText('Total time to open file: %.2gs' % (tend-tstart), 3)
            
            # Add info to document 
            temp, idName = os.path.split(dlg.GetPath())
            idName = (''.join([idName])).encode('ascii', 'replace')   
            self.docs = doc()             
            self.docs.title = idName
            self.currentDoc = idName # Currently plotted document
            self.docs.path = dlg.GetPath()
            self.docs.userParameters = self.config.userParameters
            self.docs.userParameters['date'] = getTime()
            self.docs.parameters = parameters
            self.docs.dataType = 'Type: CALIBRANT'
            self.docs.fileFormat = 'Format: MassLynx (.raw)'
            self.docs.corrC = parameters['corrC']
            # Add data
            self.docs.gotMS = True
            self.docs.massSpectrum = {'xvals':msDataX,
                                      'yvals':msDataY,
                                      'xlabels':'m/z (Da)',
                                      'xlimits':xlimits}
            self.docs.got1RT = True
            self.docs.RT = {'xvals':xvalsRT, 
                            'yvals':rtDataYnorm,
                            'xlabels':'Scans'}
            self.docs.got1DT = True
            self.docs.DT = {'xvals':xvalsDT, 
                            'yvals':imsData1D,
                            'xlabels':'Drift time (bins)',
                            'ylabels':'Intensity'}
            
            
            # Add plots
            self.onPlotRT2(xvalsRT, rtDataYnorm, 'Scans', self.docs.lineColour, self.docs.style)
            self.onPlotMSDTCalibration(msX=msDataX, 
                                       msY=msDataY,
                                       xlimits=xlimits, 
                                       dtX=xvalsDT, 
                                       dtY=imsData1D, 
                                       xlabelDT = 'Drift time (bins)',
                                       color=self.docs.lineColour)
            
            self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Calibration'])
            # Append to list
            self.documentsDict[idName] = self.docs
            # Update documents tree
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)   

        dlg.Destroy()
        return None
            
    def onAddCalibrantMultiple(self, evt):
        
        tempList = self.view.panelCCS.topP.peaklist
        for row in range(tempList.GetItemCount()):
            if evt.GetId() == ID_extractCCScalibrantAll: pass          
            elif evt.GetId() == ID_extractCCScalibrantSelected:
                if not tempList.IsChecked(index=row): continue
                            
            # Get values
            filename = tempList.GetItem(itemId=row, col=self.config.ccsTopColNames['filename']).GetText()
            mzStart = str2num(tempList.GetItem(itemId=row, col=self.config.ccsTopColNames['start']).GetText())
            mzEnd = str2num(tempList.GetItem(itemId=row, col=self.config.ccsTopColNames['end']).GetText())
            rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
            
            # Get the document
            document = self.documentsDict[filename]
            if document.fileFormat == 'Format: DataFrame':
                print('Skipping %s as this is a DataFrame document.' % rangeName)
                continue

            ml.rawExtract1DIMSdata(fileNameLocation=str(document.path), 
                                   driftscopeLocation=self.config.driftscopePath,
                                   mzStart=mzStart, mzEnd=mzEnd)
            
            # Load 1D data
            yvalsDT =  ml.rawOpen1DRTdata(path=document.path, norm=self.config.normalize)
            mphValue = (max(yvalsDT))*0.2 # 20 % cutoff
            # Get pusher 
            pusherFreq = document.parameters.get('pusherFreq', 1)
            
            if pusherFreq != 1: xlabel = 'Drift time (ms)'
            else: xlabel = 'Drift time (bins)'
            # Create x-labels in ms
            xvalsDT = (np.arange(1,len(yvalsDT)+1)*pusherFreq)/1000
    
            # Detect peak
            ind = detectPeaks(x=yvalsDT, mph=mphValue)
            if len(ind) > 1:
                self.view.SetStatusText('Found more than one peak. Selected the first one', 3)
                tD = np.round(xvalsDT[ind[0]],2)
                print(ind[0], tD)
                yval = np.round(yvalsDT[ind[0]],2)
                yval = af.normalizeMS(yval)
            elif len(ind) == 0: 
                self.view.SetStatusText('Found no peaks', 3)
                tD = "" 
            else:
                self.view.SetStatusText('Found one peak', 3)
                tD = np.round(xvalsDT[ind[0]],2)
                print(ind[0], tD)
                yval = np.round(yvalsDT[ind[0]],2)
                yval = af.normalizeMS(yval)
                 
            # Add data to document
            protein, charge, CCS, gas, mw = None, None, None, None, None
            
            # Check whether the document has molecular weight
            mw = document.moleculeDetails.get('molWeight',None)
            protein = document.moleculeDetails.get('protein', None)
            
            document.gotCalibration = True
            document.calibration[rangeName] = {'xrange':[mzStart, mzEnd],
                                               'xvals':xvalsDT,
                                               'yvals':yvalsDT,
                                               'xcentre':((mzEnd+mzStart)/2),
                                               'protein':protein, 
                                               'charge':charge,
                                               'ccs':CCS,'tD':tD, 
                                               'gas':gas,
                                               'xlabels':xlabel,
                                               'peak': [tD,yval],
                                               'mw':mw
                                               } 
            # Plot
            self.onPlot1DTCalibration(dtX=xvalsDT, 
                                      dtY=yvalsDT, 
                                      xlabel=xlabel, 
                                      color=document.lineColour)
            
            if tD != "":
                self.addMarkerMS(xvals=tD,
                                 yvals=yval,
                                 color=self.config.annotColor, 
                                 marker=self.config.markerShape,
                                 size=self.config.markerSize,
                                 plot='CalibrationDT')
            
        self.view.panelDocuments.topP.documents.addDocument(docData = document)
        self.documentsDict[document.title] = document
                
    def onAddCalibrant(self, path=None, mzStart=None, mzEnd=None, mzCentre=None,
                       pusherFreq=None, tDout=False, e=None):
        """
        Extract and plot 1DT information for selected m/z range
        """
        
        # Figure out what is the current document
        self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        if self.currentDoc == 'Current documents': return
        document = self.documentsDict[self.currentDoc]
        
        # Determine the m/z range to extract
        ml.rawExtract1DIMSdata(fileNameLocation=path, 
                               driftscopeLocation=self.config.driftscopePath,
                               mzStart=mzStart, mzEnd=mzEnd)
        # Load 1D data
        yvalsDT =  ml.rawOpen1DRTdata(path=path, norm=self.config.normalize)
        mphValue = (max(yvalsDT))*0.2 # 20 % cutoff
        if pusherFreq != 1: xlabel = 'Drift time (ms)'
        else: xlabel = 'Drift time (bins)'
        # Create x-labels in ms
        xvalsDT = (np.arange(1,len(yvalsDT)+1)*pusherFreq)/1000 

        # Detect peak
        ind = detectPeaks(x=yvalsDT, mph=mphValue)
        if len(ind) > 1:
            self.view.SetStatusText('Found more than one peak. Selected the first one', 3)
            tD = np.round(xvalsDT[ind[0]],2)
            yval = np.round(yvalsDT[ind[0]],2)
            yval = af.normalizeMS(yval) # just puts it in the middle of the peak
        elif len(ind) == 0: 
            self.view.SetStatusText('Found no peaks', 3)
            tD = "" 
        else:
            self.view.SetStatusText('Found one peak', 3)
            tD = np.round(xvalsDT[ind[0]],2)
            yval = np.round(yvalsDT[ind[0]],2)
            yval = af.normalizeMS(yval) # just puts it in the middle of the peak

        # Add data to document
        protein, charge, CCS, gas, mw = None, None, None, None, None
        
        # Check whether the document has molecular weight
        mw = document.moleculeDetails.get('molWeight',None)
        protein = document.moleculeDetails.get('protein', None)

        document.gotCalibration = True
        rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
        document.calibration[rangeName] = {'xrange':[mzStart, mzEnd],
                                           'xvals':xvalsDT,
                                           'yvals':yvalsDT,
                                           'xcentre':((mzEnd+mzStart)/2),
                                           'protein':protein, 
                                           'charge':charge,
                                           'ccs':CCS,
                                           'tD':tD, 
                                           'gas':gas,
                                           'xlabels':xlabel,
                                           'peak': [tD,yval],
                                           'mw':mw
                                           }
        # Plot
        self.onPlot1DTCalibration(dtX=xvalsDT, 
                                  dtY=yvalsDT, 
                                  xlabel='Drift time (ms)', 
                                  color=document.lineColour)
        
        if tD != "":
            self.addMarkerMS(xvals=tD,
                             yvals=yval,
                             color=self.config.annotColor, 
                             marker=self.config.markerShape,
                             size=self.config.markerSize,
                             plot='CalibrationDT')
        
        self.view.panelDocuments.topP.documents.addDocument(docData = document)
        self.documentsDict[document.title] = document
        if tDout:
            return tD
        
    def OnBuildCCSCalibrationDataset(self, evt):
        
        # Create temporary dictionary
        tempDict = {}
        self.currentCalibrationParams = []
        
        # Shortcut to the table
        tempList = self.view.panelCCS.topP.peaklist
        if tempList.GetItemCount() == 0: 
            self.view.SetStatusText('Cannot build calibration curve as the calibration list is empty. Load data first.', 3)
            
        try:
            self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        except: return
        if self.currentDoc == "Current documents": return
        
        # Check if the currently selected document is Calibration dataframe file
        if (self.documentsDict[self.currentDoc].dataType == 'Type: CALIBRANT' and 
            self.documentsDict[self.currentDoc].fileFormat == 'Format: DataFrame'):
            self.docs = self.documentsDict[self.currentDoc]
            self.view.SetStatusText('Using document: ' + self.docs.title.encode('ascii', 'replace'), 3)
        else:
            print('Checking if there is a calibration document')
            docList = self.checkIfAnyDocumentsAreOfType(type='Type: CALIBRANT', 
                                                        format = 'Format: DataFrame')
            if len(docList) == 0:
                print('Did not find appropriate document.')
                dlg =  wx.FileDialog(self.view, "Please select a name for the calibration document", 
                                     "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                if dlg.ShowModal() == wx.ID_OK:
                    path, idName = os.path.split(dlg.GetPath()) 
                else: return
                    
                # Create document
                self.docs = doc()
                self.docs.title = idName
                self.docs.path = path
                self.docs.userParameters = self.config.userParameters
                self.docs.userParameters['date'] = getTime()
                self.docs.dataType = 'Type: CALIBRANT'
                self.docs.fileFormat = 'Format: DataFrame'
            else:
                self.selectDocDlg = panelSelectDocument(self.view, self, docList)
                if self.selectDocDlg.ShowModal() == wx.ID_OK: 
                    pass
                
                # Check that document exists
                if self.currentDoc == None: 
                    self.view.SetStatusText('Please select CCS calibration document', 3)
                    return
                
                self.docs = self.documentsDict[self.currentDoc]
                self.view.SetStatusText('Using document: ' + self.docs.title.encode('ascii', 'replace'), 3)
                
        selectedIon =  None
        calibrationDict = {}
        # Update CCS dataset
        for caliID in xrange(tempList.GetItemCount()):
            # Only add info if dataset was checked
            if tempList.IsChecked(index=caliID):
                # Get document info
                selectedItem = tempList.GetItem(caliID,self.config.ccsTopColNames['filename']).GetText()
                mzStart = tempList.GetItem(caliID,self.config.ccsTopColNames['start']).GetText()
                mzEnd = tempList.GetItem(caliID,self.config.ccsTopColNames['end']).GetText()
                selectedIon = ''.join([str(mzStart),'-',str(mzEnd)])
                document = self.documentsDict[selectedItem]
                # Add to dictionary
                calibrationDict[selectedIon] = document.calibration[selectedIon]
                self.docs.gotCalibration = True
                self.docs.calibration[selectedIon] = calibrationDict[selectedIon]


        if len(calibrationDict) == 0: 
            self.view.SetStatusText('The calibration dictionary was empty. Select items in the table first', 3)
            return
          
        if selectedIon == None: 
            self.view.SetStatusText('Please select items in the table - otherwise CCS calibration cannot be created', 3)
            return
        
        # Determine what gas is used - selects it based on the last value in the list
        gas = self.config.elementalMass[calibrationDict[selectedIon]['gas']]                  
        self.docs.gas = gas

        # Determine the c correction factor
        if isempty(self.docs.corrC): 
            self.view.SetStatusText('Missing TOF correction factor - you can modify the value in the Document Information Panel', 3)
            return
                  
        # Build dataframe
        df = pd.DataFrame(columns=['m/z','z','tD','MW','CCS','RedMass','tDd','CCSd','lntDd',
                                   'lnCCSd','tDdd'], 
                          index=np.arange(0,len(calibrationDict)))
 
        # Populate dataframe
        for i, key in enumerate(calibrationDict):
            charge = calibrationDict[key]['charge']
            ccs = calibrationDict[key]['ccs']
            tD = calibrationDict[key]['tD']
            if not isnumber(charge) or not isnumber(ccs) or not isnumber(tD):
                print('continuing')
                continue
            else:
                if isnumber(calibrationDict[key]['mw']):
                    xcentre = ((self.config.elementalMass['Hydrogen']*charge)+
                                calibrationDict[key]['mw']/charge)
                else: xcentre = calibrationDict[key]['xcentre']
                df['m/z'].loc[i] = xcentre
                df['z'].loc[i] = charge
                df['CCS'].loc[i] = ccs
                df['tD'].loc[i] = tD

                
        # Remove rows with NaNs
        df = df.dropna(how='all')
        if len(df) == 0: 
            self.view.SetStatusText('Please make sure you fill in appropriate parameters', 3)
            return
         
        # Compute variables
        df['MW'] = (df['m/z']-(self.config.elementalMass['Hydrogen']*df['z']))*df['z']  # calculate molecular weight
        df['RedMass'] = ((df['MW']*self.docs.gas)/(df['MW']+self.docs.gas)) # calculate reduced mass
        df['tDd'] = (df['tD']-((self.docs.corrC*df['m/z'].apply(sqrt))/1000)) # corrected drift time
        df['CCSd'] = df['CCS']/(df['z']*(1/df['RedMass']).apply(sqrt)) # corrected ccs
        df['lntDd'] = df['tDd'].apply(log) # log drift time
        df['lnCCSd'] = df['CCSd'].apply(log) # log ccs
         
        # Compute linear regression properties
        outLinear = linregress(df['tDd'].astype(np.float64), df['CCSd'].astype(np.float64))
        slopeLinear, interceptLinear = outLinear[0], outLinear[1]
        r2Linear = outLinear[2]*outLinear[2]
                
        # Compute power regression properties
        out = linregress(df['lntDd'], df['lnCCSd'])
        slope, intercept = out[0], out[1]
        df['tDdd'] = df['tDd'].pow(slope)*df['z']*df['RedMass'].apply(sqrt)
        
        outPower = linregress(df['tDdd'].astype(np.float64), df['CCS'].astype(np.float64))
        slopePower, interceptPower = outPower[0], outPower[1]
        r2Power = outPower[2]*outPower[2]

        # Add logarithmic method

        df.fillna('')
        calibrationParams = {'linear': [slopeLinear, interceptLinear, r2Linear],
                             'power' : [slopePower,interceptPower, r2Power],
                             'powerParms' : [slope, intercept],
                             'gas': gas}

        # Add calibration DataFrame to document
        self.docs.gotCalibrationParameters = True
        self.docs.calibrationParameters = {'dataframe':df,
                                           'parameters':calibrationParams}
        
        # Calibration fit line
        xvalsLinear, yvalsLinear = af.abline(np.asarray((df.tDd.min(), df.tDd.max())), 
                                          slopeLinear, interceptLinear)
        xvalsPower, yvalsPower = af.abline(np.asarray((df.tDdd.min(), df.tDdd.max())), 
                                          slopePower, interceptPower)
        # Plot data
        # TODO: need to check this is correct 
#         self.onPlotCalibrationCurve(xvals1=df['tDd'], yvals1=df['CCSd'], label1='Linear',
#                                     xvalsLinear=xvalsLinear, yvalsLinear=yvalsLinear,
#                                     xvals2=df['tDdd'], yvals2=df['CCS'], label2='Power',
#                                     xvalsPower=xvalsPower, yvalsPower=yvalsPower,
#                                     color='red', marker='o')
 
        # Append to list
        self.documentsDict[self.docs.title] = self.docs
        # Update documents tree
        self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
         
        # Set current calibration parameters
        self.currentCalibrationParams = self.docs.calibrationParameters

        self.view.SetStatusText(''.join([u'R² (linear): ', str(np.round(r2Linear,4)), 
                                         u' | R² (power): ', str(np.round(r2Power,4)),]), 3)
   
    def OnApplyCCSCalibrationToSelectedIons(self, evt):
        
        # Shortcut to the table
        tempList = self.view.panelCCS.bottomP.peaklist
        calibrationMode = self.view.panelCCS.bottomP.calibrationMode.GetStringSelection()
        for caliID in xrange(tempList.GetItemCount()):
            # Only add info if dataset was checked
            if tempList.IsChecked(index=caliID):
                # Get document info
                filename = tempList.GetItem(caliID,self.config.ccsBottomColNames['filename']).GetText()
                mzStart = tempList.GetItem(caliID,self.config.ccsBottomColNames['start']).GetText()
                mzEnd = tempList.GetItem(caliID,self.config.ccsBottomColNames['end']).GetText()
                charge = str2int(tempList.GetItem(caliID,self.config.ccsBottomColNames['charge']).GetText())
                mzCentre = str2num(tempList.GetItem(caliID,self.config.ccsBottomColNames['ion']).GetText())
                selectedType = tempList.GetItem(caliID,self.config.ccsBottomColNames['format']).GetText()
                rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
                
                # Check these fields were filled in
                if isempty(charge) or isempty(mzCentre): 
                    msg = 'Please fill in the fields'
                    self.view.SetStatusText(msg, 3)
                    return
                elif charge == 0:
                    msg = "%s (%s) is missing charge value. Please add charge information before trying to apply CCS calibration" % (rangeName, filename)
                    dialogs.dlgBox(exceptionTitle='Missing charge information', 
                                   exceptionMsg= msg,
                                   type="Warning")
                    continue
                # Get document object based on the filename
                document = self.documentsDict[filename]

                # Select data based on the format of the object
                if selectedType == '2D, extracted':
                    data = document.IMS2Dions[rangeName]
                elif selectedType == '2D, combined':
                    data = document.IMS2DCombIons[rangeName]
                elif selectedType == '2D, processed':   
                    data = document.IMS2DionsProcess[rangeName]
                    
                # Unpack data
                zvals, xvals, xlabel, yvals, ylabel, charge, mw, mzCentre = self.get2DdataFromDictionary(dictionary=data,
                                                                                                         dataType='calibration',
                                                                                                         compact=False)
                # Check that the object has pusher frequency
                pusherFreq = document.parameters.get('pusherFreq', 1)

                
                if (pusherFreq == 1 or not isnumber(pusherFreq)) and ylabel != 'Drift time (ms)':
                    msg = "%s (%s) ion is missing pusher frequency value. Please modify it in the Notes, Information and Labels panel" % (filename, rangeName)
                    dialogs.dlgBox(exceptionTitle='Missing data', 
                                   exceptionMsg= msg,
                                   type="Error")
                    continue
                # Check if ylabel is in ms
                if ylabel != 'Drift time (ms)':
                    if ylabel == 'Drift time (bins)':
                        yvals = yvals*(pusherFreq/1000)
                    else:
                        # Need to restore scans and convert them to ms
                        yvals = 1+np.arange(len(zvals[:,1]))
                        yvals = yvals*(pusherFreq/1000)
                
                # Check for TOF correction factor
                if isempty(document.corrC) and document.parameters.get('corrC', None) == None: 
                    msg = 'Missing TOF correction factor'
                    self.view.SetStatusText(msg, 3)
                    return
                
                # Check for charge and m/z information
                if not isnumber(charge) or not isnumber(mzCentre):
                    if not isnumber(charge):
                        msg = 'Missing charge information'
                    elif not isnumber(mzCentre):
                        msg = 'Missing m/z information'
                    self.view.SetStatusText(msg, 3)
                    return
                
                # Create empty DataFrame to calculate CCS
                df = pd.DataFrame(columns=['m/z','z','tD','MW','RedMass','tDd','tDdd'],
                                  index=np.arange(0,len(yvals)))
                df['m/z'] = float(mzCentre)
                df['z'] = int(charge)
                df['tD'] = yvals
                
                # Unpack calibration parameters
                if len(self.currentCalibrationParams) == 0:
                    if document.gotCalibrationParameters:
                        self.currentCalibrationParams = document.calibrationParameters
                
                # Now assign the calibration parameters
                try:
                    calibrationParameters = self.currentCalibrationParams.get('parameters', None)
                except (IndexError, KeyError): 
                    calibrationParameters = None
                    
                if calibrationParameters == None:
                    # TODO: add function to search for calibration document 
                    docList = self.checkIfAnyDocumentsAreOfType(type='Type: CALIBRANT', 
                                                                format = 'Format: DataFrame')
                    if len(docList) == 0:
                        msg = "Cound not find calibration document or calibration file. Please create or load one in first"
                        dialogs.dlgBox(exceptionTitle='Missing data', 
                                       exceptionMsg= msg,
                                       type="Error")
                        return
                    else:
                        self.selectDocDlg = panelSelectDocument(self.view, self, docList, allowNewDoc=False)
                        if self.selectDocDlg.ShowModal() == wx.ID_OK: 
                            calibrationParameters = self.currentCalibrationParams.get('parameters', None)
                            if calibrationParameters == None: return           
                        return
                    
                # Get parameters
                slopeLinear, interceptLinear, r2Linear = calibrationParameters['linear']
                slopePower, interceptPower, r2Power = calibrationParameters['power']
                slope, intercept = calibrationParameters['powerParms']
                gas = calibrationParameters['gas']
 
                # Fill in remaining details
                df['MW'] = (df['m/z']-(self.config.elementalMass['Hydrogen']*df['z']))*df['z']
                df['RedMass'] = ((df['MW']*gas)/(df['MW']+gas))
                df['tDd'] = (df['tD']-((document.corrC*df['m/z'].apply(sqrt))/1000))
                
                # Linear law
                df['CCSd'] = slopeLinear*df['tDd']+interceptLinear
                df['CCSlinear'] = df['CCSd'] * (df['z']*(1/df['RedMass']).apply(sqrt))
                # Power law
                df['tDdd'] = df['tDd'].pow(slope)*df['z']*df['RedMass'].apply(sqrt)
                df['CCSpower'] = (df['tDdd']*slopePower)+interceptPower
            

                # Update dictionary
                document.gotCalibrationParameters = True
                document.calibrationParameters = self.currentCalibrationParams
                document.calibrationParameters['mode'] = calibrationMode
                
                document.gas = gas
                
                if calibrationMode == 'Linear':
                    ccsVals = pd.to_numeric(df['CCSlinear']).values
                elif calibrationMode == 'Power':
                    ccsVals = pd.to_numeric(df['CCSpower']).values
                                
                # Assign data
                if selectedType == '2D, extracted':
                    document.IMS2Dions[rangeName]['yvals'] = ccsVals
                    document.IMS2Dions[rangeName]['yvalsCCSBackup'] = ccsVals
                    document.IMS2Dions[rangeName]['ylabels'] = u'Collision Cross Section (Å²)'
                elif selectedType == '2D, combined':
                    document.IMS2DCombIons[rangeName]['yvals'] = ccsVals
                    document.IMS2DCombIons[rangeName]['yvalsCCSBackup'] = ccsVals
                    document.IMS2DCombIons[rangeName]['ylabels'] = u'Collision Cross Section (Å²)'
                elif selectedType == '2D, processed':   
                    document.IMS2DionsProcess[rangeName]['yvals'] = ccsVals
                    document.IMS2DionsProcess[rangeName]['yvalsCCSBackup'] = ccsVals
                    document.IMS2DionsProcess[rangeName]['ylabels'] = u'Collision Cross Section (Å²)'
                
                # Assign updated to dictionary
                self.documentsDict[document.title] = document

                # Update documents tree
                self.view.panelDocuments.topP.documents.addDocument(docData = document)
                
        # Update status bar
        try:
            self.view.SetStatusText(''.join([u'R² (linear): ', str(np.round(r2Linear,4)), 
                                             u' | R² (power): ', str(np.round(r2Power,4)),
                                             u' | Used: ',calibrationMode, ' mode']), 3)
        except: pass
    
    def OnAddDataToCCSTable(self, filename=None, mzStart=None, mzEnd=None,
                            mzCentre=None, charge=None, protein=None, 
                            format=None, evt=None):
        """
        Add data to table and prepare DataFrame for CCS calibration
        """
        # Shortcut to the table
        tempList = self.view.panelCCS.bottomP.peaklist
        
        # Add data to table
        tempList.Append([filename, mzStart, mzEnd,
                         mzCentre, protein, charge, format])
        
        # Remove duplicates
        self.view.panelCCS.bottomP.onRemoveDuplicates(evt=None)
        # Enable and show CCS table
        self.view.ccsTable.Check(True)
        self.view._mgr.GetPane(self.view.panelCCS).Show()
        self.view._mgr.Update()     
           
    def saveCCScalibrationToPickle(self, evt):
        """
        Save CCS calibration parameters to file
        """
        try:
            self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        except: return
        if self.currentDoc == "Current documents": return
        
        # Check if the currently selected document is Calibration dataframe file
        if (self.documentsDict[self.currentDoc].dataType == 'Type: CALIBRANT' and 
            self.documentsDict[self.currentDoc].fileFormat == 'Format: DataFrame'):
            self.docs = self.documentsDict[self.currentDoc]
            self.view.SetStatusText('Using document: ' + self.docs.title.encode('ascii', 'replace'), 3)
        else:
            docList = self.checkIfAnyDocumentsAreOfType(type='Type: CALIBRANT', 
                                                        format = 'Format: DataFrame')
            if len(docList) == 0:
                print('Did not find appropriate document.')
                return
            else:
                self.DocDlg = panelSelectDocument(self.view, self, docList, allowNewDoc=False)
                if self.selectDocDlg.ShowModal() == wx.ID_OK: 
                    pass
                
                # Check that document exists
                if self.currentDoc == None: 
                    self.view.SetStatusText('Please select CCS calibration document', 3)
                    return
                
                self.docs = self.documentsDict[self.currentDoc]
                self.view.SetStatusText('Using document: ' + self.docs.title.encode('ascii', 'replace'), 3)
            
        # Get calibration parameters
        # Unpack calibration parameters
        if len(self.currentCalibrationParams) == 0:
            if self.docs.gotCalibrationParameters:
                self.currentCalibrationParams = self.docs.calibrationParameters
        
        # Save parameters    
        fileType = "ORIGAMI Document File|*.pickle"
        dlg =  wx.FileDialog(self.view, "Save CCS calibration to file...", "", "", fileType,
                                wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        defaultFilename = self.docs.title.split(".")
        defaultFilename = "".join([defaultFilename[0],'_CCScaliParams'])
        dlg.SetFilename(defaultFilename)
        
        if dlg.ShowModal() == wx.ID_OK:
            saveFileName = dlg.GetPath()          
            # Save
            saveObject(filename=saveFileName, saveFile=self.currentCalibrationParams)
        else: return

    def rescaleValue(self, oldList, newList, old_value):
        """ 
        Simple rescaling function to convert values from a list of certain range to 
        a new range. For instance to convert large numbers to a 0-255 range of colormap
        """
        
        old_min = np.min(oldList)
        old_max = np.max(oldList)
        new_min = 0
        new_max = len(newList) -1
        new_value = ((old_value - old_min)/(old_max - old_min))*(new_max - new_min)+new_min
        return new_value
   
    def onIRTextFile(self, evt):
        dlg = wx.FileDialog(self.view, "Choose a text file:", wildcard = "*.txt; *.csv" ,
                           style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            print "You chose %s" % dlg.GetPath()   
            imsData2D, xAxisLabels, yAxisLabels = None, None, None
            imsData2D, xAxisLabels, yAxisLabels = ml.textOpenIRData(fileNameLocation=dlg.GetPath(), 
                                                                    norm=False)
            dataSplit, xAxisLabels, yAxisLabels, dataRT, data1DT  = af.combineIRdata(inputData=imsData2D, 
                                                                                     threshold=2000, noiseLevel=500)
            
            
             # Add data to document 
            temp, idName = os.path.split(dlg.GetPath())
            idName = (''.join([idName])).encode('ascii', 'replace')  
            self.docs = doc()  
            self.docs.title = idName
            self.currentDoc = idName # Currently plotted document
            self.docs.path = os.path.dirname(dlg.GetPath())
            self.docs.userParameters = self.config.userParameters
            self.docs.userParameters['date'] = getTime()
            self.docs.dataType = 'Type: IR IM-MS'
            self.docs.fileFormat = 'Format: Text (.csv/.txt)'
            
            self.docs.got1RT = True
            self.docs.RT = {'xvals':yAxisLabels,  # bins
                            'yvals':dataRT,
                            'xlabels':u'Wavenumber (cm⁻¹)'}
            self.docs.got1DT = True
            self.docs.DT = {'xvals':xAxisLabels, 
                            'yvals':data1DT,
                            'xlabels':'Drift time (bins)',
                            'ylabels':'Intensity'}
            
            self.docs.got2DIMS = True
            self.docs.IMS2D = {'zvals':dataSplit,
                               'xvals':xAxisLabels,
                               'xlabels':u'Wavenumber (cm⁻¹)',
                               'yvals':yAxisLabels,
                               'ylabels':'Drift time (bins)',
                               'cmap':self.docs.colormap}
            # Append to list
            self.documentsDict[idName] = self.docs
            
            # Plots
            self.onPlot1DIMS2(yAxisLabels, data1DT, 'Drift time (bins)', self.docs.lineColour, self.docs.style)
            self.onPlotRT2(xAxisLabels, dataRT, u'Wavenumber (cm⁻¹)', self.docs.lineColour, self.docs.style)
            self.plot2Ddata2(data=[dataSplit, xAxisLabels,u'Wavenumber (cm⁻¹)',yAxisLabels,'Drift time (bins)',
                                   self.docs.colormap])
            
            # Update documents tree
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
    
    def onUserDefinedListImport(self, evt):
        """ Load a csv file with CV/SPV values for the List/User-defined method"""
        dlg = wx.FileDialog(self.view, "Choose a text file:", wildcard = "*.csv" ,
                           style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            print "You chose %s" % dlg.GetPath()   

            origamiList = np.genfromtxt(dlg.GetPath(), 
                                        delimiter=',', 
                                        skip_header=True)
            self.config.origamiList = origamiList
            
        dlg.Destroy()
            
    def onImportCCSDatabase(self, evt, onStart=False):
        
        if not onStart:
            dlg = wx.FileDialog(self.view, "Choose a CCS database file:", wildcard = "*.csv" ,
                               style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
            if dlg.ShowModal() == wx.ID_OK:
                print "You chose %s" % dlg.GetPath()  
                
                # Open database
                self.config.ccsDB= ml.importCCSDatabase(filename=dlg.GetPath())
        else:
            self.config.ccsDB = ml.importCCSDatabase(filename='calibrantDB.csv')
            print('Loaded CCS database')
       
    def on2DTextFile(self, e):
        self.view.textView = False
        self.view.mainToolbar.ToggleTool(id=ID_OnOff_textView, toggle=True)
        self.view._mgr.GetPane(self.view.panelMultipleText).Show()
        self.view._mgr.Update()
        tempList = self.view.panelMultipleText.topP.filelist
        
        # TODO popup to modify x- and y- labels
        dlg = wx.FileDialog(self.view, "Choose a text file:", wildcard = "*.txt; *.csv" ,
                           style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            print "You chose %s" % dlg.GetPath()   
            imsData2D, xAxisLabels, yAxisLabels = None, None, None
            imsData2D, xAxisLabels, yAxisLabels = ml.textOpen2DIMSdata(fileNameLocation=dlg.GetPath(), 
                                                                                         norm=False)

            # Update limits
            self.setXYlimitsRMSD2D(xAxisLabels, yAxisLabels)
            # Add data to document 
            temp, idName = os.path.split(dlg.GetPath())
            idName = (''.join([idName])).encode('ascii', 'replace')  
            self.docs = doc()  
            self.docs.title = idName
            self.currentDoc = idName # Currently plotted document
            self.docs.path = os.path.dirname(dlg.GetPath())
            self.docs.userParameters = self.config.userParameters
            self.docs.userParameters['date'] = getTime()
            self.docs.dataType = 'Type: 2D IM-MS'
            self.docs.fileFormat = 'Format: Text (.csv/.txt)'
            self.docs.got2DIMS = True
            self.docs.IMS2D = {'zvals':imsData2D,
                                'xvals':xAxisLabels,
                                'xlabels':'Collision Voltage (V)',
                                'yvals':yAxisLabels,
                                'ylabels':'Drift time (bins)',
                                'cmap':self.docs.colormap}
            # Append to list
            self.documentsDict[idName] = self.docs
            
            # Update statusbar      
            self.view.SetStatusText(dlg.GetPath(), number = 4)
            # Add to table
            tempList.Append([idName, 
                             xAxisLabels[0], 
                             xAxisLabels[-1],
                             "", "", "", 
                             imsData2D.shape])
            
            # Plots
            self.plot2Ddata2(data=[imsData2D, xAxisLabels,
                                   'Collision Voltage (V)',yAxisLabels,
                                   'Drift time (bins)',
                                   self.docs.colormap])
            
            # Update documents tree
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
        dlg.Destroy()

    def on2DMultipleTextFiles(self, evt):
        
#         if evt.GetId() == ID_openTextFilesMenu:
#             self.view.textTable.Check(True)
#             self.view._mgr.GetPane(self.view.panelMultipleText).Show()
# #             self.view.ToggleView(None)
#         else:
#             self.view.textTable.Check(True)
# #             self.view.ToggleView(None)
        
        # Setup panel settings
        self.view.textTable.Check(True)
        self.view.textView = False
        self.view.mainToolbar.ToggleTool(id=ID_OnOff_textView, toggle=True)
        self.view._mgr.GetPane(self.view.panelMultipleText).Show()
        self.view._mgr.Update()
        tempList = self.view.panelMultipleText.topP.filelist
        
        
        wildcard = "Text files with axis labels (*.txt, *.csv)| *.txt;*.csv"
        dlg = wx.FileDialog(self.view, "Choose a text file. Make sure files contain x- and y-axis labels!",
                            wildcard = wildcard ,style=wx.FD_MULTIPLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            pathlist = dlg.GetPaths()
            filenames = dlg.GetFilenames()
            for (file, filename) in zip(pathlist,filenames):
                outcome = self.view.panelMultipleText.topP.onCheckDuplicates(fileName=filename)
                if outcome: continue
#                 self.view.SetStatusText(''.join(["Opened: ", file]), 3)
                # Load data for each file
                imsData2D, xAxisLabels, yAxisLabels = ml.textOpen2DIMSdata(fileNameLocation=file, 
                                                                           norm=False)
                # Try to extract labels from the text file
                if isempty(xAxisLabels) or isempty(yAxisLabels):
                    xAxisLabels = ""
                    yAxisLabels = ""
                    # Format: filename, x-min, x-max, color, alpha, label, shape
                    tempList.Append([filename,  xAxisLabels, 
                                     xAxisLabels, "", "", "", imsData2D.shape])
                    msg1 = ''.join(["Missing x- and y-axis labels for ", filename, "!"])
                    msg2 = "Consider adding x- and y-axis labels to your file to obtain full functionality."
                    msg = '\n'.join([msg1,msg2])
                    dialogs.dlgBox(exceptionTitle='Missing data', 
                                   exceptionMsg= msg,
                                   type="Warning")
                else:
                    # Add data to the table
                    tempList.Append([filename, 
                                     xAxisLabels[0], 
                                     xAxisLabels[-1],
                                     "", "", "", imsData2D.shape])
                    
                # Set XY limits
                self.setXYlimitsRMSD2D(xAxisLabels, yAxisLabels)
                # Split filename to get path
                temp, idName = os.path.split(file)
                # Add data to document
                self.docs = doc() 
                self.docs.title = filename
                self.currentDoc = idName # Currently plotted document
                self.docs.path = temp
                self.docs.userParameters = self.config.userParameters
                self.docs.userParameters['date'] = getTime()
                self.docs.dataType = 'Type: 2D IM-MS'
                self.docs.fileFormat = 'Format: Text (.csv/.txt)'
                self.docs.got2DIMS = True
                self.docs.IMS2D = {'zvals':imsData2D,
                                    'xvals':xAxisLabels,
                                    'xlabels':'Collision Voltage (V)',
                                    'yvals':yAxisLabels,
                                    'ylabels':'Drift time (bins)',
                                    'cmap':self.docs.colormap}
                
                # Append to list
                self.documentsDict[filename] = self.docs
                
                # Update documents tree
                self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
        dlg.Destroy()
                         
    def onProcessMultipleTextFiles(self, evt):
        # TODO: currently, if we threshold and then threshold again the array is not reset...
        
        if evt.GetId() == ID_processAllTextFiles:
            self.view.panelMultipleText.topP.OnCheckAllItems(evt=None, override=True)
        
        tempList = self.view.panelMultipleText.topP.filelist        
        for textID in xrange(tempList.GetItemCount()):
            # By default, if items are not checked, they will not be processed
            itemChecked = tempList.IsChecked(index=textID)
            if itemChecked == True:
                filename = tempList.GetItem(textID,0).GetText()
                self.docs = self.documentsDict[filename]
                zvals = None
                imsData2D = None
                imsData2D = self.process2Ddata(zvals=self.docs.IMS2D['zvals'].copy())
                self.docs.got2Dprocess = True
                self.docs.IMS2Dprocess = {'zvals':imsData2D,
                                          'xvals':self.docs.IMS2D['xvals'],
                                          'xlabels':self.docs.IMS2D['xlabels'],
                                          'yvals':self.docs.IMS2D['yvals'],
                                          'ylabels':self.docs.IMS2D['ylabels'],
                                          'cmap':self.docs.colormap}
                self.documentsDict[filename] = self.docs
                self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)
            else: pass
            
        if evt.GetId() == ID_processAllTextFiles:
            self.view.panelMultipleText.topP.OnCheckAllItems(evt=None, check=False, override=True)
              
    def onPopulateXaxisTextLabels(self, startVal=None, endVal=None, shapeVal=None):
        """ 
        This function will check whether specified file has x-axis labels
        present in the dictionary. If not, it will check if x-axis values are
        present in the table. If true, it will generate x-axis labels based
        on the 'Start X', 'End X' and size of the array (shape)
        """
        labels = np.linspace(startVal, endVal, shapeVal)
        return labels
      
    def checkIfAnyDocumentsAreOfType(self, type=None, format=None):
        """
        This helper function checkes whether any of the documents in the 
        document tree/ dictionary are of specified type
        """
        listOfDocs = []
        for key in self.documentsDict:
            if self.documentsDict[key].dataType == type and format==None:
                listOfDocs.append(key)
            elif (self.documentsDict[key].dataType == type and 
                  self.documentsDict[key].fileFormat == format):
                listOfDocs.append(key)
            else:
                continue
        return listOfDocs
              
#===============================================================================
#  LINEAR DT
#===============================================================================

    def onLinearDTirectory(self, e=None):
        self.config.ciuMode = 'LinearDT'
        self.config.extractMode = 'singleIon'

        # Reset arrays
        imsData2D = np.array([])
        dlg = wx.DirDialog(self.view, "Choose a MassLynx file:",
                           style=wx.DD_DEFAULT_STYLE)
        if self.config.dirname == '':
            pass
        else:
            dlg.SetPath(self.config.dirname)
        if dlg.ShowModal() == wx.ID_OK:
            tstart = time.clock()
            print "You chose %s" % dlg.GetPath()   
            # Update statusbar      
            self.view.SetStatusText(dlg.GetPath(), number = 4)
            # Get experimental parameters
            parameters = self.config.importMassLynxInfFile(path=dlg.GetPath())
            
            # Mass spectra
            ml.rawExtractMSdata(fileNameLocation=dlg.GetPath(), 
                                driftscopeLocation=self.config.driftscopePath)
            msDataX, msDataY = ml.rawOpenMSdata(path=dlg.GetPath())
            xlimits = [parameters['startMS'], parameters['endMS']]
            
            # RT
            ml.rawExtractRTdata(fileNameLocation=dlg.GetPath(), 
                                driftscopeLocation=self.config.driftscopePath)
            rtDataY,rtDataYnorm = ml.rawOpenRTdata(path=dlg.GetPath(), 
                                                   norm=True)   
            xvalsRT = np.arange(1,len(rtDataY)+1)
            
            # 2D
            ml.rawExtract2DIMSdata(fileNameLocation=dlg.GetPath(),
                                   driftscopeLocation=self.config.driftscopePath)
            imsData2D = ml.rawOpen2DIMSdata(path=dlg.GetPath(), norm=False)
            xlabels = 1+np.arange(len(imsData2D[1,:]))
            ylabels = 1+np.arange(len(imsData2D[:,1]))
            
            # Update status bar with MS range
            txt = ''.join(["MS range: ", num2str(parameters['startMS']), "-", 
                           num2str(parameters['endMS'])])
            self.view.SetStatusText(txt, 1)
            txt = ''.join(['MSMS: ', num2str(parameters['setMS'])])
            self.view.SetStatusText(txt, 2)
            
            tend= time.clock()
            self.view.SetStatusText('Total time to open file: %.2gs' % (tend-tstart), 3)
                 
            # Add info to document 
            temp, idName = os.path.split(dlg.GetPath())
            idName = (''.join([idName])).encode('ascii', 'replace')   
            self.docs = doc()             
            self.docs.title = idName
            self.currentDoc = idName # Currently plotted document
            self.docs.userParameters = self.config.userParameters
            self.docs.userParameters['date'] = getTime()
            self.docs.path = dlg.GetPath()
            self.docs.parameters = parameters
            self.docs.dataType = 'Type: Multifield Linear DT'
            self.docs.fileFormat = 'Format: MassLynx (.raw)'
            # Add data
            self.docs.gotMS = True
            self.docs.massSpectrum = {'xvals':msDataX,
                                      'yvals':msDataY,
                                      'xlabels':'m/z (Da)',
                                      'xlimits':xlimits}
            self.docs.got1RT = True
            self.docs.RT = {'xvals':xvalsRT, 
                            'yvals':rtDataYnorm,
                            'xlabels':'Scans'}            
            self.docs.got2DIMS = True
            # Format: zvals, xvals, xlabel, yvals, ylabel
            self.docs.IMS2D = {'zvals':imsData2D,
                                'xvals':xlabels,
                                'xlabels':'Scans',
                                'yvals':ylabels,
                                'ylabels':'Drift time (bins)',
                                'cmap':self.docs.colormap}
            
            # Append to list
#             self.documents.append(document)
            self.documentsDict[idName] = self.docs
            
            # Plots
            self.onPlotRT2(xvalsRT, rtDataYnorm, 'Scans', self.docs.lineColour, self.docs.style)
            self.onPlotMS2(msDataX, msDataY, self.docs.lineColour, self.docs.style, 
                           xlimits=xlimits)
            
            # Update documents tree
            self.view.panelDocuments.topP.documents.addDocument(docData = self.docs)   
        dlg.Destroy()
        return None
      
    def onExtractDToverMZrangeMultiple(self, e):
        # TODO:
        """
        Currently this function is not working well. IT doesn't store data in the correct format
        i.e. it only saves ONE RT per charge state which is useless 
        Need to do:
        - add to document object to have a sub-tree with each RT for each MZ
        - should be a dictionary with m/z, rts, charge
        """
        # Combine 1DT to array
        initialDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        
        rtList = self.view.panelLinearDT.topP.peaklist # List with MassLynx file information 
        mzList = self.view.panelLinearDT.bottomP.peaklist # List with m/z information
        
        if rtList.GetItemCount() == 0 or mzList.GetItemCount() == 0:
            self.view.SetStatusText('Please make sure you selected regions to extract', 3)
            return 
        for mz in xrange(mzList.GetItemCount()):
            mzStart= str2num(mzList.GetItem(mz,0).GetText())
            mzEnd = str2num(mzList.GetItem(mz,1).GetText())
            charge = str2num(mzList.GetItem(mz,3).GetText())
            # Get document for the ion
#             self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
            self.currentDoc = mzList.GetItem(mz,4).GetText()
            document = self.documentsDict[self.currentDoc]
            path = document.path
            scantime = document.parameters['scanTime']
            xvals = document.IMS2D['yvals']
            xlabel = document.IMS2D['ylabels'] 
            # Get height of the peak
            ms = document.massSpectrum
            ms = np.flipud(np.rot90(np.array([ms['xvals'], ms['yvals']])))
            mzYMax = self.view.getYvalue(msList=ms, mzStart=mzStart, mzEnd=mzEnd)
            mzList.SetStringItem(index=mz, col=2, label=str(mzYMax))
            tempArray = []
            driftList = []
            retTimeList = []
            for rt in xrange(rtList.GetItemCount()):
                # RT has to be in minutes to extract using Driftscope
                rtStart= str2num(rtList.GetItem(rt,0).GetText())
                rtEnd = str2num(rtList.GetItem(rt,1).GetText())
                retTimeList.append([int(rtStart), int(rtEnd)]) # create list of RTs to be saved with the document
                rtStart= round(rtStart*(scantime/60),2)
                rtEnd = round(rtEnd*(scantime/60),2)
                filename = rtList.GetItem(rt,4).GetText()
                driftVoltage = str2num(rtList.GetItem(rt,3).GetText())
                if driftVoltage == None: driftVoltage=0
                if filename != document.title: continue
                self.view.SetStatusText(''.join(['RT(s): ',str(rtStart),'-',str(rtEnd),', MS: ',str(mzStart),'-',str(mzEnd)]), 3)
                ml.rawExtract1DIMSdataOverRT(fileNameLocation=path, driftscopeLocation=self.config.driftscopePath,
                                             mzStart=mzStart, mzEnd=mzEnd, rtStart=rtStart, rtEnd=rtEnd)
                # Load output
                imsData1D =  ml.rawOpen1DRTdata(path=path, norm=self.config.normalize)
                # Append to output
                tempArray.append(imsData1D)
                driftList.append(driftVoltage)
                
            # Add data to document object  
            ims1Darray = np.array(tempArray) # combine
            imsData1D = np.sum(ims1Darray, axis=0)
            document.gotExtractedDriftTimes = True
            rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
            document.IMS1DdriftTimes[rangeName] = {'xvals':xvals,
                                                   'yvals':ims1Darray,
                                                   'yvalsSum':imsData1D,
                                                   'xlabels':xlabel,
                                                   'charge':charge,
                                                   'driftVoltage':driftList,
                                                   'retTimes':retTimeList,
                                                   'xylimits':[mzStart,mzEnd,mzYMax]}
            self.documentsDict[self.currentDoc] = document
            self.view.panelDocuments.topP.documents.addDocument(docData = document)
        document = self.documentsDict[initialDoc]
        self.view.panelDocuments.topP.documents.addDocument(docData = document)

    def get2DdataFromDictionary(self, dictionary=None, dataType='plot', 
                                compact=False, plotType='2D'):
        """ 
        This is a helper function to extract relevant data from dictionary
        Params:
        dictionary: dictionary with 2D data to be examined
        dataType: what data you want to get back
                - plot: only return the minimum required parameters
                - process: plotting + charge state
        """
        if dictionary is None: return
        if plotType == '2D':
            # These are always there
            zvals = dictionary['zvals'].copy()
            xvals = dictionary['xvals']
            xlabels = dictionary['xlabels']
            yvals = dictionary['yvals']
            ylabels = dictionary['ylabels']
            cmap = dictionary['cmap']
            charge = dictionary.get('charge', None)
            mw = dictionary.get('mw', None)
            mzCentre = dictionary.get('xcentre', None)
            
            if cmap == '' or cmap is None: cmap = 'viridis'
            
            if dataType == 'all':
                if compact:
                    data = zvals, xvals, xlabels, yvals, ylabels, cmap, charge
                    return data
                else:
                    return zvals, xvals, xlabels, yvals, ylabels, cmap, charge
            elif dataType == 'plot':
                if compact:
                    data = zvals, xvals, xlabels, yvals, ylabels, cmap
                    return data
                else:
                    return zvals, xvals, xlabels, yvals, ylabels, cmap
            elif dataType == 'calibration':
                return zvals, xvals, xlabels, yvals, ylabels, charge, mw, mzCentre
        if plotType == '1D':
            xvals = dictionary['xvals']
            xlabels = dictionary['xlabels']
            yvals = dictionary['yvals']
            try: 
                cmap = dictionary['cmap']
            except KeyError: cmap= [0,0,0]
            
            try: xlimits = dictionary['xlimits']
            except KeyError: 
                xlimits=None    
            if dataType == 'plot':
                if compact:
                    data = xvals, yvals, xlabels, cmap            
                    return data
                else: return xvals, yvals, xlabels, cmap
        elif plotType == 'Overlay':   
            zvals1 = dictionary['zvals1'] 
            zvals2 = dictionary['zvals2']
            cmapIon1 = dictionary['cmap1'] 
            cmapIon2 =dictionary['cmap2'] 
            alphaIon1 = dictionary['alpha1'] 
            alphaIon2 = dictionary['alpha2'] 
            xvals = dictionary['xvals']  
            xlabel = dictionary['xlabels'] 
            yvals = dictionary['yvals'] 
            ylabel = dictionary['ylabels']
            file1 = dictionary['file1']
            file2 = dictionary['file2']
            label1 = dictionary['label1']
            label2 = dictionary['label2']
            try: 
                charge1 = dictionary['charge1']
                charge2 = dictionary['charge2']
            except KeyError: 
                charge1=None
                charge2=None
            if dataType == 'plot':
                if compact:
                    return
                else:
                    return (zvals1, zvals2, cmapIon1, cmapIon2, alphaIon1, alphaIon2, xvals,
                            xlabel, yvals, ylabel, charge1, charge2)
        elif plotType == 'Matrix':
            zvals = dictionary['zvals']
            xylabels = dictionary['matrixLabels']
            cmap = dictionary['cmap']
            return zvals, xylabels, cmap
        elif plotType == 'RMSF':
            zvals = dictionary['zvals']
            yvalsRMSF = dictionary['yvalsRMSF']
            xvals = dictionary['xvals']
            yvals = dictionary['yvals']
            xlabelRMSD = dictionary['xlabelRMSD']
            ylabelRMSD = dictionary['ylabelRMSD']
            ylabelRMSF = dictionary['ylabelRMSF']
            color = dictionary['colorRMSF']
            cmap = dictionary['cmapRMSF']
            rmsdLabel = dictionary['rmsdLabel']
            return zvals, yvalsRMSF, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF, color, cmap, rmsdLabel
        elif plotType == 'RMSD':
            zvals = dictionary['zvals']
            xvals = dictionary['xvals']
            xlabels = dictionary['xlabel']
            yvals = dictionary['yvals']
            ylabels = dictionary['ylabel']
            rmsdLabel = dictionary['rmsdLabel']
            cmap = dictionary['cmap']
            return zvals, xvals, xlabels, yvals, ylabels, rmsdLabel, cmap
        elif plotType == 'Overlay1D':
            xvals = dictionary['xvals']
            yvals = dictionary['yvals']
            xlabels = dictionary['xlabel']
            colors = dictionary['colors']
            labels = dictionary['labels']
            xlimits = dictionary['xlimits']
            return xvals, yvals, xlabels, colors, labels, xlimits
             
    def getOverlayDataFromDictionary(self, dictionary=None, dataType='plot', compact=False):
        """ 
        This is a helper function to extract relevant data from dictionary
        Params:
        dictionary: dictionary with 2D data to be examined
        dataType: what data you want to get back
                - plot: only return the minimum required parameters
                - process: plotting + charge state
                - all: return you got
        """
        if dictionary is None: return
        # These are always there
        zvals1 = dictionary['zvals1']
        zvals2 = dictionary['zvals2']
        cmap1 = dictionary['cmap1']
        cmap2 = dictionary['cmap2']
        alpha1 = dictionary['alpha1']
        alpha2 = dictionary['alpha2']
        label1 = dictionary['label1']
        label2 = dictionary['label2']
        xvals = dictionary['xvals']
        xlabels = dictionary['xlabels']
        yvals = dictionary['yvals']
        ylabels = dictionary['ylabels']
        if dataType == 'plot':
            if compact:
                data = [zvals1, zvals2, cmap1, cmap2, alpha1, alpha2, xvals, yvals,
                        xlabels, ylabels]
                return data
            else:
                return zvals1, zvals2, cmap1, cmap2, alpha1, alpha2, xvals, yvals, xlabels, ylabels
    
    def process2Ddata(self, zvals=None, e=None):
        """
        Process data - smooth, threshold and normalize 2D data
        """

        if isempty(zvals) or zvals is None:
            self.view.SetStatusText('Sorry, missing data - cannot perform action', 3)
            return

        # Smooth data
        if self.config.smoothMode == "None" or self.config.smoothMode == False: pass
        elif self.config.smoothMode == "Gaussian":
            sigma=str2num(self.config.gaussSigma.encode('ascii', 'replace'))
            zvals = af.smoothDataGaussian(inputData=zvals, sigma=sigma)
        elif self.config.smoothMode == "Savitzky-Golay":
            savgolPoly = str2int(self.config.savGolPolyOrder.encode('ascii', 'replace'))
            savgolWindow = str2int(self.config.savGolWindowSize.encode('ascii', 'replace'))
            zvals = af.smoothDataSavGol(inputData = zvals,
                                        polyOrder = savgolPoly, 
                                        windowSize = savgolWindow)
        else: pass
        # Threshold data
        threshold = str2num(self.config.threshold.encode('ascii', 'replace'))
        
        if isempty(threshold) or threshold == None or threshold == '': pass
        else:
           zvals = af.removeNoise(inputData=zvals, threshold=threshold)
           threshold = None
        
        # Normalize data - following previous actions!
        if self.config.normalize == True:
            zvals = af.normalizeIMS(inputData=zvals)
        return zvals
            
    def process2Ddata2(self, zvals=None, labelsX=None, e=None, mode='2D'):
        """
        Process 2D data - smooth, threshold and normalize 2D data
        """
        # Gather info about the file and document
        selectedItemParent, selectedItemParentText = None, None
        self.currentDoc, selectedItem, selectedText = self.view.panelDocuments.topP.documents.enableCurrentDocument(getSelected=True)
        indent = self.view.panelDocuments.topP.documents.getItemIndent(selectedItem)
        if indent > 2:
            selectedItemParent, selectedItemParentText = self.view.panelDocuments.topP.documents.getParentItem(selectedItem,2, 
                                                                                                               getSelected=True)
        else: pass
        self.docs = self.documentsDict[self.currentDoc]
        
        # Clear current data
        zvals = None
        # Based on the selection and indent, data is selected 
        if selectedText == '2D drift time' and indent == 2:
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(dictionary=self.docs.IMS2D,
                                                                                     dataType='plot',compact=False)
            
        elif selectedText == 'Processed 2D IM-MS' and indent == 2:
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(dictionary=self.docs.IMS2Dprocess,
                                                                                     dataType='plot',compact=False)

        elif selectedItemParentText == 'Extracted 2D IM-MS (multiple ions)' and indent == 3:
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(dictionary=self.docs.IMS2Dions[selectedText],
                                                                                     dataType='plot',compact=False)
            
        elif selectedItemParentText == 'Processed 2D IM-MS (multiple ions)' and indent == 3:
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(dictionary=self.docs.IMS2DionsProcess[selectedText],
                                                                                     dataType='plot',compact=False)
            
        elif selectedItemParentText == 'Combined CV 2D IM-MS (multiple ions)' and indent == 3:
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(dictionary=self.docs.IMS2DCombIons[selectedText],
                                                                                     dataType='plot',compact=False)
            
        elif selectedItemParentText == 'Input data' and indent == 3:
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(dictionary=self.docs.IMS2DcompData[selectedText],
                                                                                     dataType='plot',compact=False)
            
        elif selectedItemParentText == 'Statistical' and indent == 3:
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(dictionary=self.docs.IMS2DstatsData[selectedText],
                                                                                     dataType='plot',compact=False)
        elif selectedText == 'MS vs DT' and indent == 2:
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(dictionary=self.docs.DTMZ,
                                                                                     dataType='plot',compact=False)
        else:
            self.view.SetStatusText('Not implemented yet', 3)
        
        if (isempty(zvals) or isempty(xvals) or isempty(xlabel) or isempty(yvals) or isempty(ylabel)):
            self.view.SetStatusText('Sorry, missing data - cannot perform action', 3)
            try:
                self.checkWhatIsMissing2D(zvals, xvals, xlabel, yvals, ylabel, cmap)
            except UnboundLocalError: return
            return

        # Smooth data
        if self.config.smoothMode == "None" or self.config.smoothMode == False: pass
        elif self.config.smoothMode == "Gaussian":
            sigma=str2num(self.config.gaussSigma.encode('ascii', 'replace'))
            zvals = af.smoothDataGaussian(inputData=zvals, sigma=sigma)
        elif self.config.smoothMode == "Savitzky-Golay":
            savgolPoly = str2int(self.config.savGolPolyOrder.encode('ascii', 'replace'))
            savgolWindow = str2int(self.config.savGolWindowSize.encode('ascii', 'replace'))
            zvals = af.smoothDataSavGol(inputData = zvals,
                                        polyOrder = savgolPoly, 
                                        windowSize = savgolWindow)
        else: pass
        # Threshold data
        threshold = str2num(self.config.threshold.encode('ascii', 'replace'))
        
        if isempty(threshold) or threshold == None or threshold == '': pass
        else:
           zvals = af.removeNoise(inputData=zvals, threshold=threshold)
           threshold = None

        # Normalize data - following previous actions!
        if self.config.normalize == True:
            zvals = af.normalizeIMS(inputData=zvals, mode=self.config.normMode)
            
        # Check and change colormap if necessary
        cmapNorm = self.onCmapNormalization(zvals,
                                            min=self.config.minCmap, 
                                            mid=self.config.midCmap,
                                            max=self.config.maxCmap)
        
        # Plot data
        if mode == '2D':
            self.onPlot2DIMS2(zvals, xvals, yvals, xlabel, ylabel, cmap, cmapNorm=cmapNorm)
            if self.config.addWaterfall:
                self.onPlotWaterfall(yvals=zvals, xvals=yvals, xlabel=xlabel, cmap=cmap) # In this case its actually the bin/ccs!           
            self.onPlot3DIMS(zvals=zvals, labelsX=xvals, labelsY=yvals, 
                             xlabel=xlabel, ylabel=ylabel, zlabel='Intensity', cmap=cmap)
        elif mode == 'MSDT':
            self.onPlotMZDT(zvals,xvals,yvals,xlabel, ylabel, cmap, cmapNorm=cmapNorm)

# ---
    
    def checkWhatIsMissing2D(self, zvals, xvals, xlabel, yvals, ylabel, cmap):
        if isempty(zvals): self.view.SetStatusText("Missing 2D array", 3)
            
        if isempty(xvals): self.view.SetStatusText("Missing x-axis labels", 3)
            
        if isempty(xlabel): self.view.SetStatusText("Missing x-axis label", 3)
             
        if isempty(yvals): self.view.SetStatusText("Missing y-axis labels", 3)
            
        if isempty(ylabel): self.view.SetStatusText("Missing y-axis label", 3)
            
        if isempty(cmap): self.view.SetStatusText("Missing colormap", 3)
        
    def onChangePlotStyle(self, evt):
        """
        This function sets the default style of each plot
        """
        self.view.panelPlots.onChangePlotStyle(evt=None)
            
            
#===============================================================================
#  PLOT DATA
#===============================================================================

    def onOverlayRT(self, xvals, yvals, xlabel, colors, labels, xlimits, style=None, e=None):

        self.view.panelPlots.plotRT.clearPlot()
        self.view.panelPlots.plotRT.plotNewOverlay1D(xvals=xvals, 
                                                     yvals=yvals, 
                                                     title="", 
                                                     xlabel=xlabel,
                                                     ylabel="Intensity", 
                                                     labels=labels,
                                                     colors=colors, 
                                                     xlimits=xlimits,
                                                     lineWidth=self.config.lineWidth, 
                                                     zoom='box',
                                                     axesSize=self.config.plotSizes['RT'],
                                                     plotName='1D')
        self.view.panelPlots.plotRT.repaint()

    def onOverlayDT(self, xvals, yvals, xlabel, colors, labels, xlimits, style=None, e=None):

        self.view.panelPlots.plot1D.clearPlot()
        self.view.panelPlots.plot1D.plotNewOverlay1D(xvals=xvals, 
                                                     yvals=yvals, 
                                                     title="", 
                                                     xlabel=xlabel,
                                                     ylabel="Intensity", 
                                                     labels=labels,
                                                     colors=colors, 
                                                     xlimits=xlimits,
                                                     lineWidth=self.config.lineWidth, 
                                                     zoom='box',
                                                     axesSize=self.config.plotSizes['DT'],
                                                     plotName='1D')
        self.view.panelPlots.plot1D.repaint()

    def onPlotMS2(self, msX, msY, color, style, xlimits=None, e=None):
        self.view.panelPlots.plot1.clearPlot()
        self.view.panelPlots.plot1.plotData1D(xvals=msX, yvals=msY, 
                                             title="", xlabel="m/z",
                                             ylabel="Intensity", label="",
                                             xlimits=xlimits, color=color,
                                             lineWidth=self.config.lineWidth, 
                                             zoom='box', testMax='yvals',
                                             axesSize=self.config.plotSizes['MS'],
                                             plotName='1D')
        # Show the mass spectrum
        self.view.panelPlots.plot1.repaint()
           
    def onPlotRT2(self, rtX, rtY, xlabel, color, style, e=None):
        # TODO: should be able to pass args/kwargs to the function       
        
        self.view.panelPlots.plotRT.clearPlot()
        self.view.panelPlots.plotRT.plotData1D(xvals=rtX, yvals=rtY, 
                                              title="", xlabel=xlabel,
                                              ylabel="Intensity", label="",
                                              color=color, testMax='yvals',
                                              lineWidth=self.config.lineWidth, 
                                              zoom='box',
                                              axesSize=self.config.plotSizes['RT'],
                                              plotName='1D')
        # Show the mass spectrum
        self.view.panelPlots.plotRT.repaint()
    
    def onPlotRMSF(self, yvals, e=None):
        yvalsRT=yvals
        xvalsRT = np.arange(0,len(yvalsRT))
        self.view.panelPlots.plotRT.clearPlot()
        self.view.panelPlots.plotRT.plotData1D(xvals=xvalsRT, yvals=yvalsRT, 
                                                  title="", xlabel="Time (scans)",
                                                  ylabel="Intensity", label="",
                                                  color=self.config.lineColour, zoom='box')
        # Show the mass spectrum
        self.view.panelPlots.plotRT.repaint()
        
    def onPlotRMSDF(self, yvalsRMSF, zvals, xvals=None, yvals=None, xlabelRMSD=None,
                    ylabelRMSD=None, ylabelRMSF=None, color='blue',
                    cmap='inferno', plotType=None, e=None):
        """
        Plot RMSD and RMSF plots together in panel RMSD
        """
        self.view.panelPlots.plotRMSF.clearPlot()
        
        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap
            

        self.view.panelPlots.plotRMSF.plotNew1D_2plot(yvalsRMSF=yvalsRMSF, 
                                                      zvals=zvals, 
                                                      labelsX=xvals, 
                                                      labelsY=yvals,
                                                      xlabelRMSD=xlabelRMSD,
                                                      ylabelRMSD=ylabelRMSD,
                                                      ylabelRMSF=ylabelRMSF,
                                                      color=color, cmap=cmap,
                                                      interpolation=self.config.interpolation,
                                                      label="", zoom="box",
                                                      colorbar=self.config.colorbar,
                                                      plotName='RMSF')
        self.view.panelPlots.plotRMSF.repaint()
        self.rmsdfFlag = False
            
    def onPlot1DIMS2(self, dtX, dtY, xlabel, color, style, e=None):
        # Plot mass spectrum
        self.view.panelPlots.plot1D.clearPlot()            
        self.view.panelPlots.plot1D.plotData1D(xvals=dtX, yvals=dtY, 
                                                  title="", xlabel=xlabel,
                                                  ylabel="Intensity", label="",
                                                  color=color, testMax='yvals',
                                                  lineWidth=self.config.lineWidth, 
                                                  zoom='box',
                                                  axesSize=self.config.plotSizes['DT'],
                                                  plotName='1D')
        # Show the mass spectrum
        self.view.panelPlots.plot1D.repaint()

    def onPlotRMSDmatrix(self, zvals, xylabels, cmap, e=None):
        
        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap
        
        self.view.panelPlots.plotCompare.clearPlot()
        self.view.panelPlots.plotCompare.plotNew2DmatrixPlot(zvals=zvals, xylabels=xylabels, 
                                                             cmap=cmap, 
                                                             interpolation=self.config.interpolation, 
                                                             xNames=None, zoom="box", 
                                                             colorbar=self.config.colorbar,
                                                             axesSize=self.config.plotSizes['Comparison'],
                                                             plotName='2D')
        
        self.view.panelPlots.plot3D.plotNew3DBarplot(xvals=None, yvals=None, 
                                                     zvals=zvals,
                                                     cmap=self.config.currentCmap, 
                                                     title="", xlabel="",
                                                     ylabel="")
        # Show the mass spectrum
        self.view.panelPlots.plotCompare.repaint()

    def onPlot2DIMS2(self, zvals, xvals, yvals, xlabel, ylabel, 
                     cmap, cmapNorm=None, plotType=None, e=None):
        self.view.panelPlots.plot2D.clearPlot()
        
        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap
            
        # Check that cmap modifier is included
        if cmapNorm==None and plotType != "RMSD":
            cmapNorm = self.onCmapNormalization(zvals, 
                                                min=0, 
                                                mid=50, max=100)
            
        # Plot 2D dataset 
        if self.config.plotType == 'Image':
            self.view.panelPlots.plot2D.plotNew2Dplot2(zvals=zvals, labelsX=xvals,
                                                       xlabel=xlabel, labelsY=yvals,
                                                       interpolation=self.config.interpolation,
                                                       ylabel=ylabel, title="",
                                                       cmap=cmap, 
                                                       cmapNorm=cmapNorm,
                                                       colorbar=self.config.colorbar,
                                                       axesSize=self.config.plotSizes['2D'],
                                                       plotName='2D')
        elif self.config.plotType == 'Contour':
            self.view.panelPlots.plot2D.plotNew2DContourPlot2(zvals=zvals, labelsX=xvals,
                                                              xlabel=xlabel, labelsY=yvals,
                                                              interpolation=self.config.interpolation,
                                                              ylabel=ylabel, title="",
                                                              cmap=cmap, cmapNorm=cmapNorm,
                                                              pretty=self.config.prettyContour,
                                                              colorbar=self.config.colorbar,
                                                              axesSize=self.config.plotSizes['2D'],
                                                              plotName='2D')

        # Show the mass spectrum
        self.view.panelPlots.plot2D.repaint()   

    def onPlot3DIMS(self, zvals, labelsX=None, labelsY=None, 
                    xlabel="", ylabel="", zlabel="",cmap='inferno',e=None):
        self.view.panelPlots.plot3D.clearPlot()
        
        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap
            
        # Plot mass spectrum
        self.view.panelPlots.plot3D.plotNew3Dplot(xvals=labelsX, 
                                                  yvals=labelsY,
                                                  zvals=zvals,
                                                  cmap=cmap, 
                                                  title="", 
                                                  xlabel=xlabel,
                                                  ylabel=ylabel,
                                                  zlabel=zlabel)
        # Show the mass spectrum
        self.view.panelPlots.plot3D.repaint() 
        
#         # Mayavi
#         self.view.panelPlots.MV.surface(labelsX, labelsY, zvals, None)
        
    def onPlotOverlayMultipleIons2(self, zvalsIon1, zvalsIon2, cmapIon1, cmapIon2,
                                  alphaIon1, alphaIon2, xvals, yvals, xlabel, ylabel,
                                  flag=None, e=None):
        """
        Plot an overlay of *2* ions
        """

        self.view.panelPlots.plotOverlay.clearPlot()
        self.view.panelPlots.plotOverlay.plotNew2DoverlayPlot(zvalsIon1=zvalsIon1, 
                                                              zvalsIon2=zvalsIon2, 
                                                              cmapIon1=cmapIon1,
                                                              cmapIon2=cmapIon2,
                                                              alphaIon1=alphaIon1, 
                                                              alphaIon2=alphaIon2,
                                                              interpolation=self.config.interpolation,
                                                              labelsX=xvals, 
                                                              labelsY=yvals,
                                                              xlabel=xlabel,
                                                              ylabel=ylabel,
                                                              colorbar=self.config.colorbar,
                                                              axesSize=self.config.plotSizes['Overlay'],
                                                              plotName='2D')
                                                          
        self.view.panelPlots.plotOverlay.repaint()

    def getXYlimits2D(self, xvals, yvals):
        
        # Get min/max values
        xmin, xmax = xvals[0], xvals[-1]
        ymin, ymax = yvals[0], yvals[-1]
        self.config.xyLimits = [xmin, xmax, ymin, ymax]
        self.view.panelControls.onUpdateXYaxisLimits(evt=None)
        
    def setXYlimitsRMSD2D(self, xvals, yvals):
        # Get min/max values
        xmin, xmax = xvals[0], xvals[-1]
        ymin, ymax = yvals[0], yvals[-1]
        self.config.xyLimitsRMSD = [xmin, xmax, ymin, ymax]
        self.view.panelControls.onUpdateXYaxisLimitsRMSD(evt=None)

    def plot2Ddata2(self, data=None, **kwargs):
        """
        This function plots IMMS data in relevant windows.
        
        Input format: zvals, xvals, xlabel, yvals, ylabel
        """
        if isempty(data[0]):
                dialogs.dlgBox(exceptionTitle='Missing data', 
                               exceptionMsg= "Missing data. Cannot plot 2D plots.",
                               type="Error")
                return
        else: pass       
        
        # Unpack data
        zvals, xvals, xlabel, yvals, ylabel, cmap = data
        
        # Check and change colormap if necessary
        cmapNorm = self.onCmapNormalization(zvals,
                                            min=self.config.minCmap, 
                                            mid=self.config.midCmap,
                                            max=self.config.maxCmap)
        
        # Get XY limits
        self.getXYlimits2D(xvals, yvals)

        # Plot data 
        self.onPlot2DIMS2(zvals, xvals, yvals, xlabel, ylabel, cmap, cmapNorm=cmapNorm)
        if self.config.addWaterfall:
            self.onPlotWaterfall(yvals=zvals, xvals=yvals, xlabel=ylabel, cmap=cmap) # In this case its actually the bin/ccs!        
        self.onPlot3DIMS(zvals=zvals, labelsX=xvals, labelsY=yvals, 
                         xlabel=xlabel, ylabel=ylabel, zlabel='Intensity', cmap=cmap)
       
    def onPlotMZDT(self, zvals, xvals, yvals, xlabel, ylabel, 
                   cmap, cmapNorm=None, plotType=None, e=None):
        self.view.panelPlots.plotMZDT.clearPlot()
        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap
            
        # Check that cmap modifier is included
        if cmapNorm==None:
            cmapNorm = self.onCmapNormalization(zvals, min=0, 
                                                mid=50, max=100)
            
        # Plot 2D dataset 
        if self.config.plotType == 'Image':
            self.view.panelPlots.plotMZDT.plotMZDT(zvals=zvals, labelsX=xvals,
                                                   xlabel=xlabel, labelsY=yvals,
                                                   interpolation=self.config.interpolation,
                                                   ylabel=ylabel, title="",
                                                   cmap=cmap, 
                                                   cmapNorm=cmapNorm,
                                                   colorbar=self.config.colorbar,
                                                   axesSize=self.config.plotSizes['2D'],
                                                   plotName='MSDT')
            
        elif self.config.plotType == 'Contour':
            self.view.panelPlots.plotMZDT.plotNew2DContourPlot2(zvals=zvals, labelsX=xvals,
                                                              xlabel=xlabel, labelsY=yvals,
                                                              interpolation=self.config.interpolation,
                                                              ylabel=ylabel, title="",
                                                              cmap=cmap, cmapNorm=cmapNorm,
                                                              pretty=self.config.prettyContour,
                                                              colorbar=self.config.colorbar,
                                                              axesSize=self.config.plotSizes['2D'],
                                                              plotName='MSDT')

        # Show the mass spectrum
        self.view.panelPlots.plotMZDT.repaint()   
             
    def onPlotLinearDT(self, yvals, e=None):
        # Plot mass spectrum
        self.view.panelPlots.plot1D.clearPlot()
        xvals = np.arange(1,201) # temporary hack
        if isempty(yvals):
            yvals = self.dc.imsData1D
        else:
            yvals=yvals
            
        self.view.panelPlots.plot1D.plotNew1Dplot(xvals=xvals, yvals=yvals, 
                                                  title="", xlabel="Drift time (bins)",
                                                  ylabel="Intensity", label="",
                                                  color=self.config.lineColour,zoom='box',
                                                  plotName='1D')
        # Show the mass spectrum
        self.view.panelPlots.plot1D.repaint()  
 
    def onPlotMSDTCalibration(self, msX=None, msY=None, xlimits=None, dtX=None, 
                              dtY=None, color=None, xlabelDT='Drift time (bins)',
                              e=None, plotType='both'):
        # MS plot
        if plotType == 'both' or plotType == 'MS':
            self.view.panelPlots.topPlotMS.clearPlot()
            self.view.panelPlots.topPlotMS.plotData1D(xvals=msX, yvals=msY, 
                                                      title="", 
                                                      xlabel="m/z",
                                                      ylabel="Intensity", 
                                                      label="",
                                                      xlimits=xlimits, 
                                                      color=color, 
                                                      zoom='box',
                                                      lineWidth=self.config.lineWidth, 
                                                      axesSize=self.config.plotSizes['CalibrationMS'],
                                                      plotName='1D')
            # Show the mass spectrum
            self.view.panelPlots.topPlotMS.repaint()
        
        if plotType == 'both' or plotType == '1DT':
            ylabel="Intensity"
            # 1DT plot
            self.view.panelPlots.bottomPlot1DT.clearPlot()            
            self.view.panelPlots.bottomPlot1DT.plotData1D(xvals=dtX, yvals=dtY, 
                                                          title="", 
                                                          xlabel=xlabelDT,
                                                          ylabel=ylabel, 
                                                          label="",
                                                          color=color, 
                                                          zoom='box',
                                                          testMax='yvals',
                                                          lineWidth=self.config.lineWidth, 
                                                          axesSize=self.config.plotSizes['CalibrationDT'],
                                                          plotName='CalibrationDT')
            self.view.panelPlots.bottomPlot1DT.repaint()  
        
    def onPlot1DTCalibration(self, dtX=None, dtY=None, color=None,
                             xlabel='Drift time (bins)', e=None):
        
        # Check yaxis labels
        ylabel="Intensity"
        # 1DT plot
        self.view.panelPlots.bottomPlot1DT.clearPlot()            
        self.view.panelPlots.bottomPlot1DT.plotData1D(xvals=dtX, yvals=dtY, 
                                                      title="", xlabel=xlabel,
                                                      ylabel=ylabel, label="",
                                                      color=color, zoom='box',
                                                      fontsize=12, testMax='yvals',
                                                      axesSize=self.config.plotSizes['CalibrationDT'],
                                                      plotName='1D')
        self.view.panelPlots.bottomPlot1DT.repaint() 
        
    def onPlotCalibrationCurve(self, xvals1, yvals1, label1, xvalsLinear, yvalsLinear,
                               xvals2, yvals2, label2, xvalsPower, yvalsPower, 
                               color, marker, markerSize=5, e=None):
        
        self.view.panelPlots.bottomPlot1DT.clearPlot()            
        self.view.panelPlots.bottomPlot1DT.plotScatter_2plot(xvals1, yvals1, label1,
                                                             xvalsLinear, yvalsLinear,
                                                             xvals2, yvals2, label2,
                                                             xvalsPower, yvalsPower, 
                                                             color, marker, markerSize=5,
                                                             axesSize=self.config.plotSizes['CalibrationDT'])
        self.view.panelPlots.bottomPlot1DT.repaint() 
        
    def onPlotWaterfall(self, yvals, xvals, xlabel, cmap, e=None):

        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap

        self.view.panelPlots.plotWaterfallIMS.clearPlot()
        self.view.panelPlots.plotWaterfallIMS.plotNewWaterfallPlot(xvals=xvals, 
                                                                   yvals=yvals, 
                                                                   yOffset=0, 
                                                                   yIncrement=self.config.waterfallOffset,
                                                                   color='black', cmap=cmap,
                                                                   label="", xlabel=xlabel,
                                                                   axesSize=self.config.plotSizes['Waterfall'],
                                                                   plotName='1D')
    
        # Show the mass spectrum
        self.view.panelPlots.plotWaterfallIMS.repaint() 

    def addMarkerMS(self, xvals=None, yvals=None, color='b', marker='o', size=5, plot='MS'):
        if plot == 'MS':
            self.view.panelPlots.plot1.onAddMarker(xval=xvals, 
                                                   yval=yvals,
                                                   color=color,
                                                   marker=marker,
                                                   size=size)
            self.view.panelPlots.plot1.repaint()
        elif plot == 'RT':
            self.view.panelPlots.plotRT.onAddMarker(xval=xvals, 
                                                   yval=yvals,
                                                   color=color,
                                                   marker=marker,
                                                   size=size)
            self.view.panelPlots.plotRT.repaint()
        elif plot == 'CalibrationMS':
            self.view.panelPlots.topPlotMS.onAddMarker(xval=xvals, 
                                                       yval=yvals,
                                                       color=color,
                                                       marker=marker,
                                                       size=size)
            self.view.panelPlots.topPlotMS.repaint()
        elif plot == 'CalibrationDT':
            self.view.panelPlots.bottomPlot1DT.onAddMarker(xval=xvals, 
                                                           yval=yvals,
                                                           color=color,
                                                           marker=marker,
                                                           size=size,
                                                           testMax='yvals')
            self.view.panelPlots.bottomPlot1DT.repaint()
             
    def addRectMS(self, x, y, width, height, color='r', alpha=0.5, repaint=False, plot = 'MS'):
        
        if plot == 'MS': 
            self.view.panelPlots.plot1.addRectangle(x,y, width,
                                                height, color=color,
                                                alpha=alpha)
            if not repaint: return 
            else:
                self.view.panelPlots.plot1.repaint()
        elif plot == 'CalibrationMS':
            self.view.panelPlots.topPlotMS.addRectangle(x,y, width,
                                                height, color=color,
                                                alpha=alpha)
            if not repaint: return 
            else:
                self.view.panelPlots.topPlotMS.repaint()
            
    def addRectRT(self, x, y, width, height, color='r', alpha=0.5, repaint=False):   
        self.view.panelPlots.plotRT.addRectangle(x,y,
                                                width,
                                                height,
                                                color=color,
                                                alpha=alpha)
        if not repaint: return 
        else:
            self.view.panelPlots.plotRT.repaint()

    def addTextMS(self, x,y, text, rotation, color="k"):
        self.view.panelPlots.plot1.addText(x,y, text, rotation, color)
        self.view.panelPlots.plot1.repaint()
        
    def addTextRMSD(self, x,y, text, rotation, color="k", plot='RMSD'):
        if plot == 'RMSD':
            self.view.panelPlots.plot2D.addText(x,y, text, 
                                                rotation, 
                                                color=self.config.rmsdColor,
                                                fontsize=self.config.rmsdFontSize)
            self.view.panelPlots.plot2D.repaint()
        elif plot == 'RMSF':
            self.view.panelPlots.plotRMSF.addText(x,y, text, 
                                                rotation, 
                                                color=self.config.rmsdColor,
                                                fontsize=self.config.rmsdFontSize,
                                                weight=self.config.rmsdFontWeight)
            self.view.panelPlots.plotRMSF.repaint()
        
    def onAddMarker1D(self, xval=None, yval=None, color='r', marker='o'):
        """ 
        This function adds marker to 1D plot
        """
        # Check yaxis labels
        ydivider = self.testXYmaxVals(values=yval)
        yval = yval / ydivider
        # Add single point
        self.view.panelPlots.bottomPlot1DT.onAddMarker(xval=xval, 
                                                       yval=yval,
                                                       color=color,
                                                       marker=marker)
        self.view.panelPlots.bottomPlot1DT.repaint() 
        
    def onZoomMS(self, startX, endX, endY, plot='MS'):
        if plot == 'MS':
            self.view.panelPlots.plot1.onZoomIn(startX,endX, endY)
            self.view.panelPlots.plot1.repaint()
        elif plot == 'CalibrationMS':
            self.view.panelPlots.topPlotMS.onZoomIn(startX,endX,endY)
    
    def OnChangedRMSF(self, xmin, xmax):
        """
        Receives a message about change in RMSF plot
        """
        
        self.view.panelPlots.plotRMSF.onZoomRMSF(xmin, xmax)
        
    def onZoom2D(self, evt):
        if self.config.restrictXYrange:
            if len(self.config.xyLimits) != 4: return 
            
            startX, endX, startY, endY = self.config.xyLimits
            
            msg = ' '.join(['Zoomed in: X:', str(startX),'-',str(endX),
                            'Y:',str(startY),'-',str(endY)])
            self.view.SetStatusText(msg, 3)
            self.view.panelPlots.plot2D.onZoom2D(startX,endX, startY, endY)
            self.view.panelPlots.plot2D.repaint()
            if self.config.addWaterfall:
                # Axes are rotated so using yaxis limits
                self.view.panelPlots.plotWaterfallIMS.onZoom1D(startY, endY)
                self.view.panelPlots.plotWaterfallIMS.repaint()
        
    def onClearPlot(self, evt, plot=None):
        """
        Clear selected plot
        """
        
        id = evt.GetId()
            
        if plot == 'MS' or id == ID_clearPlot_MS:
            self.view.panelPlots.plot1.clearPlot()
            self.view.panelPlots.plot1.repaint()
        elif plot =='RT' or id == ID_clearPlot_RT:
            self.view.panelPlots.plotRT.clearPlot()
            self.view.panelPlots.plotRT.repaint()
        elif plot == '1D' or id == ID_clearPlot_1D:
            self.view.panelPlots.plot1D.clearPlot()
            self.view.panelPlots.plot1D.repaint()
        elif plot == '2D' or id == ID_clearPlot_2D:
            self.view.panelPlots.plot2D.clearPlot()
            self.view.panelPlots.plot2D.repaint()
        elif plot == 'DT/MS' or id == ID_clearPlot_MZDT:
            self.view.panelPlots.plotMZDT.clearPlot()
            self.view.panelPlots.plotMZDT.repaint()
        elif plot == '3D' or id == ID_clearPlot_3D:
            self.view.panelPlots.plot3D.clearPlot()
            self.view.panelPlots.plot3D.repaint()
        elif plot == 'RMSF' or id == ID_clearPlot_RMSF:
            self.view.panelPlots.plotRMSF.clearPlot()
            self.view.panelPlots.plotRMSF.repaint()
        elif plot == 'Overlay' or id == ID_clearPlot_Overlay:
            self.view.panelPlots.plotOverlay.clearPlot()
            self.view.panelPlots.plotOverlay.repaint()
        elif plot == 'Matrix' or id == ID_clearPlot_Matrix:
            self.view.panelPlots.plotCompare.clearPlot()
            self.view.panelPlots.plotCompare.repaint()
        elif plot == 'Waterall' or id == ID_clearPlot_Watefall:
            self.view.panelPlots.plotWaterfallIMS.clearPlot()
            self.view.panelPlots.plotWaterfallIMS.repaint()
        elif plot == 'Calibration' or id == ID_clearPlot_Calibration:
            self.view.panelPlots.topPlotMS.clearPlot()
            self.view.panelPlots.topPlotMS.repaint()
            self.view.panelPlots.bottomPlot1DT.clearPlot()
            self.view.panelPlots.bottomPlot1DT.repaint()
    
        self.view.SetStatusText("Cleared plot", 3)
        
    def onRebootZoom(self, evt):
        plotList = [self.view.panelPlots.plot1, 
                    self.view.panelPlots.plotRT, 
                    self.view.panelPlots.plotRMSF, self.view.panelPlots.plotMZDT,
                    self.view.panelPlots.plotCompare, self.view.panelPlots.plot2D, 
                    self.view.panelPlots.plot3D, self.view.panelPlots.plotOverlay,
                    self.view.panelPlots.plotWaterfallIMS, self.view.panelPlots.topPlotMS, 
                    self.view.panelPlots.bottomPlot1DT]
        
        for plot in plotList:
            plot.onRebootZoomKeys(evt=None)
        
        # Message
        self.view.SetStatusText("Reset zoom keys", 3)
    
    def onClearAllPlots(self, evt=None):
        
        # Delete all plots
        plotList = [self.view.panelPlots.plot1, self.view.panelPlots.plotRT, 
                    self.view.panelPlots.plotRMSF,self.view.panelPlots.plot1D,
                    self.view.panelPlots.plotCompare, self.view.panelPlots.plot2D, 
                    self.view.panelPlots.plot3D, self.view.panelPlots.plotOverlay,
                    self.view.panelPlots.plotWaterfallIMS, self.view.panelPlots.topPlotMS, 
                    self.view.panelPlots.bottomPlot1DT, self.view.panelPlots.plotMZDT]
        
        for plot in plotList:
            plot.clearPlot()
            plot.repaint()
        # Message
        self.view.SetStatusText("Clear all plots", 3)

#===============================================================================
#  SAVE IMAGES
#===============================================================================

    def saveImages2(self, evt, path=None):
        """ Save figure depending on the event ID """
        
        tstart = time.clock()
        # Build kwargs
        kwargs = {"transparent":self.config.transparent,
                  "dpi":self.config.dpi, 
                  'format':self.config.imageFormat,
                  'compression':"zlib",
                  'resize': None}
        
        path, title = self.getCurrentDocumentPath()
        if path == None: return
        
        # Select default name + link to the plot
        if evt.GetId() == ID_saveMSImage or evt.GetId() == ID_saveMSImageDoc:
            defaultName = "MS"
            resizeName = "MS"
            plotWindow = self.view.panelPlots.plot1
            
        elif evt.GetId() == ID_saveRTImage or evt.GetId() == ID_saveRTImageDoc:
            defaultName = "RT"
            resizeName = "RT"
            plotWindow = self.view.panelPlots.plotRT
            
        elif evt.GetId() == ID_save1DImage or evt.GetId() == ID_save1DImageDoc:
            defaultName = "IMS1D"
            resizeName = "DT"
            plotWindow = self.view.panelPlots.plot1D
            
        elif evt.GetId() == ID_save2DImage or evt.GetId() == ID_save2DImageDoc:
            defaultName = "IMS2D"
            resizeName = "2D"
            plotWindow = self.view.panelPlots.plot2D
            
        elif evt.GetId() == ID_save3DImage or evt.GetId() == ID_save3DImageDoc:
            defaultName = "IMS3D"
            resizeName = "3D"
            plotWindow = self.view.panelPlots.plot3D
            
        elif evt.GetId() == ID_saveWaterfallImage or evt.GetId() == ID_saveWaterfallImageDoc:
            defaultName = "Waterfall"
            resizeName = "Waterfall"
            plotWindow = self.view.panelPlots.plotWaterfallIMS
            
        elif evt.GetId() == ID_saveRMSDImage or evt.GetId() == ID_saveRMSDImageDoc:
            defaultName = "RMSD"
            resizeName = "RMSD"
            plotWindow = self.view.panelPlots.plot2D
            
        elif evt.GetId() == ID_saveRMSFImage or evt.GetId() == ID_saveRMSFImageDoc:
            defaultName = "RMSF"
            resizeName = "RMSF"
            plotWindow = self.view.panelPlots.plotRMSF
            
        elif evt.GetId() == ID_saveOverlayImage or evt.GetId() == ID_saveOverlayImageDoc:
            defaultName = "Overlay"
            resizeName = "Overlay"
            plotWindow = self.view.panelPlots.plotOverlay
            
        elif evt.GetId() == ID_saveRMSDmatrixImage or evt.GetId() == ID_saveRMSDmatrixImageDoc:
            defaultName = "Matrix"
            resizeName = "Matrix"
            plotWindow = self.view.panelPlots.plotCompare
            
        elif evt.GetId() == ID_saveMZDTImage or evt.GetId() == ID_saveMZDTImageDoc:
            defaultName = "DTMS"
            resizeName = "DTMS"
            plotWindow = self.view.panelPlots.plotMZDT

        # Setup filename
        saveFileName = self.getImageFilename(prefix=True, csv=False, 
                                             defaultValue=defaultName)
        if saveFileName =='' or saveFileName == None: 
            saveFileName = defaultName
            
        
        if self.config.resize:
            kwargs['resize'] = resizeName # self.config.plotResize.get(resizeName, None)
            
        filename = ''.join([path, "\\", saveFileName, '.', self.config.imageFormat])
        if not self.config.threading:
            plotWindow.saveFigure2(path=filename, **kwargs)
            tend = time.clock()
            msg = "".join(['Saved figure to: ', filename, '. It took: ', 
                           str(np.round((tend-tstart),2)), ' s.'])
            self.view.SetStatusText(msg, 3)
            print(msg)
        else: 
            args = [plotWindow, filename, kwargs]
            self.onThreading(evt, args, action='saveFigs')
            
        tstart = time.clock()
        if path==None:
            path, title = self.getCurrentDocumentPath()
            path = ''.join([path, '\overlay.'])
            
        if path == None: return
        
        # Add extension
        path = ''.join([path, self.config.imageFormat])
        
        # Build kwargs
        kwargs = {"transparent":self.config.transparent,
                  "dpi":self.config.dpi, 
                  'format':self.config.imageFormat}
        
        self.view.panelPlots.plotOverlay.saveFigure2(path=path, **kwargs)
        tend = time.clock()
        msg = "".join(['Saved figure to: ', path, '. It took: ', 
                       str(np.round((tend-tstart),2)), ' s.'])
        self.view.SetStatusText(msg, 3)

    def saveMSImage(self, event=None, path=None):
        
        tstart = time.clock()
        if path==None:
            path, title = self.getCurrentDocumentPath()
            path = ''.join([path, '\MS.'])
            
        if path == None: return
        # Add extension
        path = ''.join([path, self.config.imageFormat])
        
        # Build kwargs
        kwargs = {"transparent":self.config.transparent,
                  "dpi":self.config.dpi, 
                  'format':self.config.imageFormat}
        
        self.view.panelPlots.plot1.saveFigure2(path=path, **kwargs)
        tend = time.clock()
        msg = "".join(['Saved figure to: ', path, '. It took: ', 
                       str(np.round((tend-tstart),2)), ' s.'])
        self.view.SetStatusText(msg, 3)
        print(msg)

    def saveRTImage(self, event=None, path=None):
        

        tstart = time.clock()
        if path==None:
            path, title = self.getCurrentDocumentPath()
            path = ''.join([path, '\RT.'])
            
        if path == None: return
        # Add extension
        path = ''.join([path, self.config.imageFormat])
        
        # Build kwargs
        kwargs = {"transparent":self.config.transparent,
                  "dpi":self.config.dpi, 
                  'format':self.config.imageFormat}
        
        self.view.panelPlots.plotRT.saveFigure2(path=path, **kwargs)
        tend = time.clock()
        msg = "".join(['Saved figure to: ', path, '. It took: ', 
                       str(np.round((tend-tstart),2)), ' s.'])
        self.view.SetStatusText(msg, 3)
        print(msg)
        
    def save1DIMSImage(self, event=None, path=None):

        
        tstart = time.clock()
        if path==None:
            path, title = self.getCurrentDocumentPath()
            path = ''.join([path, '\IMS1D.'])
            
        if path == None: return
        # Add extension
        path = ''.join([path, self.config.imageFormat])
        
        # Build kwargs
        kwargs = {"transparent":self.config.transparent,
                  "dpi":self.config.dpi, 
                  'format':self.config.imageFormat}
        
        self.view.panelPlots.plot1D.saveFigure2(path=path, **kwargs)
        tend = time.clock()
        msg = "".join(['Saved figure to: ', path, '. It took: ', 
                       str(np.round((tend-tstart),2)), ' s.'])
        self.view.SetStatusText(msg, 3)
        print(msg)

    def save2DIMSImage(self, event=None, path=None):
        
        tstart = time.clock()
        if path==None:
            path, title = self.getCurrentDocumentPath()
            path = ''.join([path, '\IMS2D.'])
            
        if path == None: return
        # Add extension
        path = ''.join([path, self.config.imageFormat])
        
        # Build kwargs
        kwargs = {"transparent":self.config.transparent,
                  "dpi":self.config.dpi, 
                  'format':self.config.imageFormat}
        
        self.view.panelPlots.plot2D.saveFigure2(path=path, **kwargs)
        tend = time.clock()
        msg = "".join(['Saved figure to: ', path, '. It took: ', 
                       str(np.round((tend-tstart),2)), ' s.'])
        self.view.SetStatusText(msg, 3)
        print(msg)

    def save3DIMSImage(self, event=None, path=None):

       
        tstart = time.clock()
        if path==None:
            path, title = self.getCurrentDocumentPath()
            path = ''.join([path, '\IMS3D.'])
            
        if path == None: return
        
        # Add extension
        path = ''.join([path, self.config.imageFormat])
        
        # Build kwargs
        kwargs = {"transparent":self.config.transparent,
                  "dpi":self.config.dpi, 
                  'format':self.config.imageFormat}
        
        self.view.panelPlots.plot3D.saveFigure2(path=path, **kwargs)
        tend = time.clock()
        msg = "".join(['Saved figure to: ', path, '. It took: ', 
                       str(np.round((tend-tstart),2)), ' s.'])
        self.view.SetStatusText(msg, 3)
        print(msg)

    def saveWaterfallImage(self, event=None, path=None):

        tstart = time.clock()
        if path==None:
            path, title = self.getCurrentDocumentPath()
            path = ''.join([path, '\Waterfall.'])
            
        if path == None: return
        
        # Add extension
        path = ''.join([path, self.config.imageFormat])

        # Build kwargs
        kwargs = {"transparent":self.config.transparent,
                  "dpi":self.config.dpi, 
                  'format':self.config.imageFormat}
        
        self.view.panelPlots.plotWaterfallIMS.saveFigure2(path=path, **kwargs)
        tend = time.clock()
        msg = "".join(['Saved figure to: ', path, '. It took: ', 
                       str(np.round((tend-tstart),2)), ' s.'])
        self.view.SetStatusText(msg, 3)
        print(msg)
        
    def saveMatrixImage(self, event=None, path=None):
       
        tstart = time.clock()
        if path==None:
            path, title = self.getCurrentDocumentPath()
            path = ''.join([path, '\RMSDmatrix.'])
            
        if path == None: return
        # Add extension
        path = ''.join([path, self.config.imageFormat])
        
        # Build kwargs
        kwargs = {"transparent":self.config.transparent,
                  "dpi":self.config.dpi, 
                  'format':self.config.imageFormat}
        
        self.view.panelPlots.plotCompare.saveFigure2(path=path, **kwargs)
        tend = time.clock()
        msg = "".join(['Saved figure to: ', path, '. It took: ', 
                       str(np.round((tend-tstart),2)), ' s.'])
        self.view.SetStatusText(msg, 3)
        print(msg)
    
    def saveRMSDImage(self, event=None, path=None):
        
        tstart = time.clock()
        if path==None:
            path, title = self.getCurrentDocumentPath()
            path = ''.join([path, '\RMSD.'])
            
        if path == None: return
        # Add extension
        path = ''.join([path, self.config.imageFormat])
        
        # Build kwargs
        kwargs = {"transparent":self.config.transparent,
                  "dpi":self.config.dpi, 
                  'format':self.config.imageFormat}
        
        self.view.panelPlots.plot2D.saveFigure2(path=path, **kwargs)
        tend = time.clock()
        msg = "".join(['Saved figure to: ', path, '. It took: ', 
                       str(np.round((tend-tstart),2)), ' s.'])
        self.view.SetStatusText(msg, 3)
        print(msg)

    def saveRMSFImage(self, event=None, path=None):

        tstart = time.clock()
        if path==None:
            path, title = self.getCurrentDocumentPath()
            path = ''.join([path, '\RMSF.'])
            
        if path == None: return
        # Add extension
        path = ''.join([path, self.config.imageFormat])
        
        # Build kwargs
        kwargs = {"transparent":self.config.transparent,
                  "dpi":self.config.dpi, 
                  'format':self.config.imageFormat}
        
        self.view.panelPlots.plotRMSF.saveFigure2(path=path, **kwargs)
        tend = time.clock()
        msg = "".join(['Saved figure to: ', path, '. It took: ', 
                       str(np.round((tend-tstart),2)), ' s.'])
        self.view.SetStatusText(msg, 3)
        print(msg)

    def onImportConfig(self, evt, onStart=False):
        """
        This function imports configuration file
        """
        if not onStart:
            if evt.GetId() == ID_openConfig:
                self.config.loadConfigXML(path='configOut.xml', evt=None)
                self.view.panelControls.importFromConfig(evt=None)
                self.view.panelControls.onPopulateAdvancedSettings(evt=None)
                return
            elif evt.GetId() == ID_openAsConfig:
                dlg = wx.FileDialog(self.view, "Open Configuration File", wildcard = "*.xml" ,
                                   style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
                if dlg.ShowModal() == wx.ID_OK:
                    fileName=dlg.GetPath()
                    self.config.loadConfigXML(path=fileName, evt=None)
                    self.view.panelControls.importFromConfig(evt=None)
                    self.view.panelControls.onPopulateAdvancedSettings(evt=None)
        else:
            print('Loaded configuration file')
            self.config.loadConfigXML(path='configOut.xml', evt=None)
            self.view.panelControls.importFromConfig(evt=None)
            self.view.panelControls.onPopulateAdvancedSettings(evt=None)
            return
        
    def onExportConfig(self, evt): 
        if evt.GetId() == ID_saveConfig:
            self.config.saveConfigXML(path='configOut.xml', evt=None)
        elif evt.GetId() == ID_saveAsConfig:
            dlg = wx.FileDialog(self.view, "Save As Configuration File", wildcard = "*.xml" ,
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            dlg.SetFilename('configOut.xml')
            if dlg.ShowModal() == wx.ID_OK:
                fileName=dlg.GetPath()
                self.config.saveConfigXML(path=fileName, evt=None)
    
    def onSetupDriftScope(self, evt):
        """
        This function sets the Driftscope directory
        """
        dlg = wx.DirDialog(self.view, "Choose a MassLynx file:",
                           style=wx.DD_DEFAULT_STYLE)
        dlg.SetPath(self.config.driftscopePath)
        if dlg.ShowModal() == wx.ID_OK:
            self.config.driftscopePath = dlg.GetPath()
            msg = ''.join(['Driftscope path: ',self.config.driftscopePath])
            self.view.SetStatusText(msg, 3)
            
            # Check if driftscope exists
            if not os.path.isdir(self.config.driftscopePath):
                print('Could not find Driftscope path')
                msg = "Could not localise Driftscope directory. Please setup path to Dritscope lib folder. It usually exists under C:\DriftScope\lib"
                dialogs.dlgBox(exceptionTitle='Could not find Driftscope', 
                               exceptionMsg= msg,
                               type="Warning")

            if not os.path.isfile(self.config.driftscopePath+"\imextract.exe"):
                print('Could not find imextract.exe')
                msg = "Could not localise Driftscope imextract.exe program. Please setup path to Dritscope lib folder. It usually exists under C:\DriftScope\lib"
                dialogs.dlgBox(exceptionTitle='Could not find Driftscope', 
                               exceptionMsg= msg,
                               type="Warning")
        evt.Skip()
    
    def openDirectory(self, evt=None):
        path, title = self.getCurrentDocumentPath()
        if path == None or title == None:
            self.view.SetStatusText('Please select a document')
            return
        try:
            os.startfile(path)
        except WindowsError:
            dialogs.dlgBox(exceptionTitle='This folder does not exist', 
                           exceptionMsg= "Could not open the directory - this folder does not exist",
                           type="Error")
            return

    def getCurrentDocumentPath(self):
        '''
        Function used to get the path to current document
        '''
        # Gather info about the file and document
        self.currentDoc, selectedItem, selectedText = self.view.panelDocuments.topP.documents.enableCurrentDocument(getSelected=True)
        indent = self.view.panelDocuments.topP.documents.getItemIndent(selectedItem)
        if self.currentDoc == 'Current documents':
            return None, None
        elif indent > 2:
            selectedItemParent, selectedItemParentText = self.view.panelDocuments.topP.documents.getParentItem(selectedItem,2, getSelected=True)
#             print(selectedText, indent, selectedItemParentText)
        else: pass
#             print(selectedText, indent)
        document = self.documentsDict[self.currentDoc]
        return document.path, document.title

    def saveObjectData(self, objName, evt=None):
        # Get directory path
        self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
        document = self.documentsDict[self.currentDoc]   
        saveName = dialogs.dlgAsk('Save data as...', defaultValue='')
        if saveName == '': 
            self.view.SetStatusText('Please select a name first', 3)
            return
        # Prep classification filename
        saveFileName = document.path+'/'+saveName+'.pickle'
        # Save
        saveObject(filename=saveFileName, saveFile=objName)

    def onSaveDocument(self, evt):
        """
        This function saves whole document to a pickled directory
        """
        fileType = "ORIGAMI Document File|*.pickle"
        
        # Save single document
        if evt.GetId() == ID_saveDocument:
            self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()
            if self.currentDoc == 'Current documents': return
            document = self.documentsDict[self.currentDoc]
            
            dlg =  wx.FileDialog(self.view, "Save document to file...", "", "", fileType,
                                    wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            defaultFilename = document.title.split(".")
            dlg.SetFilename(defaultFilename[0])
            
            if dlg.ShowModal() == wx.ID_OK:
                saveFileName = dlg.GetPath()          
                # Save
                saveObject(filename=saveFileName, saveFile=document)
            else: return
        # Save multiple documents
        elif evt.GetId() == ID_saveAllDocuments:
            for document in self.documentsDict:
                dlg =  wx.FileDialog(self.view, "Save document to file...", "", "", fileType,
                                        wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                defaultFilename = self.documentsDict[document].title.split(".")
                dlg.SetFilename(defaultFilename[0])
                
                if dlg.ShowModal() == wx.ID_OK:
                    saveFileName = dlg.GetPath()          
                    # Save
                    saveObject(filename=saveFileName, 
                               saveFile=self.documentsDict[document])
                else: continue
                   
    def onOpenDocument(self, evt):
        """
        This function opens whole document to a pickled directory
        """
        dlg = wx.FileDialog(self.view, "Open Document File", wildcard = "*.pickle" ,
                           style=wx.FD_MULTIPLE| wx.FD_CHANGE_DIR  )
        if dlg.ShowModal() == wx.ID_OK:
            pathlist = dlg.GetPaths()
            filenames = dlg.GetFilenames()
            for (file, filename) in zip(pathlist,filenames):
                print "You chose %s" % file
                document = openObject(filename=file)
                if isinstance(document, list):
                    msg = ''.join(["Sorry, cannot load the document file as file appears to be corrupt. Here is the error message: ", 
                                   "\n", str(document[1])])
                    dialogs.dlgBox(exceptionTitle='Cannot load document file', 
                                   exceptionMsg=msg,
                                   type="Error")
                    return
            
                idName = document.title
                self.documentsDict[idName] = document
                
                # Restore various plots into the program
                if document.dataType == 'Type: ORIGAMI':
                    self.config.ciuMode = 'ORIGAMI'
                elif document.dataType == 'Type: MANUAL':
                    self.config.ciuMode = 'MANUAL'
                elif document.dataType == 'Type: Multifield Linear DT':
                    self.config.ciuMode = 'LinearDT'
                elif document.dataType == 'Type: Infrared':
                    self.config.ciuMode = 'Infrared'
        
                if any([document.gotExtractedIons, document.got2DprocessIons, 
                       document.gotCombinedExtractedIonsRT, document.gotCombinedExtractedIons]):
                    self.config.extractMode = 'multipleIons'
                else:
                    self.config.extractMode = 'singleIon'
                
                if document.gotMS:
                    self.view.SetStatusText('Loaded MS', 3)
                    msX = document.massSpectrum['xvals']
                    msY = document.massSpectrum['yvals']
                    color = document.lineColour
                    style = document.style
                    try: xlimits = document.massSpectrum['xlimits']
                    except KeyError: 
                        xlimits = [document.parameters['startMS'],document.parameters['endMS']]
                    if document.dataType != 'Type: CALIBRANT':
                        self.onPlotMS2(msX, msY, color, style, xlimits=xlimits)
                    else:
                        self.onPlotMSDTCalibration(msX=msX, msY=msY, color=color, xlimits=xlimits,
                                                         plotType='MS')
                if document.got1DT:
                    self.view.SetStatusText('Loaded 1D IM-MS', 3)
                    dtX = document.DT['xvals']
                    dtY = document.DT['yvals']
                    xlabel = document.DT['xlabels']
                    color = document.lineColour
                    style = document.style
                    if document.dataType != 'Type: CALIBRANT':
                        self.onPlot1DIMS2(dtX, dtY, xlabel, color, style)
                    else:
                        self.onPlotMSDTCalibration(dtX=dtX, dtY=dtY, color=color,
                                                   xlabelDT=xlabel, plotType='1DT')
                if document.got1RT:
                    self.view.SetStatusText('Loaded RT', 3)
                    rtX = document.RT['xvals']
                    rtY = document.RT['yvals']
                    xlabel = document.RT['xlabels']
                    color = document.lineColour
                    style = document.style
                    self.onPlotRT2(rtX, rtY, xlabel, color, style)
                if document.got2DIMS:
                    self.view.SetStatusText('Loaded 2D IM-MS', 3)
                    dataOut = self.get2DdataFromDictionary(dictionary=document.IMS2D,
                                                                     dataType='plot',
                                                                     compact=True)
                    self.plot2Ddata2(data=dataOut)
    
                # Restore ion list
                if self.config.extractMode == 'multipleIons':
                    tempList = self.view.panelMultipleIons.topP.peaklist
                    if len(document.IMS2DCombIons) > 0:
                        dataset = document.IMS2DCombIons
                        print('Using combined dataset')
                    elif len(document.IMS2DCombIons) == 0:
                        dataset = document.IMS2Dions
                        print('Using extracted dataset')
                    elif len(document.IMS2Dions) == 0:
                        dataset = {}
                    if len(dataset) > 0:
                        for key in dataset:
                            out = key.split('-')
                            charge = dataset[key].get('charge', None)
                            label = dataset[key].get('label', None)
                            alpha = dataset[key].get('alpha', None)
                            cmap = dataset[key].get('cmap', None)
                            xylimits = dataset[key].get('xylimits', None)
                            if xylimits != None:
                                xylimits = xylimits[2]

                            method = dataset[key].get('parameters', None)
                            if method != None:
                                method = method.get('method', "")
                            elif method == None and document.dataType == 'Type: MANUAL':
                                method = 'Manual'
                            else:
                                method = ""
                                
                            tempList.Append([out[0],out[1],
                                             charge,
                                             cmap,
                                             str(alpha),
                                             document.title, 
                                             method,
                                             str(xylimits),
                                             str(label)])

                        # Update aui manager
                        self.view.mainToolbar.ToggleTool(id=ID_OnOff_ionView, toggle=True)
                        self.view.peakView = False
                        self.view.mzTable.Check(True)
                        self.view._mgr.GetPane(self.view.panelMultipleIons).Show()
                        self.view._mgr.Update()
                    self.view.panelMultipleIons.topP.onRemoveDuplicates(evt=None, limitCols=False)
                    
                # Restore file list
                if self.config.ciuMode == 'MANUAL':
                    tempList = self.view.panelMML.topP.filelist
                    for key in document.multipleMassSpectrum:
                        energy = document.multipleMassSpectrum[key]['trap']
                        tempList.Append([key,energy,document.title])
                        
                    # Update aui manager
                    self.view.mainToolbar.ToggleTool(id=ID_OnOff_mlynxView, toggle=True)
                    self.view.masslynxView = False
                    self.view.multipleMLTable.Check(True)
                    self.view._mgr.GetPane(self.view.panelMML).Show()
                    self.view._mgr.Update()
                    
                # Restore calibration list
                if document.dataType == 'Type: CALIBRANT':
                    tempList = self.view.panelCCS.topP.peaklist
                    if document.fileFormat == 'Format: MassLynx (.raw)':
                        for key in document.calibration:
                            print(key)
                            tempList.Append([document.title,
                                             str(document.calibration[key]['xrange'][0]),
                                             str(document.calibration[key]['xrange'][1]),
                                             document.calibration[key]['protein'],
                                             str(document.calibration[key]['charge']),
                                             str(document.calibration[key]['ccs']),
                                             str(document.calibration[key]['tD']),
                                             ])
                    elif document.fileFormat == 'Format: DataFrame':
                        try:
                            self.currentCalibrationParams = document.calibrationParameters
                        except KeyError: pass 
                        for key in document.calibration:
                            tempList.Append([document.title,
                                             str(document.calibration[key]['xrange'][0]),
                                             str(document.calibration[key]['xrange'][1]),
                                             document.calibration[key]['protein'],
                                             str(document.calibration[key]['charge']),
                                             str(document.calibration[key]['ccs']),
                                             str(document.calibration[key]['tD']),
                                             ])
                    # Check for duplicates
                    self.view.panelCCS.topP.onRemoveDuplicates(evt=None)
                    # Update aui manager
                    self.view.ccsView = False
                    self.view.ccsTable.Check(True)
                    self.view.mainToolbar.ToggleTool(id=ID_OnOff_ccsView, toggle=True)
                    self.view._mgr.GetPane(self.view.panelCCS).Show()
                    self.view._mgr.Update()              
                    
                # Restore ion list 
                if self.config.ciuMode == 'LinearDT':
                    rtList = self.view.panelLinearDT.topP.peaklist # List with MassLynx file information 
                    mzList = self.view.panelLinearDT.bottomP.peaklist # List with m/z information
                    for key in document.IMS1DdriftTimes:
                        retTimes = document.IMS1DdriftTimes[key]['retTimes']
                        driftVoltages = document.IMS1DdriftTimes[key]['driftVoltage']
                        mzVals = document.IMS1DdriftTimes[key]['xylimits']
                        mzStart = mzVals[0]
                        mzEnd = mzVals[1]
                        mzYmax = mzVals[2]
                        charge = document.IMS1DdriftTimes[key]['charge']
                        for row in range(len(retTimes)):
                            rtStart = retTimes[row][0]
                            rtEnd  = retTimes[row][1]
                            rtDiff = rtEnd-rtStart
                            driftVoltage = driftVoltages[row]
                            rtList.Append([str(rtStart), str(rtEnd), str(rtDiff), str(driftVoltage), document.title])
                        self.view.panelLinearDT.topP.onRemoveDuplicates(evt=None)
                        mzList.Append([str(mzStart), str(mzEnd), str(mzYmax), str(charge), document.title])
                    self.view.panelLinearDT.bottomP.onRemoveDuplicates(evt=None)
                    
                    self.view.dtView = False
                    self.view.multifieldTable.Check(True)
                    self.view.mainToolbar.ToggleTool(id=ID_OnOff_dtView, toggle=True)
                    self.view._mgr.GetPane(self.view.panelLinearDT).Show()
                    self.view._mgr.Update()

            
                # Update documents tree
                self.view.panelDocuments.topP.documents.addDocument(docData = document)
            self.currentDoc = self.view.panelDocuments.topP.documents.enableCurrentDocument()

    def onLibraryLink(self, evt):
        """Open selected webpage."""
        
        # set link
        links = {ID_helpHomepage : 'home',
                 ID_helpGitHub : 'github',
                 ID_helpCite : 'cite',
                 ID_helpNewVersion : 'newVersion',
                 ID_helpYoutube: 'youtube',
                 ID_helpGuide: 'guide',
                 ID_helpHTMLEditor: 'htmlEditor'}
        
        link = self.config.links[links[evt.GetId()]]
        
        # open webpage
        try: 
            self.view.SetStatusText("Opening a link in your default internet browser", 3)
            webbrowser.open(link, autoraise=1)
        except: pass
        
    def removeDuplicates(self, input, columnsIn=None, limitedCols=None):
        """ remove duplicates from list based on columns """
        
        df = pd.DataFrame(input, columns=columnsIn)
        df.drop_duplicates(subset=limitedCols, inplace=True)
        output = df.values.tolist()
        return output

    def onCheckVersion(self, evt):
        """ 
        Simple function to check whether this is the newest version available
        """
        
        try:
            newVersion = checkVersion(link=self.config.links['newVersion'])
            update = compareVersions(newVersion, self.config.version)
            if not update:
                print('You are using the most up to date version %s.' % (self.config.version))
            else:
                message = "Version %s is now available for download.\nYou are currently using version %s." % (newVersion, self.config.version)
                dialogs.dlgBox(exceptionTitle='New version available online.', 
                exceptionMsg= message,
                type="Info")
        except:
            print('Could not check version number')

    def onOpenUserGuide(self, evt):
        """ 
        Opens PDF viewer
        """
        try:
            os.startfile('UserGuide_ANALYSE.pdf')
        except:
            return
        
        
if __name__ == '__main__':
    app = ORIGAMI(redirect=False)
    app.start()