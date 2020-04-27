# Standard library imports
import logging

# Local imports
from origami.objects.annotations import Annotations
from origami.readers.io_document import open_py_object

logger = logging.getLogger(__name__)


def convert_pickle_to_zarr(path: str):
    """Convert pickle object to the latest zarr version"""
    document_obj, document_version = open_py_object(path)
    # check version
    if document_version < 2:
        document_obj = convert_v1_to_v2(document_obj)
    # upgrade annotations
    upgrade_document_annotations(document_obj)

    #


def convert_v1_to_v2(document):
    """Fix old-style documents to comply with current version

    Since the original release, a couple of things have changed. I've tried to keep things as backward-compatible
    as possible, but some things need to be changed. Whatever changes were made, old-documents can be re-processed
    into the new format, hopefully permitting continuous usage. New documents are not backward compatible so will
    not work on ORIGAMI version < 2.

    Parameters
    ----------
    document : document object
        document object

    Returns
    -------
    document
    """
    logger.info("Upgrading document to latest version...")

    # update document with new attributes
    for attr in ["other_data", "tandem_spectra", "file_reader", "app_data", "last_saved", "metadata"]:
        if not hasattr(document, attr):
            setattr(document, attr, {})
            logger.info(f"FIXED [Missing attribute]: {attr}")

    # OVERLAY DATA
    for key in list(document.IMS2DoverlayData):
        data = document.IMS2DoverlayData.pop(key)
        # change data structure
        if key.startswith("Grid (2->1): "):
            data["zlist"] = [data.pop("zvals_1"), data.pop("zvals_2")]
            data["cmaps"] = [data.pop("cmap_1"), data.pop("cmap_2")]
            data["zvals"] = data.pop("zvals_cum")
            logger.info(f"FIXED [Keywords]: {key}")
        if key.startswith("Grid (n x n): "):
            data["xlist"] = data.pop("xvals")
            data["ylist"] = data.pop("yvals")
            data["zlist"] = data.pop("zvals_list")
            data["cmaps"] = data.pop("cmap_list")
            data["legend_text"] = data.pop("title_list")
            logger.info(f"FIXED [Keywords]: {key}")
        if key.startswith("Mask: "):
            data["zlist"] = [data.pop("zvals1"), data.pop("zvals2")]
            data["cmaps"] = [data.pop("cmap1"), data.pop("cmap2")]
            data["masks"] = [data.pop("mask1"), data.pop("mask2")]
            [data.pop(key) for key in ["alpha1", "alpha2"]]
            logger.info(f"FIXED [Keywords]: {key}")
        if key.startswith("Transparent: "):
            data["zlist"] = [data.pop("zvals1"), data.pop("zvals2")]
            data["cmaps"] = [data.pop("cmap1"), data.pop("cmap2")]
            data["alphas"] = [data.pop("alpha1"), data.pop("alpha2")]
            [data.pop(key) for key in ["mask1", "mask2"]]
            logger.info(f"FIXED [Keywords]: {key}")
        if key.startswith("1D: ") or key.startswith("RT: "):
            data["xlabels"] = data.pop("xlabel")
            logger.info(f"FIXED [Keywords]: {key}")
        document.IMS2DoverlayData[key] = data

        # rename
        if key.startswith("1D: "):
            document.IMS2DoverlayData[key.replace("1D: ", "Overlay (DT): ")] = document.IMS2DoverlayData.pop(key)
            logger.info(f"FIXED [Renamed]: {key}")
        if key.startswith("RT: "):
            document.IMS2DoverlayData[key.replace("RT: ", "Overlay (RT): ")] = document.IMS2DoverlayData.pop(key)
            logger.info(f"FIXED [Renamed]: {key}")

        # move to new location
        if key.startswith("RMSD: ") or key.startswith("RMSF: "):
            document.gotStatsData = True
            document.IMS2DstatsData[key] = document.IMS2DoverlayData.pop(key)
            logger.info(f"FIXED [Moved]: {key}")

    # STATISTICAL DATA
    for key in list(document.IMS2DstatsData):
        data = document.IMS2DstatsData.pop(key)
        if key.startswith("RMSD: "):
            data["xlabels"] = data.pop("xlabel")
            data["ylabels"] = data.pop("ylabel")
            logger.info(f"FIXED [Keywords]: {key}")
        if key.startswith("RMSF: "):
            data["xlabels"] = data.pop("xlabelRMSD")
            data["ylabels"] = data.pop("ylabelRMSD")
            logger.info(f"FIXED [Keywords]: {key}")
        if key.startswith("RMSD Matrix"):
            data["labels"] = data.pop("matrixLabels")
            logger.info(f"FIXED [Keywords]: {key}")
        document.IMS2DstatsData[key] = data

    logger.info("Finished upgrading document to the latest version")
    return document


def upgrade_document_annotations(document):

    if "annotations" in document.massSpectrum:
        document.massSpectrum["annotations"] = convert_annotation(document.massSpectrum.pop("annotations"))
    if "annotations" in document.smoothMS:
        document.smoothMS["annotations"] = convert_annotation(document.smoothMS.pop("annotations"))
    for key in document.multipleMassSpectrum:
        if "annotations" in document.multipleMassSpectrum[key]:
            document.multipleMassSpectrum[key]["annotations"] = convert_annotation(
                document.multipleMassSpectrum[key].pop("annotations")
            )


def convert_annotation(annotations):
    annotations_doc_obj = annotations
    if type(annotations) == dict:
        annotations_doc_obj = Annotations()
        for name, annotation_dict in annotations.items():
            annotations_doc_obj.add_annotation_from_old_format(name, annotation_dict, 0)

        logger.info(f"Converted annotations to latest version. {annotations_doc_obj}")

    return annotations_doc_obj
