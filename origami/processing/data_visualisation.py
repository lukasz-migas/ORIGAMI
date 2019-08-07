# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging

import numpy as np
import processing.activation as pr_activation
import processing.heatmap as pr_heatmap
import processing.spectra as pr_spectra
import wx
from numpy.ma.core import masked_array
from utils.color import combine_rgb
from utils.color import convertRGB255to1
from utils.color import make_rgb
from utils.exceptions import MessageError
from utils.visuals import calculate_label_position

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

        self.panelPlots = self.view.panelPlots

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

    def _check_overlay_count(self, item_list, n_min, n_max):

        # check number of items
        n_items = len(item_list)

        if n_min == -1:
            n_min = n_items
        if n_max == -1:
            n_max = n_items

        if n_items > n_max:
            raise MessageError(
                "Too many items in the list",
                f"There should be a maximum of {n_max} items in the list" + f" You've selected {n_items}.",
            )

        if n_items < n_min:
            raise MessageError(
                "Too few items in the list",
                f"There should only be a minimum of {n_min} items in the list." + f" You've selected {n_items}.",
            )

    def _check_overlay_shape(self, item_list, dimension=None):
        """Check whether input dataset has identical shape

        Parameters
        ----------
        item_list : list
            list of dictionaries with necessary metadata
        dimension : None or int
            dimension to be checked. If set to None, check entire shape, otherwise check either row or column

        Raises
        ------
        raises MessageError if more than one item found in the final shape list
        """
        # collect all shapes
        shape_list = []
        for item_info in item_list:
            shape = item_info["shape"]
            if dimension is not None:
                shape_split = shape.replace("(", "").replace(")", "").split(",")
                if len(shape_split) - 1 >= dimension:
                    shape = shape_split[dimension]
            shape_list.append(shape)

        # reduce to only include unique values
        shape = list(set(shape_list))

        # raise an error if incorrect shape
        if len(shape) > 1:
            raise MessageError(
                "Incorrect shape",
                "Your current selection has datasets that mismatch in shape. Please only select items"
                + f" that have identical size. Your selection sizes: {shape}",
            )

    def _check_overlay_html_tags(self):
        pass

    #         # Add data to the dictionary (overlay data)
    #         if add_data_to_document:
    #             self.docs.gotOverlay = True
    #             # add label
    #             idName = "{}, {}".format(compList[0], compList[1])
    #
    #             idName = "{}: {}".format(self.config.overlayMethod, idName)
    #             # Add to the name to includ the method
    #             # Check if exists. We need to extract labels (header...)
    #             checkExist = self.docs.IMS2DoverlayData.get(idName, None)
    #             if checkExist is not None:
    #                 title = self.docs.IMS2DoverlayData[idName].get("header", "")
    #                 header = self.docs.IMS2DoverlayData[idName].get("header", "")
    #                 footnote = self.docs.IMS2DoverlayData[idName].get("footnote", "")
    #             else:
    #                 title, header, footnote = "", "", ""

    def _generate_overlay_name(self, dataset_info, prepend=None):
        """Generate name for overlay object based on dataset info (eg. document_title, dataset_type and dataset_name

        Parameters
        ----------
        dataset_info : list
            list of lists containing document_title, dataset_type and dataset_name

        Returns
        -------
        dataset_name : str
            overlay item name
        """
        dataset_name = ""

        # first check whether it comes from the same document
        add_document_title = True
        document_list = []
        for item_info in dataset_info:
            document_list.append(item_info[0])

        document_list = list(set(document_list))
        if len(document_list) == 1:
            add_document_title = False

        for i, item_info in enumerate(dataset_info):
            item_name = f"{item_info[2]}"

            # add individual document title
            if add_document_title:
                item_name += f", {item_info[0]}"

            # add seperator
            if i > 0:
                dataset_name += "; "

            # append to name
            dataset_name += item_name

        # if document name was not incldued in each iteration, add it at the end
        if not add_document_title:
            dataset_name += f" :: {document_list[0]}"

        # add plot classifier to the filename
        if prepend is not None and isinstance(prepend, str):
            dataset_name = prepend + dataset_name

        # check length
        if len(dataset_name) > 511:
            logger.warning("Filename was too long. Reducing...")
            # replace unnecessary extensions
            dataset_name = dataset_name.replace(".csv", "").replace(".txt", "").replace(".raw", "").replace(".d", "")

            # check again, this time simply capping the name
            if len(dataset_name) > 511:
                dataset_name = dataset_name[:500]

        return dataset_name

    def on_overlay_spectrum_overlay(self, item_list, data_type, **kwargs):
        # TODO: Add checks for same labels

        if data_type not in ["mobilogram", "chromatogram", "mass_spectra"]:
            raise MessageError(
                "Incorrect data type",
                f"Incorrect data type of `{data_type}` was specified. Accepted values include"
                + "['mobilogram', 'chromatogram']",
            )

        # ensure shape is correct
        if data_type == "mobilogram":
            self._check_overlay_shape(item_list, 0)
        elif data_type == "chromatogram":
            self._check_overlay_shape(item_list, 1)
        elif data_type == "mass_spectra":
            self._check_overlay_shape(item_list, None)

        # ensure correct number of items is present
        self._check_overlay_count(item_list, n_min=2, n_max=-1)

        normalize_dataset = kwargs.get("normalize_dataset", False)

        # pre-generate empty lists
        xlist, ylist, colorlist, legend, dataset_info = [], [], [], [], []
        for item_info in item_list:
            # get data
            try:
                if data_type in ["mobilogram", "chromatogram"]:
                    query_info = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
                    __, data = self.data_handling.get_mobility_chromatographic_data(query_info)
                elif data_type == "mass_spectra":
                    query_info = [item_info["document"], item_info["dataset_name"]]
                    __, data = self.data_handling.get_spectrum_data(query_info)
            except KeyError:
                continue
            dataset_info.append([item_info["document"], item_info["dataset_type"], item_info["dataset_name"]])

            # get data
            if data_type == "mobilogram":
                xvals = data["yvals"]
                yvals = data.get("yvals1D", data["zvals"].sum(axis=1))
            elif data_type == "chromatogram":
                xvals = data["xvals"]
                yvals = data.get("yvalsRT", data["zvals"].sum(axis=0))
            elif data_type == "mass_spectra":
                xvals = data["xvals"]
                yvals = data["yvals"]

            # normalize data
            if normalize_dataset:
                yvals = pr_spectra.normalize_1D(yvals)

            # Append data to list
            xlist.append(xvals)
            ylist.append(yvals)
            colorlist.append(item_info["color_255to1"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append(label)

        xlimits = [min(xvals), max(xvals)]

        # plot
        if data_type == "mobilogram":
            xlabel = data["ylabels"]
            self.panelPlots.on_plot_overlay_DT(
                xvals=xlist, yvals=ylist, xlabel=xlabel, colors=colorlist, xlimits=xlimits, labels=legend, **kwargs
            )
            dataset_name = self._generate_overlay_name(dataset_info, "Overlay (DT): ")
        elif data_type == "chromatogram":
            xlabel = data["xlabels"]
            self.panelPlots.on_plot_overlay_RT(
                xvals=xlist, yvals=ylist, xlabel=xlabel, colors=colorlist, xlimits=xlimits, labels=legend, **kwargs
            )
            dataset_name = self._generate_overlay_name(dataset_info, "Overlay (RT): ")
        elif data_type == "mass_spectra":
            xlabel = data["xlabels"]
            self.panelPlots.on_plot_overlay_RT(
                xvals=xlist, yvals=ylist, xlabel=xlabel, colors=colorlist, xlimits=xlimits, labels=legend, **kwargs
            )
            dataset_name = self._generate_overlay_name(dataset_info, "Overlay (MS): ")

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "Overlay",
                "xvals": xlist,
                "yvals": ylist,
                "xlabel": xlabel,
                "colors": colorlist,
                "xlimits": xlimits,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }
        return dataset_holder

    def on_overlay_spectrum_butterfly(self, item_list, data_type, **kwargs):

        if data_type not in ["mobilogram", "chromatogram", "mass_spectra"]:
            raise MessageError(
                "Incorrect data type",
                f"Incorrect data type of `{data_type}` was specified. Accepted values include"
                + "['mobilogram', 'chromatogram']",
            )

        # ensure shape is correct
        if data_type == "mobilogram":
            self._check_overlay_shape(item_list, 0)
        elif data_type == "chromatogram":
            self._check_overlay_shape(item_list, 1)
        elif data_type == "mass_spectra":
            self._check_overlay_shape(item_list, None)

        # ensure correct number of items is present
        self._check_overlay_count(item_list, n_min=2, n_max=2)

        normalize_dataset = kwargs.get("normalize_dataset", False)

        # pre-generate empty lists
        xlist, ylist, colorlist, legend, dataset_info = [], [], [], [], []
        for item_info in item_list:
            try:
                if data_type in ["mobilogram", "chromatogram"]:
                    query_info = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
                    __, data = self.data_handling.get_mobility_chromatographic_data(query_info)
                elif data_type == "mass_spectra":
                    query_info = [item_info["document"], item_info["dataset_name"]]
                    __, data = self.data_handling.get_spectrum_data(query_info)
            except KeyError:
                continue
            dataset_info.append([item_info["document"], item_info["dataset_type"], item_info["dataset_name"]])

            # get data
            if data_type == "mobilogram":
                xvals = data["yvals"]
                yvals = data.get("yvals1D", data["zvals"].sum(axis=1))
            elif data_type == "chromatogram":
                xvals = data["xvals"]
                yvals = data.get("yvalsRT", data["zvals"].sum(axis=0))
            elif data_type == "mass_spectra":
                xvals = data["xvals"]
                yvals = data["yvals"]

            if normalize_dataset:
                yvals = pr_spectra.normalize_1D(yvals)

            # Append data to list
            xlist.append(xvals)
            ylist.append(yvals)
            colorlist.append(item_info["color_255to1"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append(label)

        # negate second item
        ylist[1] = -ylist[1]

        # plot
        if data_type == "mobilogram":
            xlabel = data["ylabels"]
            dataset_name = self._generate_overlay_name(dataset_info, "Butterfly (DT): ")
        elif data_type == "chromatogram":
            xlabel = data["xlabels"]
            dataset_name = self._generate_overlay_name(dataset_info, "Butterfly (RT): ")
        elif data_type == "mass_spectra":
            xlabel = data["xlabels"]
            dataset_name = self._generate_overlay_name(dataset_info, "Butterfly (MS): ")

        # plot
        self.panelPlots.plot_compare_spectra(
            xlist[0], xlist[1], ylist[0], ylist[1], xlabel=xlabel, legend=legend, **kwargs
        )

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "Butterfly",
                "xvals": xlist,
                "yvals": ylist,
                "xlabel": xlabel,
                "colors": colorlist,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }
        return dataset_holder

    def on_overlay_spectrum_subtract(self, item_list, data_type, **kwargs):

        if data_type not in ["mobilogram", "chromatogram", "mass_spectra"]:
            raise MessageError(
                "Incorrect data type",
                f"Incorrect data type of `{data_type}` was specified. Accepted values include"
                + "['mobilogram', 'chromatogram']",
            )

        # ensure shape is correct
        if data_type == "mobilogram":
            self._check_overlay_shape(item_list, 0)
        elif data_type == "chromatogram":
            self._check_overlay_shape(item_list, 1)
        elif data_type == "mass_spectra":
            self._check_overlay_shape(item_list, None)

        # ensure correct number of items is present
        self._check_overlay_count(item_list, n_min=2, n_max=2)

        normalize_dataset = kwargs.get("normalize_dataset", False)

        # pre-generate empty lists
        xlist, ylist, colorlist, legend, dataset_info = [], [], [], [], []
        for item_info in item_list:
            # get data
            try:
                if data_type in ["mobilogram", "chromatogram"]:
                    query_info = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
                    __, data = self.data_handling.get_mobility_chromatographic_data(query_info)
                elif data_type == "mass_spectra":
                    query_info = [item_info["document"], item_info["dataset_name"]]
                    __, data = self.data_handling.get_spectrum_data(query_info)
            except KeyError:
                continue
            dataset_info.append([item_info["document"], item_info["dataset_type"], item_info["dataset_name"]])

            # get data
            if data_type == "mobilogram":
                xvals = data["yvals"]
                yvals = data.get("yvals1D", data["zvals"].sum(axis=1))
            elif data_type == "chromatogram":
                xvals = data["xvals"]
                yvals = data.get("yvalsRT", data["zvals"].sum(axis=0))
            elif data_type == "mass_spectra":
                xvals = data["xvals"]
                yvals = data["yvals"]

            if normalize_dataset:
                yvals = pr_spectra.normalize_1D(yvals)

            # Append data to list
            xlist.append(xvals)
            ylist.append(yvals)
            colorlist.append(item_info["color_255to1"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append(label)

        # unpack and process
        xvals_1, yvals_1, xvals_2, yvals_2 = xlist[0], ylist[0], xlist[1], ylist[1]
        xvals_1, yvals_1, xvals_2, yvals_2 = self.data_processing.subtract_spectra(xvals_1, yvals_1, xvals_2, yvals_2)

        # plot
        if data_type == "mobilogram":
            xlabel = data["ylabels"]
            dataset_name = self._generate_overlay_name(dataset_info, "Butterfly (DT): ")
        elif data_type == "chromatogram":
            xlabel = data["xlabels"]
            dataset_name = self._generate_overlay_name(dataset_info, "Butterfly (RT): ")
        elif data_type == "mass_spectra":
            xlabel = data["xlabels"]
            dataset_name = self._generate_overlay_name(dataset_info, "Butterfly (MS): ")

        # plot
        self.panelPlots.plot_compare_spectra(
            xvals_1,
            xvals_2,
            yvals_1,
            yvals_2,
            xlabel=xlabel,
            legend=legend,
            line_color_1=colorlist[0],
            line_color_2=colorlist[1],
            **kwargs,
        )

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "Butterfly",
                "xvals": xlist,
                "yvals": ylist,
                "xlabel": xlabel,
                "colors": colorlist,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }
        return dataset_holder

    def on_overlay_spectrum_waterfall(self, item_list, data_type, **kwargs):

        if data_type not in ["mobilogram", "chromatogram", "mass_spectra"]:
            raise MessageError(
                "Incorrect data type",
                f"Incorrect data type of `{data_type}` was specified. Accepted values include"
                + "['mobilogram', 'chromatogram']",
            )

        # ensure shape is correct
        if data_type == "mobilogram":
            self._check_overlay_shape(item_list, 0)
        elif data_type == "chromatogram":
            self._check_overlay_shape(item_list, 1)
        elif data_type == "mass_spectra":
            self._check_overlay_shape(item_list, None)

        # ensure correct number of items is present
        self._check_overlay_count(item_list, n_min=2, n_max=-1)

        normalize_dataset = kwargs.pop("normalize_dataset", False)

        # pre-generate empty lists
        xlist, ylist, colorlist, legend, dataset_info = [], [], [], [], []
        for item_info in item_list:
            # get data
            try:
                if data_type in ["mobilogram", "chromatogram"]:
                    query_info = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
                    __, data = self.data_handling.get_mobility_chromatographic_data(query_info)
                elif data_type == "mass_spectra":
                    query_info = [item_info["document"], item_info["dataset_name"]]
                    __, data = self.data_handling.get_spectrum_data(query_info)
            except KeyError:
                continue
            dataset_info.append([item_info["document"], item_info["dataset_type"], item_info["dataset_name"]])

            # get data
            if data_type == "mobilogram":
                xvals = data["yvals"]
                yvals = data.get("yvals1D", data["zvals"].sum(axis=1))
            elif data_type == "chromatogram":
                xvals = data["xvals"]
                yvals = data.get("yvalsRT", data["zvals"].sum(axis=0))
            elif data_type == "mass_spectra":
                xvals = data["xvals"]
                yvals = data["yvals"]

            if normalize_dataset:
                yvals = pr_spectra.normalize_1D(yvals)

            # Append data to list
            xlist.append(xvals)
            ylist.append(yvals)
            colorlist.append(item_info["color_255to1"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append(label)

        # plot
        if data_type == "mobilogram":
            xlabel = data["ylabels"]
            dataset_name = self._generate_overlay_name(dataset_info, "Waterfall (DT): ")
        elif data_type == "chromatogram":
            xlabel = data["xlabels"]
            dataset_name = self._generate_overlay_name(dataset_info, "Waterfall (RT): ")
        elif data_type == "mass_spectra":
            xlabel = data["xlabels"]
            dataset_name = self._generate_overlay_name(dataset_info, "Waterfall (MS): ")

        # plot
        kwargs.update(show_y_labels=True, labels=legend, add_legend=True)
        self.panelPlots.on_plot_waterfall(
            xlist, ylist, None, colors=colorlist, xlabel=xlabel, ylabel="Intensity", **kwargs
        )

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "Butterfly",
                "xvals": xlist,
                "yvals": ylist,
                "xlabel": xlabel,
                "colors": colorlist,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }
        return dataset_holder

    def on_overlay_heatmap_waterfall(self, item_list, **kwargs):
        pass

    #         rows = self.peaklist.GetItemCount()
    #
    #         # Iterate over row and columns to get data
    #         xvals, yvals, zvals, colors, labels = [], [], [], [], []
    #         item_name = "Waterfall overlay:"
    #         for row in range(rows):
    #             if not self.peaklist.IsChecked(index=row):
    #                 continue
    #
    #             itemInfo = self.OnGetItemInformation(row)
    #             try:
    #                 ion_title = itemInfo["document"]
    #                 document = self.presenter.documentsDict[ion_title]
    #
    #                 # get data
    #                 data = document.IMS2D
    #             except Exception:
    #                 document_title, ion_title = re.split(": ", itemInfo["document"])
    #                 document = self.presenter.documentsDict[document_title]
    #                 try:
    #                     data = document.IMS2DcompData[ion_title]
    #                 except KeyError:
    #                     try:
    #                         data = document.IMS2Dions[ion_title]
    #                     except Exception:
    #                         data = None
    #
    #             if data is None:
    #                 continue
    #
    #             xvals.append(deepcopy(data["yvals"]))
    #             yvals.append(deepcopy(data["xvals"]))
    #             zvals.append(deepcopy(data["zvals"]))
    #             colors.append(convertRGB255to1(itemInfo["color"]))
    #             labels.append(itemInfo["label"])
    #
    #             if self.addToDocument:
    #                 if itemInfo["label"] != "":
    #                     item_label = itemInfo["label"]
    #                 else:
    #                     item_label = ion_title
    #
    #                 if len(xvals) == 1:
    #                     item_name = "{} {}".format(item_name, item_label)
    #                 else:
    #                     item_name = "{}, {}".format(item_name, item_label)
    #
    #         if len(xvals) > 0:
    #             xlabel = data["xlabels"]
    #             ylabel = data["ylabels"]
    #             self.presenter.view.panelPlots.on_plot_waterfall_overlay(
    #                 xvals, yvals, zvals, colors, xlabel, ylabel, labels
    #             )
    #             self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames["Waterfall"])
    #
    #         # add data to document
    #         if self.addToDocument:
    #             _document = self.onGetOverlayDocument()
    #             checkExist = _document.IMS2DoverlayData.get(item_name, None)
    #             data = {
    #                 "xvals": xvals,
    #                 "yvals": yvals,
    #                 "zvals": zvals,
    #                 "colors": colors,
    #                 "xlabel": xlabel,
    #                 "ylabel": ylabel,
    #                 "labels": labels,
    #             }
    #             if checkExist is not None:
    #                 # retrieve and merge
    #                 old_data = document.IMS2DoverlayData.get(item_name, {})
    #                 data = merge_two_dicts(old_data, data)
    #             else:
    #                 data.update(title="", header="", footnote="")
    #
    #             _document.gotOverlay = True
    #             _document.IMS2DoverlayData[item_name] = data
    #
    #             self.data_handling.on_update_document(_document, "document")

    def on_overlay_heatmap_mask(self, item_list, **kwargs):

        # ensure correct number of items is present
        self._check_overlay_count(item_list, n_min=2, n_max=2)

        # ensure shape is correct
        self._check_overlay_shape(item_list, None)

        # pre-generate empty lists
        zlist, xlist, ylist, cmaplist, dataset_info, masklist, legend = [], [], [], [], [], [], []
        for item_info in item_list:
            # get data
            try:
                query_info = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
                __, data = self.data_handling.get_mobility_chromatographic_data(query_info)
            except KeyError:
                continue

            dataset_info.append(query_info)
            zlist.append(data["zvals"])
            cmaplist.append(item_info["colormap"])
            masklist.append(item_info["mask"])
            xlist.append(data["xvals"])
            ylist.append(data["yvals"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append(label)

        # get labels
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]
        xvals = data["xvals"]
        yvals = data["yvals"]

        # generate masked arrays
        zvals_1 = masked_array(zlist[0], zlist[0] < masklist[0])
        zvals_2 = masked_array(zlist[1], zlist[1] < masklist[1])

        self.panelPlots.on_plot_overlay_2D(
            zvalsIon1=zvals_1,
            cmapIon1=cmaplist[0],
            alphaIon1=1,
            zvalsIon2=zvals_2,
            cmapIon2=cmaplist[1],
            alphaIon2=1,
            xvals=xvals,
            yvals=yvals,
            xlabel=xlabel,
            ylabel=ylabel,
            plotName="Mask",
            **kwargs,
        )

        # generate item name
        dataset_name = self._generate_overlay_name(dataset_info, "Mask: ")

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "Mask",
                "xlist": xlist,
                "ylist": ylist,
                "zlist": zlist,
                "xvals": xvals,
                "yvals": yvals,
                "xlabel": xlabel,
                "ylabel": ylabel,
                "cmaps": cmaplist,
                "masks": masklist,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }
        return dataset_holder

    def on_overlay_heatmap_transparent(self, item_list, **kwargs):

        # ensure correct number of items is present
        self._check_overlay_count(item_list, n_min=2, n_max=2)

        # ensure shape is correct
        self._check_overlay_shape(item_list, None)

        # pre-generate empty lists
        zlist, xlist, ylist, cmaplist, dataset_info, alphalist, legend = [], [], [], [], [], [], []
        for item_info in item_list:
            # get data
            try:
                query_info = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
                __, data = self.data_handling.get_mobility_chromatographic_data(query_info)
            except KeyError:
                continue

            dataset_info.append(query_info)
            zlist.append(data["zvals"])
            cmaplist.append(item_info["colormap"])
            alphalist.append(item_info["alpha"])
            xlist.append(data["xvals"])
            ylist.append(data["yvals"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append(label)

        # get labels
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]
        xvals = data["xvals"]
        yvals = data["yvals"]

        # generate masked arrays
        zvals_1 = zlist[0]
        zvals_2 = zlist[1]

        self.panelPlots.on_plot_overlay_2D(
            zvalsIon1=zvals_1,
            cmapIon1=cmaplist[0],
            alphaIon1=alphalist[0],
            zvalsIon2=zvals_2,
            cmapIon2=cmaplist[1],
            alphaIon2=alphalist[1],
            xvals=xvals,
            yvals=yvals,
            xlabel=xlabel,
            ylabel=ylabel,
            plotName="Mask",
            **kwargs,
        )

        # generate item name
        dataset_name = self._generate_overlay_name(dataset_info, "Transparent: ")

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "Transparent",
                "xlist": xlist,
                "ylist": ylist,
                "zlist": zlist,
                "xvals": xvals,
                "yvals": yvals,
                "xlabel": xlabel,
                "ylabel": ylabel,
                "cmaps": cmaplist,
                "alphas": alphalist,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }
        return dataset_holder

    #     def on_overlay_1D(self, source, plot_type):
    #         """
    #         This function enables overlaying of multiple ions together - 1D and RT
    #         """
    #         # Check what is the ID
    #         if source == "ion":
    #             tempList = self.ionList
    #             add_data_to_document = self.view.panelMultipleIons.addToDocument
    #             normalize_dataset = self.view.panelMultipleIons.normalize1D
    #         elif source == "text":
    #             tempList = self.textList
    #             add_data_to_document = self.view.panelMultipleText.addToDocument
    #             normalize_dataset = self.view.panelMultipleText.normalize1D
    #
    #         if add_data_to_document:
    #             document = self._get_document_of_type("Type: Comparison")
    #             document_title = document.title
    #
    #         # Empty lists
    #         xlist, ylist, colorlist, legend = [], [], [], []
    #         idName = ""
    #         # Get data for the dataset
    #         for row in range(tempList.GetItemCount()):
    #             if tempList.IsChecked(index=row):
    #                 if source == "ion":
    #                     # Get current document
    #                     itemInfo = self.ionPanel.OnGetItemInformation(itemID=row)
    #                     document_title = itemInfo["document"]
    #                     # Check that data was extracted first
    #                     if document_title == "":
    #                         continue
    #
    #                     document = self.data_handling._on_get_document(document_title)
    #                     dataType = document.dataType
    #                     selectedItem = itemInfo["ionName"]
    #                     label = itemInfo["label"]
    #                     color = convertRGB255to1(itemInfo["color"])
    #                     itemName = "ion={} ({})".format(selectedItem, document_title)
    #
    #                     # ORIGAMI dataset
    #                     if dataType == "Type: ORIGAMI" and document.gotCombinedExtractedIons:
    #                         try:
    #                             data = document.IMS2DCombIons[selectedItem]
    #                         except KeyError:
    #                             try:
    #                                 data = document.IMS2Dions[selectedItem]
    #                             except KeyError:
    #                                 continue
    #                     elif dataType == "Type: ORIGAMI" and not document.gotCombinedExtractedIons:
    #                         try:
    #                             data = document.IMS2Dions[selectedItem]
    #                         except KeyError:
    #                             continue
    #
    #                     # MANUAL dataset
    #                     if dataType == "Type: MANUAL" and document.gotCombinedExtractedIons:
    #                         try:
    #                             data = document.IMS2DCombIons[selectedItem]
    #                         except KeyError:
    #                             try:
    #                                 data = document.IMS2Dions[selectedItem]
    #                             except KeyError:
    #                                 continue
    #
    #                     # Add new label
    #                     if idName == "":
    #                         idName = itemName
    #                     else:
    #                         idName = "{}, {}".format(idName, itemName)
    #
    #                     # Add depending which event was triggered
    #                     if plot_type == "mobiligram":
    #                         xvals = data["yvals"]  # normally this would be the y-axis
    #                         yvals = data["yvals1D"]
    #                         if normalize_dataset:
    #                             yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
    #                             yvals = pr_spectra.normalize_1D(yvals)
    #                         xlabels = data["ylabels"]  # data was rotated so using ylabel for xlabel
    #
    #                     elif plot_type == "chromatogram":
    #                         xvals = data["xvals"]
    #                         yvals = data["yvalsRT"]
    #                         if normalize_dataset:
    #                             yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
    #                             yvals = pr_spectra.normalize_1D(yvals)
    #                         xlabels = data["xlabels"]
    #
    #                     # Append data to list
    #                     xlist.append(xvals)
    #                     ylist.append(yvals)
    #                     colorlist.append(color)
    #                     if label == "":
    #                         label = selectedItem
    #                     legend.append(label)
    #                 elif source == "text":
    #                     itemInfo = self.textPanel.OnGetItemInformation(itemID=row)
    #                     document_title = itemInfo["document"]
    #                     label = itemInfo["label"]
    #                     color = itemInfo["color"]
    #                     color = convertRGB255to1(itemInfo["color"])
    #                     # get document
    #                     try:
    #                         document = self.data_handling._on_get_document(document_title)
    #                         comparison_flag = False
    #                         selectedItem = document_title
    #                         itemName = "file={}".format(document_title)
    #                     except Exception as __:
    #                         comparison_flag = True
    #                         document_title, ion_name = re.split(": ", document_title)
    #                         document = self.data_handling._on_get_document(document_title)
    #                         selectedItem = ion_name
    #                         itemName = "file={}".format(ion_name)
    #
    #                     # Text dataset
    #                     if comparison_flag:
    #                         try:
    #                             data = document.IMS2DcompData[ion_name]
    #                         except Exception:
    #                             data = document.IMS2Dions[ion_name]
    #                     else:
    #                         try:
    #                             data = document.IMS2D
    #                         except Exception:
    #                             logger.error("No data for selected file")
    #                             continue
    #
    #                     # Add new label
    #                     if idName == "":
    #                         idName = itemName
    #                     else:
    #                         idName = "{}, {}".format(idName, itemName)
    #
    #                     # Add depending which event was triggered
    #                     if plot_type == "mobiligram":
    #                         xvals = data["yvals"]  # normally this would be the y-axis
    #                         try:
    #                             yvals = data["yvals1D"]
    #                         except KeyError:
    #                             yvals = np.sum(data["zvals"], axis=1).T
    #                         if normalize_dataset:
    #                             yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
    #                             yvals = pr_spectra.normalize_1D(yvals)
    #                         xlabels = data["ylabels"]  # data was rotated so using ylabel for xlabel
    #
    #                     elif plot_type == "chromatogram":
    #                         xvals = data["xvals"][:-1]  # TEMPORARY FIX
    #                         try:
    #                             yvals = data["yvalsRT"]
    #                         except KeyError:
    #                             yvals = np.sum(data["zvals"], axis=0)
    #                         if normalize_dataset:
    #                             yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
    #                             yvals = pr_spectra.normalize_1D(yvals)
    #                         xlabels = data["xlabels"]
    #
    #                     # Append data to list
    #                     xlist.append(xvals)
    #                     ylist.append(yvals)
    #                     colorlist.append(color)
    #                     if label == "":
    #                         label = selectedItem
    #                     legend.append(label)
    #
    #         # Modify the name to include ion tags
    #         if plot_type == "mobiligram":
    #             idName = "1D: %s" % idName
    #         elif plot_type == "chromatogram":
    #             idName = "RT: %s" % idName
    #
    #         # remove unnecessary file extensions from filename
    #         if len(idName) > 511:
    #             logger.warning("Filename was too long. Reducing...")
    #             idName = idName.replace(".csv", "").replace(".txt", "").replace(".raw", "").replace(".d", "")
    #             idName = idName[:500]
    #
    #         # Determine x-axis limits for the zoom function
    #         try:
    #             xlimits = [min(xvals), max(xvals)]
    #         except UnboundLocalError:
    #             logger.error("Please select at least one item in the table")
    #             return
    #
    #         # Add data to dictionary
    #         if add_data_to_document:
    #             document = self._get_document_of_type("Type: Comparison")
    #             document.gotOverlay = True
    #             document.IMS2DoverlayData[idName] = {
    #                 "xvals": xlist,
    #                 "yvals": ylist,
    #                 "xlabel": xlabels,
    #                 "colors": colorlist,
    #                 "xlimits": xlimits,
    #                 "labels": legend,
    #             }
    #             document_title = document.title
    #             self.data_handling.on_update_document(document, "comparison_data")
    #
    #         # Plot
    #         if plot_type == "mobiligram":
    #             self.panelPlots.on_plot_overlay_DT(
    #                 xvals=xlist,
    #                 yvals=ylist,
    #                 xlabel=xlabels,
    #                 colors=colorlist,
    #                 xlimits=xlimits,
    #                 labels=legend,
    #                 set_page=True,
    #             )
    #         elif plot_type == "chromatogram":
    #             self.panelPlots.on_plot_overlay_RT(
    #                 xvals=xlist,
    #                 yvals=ylist,
    #                 xlabel=xlabels,
    #                 colors=colorlist,
    #                 xlimits=xlimits,
    #                 labels=legend,
    #                 set_page=True,
    #             )

    def on_overlay_heatmap_rmsd(self, item_list, **kwargs):
        # TODO: Add ability to select subset of the dataset to calculate smaller ROI
        # TODO: Add ability to disable normalization by default

        # ensure correct number of items is present
        self._check_overlay_count(item_list, n_min=2, n_max=2)

        # ensure shape is correct
        self._check_overlay_shape(item_list, None)

        # pre-generate empty lists
        zlist, xlist, ylist, dataset_info, legend = [], [], [], [], []
        for item_info in item_list:
            # get data
            try:
                query_info = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
                __, data = self.data_handling.get_mobility_chromatographic_data(query_info)
            except KeyError:
                continue

            dataset_info.append(query_info)
            zlist.append(data["zvals"])
            xlist.append(data["xvals"])
            ylist.append(data["yvals"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append(label)

        # get labels
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]
        xvals = data["xvals"]
        yvals = data["yvals"]

        #         # Check whether we should be restricting the RMSD range
        #         if self.config.restrictXYrangeRMSD:
        #             zvalsIon1plot, xvals, yvals = self.restrictRMSDrange(
        #                 zvalsIon1plot, xaxisLabels, yaxisLabels, self.config.xyLimitsRMSD
        #             )
        #
        #             zvalsIon2plot, xvals, yvals = self.restrictRMSDrange(
        #                 zvalsIon2plot, xaxisLabels, yaxisLabels, self.config.xyLimitsRMSD
        #             )
        #             xaxisLabels, yaxisLabels = xvals, yvals
        #
        # calculate RMSD
        pRMSD, zvals = pr_activation.compute_RMSD(zlist[0], zlist[1])
        rmsd_label = f"RMSD: {pRMSD:.2f}"
        #
        #         self.setXYlimitsRMSD2D(xaxisLabels, yaxisLabels)
        #
        # plot
        cmap = self.config.currentCmap
        self.panelPlots.on_plot_RMSD(zvals, xvals, yvals, xlabel, ylabel, cmap, plotType="RMSD", **kwargs)

        # add label
        label_x_pos, label_y_pos = calculate_label_position(xvals, yvals, self.config.rmsd_location)
        if None not in [label_x_pos, label_y_pos]:
            self.panelPlots.on_add_label(label_x_pos, label_y_pos, rmsd_label, 0, **kwargs)

        # generate item name
        dataset_name = self._generate_overlay_name(dataset_info, "RMSD: ")

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "Transparent",
                "xlist": xlist,
                "ylist": ylist,
                "zlist": zlist,
                "xvals": xvals,
                "yvals": yvals,
                "zvals": zvals,
                "xlabel": xlabel,
                "ylabel": ylabel,
                "rmsdLabel": rmsd_label,
                "rmsd_location": [label_x_pos, label_y_pos],
                "cmap": cmap,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }
        return dataset_holder

    def on_overlay_heatmap_rmsf(self, item_list, **kwargs):
        # ensure correct number of items is present
        self._check_overlay_count(item_list, n_min=2, n_max=2)

        # ensure shape is correct
        self._check_overlay_shape(item_list, None)

        # pre-generate empty lists
        zlist, xlist, ylist, dataset_info, legend = [], [], [], [], []
        for item_info in item_list:
            # get data
            try:
                query_info = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
                __, data = self.data_handling.get_mobility_chromatographic_data(query_info)
            except KeyError:
                continue

            dataset_info.append(query_info)
            zlist.append(data["zvals"])
            xlist.append(data["xvals"])
            ylist.append(data["yvals"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append(label)

        # get labels
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]
        xvals = data["xvals"]
        yvals = data["yvals"]

        # calculate RMSD
        pRMSD, zvals = pr_activation.compute_RMSD(zlist[0], zlist[1])
        rmsd_label = f"RMSD: {pRMSD:.2f}"

        # calculate RMSF
        pRMSF_list = pr_activation.compute_RMSF(zlist[0], zlist[1])
        pRMSF_list = pr_heatmap.smooth_gaussian_2D(pRMSF_list, sigma=1)

        # plot
        cmap = self.config.currentCmap
        self.panelPlots.on_plot_RMSDF(
            yvalsRMSF=pRMSF_list,
            zvals=zvals,
            xvals=xvals,
            yvals=yvals,
            xlabelRMSD=xlabel,
            ylabelRMSD=ylabel,
            ylabelRMSF="RMSD (%)",
            color=self.config.lineColour_1D,
            cmap=cmap,
            **kwargs,
        )

        # add label
        label_x_pos, label_y_pos = calculate_label_position(xvals, yvals, self.config.rmsd_location)
        if None not in [label_x_pos, label_y_pos]:
            self.panelPlots.on_add_label(label_x_pos, label_y_pos, rmsd_label, 0, **kwargs)

        # generate item name
        dataset_name = self._generate_overlay_name(dataset_info, "RMSD: ")

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "Transparent",
                "xlist": xlist,
                "ylist": ylist,
                "zlist": zlist,
                "xvals": xvals,
                "yvals": yvals,
                "zvals": zvals,
                "yvalsRMSF": pRMSF_list,
                "xlabel": xlabel,
                "xlabelRMSD": xlabel,
                "ylabelRMSD": ylabel,
                "ylabelRMSF": "RMSD (%)",
                "ylabel": ylabel,
                "rmsdLabel": rmsd_label,
                "rmsd_location": [label_x_pos, label_y_pos],
                "cmap": cmap,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }
        return dataset_holder

    def on_overlay_heatmap_2to1(self, item_list, **kwargs):
        # ensure correct number of items is present
        self._check_overlay_count(item_list, n_min=2, n_max=2)

        # ensure shape is correct
        self._check_overlay_shape(item_list, None)

        # pre-generate empty lists
        zlist, xlist, ylist, dataset_info, legend, cmaplist = [], [], [], [], [], []
        for item_info in item_list:
            # get data
            try:
                query_info = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
                __, data = self.data_handling.get_mobility_chromatographic_data(query_info)
            except KeyError:
                continue

            dataset_info.append(query_info)
            zlist.append(data["zvals"])
            xlist.append(data["xvals"])
            ylist.append(data["yvals"])
            cmaplist.append(item_info["colormap"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append(label)

        # get labels
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]
        xvals = data["xvals"]
        yvals = data["yvals"]

        # calculate RMSD
        pRMSD, zvals = pr_activation.compute_RMSD(zlist[0], zlist[1])
        rmsd_label = f"RMSD: {pRMSD:.2f}"

        self.panelPlots.on_plot_grid(
            zlist[0], zlist[1], zvals, xvals, yvals, xlabel, ylabel, cmaplist[0], cmaplist[1], **kwargs
        )

        # add label
        label_x_pos, label_y_pos = calculate_label_position(xvals, yvals, self.config.rmsd_location)
        if None not in [label_x_pos, label_y_pos]:
            self.panelPlots.on_add_label(
                label_x_pos, label_y_pos, rmsd_label, 0, plot="Grid", plot_obj=kwargs.pop("plot_obj")
            )

        # generate item name
        dataset_name = self._generate_overlay_name(dataset_info, "Grid (2->1): ")

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "Transparent",
                "xlist": xlist,
                "ylist": ylist,
                "zlist": zlist,
                "xvals": xvals,
                "yvals": yvals,
                "zvals": zvals,
                "xlabel": xlabel,
                "ylabel": ylabel,
                "rmsdLabel": rmsd_label,
                "rmsd_location": [label_x_pos, label_y_pos],
                "cmap": self.config.currentCmap,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }
        return dataset_holder

    def on_overlay_heatmap_grid_nxn(self, item_list, **kwargs):
        # ensure correct number of items is present
        self._check_overlay_count(item_list, n_min=2, n_max=25)

        # ensure shape is correct
        self._check_overlay_shape(item_list, None)

        # pre-generate empty lists
        zlist, xlist, ylist, cmaplist, dataset_info, legend = [], [], [], [], [], []
        for item_info in item_list:
            # get data
            try:
                query_info = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
                __, data = self.data_handling.get_mobility_chromatographic_data(query_info)
            except KeyError:
                continue

            dataset_info.append(query_info)
            zlist.append(data["zvals"])
            cmaplist.append(item_info["colormap"])
            xlist.append(data["xvals"])
            ylist.append(data["yvals"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append(label)

        # get labels
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]

        self.panelPlots.on_plot_n_grid(zlist, cmaplist, legend, xlist, ylist, xlabel, ylabel, **kwargs)

        # generate item name
        dataset_name = self._generate_overlay_name(dataset_info, prepend="Grid (n x n): ")

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "RGB",
                "xlist": xlist,
                "ylist": ylist,
                "zlist": zlist,
                "xlabel": xlabel,
                "ylabel": ylabel,
                "cmaps": cmaplist,
                "legend_text": legend,
                "dataset_info": dataset_info,
            },
        }
        return dataset_holder

    def on_overlay_heatmap_rgb(self, item_list, **kwargs):
        # TODO: add possibility to adjust R, G, B channels normalization  to bring out details

        # ensure correct number of items is present
        self._check_overlay_count(item_list, n_min=2, n_max=-1)

        # ensure shape is correct
        self._check_overlay_shape(item_list, None)

        # pre-generate empty lists
        zlist, xlist, ylist, colorlist, dataset_info, legend = [], [], [], [], [], []
        for item_info in item_list:
            # get data
            try:
                query_info = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
                __, data = self.data_handling.get_mobility_chromatographic_data(query_info)
            except KeyError:
                continue
            dataset_info.append(query_info)

            zvals = data["zvals"].copy()
            color = convertRGB255to1(item_info["color"])
            min_threshold = item_info["min_threshold"]
            max_threshold = item_info["max_threshold"]

            zvals = pr_heatmap.adjust_min_max_intensity(zvals, min_threshold, max_threshold)

            # convert to rgb plot
            rgb = make_rgb(zvals, color, add_alpha=True)

            zlist.append(rgb)
            colorlist.append(item_info["color"])
            xlist.append(data["xvals"])
            ylist.append(data["yvals"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append([color, label])

        # get labels
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]
        xvals = data["xvals"]
        yvals = data["yvals"]

        rgb_plot = combine_rgb(zlist)

        self.panelPlots.on_plot_rgb(rgb_plot, xvals, yvals, xlabel, ylabel, legend, **kwargs)

        # generate item name
        dataset_name = self._generate_overlay_name(dataset_info, prepend="RGB: ")

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "RGB",
                "xlist": xlist,
                "ylist": ylist,
                "zlist": zlist,
                "xvals": xvals,
                "yvals": yvals,
                "zvals": rgb_plot,
                "xlabel": xlabel,
                "ylabel": ylabel,
                "colors": colorlist,
                "legend_text": legend,
                "dataset_info": dataset_info,
            },
        }
        return dataset_holder

    def on_overlay_heatmap_rmsd_matrix(self, item_list, **kwargs):
        # TODO: Add ability to better controls font details
        # TODO: Add ability to control colormap

        # ensure correct number of items is present
        self._check_overlay_count(item_list, n_min=2, n_max=-1)

        # ensure shape is correct
        self._check_overlay_shape(item_list, None)

        # pre-generate empty lists
        zlist, xlist, ylist, cmaplist, dataset_info, legend = [], [], [], [], [], []
        for item_info in item_list:
            # get data
            try:
                query_info = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
                __, data = self.data_handling.get_mobility_chromatographic_data(query_info)
            except KeyError:
                continue

            dataset_info.append(query_info)
            zlist.append(data["zvals"])
            cmaplist.append(item_info["colormap"])
            xlist.append(data["xvals"])
            ylist.append(data["yvals"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append(label)

        # compute RMSD for each heatmap
        n_items = len(zlist)
        zvals = np.zeros((n_items, n_items))
        for i in range(n_items):
            for j in range(i + 1, n_items):
                pRMSD, __ = pr_activation.compute_RMSD(zlist[i], zlist[j])
                zvals[i, j] = np.round(pRMSD, 2)

        # plot
        cmap = self.config.currentCmap
        self.panelPlots.on_plot_matrix(zvals=zvals, xylabels=legend, cmap=cmap, **kwargs)

        # generate item name
        dataset_name = self._generate_overlay_name(dataset_info, prepend="RMSD Matrix: ")

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "RMSD Matrix",
                "xlist": xlist,
                "ylist": ylist,
                "zlist": zlist,
                "zvals": zvals,
                "cmap": cmap,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }
        return dataset_holder

    def on_overlay_heatmap_statistical(self, item_list, method, **kwargs):

        # ensure correct number of items is present
        self._check_overlay_count(item_list, n_min=2, n_max=-1)

        # ensure shape is correct
        self._check_overlay_shape(item_list, None)

        # pre-generate empty lists
        zlist, xlist, ylist, cmaplist, dataset_info, legend = [], [], [], [], [], []
        for item_info in item_list:
            # get data
            try:
                query_info = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
                __, data = self.data_handling.get_mobility_chromatographic_data(query_info)
            except KeyError:
                continue

            dataset_info.append(query_info)
            zlist.append(data["zvals"])
            cmaplist.append(item_info["colormap"])
            xlist.append(data["xvals"])
            ylist.append(data["yvals"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append(label)

        # calculate statistical array
        if method == "Mean":
            zvals = pr_activation.compute_mean(zlist)
        elif method == "Standard Deviation":
            zvals = pr_activation.compute_std_dev(zlist)
        elif method == "Variance":
            zvals = pr_activation.compute_variance(zlist)

        # get labels
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]
        xvals = data["xvals"]
        yvals = data["yvals"]
        cmap = self.config.currentCmap

        self.panelPlots.on_plot_2D_data(data=[zvals, xvals, xlabel, yvals, ylabel, cmap], **kwargs)

        # generate item name
        dataset_name = self._generate_overlay_name(dataset_info)

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": method,
                "xlist": xlist,
                "ylist": ylist,
                "zlist": zlist,
                "xvals": xvals,
                "yvals": yvals,
                "zvals": zvals,
                "xlabel": xlabel,
                "ylabel": ylabel,
                "cmap": cmap,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }
        return dataset_holder


#     def on_overlay_2D(self, source):
#         """
#         This function enables overlaying multiple ions from the same CIU datasets together
#         """
#         # Check what is the ID
#         if source == "ion":
#             tempList = self.view.panelMultipleIons.peaklist
#             col_order = self.config.peaklistColNames
#             add_data_to_document = self.view.panelMultipleIons.addToDocument
#             self.config.overlayMethod = self.view.panelMultipleIons.combo.GetStringSelection()
#         elif source == "text":
#             tempList = self.view.panelMultipleText.peaklist
#             col_order = self.config.textlistColNames
#             add_data_to_document = self.view.panelMultipleText.addToDocument
#             self.config.overlayMethod = self.view.panelMultipleText.combo.GetStringSelection()
#
#         tempAccumulator = 0  # Keeps count of how many items are ticked
#         try:
#             self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
#         except Exception:
#             return
#         if self.currentDoc == "Documents":
#             return
#
#         # Check if current document is a comparison document
#         # If so, it will be used
#         if add_data_to_document:
#             if self.documentsDict[self.currentDoc].dataType == "Type: Comparison":
#                 self.docs = self.documentsDict[self.currentDoc]
#                 self.onThreading(
#                     None, ("Using document: " + self.docs.title.encode("ascii", "replace"), 4), action="updateStatusbar"
#                 )
#                 if self.docs.gotComparisonData:
#                     compDict = self.docs.IMS2DcompData
#                     compList = []
#                     for key in self.docs.IMS2DcompData:
#                         compList.append(key)
#                 else:
#                     compDict, compList = {}, []
#             else:
#                 self.onThreading(None, ("Checking if there is a comparison document", 4), action="updateStatusbar")
#                 docList = self.checkIfAnyDocumentsAreOfType(type="Type: Comparison")
#                 if len(docList) == 0:
#                     self.onThreading(
#                         None, ("Did not find appropriate document. Creating a new one", 4), action="updateStatusbar"
#                     )
#                     dlg = wx.FileDialog(
#                         self.view,
#                         "Please select a name for the comparison document",
#                         "",
#                         "",
#                         "",
#                         wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
#                     )
#                     if dlg.ShowModal() == wx.ID_OK:
#                         path, idName = os.path.split(dlg.GetPath())
#                     else:
#                         return
#
#                     # Create document
#                     self.docs = documents()
#                     self.docs.title = idName
#                     self.docs.path = path
#                     self.docs.userParameters = self.config.userParameters
#                     self.docs.userParameters["date"] = getTime()
#                     self.docs.dataType = "Type: Comparison"
#                     self.docs.fileFormat = "Format: ORIGAMI"
#                     # Initiate empty list and dictionary
#                     compDict, compList = {}, []
#                 else:
#                     self.selectDocDlg = DialogSelectDocument(self.view, presenter=self, document_list=docList)
#                     if self.selectDocDlg.ShowModal() == wx.ID_OK:
#                         pass
#
#                     # Check that document exists
#                     if self.currentDoc is None:
#                         msg = "Please select comparison document"
#                         self.onThreading(None, (msg, 4), action="updateStatusbar")
#                         return
#
#                     self.docs = self.documentsDict[self.currentDoc]
#                     self.onThreading(
#                         None,
#                         ("Using document: " + self.docs.title.encode("ascii", "replace"), 4),
#                         action="updateStatusbar",
#                     )
#                     if self.docs.gotComparisonData:
#                         compDict = self.docs.IMS2DcompData
#                         compList = []
#                         for key in self.docs.IMS2DcompData:
#                             compList.append(key)
#                     else:
#                         compDict, compList = {}, []
#         else:
#             compDict, compList = {}, []
#
#         comparisonFlag = False
#         # Get data for the dataset
#         for row in range(tempList.GetItemCount()):
#             if tempList.IsChecked(index=row):
#                 if source == "ion":
#                     # Get data for each ion
#                     (
#                         __,
#                         __,
#                         charge,
#                         color,
#                         colormap,
#                         alpha,
#                         mask,
#                         label,
#                         self.currentDoc,
#                         ionName,
#                         min_threshold,
#                         max_threshold,
#                     ) = self.view.panelMultipleIons.OnGetItemInformation(itemID=row, return_list=True)
#
#                     # processed name
#                     ionNameProcessed = "%s (processed)" % ionName
#
#                     # Check that data was extracted first
#                     if self.currentDoc == "":
#                         msg = "Please extract data first"
#                         self.onThreading(None, (msg, 4), action="updateStatusbar")
#                         continue
#                     document = self.documentsDict[self.currentDoc]
#                     dataType = document.dataType
#
#                     # ORIGAMI dataset
#                     if dataType in ["Type: ORIGAMI", "Type: MANUAL"] and document.gotCombinedExtractedIons:
#                         if self.config.overlay_usedProcessed:
#                             try:
#                                 dataIn = document.IMS2DCombIons[ionNameProcessed]
#                             except KeyError:
#                                 try:
#                                     dataIn = document.IMS2DCombIons[ionName]
#                                 except KeyError:
#                                     try:
#                                         dataIn = document.IMS2Dions[ionNameProcessed]
#                                     except KeyError:
#                                         try:
#                                             dataIn = document.IMS2Dions[ionName]
#                                         except KeyError:
#                                             continue
#                         else:
#                             try:
#                                 dataIn = document.IMS2DCombIons[ionName]
#                             except KeyError:
#                                 try:
#                                     dataIn = document.IMS2Dions[ionName]
#                                 except KeyError:
#                                     continue
#                     elif dataType in ["Type: ORIGAMI", "Type: MANUAL"] and not document.gotCombinedExtractedIons:
#                         if self.config.overlay_usedProcessed:
#                             try:
#                                 dataIn = document.IMS2Dions[ionNameProcessed]
#                             except KeyError:
#                                 try:
#                                     dataIn = document.IMS2Dions[ionName]
#                                 except KeyError:
#                                     continue
#                         else:
#                             try:
#                                 dataIn = document.IMS2Dions[ionName]
#                             except KeyError:
#                                 continue
#
#                     #                     # MANUAL dataset
#                     #                     if dataType == 'Type: MANUAL' and document.gotCombinedExtractedIons:
#                     #                         try: tempData = document.IMS2DCombIons
#                     #                         except KeyError:
#                     #                             try: tempData = document.IMS2Dions
#                     #                             except KeyError: continue
#
#                     # INFRARED dataset
#                     if dataType == "Type: Infrared" and document.gotCombinedExtractedIons:
#                         try:
#                             dataIn = document.IMS2DCombIons
#                         except KeyError:
#                             try:
#                                 dataIn = document.IMS2Dions
#                             except KeyError:
#                                 continue
#                     tempAccumulator = tempAccumulator + 1
#
#                     selectedItemUnique = "ion={} ({})".format(ionName, self.currentDoc)
#                     zvals, xaxisLabels, xlabel, yaxisLabels, ylabel, __ = self.get2DdataFromDictionary(
#                         dictionary=dataIn, dataType="plot", compact=False
#                     )
#
#                 elif source == "text":
#                     tempAccumulator += 1
#                     comparisonFlag = False  # used only in case the user reloaded comparison document
#                     # Get data for each ion
#                     itemInfo = self.view.panelMultipleText.OnGetItemInformation(itemID=row)
#                     charge = itemInfo["charge"]
#                     color = itemInfo["color"]
#                     colormap = itemInfo["colormap"]
#                     alpha = itemInfo["alpha"]
#                     mask = itemInfo["mask"]
#                     label = itemInfo["label"]
#                     filename = itemInfo["document"]
#                     min_threshold = itemInfo["min_threshold"]
#                     max_threshold = itemInfo["max_threshold"]
#                     # get document
#                     try:
#                         document = self.documentsDict[filename]
#
#                         if self.config.overlay_usedProcessed:
#                             if document.got2Dprocess:
#                                 try:
#                                     tempData = document.IMS2Dprocess
#                                 except Exception:
#                                     tempData = document.IMS2D
#                             else:
#                                 tempData = document.IMS2D
#                         else:
#                             try:
#                                 tempData = document.IMS2D
#                             except Exception:
#                                 self.onThreading(None, ("No data for selected file", 4), action="updateStatusbar")
#                                 continue
#
#                         zvals = tempData["zvals"]
#                         xaxisLabels = tempData["xvals"]
#                         xlabel = tempData["xlabels"]
#                         yaxisLabels = tempData["yvals"]
#                         ylabel = tempData["ylabels"]
#                         ionName = filename
#                         # Populate x-axis labels
#                         if isinstance(xaxisLabels, list):
#                             pass
#                         elif xaxisLabels == "":
#                             startX = tempList.GetItem(itemId=row, col=self.config.textlistColNames["startX"]).GetText()
#                             endX = tempList.GetItem(itemId=row, col=self.config.textlistColNames["endX"]).GetText()
#                             stepsX = len(zvals[0])
#                             if startX == "" or endX == "":
#                                 pass
#                             else:
#                                 xaxisLabels = self.onPopulateXaxisTextLabels(
#                                     startVal=str2num(startX), endVal=str2num(endX), shapeVal=stepsX
#                                 )
#                                 document.IMS2D["xvals"] = xaxisLabels
#
#                         if not comparisonFlag:
#                             selectedItemUnique = "file:%s" % filename
#                     # only triggered when using data from comparison document
#                     except Exception:
#                         try:
#                             comparisonFlag = True
#                             dpcument_filename, selectedItemUnique = re.split(": ", filename)
#                             document = self.documentsDict[dpcument_filename]
#                             tempData = document.IMS2DcompData[selectedItemUnique]
#                             # unpack data
#                             zvals = tempData["zvals"]
#                             ionName = tempData["ion_name"]
#                             xaxisLabels = tempData["xvals"]
#                             yaxisLabels = tempData["yvals"]
#                             ylabel = tempData["ylabels"]
#                             xlabel = tempData["xlabels"]
#                         # triggered when using data from interactive document
#                         except Exception:
#                             comparisonFlag = False
#                             dpcument_filename, selectedItemUnique = re.split(": ", filename)
#                             document = self.documentsDict[dpcument_filename]
#                             tempData = document.IMS2Dions[selectedItemUnique]
#                             # unpack data
#                             zvals = tempData["zvals"]
#                             ionName = filename
#                             xaxisLabels = tempData["xvals"]
#                             yaxisLabels = tempData["yvals"]
#                             ylabel = tempData["ylabels"]
#                             xlabel = tempData["xlabels"]
#
#                 if not comparisonFlag:
#                     if label == "" or label is None:
#                         label = ""
#                     compList.insert(0, selectedItemUnique)
#                     # Check if exists. We need to extract labels (header...)
#                     checkExist = compDict.get(selectedItemUnique, None)
#                     if checkExist is not None:
#                         title = compDict[selectedItemUnique].get("header", "")
#                         header = compDict[selectedItemUnique].get("header", "")
#                         footnote = compDict[selectedItemUnique].get("footnote", "")
#                     else:
#                         title, header, footnote = "", "", ""
#                     compDict[selectedItemUnique] = {
#                         "zvals": zvals,
#                         "ion_name": ionName,
#                         "cmap": colormap,
#                         "color": color,
#                         "alpha": str2num(alpha),
#                         "mask": str2num(mask),
#                         "xvals": xaxisLabels,
#                         "xlabels": xlabel,
#                         "yvals": yaxisLabels,
#                         "charge": charge,
#                         "min_threshold": min_threshold,
#                         "max_threshold": max_threshold,
#                         "ylabels": ylabel,
#                         "index": row,
#                         "shape": zvals.shape,
#                         "label": label,
#                         "title": title,
#                         "header": header,
#                         "footnote": footnote,
#                     }
#                 else:
#                     compDict[selectedItemUnique] = tempData
#
#         # Check whether the user selected at least two files (and no more than 2 for certain functions)
#         if tempAccumulator < 2:
#             msg = "Please select at least two files"
#             DialogBox(exceptionTitle="Error", exceptionMsg=msg, type="Error")
#             return
#
#         # Remove duplicates from list
#         compList = removeDuplicates(compList)
#
#         zvalsIon1plot = compDict[compList[0]]["zvals"]
#         zvalsIon2plot = compDict[compList[1]]["zvals"]
#         name1 = compList[0]
#         name2 = compList[1]
#         # Check if text files are of identical size
#         if (zvalsIon1plot.shape != zvalsIon2plot.shape) and self.config.overlayMethod not in ["Grid (n x n)"]:
#             msg = "Comparing ions: {} and {}. These files are NOT of identical shape!".format(name1, name2)
#             DialogBox(exceptionTitle="Error", exceptionMsg=msg, type="Error")
#             return
#
#         defaultVals = ["Reds", "Greens"]
#
#         # Check if the table has information about colormap
#         if compDict[compList[0]]["cmap"] == "":
#             cmapIon1 = defaultVals[0]  # change here
#             compDict[compList[0]]["cmap"] = cmapIon1
#             tempList.SetStringItem(index=compDict[compList[0]]["index"], col=3, label=cmapIon1)
#         else:
#             cmapIon1 = compDict[compList[0]]["cmap"]
#
#         if compDict[compList[1]]["cmap"] == "":
#             cmapIon2 = defaultVals[1]
#             compDict[compList[1]]["cmap"] = cmapIon1
#             tempList.SetStringItem(index=compDict[compList[1]]["index"], col=3, label=cmapIon2)
#         else:
#             cmapIon2 = compDict[compList[1]]["cmap"]
#
#         # Defaults for alpha and mask
#         defaultVals_alpha = [1, 0.5]
#         defaultVals_mask = [0.25, 0.25]
#
#         # Check if the user set value of transparency (alpha)
#         if compDict[compList[0]]["alpha"] == "" or compDict[compList[0]]["alpha"] is None:
#             alphaIon1 = defaultVals_alpha[0]
#             compDict[compList[0]]["alpha"] = alphaIon1
#             tempList.SetStringItem(index=compDict[compList[0]]["index"], col=col_order["alpha"], label=str(alphaIon1))
#         else:
#             alphaIon1 = str2num(compDict[compList[0]]["alpha"])
#
#         if compDict[compList[1]]["alpha"] == "" or compDict[compList[1]]["alpha"] is None:
#             alphaIon2 = defaultVals_alpha[1]
#             compDict[compList[1]]["alpha"] = alphaIon2
#             tempList.SetStringItem(index=compDict[compList[1]]["index"], col=col_order["alpha"], label=str(alphaIon2))
#         else:
#             alphaIon2 = str2num(compDict[compList[1]]["alpha"])
#
#         # Check if the user set value of transparency (mask)
#         if compDict[compList[0]]["mask"] == "" or compDict[compList[0]]["mask"] is None:
#             maskIon1 = defaultVals_mask[0]
#             compDict[compList[0]]["mask"] = maskIon1
#             tempList.SetStringItem(index=compDict[compList[0]]["index"], col=col_order["mask"], label=str(maskIon1))
#         else:
#             maskIon1 = str2num(compDict[compList[0]]["mask"])
#
#         if compDict[compList[1]]["mask"] == "" or compDict[compList[1]]["mask"] is None:
#             maskIon2 = defaultVals_mask[1]
#             compDict[compList[1]]["mask"] = maskIon2
#             tempList.SetStringItem(index=compDict[compList[1]]["index"], col=col_order["mask"], label=str(maskIon2))
#         else:
#             maskIon2 = str2num(compDict[compList[1]]["mask"])
#
#             # Check how many items were selected
#             if tempAccumulator > 2:
#                 msg = "Currently only supporting an overlay of two ions.\n" + "Comparing: {} and {}.".format(
#                     compList[0], compList[1]
#                 )
#                 DialogBox(exceptionTitle="Warning", exceptionMsg=msg, type="Warning")
#                 print(msg)
#
#             if self.config.overlayMethod == "RMSD":
#                 """ Compute RMSD of two selected files """
#
#             elif self.config.overlayMethod == "RMSF":
#                 """ Compute RMSF of two selected files """
#                 self.rmsdfFlag = True
#
#
#
#
#
#
#
#
#         # Add data to document
#         if add_data_to_document:
#             self.docs.gotComparisonData = True
#             self.docs.IMS2DcompData = compDict
#             self.currentDoc = self.docs.title
#
#             # Update file list
#             self.OnUpdateDocument(self.docs, "comparison_data")
