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

import wx, os, time
import wx.lib.agw.multidirdialog as MDD

from document import document as documents
import readers.io_waters_raw as io_waters
from toolbox import (getTime, randomColorGenerator, convertRGB1to255)
from gui_elements.dialog_selectDocument import panelSelectDocument
import processing.spectra as pr_spectra
import numpy as np
import pandas as pd


class data_loading():

    def __init__(self, presenter, view, config, **kwargs):
        self.presenter = presenter
        self.view = view
        self.documentTree = view.panelDocuments.documents
        self.config = config

    def on_create_document(self, name, path, **kwargs):
        """
        Create document
        """

        document = documents()
        document.title = name
        document.path = path
        document.userParameters = self.config.userParameters
        document.userParameters['date'] = getTime()

    def on_open_multiple_ML_files(self, open_type, pathlist=[]):
        # http://stackoverflow.com/questions/1252481/sort-dictionary-by-another-dictionary
        # http://stackoverflow.com/questions/22520739/python-sort-a-dict-by-values-producing-a-list-how-to-sort-this-from-largest-to

        self.config.ciuMode = 'MANUAL'
        tempList = self.view.panelMML.peaklist

        tstart = time.clock()
        if len(pathlist) > 0:
            dlg = None
        else:
            if self.config.lastDir == None or not os.path.isdir(self.config.lastDir):
                self.config.lastDir = os.getcwd()

            dlg = MDD.MultiDirDialog(self.view, title="Choose MassLynx files to open:",
                                     defaultPath=self.config.lastDir,
                                     agwStyle=MDD.DD_MULTIPLE | MDD.DD_DIR_MUST_EXIST)

            if dlg.ShowModal() == wx.ID_OK:
                pathlist = dlg.GetPaths()

        if open_type == "multiple_files_add":
            # Check if current document is a comparison document
            # If so, it will be used
            docList = self.checkIfAnyDocumentsAreOfType(type='Type: MANUAL')

            if len(docList) == 0:
                self.onThreading(None, ("Did not find appropriate document. Creating a new one...", 4),
                                 action='updateStatusbar')
                dlg = wx.FileDialog(self.view, "Please select a name for the document",
                                     "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                if dlg.ShowModal() == wx.ID_OK:
                    path, idName = os.path.split(dlg.GetPath())
                else: return
                # Create document
                self.docs = documents()
                self.docs.title = idName
                self.docs.path = path
                self.docs.userParameters = self.config.userParameters
                self.docs.userParameters['date'] = getTime()
            else:
                self.selectDocDlg = panelSelectDocument(self.view, self, docList)
                if self.selectDocDlg.ShowModal() == wx.ID_OK:
                    pass

                # Check that document exists
                if self.currentDoc == None:
                    self.onThreading(None, ('Please select a document', 4), action='updateStatusbar')
                    return
                self.docs = self.documentsDict[self.currentDoc]
                self.onThreading(None, ('Using document: ' + self.docs.title.encode('ascii', 'replace'), 4),
                                 action='updateStatusbar')

        elif open_type == "multiple_files_new_document":
            dlg = wx.FileDialog(self.view, "Please select a name for the document",
                                 "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            if dlg.ShowModal() == wx.ID_OK:
                path, idName = os.path.split(dlg.GetPath())
            else: return
            # Create document
            self.docs = documents()
            self.docs.title = idName
            self.docs.path = path
            self.docs.userParameters = self.config.userParameters
            self.docs.userParameters['date'] = getTime()

        for i, file_path in enumerate(pathlist):
            path = self.checkIfRawFile(file_path)
            if path is None:
                continue
            else:
                try:
                    pathSplit = path.encode('ascii', 'replace').split(':)')
                    start = pathSplit[0].split('(')
                    start = start[-1]
                    path = ''.join([start, ':', pathSplit[1]])
                except IndexError:
                    path = path
                temp, rawfile = os.path.split(path)
                # Update lastDir with current path
                self.config.lastDir = path
                parameters = self.config.importMassLynxInfFile(path=path, manual=True)
                xlimits = [parameters['startMS'], parameters['endMS']]
                extract_kwargs = {'return_data':True}
                msDataX, msDataY = io_waters.rawMassLynx_MS_extract(path=path,
                                                                    driftscope_path=self.config.driftscopePath,
                                                                    **extract_kwargs)
                extract_kwargs = {'return_data':True}
                xvalsDT, imsData1D = io_waters.rawMassLynx_DT_extract(path=path,
                                                                 driftscope_path=self.config.driftscopePath,
                                                                 **extract_kwargs)
                if i <= 15: color = self.config.customColors[i]
                else: color = randomColorGenerator(True)
                color = self.view.panelMML.on_check_duplicate_colors(color,
                                                                          document_name=self.docs.title)

                tempList.Append([rawfile,
                                 str(parameters['trapCE']),
                                 self.docs.title,
                                 os.path.splitext(rawfile)[0]])  # name as initial label
                tempList.SetItemBackgroundColour(tempList.GetItemCount() - 1,
                                                 convertRGB1to255(color))

                self.docs.gotMultipleMS = True
                self.docs.multipleMassSpectrum[rawfile] = {'trap':parameters['trapCE'],
                                                           'xvals':msDataX, 'yvals':msDataY,
                                                           'ims1D':imsData1D, 'ims1DX':xvalsDT,
                                                           'xlabel':'Drift time (bins)',
                                                           'xlabels':'m/z (Da)',
                                                           'path': path, 'color':color,
                                                           'parameters':parameters,
                                                           'xlimits':xlimits}
        # Sum all mass spectra into one
        if self.config.ms_enable_in_MML_start:
            msFilenames = ["m/z"]
            counter = 0
            kwargs = {'auto_range':self.config.ms_auto_range,
                      'mz_min':self.config.ms_mzStart,
                      'mz_max':self.config.ms_mzEnd,
                      'mz_bin':self.config.ms_mzBinSize,
                      'linearization_mode':self.config.ms_linearization_mode}
            msg = "Linearization method: {} | min: {} | max: {} | window: {} | auto-range: {}".format(self.config.ms_linearization_mode,
                                                                                                      self.config.ms_mzStart,
                                                                                                      self.config.ms_mzEnd,
                                                                                                      self.config.ms_mzBinSize,
                                                                                                      self.config.ms_auto_range)
            self.onThreading(None, (msg, 4), action='updateStatusbar')

            for key in self.docs.multipleMassSpectrum:
                msFilenames.append(key)
                if counter == 0:
                    msDataX, tempArray = pr_spectra.linearize_data(self.docs.multipleMassSpectrum[key]['xvals'],
                                                                   self.docs.multipleMassSpectrum[key]['yvals'],
                                                                   **kwargs)
                    msList = tempArray
                else:
                    msDataX, msList = pr_spectra.linearize_data(self.docs.multipleMassSpectrum[key]['xvals'],
                                                                self.docs.multipleMassSpectrum[key]['yvals'],
                                                                **kwargs)
                    tempArray = np.concatenate((tempArray, msList), axis=0)
                counter += 1

            # Reshape the list
            combMS = tempArray.reshape((len(msList), int(counter)), order='F')

            # Sum y-axis data
            msDataY = np.sum(combMS, axis=1)
            msDataY = pr_spectra.normalize_1D(inputData=msDataY)
            xlimits = [parameters['startMS'], parameters['endMS']]

            # Form pandas dataframe
            combMSOut = np.concatenate((msDataX, tempArray), axis=0)
            combMSOut = combMSOut.reshape((len(msList), int(counter + 1)), order='F')

            msSaveData = pd.DataFrame(data=combMSOut, columns=msFilenames)

            # Add data
            self.docs.gotMSSaveData = True
            self.docs.massSpectraSave = msSaveData  # pandas dataframe that can be exported as csv
            self.docs.gotMS = True
            self.docs.massSpectrum = {'xvals':msDataX, 'yvals':msDataY, 'xlabels':'m/z (Da)', 'xlimits':xlimits}
            # Plot
            name_kwargs = {"document":self.docs.title, "dataset": "Mass Spectrum"}
            self.view.panelPlots.on_plot_MS(msDataX, msDataY, xlimits=xlimits, **name_kwargs)

        # Update status bar with MS range
        self.view.SetStatusText("{}-{}".format(parameters['startMS'], parameters['endMS']), 1)
        self.view.SetStatusText("MSMS: {}".format(parameters['setMS']), 2)

        # Add info to document
        self.docs.parameters = parameters
        self.docs.dataType = 'Type: MANUAL'
        self.docs.fileFormat = 'Format: MassLynx (.raw)'
        self.OnUpdateDocument(self.docs, 'document')

        # Show panel
        self.view.onPaneOnOff(evt=ID_window_multipleMLList, check=True)
        # Removing duplicates
        self.view.panelMML.onRemoveDuplicates(evt=None)

        tend = time.clock()
        self.onThreading(None, ('Total time to extract %d files was: %.3gs' % (len(pathlist), tend - tstart), 4), action='updateStatusbar')
