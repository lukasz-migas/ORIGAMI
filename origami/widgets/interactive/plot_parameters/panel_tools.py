"""Legend panel"""
# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_static_text
from origami.gui_elements.plot_parameters.panel_base import PanelSettingsBase


class PanelToolsSettings(PanelSettingsBase):
    """General settings"""

    # ui elements
    tools_position_choice, tools_check_all, tools_save_check, tools_reset_check = None, None, None, None
    tools_hover_check, tools_crosshair_check, tools_pan_xy_check, tools_pan_x_check = None, None, None, None
    tools_pan_y_check, tools_boxzoom_xy_check, tools_boxzoom_x_check, tools_boxzoom_y_check = None, None, None, None
    tools_wheel_check, tools_wheel_choice, tools_active_wheel_choice, tools_active_drag_choice = None, None, None, None
    tools_active_inspect_choice = None

    def __init__(self, parent, view):
        PanelSettingsBase.__init__(self, parent, view)

    def make_panel(self):
        """Make RMSD/RMSF/Matrix panel"""

        tools_position_choice = make_static_text(self, "Position:")
        self.tools_position_choice = wx.ComboBox(
            self, style=wx.CB_READONLY, choices=["above", "right", "below", "left"]
        )
        self.tools_position_choice.SetToolTip(wx.ToolTip("Position of the toolbar."))
        self.tools_position_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)

        tools_check_all = make_static_text(self, "Check defaults:")
        self.tools_check_all = make_checkbox(self, "")
        # self.tools_check_all.Bind(wx.EVT_CHECKBOX, self.onCheck_tools)

        self.tools_save_check = make_checkbox(self, "Save", name="save")
        self.tools_save_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.tools_reset_check = make_checkbox(self, "Reset", name="reset")
        self.tools_reset_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.tools_hover_check = make_checkbox(self, "Hover", name="hover")
        self.tools_hover_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.tools_crosshair_check = make_checkbox(self, "Crosshair", name="crosshair")
        self.tools_crosshair_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.tools_pan_xy_check = make_checkbox(self, "Pan (both)", name="pan")
        self.tools_pan_xy_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.tools_pan_x_check = make_checkbox(self, "Pan (horizontal)", name="xpan")
        self.tools_pan_x_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.tools_pan_y_check = make_checkbox(self, "Pan (vertical)", name="ypan")
        self.tools_pan_y_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.tools_boxzoom_xy_check = make_checkbox(self, "Box zoom (both)", name="box_zoom")
        self.tools_boxzoom_xy_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.tools_boxzoom_x_check = make_checkbox(self, "Box zoom (horizontal)", name="xbox_zoom")
        self.tools_boxzoom_x_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.tools_boxzoom_y_check = make_checkbox(self, "Box zoom (vertical)", name="ybox_zoom")
        self.tools_boxzoom_y_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.tools_wheel_check = make_checkbox(self, "Wheel", name="wheel_zoom")
        self.tools_wheel_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.tools_wheel_choice = wx.ComboBox(
            self,
            style=wx.CB_READONLY,
            choices=["Wheel zoom (both)", "Wheel zoom (horizontal)", "Wheel zoom (vertical)"],
        )
        self.tools_wheel_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)

        tools_active_wheel_choice = make_static_text(self, "Active wheel:")
        self.tools_active_wheel_choice = wx.ComboBox(
            self, style=wx.CB_READONLY, choices=CONFIG.bokeh_tools_active_wheel_choices
        )
        self.tools_active_wheel_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)

        tools_active_drag_choice = make_static_text(self, "Active drag:")
        self.tools_active_drag_choice = wx.ComboBox(
            self, style=wx.CB_READONLY, choices=CONFIG.bokeh_tools_active_drag_choices
        )
        self.tools_active_drag_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)

        tools_active_inspect_choice = make_static_text(self, "Active inspect:")
        self.tools_active_inspect_choice = wx.ComboBox(
            self, style=wx.CB_READONLY, choices=CONFIG.bokeh_tools_active_inspect_choices
        )
        self.tools_active_inspect_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(tools_position_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.tools_position_choice, (n, 1), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(tools_check_all, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.tools_check_all, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(self.tools_save_check, (n, 1), flag=wx.EXPAND)
        grid.Add(self.tools_reset_check, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.tools_hover_check, (n, 1), flag=wx.EXPAND)
        grid.Add(self.tools_crosshair_check, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.tools_pan_xy_check, (n, 1), flag=wx.EXPAND)
        grid.Add(self.tools_boxzoom_xy_check, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.tools_pan_x_check, (n, 1), flag=wx.EXPAND)
        grid.Add(self.tools_boxzoom_x_check, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.tools_pan_y_check, (n, 1), flag=wx.EXPAND)
        grid.Add(self.tools_boxzoom_y_check, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(self.tools_wheel_check, (n, 1), flag=wx.EXPAND)
        grid.Add(self.tools_wheel_choice, (n, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(tools_active_wheel_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.tools_active_wheel_choice, (n, 1), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(tools_active_drag_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.tools_active_drag_choice, (n, 1), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(tools_active_inspect_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.tools_active_inspect_choice, (n, 1), (1, 2), flag=wx.EXPAND)

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
                self.scrolledPanel = PanelToolsSettings(self, None)

        app = wx.App()

        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
