"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_static_text
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelAnnotationSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    annotation_label_show, annotation_label_add_to_peak, annotation_label_offset_x = None, None, None
    annotation_label_offset_y, annotation_label_rotation, annotation_label_fontsize = None, None, None
    annotation_label_weight, annotation_label_font_color_btn, annotation_patch_show = None, None, None
    annotation_patch_transparency = None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""
        annotation_label_show = make_static_text(self, "Show annotations:")
        self.annotation_label_show = wx.CheckBox(self, -1, "", (15, 30))
        self.annotation_label_show.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.annotation_label_show.SetToolTip(wx.ToolTip("Show annotations in exported plot - when available"))

        annotation_label_add_to_peak = make_static_text(self, "Add label to peaks:")
        self.annotation_label_add_to_peak = wx.CheckBox(self, -1, "", (15, 30))
        self.annotation_label_add_to_peak.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.annotation_label_add_to_peak.SetToolTip(
            wx.ToolTip("A pre-defined (by you) label will be added to selected peaks")
        )

        annotation_label_offset_x = make_static_text(self, "Position offset X:")
        self.annotation_label_offset_x = wx.SpinCtrlDouble(self, wx.ID_ANY, inc=5, min=-100, max=100, size=(50, -1))
        self.annotation_label_offset_x.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        annotation_label_offset_y = make_static_text(self, "Position offset Y:")
        self.annotation_label_offset_y = wx.SpinCtrlDouble(self, wx.ID_ANY, min=-100, max=100, inc=5, size=(50, -1))
        self.annotation_label_offset_y.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        annotation_label_rotation = make_static_text(self, "Label rotation:")
        self.annotation_label_rotation = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=180, inc=45, size=(50, -1))
        self.annotation_label_rotation.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        annotation_label_fontsize = make_static_text(self, "Font size:")
        self.annotation_label_fontsize = wx.SpinCtrlDouble(self, wx.ID_ANY, min=0, max=32, inc=2, size=(50, -1))
        self.annotation_label_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.annotation_label_weight = make_checkbox(self, "bold")
        self.annotation_label_weight.Bind(wx.EVT_CHECKBOX, self.on_apply)

        annotation_label_font_color_btn = make_static_text(self, "Font color:")
        self.annotation_label_font_color_btn = wx.Button(
            self, wx.ID_ANY, "", size=wx.Size(26, 26), name="annotation_color"
        )
        self.annotation_label_font_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        annotation_patch_show = make_static_text(self, "Add patch to peaks:")
        self.annotation_patch_show = wx.CheckBox(self, -1, "", (15, 30))
        self.annotation_patch_show.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.annotation_patch_show.SetToolTip(
            wx.ToolTip("A rectangular-shaped patch will be added to the spectrum to highlight selected peaks")
        )

        annotation_patch_transparency = make_static_text(self, "Patch transparency:")
        self.annotation_patch_transparency = wx.SpinCtrlDouble(self, wx.ID_ANY, inc=0.25, min=0, max=1, size=(50, -1))
        self.annotation_patch_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(annotation_label_show, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.annotation_label_show, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_label_add_to_peak, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.annotation_label_add_to_peak, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_label_offset_x, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.annotation_label_offset_x, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_label_offset_y, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.annotation_label_offset_y, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_label_rotation, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.annotation_label_rotation, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_label_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.annotation_label_fontsize, (n, 1), flag=wx.EXPAND)
        grid.Add(self.annotation_label_weight, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_label_font_color_btn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.annotation_label_font_color_btn, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_patch_show, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.annotation_patch_show, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(annotation_patch_transparency, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.annotation_patch_transparency, (n, 1), flag=wx.EXPAND)

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

        # # update configuration and button color
        # if source == "1d.marker.fill":
        #     CONFIG.marker_fill_color = color_1
        #     self.plot1d_marker_color_btn.SetBackgroundColour(color_255)

    def on_apply(self, evt):
        """Apply other parameters"""
        if self.import_evt:
            return
        self._parse_evt(evt)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.import_evt = False


if __name__ == "__main__":

    def _main():
        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                self.scrolledPanel = PanelAnnotationSettings(self, None)

        app = wx.App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
