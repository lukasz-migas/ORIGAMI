# Standard library imports
import re
from copy import deepcopy
from time import time as ttime

# Third-party imports
import wx

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_staticbox
from origami.gui_elements.helpers import make_static_text


class PanelCustomiseInteractivePlot(wx.MiniFrame):
    """
    Panel where you can customise interactive plots
    """

    def __init__(self, presenter, parent, config, icons, **kwargs):
        wx.MiniFrame.__init__(
            self,
            parent,
            -1,
            "Customise interactive plot...",
            size=(-1, -1),
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER,
        )
        tstart = ttime()
        self._loading_ = True
        self.presenter = presenter
        self.parent = parent
        self.config = config
        self.icons = icons

        # retrieve data from kwargs
        self.data = kwargs.pop("data")
        self.document_title = kwargs.pop("document_title")
        self.item_type = kwargs.pop("item_type")
        self.item_title = kwargs.pop("item_title")
        self.kwargs = deepcopy(self.data.get("interactive_params", {}))

        self._checkInteractiveParameters()

        # make gui items
        self.make_gui()
        self.Layout()
        self.SetSize((521, 550))
        self.SetMinSize((521, 550))
        self.SetFocus()

        # bind
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

        self.onEnableDisable_widgets(None)

        self._loading_ = False

        self.parent.onUpdateItemParameters(self.document_title, self.item_type, self.item_title, self.kwargs)

        msg = "Customising parameters of: {} - {} - {}. Startup took {:.3f} seconds".format(
            self.document_title, self.item_type, self.item_title, ttime() - tstart
        )
        print(msg)

    def on_key_event(self, evt):
        """Respond to key press"""
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)

        if evt is not None:
            evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def _checkInteractiveParameters(self):

        if "widgets" not in self.kwargs:
            self.kwargs["widgets"] = {}

        if "tools" not in self.kwargs:
            self.kwargs["tools"] = {}

        if "preprocessing_properties" not in self.kwargs:
            self.kwargs["preprocessing_properties"] = {}

        if "plot_properties" not in self.kwargs:
            self.kwargs["plot_properties"] = {}

        if "legend_properties" not in self.kwargs:
            self.kwargs["legend_properties"] = {}

        if "colorbar_properties" not in self.kwargs:
            self.kwargs["colorbar_properties"] = {}

        if "annotation_properties" not in self.kwargs:
            self.kwargs["annotation_properties"] = {}

        if "frame_properties" not in self.kwargs:
            self.kwargs["frame_properties"] = {}

        if "overlay_properties" not in self.kwargs:
            self.kwargs["overlay_properties"] = {}

        # plot size information
        if "plot_width" not in self.kwargs:
            self.kwargs["plot_width"] = self.config.figWidth
        if "plot_height" not in self.kwargs:
            self.kwargs["plot_height"] = self.config.figHeight

        # plot information
        if "xlimits" not in self.kwargs:
            self.kwargs["xlimits"] = None
        if "ylimits" not in self.kwargs:
            self.kwargs["ylimits"] = None

    def _check_allowed_windows(self):
        """
        Check which settings can be displayed for selected item
        """
        allowed_window = [
            "general",
            "plots",
            "tools",
            "annotations",
            "legend",
            "colorbar",
            "overlay",
            "widgets",
            "preprocess",
        ]
        remove_window_list = []

        if self.item_type in ["1D", "RT", "MS"]:
            remove_window_list = ["overlay", "colorbar"]
        elif self.item_type in ["2D"]:
            remove_window_list = ["annotations"]
        elif self.item_type in ["Overlay", "Statistical"]:
            method = re.split("-|,|:|__", self.item_title)
            if method[0] in [
                "Mask",
                "Transparent",
                "RMSD",
                "RMSF",
                "Mean",
                "Standard Deviation",
                "Variance",
                "RMSD Matrix",
            ]:
                remove_window_list = ["preprocess", "annotations"]
            elif method[0] in ["1D", "RT"]:
                remove_window_list = ["colorbar"]
        elif self.item_type in ["Annotated data"]:
            remove_window_list = ["overlay"]
        #
        for item in remove_window_list:
            try:
                allowed_window.remove(item)
            except Exception:
                pass

        #             if any(method[0] in item for item in ['Mask', 'Transparent']):
        #                 preset = 'Overlay'
        #             elif any(method[0] in item for item in ['RMSD', 'RMSF', 'Mean',
        #                                                     'Standard Deviation',
        #                                                     'Variance', 'RMSD Matrix']):
        #                 preset = '2D'
        #             elif any(method[0] in item for item in ['1D', 'RT']):
        #                 preset = '1D'

        return allowed_window

    def makeOverlayPanel_grid(self, panel):

        grid_add_labels_label = make_static_text(panel, "Add labels:")
        self.overlay_grid_show_labels = make_checkbox(panel, "")
        self.overlay_grid_show_labels.SetValue(
            self.kwargs.get("overlay_properties", {}).get("overlay_grid_add_labels", False)
        )
        self.overlay_grid_show_labels.Bind(wx.EVT_CHECKBOX, self.on_apply_overlay)

        annotation_fontSize_label = make_static_text(panel, "Font size:")
        self.overlay_grid_fontSize_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=0,
            max=32,
            inc=2,
            size=(50, -1),
            value=str(
                self.kwargs.get("overlay_properties", {}).get(
                    "grid_label_fontsize", self.config.bokeh_grid_label_font_size
                )
            ),
            initial=self.kwargs.get("overlay_properties", {}).get(
                "grid_label_fontsize", self.config.bokeh_grid_label_font_size
            ),
        )
        self.overlay_grid_fontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        self.overlay_grid_fontWeight_value = make_checkbox(panel, "bold")
        self.overlay_grid_fontWeight_value.SetValue(
            self.kwargs.get("overlay_properties", {}).get(
                "grid_label_fontweight", self.config.bokeh_grid_label_font_weight
            )
        )
        self.overlay_grid_fontWeight_value.Bind(wx.EVT_CHECKBOX, self.on_apply_overlay)

        annotation_fontColor_label = make_static_text(panel, "Font color:")
        self.overlay_grid_label_colorBtn = wx.Button(
            panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="overlay_grid_label_color"
        )
        self.overlay_grid_label_colorBtn.SetBackgroundColour(
            convert_rgb_1_to_255(
                self.kwargs.get("overlay_properties", {}).get(
                    "grid_label_color", self.config.bokeh_annotation_font_color
                )
            )
        )
        self.overlay_grid_label_colorBtn.Bind(wx.EVT_BUTTON, self.on_apply_color)

        annotation_xpos_label = make_static_text(panel, "Position offset X:")
        self.overlay_grid_xpos_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            inc=5,
            min=-100,
            max=100,
            size=(50, -1),
            value=str(
                self.kwargs.get("overlay_properties", {}).get(
                    "grid_position_offset_x", self.config.bokeh_labels_label_offset_x
                )
            ),
            initial=self.kwargs.get("overlay_properties", {}).get(
                "grid_position_offset_x", self.config.bokeh_labels_label_offset_x
            ),
        )
        self.overlay_grid_xpos_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        annotation_ypos_label = make_static_text(panel, "Position offset Y:")
        self.overlay_grid_ypos_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            min=-100,
            max=100,
            inc=5,
            size=(50, -1),
            value=str(
                self.kwargs.get("overlay_properties", {}).get(
                    "grid_position_offset_y", self.config.bokeh_labels_label_offset_y
                )
            ),
            initial=self.kwargs.get("overlay_properties", {}).get(
                "grid_position_offset_y", self.config.bokeh_labels_label_offset_y
            ),
        )
        self.overlay_grid_ypos_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        grid_staticBox = make_staticbox(panel, "Grid (NxN) parameters", size=(-1, -1), color=wx.BLACK)
        grid_staticBox.SetSize((-1, -1))
        grid_box_sizer = wx.StaticBoxSizer(grid_staticBox, wx.HORIZONTAL)
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(grid_add_labels_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.overlay_grid_show_labels, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(annotation_fontSize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.overlay_grid_fontSize_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_grid_fontWeight_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(annotation_fontColor_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.overlay_grid_label_colorBtn, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(annotation_xpos_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.overlay_grid_xpos_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(annotation_ypos_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.overlay_grid_ypos_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return grid_box_sizer

    def makeOverlayPanel_overlay(self, panel):

        overlay_layout_label = make_static_text(panel, "Layout:")
        self.overlay_layout = wx.ComboBox(
            panel,
            -1,
            style=wx.CB_READONLY,
            choices=["Rows", "Columns"],
            value=self.kwargs.get("overlay_properties", {}).get("overlay_layout", self.config.plotLayoutOverlay),
        )
        self.overlay_layout.Bind(wx.EVT_COMBOBOX, self.on_apply_overlay)
        self.overlay_layout.SetToolTip(
            wx.ToolTip(
                "Layout to be used when creating mask/transparent plot. "
                + "Currently, actual overlaying of two heatmaps is not possible"
            )
        )

        overlay_linkXY_label = make_static_text(panel, "Link XY axes:")
        self.overlay_linkXY = make_checkbox(panel, "")
        self.overlay_linkXY.SetValue(
            self.kwargs.get("overlay_properties", {}).get("overlay_link_xy", self.config.linkXYaxes)
        )
        self.overlay_linkXY.Bind(wx.EVT_CHECKBOX, self.on_apply_overlay)
        self.overlay_linkXY.SetToolTip(wx.ToolTip("Hover response when zooming/panning"))

        overlay_colormap_1_label = make_static_text(panel, "Colormap (1):")
        self.overlay_colormap_1 = wx.ComboBox(
            panel,
            -1,
            style=wx.CB_READONLY,
            choices=self.config.colormap_choices,
            value=self.kwargs.get("overlay_properties", {}).get("overlay_colormap_1", "Reds"),
        )
        self.overlay_colormap_1.Bind(wx.EVT_COMBOBOX, self.on_apply_overlay)

        overlay_colormap_2_label = make_static_text(panel, "Colormap (2):")
        self.overlay_colormap_2 = wx.ComboBox(
            panel,
            -1,
            style=wx.CB_READONLY,
            choices=self.config.colormap_choices,
            value=self.kwargs.get("overlay_properties", {}).get("overlay_colormap_2", "Blues"),
        )
        self.overlay_colormap_2.Bind(wx.EVT_COMBOBOX, self.on_apply_overlay)

        overlay_merge_tools_label = make_static_text(panel, "Merge tools:")
        self.overlay_merge_tools = make_checkbox(panel, "")
        self.overlay_merge_tools.SetValue(self.kwargs.get("overlay_properties", {}).get("overlay_merge_tools", False))
        self.overlay_merge_tools.Bind(wx.EVT_CHECKBOX, self.on_apply_overlay)
        self.overlay_merge_tools.SetToolTip(
            wx.ToolTip("Merge tools for both plots. If checked, a lot of the tools will be removed by default.")
        )

        overlay_staticBox = make_staticbox(panel, "Mask/Transparency parameters", size=(-1, -1), color=wx.BLACK)
        overlay_staticBox.SetSize((-1, -1))
        overlay_box_sizer = wx.StaticBoxSizer(overlay_staticBox, wx.HORIZONTAL)
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(overlay_layout_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.overlay_layout, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(overlay_linkXY_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.overlay_linkXY, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(overlay_colormap_1_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.overlay_colormap_1, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(overlay_colormap_2_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.overlay_colormap_2, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(overlay_merge_tools_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.overlay_merge_tools, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        overlay_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return overlay_box_sizer

    def makeOverlayPanel_multiline(self, panel):

        multiline_shade_under_label = make_static_text(panel, "Shade under line:")
        self.multiline_shade_under_value = make_checkbox(panel, "")
        self.multiline_shade_under_value.SetValue(
            self.kwargs.get("overlay_properties", {}).get("multiline_shade_under", False)
        )
        self.multiline_shade_under_value.Bind(wx.EVT_CHECKBOX, self.on_apply_overlay)

        multiline_shade_transparency_label = make_static_text(panel, "Shade transparency:")
        self.multiline_shade_transparency_value = wx.SpinCtrlDouble(
            panel,
            wx.ID_ANY,
            inc=0.25,
            min=0,
            max=1,
            size=(50, -1),
            value=str(self.kwargs.get("overlay_properties", {}).get("multiline_shade_transparency", 0.25)),
            initial=self.kwargs.get("overlay_properties", {}).get("multiline_shade_transparency", 0.25),
        )
        self.multiline_shade_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_overlay)

        grid_staticBox = make_staticbox(panel, "Multi-line parameters", size=(-1, -1), color=wx.BLACK)
        grid_staticBox.SetSize((-1, -1))
        grid_box_sizer = wx.StaticBoxSizer(grid_staticBox, wx.HORIZONTAL)
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(multiline_shade_under_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.multiline_shade_under_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(multiline_shade_transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.multiline_shade_transparency_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return grid_box_sizer

    def on_apply_tools(self, evt):
        if self._loading_:
            return

        self.kwargs["tools"]["position"] = self.tools_position_choice.GetStringSelection()
        self.kwargs["tools"]["hover"] = self.tools_hover_check.GetValue()
        self.kwargs["tools"]["pan"] = self.tools_pan_xy_check.GetValue()
        self.kwargs["tools"]["xpan"] = self.tools_pan_x_check.GetValue()
        self.kwargs["tools"]["ypan"] = self.tools_pan_y_check.GetValue()
        self.kwargs["tools"]["box_zoom"] = self.tools_boxzoom_xy_check.GetValue()
        self.kwargs["tools"]["xbox_zoom"] = self.tools_boxzoom_x_check.GetValue()
        self.kwargs["tools"]["ybox_zoom"] = self.tools_boxzoom_y_check.GetValue()
        self.kwargs["tools"]["save"] = self.tools_save_check.GetValue()
        self.kwargs["tools"]["crosshair"] = self.tools_crosshair_check.GetValue()
        self.kwargs["tools"]["reset"] = self.tools_reset_check.GetValue()
        self.kwargs["tools"]["wheel"] = self.tools_wheel_check.GetValue()
        self.kwargs["tools"]["wheel_type"] = self.tools_wheel_choice.GetStringSelection()
        if self.kwargs["tools"]["wheel"]:
            if self.kwargs["tools"]["wheel_type"] == "Wheel zoom (both)":
                self.kwargs["tools"]["wheel_zoom"] = True
                self.kwargs["tools"]["xwheel_zoom"] = False
                self.kwargs["tools"]["ywheel_zoom"] = False
            elif self.kwargs["tools"]["wheel_type"] == "Wheel zoom (horizontal)":
                self.kwargs["tools"]["wheel_zoom"] = False
                self.kwargs["tools"]["xwheel_zoom"] = True
                self.kwargs["tools"]["ywheel_zoom"] = False
            elif self.kwargs["tools"]["wheel_type"] == "Wheel zoom (vertical)":
                self.kwargs["tools"]["wheel_zoom"] = False
                self.kwargs["tools"]["xwheel_zoom"] = False
                self.kwargs["tools"]["ywheel_zoom"] = True
        else:
            self.kwargs["tools"]["wheel_zoom"] = False
            self.kwargs["tools"]["xwheel_zoom"] = False
            self.kwargs["tools"]["ywheel_zoom"] = False

        _active_replace_ = {
            "Box zoom (both)": "box_zoom",
            "Box zoom (horizontal)": "xbox_zoom",
            "Box zoom (vertical)": "ybox_zoom",
            "Pan (both)": "pan",
            "Pan (horizontal)": "xpan",
            "Wheel zoom (both)": "wheel_zoom",
            "Wheel zoom (horizontal)": "xwheel_zoom",
            "Wheel zoom (vertical)": "ywheel_zoom",
            "Pan (vertical)": "ypan",
            "auto": "auto",
            "None": None,
            "Hover": "hover",
            "Crosshair": "crosshair",
        }

        self.kwargs["tools"]["active_drag_type"] = self.tools_active_drag_choice.GetStringSelection()
        self.kwargs["tools"]["active_drag"] = _active_replace_[self.kwargs["tools"]["active_drag_type"]]
        self.kwargs["tools"]["active_inspect_type"] = self.tools_active_inspect_choice.GetStringSelection()
        self.kwargs["tools"]["active_inspect"] = _active_replace_[self.kwargs["tools"]["active_inspect_type"]]
        self.kwargs["tools"]["active_wheel_type"] = self.tools_active_wheel_choice.GetStringSelection()
        self.kwargs["tools"]["active_wheel"] = _active_replace_[self.kwargs["tools"]["active_wheel_type"]]

        # create string representation of tools
        on_tools = []
        for key in self.kwargs["tools"]:
            if key in [
                "on_tools",
                "wheel",
                "wheel_type",
                "position",
                "active_drag_type",
                "active_inspect_type",
                "active_wheel_type",
            ]:
                continue
            elif key in ["active_drag", "active_inspect", "active_wheel"]:
                active_value = self.kwargs["tools"][key]
                if active_value not in ["auto", "None", None]:
                    on_tools.append(active_value)
            elif self.kwargs["tools"][key]:
                on_tools.append(key)

        # remove duplicates
        on_tools = list(set(on_tools))

        # join together
        self.kwargs["tools"]["on_tools"] = ",".join(on_tools)

        self.on_update_document()

    def on_apply_widgets(self, evt):
        if self._loading_:
            return

        self.kwargs["widgets"]["add_custom_widgets"] = self.widgets_add_widgets.GetValue()

        self.kwargs["widgets"]["label_toggle"] = self.widgets_labels_show.GetValue()
        self.kwargs["widgets"]["label_size_slider"] = self.widgets_labels_font_size.GetValue()
        self.kwargs["widgets"]["label_rotation"] = self.widgets_labels_rotate.GetValue()
        self.kwargs["widgets"]["label_offset_x"] = self.widgets_labels_offset_x.GetValue()
        self.kwargs["widgets"]["label_offset_y"] = self.widgets_labels_offset_y.GetValue()

        self.kwargs["widgets"]["slider_zoom"] = self.widgets_general_zoom_1D.GetValue()
        self.kwargs["widgets"]["hover_mode"] = self.widgets_general_hover_mode.GetValue()
        self.kwargs["widgets"]["colorblind_safe_1D"] = self.widgets_color_colorblind.GetValue()
        self.kwargs["widgets"]["colorblind_safe_2D"] = self.widgets_color_colorblind.GetValue()
        self.kwargs["widgets"]["colorblind_safe_scatter"] = self.widgets_color_colorblind.GetValue()
        self.kwargs["widgets"]["colormap_change"] = self.widgets_color_colormap.GetValue()

        self.kwargs["widgets"]["legend_toggle"] = self.widgets_legend_show.GetValue()
        self.kwargs["widgets"]["legend_position"] = self.widgets_legend_position.GetValue()
        self.kwargs["widgets"]["legend_orientation"] = self.widgets_legend_orientation.GetValue()
        self.kwargs["widgets"]["legend_transparency"] = self.widgets_legend_transparency.GetValue()

        self.kwargs["widgets"]["scatter_size"] = self.widgets_scatter_size.GetValue()
        self.kwargs["widgets"]["scatter_transparency"] = self.widgets_scatter_transparency.GetValue()
        self.kwargs["widgets"]["processing_normalization"] = self.widgets_processing_normalization.GetValue()

        self.on_update_document()
