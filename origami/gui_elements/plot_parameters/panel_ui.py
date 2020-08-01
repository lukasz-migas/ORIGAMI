"""Legend panel"""
# Standard library imports
import logging

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.ids import ID_extraSettings_logging
from origami.ids import ID_extraSettings_autoSaveSettings
from origami.styles import make_checkbox
from origami.styles import set_item_font
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.color import convert_rgb_1_to_hex
from origami.config.config import CONFIG
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase

LOGGER = logging.getLogger(__name__)


class PanelUISettings(PanelSettingsBase):
    """Violin settings"""

    zoom_normal_color_btn, zoom_extract_color_btn = None, None
    general_log_to_file_check, general_auto_save_check = None, None

    def make_panel(self):
        """Make UI behaviour panel"""
        zoom_zoom_vertical_color_label = wx.StaticText(self, -1, "Drag color (normal):")
        self.zoom_normal_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="zoom.drag.normal"
        )
        self.zoom_normal_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.zoom_color_normal))  # noqa
        self.zoom_normal_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        zoom_zoom_horizontal_color_label = wx.StaticText(self, -1, "Drag color (extract):")
        self.zoom_extract_color_btn = wx.Button(
            self, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0, name="zoom.drag.extract"
        )
        self.zoom_extract_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.zoom_color_extract))  # noqa
        self.zoom_extract_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        general_log_to_file_check = wx.StaticText(self, -1, "Log events to file:")
        self.general_log_to_file_check = make_checkbox(self, "", evt_id=ID_extraSettings_logging)
        self.general_log_to_file_check.SetValue(CONFIG.logging)
        self.general_log_to_file_check.Bind(wx.EVT_CHECKBOX, self.on_update_states)

        general_auto_save_check = wx.StaticText(self, -1, "Auto-save settings:")
        self.general_auto_save_check = make_checkbox(self, "", evt_id=ID_extraSettings_autoSaveSettings)
        self.general_auto_save_check.SetValue(CONFIG.autoSaveSettings)
        self.general_auto_save_check.Bind(wx.EVT_CHECKBOX, self.on_update_states)

        usage_parameters_label = wx.StaticText(self, -1, "In-plot interactivity parameters")
        set_item_font(usage_parameters_label)

        ui_parameters_label = wx.StaticText(self, -1, "Graphical User Interface parameters")
        set_item_font(ui_parameters_label)

        n_col = 3
        grid = wx.GridBagSizer(2, 2)
        # interaction parameters
        n = 0
        grid.Add(usage_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(zoom_zoom_vertical_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.zoom_normal_color_btn, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(zoom_zoom_horizontal_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.zoom_extract_color_btn, (n, 1), flag=wx.ALIGN_LEFT)
        # gui parameters
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(ui_parameters_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(general_log_to_file_check, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.general_log_to_file_check, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(general_auto_save_check, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.general_auto_save_check, (n, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_apply(self, evt):
        """Apply zoom parameters"""
        if self.import_evt:
            return
        self._parse_evt(evt)

    def on_update_states(self, evt):
        """Update states"""
        if self.import_evt:
            return

        evt_id = evt.GetId()

        CONFIG.logging = self.general_log_to_file_check.GetValue()
        CONFIG.autoSaveSettings = self.general_auto_save_check.GetValue()

        if evt_id == ID_extraSettings_autoSaveSettings:
            on_off = "enabled" if CONFIG.autoSaveSettings else "disabled"
            msg = f"Auto-saving of settings was `{on_off}`"
        elif evt_id == ID_extraSettings_logging:
            on_off = "enabled" if CONFIG.logging else "disabled"
            msg = f"Logging to file was `{on_off}`"
        else:
            return

        pub.sendMessage("notify.message.info", message=msg)
        LOGGER.info(msg)
        self._parse_evt(evt)

    def on_assign_color(self, evt):
        """Update color"""

        # get color
        source, color_255, color_1 = self._on_assign_color(evt)

        # update configuration and button color
        if source == "zoom.drag.normal":
            CONFIG.zoom_color_normal = color_1
            self.zoom_normal_color_btn.SetBackgroundColour(color_255)
        elif source == "zoom.drag.extract":
            CONFIG.zoom_color_extract = color_1
            self.zoom_extract_color_btn.SetBackgroundColour(color_255)

        pub.sendMessage(
            "zoom.parameters",
            plot_parameters=dict(
                normal=convert_rgb_1_to_hex(CONFIG.zoom_color_normal),
                extract=convert_rgb_1_to_hex(CONFIG.zoom_color_extract),
            ),
        )
