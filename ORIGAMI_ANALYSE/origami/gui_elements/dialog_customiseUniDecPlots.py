# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
#
# 	 GitHub : https://github.com/lukasz-migas/ORIGAMI
# 	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
# 	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or
#    modify it under the condition you cite and credit the authors whenever
#    appropriate.
#    The program is distributed in the hope that it will be useful but is
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

import wx
from wx.adv import BitmapComboBox

from ids import (ID_unidecPanel_fitLineColor, ID_unidecPanel_barEdgeColor)
from toolbox import (str2num, str2int, convertRGB1to255, convertRGB255to1,
                             num2str)
from styles import makeStaticBox, makeCheckbox
from gui_elements.misc_dialogs import dlgBox


class panelCustomiseParameters(wx.Dialog):

    def __init__(self, parent, config, icons, **kwargs):
        wx.Dialog.__init__(self, parent, -1, 'Other parameters...', size=(-1, -1),
                              style=wx.DEFAULT_FRAME_STYLE & ~
                              (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.config = config
        self.icons = icons

        self.makeGUI()
        self.CentreOnParent()

    def onClose(self, evt):
        """Destroy this frame."""
        self.Destroy()
    # ----

    def onOK(self, evt):
        self.EndModal(wx.OK)

    def makeGUI(self):

        # make panel
        panel = self.makePanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 10)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makePanel(self):
        panel = wx.Panel(self, -1)

        general_staticBox = makeStaticBox(panel, "General", size=(-1, -1), color=wx.BLACK)
        general_staticBox.SetSize((-1, -1))
        general_box_sizer = wx.StaticBoxSizer(general_staticBox, wx.HORIZONTAL)

        unidec_view_label = wx.StaticText(panel, -1, "Panel view:")
        self.unidec_view_value = wx.Choice(panel, -1, choices=["Single page view", "Tabbed view"],
                                          size=(-1, -1))
        self.unidec_view_value.SetStringSelection(self.config.unidec_plot_panel_view)
        self.unidec_view_value.Bind(wx.EVT_CHOICE, self.onUniDecView)

        remove_label_overlap_label = wx.StaticText(panel, wx.ID_ANY, "Optimise label position:")
        self.unidec_labels_optimise_position_check = makeCheckbox(panel, "")
        self.unidec_labels_optimise_position_check.SetValue(self.config.unidec_optimiseLabelPositions)
        self.unidec_labels_optimise_position_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        general_grid = wx.GridBagSizer(2, 2)
        y = 0
        general_grid.Add(unidec_view_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        general_grid.Add(self.unidec_view_value, (y, 1), flag=wx.EXPAND)
        y = y + 1
        general_grid.Add(remove_label_overlap_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        general_grid.Add(self.unidec_labels_optimise_position_check, (y, 1), flag=wx.EXPAND)
        general_box_sizer.Add(general_grid, 0, wx.EXPAND, 10)

        # MS and MS Fit
        MS_staticBox = makeStaticBox(panel, "MS and UniDec Fit", size=(-1, -1), color=wx.BLACK)
        MS_staticBox.SetSize((-1, -1))
        MS_box_sizer = wx.StaticBoxSizer(MS_staticBox, wx.HORIZONTAL)

        fit_lineColor_label = wx.StaticText(panel, -1, "Line color:")
        self.fit_lineColor_Btn = wx.Button(panel, ID_unidecPanel_fitLineColor,
                                           "", wx.DefaultPosition,
                                           wx.Size(26, 26), 0)
        self.fit_lineColor_Btn.SetBackgroundColour(convertRGB1to255(self.config.unidec_plot_fit_lineColor))
        self.fit_lineColor_Btn.Bind(wx.EVT_BUTTON, self.onChangeColour)

        MS_grid = wx.GridBagSizer(2, 2)
        y = 0
        MS_grid.Add(fit_lineColor_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        MS_grid.Add(self.fit_lineColor_Btn, (y, 1), flag=wx.EXPAND)
        MS_box_sizer.Add(MS_grid, 0, wx.EXPAND, 10)

        # m/z vs charge
        contour_staticBox = makeStaticBox(panel, "m/z vs charge | MW vs charge", size=(-1, -1), color=wx.BLACK)
        contour_staticBox.SetSize((-1, -1))
        contour_box_sizer = wx.StaticBoxSizer(contour_staticBox, wx.HORIZONTAL)

        speedy_label = wx.StaticText(panel, wx.ID_ANY, "Quick plot:")
        self.speedy_check = makeCheckbox(panel, "")
        self.speedy_check.SetValue(self.config.unidec_speedy)
        self.speedy_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        contour_levels_label = wx.StaticText(panel, -1, "Contour levels:")
        self.contour_levels_value = wx.SpinCtrlDouble(panel, -1,
                                                      value=str(self.config.unidec_plot_contour_levels),
                                                      min=25, max=200, initial=25, inc=25,
                                                      size=(90, -1))
        self.contour_levels_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        contour_grid = wx.GridBagSizer(2, 2)
        y = 0
        contour_grid.Add(speedy_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        contour_grid.Add(self.speedy_check, (y, 1), flag=wx.EXPAND)
        y = y + 1
        contour_grid.Add(contour_levels_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        contour_grid.Add(self.contour_levels_value, (y, 1), flag=wx.EXPAND)
        contour_box_sizer.Add(contour_grid, 0, wx.EXPAND, 10)

        # Zero-charge MS
        MW_staticBox = makeStaticBox(panel, "Zero-charge Mass Spectrum", size=(-1, -1), color=wx.BLACK)
        MW_staticBox.SetSize((-1, -1))
        MW_box_sizer = wx.StaticBoxSizer(MW_staticBox, wx.HORIZONTAL)

        MW_show_markers = wx.StaticText(panel, -1, "Show markers:")
        self.MW_show_markers_check = makeCheckbox(panel, "")
        self.MW_show_markers_check.SetValue(self.config.unidec_plot_MW_showMarkers)
        self.MW_show_markers_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        MW_markerSize_label = wx.StaticText(panel, -1, "Marker size:")
        self.MW_markerSize_value = wx.SpinCtrlDouble(panel, -1,
                                               value=str(self.config.unidec_plot_MW_markerSize),
                                               min=1, max=100, initial=1, inc=5,
                                               size=(90, -1))
        self.MW_markerSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        MW_grid = wx.GridBagSizer(2, 2)
        y = 0
        MW_grid.Add(MW_show_markers, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        MW_grid.Add(self.MW_show_markers_check, (y, 1), flag=wx.EXPAND)
        y = y + 1
        MW_grid.Add(MW_markerSize_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        MW_grid.Add(self.MW_markerSize_value, (y, 1), flag=wx.EXPAND)
        MW_box_sizer.Add(MW_grid, 0, wx.EXPAND, 10)

#         # Zero-charge MS
#         MW_staticBox = makeStaticBox(panel, "Zero-charge Mass Spectrum", size=(-1, -1), color=wx.BLACK)
#         MW_staticBox.SetSize((-1,-1))
#         MW_box_sizer = wx.StaticBoxSizer(MW_staticBox, wx.HORIZONTAL)
#
#         MW_show_markers = wx.StaticText(panel, -1, "Show markers:")
#         self.MW_show_markers_check = makeCheckbox(panel, u"")
#         self.MW_show_markers_check.SetValue(self.config.unidec_plot_MW_showMarkers)
#         self.MW_show_markers_check.Bind(wx.EVT_CHECKBOX, self.onApply)
#
#         MW_markerSize_label = wx.StaticText(panel, -1, "Marker size:")
#         self.MW_markerSize_value = wx.SpinCtrlDouble(panel, -1,
#                                                value=str(self.config.unidec_plot_MW_markerSize),
#                                                min=1, max=100, initial=1, inc=5,
#                                                size=(90, -1))
#         self.MW_markerSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
#
#         MW_grid = wx.GridBagSizer(2, 2)
#         y = 0
#         MW_grid.Add(MW_show_markers, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
#         MW_grid.Add(self.MW_show_markers_check, (y,1), flag=wx.EXPAND)
#         y = y + 1
#         MW_grid.Add(MW_markerSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
#         MW_grid.Add(self.MW_markerSize_value, (y,1), flag=wx.EXPAND)
#         MW_box_sizer.Add(MW_grid, 0, wx.EXPAND, 10)

        # MS with isolated species
        isolatedMS_staticBox = makeStaticBox(panel, "MS with isolated species", size=(-1, -1), color=wx.BLACK)
        isolatedMS_staticBox.SetSize((-1, -1))
        isolatedMS_box_sizer = wx.StaticBoxSizer(isolatedMS_staticBox, wx.HORIZONTAL)

        isolatedMS_markerSize_label = wx.StaticText(panel, -1, "Marker size:")
        self.isolatedMS_markerSize_value = wx.SpinCtrlDouble(panel, -1,
                                               value=str(self.config.unidec_plot_isolatedMS_markerSize),
                                               min=1, max=100, initial=1, inc=5,
                                               size=(90, -1))
        self.isolatedMS_markerSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        isolatedMS_grid = wx.GridBagSizer(2, 2)
        y = 0
        isolatedMS_grid.Add(isolatedMS_markerSize_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        isolatedMS_grid.Add(self.isolatedMS_markerSize_value, (y, 1), flag=wx.EXPAND)
        isolatedMS_box_sizer.Add(isolatedMS_grid, 0, wx.EXPAND, 10)

        # Barchart
        barParameters_staticBox = makeStaticBox(panel, "Peak intensities (Barchart)",
                                                 size=(-1, -1), color=wx.BLACK)
        barParameters_staticBox.SetSize((-1, -1))
        bar_box_sizer = wx.StaticBoxSizer(barParameters_staticBox, wx.HORIZONTAL)

        bar_markerSize_label = wx.StaticText(panel, -1, "Marker size:")
        self.bar_markerSize_value = wx.SpinCtrlDouble(panel, -1,
                                               value=str(self.config.unidec_plot_bar_markerSize),
                                               min=1, max=100, initial=1, inc=5,
                                               size=(90, -1))
        self.bar_markerSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        bar_width_label = wx.StaticText(panel, -1, "Bar width:")
        self.bar_width_value = wx.SpinCtrlDouble(panel, -1,
                                               value=str(self.config.unidec_plot_bar_width),
                                               min=0.01, max=10, inc=0.1,
                                               initial=self.config.unidec_plot_bar_width,
                                               size=(90, -1))
        self.bar_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        bar_alpha_label = wx.StaticText(panel, -1, "Bar transparency:")
        self.bar_alpha_value = wx.SpinCtrlDouble(panel, -1,
                                                    value=str(self.config.unidec_plot_bar_alpha),
                                                    min=0, max=1, initial=self.config.unidec_plot_bar_alpha,
                                                    inc=0.25, size=(90, -1))
        self.bar_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        bar_lineWidth_label = wx.StaticText(panel, -1, "Edge line width:")
        self.bar_lineWidth_value = wx.SpinCtrlDouble(panel, -1,
                                                    value=str(self.config.unidec_plot_bar_lineWidth),
                                                    min=0, max=5, initial=self.config.unidec_plot_bar_lineWidth,
                                                    inc=1, size=(90, -1))
        self.bar_lineWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        bar_edgeColor_label = wx.StaticText(panel, -1, "Edge color:")
        self.bar_edgeColor_Btn = wx.Button(panel, ID_unidecPanel_barEdgeColor,
                                              "", wx.DefaultPosition,
                                              wx.Size(26, 26), 0)
        self.bar_edgeColor_Btn.SetBackgroundColour(convertRGB1to255(self.config.unidec_plot_bar_edge_color))
        self.bar_edgeColor_Btn.Bind(wx.EVT_BUTTON, self.onChangeColour)

        bar_colorEdge_check_label = wx.StaticText(panel, -1, "Same as fill:")
        self.bar_colorEdge_check = makeCheckbox(panel, "")
        self.bar_colorEdge_check.SetValue(self.config.unidec_plot_bar_sameAsFill)
        self.bar_colorEdge_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        bar_grid = wx.GridBagSizer(2, 2)
        y = 0
        bar_grid.Add(bar_markerSize_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        bar_grid.Add(self.bar_markerSize_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y = y + 1
        bar_grid.Add(bar_width_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        bar_grid.Add(self.bar_width_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y = y + 1
        bar_grid.Add(bar_alpha_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        bar_grid.Add(self.bar_alpha_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y = y + 1
        bar_grid.Add(bar_lineWidth_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        bar_grid.Add(self.bar_lineWidth_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y = y + 1
        bar_grid.Add(bar_edgeColor_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        bar_grid.Add(self.bar_edgeColor_Btn, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        y = y + 1
        bar_grid.Add(bar_colorEdge_check_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        bar_grid.Add(self.bar_colorEdge_check, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        bar_box_sizer.Add(bar_grid, 0, wx.EXPAND, 10)

        # Color
        color_staticBox = makeStaticBox(panel, "Color scheme", size=(-1, -1), color=wx.BLACK)
        color_staticBox.SetSize((-1, -1))
        color_box_sizer = wx.StaticBoxSizer(color_staticBox, wx.HORIZONTAL)

        color_scheme_label = wx.StaticText(panel, -1, "Color scheme:")
        self.colorScheme_value = wx.Choice(panel, -1, choices=["Color palette", "Colormap"],
                                          size=(-1, -1), name="color")
        self.colorScheme_value.SetStringSelection(self.config.violin_color_value)
        self.colorScheme_value.Bind(wx.EVT_CHOICE, self.onApply)

        cmap_list = self.config.cmaps2[:]
        cmap_list.remove("jet")
        colormap_label = wx.StaticText(panel, -1, "Colormap:")
        self.colormap_value = wx.Choice(panel, -1, choices=cmap_list,
                                        size=(-1, -1), name="color")
        self.colormap_value.SetStringSelection(self.config.unidec_plot_colormap)
        self.colormap_value.Bind(wx.EVT_CHOICE, self.onApply)

        palette_label = wx.StaticText(panel, -1, "Color palette:")
        self.color_palette_value = BitmapComboBox(panel, -1, choices=[],
                                                  size=(160, -1), style=wx.CB_READONLY)
        self.color_palette_value.Bind(wx.EVT_COMBOBOX, self.onApply)

        # add choices
        self.color_palette_value.Append("HLS", bitmap=self.icons.iconsLib['cmap_hls'])
        self.color_palette_value.Append("HUSL", bitmap=self.icons.iconsLib['cmap_husl'])
        self.color_palette_value.Append("Cubehelix", bitmap=self.icons.iconsLib['cmap_cubehelix'])
        self.color_palette_value.Append("Spectral", bitmap=self.icons.iconsLib['cmap_spectral'])
        self.color_palette_value.Append("Viridis", bitmap=self.icons.iconsLib['cmap_viridis'])
        self.color_palette_value.Append("Rainbow", bitmap=self.icons.iconsLib['cmap_rainbow'])
        self.color_palette_value.Append("Inferno", bitmap=self.icons.iconsLib['cmap_inferno'])
        self.color_palette_value.Append("Cividis", bitmap=self.icons.iconsLib['cmap_cividis'])
        self.color_palette_value.Append("Winter", bitmap=self.icons.iconsLib['cmap_winter'])
        self.color_palette_value.Append("Cool", bitmap=self.icons.iconsLib['cmap_cool'])
        self.color_palette_value.Append("Gray", bitmap=self.icons.iconsLib['cmap_gray'])
        self.color_palette_value.Append("RdPu", bitmap=self.icons.iconsLib['cmap_rdpu'])
        self.color_palette_value.Append("Tab20b", bitmap=self.icons.iconsLib['cmap_tab20b'])
        self.color_palette_value.Append("Tab20c", bitmap=self.icons.iconsLib['cmap_tab20c'])

        self.color_palette_value.SetStringSelection(self.config.unidec_plot_palette)

        color_grid = wx.GridBagSizer(2, 2)
        y = 0
        color_grid.Add(color_scheme_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        color_grid.Add(self.colorScheme_value, (y, 1), flag=wx.EXPAND)
        y = y + 1
        color_grid.Add(colormap_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        color_grid.Add(self.colormap_value, (y, 1), flag=wx.EXPAND)
        y = y + 1
        color_grid.Add(palette_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        color_grid.Add(self.color_palette_value, (y, 1), flag=wx.EXPAND)
        color_box_sizer.Add(color_grid, 0, wx.EXPAND, 10)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(general_box_sizer, 0, wx.EXPAND, 10)
        mainSizer.Add(MS_box_sizer, 0, wx.EXPAND, 10)
        mainSizer.Add(contour_box_sizer, 0, wx.EXPAND, 10)
        mainSizer.Add(MW_box_sizer, 0, wx.EXPAND, 10)
        mainSizer.Add(isolatedMS_box_sizer, 0, wx.EXPAND, 10)
        mainSizer.Add(bar_box_sizer, 0, wx.EXPAND, 10)
        mainSizer.Add(color_box_sizer, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def onChangePalette(self, evt):
        pass

    def onChangeColour(self, evt):
        evtID = evt.GetId()

        # Restore custom colors
        custom = wx.ColourData()
        for key in range(len(self.config.customColors)):  # key in self.config.customColors:
            custom.SetCustomColour(key, self.config.customColors[key])
        dlg = wx.ColourDialog(self, custom)
        dlg.GetColourData().SetChooseFull(True)

        # Show dialog and get new colour
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            newColour = list(data.GetColour().Get())
            dlg.Destroy()
            # Retrieve custom colors
            for i in range(15):
                self.config.customColors[i] = data.GetCustomColour(i)
        else:
            return

        if evtID == ID_unidecPanel_barEdgeColor:
            self.config.unidec_plot_bar_edge_color = convertRGB255to1(newColour)
            self.bar_edgeColor_Btn.SetBackgroundColour(newColour)

        elif evtID == ID_unidecPanel_fitLineColor:
            self.config.unidec_plot_fit_lineColor = convertRGB255to1(newColour)
            self.fit_lineColor_Btn.SetBackgroundColour(newColour)

    def onApply(self, evt):

        self.config.unidec_plot_MW_showMarkers = self.MW_show_markers_check.GetValue()
        self.config.unidec_plot_MW_markerSize = self.MW_markerSize_value.GetValue()
        self.config.unidec_plot_contour_levels = int(self.contour_levels_value.GetValue())
        self.config.unidec_plot_isolatedMS_markerSize = self.isolatedMS_markerSize_value.GetValue()
        self.config.unidec_plot_bar_width = self.bar_width_value.GetValue()
        self.config.unidec_plot_bar_alpha = self.bar_alpha_value.GetValue()
        self.config.unidec_plot_bar_sameAsFill = self.bar_colorEdge_check.GetValue()
        self.config.unidec_plot_bar_lineWidth = self.bar_lineWidth_value.GetValue()
        self.config.unidec_plot_bar_markerSize = self.bar_markerSize_value.GetValue()
        self.config.unidec_plot_color_scheme = self.colorScheme_value.GetStringSelection()
        self.config.unidec_plot_colormap = self.colormap_value.GetStringSelection()
        self.config.unidec_plot_palette = self.color_palette_value.GetStringSelection()

        self.config.unidec_optimiseLabelPositions = self.unidec_labels_optimise_position_check.GetValue()
        self.config.unidec_speedy = self.speedy_check.GetValue()

    def onUniDecView(self, evt):
        self.config.unidec_plot_panel_view = self.unidec_view_value.GetStringSelection()

        dlgBox(exceptionTitle="Warning",
               exceptionMsg="Changing the panel view will not take place until you restart ORIGAMI.",
               type="Warning")

