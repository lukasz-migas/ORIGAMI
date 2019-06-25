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

from ast import literal_eval
from operator import itemgetter
from re import split as re_split
from time import time as ttime

import wx
from natsort import natsorted
from numpy import amax, arange, average, round, where
from pandas import read_csv
from pubsub import pub

import processing.utils as pr_utils
from gui_elements.dialog_customise_user_annotations import \
    dialog_customise_user_annotations
from help_documentation import OrigamiHelp
from ids import (ID_annotPanel_addAnnotations,
                 ID_annotPanel_assignChargeState_selected,
                 ID_annotPanel_assignColor_selected,
                 ID_annotPanel_assignLabel_selected,
                 ID_annotPanel_deleteSelected_selected,
                 ID_annotPanel_fixIntensity_selected,
                 ID_annotPanel_multipleAnnotation, ID_annotPanel_otherSettings,
                 ID_annotPanel_savePeakList_selected,
                 ID_annotPanel_show_adjustLabelPosition,
                 ID_annotPanel_show_charge, ID_annotPanel_show_label,
                 ID_annotPanel_show_labelsAtIntensity,
                 ID_annotPanel_show_mzAndIntensity)
from styles import makeCheckbox, makeMenuItem, makeToggleBtn, validator, ListCtrl
from toolbox import (checkExtension)
from gui_elements.dialog_ask import DialogAsk
from gui_elements.misc_dialogs import dlgBox, dlgAsk
from utils.color import convertRGB1to255, convertRGB255to1
from utils.converters import str2num, str2int
from utils.labels import _replace_labels

# TODO: need to override the on_select_item with the built-in method OR call after with similar method


class panel_peak_annotation_editor(wx.MiniFrame):
    """
    Simple GUI to view and annotate mass spectra
    """

    def __init__(self, parent, documentTree, config, icons, **kwargs):
        wx.MiniFrame.__init__(self, parent, -1,
                              'Annotation...', size=(-1, -1),
                              style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER
                              )

        tstart = ttime()

        self.parent = parent
        self.documentTree = documentTree
        self.panelPlot = documentTree.presenter.view.panelPlots
        self.config = config
        self.icons = icons
        self.help = OrigamiHelp()
        self.data_processing = self.parent.presenter.data_processing

        self.kwargs = kwargs

        # presets
        self.showLabelsAtIntensity = True
        self.adjustLabelPosition = False
        self.item_loading_lock = False
        self.check_all = False
        self.reverse = False
        self.lastColumn = None
#         self.peaklist.item_id = None

        self.config.annotation_patch_transparency = 0.2
        self.config.annotation_patch_width = 3

        self.data_xmin = None
        self.data_ymin = None
        self.manual_add_only = False
        if "data" in self.kwargs and self.kwargs['data'] is not None:
            self.data_xmin = min(self.kwargs["data"][:, 0])
            self.data_ymin = max(self.kwargs["data"][:, 0])
        elif self.kwargs['data'] is None:
            self.manual_add_only = True

        self.plot = self.kwargs['plot']

        # make gui items
        self.make_gui()

        self.Layout()
        self.SetSize((-1, 500))
        self.SetMinSize((521, 300))
        self.SetFocus()

        # bind
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_item)
        self.onPopulateTable()
        self.on_toggle_controls(None)

        # add listener
        pub.subscribe(self.add_annotation_from_mouse_evt, 'mark_annotation')

        try:
            self.SetTitle("Annotating - {} / {}".format(kwargs['document'], kwargs['dataset']))
        except Exception:
            pass

        print(("Startup took {:.3f} seconds".format(ttime() - tstart)))

    def on_key_event(self, evt):
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)
#         elif key_code == 127: # delete
#             self.onRemove(None)

        evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""
        # reset state
        try:
            self.plot.plot_remove_temporary(repaint=True)
        except TypeError:
            pass
        self.plot._on_mark_annotation(state=False)
        try:
            pub.unsubscribe(self.add_annotation_from_mouse_evt, 'mark_annotation')
        except Exception:
            pass
        self.documentTree.annotateDlg = None
        self.Destroy()
    # ----

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 5)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def make_peaklist(self, panel):

        self.annotation_list = {'check': 0, 'min': 1, 'max': 2, 'position': 3,
                                'intensity': 4, 'charge': 5, 'label': 6, 'color': 7,
                                'arrow': 8}

        self.peaklist = ListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES | wx.LC_SINGLE_SEL)
        self.peaklist.InsertColumn(self.annotation_list['check'], '', width=25)
        self.peaklist.InsertColumn(self.annotation_list['min'], 'min band', width=75)
        self.peaklist.InsertColumn(self.annotation_list['max'], 'max band', width=75)
        self.peaklist.InsertColumn(self.annotation_list['position'], 'value (x)', width=75)
        self.peaklist.InsertColumn(self.annotation_list['intensity'], 'value (y)', width=75)
        self.peaklist.InsertColumn(self.annotation_list['charge'], 'charge', width=50)
        self.peaklist.InsertColumn(self.annotation_list['label'], 'label', width=100)
        self.peaklist.InsertColumn(self.annotation_list['color'], 'color', width=107)
        self.peaklist.InsertColumn(self.annotation_list['arrow'], 'show arrow', width=75)

