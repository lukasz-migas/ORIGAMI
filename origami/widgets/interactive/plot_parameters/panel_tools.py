"""Legend panel"""
# Standard library imports
from typing import Dict

# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_static_text
from origami.widgets.interactive.plot_parameters.panel_base import PanelSettingsBase


class PanelToolsSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    bokeh_tools_position, bokeh_tools_save, bokeh_tools_reset = None, None, None
    bokeh_tools_hover, bokeh_tools_crosshair, bokeh_tools_pan_xy, bokeh_tools_pan_x = None, None, None, None
    bokeh_tools_pan_y, bokeh_tools_boxzoom_xy, bokeh_tools_boxzoom_x, bokeh_tools_boxzoom_y = None, None, None, None
    bokeh_tools_wheel, bokeh_tools_wheel_choice, bokeh_tools_active_wheel, bokeh_tools_active_drag = (
        None,
        None,
        None,
        None,
    )
    bokeh_tools_active_inspect = None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        tools_position_choice = make_static_text(self, "Position:")
        self.bokeh_tools_position = wx.ComboBox(self, style=wx.CB_READONLY, choices=["above", "right", "below", "left"])
        self.bokeh_tools_position.SetToolTip(wx.ToolTip("Position of the toolbar."))
        self.bokeh_tools_position.Bind(wx.EVT_COMBOBOX, self.on_apply)

        self.bokeh_tools_save = make_checkbox(self, "Save", name="save")
        self.bokeh_tools_save.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_tools_reset = make_checkbox(self, "Reset", name="reset")
        self.bokeh_tools_reset.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_tools_hover = make_checkbox(self, "Hover", name="hover")
        self.bokeh_tools_hover.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_tools_crosshair = make_checkbox(self, "Crosshair", name="crosshair")
        self.bokeh_tools_crosshair.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_tools_pan_xy = make_checkbox(self, "Pan (xy)", name="pan")
        self.bokeh_tools_pan_xy.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_tools_pan_x = make_checkbox(self, "Pan (x)", name="xpan")
        self.bokeh_tools_pan_x.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_tools_pan_y = make_checkbox(self, "Pan (y)", name="ypan")
        self.bokeh_tools_pan_y.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_tools_boxzoom_xy = make_checkbox(self, "Box zoom (xy)", name="box_zoom")
        self.bokeh_tools_boxzoom_xy.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_tools_boxzoom_x = make_checkbox(self, "Box zoom (x)", name="xbox_zoom")
        self.bokeh_tools_boxzoom_x.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_tools_boxzoom_y = make_checkbox(self, "Box zoom (y)", name="ybox_zoom")
        self.bokeh_tools_boxzoom_y.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.bokeh_tools_wheel = make_checkbox(self, "Wheel", name="wheel_zoom")
        self.bokeh_tools_wheel.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.bokeh_tools_wheel_choice = wx.ComboBox(
            self, style=wx.CB_READONLY, choices=CONFIG.bokeh_tools_wheel_choices
        )
        self.bokeh_tools_wheel_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)

        tools_active_wheel_choice = make_static_text(self, "Active wheel:")
        self.bokeh_tools_active_wheel = wx.ComboBox(
            self, style=wx.CB_READONLY, choices=CONFIG.bokeh_tools_active_wheel_choices
        )
        self.bokeh_tools_active_wheel.Bind(wx.EVT_COMBOBOX, self.on_apply)

        tools_active_drag_choice = make_static_text(self, "Active drag:")
        self.bokeh_tools_active_drag = wx.ComboBox(
            self, style=wx.CB_READONLY, choices=CONFIG.bokeh_tools_active_drag_choices
        )
        self.bokeh_tools_active_drag.Bind(wx.EVT_COMBOBOX, self.on_apply)

        tools_active_inspect_choice = make_static_text(self, "Active inspect:")
        self.bokeh_tools_active_inspect = wx.ComboBox(
            self, style=wx.CB_READONLY, choices=CONFIG.bokeh_tools_active_inspect_choices
        )
        self.bokeh_tools_active_inspect.Bind(wx.EVT_COMBOBOX, self.on_apply)

        tools_check_default_btn = wx.Button(self, wx.ID_ANY, "Check defaults", size=(-1, -1))
        tools_check_default_btn.Bind(wx.EVT_BUTTON, self.on_check_defaults)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(tools_position_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_tools_position, (n, 1), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_tools_save, (n, 1), flag=wx.EXPAND)
        grid.Add(self.bokeh_tools_reset, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_tools_hover, (n, 1), flag=wx.EXPAND)
        grid.Add(self.bokeh_tools_crosshair, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_tools_pan_xy, (n, 1), flag=wx.EXPAND)
        grid.Add(self.bokeh_tools_boxzoom_xy, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_tools_pan_x, (n, 1), flag=wx.EXPAND)
        grid.Add(self.bokeh_tools_boxzoom_x, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_tools_pan_y, (n, 1), flag=wx.EXPAND)
        grid.Add(self.bokeh_tools_boxzoom_y, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.bokeh_tools_wheel, (n, 1), flag=wx.EXPAND)
        grid.Add(self.bokeh_tools_wheel_choice, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(tools_active_wheel_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_tools_active_wheel, (n, 1), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(tools_active_drag_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_tools_active_drag, (n, 1), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(tools_active_inspect_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bokeh_tools_active_inspect, (n, 1), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(tools_check_default_btn, (n, 1), (1, 1), flag=wx.EXPAND)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER, 2)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def on_toggle_controls(self, evt):
        """Toggle controls"""
        # wheel
        check_wheel = self.bokeh_tools_wheel.GetValue()
        self.bokeh_tools_wheel_choice.Enable(check_wheel)
        self.bokeh_tools_active_wheel.Enable(check_wheel)
        self._parse_evt(evt)

    def on_check_defaults(self, _evt):
        """Check default tools"""
        for tool in [
            self.bokeh_tools_save,
            self.bokeh_tools_reset,
            self.bokeh_tools_hover,
            self.bokeh_tools_boxzoom_xy,
            self.bokeh_tools_wheel,
        ]:
            tool.SetValue(True)

        for tool in [
            self.bokeh_tools_crosshair,
            self.bokeh_tools_pan_x,
            self.bokeh_tools_pan_y,
            self.bokeh_tools_pan_xy,
            self.bokeh_tools_boxzoom_x,
            self.bokeh_tools_boxzoom_y,
        ]:
            tool.SetValue(False)
        self.on_toggle_controls(_evt)

    def get_config(self) -> Dict:
        """Get configuration data"""
        if self.import_evt:
            return dict()
        return {
            "bokeh_tools_position": self.bokeh_tools_position.GetStringSelection(),
            "bokeh_tools_save": self.bokeh_tools_save.GetValue(),
            "bokeh_tools_reset": self.bokeh_tools_reset.GetValue(),
            "bokeh_tools_hover": self.bokeh_tools_hover.GetValue(),
            "bokeh_tools_crosshair": self.bokeh_tools_crosshair.GetValue(),
            "bokeh_tools_pan_xy": self.bokeh_tools_pan_xy.GetValue(),
            "bokeh_tools_pan_x": self.bokeh_tools_pan_x.GetValue(),
            "bokeh_tools_pan_y": self.bokeh_tools_pan_y.GetValue(),
            "bokeh_tools_boxzoom_xy": self.bokeh_tools_boxzoom_xy.GetValue(),
            "bokeh_tools_boxzoom_x": self.bokeh_tools_boxzoom_x.GetValue(),
            "bokeh_tools_boxzoom_y": self.bokeh_tools_boxzoom_y.GetValue(),
            "bokeh_tools_wheel": self.bokeh_tools_wheel.GetValue(),
            "bokeh_tools_wheel_choice": self.bokeh_tools_wheel_choice.GetStringSelection(),
            "bokeh_tools_active_drag": self.bokeh_tools_active_drag.GetStringSelection(),
            "bokeh_tools_active_wheel": self.bokeh_tools_active_wheel.GetStringSelection(),
            "bokeh_tools_active_inspect": self.bokeh_tools_active_inspect.GetStringSelection(),
        }

    def _on_set_config(self, config):
        """Update values in the application based on config values"""
        self.import_evt = True
        self.bokeh_tools_position.SetStringSelection(config.get("bokeh_tools_position", CONFIG.bokeh_tools_position))
        self.bokeh_tools_save.SetValue(config.get("bokeh_tools_save", CONFIG.bokeh_tools_save))
        self.bokeh_tools_reset.SetValue(config.get("bokeh_tools_reset", CONFIG.bokeh_tools_reset))
        self.bokeh_tools_hover.SetValue(config.get("bokeh_tools_hover", CONFIG.bokeh_tools_hover))
        self.bokeh_tools_crosshair.SetValue(config.get("bokeh_tools_crosshair", CONFIG.bokeh_tools_crosshair))
        self.bokeh_tools_pan_xy.SetValue(config.get("bokeh_tools_pan_xy", CONFIG.bokeh_tools_pan_xy))
        self.bokeh_tools_pan_x.SetValue(config.get("bokeh_tools_pan_x", CONFIG.bokeh_tools_pan_x))
        self.bokeh_tools_pan_y.SetValue(config.get("bokeh_tools_pan_y", CONFIG.bokeh_tools_pan_y))
        self.bokeh_tools_boxzoom_xy.SetValue(config.get("bokeh_tools_boxzoom_xy", CONFIG.bokeh_tools_boxzoom_xy))
        self.bokeh_tools_boxzoom_x.SetValue(config.get("bokeh_tools_boxzoom_x", CONFIG.bokeh_tools_boxzoom_x))
        self.bokeh_tools_boxzoom_y.SetValue(config.get("bokeh_tools_boxzoom_y", CONFIG.bokeh_tools_boxzoom_y))
        self.bokeh_tools_wheel.SetValue(config.get("bokeh_tools_wheel", CONFIG.bokeh_tools_wheel))
        self.bokeh_tools_wheel_choice.SetStringSelection(
            config.get("bokeh_tools_wheel_choice", CONFIG.bokeh_tools_wheel_choice)
        )
        self.bokeh_tools_active_drag.SetStringSelection(
            config.get("bokeh_tools_active_drag", CONFIG.bokeh_tools_active_drag)
        )
        self.bokeh_tools_active_wheel.SetStringSelection(
            config.get("bokeh_tools_active_wheel", CONFIG.bokeh_tools_active_wheel)
        )
        self.bokeh_tools_active_inspect.SetStringSelection(
            config.get("bokeh_tools_active_inspect", CONFIG.bokeh_tools_active_inspect)
        )
        self.import_evt = False


if __name__ == "__main__":

    def _main():
        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                self.scrolledPanel = PanelToolsSettings(self, None)

        app = wx.App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
