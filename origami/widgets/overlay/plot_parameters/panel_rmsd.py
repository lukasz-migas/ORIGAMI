"""Legend panel"""
# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.config.config import CONFIG
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.views.view_register import VIEW_REG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


class PanelRMSDSettings(PanelSettingsBase):
    """Violin settings"""

    rmsd_position_value, rmsd_x_position_value, rmsd_y_position_value = None, None, None
    rmsd_fontsize_value, rmsd_font_weight_check, rmsd_color_btn = None, None, None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""
        rmsd_position_label = wx.StaticText(self, -1, "Position:")
        self.rmsd_position_value = wx.Choice(
            self, -1, choices=CONFIG.rmsd_label_position_choices, size=(-1, -1), name="rmsd.label"
        )
        self.rmsd_position_value.Bind(wx.EVT_CHOICE, self.on_toggle_controls)
        self.rmsd_position_value.Bind(wx.EVT_CHOICE, self.on_apply)
        self.rmsd_position_value.Bind(wx.EVT_CHOICE, self.on_update_style)

        rmsd_x_position = wx.StaticText(self, -1, "Position x:")
        self.rmsd_x_position_value = wx.SpinCtrlDouble(
            self, -1, value=str(), min=0, max=100, initial=0, inc=5, size=(90, -1), name="rmsd.label"
        )
        self.rmsd_x_position_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        rmsd_y_position = wx.StaticText(self, -1, "Position y:")
        self.rmsd_y_position_value = wx.SpinCtrlDouble(
            self, -1, value=str(), min=0, max=100, initial=0, inc=5, size=(90, -1), name="rmsd.label"
        )
        self.rmsd_y_position_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        rmsd_fontsize = wx.StaticText(self, -1, "Label size:")
        self.rmsd_fontsize_value = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.rmsd_label_font_size),
            min=1,
            max=50,
            initial=0,
            inc=1,
            size=(90, -1),
            name="rmsd.label",
        )
        self.rmsd_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.rmsd_fontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_update_style)

        self.rmsd_font_weight_check = make_checkbox(self, "Bold", name="rmsd.label")
        self.rmsd_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.rmsd_font_weight_check.Bind(wx.EVT_CHECKBOX, self.on_update_style)

        rmsd_color_label = wx.StaticText(self, -1, "Label color:")
        self.rmsd_color_btn = wx.Button(self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="rmsd.label")
        self.rmsd_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        grid = wx.GridBagSizer(2, 2)
        # rmsd controls
        n = 0
        grid.Add(rmsd_position_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_position_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_x_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_x_position_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_y_position, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_y_position_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_fontsize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_fontsize_value, (n, 1), flag=wx.EXPAND)
        grid.Add(self.rmsd_font_weight_check, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(rmsd_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.rmsd_color_btn, (n, 1), flag=wx.ALIGN_LEFT)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_apply(self, evt):
        """Apply other parameters"""
        if self.import_evt:
            return

        # rmsd
        CONFIG.rmsd_label_position = self.rmsd_position_value.GetStringSelection()
        CONFIG.rmsd_label_font_size = str2num(self.rmsd_fontsize_value.GetValue())
        CONFIG.rmsd_label_font_weight = self.rmsd_font_weight_check.GetValue()

        self._parse_evt(evt)

    def _recalculate_rmsd_position(self, evt):
        if self.import_evt:
            return

        CONFIG.rmsd_label_position = self.rmsd_position_value.GetStringSelection()
        rmsd_dict = {
            "bottom left": [5, 5],
            "bottom right": [75, 5],
            "top left": [5, 90],
            "top right": [75, 90],
            "none": (None, None),
            "other": [str2int(self.rmsd_x_position_value.GetValue()), str2int(self.rmsd_y_position_value.GetValue())],
        }
        CONFIG.rmsd_location = rmsd_dict[CONFIG.rmsd_label_position]

        if CONFIG.rmsd_location != (None, None):
            self.rmsd_x_position_value.SetValue(CONFIG.rmsd_location[0])
            self.rmsd_y_position_value.SetValue(CONFIG.rmsd_location[1])

        self._parse_evt(evt)

    def on_toggle_controls(self, evt):
        """Update RMSD settings"""
        CONFIG.rmsd_label_position = self.rmsd_position_value.GetStringSelection()
        self.rmsd_x_position_value.Enable(CONFIG.rmsd_label_position == "other")
        self.rmsd_y_position_value.Enable(CONFIG.rmsd_label_position == "other")

        self._parse_evt(evt)

    def on_assign_color(self, evt):
        """Update color"""
        # get color
        source, color_255, color_1 = self._on_assign_color(evt)

        # update configuration and button color
        if source == "rmsd.label":
            CONFIG.rmsd_color = color_1
            self.rmsd_color_btn.SetBackgroundColour(color_255)
            self.on_update_style(evt)

    def on_update_style(self, evt):
        """Update 1d plots"""
        evt, source = self._preparse_evt(evt)
        if evt is None:
            return
        if not source.startswith("rmsd"):
            self._parse_evt(evt)
            return
        self.on_apply(None)
        self._recalculate_rmsd_position(None)

        try:
            view = VIEW_REG.view
            view.update_style(source)
        except (AttributeError, KeyError):
            LOGGER.warning("Could not retrieve view - cannot update plot style")
        self._parse_evt(evt)

    def _on_set_config(self):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.rmsd_position_value.SetStringSelection(CONFIG.rmsd_label_position)
        self.rmsd_fontsize_value.SetValue(CONFIG.rmsd_label_font_size)
        self.rmsd_font_weight_check.SetValue(CONFIG.rmsd_label_font_weight)
        self.rmsd_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.rmsd_color))
        self.import_evt = False


def _main():

    from origami.app import App

    class _TestFrame(wx.Frame):
        def __init__(self):
            wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
            self.scrolledPanel = PanelRMSDSettings(self, None)

    app = App()
    ex = _TestFrame()
    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
