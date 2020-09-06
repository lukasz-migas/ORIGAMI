"""Heatmap groups"""
# Standard library imports
from typing import Dict
from typing import List
from typing import Union

# Local imports
from origami.objects.containers import DataObject
from origami.objects.groups.base import DataGroup


class HeatmapGroup(DataGroup):
    """Heatmap group object"""

    def __init__(
        self,
        data_objects: Union[Dict[str, DataObject], Dict[str, str], List[DataObject], List[List[str]]],
        x_label="",
        y_label="",
        x_label_options=None,
        y_label_options=None,
        metadata=None,
        extra_data=None,
        **kwargs,
    ):
        super().__init__(
            data_objects,
            x_label=x_label,
            y_label=y_label,
            metadata=metadata,
            extra_data=extra_data,
            x_label_options=x_label_options,
            y_label_options=y_label_options,
            **kwargs,
        )

    @property
    def arrays(self):
        """Return list of arrays"""
        return [data_obj.array for data_obj in self]

    @property
    def x(self):
        """Returns x-axis array"""
        if not self.validate_x_labels():
            raise ValueError("x-axis labels are not the same")
        return self.xs[0]

    @property
    def y(self):
        """Returns x-axis array"""
        if not self.validate_y_labels():
            raise ValueError("y-axis labels are not the same")
        return self.ys[0]

    @property
    def x_label(self):
        """Returns x-axis label"""
        if not self.validate_x_labels():
            raise ValueError("x-axis labels are not the same")
        return self.x_labels[0]

    @property
    def y_label(self):
        """Returns y-axis label"""
        if not self.validate_y_labels():
            raise ValueError("y-axis labels are not the same")
        return self.y_labels[0]

    @property
    def need_resample(self):
        return False

    def mean(self):
        pass

    def sum(self):
        pass

    def resample(self):
        pass

    def reset(self):
        pass


class IonHeatmapGroup(HeatmapGroup):
    """Ion heatmap group"""

    def __init__(
        self, data_objects, metadata=None, extra_data=None, x_label="Scans", y_label="Drift time (bins)", **kwargs
    ):
        super().__init__(
            data_objects,
            x_label=x_label,
            y_label=y_label,
            x_label_options=[
                "Scans",
                "Time (mins)",
                "Retention time (mins)",
                "Collision Voltage (V)",
                "Activation Voltage (V)",
                "Activation Energy (V)",
                "Lab Frame Energy (eV)",
                "Activation Voltage (eV)",
                "Activation Energy (eV)",
            ],
            y_label_options=[
                "Drift time (bins)",
                "Drift time (ms)",
                "Arrival time (ms)",
                "Collision Cross Section (Å²)",
                "CCS (Å²)",
            ],
            metadata=metadata,
            extra_data=extra_data,
            **kwargs,
        )
