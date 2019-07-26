# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import wx
from gui_elements.dialog_color_picker import DialogColorPicker
from styles import Dialog
from styles import makeCheckbox
from styles import makeTooltip
from utils.color import convertRGB1to255


class DialogCustomisePeptideAnnotations(Dialog):
    def __init__(self, parent, config, **kwargs):
        Dialog.__init__(self, parent, title="Other parameters...")

        self.parent = parent
        self.config = config

        self.make_gui()
        self.CentreOnParent()

    def onOK(self, evt):
        self.EndModal(wx.OK)

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 0, wx.EXPAND, 50)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

    def make_panel(self):
        panel = wx.Panel(self, -1)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        add_arrows_check = wx.StaticText(panel, -1, "Add arrows to labels:")
        self.add_arrows_check = makeCheckbox(panel, "")
        self.add_arrows_check.SetValue(self.config.msms_add_arrows)
        self.add_arrows_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        arrow_line_width = wx.StaticText(panel, -1, "Line width:")
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

        arrow_line_style = wx.StaticText(panel, -1, "Line style:")
        self.arrow_line_style_value = wx.Choice(panel, -1, choices=self.config.lineStylesList, size=(-1, -1))
        self.arrow_line_style_value.SetStringSelection(self.config.annotation_arrow_line_style)
        self.arrow_line_style_value.Bind(wx.EVT_CHOICE, self.on_apply)

        # temporarily disable
        self.arrow_line_width_value.Disable()
        self.arrow_line_style_value.Disable()

        hz_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        label_yaxis_offset_value = wx.StaticText(panel, -1, "Y-axis label offset:")
        self.label_yaxis_offset_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(self.config.msms_label_y_offset),
            min=0.0,
            max=1000,
            initial=self.config.msms_label_y_offset,
            inc=0.01,
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

        hz_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        plot_tandem_line_unlabelled_colorBtn = wx.StaticText(panel, -1, "Line color (unlabelled):")
        self.plot_tandem_line_unlabelled_colorBtn = wx.Button(
            panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="plot_tandem_unlabelled"
        )
        self.plot_tandem_line_unlabelled_colorBtn.SetBackgroundColour(
            convertRGB1to255(self.config.msms_line_color_unlabelled)
        )
        self.plot_tandem_line_unlabelled_colorBtn.Bind(wx.EVT_BUTTON, self.on_apply_color)

        plot_tandem_line_labelled_colorBtn = wx.StaticText(panel, -1, "Line color (labelled):")
        self.plot_tandem_line_labelled_colorBtn = wx.Button(
            panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="plot_tandem_labelled"
        )
        self.plot_tandem_line_labelled_colorBtn.SetBackgroundColour(
            convertRGB1to255(self.config.msms_line_color_labelled)
        )
        self.plot_tandem_line_labelled_colorBtn.Bind(wx.EVT_BUTTON, self.on_apply_color)

        label_show_neutral_loss = wx.StaticText(panel, -1, "Show neutral loss labels:")
        self.label_show_neutral_loss_check = makeCheckbox(panel, "")
        self.label_show_neutral_loss_check.SetValue(self.config.msms_show_neutral_loss)
        self.label_show_neutral_loss_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.label_show_neutral_loss_check.SetToolTip(
            makeTooltip(text="When checked neutral loss labels (e.g. H2O, NH3) will be shown.")
        )

        label_show_full_label = wx.StaticText(panel, -1, "Show full label:")
        self.label_show_full_label_check = makeCheckbox(panel, "")
        self.label_show_full_label_check.SetValue(self.config.msms_show_full_label)
        self.label_show_full_label_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.label_show_full_label_check.SetToolTip(
            makeTooltip(text="Full labels will be shown, e.g. y5_H2Ox2+1. When unchecked, this label would look: y5+1.")
        )

        hz_line_3 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        label_show_name = wx.StaticText(panel, -1, "Label structure:")

        self.label_show_fragment_check = makeCheckbox(panel, "fragment")
        self.label_show_fragment_check.SetValue(self.config._tandem_label_format["fragment_name"])
        self.label_show_fragment_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.label_show_charge_check = makeCheckbox(panel, "charge")
        self.label_show_charge_check.SetValue(self.config._tandem_label_format["charge"])
        self.label_show_charge_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.label_show_peptide_check = makeCheckbox(panel, "sequence")
        self.label_show_peptide_check.SetValue(self.config._tandem_label_format["peptide_seq"])
        self.label_show_peptide_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.label_show_error_check = makeCheckbox(panel, "Δ error")
        self.label_show_error_check.SetValue(self.config._tandem_label_format["delta_mz"])
        self.label_show_error_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        # temporarily disable
        self.label_show_error_check.Disable()

        label_grid = wx.GridBagSizer(5, 5)
        y = 0
        label_grid.Add(
            self.label_show_fragment_check, (y, 0), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL
        )
        label_grid.Add(self.label_show_charge_check, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        label_grid.Add(
            self.label_show_peptide_check, (y, 2), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL
        )
        label_grid.Add(self.label_show_error_check, (y, 3), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(add_arrows_check, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.add_arrows_check, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(arrow_line_width, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.arrow_line_width_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(arrow_line_style, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.arrow_line_style_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(hz_line_1, (y, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
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
        grid.Add(hz_line_2, (y, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        y = y + 1
        grid.Add(
            plot_tandem_line_unlabelled_colorBtn,
            (y, 0),
            wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(
            self.plot_tandem_line_unlabelled_colorBtn,
            (y, 1),
            wx.GBSpan(1, 1),
            flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL,
        )
        y = y + 1
        grid.Add(
            plot_tandem_line_labelled_colorBtn, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT
        )
        grid.Add(
            self.plot_tandem_line_labelled_colorBtn, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL
        )
        y = y + 1
        grid.Add(label_show_neutral_loss, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_show_neutral_loss_check, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(label_show_full_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_show_full_label_check, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(hz_line_3, (y, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        y = y + 1
        grid.Add(label_show_name, (y, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        y = y + 1
        grid.Add(label_grid, (y, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        main_sizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_apply(self, evt):
        self.config.annotation_label_font_size = self.label_fontSize_value.GetStringSelection()
        self.config.annotation_label_font_weight = self.label_fontWeight_value.GetStringSelection()
        self.config.annotation_label_vert = self.label_vert_alignment_value.GetStringSelection()
        self.config.annotation_label_horz = self.label_horz_alignment_value.GetStringSelection()
        self.config.annotation_label_font_orientation = self.label_fontOrientation_value.GetStringSelection()

        self.config.annotation_arrow_line_width = self.arrow_line_width_value.GetValue()
        self.config.annotation_arrow_line_style = self.arrow_line_style_value.GetStringSelection()

        self.config.msms_add_arrows = self.add_arrows_check.GetValue()
        self.config.msms_show_neutral_loss = self.label_show_neutral_loss_check.GetValue()
        self.config.msms_label_y_offset = self.label_yaxis_offset_value.GetValue()
        self.config.msms_show_full_label = self.label_show_full_label_check.GetValue()

        _label_format = {
            "fragment_name": self.label_show_fragment_check.GetValue(),
            "peptide_seq": self.label_show_peptide_check.GetValue(),
            "charge": self.label_show_charge_check.GetValue(),
            "delta_mz": self.label_show_error_check.GetValue(),
        }

        self.config._tandem_label_format = _label_format

    def on_apply_color(self, evt):
        source = evt.GetEventObject().GetName()

        dlg = DialogColorPicker(self, self.config.customColors)
        if dlg.ShowModal() == "ok":
            color_255, color_1, __ = dlg.GetChosenColour()
            self.config.customColors = dlg.GetCustomColours()

            if source == "plot_tandem_labelled":
                self.plot_tandem_line_labelled_colorBtn.SetBackgroundColour(color_255)
                self.config.msms_line_color_labelled = color_1
            elif source == "plot_tandem_unlabelled":
                self.plot_tandem_line_unlabelled_colorBtn.SetBackgroundColour(color_255)
                self.config.msms_line_color_unlabelled = color_1
