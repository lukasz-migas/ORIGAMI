"""Data visualisation module"""
# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging

import numpy as np
import processing.activation as pr_activation
import processing.heatmap as pr_heatmap
import processing.spectra as pr_spectra
from numpy.ma.core import masked_array
from utils.color import combine_rgb
from utils.color import convert_rgb_255_to_1
from utils.color import make_rgb_cube
from utils.exceptions import MessageError
from utils.visuals import calculate_label_position

logger = logging.getLogger("origami")


class DataVisualization:
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
                    if shape == "":
                        alternative_dimension = 0 if dimension == 1 else 1
                        shape = shape_split[alternative_dimension]
            shape_list.append(shape.strip())

        # reduce to only include unique values
        print(shape_list)
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

    def _check_array_shape(self, xvals, yvals):
        xvals = np.asarray(xvals)
        yvals = np.asarray(yvals)
        return xvals.shape == yvals.shape

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
                try:
                    xvals = data["yvals"]
                    yvals = data.get("yvals1D", data["zvals"].sum(axis=1))
                except KeyError:
                    xvals = data["xvals"]
                    yvals = data["yvals"]
            elif data_type == "chromatogram":
                xvals = data["xvals"]
                try:
                    yvals = data.get("yvalsRT", data["zvals"].sum(axis=0))
                except KeyError:
                    yvals = data["yvals"]
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

        # plot
        if data_type == "mobilogram":
            xlabel = data["ylabels"]
            dataset_name = self._generate_overlay_name(dataset_info, "Overlay (DT): ")
        elif data_type == "chromatogram":
            xlabel = data["xlabels"]
            dataset_name = self._generate_overlay_name(dataset_info, "Overlay (RT): ")
        elif data_type == "mass_spectra":
            xlabel = data["xlabels"]
            dataset_name = self._generate_overlay_name(dataset_info, "Overlay (MS): ")

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "Overlay",
                "xvals": xlist,
                "yvals": ylist,
                "xlabels": xlabel,
                "colors": colorlist,
                "xlimits": [min(xvals), max(xvals)],
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }

        # plot
        self.on_show_overlay_spectrum_overlay(dataset_holder["data"], data_type, **kwargs)

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
                try:
                    yvals = data.get("yvals1D", data["zvals"].sum(axis=1))
                except KeyError:
                    yvals = data["yvals"]
            elif data_type == "chromatogram":
                xvals = data["xvals"]
                try:
                    yvals = data.get("yvalsRT", data["zvals"].sum(axis=0))
                except KeyError:
                    yvals = data["yvals"]
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

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "Butterfly",
                "xvals": xlist,
                "yvals": ylist,
                "xlabels": xlabel,
                "colors": colorlist,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }

        # plot
        self.on_show_overlay_spectrum_butterfly(dataset_holder["data"], **kwargs)

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
                try:
                    yvals = data.get("yvals1D", data["zvals"].sum(axis=1))
                except KeyError:
                    yvals = data["yvals"]
            elif data_type == "chromatogram":
                xvals = data["xvals"]
                try:
                    yvals = data.get("yvalsRT", data["zvals"].sum(axis=0))
                except KeyError:
                    yvals = data["yvals"]
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
        xlist[0], ylist[0], xlist[0], ylist[1] = self.data_processing.subtract_spectra(
            xlist[0], ylist[0], xlist[1], ylist[1]
        )

        # plot
        if data_type == "mobilogram":
            xlabel = data["ylabels"]
            dataset_name = self._generate_overlay_name(dataset_info, "Subtract (DT): ")
        elif data_type == "chromatogram":
            xlabel = data["xlabels"]
            dataset_name = self._generate_overlay_name(dataset_info, "Subtract (RT): ")
        elif data_type == "mass_spectra":
            xlabel = data["xlabels"]
            dataset_name = self._generate_overlay_name(dataset_info, "Subtract (MS): ")

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "Subtract",
                "xvals": xlist,
                "yvals": ylist,
                "xlabels": xlabel,
                "colors": colorlist,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }

        # plot
        self.on_show_overlay_spectrum_butterfly(dataset_holder["data"], **kwargs)

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
                try:
                    yvals = data.get("yvals1D", data["zvals"].sum(axis=1))
                except KeyError:
                    yvals = data["yvals"]
                xvals = data["xvals"]
                if not self._check_array_shape(xvals, yvals):
                    xvals = data["yvals"]
            elif data_type == "chromatogram":
                xvals = data["xvals"]
                try:
                    yvals = data.get("yvalsRT", data["zvals"].sum(axis=0))
                except KeyError:
                    yvals = data["yvals"]
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
                "xlabels": xlabel,
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
    #             itemInfo = self.on_get_item_information(row)
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
    #             colors.append(convert_rgb_255_to_1(itemInfo["color"]))
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
    #                 "xlabels": xlabel,
    #                 "ylabels": ylabel,
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
                "xvals": data["xvals"],
                "yvals": data["yvals"],
                "xlabels": data["xlabels"],
                "ylabels": data["ylabels"],
                "cmaps": cmaplist,
                "masks": masklist,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }

        # plot
        self.on_show_overlay_heatmap_mask(dataset_holder["data"], **kwargs)

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
                "xvals": data["xvals"],
                "yvals": data["yvals"],
                "xlabels": data["xlabels"],
                "ylabels": data["ylabels"],
                "cmaps": cmaplist,
                "alphas": alphalist,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }

        # plot
        self.on_show_overlay_heatmap_transparent(dataset_holder["data"], **kwargs)

        return dataset_holder

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
        #
        #         self.setXYlimitsRMSD2D(xaxisLabels, yaxisLabels)
        #
        # plot

        # add label
        label_x_pos, label_y_pos = calculate_label_position(xvals, yvals, self.config.rmsd_location)

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
                "xlabels": data["xlabels"],
                "ylabels": data["ylabels"],
                "rmsdLabel": f"RMSD: {pRMSD:.2f}",
                "rmsd_location": [label_x_pos, label_y_pos],
                "cmap": self.config.currentCmap,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }

        # plot
        self.on_show_overlay_heatmap_rmsd(dataset_holder["data"], **kwargs)

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
        xvals = data["xvals"]
        yvals = data["yvals"]

        # calculate RMSD
        pRMSD, zvals = pr_activation.compute_RMSD(zlist[0], zlist[1])

        # calculate RMSF
        pRMSF_list = pr_activation.compute_RMSF(zlist[0], zlist[1])
        pRMSF_list = pr_heatmap.smooth_gaussian_2D(pRMSF_list, sigma=1)

        # add label
        label_x_pos, label_y_pos = calculate_label_position(xvals, yvals, self.config.rmsd_location)

        # generate item name
        dataset_name = self._generate_overlay_name(dataset_info, "RMSF: ")

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
                "xlabels": data["xlabels"],
                "xlabelRMSD": data["xlabels"],
                "ylabelRMSD": data["ylabels"],
                "ylabelRMSF": "RMSD (%)",
                "ylabels": data["ylabels"],
                "rmsdLabel": f"RMSD: {pRMSD:.2f}",
                "rmsd_location": [label_x_pos, label_y_pos],
                "cmap": self.config.currentCmap,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }

        # plot
        self.on_show_overlay_heatmap_rmsf(dataset_holder["data"], **kwargs)

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
        xvals = data["xvals"]
        yvals = data["yvals"]

        # calculate RMSD
        pRMSD, zvals = pr_activation.compute_RMSD(zlist[0], zlist[1])
        label_x_pos, label_y_pos = calculate_label_position(xvals, yvals, self.config.rmsd_location)

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
                "xlabels": data["xlabels"],
                "ylabels": data["ylabels"],
                "cmaps": cmaplist,
                "rmsdLabel": f"RMSD: {pRMSD:.2f}",
                "rmsd_location": [label_x_pos, label_y_pos],
                "cmap": self.config.currentCmap,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }

        # plot
        self.on_show_overlay_heatmap_grid_2to1(dataset_holder["data"], **kwargs)

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

        # generate item name
        dataset_name = self._generate_overlay_name(dataset_info, prepend="Grid (n x n): ")

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": "Grid (n x n)",
                "xlist": xlist,
                "ylist": ylist,
                "zlist": zlist,
                "xlabels": data["xlabels"],
                "ylabels": data["ylabels"],
                "cmaps": cmaplist,
                "legend_text": legend,
                "dataset_info": dataset_info,
            },
        }

        # plot
        self.on_show_overlay_heatmap_grid_nxn(dataset_holder["data"], **kwargs)

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
            color = convert_rgb_255_to_1(item_info["color"])
            min_threshold = item_info["min_threshold"]
            max_threshold = item_info["max_threshold"]

            zvals = pr_heatmap.adjust_min_max_intensity(zvals, min_threshold, max_threshold)

            # convert to rgb plot
            rgb = make_rgb_cube(zvals, color, add_alpha=True)

            zlist.append(rgb)
            colorlist.append(item_info["color"])
            xlist.append(data["xvals"])
            ylist.append(data["yvals"])
            label = item_info["label"]
            if label == "":
                label = item_info["dataset_name"]
            legend.append([color, label])

        # combine channels
        rgb_plot = combine_rgb(zlist)

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
                "zvals": rgb_plot,
                "xvals": data["xvals"],
                "yvals": data["yvals"],
                "xlabels": data["xlabels"],
                "ylabels": data["ylabels"],
                "colors": colorlist,
                "legend_text": legend,
                "dataset_info": dataset_info,
            },
        }

        # plot
        self.on_show_overlay_heatmap_rgb(dataset_holder["data"], **kwargs)

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
                "cmap": self.config.currentCmap,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }

        # plot
        self.on_show_overlay_heatmap_rmsd_matrix(dataset_holder["data"], **kwargs)

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

        # generate item name
        dataset_name = self._generate_overlay_name(dataset_info, f"{method}: ")

        # generate dataset holder
        dataset_holder = {
            "name": dataset_name,
            "data": {
                "method": method,
                "xlist": xlist,
                "ylist": ylist,
                "zlist": zlist,
                "zvals": zvals,
                "xvals": data["xvals"],
                "yvals": data["yvals"],
                "xlabels": data["xlabels"],
                "ylabels": data["ylabels"],
                "cmap": self.config.currentCmap,
                "labels": legend,
                "dataset_info": dataset_info,
            },
        }

        # plot
        self.on_show_overlay_heatmap_statistical(dataset_holder["data"], **kwargs)

        return dataset_holder

    def on_show_overlay_spectrum_overlay(self, data, data_type, **kwargs):

        colorlist = data["colors"]
        xlimits = data["xlimits"]
        legend = data["labels"]
        xlist = data["xvals"]
        ylist = data["yvals"]
        xlabel = data["xlabels"]

        # ensure plot is shown in right window
        if "plot_obj" not in kwargs:
            kwargs["plot"] = "Overlay"

        # plot
        if data_type == "mobilogram":
            self.panelPlots.on_plot_overlay_DT(
                xvals=xlist, yvals=ylist, xlabel=xlabel, colors=colorlist, xlimits=xlimits, labels=legend, **kwargs
            )
        elif data_type == "chromatogram":
            self.panelPlots.on_plot_overlay_RT(
                xvals=xlist, yvals=ylist, xlabel=xlabel, colors=colorlist, xlimits=xlimits, labels=legend, **kwargs
            )
        elif data_type == "mass_spectra":
            self.panelPlots.on_plot_overlay_RT(
                xvals=xlist, yvals=ylist, xlabel=xlabel, colors=colorlist, xlimits=xlimits, labels=legend, **kwargs
            )

    def on_show_overlay_spectrum_butterfly(self, data, **kwargs):

        colorlist = data["colors"]
        legend = data["labels"]
        xlist = data["xvals"]
        ylist = data["yvals"]
        xlabel = data["xlabels"]

        # ensure plot is shown in right window
        if "plot_obj" not in kwargs:
            kwargs["plot"] = "Overlay"

        # plot
        self.panelPlots.plot_compare_spectra(
            xlist[0],
            xlist[1],
            ylist[0],
            ylist[1],
            xlabel=xlabel,
            legend=legend,
            line_color_1=colorlist[0],
            line_color_2=colorlist[1],
            **kwargs,
        )

    def on_show_overlay_spectrum_waterfall(self, data, **kwargs):

        colorlist = data["colors"]
        legend = data["labels"]
        xlist = data["xvals"]
        ylist = data["yvals"]
        xlabel = data["xlabels"]

        # ensure plot is shown in right window
        if "plot_obj" not in kwargs:
            kwargs["plot"] = "Overlay"

        # plot
        kwargs.update(show_y_labels=True, labels=legend, add_legend=True)
        self.panelPlots.on_plot_waterfall(
            xlist, ylist, None, colors=colorlist, xlabel=xlabel, ylabel="Intensity", **kwargs
        )

    def on_show_overlay_heatmap_statistical(self, data, **kwargs):

        # get labels
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]
        xvals = data["xvals"]
        yvals = data["yvals"]
        zvals = data["zvals"]
        cmap = self.config.currentCmap

        # ensure plot is shown in right window
        if "plot_obj" not in kwargs:
            kwargs["plot"] = "Overlay"

        self.panelPlots.on_plot_2D_data(data=[zvals, xvals, xlabel, yvals, ylabel, cmap], **kwargs)

    def on_show_overlay_heatmap_rmsd(self, data, **kwargs):

        # get labels
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]
        xvals = data["xvals"]
        yvals = data["yvals"]
        zvals = data["zvals"]
        rmsd_label = data["rmsdLabel"]

        # plot
        cmap = self.config.currentCmap
        self.panelPlots.on_plot_RMSD(zvals, xvals, yvals, xlabel, ylabel, cmap, plotType="RMSD", **kwargs)

        # add label
        label_x_pos, label_y_pos = calculate_label_position(xvals, yvals, self.config.rmsd_location)
        if None not in [label_x_pos, label_y_pos]:
            self.panelPlots.on_add_label(label_x_pos, label_y_pos, rmsd_label, 0, **kwargs)

    def on_show_overlay_heatmap_rmsf(self, data, **kwargs):

        # get labels
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]
        xvals = data["xvals"]
        yvals = data["yvals"]
        pRMSF_list = data["yvalsRMSF"]
        zvals = data["zvals"]
        rmsd_label = data["rmsdLabel"]

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

    def on_show_overlay_heatmap_rmsd_matrix(self, data, **kwargs):

        zvals = data["zvals"]
        legend = data["labels"]

        # plot
        cmap = self.config.currentCmap
        self.panelPlots.on_plot_matrix(zvals=zvals, xylabels=legend, cmap=cmap, **kwargs)

    def on_show_overlay_heatmap_rgb(self, data, **kwargs):

        # get labels
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]
        xvals = data["xvals"]
        yvals = data["yvals"]
        legend = data["legend_text"]
        rgb_plot = data["zvals"]

        # ensure plot is shown in right window
        if "plot_obj" not in kwargs:
            kwargs["plot"] = "Overlay"

        self.panelPlots.on_plot_rgb(rgb_plot, xvals, yvals, xlabel, ylabel, legend, **kwargs)

    def on_show_overlay_heatmap_transparent(self, data, **kwargs):

        # get labels
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]
        xvals = data["xvals"]
        yvals = data["yvals"]
        zlist = data["zlist"]
        alphalist = data["alphas"]
        cmaplist = data["cmaps"]

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

    def on_show_overlay_heatmap_mask(self, data, **kwargs):

        # get labels
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]
        xvals = data["xvals"]
        yvals = data["yvals"]
        zlist = data["zlist"]
        masklist = data["masks"]
        cmaplist = data["cmaps"]

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

    def on_show_overlay_heatmap_grid_2to1(self, data, **kwargs):

        # get labels
        zlist = data["zlist"]
        zvals = data["zvals"]
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]
        xvals = data["xvals"]
        yvals = data["yvals"]
        cmaplist = data.get("cmaps", ["Reds", "Greens"])
        rmsd_label = data["rmsdLabel"]

        self.panelPlots.on_plot_grid(
            zlist[0], zlist[1], zvals, xvals, yvals, xlabel, ylabel, cmaplist[0], cmaplist[1], **kwargs
        )

        # add label
        label_x_pos, label_y_pos = calculate_label_position(xvals, yvals, self.config.rmsd_location)
        if None not in [label_x_pos, label_y_pos]:
            self.panelPlots.on_add_label(
                label_x_pos, label_y_pos, rmsd_label, 0, plot="Grid", plot_obj=kwargs.pop("plot_obj", None)
            )

    def on_show_overlay_heatmap_grid_nxn(self, data, **kwargs):

        # get labels
        zlist = data["zlist"]
        legend = data["legend_text"]
        xlabel = data["xlabels"]
        ylabel = data["ylabels"]
        xlist = data["xlist"]
        ylist = data["ylist"]
        cmaplist = data.get("cmaps", ["Reds", "Greens"])

        self.panelPlots.on_plot_n_grid(zlist, cmaplist, legend, xlist, ylist, xlabel, ylabel, **kwargs)