#         self.peaklist.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)

    def make_panel(self):

        panel = wx.Panel(self, -1, size=(-1, -1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # make peaklist
        self.make_peaklist(panel)

        # make editor
        min_label = wx.StaticText(panel, -1, "min band (x):")
        self.min_value = wx.TextCtrl(panel, -1, "", validator=validator('float'))

        max_label = wx.StaticText(panel, -1, "max band (x):")
        self.max_value = wx.TextCtrl(panel, -1, "", validator=validator('float'))

        charge_label = wx.StaticText(panel, -1, "charge:")
        self.charge_value = wx.TextCtrl(panel, -1, "", validator=validator('int'))

        label_label = wx.StaticText(panel, -1, "label:")
        self.label_value = wx.TextCtrl(panel, -1, "", style=wx.TE_RICH2)

        color_label = wx.StaticText(panel, -1, "color:")
        self.colorBtn = wx.Button(panel, wx.ID_ANY,
                                  "", wx.DefaultPosition,
                                  wx.Size(26, 26), 0)
        self.colorBtn.SetBackgroundColour(convertRGB1to255(self.config.interactive_ms_annotations_color))
        self.colorBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)

        label_format = wx.StaticText(panel, -1, "format:")
        self.label_format = wx.ComboBox(panel, -1, choices=["None", "charge-only [n+]", "charge-only [+n]", "superscript", "M+nH", "2M+nH", "3M+nH", "4M+nH"],
                                        value="None", style=wx.CB_READONLY, size=(-1, -1))

        intensity_label = wx.StaticText(panel, -1, "value (y):")
        self.intensity_value = wx.TextCtrl(panel, -1, "", validator=validator('float'))
        self.intensity_value.SetToolTip(wx.ToolTip("Value (y) could represent intensity of an ion in a mass spectrum."))

        position_label = wx.StaticText(panel, -1, "value (x):")
        self.position_value = wx.TextCtrl(panel, -1, "", validator=validator('float'))
        self.position_value.SetToolTip(wx.ToolTip("Value (x) could represent m/z of an ion in a mass spectrum."))

        position_x_label = wx.StaticText(panel, -1, "label position (x):")
        self.position_x_value = wx.TextCtrl(panel, -1, "", validator=validator('float'))

        position_y_label = wx.StaticText(panel, -1, "label position (y):")
        self.position_y_value = wx.TextCtrl(panel, -1, "", validator=validator('float'))

        add_arrow_to_peak = wx.StaticText(panel, -1, "add arrow:")
        self.add_arrow_to_peak = makeCheckbox(panel, "")
        self.add_arrow_to_peak.SetValue(False)
        self.add_arrow_to_peak.Bind(wx.EVT_CHECKBOX, self.onAddAnnotation)

        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        # make buttons
        self.markTgl = makeToggleBtn(panel, 'Annotating: Off', wx.RED, size=(-1, -1))
        self.markTgl.SetLabel('Annotating: Off')
        self.markTgl.SetForegroundColour(wx.WHITE)
        self.markTgl.SetBackgroundColour(wx.RED)
        self.markTgl.SetToolTip(wx.ToolTip(
            "When toggled to On, right-click in the plot area to select an area and annotate accordingly."))

#         if self.manual_add_only:
#             self.markTgl.Disable()

        self.addBtn = wx.Button(panel, wx.ID_OK, "Add annotation", size=(-1, 22))
        self.showBtn = wx.Button(panel, wx.ID_OK, "Show ▼", size=(-1, 22))
        self.removeBtn = wx.Button(panel, wx.ID_OK, "Remove", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
        self.actionBtn = wx.Button(panel, wx.ID_OK, "Action ▼", size=(-1, 22))

        self.highlight_on_selection = makeCheckbox(panel, "highlight")
        self.highlight_on_selection.SetValue(True)

        self.zoom_on_selection = makeCheckbox(panel, "zoom-in")
        self.zoom_on_selection.SetValue(False)

        window_size = wx.StaticText(panel, wx.ID_ANY, "window size:")
        self.zoom_window_size = wx.SpinCtrlDouble(
            panel, -1,
            value=str(5),
            min=0.0001, max=250,
            initial=5,
            inc=25, size=(90, -1))

        self.markTgl.Bind(wx.EVT_TOGGLEBUTTON, self.onMarkOnSpectrum)
        self.addBtn.Bind(wx.EVT_BUTTON, self.onAddAnnotation)
        self.removeBtn.Bind(wx.EVT_BUTTON, self.onRemove)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)
        self.showBtn.Bind(wx.EVT_BUTTON, self.on_plot_tools)
        self.actionBtn.Bind(wx.EVT_BUTTON, self.on_action_tools)
        self.label_format.Bind(wx.EVT_COMBOBOX, self.onUpdateLabel)

        # button grid
        btn_grid = wx.GridBagSizer(5, 5)
        y = 0
        btn_grid.Add(self.actionBtn, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        btn_grid.Add(self.markTgl, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid.Add(self.addBtn, (y, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid.Add(self.showBtn, (y, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid.Add(self.removeBtn, (y, 4), wx.GBSpan(1, 1),
                     flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid.Add(self.cancelBtn, (y, 5), wx.GBSpan(1, 1),
                     flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        y = y + 1
        btn_grid.Add(self.highlight_on_selection, (y, 0), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        btn_grid.Add(self.zoom_on_selection, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        btn_grid.Add(window_size, (y, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid.Add(self.zoom_window_size, (y, 3), wx.GBSpan(1, 1),
                     flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(min_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.min_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(max_label, (y, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.max_value, (y, 3), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(position_label, (y, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.position_value, (y, 5), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(charge_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.charge_value, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(intensity_label, (y, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.intensity_value, (y, 3), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(color_label, (y, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colorBtn, (y, 5), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(label_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_value, (y, 1), wx.GBSpan(1, 3), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(label_format, (y, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_format, (y, 5), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(position_x_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.position_x_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(position_y_label, (y, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.position_y_value, (y, 3), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(add_arrow_to_peak, (y, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.add_arrow_to_peak, (y, 5), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(horizontal_line, (y, 0), wx.GBSpan(1, 8), flag=wx.EXPAND)
        y = y + 1
        grid.Add(btn_grid, (y, 0), wx.GBSpan(1, 8), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

        mainSizer.Add(grid, 0, wx.EXPAND, 10)
        mainSizer.Add(self.peaklist, 1, wx.EXPAND | wx.ALL, 2)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def on_toggle_controls(self, evt):

        #         add_arrow = self.add_arrow_to_peak.GetValue()
        #         if add_arrow:
        #             self.position_x_value.Enable()
        #             self.position_y_value.Enable()
        #         else:
        #             self.position_x_value.Disable()
        #             self.position_y_value.Disable()

        if evt is not None:
            evt.Skip()

    def on_multiple_annotations(self, evt):
        import copy

        rows = self.peaklist.GetItemCount()
        checked = []

        for row in range(rows):
            if self.peaklist.IsChecked(row):
                checked.append(row)

        if len(checked) == 0:
            print("Please check at least one annotation the table...")
            return

        n_duplicates = dlgAsk('How many times would you like to duplicate this annotations?',
                              defaultValue="1")
        n_duplicates = int(n_duplicates)

        for row in checked:
            min_value = self.peaklist.GetItem(row, self.annotation_list['min']).GetText()
            max_value = self.peaklist.GetItem(row, self.annotation_list['max']).GetText()
            annotation = self.get_annotation(min_value, max_value)

            # modify parameters
            for i in range(n_duplicates):
                _annotation = copy.deepcopy(annotation)
                _annotation["min"] = annotation["min"] - (0.001 * (i + 1))

                xmin = _annotation['min']
                xmax = _annotation['max']
                charge = _annotation['charge']
                position = _annotation['isotopic_x']
                intensity = _annotation['intensity']
                label = _annotation['label']
                color = _annotation['color']
                add_arrow = _annotation['add_arrow']

                name = "{} - {}".format(xmin, xmax)

                self.kwargs['annotations'][name] = _annotation
                self.peaklist.Append(["", xmin, xmax, position, intensity, charge, label, color, str(add_arrow)])

        self.documentTree.onUpdateAnotations(self.kwargs['annotations'],
                                             self.kwargs['document'],
                                             self.kwargs['dataset'])

    def on_action_tools(self, evt):
        label_format = self.label_format.GetStringSelection()

        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_annotPanel_assignChargeState_selected)
        self.Bind(wx.EVT_MENU, self.onDeleteItems, id=ID_annotPanel_deleteSelected_selected)
        self.Bind(wx.EVT_MENU, self.onChangeColour, id=ID_annotPanel_assignColor_selected)
        self.Bind(wx.EVT_MENU, self.onFixIntensity, id=ID_annotPanel_fixIntensity_selected)
        self.Bind(wx.EVT_MENU, self.onUpdateLabel, id=ID_annotPanel_assignLabel_selected)
        self.Bind(wx.EVT_MENU, self.onOpenPeakList, id=ID_annotPanel_addAnnotations)
        self.Bind(wx.EVT_MENU, self.onSavePeaklist, id=ID_annotPanel_savePeakList_selected)
        self.Bind(wx.EVT_MENU, self.onCustomiseParameters, id=ID_annotPanel_otherSettings)
        self.Bind(wx.EVT_MENU, self.on_multiple_annotations, id=ID_annotPanel_multipleAnnotation)

        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_annotPanel_otherSettings,
                                     text='Customise other settings...',
                                     bitmap=self.icons.iconsLib['settings16_2'],
                                     help_text=''))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_annotPanel_multipleAnnotation,
                                     text="Multiply annotation (selected)",
                                     bitmap=None))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_annotPanel_addAnnotations,
                                     text='Add list of ions (.csv/.txt)',
                                     bitmap=self.icons.iconsLib['filelist_16'],
                                     help_text='Format: min, max, charge (optional), label (optional), color (optional)'))
        menu.AppendSeparator()
        menu.Append(ID_annotPanel_assignColor_selected, "Set color (selected)")
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_annotPanel_assignChargeState_selected,
                                     text="Set charge state (selected)",
                                     bitmap=self.icons.iconsLib['assign_charge_16']))
        menu.Append(ID_annotPanel_assignLabel_selected, "Auto-generate labels ({})".format(label_format))
        menu.Append(ID_annotPanel_fixIntensity_selected, "Fix intensity (selected)")
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_annotPanel_savePeakList_selected,
                                     text="Save peaks to file (all))",
                                     bitmap=self.icons.iconsLib['file_csv_16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_annotPanel_deleteSelected_selected,
                                     text='Delete (selected)',
                                     bitmap=self.icons.iconsLib['bin16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_plot_tools(self, evt):

        self.Bind(wx.EVT_MENU, self.onShowOnPlot, id=ID_annotPanel_show_charge)
        self.Bind(wx.EVT_MENU, self.onShowOnPlot, id=ID_annotPanel_show_label)
        self.Bind(wx.EVT_MENU, self.onShowOnPlot, id=ID_annotPanel_show_mzAndIntensity)
        self.Bind(wx.EVT_TOOL, self.on_check_tools, id=ID_annotPanel_show_labelsAtIntensity)
        self.Bind(wx.EVT_TOOL, self.on_check_tools, id=ID_annotPanel_show_adjustLabelPosition)

        menu = wx.Menu()
        self.showLabelsAtIntensity_check = menu.AppendCheckItem(ID_annotPanel_show_labelsAtIntensity,
                                                                "Show labels at intensity value",
                                                                help="If checked, labels will 'stick' to the intensity values")
        self.showLabelsAtIntensity_check.Check(self.showLabelsAtIntensity)
        self.adjustLabelPosition_check = menu.AppendCheckItem(ID_annotPanel_show_adjustLabelPosition,
                                                              "Adjust positions to prevent overlap",
                                                              help="If checked, labels will be repositioned to prevent overlap.")
        self.adjustLabelPosition_check.Check(self.adjustLabelPosition)

        menu.AppendSeparator()
        menu.Append(ID_annotPanel_show_mzAndIntensity, "Show m/z, intensity, charge")
        menu.Append(ID_annotPanel_show_charge, "Show charge")
        menu.Append(ID_annotPanel_show_label, "Show label")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_check_tools(self, evt):
        """ Check/uncheck menu item """

        evtID = evt.GetId()
        # check which event was triggered
        if evtID == ID_annotPanel_show_labelsAtIntensity:
            check_value = not self.showLabelsAtIntensity
            self.showLabelsAtIntensity = check_value

        elif evtID == ID_annotPanel_show_adjustLabelPosition:
            check_value = not self.adjustLabelPosition
            self.adjustLabelPosition = check_value

    def onCustomiseParameters(self, evt):

        dlg = dialog_customise_user_annotations(self, self.config)
        dlg.ShowModal()

    def onFixIntensity(self, evt):

        if self.manual_add_only:
            return

        rows = self.peaklist.GetItemCount()
        if rows == 0:
            return

        for row in range(rows):
            if self.peaklist.IsChecked(index=row):
                position = None

                min_value = str2num(self.peaklist.GetItem(row, self.annotation_list['min']).GetText())
                max_value = str2num(self.peaklist.GetItem(row, self.annotation_list['max']).GetText())

                mz_narrow = pr_utils.get_narrow_data_range(data=self.kwargs["data"],
                                                           mzRange=[min_value, max_value])
                intensity = pr_utils.find_peak_maximum(mz_narrow)
                max_index = where(mz_narrow[:, 1] == intensity)[0]
                intensity = round(intensity, 2)

                if position in ["", "None", None, False]:
                    try:
                        position = mz_narrow[max_index, 0]
                    except Exception:
                        position = max_value - ((max_value - min_value) / 2)

                try:
                    position = position[0]
                except Exception:
                    pass
                self.peaklist.SetStringItem(index=row,
                                            col=self.annotation_list["intensity"],
                                            label=str(intensity))
                self.peaklist.SetStringItem(index=row,
                                            col=self.annotation_list['position'],
                                            label=str((position)))

                self.onUpdateAnnotation(row)

        # update document
        self.documentTree.onUpdateAnotations(self.kwargs['annotations'],
                                             self.kwargs['document'],
                                             self.kwargs['dataset'],
                                             set_data_only=True)

    def onOpenPeakList(self, evt):
        """
        This function opens a formatted CSV file with peaks
        """
        dlg = wx.FileDialog(self, "Choose a text file (m/z, window size, charge):",
                            wildcard="*.csv;*.txt",
                            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_CANCEL:
            return
        else:

            # Create shortcut
            delimiter, __ = checkExtension(input=dlg.GetPath().encode('ascii', 'replace'))
            peaklist = read_csv(dlg.GetPath(), delimiter=delimiter)
            peaklist = peaklist.fillna("")

            columns = peaklist.columns.values.tolist()
            for min_name in ["min", "min m/z"]:
                if min_name in columns:
                    break
                else:
                    continue
            if min_name not in columns:
                min_name = None

            for max_name in ["max", "max m/z"]:
                if max_name in columns:
                    break
                else:
                    continue
            if max_name not in columns:
                max_name = None

            for position_name in ["position"]:
                if position_name in columns:
                    break
                else:
                    continue
            if position_name not in columns:
                position_name = None

            for charge_name in ["z", "charge"]:
                if charge_name in columns:
                    break
                else:
                    continue
            if charge_name not in columns:
                charge_name = None

            for label_name in ["label", "information"]:
                if label_name in columns:
                    break
                else:
                    continue
            if label_name not in columns:
                label_name = None

            for color_name in ["color", "colour"]:
                if color_name in columns:
                    break
                else:
                    continue
            if color_name not in columns:
                color_name = None

            for intensity_name in ["intensity"]:
                if intensity_name in columns:
                    break
                else:
                    continue
            if intensity_name not in columns:
                intensity_name = None

            if min_name is None or max_name is None:
                return

            # iterate
            color_value = str(convertRGB255to1(self.colorBtn.GetBackgroundColour()))
            arrow = False
            for peak in range(len(peaklist)):
                min_value = peaklist[min_name][peak]
                max_value = peaklist[max_name][peak]
                if position_name is not None:
                    position = peaklist[position_name][peak]
                else:
                    position = max_value - ((max_value - min_value) / 2)

                in_table, __ = self.checkDuplicate(min_value, max_value)

                if in_table:
                    continue

                if intensity_name is not None:
                    intensity = peaklist[intensity_name][peak]
                else:
                    intensity = round(pr_utils.find_peak_maximum(pr_utils.get_narrow_data_range(data=self.kwargs["data"],
                                                                                                mzRange=[min_value, max_value]),
                                                                 fail_value=0.),
                                      2)
                if charge_name is not None:
                    charge_value = peaklist[charge_name][peak]
                else:
                    charge_value = ""

                if label_name is not None:
                    label_value = peaklist[label_name][peak]
                else:
                    label_value = ""

                self.peaklist.Append(["", str(min_value), str(max_value),
                                      str(position),
                                      str(intensity),
                                      str(charge_value),
                                      str(label_value),
                                      str(color_value),
                                      str(arrow)])

                annotation_dict = {"min": min_value,
                                   "max": max_value,
                                   "charge": charge_value,
                                   "intensity": intensity,
                                   "label": label_value,
                                   'color': literal_eval(color_value),
                                   'isotopic_x': position,
                                   'isotopic_y': intensity}

                name = "{} - {}".format(min_value, max_value)
                self.kwargs['annotations'][name] = annotation_dict

            self.documentTree.onUpdateAnotations(self.kwargs['annotations'],
                                                 self.kwargs['document'],
                                                 self.kwargs['dataset'])

            dlg.Destroy()

    def on_change_item_parameter(self, evt):
        """ Iterate over list to assign charge state """

        rows = self.peaklist.GetItemCount()
        if rows == 0:
            return

        if evt == "label":
            ask_kwargs = {'static_text': 'Assign label for selected items',
                          'value_text': "", 'validator': 'str', 'keyword': 'label'}

        elif evt.GetId() == ID_annotPanel_assignChargeState_selected:
            ask_kwargs = {'static_text': 'Assign charge state for selected items.',
                          'value_text': "", 'validator': 'integer', 'keyword': 'charge'}

        ask = DialogAsk(self, **ask_kwargs)
        if ask.ShowModal() == wx.ID_OK:
            pass

        if self.ask_value is None:
            return

        for row in range(rows):
            if self.peaklist.IsChecked(index=row):
                self.peaklist.SetStringItem(index=row,
                                            col=self.annotation_list[ask_kwargs['keyword']],
                                            label=str(self.ask_value))
                self.onUpdateAnnotation(row)

        # update document
        self.documentTree.onUpdateAnotations(self.kwargs['annotations'],
                                             self.kwargs['document'],
                                             self.kwargs['dataset'],
                                             set_data_only=True)

    def onDeleteItems(self, evt):
        rows = self.peaklist.GetItemCount() - 1

        if evt.GetId() == ID_annotPanel_deleteSelected_selected:
            while rows >= 0:
                if self.peaklist.IsChecked(index=rows):
                    min_value = str2num(self.peaklist.GetItem(rows, self.annotation_list['min']).GetText())
                    max_value = str2num(self.peaklist.GetItem(rows, self.annotation_list['max']).GetText())
                    self.onRemove(None, min_value, max_value)
                rows -= 1

    def onChangeColour(self, evt):
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
        if evt.GetId() == ID_annotPanel_assignColor_selected:
            rows = self.peaklist.GetItemCount()
            for row in range(rows):
                if self.peaklist.IsChecked(index=row):
                    self.peaklist.SetStringItem(index=row,
                                                col=self.annotation_list["color"],
                                                label=str(convertRGB255to1(newColour)))
                    self.onUpdateAnnotation(row)

            # update document
            self.documentTree.onUpdateAnotations(self.kwargs['annotations'],
                                                 self.kwargs['document'],
                                                 self.kwargs['dataset'],
                                                 set_data_only=True)
        else:
            self.config.interactive_ms_annotations_color = convertRGB255to1(newColour)
            self.colorBtn.SetBackgroundColour(newColour)

#     def OnGetColumnClick(self, evt):
#         column = evt.GetColumn()
#
#         if column == self.annotation_list['check']:
#             self.OnCheckAllItems()
#         else:
#             if self.lastColumn is None:
#                 self.lastColumn = column
#             elif self.lastColumn == column:
#                 if self.reverse :
#                     self.reverse = False
#                 else:
#                     self.reverse = True
#             else:
#                 self.reverse = False
#                 self.lastColumn = column
#
#             columns = self.peaklist.GetColumnCount()
#             rows = self.peaklist.GetItemCount()
#
#             tempData = []
#             for row in range(rows):
#                 tempRow = []
#                 for col in range(columns):
#                     item = self.peaklist.GetItem(itemId=row, col=col)
#                     tempRow.append(item.GetText())
#                 tempRow.append(self.peaklist.IsChecked(index=row))
#                 tempData.append(tempRow)
#
#             # Sort data
#             tempData = natsorted(tempData, key=itemgetter(column), reverse=self.reverse)
#             # Clear table
#             self.peaklist.DeleteAllItems()
#
#             checkData = []
#             for check in tempData:
#                 checkData.append(check[-1])
#                 del check[-1]
#
#             # Reinstate data
#             rowList = arange(len(tempData))
#             for row, check in zip(rowList, checkData):
#                 self.peaklist.Append(tempData[row])
#                 self.peaklist.CheckItem(row, check)

#     def OnCheckAllItems(self):
#         """
#         Check/uncheck all items in the list
#         """
#         self.check_all = not self.check_all
#
#         rows = self.peaklist.GetItemCount()
#
#         for row in range(rows):
#             self.peaklist.CheckItem(row, check=self.check_all)

    def on_select_item(self, evt):

        self.item_loading_lock = True

        # populate values
        min_value = self.peaklist.GetItem(self.peaklist.item_id, self.annotation_list['min']).GetText()
        self.min_value.SetValue(min_value)
        max_value = self.peaklist.GetItem(self.peaklist.item_id, self.annotation_list['max']).GetText()
        self.max_value.SetValue(max_value)
        intensity = self.peaklist.GetItem(self.peaklist.item_id, self.annotation_list['intensity']).GetText()
        self.intensity_value.SetValue(intensity)
        charge = self.peaklist.GetItem(self.peaklist.item_id, self.annotation_list['charge']).GetText()
        self.charge_value.SetValue(charge)
        label = self.peaklist.GetItem(self.peaklist.item_id, self.annotation_list['label']).GetText()
        self.label_value.SetValue(label)

        color = self.peaklist.GetItem(self.peaklist.item_id, self.annotation_list['color']).GetText()
        if color in ["", "None", None]:
            color = self.config.interactive_ms_annotations_color
        self.colorBtn.SetBackgroundColour(convertRGB1to255(literal_eval(color)))

        try:
            annotations = self.kwargs['annotations']["{} - {}".format(str2num(min_value), str2num(max_value))]
            position = annotations['isotopic_x']
        except Exception:
            position = str2num(max_value) - ((str2num(max_value) - str2num(min_value)) / 2)

        self.position_value.SetValue(str(position))
        add_arrow = annotations.get('add_arrow', False)
        self.add_arrow_to_peak.SetValue(add_arrow)
        position_label_x = annotations.get('position_label_x', position)
        self.position_x_value.SetValue(str(position_label_x))
        position_label_y = annotations.get('position_label_y', intensity)
        self.position_y_value.SetValue(str(position_label_y))

        self.item_loading_lock = False

        if self.manual_add_only:
            return

        if self.data_xmin is not None:
            if self.data_xmin > str2num(min_value):
                return

        if str2num(intensity) == 0.:
            return

        # put a red patch around the peak of interest and zoom-in on the peak
        window_size = self.zoom_window_size.GetValue()
        intensity = str2num(intensity) * 1.5

        if self.highlight_on_selection.GetValue():
            self.plot.plot_add_patch(str2num(position) - self.config.annotation_patch_width * 0.5, 0,
                                     self.config.annotation_patch_width,
                                     intensity * 10,
                                     color="r",
                                     alpha=self.config.annotation_patch_transparency, add_temporary=True)
            self.plot.repaint()

        if self.zoom_on_selection.GetValue():
            self.plot.on_zoom(str2num(min_value) - window_size, str2num(max_value) + window_size, intensity)

    def onPopulateTable(self):

        for key in self.kwargs["annotations"]:
            color = self.kwargs["annotations"][key].get('color', self.config.interactive_ms_annotations_color)
            if color in ["", None, "None"]:
                color = self.config.interactive_ms_annotations_color

            label_tag = re_split(' - ', key)
            self.peaklist.Append(["",
                                  label_tag[0],  # self.kwargs["annotations"][key]['min'],
                                  label_tag[1],  # self.kwargs["annotations"][key]['max'],
                                  self.kwargs["annotations"][key]['isotopic_x'],
                                  self.kwargs["annotations"][key]['intensity'],
                                  self.kwargs["annotations"][key]['charge'],
                                  self.kwargs["annotations"][key]['label'],
                                  color,
                                  self.kwargs["annotations"][key].get('add_arrow', False)
                                  ])

    def onUpdateAnnotations(self, document_title, dataaset_title, annotations):
        if (document_title == self.kwargs['document'] and
                dataaset_title == self.kwargs['dataset']):

            self.kwargs['annotations'] = annotations

    def add_annotation_from_mouse_evt(self, xmin, xmax, ymin, ymax):
        # set them in correct order
        if xmax < xmin:
            xmin, xmax = xmax, xmin

        if ymax < ymin:
            ymin, ymax = ymax, ymin

        # set intensity
        intensity = round(average([ymin, ymax]), 4)

        # set to 4 decimal places
        min_value = round(xmin, 4)
        max_value = round(xmax, 4)

        try:
            mz_narrow = pr_utils.get_narrow_data_range(
                data=self.kwargs["data"], mzRange=[min_value, max_value])
            intensity = pr_utils.find_peak_maximum(mz_narrow)
            max_index = where(mz_narrow[:, 1] == intensity)[0]
            intensity = round(intensity, 2)
        except TypeError:
            pass
        try:
            position = mz_narrow[max_index, 0][0]
        except Exception:
            position = max_value - ((max_value - min_value) / 2)

        try:
            charge = self.data_processing.predict_charge_state(
                self.kwargs['data'][:, 0], self.kwargs['data'][:, 1],
                [min_value, max_value], std_dev=self.config.annotation_charge_std_dev)
        except TypeError:
            charge = 0

        # set values
#         try:
        self.min_value.SetValue(str(min_value))
        self.max_value.SetValue(str(max_value))
        self.position_value.SetValue(str(position))
        self.intensity_value.SetValue(str(intensity))
        self.charge_value.SetValue(str(charge))
        self.charge_value.SetFocus()
        self.label_value.SetValue("")
        self.position_x_value.SetValue(str(position))
        self.position_y_value.SetValue(str(intensity))
        self.add_arrow_to_peak.SetValue(False)
        self.position_x_value.SetValue("")
        self.position_y_value.SetValue("")
#         except Exception: pass

        self.addBtn.SetFocus()

    def onMarkOnSpectrum(self, evt):
        marking_state = self.markTgl.GetValue()
        if not marking_state:
            self.markTgl.SetLabel('Annotating: Off')
            self.markTgl.SetForegroundColour(wx.WHITE)
            self.markTgl.SetBackgroundColour(wx.RED)
        else:
            self.markTgl.SetLabel('Annotating: On')
            self.markTgl.SetForegroundColour(wx.WHITE)
            self.markTgl.SetBackgroundColour(wx.BLUE)

        self.plot._on_mark_annotation(state=marking_state)

    def onUpdateAnnotation(self, index):
        min_value = self.peaklist.GetItem(index, self.annotation_list['min']).GetText()
        max_value = self.peaklist.GetItem(index, self.annotation_list['max']).GetText()
        charge_value = self.peaklist.GetItem(index, self.annotation_list['charge']).GetText()
        label_value = self.peaklist.GetItem(index, self.annotation_list['label']).GetText()
        color_value = self.peaklist.GetItem(index, self.annotation_list['color']).GetText()
        intensity_value = self.peaklist.GetItem(index, self.annotation_list['intensity']).GetText()

        name = "{} - {}".format(min_value, max_value)
        self.kwargs['annotations'][name]['charge'] = charge_value
        self.kwargs['annotations'][name]['label'] = label_value
        self.kwargs['annotations'][name]['color'] = literal_eval(color_value)
        self.kwargs['annotations'][name]['intensity'] = str2num(intensity_value)
        self.kwargs['annotations'][name]['isotopic_y'] = str2num(intensity_value)

    def get_annotation(self, min_value, max_value):
        name = "{} - {}".format(min_value, max_value)
        return self.kwargs['annotations'].get(name, {})

    def onAddAnnotation(self, evt):
        if self.item_loading_lock:
            return

        # trigger events
        self.on_toggle_controls(None)

        min_value = str2num(self.min_value.GetValue())
        max_value = str2num(self.max_value.GetValue())
        charge_value = str2int(self.charge_value.GetValue())
        label_value = self.label_value.GetValue()
        color_value = str(convertRGB255to1(self.colorBtn.GetBackgroundColour()))
        intensity = str2num(self.intensity_value.GetValue())
        position = str2num(self.position_value.GetValue())
        add_arrow = self.add_arrow_to_peak.GetValue()
        position_label_x = str2num(self.position_x_value.GetValue())
        position_label_y = str2num(self.position_y_value.GetValue())

        if position_label_x in [None, "None", ""]:
            position_label_x = position
        if position_label_y in [None, "None", ""]:
            position_label_y = intensity

        label_format = self.label_format.GetStringSelection()
        if label_value in ["", None, "None"]:
            label_value = self._convert_str_to_unicode(str(charge_value), return_type=label_format)

        name = "{} - {}".format(min_value, max_value)

        # check for duplicate
        in_table, index = self.checkDuplicate(min_value, max_value)
        if in_table:
            # annotate duplicate item
            if index != -1:
                self.kwargs['annotations'][name]['charge'] = charge_value
                self.peaklist.SetStringItem(index, self.annotation_list['charge'], str(charge_value))

                if intensity not in ["", "None", None, False]:
                    self.kwargs['annotations'][name]['intensity'] = intensity
                    self.kwargs['annotations'][name]['isotopic_y'] = intensity
                    self.peaklist.SetStringItem(index, self.annotation_list['intensity'], str(intensity))

                if position not in ["", "None", None, False]:
                    self.kwargs['annotations'][name]['isotopic_x'] = position
                    self.peaklist.SetStringItem(index, self.annotation_list['position'], str((position)))

                self.kwargs['annotations'][name]['add_arrow'] = add_arrow
                self.peaklist.SetStringItem(index, self.annotation_list['arrow'], str(add_arrow))

                self.kwargs['annotations'][name]['position_label_x'] = position_label_x
                self.kwargs['annotations'][name]['position_label_y'] = position_label_y

                self.kwargs['annotations'][name]['label'] = label_value
                self.peaklist.SetStringItem(index, self.annotation_list['label'], label_value)

                self.kwargs['annotations'][name]['color'] = literal_eval(color_value)
                self.peaklist.SetStringItem(index, self.annotation_list['color'], color_value)

            self.documentTree.onUpdateAnotations(self.kwargs['annotations'],
                                                 self.kwargs['document'],
                                                 self.kwargs['dataset'],
                                                 set_data_only=True)
            return

        if min_value is None or max_value is None:
            dlgBox("Error", "Please fill min, max fields at least!",
                   type="Error")
            return

        if charge_value is None:
            charge_value = 0

        if intensity in ["", "None", None, False] and self.kwargs['data'] and not self.manual_add_only:
            mz_narrow = pr_utils.get_narrow_data_range(data=self.kwargs["data"],
                                                       mzRange=[min_value, max_value])
            intensity = pr_utils.find_peak_maximum(mz_narrow)
            max_index = where(mz_narrow[:, 1] == intensity)[0]
            intensity = round(intensity, 2)

        if position in ["", "None", None, False]:
            try:
                position = mz_narrow[max_index, 0]
            except Exception:
                position = max_value - ((max_value - min_value) / 2)

        try:
            if len(position) > 1:
                position = position[0]
        except Exception:
            pass

        annotation_dict = {"min": min_value,
                           "max": max_value,
                           "charge": charge_value,
                           "intensity": intensity,
                           "label": label_value,
                           'color': literal_eval(color_value),
                           'isotopic_x': position,
                           'isotopic_y': intensity,
                           'add_arrow': add_arrow,
                           'position_label_x': position_label_x,
                           'position_label_y': position_label_y}

        self.kwargs['annotations'][name] = annotation_dict
        self.peaklist.Append(["", min_value, max_value, position, intensity,
                              charge_value, label_value, color_value, str(add_arrow)])

        if not self.manual_add_only:
            plt_kwargs = self._buildPlotParameters(plotType="label")
            self.plot.plot_add_text_and_lines(xpos=position, yval=intensity,
                                              label=charge_value, **plt_kwargs)
            self.plot.repaint()

        self.documentTree.onUpdateAnotations(self.kwargs['annotations'],
                                             self.kwargs['document'],
                                             self.kwargs['dataset'])

    def onRemove(self, evt, min_value=None, max_value=None):
        if min_value is None and max_value is None:
            min_value = str2num(self.min_value.GetValue())
            max_value = str2num(self.max_value.GetValue())

        __, index = self.checkDuplicate(min_value, max_value)

        if index != -1:
            self.peaklist.DeleteItem(index)
            name = "{} - {}".format(min_value, max_value)
            del self.kwargs['annotations'][name]
            print(("Removed {} from annotations".format(name)))
            # update annotations
            self.documentTree.onUpdateAnotations(self.kwargs['annotations'],
                                                 self.kwargs['document'],
                                                 self.kwargs['dataset'])
            self.peaklist.SetFocus()
            if (index) != -1:
                self.peaklist.Select(index, on=1)
            if self.peaklist.GetItemCount() == 0:
                self.min_value.SetValue("")
                self.max_value.SetValue("")
                self.charge_value.SetValue("")
                self.label_value.SetValue("")

    def onShowOnPlot(self, evt):

        evtID = evt.GetId()
        # clear plot
        self.plot.plot_remove_text_and_lines()
        # prepare plot kwargs
        label_kwargs = self._buildPlotParameters(plotType="label")
        arrow_kwargs = self._buildPlotParameters(plotType="arrow")
        vline = False
        _ymax = []
        for key in self.kwargs['annotations']:
            # get annotation
            annotation = self.kwargs['annotations'][key]
            intensity = str2num(annotation['intensity'])
            charge = annotation['charge']
            label = annotation['label']
            min_x_value = annotation['min']
            max_x_value = annotation['max']
            color_value = annotation.get('color', self.config.interactive_ms_annotations_color)
            add_arrow = annotation.get('add_arrow', False)

            if 'isotopic_x' in annotation:
                mz_value = annotation['isotopic_x']
                if mz_value in ["", 0] or mz_value < min_x_value:
                    mz_value = max_x_value - ((max_x_value - min_x_value) / 2)
            else:
                mz_value = max_x_value - ((max_x_value - min_x_value) / 2)

            label_x_position = annotation.get('position_label_x', mz_value)
            label_y_position = annotation.get('position_label_y', intensity)

            if evtID == ID_annotPanel_show_charge:
                show_label = charge
            elif evtID == ID_annotPanel_show_label:
                show_label = _replace_labels(label)
            elif evtID == ID_annotPanel_show_mzAndIntensity:
                show_label = "{:.2f}, {}\nz={}".format(mz_value, intensity, charge)

            if show_label == "":
                return

            # arrows have 4 positional parameters:
            #    xpos, ypos = correspond to the label position
            #    dx, dy = difference between label position and peak position
            if add_arrow and self.showLabelsAtIntensity:
                arrow_x_end = annotation.get('isotopic_x', label_x_position)
                arrow_dx = arrow_x_end - label_x_position
                arrow_y_end = annotation.get('isotopic_y', label_y_position)
                arrow_dy = arrow_y_end - label_y_position

            # add  custom name tag
            obj_name_tag = "{}|-|{}|-|{} - {}|-|{}".format(
                self.kwargs['document'], self.kwargs['dataset'], min_x_value, max_x_value,
                "annotation")
            label_kwargs['text_name'] = obj_name_tag

            self.plot.plot_add_text_and_lines(
                xpos=label_x_position, yval=label_y_position,
                label=show_label, vline=vline,
                vline_position=mz_value,
                stick_to_intensity=self.showLabelsAtIntensity,
                yoffset=self.config.annotation_label_y_offset,
                color=color_value, **label_kwargs)

            _ymax.append(label_y_position)
            if add_arrow and self.showLabelsAtIntensity:
                arrow_list = [label_x_position, label_y_position, arrow_dx, arrow_dy]
                arrow_kwargs['text_name'] = obj_name_tag
                arrow_kwargs['props'] = [arrow_x_end, arrow_y_end]
                self.plot.plot_add_arrow(
                    arrow_list, stick_to_intensity=self.showLabelsAtIntensity,
                    **arrow_kwargs)

        if self.adjustLabelPosition:
            self.plot._fix_label_positions()

        # update intensity
        if self.config.annotation_zoom_y:
            try:
                self.plot.on_zoom_y_axis(endY=amax(_ymax) * self.config.annotation_zoom_y_multiplier)
            except TypeError:
                pass

        self.plot.repaint()

    def onUpdateLabel(self, evt):
        evtID = evt.GetId()
        label_format = self.label_format.GetStringSelection()
        if evtID == ID_annotPanel_assignLabel_selected:
            rows = self.peaklist.GetItemCount()
            for row in range(rows):
                if self.peaklist.IsChecked(index=row):
                    charge_value = self.peaklist.GetItem(row, self.annotation_list['charge']).GetText()
                    label_value = self._convert_str_to_unicode(str(charge_value), return_type=label_format)
                    self.peaklist.SetStringItem(index=row,
                                                col=self.annotation_list['label'],
                                                label=label_value)
                    self.onUpdateAnnotation(row)

            # update document
            self.documentTree.onUpdateAnotations(self.kwargs['annotations'],
                                                 self.kwargs['document'],
                                                 self.kwargs['dataset'])
        else:
            if self.peaklist.item_id is None:
                return

            charge_value = self.peaklist.GetItem(self.peaklist.item_id, self.annotation_list['charge']).GetText()
            label_value = self._convert_str_to_unicode(str(charge_value), return_type=label_format)
            self.label_value.SetValue(label_value)

    def onSavePeaklist(self, evt):
        from pandas import DataFrame
        peaklist = []
        for key in self.kwargs['annotations']:
            annotation = self.kwargs['annotations'][key]
            intensity = str2num(annotation['intensity'])
            charge = annotation['charge']
            label = annotation['label']
            min_value = annotation['min']
            max_value = annotation['max']
            isotopic_x = annotation.get('isotopic_x', "")
            peaklist.append([min_value, max_value, isotopic_x, intensity, charge, label])

        # make dataframe
        columns = ["min", "max", "position", "intensity", "charge", "label"]
        df = DataFrame(data=peaklist, columns=columns)

        # save
        wildcard = "CSV (Comma delimited) (*.csv)|*.csv|" + \
                   "Text (Tab delimited) (*.txt)|*.txt|" + \
                   "Text (Space delimited (*.txt)|*.txt"

        wildcard_dict = {',': 0, '\t': 1, ' ': 2}
        dlg = wx.FileDialog(self, "Please select a name for the file",
                            "", "", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        dlg.CentreOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            separator = list(wildcard_dict.keys())[list(wildcard_dict.values()).index(dlg.GetFilterIndex())]
            try:
                df.to_csv(path_or_buf=filename, sep=separator)
                print(("Saved peaklist to {}".format(filename)))
            except IOError:
                print("Could not save file as it is currently open in another program")

    def checkDuplicate(self, min_value, max_value):
        count = self.peaklist.GetItemCount()
        for i in range(count):
            table_min = str2num(self.peaklist.GetItem(i, self.annotation_list['min']).GetText())
            table_max = str2num(self.peaklist.GetItem(i, self.annotation_list['max']).GetText())

            if min_value == table_min and max_value == table_max:
                return True, i
            else:
                continue

        return False, -1

    def _convert_str_to_unicode(self, s, return_type="superscript"):

        if "+" not in s and "-" not in s and return_type not in ['charge-only [n+]', 'charge-only [+n]']:
            s = "+{}".format(s)

        if return_type == "None":
            return ""
        elif return_type == "charge-only [+n]":
            return "+{}".format(s)
        elif return_type == "charge-only [n+]":
            return "{}+".format(s)
        elif return_type == "superscript":
            unicode_string = ''.join(dict(list(zip("+-0123456789", "⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))).get(c, c) for c in s)
            return unicode_string
        elif return_type == "M+nH":
            unicode_string = ''.join(dict(list(zip("+-0123456789", "⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))).get(c, c) for c in s)
            modified_label = "[M{}H]{}".format(s, unicode_string)
            return modified_label
        elif return_type == "2M+nH":
            unicode_string = ''.join(dict(list(zip("+-0123456789", "⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))).get(c, c) for c in s)
            modified_label = "[2M{}H]{}".format(s, unicode_string)
            return modified_label
        elif return_type == "3M+nH":
            unicode_string = ''.join(dict(list(zip("+-0123456789", "⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))).get(c, c) for c in s)
            modified_label = "[3M{}H]{}".format(s, unicode_string)
            return modified_label
        elif return_type == "4M+nH":
            unicode_string = ''.join(dict(list(zip("+-0123456789", "⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))).get(c, c) for c in s)
            modified_label = "[4M{}H]{}".format(s, unicode_string)
            return modified_label
        else:
            return s

    def _buildPlotParameters(self, plotType="label"):
        if plotType == "arrow":
            kwargs = {'arrow_line_width': self.config.annotation_arrow_line_width,
                      'arrow_line_style': self.config.annotation_arrow_line_style,
                      'arrow_head_length': self.config.annotation_arrow_cap_length,
                      'arrow_head_width': self.config.annotation_arrow_cap_width}

        elif plotType == "label":
            kwargs = {'horizontalalignment': self.config.annotation_label_horz,
                      'verticalalignment': self.config.annotation_label_vert,
                      'fontweight': self.config.annotation_label_font_weight,
                      'fontsize': self.config.annotation_label_font_size,
                      'rotation': self.config.annotation_label_font_orientation

                      }
        return kwargs
