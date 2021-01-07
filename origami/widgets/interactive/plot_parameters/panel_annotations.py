"""Legend panel"""
# Standard library imports
from typing import Dict

# Third-party imports
import wx

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.color import convert_rgb_255_to_1
from origami.config.config import CONFIG
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_static_text
from origami.widgets.interactive.plot_parameters.panel_base import PanelSettingsBase


class PanelAnnotationSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    bokeh_labels_show, bokeh_labels_label_show, bokeh_labels_label_offset_x = None, None, None
    bokeh_labels_label_offset_y, bokeh_labels_label_rotation, bokeh_labels_label_font_size = None, None, None
    bokeh_labels_label_font_weight, bokeh_labels_label_color, bokeh_labels_patch_show = None, None, None
    bokeh_labels_patch_alpha, bokeh_labels_patch_color = None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""
        annotation_label_show = make_static_text(self, "Show annotations:")
        self.bokeh_labels_show = wx.CheckBox(self, -1, "", (15, 30))
        self.bokeh_labels_show.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.bokeh_labels_show, "Show annotations in exported plot - when available")

        annotation_label_add_to_peak = make_static_text(self, "Add label to peaks:")
        self.bokeh_labels_label_show = wx.CheckBox(self, -1, "", (15, 30))
        self.bokeh_labels_label_show.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.bokeh_labels_label_show, "A pre-defined (by you) label will be added to selected peaks")

        annotation_label_offset_x = make_static_text(self, "Position offset X:")
        self.bokeh_labels_label_offset_x = wx.SpinCtrlDouble(self, wx.ID_ANY, inc=5, min=-100, max=100, size=(50, -1))
        self.bokeh_labels_label_offset_x.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        annotation_label_offset_y = make_static_text(self, "Position offset Y:")
        self.bokeh_labels_label_offset_y = wx.SpinCtrlDouble(self, wx.ID_ANY, min=-100, max=100, inc=5, size=(50, -1))
        self.bokeh_labels_label_offset_y.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        annotation_label_rotation = make_static_text(self, "Label rotation:")
        self.bokeh_labels_label_rotation = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=180, inc=45, size=(50, -1))
        self.bokeh_labels_label_rotation.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        annotation_label_fontsize = make_static_text(self, "Font size:")
        self.bokeh_labels_label_font_size = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=32, inc=2, size=(50, -1))
        self.bokeh_labels_label_font_size.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.bokeh_labels_label_font_weight = make_checkbox(self, "bold")
        self.bokeh_labels_label_font_weight.Bind(wx.EVT_CHECKBOX, self.on_apply)

        annotation_label_font_color_btn = make_static_text(self, "Font color:")
        self.bokeh_labels_label_color = wx.Button(self, wx.ID_ANY, "", size=wx.Size(26, 26), name="annotation_color")
        self.bokeh_labels_label_color.Bind(wx.EVT_BUTTON, self.on_assign_color)

        annotation_patch_show = make_static_text(self, "Add patch to peaks:")
        self.bokeh_labels_patch_show = wx.CheckBox(self, -1, "", (15, 30))
        self.bokeh_labels_patch_show.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(
            self.bokeh_labels_patch_show,
            "A rectangular-shaped patch will be added to the spectrum to highlight selected peaks",
        )

        annotation_patch_transparency = make_static_text(self, "Patch transparency:")
        self.bokeh_labels_patch_alpha = wx.SpinCtrlDouble(self, wx.ID_ANY, inc=0.25, min=0, max=1, size=(50, -1))
        self.bokeh_labels_patch_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bokeh_labels_patch_color = make_static_text(self, "Font color:")
        self.bokeh_labels_patch_color = wx.Button(self, wx.ID_ANY, "", size=wx.Size(26, 26), name="patch_color")
        self.bokeh_labels_patch_color.Bind(wx.EVT_BUTTON, self.on_assign_color)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(annotation_label_show, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_labels_show, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_label_add_to_peak, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_labels_label_show, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_label_offset_x, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_labels_label_offset_x, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_label_offset_y, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_labels_label_offset_y, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_label_rotation, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_labels_label_rotation, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_label_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_labels_label_font_size, (n, 1), flag=wx.EXPAND)
        grid.Add(self.bokeh_labels_label_font_weight, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_label_font_color_btn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_labels_label_color, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_patch_show, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_labels_patch_show, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_patch_transparency, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_labels_patch_alpha, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(bokeh_labels_patch_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_labels_patch_color, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_assign_color(self, evt):
        """Update color"""
        # get color
        source, color_255, color_1 = self._on_assign_color(evt)
        # update configuration and button color
        if source == "annotation_color":
            self.bokeh_labels_label_color.SetBackgroundColour(color_255)
        elif source == "patch_color":
            self.bokeh_labels_patch_color.SetBackgroundColour(color_255)

    def get_config(self) -> Dict:
        """Get configuration data"""
        if self.import_evt:
            return dict()
        return {
            "bokeh_labels_show": self.bokeh_labels_show.GetValue(),
            "bokeh_labels_label_show": self.bokeh_labels_label_show.GetValue(),
            "bokeh_labels_label_offset_x": self.bokeh_labels_label_offset_x.GetValue(),
            "bokeh_labels_label_offset_y": self.bokeh_labels_label_offset_y.GetValue(),
            "bokeh_labels_label_rotation": self.bokeh_labels_label_rotation.GetValue(),
            "bokeh_labels_label_font_size": self.bokeh_labels_label_font_size.GetValue(),
            "bokeh_labels_label_font_weight": self.bokeh_labels_label_font_weight.GetValue(),
            "bokeh_labels_label_color": convert_rgb_255_to_1(self.bokeh_labels_label_color.GetBackgroundColour()),
            "bokeh_labels_patch_show": self.bokeh_labels_patch_show.GetValue(),
            "bokeh_labels_patch_alpha": self.bokeh_labels_patch_alpha.GetValue(),
            "bokeh_labels_patch_color": convert_rgb_255_to_1(self.bokeh_labels_patch_color.GetBackgroundColour()),
        }

    def _on_set_config(self, config):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.bokeh_labels_show.SetValue(config.get("bokeh_labels_show", CONFIG.bokeh_labels_show))
        self.bokeh_labels_label_show.SetValue(config.get("bokeh_labels_label_show", CONFIG.bokeh_labels_label_show))
        self.bokeh_labels_label_offset_x.SetValue(
            config.get("bokeh_labels_label_offset_x", CONFIG.bokeh_labels_label_offset_x)
        )
        self.bokeh_labels_label_offset_y.SetValue(
            config.get("bokeh_labels_label_offset_y", CONFIG.bokeh_labels_label_offset_y)
        )
        self.bokeh_labels_label_rotation.SetValue(
            config.get("bokeh_labels_label_rotation", CONFIG.bokeh_labels_label_rotation)
        )
        self.bokeh_labels_label_font_size.SetValue(
            config.get("bokeh_labels_label_font_size", CONFIG.bokeh_labels_label_font_size)
        )
        self.bokeh_labels_label_font_weight.SetValue(
            config.get("bokeh_labels_label_font_weight", CONFIG.bokeh_labels_label_font_weight)
        )
        self.bokeh_labels_label_color.SetBackgroundColour(
            convert_rgb_1_to_255(config.get("bokeh_labels_label_color", CONFIG.bokeh_labels_label_color))
        )
        self.bokeh_labels_patch_show.SetValue(config.get("bokeh_labels_patch_show", CONFIG.bokeh_labels_patch_show))
        self.bokeh_labels_patch_alpha.SetValue(config.get("bokeh_labels_patch_alpha", CONFIG.bokeh_labels_patch_alpha))
        self.bokeh_labels_patch_color.SetBackgroundColour(
            convert_rgb_1_to_255(config.get("bokeh_labels_patch_color", CONFIG.bokeh_labels_patch_color))
        )
        self.import_evt = False


if __name__ == "__main__":

    def _main():
        # Local imports
        from origami.app import App

        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                self.scrolledPanel = PanelAnnotationSettings(self, None)

        app = App()
        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
