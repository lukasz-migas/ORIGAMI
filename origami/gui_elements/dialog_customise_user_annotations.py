# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import wx
from styles import Dialog
from styles import makeCheckbox


class DialogCustomiseUserAnnotations(Dialog):
    def __init__(self, parent, **kwargs):
        Dialog.__init__(self, parent, title="Annotation...")

        self.parent = parent
        self.config = kwargs["config"]

        self.make_gui()
        self.CentreOnParent()

    def on_ok(self, evt):
        self.EndModal(wx.OK)

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 0, wx.EXPAND, 10)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

    def make_panel(self):
        panel = wx.Panel(self, -1)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        charge_std_dev = wx.StaticText(panel, -1, "Charge prediction (std dev):")
        self.charge_std_dev_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(self.config.annotation_charge_std_dev),
            min=0.005,
            max=0.25,
            initial=self.config.annotation_charge_std_dev,
            inc=0.01,
            size=(-1, -1),
        )
        self.charge_std_dev_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        hz_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        arrow_line_width = wx.StaticText(panel, -1, "Arrow line width:")
        self.arrow_line_width_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(self.config.annotation_arrow_line_width),
            min=0.005,
            max=2,
            initial=self.config.annotation_arrow_line_width,
            inc=0.25,
            size=(-1, -1),
        )
        self.arrow_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        arrow_line_style = wx.StaticText(panel, -1, "Arrow line style:")
        self.arrow_line_style_value = wx.Choice(panel, -1, choices=self.config.lineStylesList, size=(-1, -1))
        self.arrow_line_style_value.SetStringSelection(self.config.annotation_arrow_line_style)
        self.arrow_line_style_value.Bind(wx.EVT_CHOICE, self.on_apply)

        arrow_cap_length_value = wx.StaticText(panel, -1, "Arrow cap length:")
        self.arrow_cap_length_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(self.config.annotation_arrow_cap_length),
            min=0.0,
            max=1000,
            initial=self.config.annotation_arrow_cap_length,
            inc=0.1,
            size=(-1, -1),
        )
        self.arrow_cap_length_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        arrow_cap_width_value = wx.StaticText(panel, -1, "Arrow cap width:")
        self.arrow_cap_width_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(self.config.annotation_arrow_cap_width),
            min=0.0,
            max=1000,
            initial=self.config.annotation_arrow_cap_width,
            inc=0.1,
            size=(-1, -1),
        )
        self.arrow_cap_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        hz_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        label_yaxis_offset_value = wx.StaticText(panel, -1, "Y-axis label offset:")
        self.label_yaxis_offset_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(self.config.annotation_label_y_offset),
            min=0.0,
            max=1000,
            initial=self.config.annotation_label_y_offset,
            inc=0.05,
            size=(-1, -1),
        )
        self.label_yaxis_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        label_fontOrientation_label = wx.StaticText(panel, -1, "Font orientation:")
        self.label_fontOrientation_value = wx.Choice(
            panel, -1, choices=self.config.label_font_orientation_list, size=(-1, -1)
        )
        self.label_fontOrientation_value.SetStringSelection(self.config.annotation_label_font_orientation)
        self.label_fontOrientation_value.Bind(wx.EVT_CHOICE, self.on_apply)

        label_fontSize_label = wx.StaticText(panel, -1, "Font size:")
        self.label_fontSize_value = wx.Choice(panel, -1, choices=self.config.label_fontsize_list, size=(-1, -1))
        self.label_fontSize_value.SetStringSelection(self.config.annotation_label_font_size)
        self.label_fontSize_value.Bind(wx.EVT_CHOICE, self.on_apply)

        label_fontWeight_label = wx.StaticText(panel, -1, "Font weight:")
        self.label_fontWeight_value = wx.Choice(panel, -1, choices=self.config.label_fontweight_list, size=(-1, -1))
        self.label_fontWeight_value.SetStringSelection(self.config.annotation_label_font_weight)
        self.label_fontWeight_value.Bind(wx.EVT_CHOICE, self.on_apply)

        label_horz_alignment = wx.StaticText(panel, -1, "Label horizontal alignment:")
        self.label_horz_alignment_value = wx.Choice(
            panel, -1, choices=self.config.horizontal_alignment_list, size=(-1, -1)
        )
        self.label_horz_alignment_value.SetStringSelection(self.config.annotation_label_horz)
        self.label_horz_alignment_value.Bind(wx.EVT_CHOICE, self.on_apply)

        label_vert_alignment = wx.StaticText(panel, -1, "Label vertical alignment:")
        self.label_vert_alignment_value = wx.Choice(
            panel, -1, choices=self.config.vertical_alignment_list, size=(-1, -1)
        )
        self.label_vert_alignment_value.SetStringSelection(self.config.annotation_label_vert)
        self.label_vert_alignment_value.Bind(wx.EVT_CHOICE, self.on_apply)

        hz_line_3 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        zoom_y_buffer_check = wx.StaticText(panel, -1, "Adjust y-axis zoom:")
        self.zoom_y_buffer_check = makeCheckbox(panel, "")
        self.zoom_y_buffer_check.SetValue(self.config.annotation_zoom_y)

        zoom_y_buffer = wx.StaticText(panel, -1, "Zoom y-axis multiplier:")
        self.zoom_y_buffer_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(self.config.annotation_zoom_y_multiplier),
            min=1,
            max=3,
            initial=self.config.annotation_zoom_y_multiplier,
            inc=0.1,
            size=(-1, -1),
        )
        self.zoom_y_buffer_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        hz_line_4 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        highlight_alpha = wx.StaticText(panel, -1, "Highlight transparency:")
        self.highlight_alpha_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(self.config.annotation_patch_transparency),
            min=0.0,
            max=1.0,
            initial=self.config.annotation_patch_transparency,
            inc=0.2,
            size=(-1, -1),
        )
        self.highlight_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        highlight_width = wx.StaticText(panel, -1, "Highlight width:")
        self.highlight_width_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(self.config.annotation_patch_width),
            min=1.0,
            max=10.0,
            initial=self.config.annotation_patch_width,
            inc=1,
            size=(-1, -1),
        )
        self.highlight_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        #
        #         self.applyBtn = wx.Button(panel, wx.ID_ANY, "Apply", size=(-1, 22))
        #         self.closeBtn = wx.Button(panel, wx.ID_OK, "Close", size=(-1, 22))

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(charge_std_dev, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.charge_std_dev_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(hz_line_1, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        grid.Add(arrow_line_width, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.arrow_line_width_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(arrow_line_style, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.arrow_line_style_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(arrow_cap_length_value, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.arrow_cap_length_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(arrow_cap_width_value, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.arrow_cap_width_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(hz_line_2, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        grid.Add(label_yaxis_offset_value, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_yaxis_offset_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(label_fontOrientation_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_fontOrientation_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(label_fontSize_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_fontSize_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(label_fontWeight_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_fontWeight_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(label_horz_alignment, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_horz_alignment_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(label_vert_alignment, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_vert_alignment_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(hz_line_3, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        grid.Add(zoom_y_buffer_check, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.zoom_y_buffer_check, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(zoom_y_buffer, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.zoom_y_buffer_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(hz_line_4, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        y = y + 1
        grid.Add(highlight_alpha, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.highlight_alpha_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(highlight_width, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.highlight_width_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        #         y = y+1
        #         grid.Add(self.applyBtn, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        #         grid.Add(self.closeBtn, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_apply(self, evt):
        self.config.annotation_charge_std_dev = self.charge_std_dev_value.GetValue()

        self.config.annotation_arrow_line_width = self.arrow_line_width_value.GetValue()
        self.config.annotation_arrow_line_style = self.arrow_line_style_value.GetStringSelection()
        self.config.annotation_arrow_cap_length = self.arrow_cap_length_value.GetValue()
        self.config.annotation_arrow_cap_width = self.arrow_cap_width_value.GetValue()

        self.config.annotation_label_y_offset = self.label_yaxis_offset_value.GetValue()
        self.config.annotation_label_font_size = self.label_fontSize_value.GetStringSelection()
        self.config.annotation_label_font_weight = self.label_fontWeight_value.GetStringSelection()
        self.config.annotation_label_vert = self.label_vert_alignment_value.GetStringSelection()
        self.config.annotation_label_horz = self.label_horz_alignment_value.GetStringSelection()
        self.config.annotation_label_font_orientation = self.label_fontOrientation_value.GetStringSelection()

        self.config.annotation_zoom_y = self.zoom_y_buffer_check.GetValue()
        self.config.annotation_zoom_y_multiplier = self.zoom_y_buffer_value.GetValue()

        self.config.annotation_patch_transparency = self.highlight_alpha_value.GetValue()
        self.config.annotation_patch_width = self.highlight_width_value.GetValue()
