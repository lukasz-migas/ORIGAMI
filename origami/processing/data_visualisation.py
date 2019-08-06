# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging
import os
import re

import numpy as np
import processing.activation as pr_activation
import processing.heatmap as pr_heatmap
import processing.spectra as pr_spectra
import wx
from document import document as documents
from gui_elements.dialog_select_document import DialogSelectDocument
from gui_elements.misc_dialogs import DialogBox
from numpy.ma.core import masked_array
from toolbox import removeDuplicates
from utils.color import combine_rgb
from utils.color import convertRGB255to1
from utils.color import make_rgb
from utils.converters import str2num
from utils.time import getTime

logger = logging.getLogger("origami")


class data_visualisation:
    """Module that carries out more complex visualisation steps"""

    def __init__(self, presenter, view, config):
        self.presenter = presenter
        self.view = view
        self.config = config

        # processing links
        self.data_processing = self.view.data_processing

        # panel links
        self.documentTree = self.view.panelDocuments.documents

        self.plotsPanel = self.view.panelPlots

        self.ionPanel = self.view.panelMultipleIons
        self.ionList = self.ionPanel.peaklist

        self.textPanel = self.view.panelMultipleText
        self.textList = self.textPanel.peaklist

        self.filesPanel = self.view.panelMML
        self.filesList = self.filesPanel.peaklist

        # add application defaults
        self.plot_page = None

    def _setup_handling_and_processing(self):
        self.data_handling = self.view.data_handling
        self.data_processing = self.view.data_processing

    def on_overlay_mobilogram(self, item_list, **kwargs):
        # TODO: Add checks for size and shape
        # TODO: Add possibility to add to document

        # Empty lists
        xlist, ylist, colorlist, legend = [], [], [], []
        for item_info in item_list:
            # get data
            try:
                query_info = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
                __, data = self.data_handling.get_mobility_chromatographic_data(query_info)
            except KeyError:
                continue

            # get data
            xvals = data["yvals"]
            yvals = data.get("yvals1D", data["zvals"].sum(axis=1))

            if kwargs.get("normalize_dataset", False):
                yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
                yvals = pr_spectra.normalize_1D(yvals)
            xlabels = data["xlabels"]

            # Append data to list
            xlist.append(xvals)
            ylist.append(yvals)
            colorlist.append(item_info["color_255to1"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append(label)

        # plot
        xlimits = [min(xvals), max(xvals)]
        self.plotsPanel.on_plot_overlay_RT(
            xvals=xlist, yvals=ylist, xlabel=xlabels, colors=colorlist, xlimits=xlimits, labels=legend, **kwargs
        )

        # generate dataset holder
        dataset_holder = {
            "xvals": xlist,
            "yvals": ylist,
            "xlabel": xlabels,
            "colors": colorlist,
            "xlimits": xlimits,
            "labels": legend,
        }
        return dataset_holder

    def on_overlay_chromatogram(self, item_list, **kwargs):

        # Empty lists
        xlist, ylist, colorlist, legend, dataset_info = [], [], [], [], []
        for item_info in item_list:
            # get data
            try:
                query_info = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
                __, data = self.data_handling.get_mobility_chromatographic_data(query_info)
            except KeyError:
                continue

            dataset_info.append(query_info)

            # get data
            xvals = data["xvals"]
            yvals = data.get("yvalsRT", data["zvals"].sum(axis=0))

            if kwargs.get("normalize_dataset", False):
                yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
                yvals = pr_spectra.normalize_1D(yvals)
            xlabels = data["xlabels"]

            # Append data to list
            xlist.append(xvals)
            ylist.append(yvals)
            colorlist.append(item_info["color_255to1"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append(label)

        # plot
        xlimits = [min(xvals), max(xvals)]
        self.plotsPanel.on_plot_overlay_RT(
            xvals=xlist, yvals=ylist, xlabel=xlabels, colors=colorlist, xlimits=xlimits, labels=legend, **kwargs
        )

        # generate dataset holder
        dataset_holder = {
            "name": "",
            "data": {
                "xvals": xlist,
                "yvals": ylist,
                "xlabel": xlabels,
                "colors": colorlist,
                "xlimits": xlimits,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }
        return dataset_holder

    def on_overlay_1D(self, source, plot_type):
        """
        This function enables overlaying of multiple ions together - 1D and RT
        """
        # Check what is the ID
        if source == "ion":
            tempList = self.ionList
            add_data_to_document = self.view.panelMultipleIons.addToDocument
            normalize_dataset = self.view.panelMultipleIons.normalize1D
        elif source == "text":
            tempList = self.textList
            add_data_to_document = self.view.panelMultipleText.addToDocument
            normalize_dataset = self.view.panelMultipleText.normalize1D

        if add_data_to_document:
            document = self._get_document_of_type("Type: Comparison")
            document_title = document.title

        # Empty lists
        xlist, ylist, colorlist, legend = [], [], [], []
        idName = ""
        # Get data for the dataset
        for row in range(tempList.GetItemCount()):
            if tempList.IsChecked(index=row):
                if source == "ion":
                    # Get current document
                    itemInfo = self.ionPanel.OnGetItemInformation(itemID=row)
                    document_title = itemInfo["document"]
                    # Check that data was extracted first
                    if document_title == "":
                        continue

                    document = self.data_handling._on_get_document(document_title)
                    dataType = document.dataType
                    selectedItem = itemInfo["ionName"]
                    label = itemInfo["label"]
                    color = convertRGB255to1(itemInfo["color"])
                    itemName = "ion={} ({})".format(selectedItem, document_title)

                    # ORIGAMI dataset
                    if dataType == "Type: ORIGAMI" and document.gotCombinedExtractedIons:
                        try:
                            data = document.IMS2DCombIons[selectedItem]
                        except KeyError:
                            try:
                                data = document.IMS2Dions[selectedItem]
                            except KeyError:
                                continue
                    elif dataType == "Type: ORIGAMI" and not document.gotCombinedExtractedIons:
                        try:
                            data = document.IMS2Dions[selectedItem]
                        except KeyError:
                            continue

                    # MANUAL dataset
                    if dataType == "Type: MANUAL" and document.gotCombinedExtractedIons:
                        try:
                            data = document.IMS2DCombIons[selectedItem]
                        except KeyError:
                            try:
                                data = document.IMS2Dions[selectedItem]
                            except KeyError:
                                continue

                    # Add new label
                    if idName == "":
                        idName = itemName
                    else:
                        idName = "{}, {}".format(idName, itemName)

                    # Add depending which event was triggered
                    if plot_type == "mobiligram":
                        xvals = data["yvals"]  # normally this would be the y-axis
                        yvals = data["yvals1D"]
                        if normalize_dataset:
                            yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
                            yvals = pr_spectra.normalize_1D(yvals)
                        xlabels = data["ylabels"]  # data was rotated so using ylabel for xlabel

                    elif plot_type == "chromatogram":
                        xvals = data["xvals"]
                        yvals = data["yvalsRT"]
                        if normalize_dataset:
                            yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
                            yvals = pr_spectra.normalize_1D(yvals)
                        xlabels = data["xlabels"]

                    # Append data to list
                    xlist.append(xvals)
                    ylist.append(yvals)
                    colorlist.append(color)
                    if label == "":
                        label = selectedItem
                    legend.append(label)
                elif source == "text":
                    itemInfo = self.textPanel.OnGetItemInformation(itemID=row)
                    document_title = itemInfo["document"]
                    label = itemInfo["label"]
                    color = itemInfo["color"]
                    color = convertRGB255to1(itemInfo["color"])
                    # get document
                    try:
                        document = self.data_handling._on_get_document(document_title)
                        comparison_flag = False
                        selectedItem = document_title
                        itemName = "file={}".format(document_title)
                    except Exception as __:
                        comparison_flag = True
                        document_title, ion_name = re.split(": ", document_title)
                        document = self.data_handling._on_get_document(document_title)
                        selectedItem = ion_name
                        itemName = "file={}".format(ion_name)

                    # Text dataset
                    if comparison_flag:
                        try:
                            data = document.IMS2DcompData[ion_name]
                        except Exception:
                            data = document.IMS2Dions[ion_name]
                    else:
                        try:
                            data = document.IMS2D
                        except Exception:
                            logger.error("No data for selected file")
                            continue

                    # Add new label
                    if idName == "":
                        idName = itemName
                    else:
                        idName = "{}, {}".format(idName, itemName)

                    # Add depending which event was triggered
                    if plot_type == "mobiligram":
                        xvals = data["yvals"]  # normally this would be the y-axis
                        try:
                            yvals = data["yvals1D"]
                        except KeyError:
                            yvals = np.sum(data["zvals"], axis=1).T
                        if normalize_dataset:
                            yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
                            yvals = pr_spectra.normalize_1D(yvals)
                        xlabels = data["ylabels"]  # data was rotated so using ylabel for xlabel

                    elif plot_type == "chromatogram":
                        xvals = data["xvals"][:-1]  # TEMPORARY FIX
                        try:
                            yvals = data["yvalsRT"]
                        except KeyError:
                            yvals = np.sum(data["zvals"], axis=0)
                        if normalize_dataset:
                            yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
                            yvals = pr_spectra.normalize_1D(yvals)
                        xlabels = data["xlabels"]

                    # Append data to list
                    xlist.append(xvals)
                    ylist.append(yvals)
                    colorlist.append(color)
                    if label == "":
                        label = selectedItem
                    legend.append(label)

        # Modify the name to include ion tags
        if plot_type == "mobiligram":
            idName = "1D: %s" % idName
        elif plot_type == "chromatogram":
            idName = "RT: %s" % idName

        # remove unnecessary file extensions from filename
        if len(idName) > 511:
            logger.warning("Filename was too long. Reducing...")
            idName = idName.replace(".csv", "").replace(".txt", "").replace(".raw", "").replace(".d", "")
            idName = idName[:500]

        # Determine x-axis limits for the zoom function
        try:
            xlimits = [min(xvals), max(xvals)]
        except UnboundLocalError:
            logger.error("Please select at least one item in the table")
            return

        # Add data to dictionary
        if add_data_to_document:
            document = self._get_document_of_type("Type: Comparison")
            document.gotOverlay = True
            document.IMS2DoverlayData[idName] = {
                "xvals": xlist,
                "yvals": ylist,
                "xlabel": xlabels,
                "colors": colorlist,
                "xlimits": xlimits,
                "labels": legend,
            }
            document_title = document.title
            self.data_handling.on_update_document(document, "comparison_data")

        # Plot
        if plot_type == "mobiligram":
            self.plotsPanel.on_plot_overlay_DT(
                xvals=xlist,
                yvals=ylist,
                xlabel=xlabels,
                colors=colorlist,
                xlimits=xlimits,
                labels=legend,
                set_page=True,
            )
        elif plot_type == "chromatogram":
            self.plotsPanel.on_plot_overlay_RT(
                xvals=xlist,
                yvals=ylist,
                xlabel=xlabels,
                colors=colorlist,
                xlimits=xlimits,
                labels=legend,
                set_page=True,
            )

    def on_overlay_2D(self, source):
        """
        This function enables overlaying multiple ions from the same CIU datasets together
        """
        # Check what is the ID
        if source == "ion":
            tempList = self.view.panelMultipleIons.peaklist
            col_order = self.config.peaklistColNames
            add_data_to_document = self.view.panelMultipleIons.addToDocument
            self.config.overlayMethod = self.view.panelMultipleIons.combo.GetStringSelection()
        elif source == "text":
            tempList = self.view.panelMultipleText.peaklist
            col_order = self.config.textlistColNames
            add_data_to_document = self.view.panelMultipleText.addToDocument
            self.config.overlayMethod = self.view.panelMultipleText.combo.GetStringSelection()

        tempAccumulator = 0  # Keeps count of how many items are ticked
        try:
            self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
        except Exception:
            return
        if self.currentDoc == "Documents":
            return

        # Check if current document is a comparison document
        # If so, it will be used
        if add_data_to_document:
            if self.documentsDict[self.currentDoc].dataType == "Type: Comparison":
                self.docs = self.documentsDict[self.currentDoc]
                self.onThreading(
                    None, ("Using document: " + self.docs.title.encode("ascii", "replace"), 4), action="updateStatusbar"
                )
                if self.docs.gotComparisonData:
                    compDict = self.docs.IMS2DcompData
                    compList = []
                    for key in self.docs.IMS2DcompData:
                        compList.append(key)
                else:
                    compDict, compList = {}, []
            else:
                self.onThreading(None, ("Checking if there is a comparison document", 4), action="updateStatusbar")
                docList = self.checkIfAnyDocumentsAreOfType(type="Type: Comparison")
                if len(docList) == 0:
                    self.onThreading(
                        None, ("Did not find appropriate document. Creating a new one", 4), action="updateStatusbar"
                    )
                    dlg = wx.FileDialog(
                        self.view,
                        "Please select a name for the comparison document",
                        "",
                        "",
                        "",
                        wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                    )
                    if dlg.ShowModal() == wx.ID_OK:
                        path, idName = os.path.split(dlg.GetPath())
                    else:
                        return

                    # Create document
                    self.docs = documents()
                    self.docs.title = idName
                    self.docs.path = path
                    self.docs.userParameters = self.config.userParameters
                    self.docs.userParameters["date"] = getTime()
                    self.docs.dataType = "Type: Comparison"
                    self.docs.fileFormat = "Format: ORIGAMI"
                    # Initiate empty list and dictionary
                    compDict, compList = {}, []
                else:
                    self.selectDocDlg = DialogSelectDocument(self.view, presenter=self, document_list=docList)
                    if self.selectDocDlg.ShowModal() == wx.ID_OK:
                        pass

                    # Check that document exists
                    if self.currentDoc is None:
                        msg = "Please select comparison document"
                        self.onThreading(None, (msg, 4), action="updateStatusbar")
                        return

                    self.docs = self.documentsDict[self.currentDoc]
                    self.onThreading(
                        None,
                        ("Using document: " + self.docs.title.encode("ascii", "replace"), 4),
                        action="updateStatusbar",
                    )
                    if self.docs.gotComparisonData:
                        compDict = self.docs.IMS2DcompData
                        compList = []
                        for key in self.docs.IMS2DcompData:
                            compList.append(key)
                    else:
                        compDict, compList = {}, []
        else:
            compDict, compList = {}, []

        comparisonFlag = False
        # Get data for the dataset
        for row in range(tempList.GetItemCount()):
            if tempList.IsChecked(index=row):
                if source == "ion":
                    # Get data for each ion
                    (
                        __,
                        __,
                        charge,
                        color,
                        colormap,
                        alpha,
                        mask,
                        label,
                        self.currentDoc,
                        ionName,
                        min_threshold,
                        max_threshold,
                    ) = self.view.panelMultipleIons.OnGetItemInformation(itemID=row, return_list=True)

                    # processed name
                    ionNameProcessed = "%s (processed)" % ionName

                    # Check that data was extracted first
                    if self.currentDoc == "":
                        msg = "Please extract data first"
                        self.onThreading(None, (msg, 4), action="updateStatusbar")
                        continue
                    document = self.documentsDict[self.currentDoc]
                    dataType = document.dataType

                    # ORIGAMI dataset
                    if dataType in ["Type: ORIGAMI", "Type: MANUAL"] and document.gotCombinedExtractedIons:
                        if self.config.overlay_usedProcessed:
                            try:
                                dataIn = document.IMS2DCombIons[ionNameProcessed]
                            except KeyError:
                                try:
                                    dataIn = document.IMS2DCombIons[ionName]
                                except KeyError:
                                    try:
                                        dataIn = document.IMS2Dions[ionNameProcessed]
                                    except KeyError:
                                        try:
                                            dataIn = document.IMS2Dions[ionName]
                                        except KeyError:
                                            continue
                        else:
                            try:
                                dataIn = document.IMS2DCombIons[ionName]
                            except KeyError:
                                try:
                                    dataIn = document.IMS2Dions[ionName]
                                except KeyError:
                                    continue
                    elif dataType in ["Type: ORIGAMI", "Type: MANUAL"] and not document.gotCombinedExtractedIons:
                        if self.config.overlay_usedProcessed:
                            try:
                                dataIn = document.IMS2Dions[ionNameProcessed]
                            except KeyError:
                                try:
                                    dataIn = document.IMS2Dions[ionName]
                                except KeyError:
                                    continue
                        else:
                            try:
                                dataIn = document.IMS2Dions[ionName]
                            except KeyError:
                                continue

                    #                     # MANUAL dataset
                    #                     if dataType == 'Type: MANUAL' and document.gotCombinedExtractedIons:
                    #                         try: tempData = document.IMS2DCombIons
                    #                         except KeyError:
                    #                             try: tempData = document.IMS2Dions
                    #                             except KeyError: continue

                    # INFRARED dataset
                    if dataType == "Type: Infrared" and document.gotCombinedExtractedIons:
                        try:
                            dataIn = document.IMS2DCombIons
                        except KeyError:
                            try:
                                dataIn = document.IMS2Dions
                            except KeyError:
                                continue
                    tempAccumulator = tempAccumulator + 1

                    selectedItemUnique = "ion={} ({})".format(ionName, self.currentDoc)
                    zvals, xaxisLabels, xlabel, yaxisLabels, ylabel, __ = self.get2DdataFromDictionary(
                        dictionary=dataIn, dataType="plot", compact=False
                    )

                elif source == "text":
                    tempAccumulator += 1
                    comparisonFlag = False  # used only in case the user reloaded comparison document
                    # Get data for each ion
                    itemInfo = self.view.panelMultipleText.OnGetItemInformation(itemID=row)
                    charge = itemInfo["charge"]
                    color = itemInfo["color"]
                    colormap = itemInfo["colormap"]
                    alpha = itemInfo["alpha"]
                    mask = itemInfo["mask"]
                    label = itemInfo["label"]
                    filename = itemInfo["document"]
                    min_threshold = itemInfo["min_threshold"]
                    max_threshold = itemInfo["max_threshold"]
                    # get document
                    try:
                        document = self.documentsDict[filename]

                        if self.config.overlay_usedProcessed:
                            if document.got2Dprocess:
                                try:
                                    tempData = document.IMS2Dprocess
                                except Exception:
                                    tempData = document.IMS2D
                            else:
                                tempData = document.IMS2D
                        else:
                            try:
                                tempData = document.IMS2D
                            except Exception:
                                self.onThreading(None, ("No data for selected file", 4), action="updateStatusbar")
                                continue

                        zvals = tempData["zvals"]
                        xaxisLabels = tempData["xvals"]
                        xlabel = tempData["xlabels"]
                        yaxisLabels = tempData["yvals"]
                        ylabel = tempData["ylabels"]
                        ionName = filename
                        # Populate x-axis labels
                        if isinstance(xaxisLabels, list):
                            pass
                        elif xaxisLabels == "":
                            startX = tempList.GetItem(itemId=row, col=self.config.textlistColNames["startX"]).GetText()
                            endX = tempList.GetItem(itemId=row, col=self.config.textlistColNames["endX"]).GetText()
                            stepsX = len(zvals[0])
                            if startX == "" or endX == "":
                                pass
                            else:
                                xaxisLabels = self.onPopulateXaxisTextLabels(
                                    startVal=str2num(startX), endVal=str2num(endX), shapeVal=stepsX
                                )
                                document.IMS2D["xvals"] = xaxisLabels

                        if not comparisonFlag:
                            selectedItemUnique = "file:%s" % filename
                    # only triggered when using data from comparison document
                    except Exception:
                        try:
                            comparisonFlag = True
                            dpcument_filename, selectedItemUnique = re.split(": ", filename)
                            document = self.documentsDict[dpcument_filename]
                            tempData = document.IMS2DcompData[selectedItemUnique]
                            # unpack data
                            zvals = tempData["zvals"]
                            ionName = tempData["ion_name"]
                            xaxisLabels = tempData["xvals"]
                            yaxisLabels = tempData["yvals"]
                            ylabel = tempData["ylabels"]
                            xlabel = tempData["xlabels"]
                        # triggered when using data from interactive document
                        except Exception:
                            comparisonFlag = False
                            dpcument_filename, selectedItemUnique = re.split(": ", filename)
                            document = self.documentsDict[dpcument_filename]
                            tempData = document.IMS2Dions[selectedItemUnique]
                            # unpack data
                            zvals = tempData["zvals"]
                            ionName = filename
                            xaxisLabels = tempData["xvals"]
                            yaxisLabels = tempData["yvals"]
                            ylabel = tempData["ylabels"]
                            xlabel = tempData["xlabels"]

                if not comparisonFlag:
                    if label == "" or label is None:
                        label = ""
                    compList.insert(0, selectedItemUnique)
                    # Check if exists. We need to extract labels (header...)
                    checkExist = compDict.get(selectedItemUnique, None)
                    if checkExist is not None:
                        title = compDict[selectedItemUnique].get("header", "")
                        header = compDict[selectedItemUnique].get("header", "")
                        footnote = compDict[selectedItemUnique].get("footnote", "")
                    else:
                        title, header, footnote = "", "", ""
                    compDict[selectedItemUnique] = {
                        "zvals": zvals,
                        "ion_name": ionName,
                        "cmap": colormap,
                        "color": color,
                        "alpha": str2num(alpha),
                        "mask": str2num(mask),
                        "xvals": xaxisLabels,
                        "xlabels": xlabel,
                        "yvals": yaxisLabels,
                        "charge": charge,
                        "min_threshold": min_threshold,
                        "max_threshold": max_threshold,
                        "ylabels": ylabel,
                        "index": row,
                        "shape": zvals.shape,
                        "label": label,
                        "title": title,
                        "header": header,
                        "footnote": footnote,
                    }
                else:
                    compDict[selectedItemUnique] = tempData

        # Check whether the user selected at least two files (and no more than 2 for certain functions)
        if tempAccumulator < 2:
            msg = "Please select at least two files"
            DialogBox(exceptionTitle="Error", exceptionMsg=msg, type="Error")
            return

        # Remove duplicates from list
        compList = removeDuplicates(compList)

        zvalsIon1plot = compDict[compList[0]]["zvals"]
        zvalsIon2plot = compDict[compList[1]]["zvals"]
        name1 = compList[0]
        name2 = compList[1]
        # Check if text files are of identical size
        if (zvalsIon1plot.shape != zvalsIon2plot.shape) and self.config.overlayMethod not in ["Grid (n x n)"]:
            msg = "Comparing ions: {} and {}. These files are NOT of identical shape!".format(name1, name2)
            DialogBox(exceptionTitle="Error", exceptionMsg=msg, type="Error")
            return

        defaultVals = ["Reds", "Greens"]
        ylabelRMSF = "RMSD (%)"
        # Check if the table has information about colormap
        if compDict[compList[0]]["cmap"] == "":
            cmapIon1 = defaultVals[0]  # change here
            compDict[compList[0]]["cmap"] = cmapIon1
            tempList.SetStringItem(index=compDict[compList[0]]["index"], col=3, label=cmapIon1)
        else:
            cmapIon1 = compDict[compList[0]]["cmap"]

        if compDict[compList[1]]["cmap"] == "":
            cmapIon2 = defaultVals[1]
            compDict[compList[1]]["cmap"] = cmapIon1
            tempList.SetStringItem(index=compDict[compList[1]]["index"], col=3, label=cmapIon2)
        else:
            cmapIon2 = compDict[compList[1]]["cmap"]

        # Defaults for alpha and mask
        defaultVals_alpha = [1, 0.5]
        defaultVals_mask = [0.25, 0.25]

        # Check if the user set value of transparency (alpha)
        if compDict[compList[0]]["alpha"] == "" or compDict[compList[0]]["alpha"] is None:
            alphaIon1 = defaultVals_alpha[0]
            compDict[compList[0]]["alpha"] = alphaIon1
            tempList.SetStringItem(index=compDict[compList[0]]["index"], col=col_order["alpha"], label=str(alphaIon1))
        else:
            alphaIon1 = str2num(compDict[compList[0]]["alpha"])

        if compDict[compList[1]]["alpha"] == "" or compDict[compList[1]]["alpha"] is None:
            alphaIon2 = defaultVals_alpha[1]
            compDict[compList[1]]["alpha"] = alphaIon2
            tempList.SetStringItem(index=compDict[compList[1]]["index"], col=col_order["alpha"], label=str(alphaIon2))
        else:
            alphaIon2 = str2num(compDict[compList[1]]["alpha"])

        # Check if the user set value of transparency (mask)
        if compDict[compList[0]]["mask"] == "" or compDict[compList[0]]["mask"] is None:
            maskIon1 = defaultVals_mask[0]
            compDict[compList[0]]["mask"] = maskIon1
            tempList.SetStringItem(index=compDict[compList[0]]["index"], col=col_order["mask"], label=str(maskIon1))
        else:
            maskIon1 = str2num(compDict[compList[0]]["mask"])

        if compDict[compList[1]]["mask"] == "" or compDict[compList[1]]["mask"] is None:
            maskIon2 = defaultVals_mask[1]
            compDict[compList[1]]["mask"] = maskIon2
            tempList.SetStringItem(index=compDict[compList[1]]["index"], col=col_order["mask"], label=str(maskIon2))
        else:
            maskIon2 = str2num(compDict[compList[1]]["mask"])

        # Various comparison plots
        if self.config.overlayMethod == "Grid (2->1)":
            self.view.panelPlots.mainBook.SetSelection(self.config.panelNames["Overlay"])

            pRMSD, tempArray = pr_activation.compute_RMSD(inputData1=zvalsIon1plot, inputData2=zvalsIon2plot)
            rmsdLabel = "RMSD: %2.2f" % pRMSD
            self.onThreading(None, ("RMSD: %2.2f" % pRMSD, 4), action="updateStatusbar")
            self.setXYlimitsRMSD2D(xaxisLabels, yaxisLabels)
            self.view.panelPlots.on_plot_grid(
                zvalsIon1plot, zvalsIon2plot, tempArray, xaxisLabels, yaxisLabels, xlabel, ylabel, cmapIon1, cmapIon2
            )

            #             # Add RMSD label
            rmsdXpos, rmsdYpos = self.onCalculateRMSDposition(xlist=xaxisLabels, ylist=yaxisLabels)
            if rmsdXpos is not None and rmsdYpos is not None:
                self.addTextRMSD(rmsdXpos, rmsdYpos, rmsdLabel, 0, plot="Grid")

            # Add data to the dictionary (overlay data)
            idName = "{}, {}".format(compList[0], compList[1])
            idName = "{}: {}".format(self.config.overlayMethod, idName)
            if add_data_to_document:
                self.docs.gotOverlay = True
                # Add to the name to includ the method
                # Check if exists. We need to extract labels (header...)
                checkExist = self.docs.IMS2DoverlayData.get(idName, None)
                if checkExist is not None:
                    title = self.docs.IMS2DoverlayData[idName].get("header", "")
                    header = self.docs.IMS2DoverlayData[idName].get("header", "")
                    footnote = self.docs.IMS2DoverlayData[idName].get("footnote", "")
                else:
                    title, header, footnote = "", "", ""

                self.docs.IMS2DoverlayData[idName] = {
                    "zvals_1": zvalsIon1plot,
                    "zvals_2": zvalsIon2plot,
                    "zvals_cum": tempArray,
                    "cmap_1": cmapIon1,
                    "cmap_2": cmapIon2,
                    "xvals": xaxisLabels,
                    "xlabels": xlabel,
                    "yvals": yaxisLabels,
                    "ylabels": ylabel,
                    "rmsdLabel": rmsdLabel,
                    "title": title,
                    "header": header,
                    "footnote": footnote,
                }
        elif self.config.overlayMethod == "Grid (n x n)":
            zvals_list, xvals_list, yvals_list, cmap_list, title_list, idName = [], [], [], [], [], ""
            for row in range(tempAccumulator):
                key = compList[row]
                zvals_list.append(compDict[key]["zvals"])
                cmap_list.append(compDict[key]["cmap"])
                title_list.append(compDict[key]["label"])
                xvals_list.append(compDict[key]["xvals"])
                yvals_list.append(compDict[key]["yvals"])

                # Add new label
                if idName == "":
                    idName = compList[row]
                else:
                    idName = "{}, {}".format(idName, compList[row])

            n_grid = len(zvals_list)
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
            elif n_grid in list(range(17, 26)):
                n_rows, n_cols = 5, 5
            elif n_grid in list(range(26, 37)):
                n_rows, n_cols = 6, 6
            else:
                DialogBox(
                    exceptionTitle="Error",
                    exceptionMsg=f"Cannot plot grid larger than 6 x 6. You have selected {n_grid}",
                    type="Error",
                )
                return

            checkExist = compDict.get(selectedItemUnique, None)
            if checkExist is not None:
                title = compDict[selectedItemUnique].get("header", "")
                header = compDict[selectedItemUnique].get("header", "")
                footnote = compDict[selectedItemUnique].get("footnote", "")
            else:
                title, header, footnote = "", "", ""
            idName = "{}: {}".format(self.config.overlayMethod, idName)
            # remove unnecessary file extensions from filename
            if len(idName) > 511:
                print("Filename is too long. Reducing...")
                idName = idName.replace(".csv", "").replace(".txt", "").replace(".raw", "").replace(".d", "")
                idName = idName[:500]

            self.view.panelPlots.on_plot_n_grid(
                zvals_list, cmap_list, title_list, xvals_list, yvals_list, xlabel, ylabel
            )
            if add_data_to_document:
                self.docs.gotOverlay = True
                self.docs.IMS2DoverlayData[idName] = {
                    "zvals_list": zvals_list,
                    "cmap_list": cmap_list,
                    "title_list": title_list,
                    "plot_parameters": {"n_grid": n_grid, "n_rows": n_rows, "n_cols": n_cols},
                    "xvals": xvals_list,
                    "xlabels": xlabel,
                    "yvals": yvals_list,
                    "ylabels": ylabel,
                    "title": title,
                    "header": header,
                    "footnote": footnote,
                }

        elif self.config.overlayMethod in ["Transparent", "Mask", "RMSD", "RMSF"]:

            # Check how many items were selected
            if tempAccumulator > 2:
                msg = "Currently only supporting an overlay of two ions.\n" + "Comparing: {} and {}.".format(
                    compList[0], compList[1]
                )
                DialogBox(exceptionTitle="Warning", exceptionMsg=msg, type="Warning")
                print(msg)

            if self.config.overlayMethod == "Transparent":
                self.view.panelPlots.mainBook.SetSelection(self.config.panelNames["Overlay"])
                # Overlay plot of two species to see whether there is a difference between

                self.view.panelPlots.on_plot_overlay_2D(
                    zvalsIon1=zvalsIon1plot,
                    cmapIon1=cmapIon1,
                    alphaIon1=alphaIon1,
                    zvalsIon2=zvalsIon2plot,
                    cmapIon2=cmapIon2,
                    alphaIon2=alphaIon2,
                    xvals=xaxisLabels,
                    yvals=yaxisLabels,
                    xlabel=xlabel,
                    ylabel=ylabel,
                    flag="Text",
                    plotName="Transparent",
                )

            elif self.config.overlayMethod == "Mask":
                # In this case, the values are not transparency but a threshold cutoff! Values between 0-1
                cutoffIon1 = maskIon1
                cutoffIon2 = maskIon2
                # Based on the value in alpha/cutoff, data will be cleared up
                zvalsIon1plotMask = masked_array(zvalsIon1plot, zvalsIon1plot < cutoffIon1)
                zvalsIon1plot = zvalsIon1plotMask
                zvalsIon2plotMask = masked_array(zvalsIon2plot, zvalsIon2plot < cutoffIon2)
                zvalsIon2plot = zvalsIon2plotMask
                self.view.panelPlots.mainBook.SetSelection(self.config.panelNames["Overlay"])
                self.view.panelPlots.on_plot_overlay_2D(
                    zvalsIon1=zvalsIon1plotMask,
                    cmapIon1=cmapIon1,
                    alphaIon1=1,
                    zvalsIon2=zvalsIon2plotMask,
                    cmapIon2=cmapIon2,
                    alphaIon2=1,
                    xvals=xaxisLabels,
                    yvals=yaxisLabels,
                    xlabel=xlabel,
                    ylabel=ylabel,
                    flag="Text",
                    plotName="Mask",
                )

            elif self.config.overlayMethod == "RMSD":
                """ Compute RMSD of two selected files """
                # Check whether we should be restricting the RMSD range
                if self.config.restrictXYrangeRMSD:
                    zvalsIon1plot, xvals, yvals = self.restrictRMSDrange(
                        zvalsIon1plot, xaxisLabels, yaxisLabels, self.config.xyLimitsRMSD
                    )

                    zvalsIon2plot, xvals, yvals = self.restrictRMSDrange(
                        zvalsIon2plot, xaxisLabels, yaxisLabels, self.config.xyLimitsRMSD
                    )
                    xaxisLabels, yaxisLabels = xvals, yvals

                pRMSD, tempArray = pr_activation.compute_RMSD(inputData1=zvalsIon1plot, inputData2=zvalsIon2plot)
                rmsdLabel = "RMSD: %2.2f" % pRMSD
                self.onThreading(None, ("RMSD: %2.2f" % pRMSD, 4), action="updateStatusbar")

                self.setXYlimitsRMSD2D(xaxisLabels, yaxisLabels)

                self.view.panelPlots.on_plot_RMSD(
                    tempArray,
                    xaxisLabels,
                    yaxisLabels,
                    xlabel,
                    ylabel,
                    self.config.currentCmap,
                    plotType="RMSD",
                    set_page=True,
                )
                # Add RMSD label
                rmsdXpos, rmsdYpos = self.onCalculateRMSDposition(xlist=xaxisLabels, ylist=yaxisLabels)
                if rmsdXpos is not None and rmsdYpos is not None:
                    self.addTextRMSD(rmsdXpos, rmsdYpos, rmsdLabel, 0)
                try:
                    self.view.panelPlots.on_plot_3D(
                        zvals=tempArray,
                        labelsX=xaxisLabels,
                        labelsY=yaxisLabels,
                        xlabel=xlabel,
                        ylabel=ylabel,
                        zlabel="Intensity",
                        cmap=self.config.currentCmap,
                    )
                except Exception:
                    pass

            elif self.config.overlayMethod == "RMSF":
                """ Compute RMSF of two selected files """
                self.rmsdfFlag = True

                if self.config.restrictXYrangeRMSD:
                    zvalsIon1plot, xvals, yvals = self.restrictRMSDrange(
                        zvalsIon1plot, xaxisLabels, yaxisLabels, self.config.xyLimitsRMSD
                    )

                    zvalsIon2plot, xvals, yvals = self.restrictRMSDrange(
                        zvalsIon2plot, xaxisLabels, yaxisLabels, self.config.xyLimitsRMSD
                    )
                    xaxisLabels, yaxisLabels = xvals, yvals

                pRMSFlist = pr_activation.compute_RMSF(inputData1=zvalsIon1plot, inputData2=zvalsIon2plot)
                pRMSD, tempArray = pr_activation.compute_RMSD(inputData1=zvalsIon1plot, inputData2=zvalsIon2plot)

                rmsdLabel = "RMSD: %2.2f" % pRMSD
                self.onThreading(None, ("RMSD: %2.2f" % pRMSD, 4), action="updateStatusbar")
                xLabel = compDict[compList[0]]["xlabels"]
                yLabel = compDict[compList[0]]["ylabels"]
                pRMSFlist = pr_heatmap.smooth_gaussian_2D(inputData=pRMSFlist, sigma=1)

                self.setXYlimitsRMSD2D(xaxisLabels, yaxisLabels)
                self.view.panelPlots.on_plot_RMSDF(
                    yvalsRMSF=pRMSFlist,
                    zvals=tempArray,
                    xvals=xaxisLabels,
                    yvals=yaxisLabels,
                    xlabelRMSD=xLabel,
                    ylabelRMSD=yLabel,
                    ylabelRMSF=ylabelRMSF,
                    color=self.config.lineColour_1D,
                    cmap=self.config.currentCmap,
                )
                #                 self.onPlotRMSDF(yvalsRMSF=pRMSFlist,
                #                                  zvals=tempArray,
                #                                  xvals=xaxisLabels, yvals=yaxisLabels,
                #                                  xlabelRMSD=xLabel, ylabelRMSD=yLabel,
                #                                  ylabelRMSF=ylabelRMSF,
                #                                  color=self.config.lineColour_1D,
                #                                  cmap=self.config.currentCmap)
                self.view.panelPlots.mainBook.SetSelection(self.config.panelNames["RMSF"])
                # Add RMSD label
                rmsdXpos, rmsdYpos = self.onCalculateRMSDposition(xlist=xaxisLabels, ylist=yaxisLabels)
                if rmsdXpos is not None and rmsdYpos is not None:
                    self.addTextRMSD(rmsdXpos, rmsdYpos, rmsdLabel, 0, plot="RMSF")

            # Add data to the dictionary (overlay data)
            if add_data_to_document:
                self.docs.gotOverlay = True
                # add label
                idName = "{}, {}".format(compList[0], compList[1])

                idName = "{}: {}".format(self.config.overlayMethod, idName)
                # Add to the name to includ the method
                # Check if exists. We need to extract labels (header...)
                checkExist = self.docs.IMS2DoverlayData.get(idName, None)
                if checkExist is not None:
                    title = self.docs.IMS2DoverlayData[idName].get("header", "")
                    header = self.docs.IMS2DoverlayData[idName].get("header", "")
                    footnote = self.docs.IMS2DoverlayData[idName].get("footnote", "")
                else:
                    title, header, footnote = "", "", ""
                # Add data to dictionary
                if self.config.overlayMethod in ["Mask", "Transparent"]:
                    self.docs.IMS2DoverlayData[idName] = {
                        "zvals1": zvalsIon1plot,
                        "zvals2": zvalsIon2plot,
                        "cmap1": cmapIon1,
                        "cmap2": cmapIon2,
                        "alpha1": alphaIon1,
                        "alpha2": alphaIon2,
                        "mask1": maskIon1,
                        "mask2": maskIon2,
                        "xvals": xaxisLabels,
                        "xlabels": xlabel,
                        "yvals": yaxisLabels,
                        "ylabels": ylabel,
                        "file1": compList[0],
                        "file2": compList[1],
                        "label1": compDict[compList[0]]["label"],
                        "label2": compDict[compList[1]]["label"],
                        "title": title,
                        "header": header,
                        "footnote": footnote,
                    }
                elif self.config.overlayMethod == "RMSF":
                    self.docs.IMS2DoverlayData[idName] = {
                        "yvalsRMSF": pRMSFlist,
                        "zvals": tempArray,
                        "xvals": xaxisLabels,
                        "yvals": yaxisLabels,
                        "ylabelRMSF": ylabelRMSF,
                        "xlabelRMSD": xLabel,
                        "ylabelRMSD": yLabel,
                        "rmsdLabel": rmsdLabel,
                        "colorRMSF": self.config.lineColour_1D,
                        "cmapRMSF": self.config.currentCmap,
                        "title": title,
                        "header": header,
                        "footnote": footnote,
                    }
                elif self.config.overlayMethod == "RMSD":
                    self.docs.IMS2DoverlayData[idName] = {
                        "zvals": tempArray,
                        "xvals": xaxisLabels,
                        "yvals": yaxisLabels,
                        "xlabel": xlabel,
                        "ylabel": ylabel,
                        "rmsdLabel": rmsdLabel,
                        "cmap": self.config.currentCmap,
                        "title": title,
                        "header": header,
                        "footnote": footnote,
                    }

        elif any(self.config.overlayMethod in method for method in ["Mean", "Standard Deviation", "Variance"]):
            meanData = []
            for row in range(tempAccumulator):
                key = compList[row]
                meanData.append(compDict[key]["zvals"])

            xAxisLabels = compDict[key]["xvals"]
            xlabel = compDict[key]["xlabels"]
            yAxisLabels = compDict[key]["yvals"]
            ylabel = compDict[key]["ylabels"]
            msg = "".join(["Computing ", self.config.textOverlayMethod, " for ", str(len(meanData)), " files."])
            self.onThreading(None, (msg, 4), action="updateStatusbar")
            if self.config.overlayMethod == "Mean":
                """ Computes mean of selected files """
                zvals = pr_activation.compute_mean(inputData=meanData)
            elif self.config.overlayMethod == "Standard Deviation":
                """ Computes standard deviation of selected files """
                zvals = pr_activation.compute_std_dev(inputData=meanData)
            elif self.config.overlayMethod == "Variance":
                """ Computes variance of selected files """
                zvals = pr_activation.compute_variance(inputData=meanData)
            # Plot
            self.view.panelPlots.on_plot_2D_data(
                data=[zvals, xAxisLabels, xlabel, yAxisLabels, ylabel, self.config.currentCmap]
            )
            self.view.panelPlots.mainBook.SetSelection(self.config.panelNames["2D"])
            if add_data_to_document:
                self.docs.gotStatsData = True
                # Check if exists. We need to extract labels (header...)
                checkExist = self.docs.IMS2DstatsData.get(self.config.overlayMethod, None)
                if checkExist is not None:
                    title = self.docs.IMS2DstatsData[self.config.overlayMethod].get("header", "")
                    header = self.docs.IMS2DstatsData[self.config.overlayMethod].get("header", "")
                    footnote = self.docs.IMS2DstatsData[self.config.overlayMethod].get("footnote", "")
                else:
                    title, header, footnote = "", "", ""

                # add label
                idName = "{}, {}".format(compList[0], compList[1])
                idName = "{}: {}".format(self.config.overlayMethod, idName)

                self.docs.IMS2DstatsData[idName] = {
                    "zvals": zvals,
                    "xvals": xAxisLabels,
                    "xlabels": xlabel,
                    "yvals": yAxisLabels,
                    "ylabels": ylabel,
                    "cmap": self.config.currentCmap,
                    "title": title,
                    "header": header,
                    "footnote": footnote,
                }
        elif self.config.overlayMethod == "RMSD Matrix":
            """ Compute RMSD matrix for selected files """
            zvals = np.zeros([tempAccumulator, tempAccumulator])
            tickLabels = []
            for row in range(tempAccumulator):
                key = compList[row]
                # Extract text labels from table
                tickLabels.append(compDict[key]["label"])
                # Compute pairwise RMSD
                for row2 in range(row + 1, tempAccumulator):
                    zvalsIon1plot = compDict[compList[row]]["zvals"]
                    zvalsIon2plot = compDict[compList[row2]]["zvals"]
                    pRMSD, tempArray = pr_activation.compute_RMSD(inputData1=zvalsIon1plot, inputData2=zvalsIon2plot)
                    zvals[row, row2] = np.round(pRMSD, 2)
            self.view.panelPlots.on_plot_matrix(zvals=zvals, xylabels=tickLabels, cmap=self.docs.colormap)
            self.view.panelPlots.mainBook.SetSelection(self.config.panelNames["Comparison"])
            if add_data_to_document:
                self.docs.gotStatsData = True
                # Check if exists. We need to extract labels (header...)
                checkExist = self.docs.IMS2DstatsData.get(self.config.overlayMethod, None)
                if checkExist is not None:
                    title = self.docs.IMS2DstatsData[self.config.overlayMethod].get("header", "")
                    header = self.docs.IMS2DstatsData[self.config.overlayMethod].get("header", "")
                    footnote = self.docs.IMS2DstatsData[self.config.overlayMethod].get("footnote", "")
                else:
                    title, header, footnote = "", "", ""
                self.docs.IMS2DstatsData[self.config.overlayMethod] = {
                    "zvals": zvals,
                    "cmap": self.config.currentCmap,
                    "matrixLabels": tickLabels,
                    "title": title,
                    "header": header,
                    "footnote": footnote,
                }

        elif self.config.overlayMethod == "RGB":
            data_list, idName = [], ""
            legend_text = []
            for row in range(tempAccumulator):
                key = compList[row]
                data = compDict[key]["zvals"]
                color = convertRGB255to1(compDict[key]["color"])
                min_threshold = compDict[key]["min_threshold"]
                max_threshold = compDict[key]["max_threshold"]
                label = compDict[key]["label"]
                if label == "":
                    label = compDict[key]["ion_name"]
                legend_text.append([color, label])

                # Change intensity
                data = pr_heatmap.adjust_min_max_intensity(data.copy(), min_threshold, max_threshold)
                # Convert to RGB
                rgb = make_rgb(data, color)
                data_list.append(rgb)
                # Add new label
                if idName == "":
                    idName = compList[row]
                else:
                    idName = "{}, {}".format(idName, compList[row])
            xAxisLabels = compDict[key]["xvals"]
            xlabel = compDict[key]["xlabels"]
            yAxisLabels = compDict[key]["yvals"]
            ylabel = compDict[key]["ylabels"]

            # Sum rgb list
            if len(data_list) >= 1:
                rgb_plot = combine_rgb(data_list)

                self.view.panelPlots.on_plot_rgb(rgb_plot, xAxisLabels, yAxisLabels, xlabel, ylabel, legend_text)
                self.view.panelPlots.mainBook.SetSelection(self.config.panelNames["2D"])

            # Add data to the dictionary (overlay data)
            if add_data_to_document:
                self.docs.gotOverlay = True
                # Add to the name to includ the method
                # Check if exists. We need to extract labels (header...)
                checkExist = self.docs.IMS2DoverlayData.get(idName, None)
                if checkExist is not None:
                    title = self.docs.IMS2DoverlayData[idName].get("header", "")
                    header = self.docs.IMS2DoverlayData[idName].get("header", "")
                    footnote = self.docs.IMS2DoverlayData[idName].get("footnote", "")
                else:
                    title, header, footnote = "", "", ""
                idName = "{}: {}".format(self.config.overlayMethod, idName)
                # remove unnecessary file extensions from filename
                if len(idName) > 511:
                    self.onThreading(None, ("Filename is too long. Reducing...", 4), action="updateStatusbar")
                    idName = idName.replace(".csv", "").replace(".txt", "").replace(".raw", "").replace(".d", "")
                    idName = idName[:500]

                self.docs.IMS2DoverlayData[idName] = {
                    "zvals": rgb_plot,
                    "xvals": xaxisLabels,
                    "xlabels": xlabel,
                    "yvals": yaxisLabels,
                    "ylabels": ylabel,
                    "rgb_list": data_list,
                    "legend_text": legend_text,
                    "title": title,
                    "header": header,
                    "footnote": footnote,
                }

        # Add data to document
        if add_data_to_document:
            self.docs.gotComparisonData = True
            self.docs.IMS2DcompData = compDict
            self.currentDoc = self.docs.title

            # Update file list
            self.OnUpdateDocument(self.docs, "comparison_data")
