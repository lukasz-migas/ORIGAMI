"""Legend panel"""
# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.config.config import CONFIG
from origami.utils.converters import str2num
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.views.view_register import VIEW_REG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


class PanelRMSDMatrixSettings(PanelSettingsBase):
    """Violin settings"""

    rmsd_x_rotation_value, rmsd_y_rotation_value, rmsd_add_labels_check = None, None, None
    rmsd_matrix_fontsize, rmsd_matrix_color_fmt, rmsd_matrix_font_color_btn = None, None, None
    rmsd_matrix_font_weight_check = None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""
        rmsd_x_rotation = wx.StaticText(self, -1, "Tick rotation (x):")
        self.rmsd_x_rotation_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.rmsd_rotation_x),
            min=0,
            max=360,
            initial=0,
            inc=45,
            size=(90, -1),
            name="rmsd_matrix.ticks",
        )
        self.rmsd_x_rotation_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.rmsd_x_rotation_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        rmsd_y_rotation = wx.StaticText(self, -1, "Tick rotation (y):")
        self.rmsd_y_rotation_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.rmsd_rotation_y),
            min=0,
            max=360,
            initial=0,
            inc=45,
            size=(90, -1),
            name="rmsd_matrix.ticks",
        )
        self.rmsd_y_rotation_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.rmsd_y_rotation_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        rmsd_add_labels_label = wx.StaticText(self, -1, "Show values:")
        self.rmsd_add_labels_check = make_checkbox(self, "", name="rmsd_matrix.label")
        self.rmsd_add_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.rmsd_add_labels_check.Bind(wx.EVT_CHECKBOX, self.on_update_style)
        self.rmsd_add_labels_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        rmsd_matrix_fontsize = wx.StaticText(self, -1, "Label font size:")
        self.rmsd_matrix_fontsize = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.axes_label_font_size),
            min=0,
            max=48,
            initial=CONFIG.axes_label_font_size,
            inc=2,
            size=(90, -1),
            name="rmsd_matrix.label",
        )
        self.rmsd_matrix_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.rmsd_matrix_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        self.rmsd_matrix_font_weight_check = make_checkbox(self, "Bold", name="rmsd_matrix.label")
        self.rmsd_matrix_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.rmsd_matrix_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update_style)

        rmsd_matrix_color_fmt = wx.StaticText(self, -1, "Color formatter:")
        self.rmsd_matrix_color_fmt = wx.Choice(
            self, -1, choices=CONFIG.rmsd_matrix_font_color_fmt_choices, size=(-1, -1), name="rmsd_matrix.label"
        )
        self.rmsd_matrix_color_fmt.Bind(wx.EVT_CHOICE, self.on_apply)
        self.rmsd_matrix_color_fmt.Bind(wx.EVT_CHOICE, self.on_toggle_controls)
        self.rmsd_matrix_color_fmt.Bind(wx.EVT_CHOICE, self.on_update_style)

        rmsd_matrix_font_color = wx.StaticText(self, -1, "Labels color:")
        self.rmsd_matrix_font_color_btn = wx.Button(
            self, -1, "", wx.DefaultPosition, wx.Size(26, 26), name="rmsd_matrix.label"
        )
        self.rmsd_matrix_font_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        grid = wx.GridBagSizer(2, 2)
        # rmsd controls
        n = 0
        grid.Add(rmsd_x_rotation, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_x_rotation_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_y_rotation, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_y_rotation_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_add_labels_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_add_labels_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_matrix_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_matrix_fontsize, (n, 1), flag=wx.EXPAND)
        grid.Add(self.rmsd_matrix_font_weight_check, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_matrix_color_fmt, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_matrix_color_fmt, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_matrix_font_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_matrix_font_color_btn, (n, 1), flag=wx.ALIGN_LEFT)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_update_style(self, evt):
        """Update 1d plots"""
        evt, source = self._preparse_evt(evt)
        if evt is None:
            return
        if not source.startswith("rmsd_matrix"):
            self._parse_evt(evt)
            return
        self.on_apply(None)

        try:
            view = VIEW_REG.view
            view.update_style(source)
        except (AttributeError, KeyError):
            LOGGER.warning("Could not retrieve view - cannot update plot style")
        self._parse_evt(evt)

    def on_apply(self, evt):
        """Apply other parameters"""
        if self.import_evt:
            return

        CONFIG.rmsd_rotation_x = str2num(self.rmsd_x_rotation_value.GetValue())
        CONFIG.rmsd_rotation_y = str2num(self.rmsd_y_rotation_value.GetValue())
        CONFIG.rmsd_matrix_add_labels = self.rmsd_add_labels_check.GetValue()
        CONFIG.rmsd_matrix_font_color_fmt = self.rmsd_matrix_color_fmt.GetStringSelection()
        CONFIG.rmsd_matrix_font_weight = self.rmsd_matrix_font_weight_check.GetValue()
        CONFIG.rmsd_matrix_font_size = self.rmsd_matrix_fontsize.GetValue()

        self._parse_evt(evt)

    def on_toggle_controls(self, evt):
        """Update RMSD settings"""
        CONFIG.rmsd_matrix_add_labels = self.rmsd_add_labels_check.GetValue()
        self.rmsd_matrix_color_fmt.Enable(CONFIG.rmsd_matrix_add_labels)
        self.rmsd_matrix_font_weight_check.Enable(CONFIG.rmsd_matrix_add_labels)
        self.rmsd_matrix_fontsize.Enable(CONFIG.rmsd_matrix_add_labels)
        self.rmsd_matrix_font_color_btn.Enable(CONFIG.rmsd_matrix_add_labels)

        CONFIG.rmsd_matrix_font_color_fmt = self.rmsd_matrix_color_fmt.GetStringSelection()
        self.rmsd_matrix_font_color_btn.Enable(
            CONFIG.rmsd_matrix_font_color_fmt != "auto" and CONFIG.rmsd_matrix_add_labels
        )

        self._parse_evt(evt)

    def on_assign_color(self, evt):
        """Update color"""

        # get color
        source, color_255, color_1 = self._on_assign_color(evt)

        # update configuration and button color
        if source == "rmsd_matrix.label":
            CONFIG.rmsd_matrix_font_color = color_1
            self.rmsd_matrix_font_color_btn.SetBackgroundColour(color_255)
            self.on_update_style(evt)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.rmsd_x_rotation_value.SetValue(CONFIG.rmsd_rotation_x)
        self.rmsd_y_rotation_value.SetValue(CONFIG.rmsd_rotation_y)
        self.rmsd_add_labels_check.SetValue(CONFIG.rmsd_matrix_add_labels)
        self.rmsd_matrix_fontsize.SetValue(CONFIG.axes_label_font_size)
        self.rmsd_matrix_font_weight_check.SetValue(CONFIG.axes_label_font_weight)
        self.rmsd_matrix_color_fmt.SetStringSelection(CONFIG.rmsd_matrix_font_color_fmt)
        self.rmsd_matrix_font_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.rmsd_matrix_font_color))
        self.import_evt = False


def _main():
    # Local imports
    from origami.app import App

    class _TestFrame(wx.Frame):
        def __init__(self):
            wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
            self.scrolledPanel = PanelRMSDMatrixSettings(self, None)

    app = App()
    ex = _TestFrame()
    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
