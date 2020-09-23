"""Handler solely responsible for generating collections of loaded data"""
# Standard library imports
from typing import Dict
from typing import List

# Local imports
from origami.utils.secret import get_short_hash
from origami.objects.document import DocumentStore
from origami.config.environment import ENV
from origami.objects.containers import DataObject


def get_overlay_metadata(data_obj: DataObject, dataset_name: str, document_title: str) -> List:
    """Get data necessary for overlay panel"""
    label, order = data_obj.get_metadata(["label", "order"])
    return [dataset_name, document_title, data_obj.shape, label, order, get_short_hash()]


def get_interactive_metadata(dataset_name: str, document_title: str) -> List:
    """Get data necessary for overlay panel"""
    return [dataset_name, document_title, get_short_hash()]


def cleanup(item_dict) -> Dict:
    """Clean-up generated dict"""
    document_titles = list(item_dict.keys())
    for document_title in document_titles:
        if not item_dict[document_title]:
            item_dict.pop(document_title)
    return item_dict


class QueryHandler:
    """Handler used to query currently present data"""

    @staticmethod
    def item_dict_to_list(item_dict) -> List:
        """Parse dictionary of items present in the document to a list"""
        item_list = []
        for _item_list in item_dict.values():
            item_list.extend(_item_list)
        return item_list

    def generate_item_dict_all(self, output_fmt="overlay"):
        """Generate list of items with the correct data type"""
        return self._generate_item_dict(
            output_fmt, ["MassSpectra", "Chromatograms", "Mobilograms", "IonHeatmaps", "MSDTHeatmaps"]
        )

    def generate_item_dict(self, plot_type: str, output_fmt="overlay"):
        """Generate list of items with the correct data type"""
        if plot_type == "mass_spectrum":
            return self.generate_item_dict_mass_spectra(output_fmt)
        elif plot_type == "chromatogram":
            return self.generate_item_dict_chromatogram(output_fmt)
        elif plot_type == "mobilogram":
            return self.generate_item_dict_mobilogram(output_fmt)
        elif plot_type == "heatmap":
            return self.generate_item_dict_heatmap(output_fmt)
        elif plot_type == "ms_heatmap":
            return self.generate_item_dict_msdt(output_fmt)

    def generate_item_dict_mass_spectra(self, output_fmt="overlay"):
        """Generate list of items with the correct data type"""
        return self._generate_item_dict(output_fmt, ["MassSpectra"])

    def generate_item_dict_chromatogram(self, output_fmt="overlay"):
        """Generate list of items with the correct data type"""
        return self._generate_item_dict(output_fmt, ["Chromatograms"])

    def generate_item_dict_mobilogram(self, output_fmt="overlay"):
        """Generate list of items with the correct data type"""
        return self._generate_item_dict(output_fmt, ["Mobilograms"])

    def generate_item_dict_heatmap(self, output_fmt="overlay"):
        """Generate list of items with the correct data type"""
        return self._generate_item_dict(output_fmt, ["IonHeatmaps"])

    def generate_item_dict_msdt(self, output_fmt="overlay"):
        """Generate list of items with the correct data type"""
        return self._generate_item_dict(output_fmt, ["MSDTHeatmaps"])

    @staticmethod
    def _generate_item_dict(output_fmt: str, all_datasets: List[str]):
        """Actually generate the item dictionary"""
        all_documents = ENV.get_document_list()

        item_dict = dict().fromkeys(all_documents, None)

        # iterate over all documents
        for document_title in all_documents:
            document: DocumentStore = ENV.on_get_document(document_title)
            item_dict[document_title] = []

            # iterate over all groups
            for dataset_type in all_datasets:
                dataset_items = document.view_group(dataset_type)

                # iterate over all data objects
                for dataset_name in dataset_items:
                    if output_fmt == "overlay":
                        data_obj = document[dataset_name, True, True]
                        item_dict[document_title].append(
                            [*get_overlay_metadata(data_obj, dataset_name, document_title)]
                        )
                    elif output_fmt == "interactive":
                        item_dict[document_title].append([*get_interactive_metadata(dataset_name, document_title)])
                    elif output_fmt == "document_dataset_list":  # simple_list
                        item_dict[document_title].append((dataset_type, dataset_name))
                    elif output_fmt == "dataset_list":  # item_list, comparison, annotations
                        item_dict[document_title].append(dataset_name)

        item_dict = cleanup(item_dict)
        return item_dict


QUERY_HANDLER = QueryHandler()
