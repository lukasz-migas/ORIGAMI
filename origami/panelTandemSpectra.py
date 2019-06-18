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

# Load libraries
import wx
import wx.lib.mixins.listctrl as listmix
from natsort import natsorted
from operator import itemgetter
import numpy as np
from time import time as ttime
from re import split as re_split

from toolbox import (str2num, str2int, str2bool, removeListDuplicates)
from styles import (makeCheckbox, makeStaticBox, makeMenuItem)
from gui_elements.dialog_customise_peptide_annotations import dialog_customise_peptide_annotations
from gui_elements.misc_dialogs import dlgBox
from ids import (ID_tandemPanel_otherSettings, ID_tandemPanel_showPTMs,
                 ID_tandemPanel_peaklist_show_selected,
                 ID_tandemPanel_showUnidentifiedScans,
                 ID_tandemPanel_sort_peptide_by_AZ,
                 ID_tandemPanel_sort_peptide_by_length)


class EditableListCtrl(wx.ListCtrl, listmix.CheckListCtrlMixin):
    """
    Editable list
    """

    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.CheckListCtrlMixin.__init__(self)


class panelTandemSpectra(wx.MiniFrame):
    """
    Simple GUI to visualise and edit features
    """

    def __init__(self, parent, presenter, config, icons, **kwargs):
        wx.MiniFrame.__init__(self, parent, -1, 'MS/MS spectra...', size=(-1, -1),
                              style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER |
                              wx.MAXIMIZE_BOX)

        self.view = self
        self.presenter = presenter
        self.config = config
        self.icons = icons
        self.data_processing = self.presenter.data_processing

        self.peaklist_page = "All scans"
        self.n_loaded_scans = 0
        self.fragment_ions = {}

        # peaklist
        self.check_all = False
        self.currentItem = None
        self.reverse = False
        self.lastColumn = None

        self.__gui__ = {}

        # fraglist
        self.frag_check_all = False
        self.frag_reverse = False
        self.frag_lastColumn = None
        self.frag_currentItem = None

        # peaklist_selected
        self.selected_check_all = False
        self.selected_reverse = False
        self.selected_lastColumn = None
        self.selected_currentItem = None

        self.verbose = True
        self.butterfly_plot = False

        # make gui items
        self.make_gui()
        self.Centre()
        self.Show(True)
        self.SetFocus()

        self._fragments = self._build_fragment_search_query()

        if "document" in kwargs:
            scans = len(list(kwargs['tandem_spectra'].keys()))
            self.SetTitle("MS/MS spectra - {} - Scans: {}".format(kwargs['document'], scans))

        self.kwargs = kwargs

        if "tandem_spectra" in kwargs:
            self.on_populate_table()

        # bind events
        wx.EVT_CLOSE(self, self.on_close)

    def onThreading(self, evt, args, action):
        if action == "annotate_fragments":
            pass

    def on_tool_menu(self, evt):

        self.Bind(wx.EVT_MENU, self.on_sort, id=ID_tandemPanel_sort_peptide_by_AZ)
        self.Bind(wx.EVT_MENU, self.on_sort, id=ID_tandemPanel_sort_peptide_by_length)

        menu = wx.Menu()
        self.menu_tool_sort_peptide_az = makeMenuItem(parent=menu, id=ID_tandemPanel_sort_peptide_by_AZ,
                                                      text='Sort by A-Z', bitmap=None)
        menu.AppendItem(self.menu_tool_sort_peptide_az)
        self.menu_tool_sort_peptide_length = makeMenuItem(parent=menu, id=ID_tandemPanel_sort_peptide_by_length,
                                                          text='Sort by size', bitmap=None)
        menu.AppendItem(self.menu_tool_sort_peptide_length)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_sort(self, evt):

        if evt.GetId() == ID_tandemPanel_sort_peptide_by_AZ:
            self.sort_by_column_peaklist(column=self.__gui__['peaklist_all_column'])
        elif evt.GetId() == ID_tandemPanel_sort_peptide_by_length:
            self.sort_by_column_peaklist(column=self.__gui__['peaklist_all_column'],
                                         sort_type="length")

    def onRightClickMenu_peaklist(self, evt):

        self.Bind(wx.EVT_MENU, self.on_keep_selected_peaklist, id=ID_tandemPanel_peaklist_show_selected)

        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_tandemPanel_peaklist_show_selected,
                                     text='Hide unselected items',
                                     bitmap=None))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def onCustomiseParameters(self, evt):

        dlg = dialog_customise_peptide_annotations(self, self.config)
        dlg.ShowModal()

    def on_show_PTMs_peaklist(self, evt):
        self.config._tandem_show_PTMs_in_table = not self.config._tandem_show_PTMs_in_table

        # clear table
        self.peaklist.DeleteAllItems()

        if "tandem_spectra" in self.kwargs:
            self.on_populate_table()

    def on_show_unidentified_peaklist(self, evt):
        self.config._tandem_show_unidentified_in_table = not self.config._tandem_show_unidentified_in_table

        # clear table
        self.peaklist.DeleteAllItems()

        if "tandem_spectra" in self.kwargs:
            self.on_populate_table()

    def on_keep_selected_peaklist(self, evt):
        print("This action does nothing at the moment!")
        pass

    def on_check_item_peaklist(self, index, flag):
        "flag is True if the item was checked, False if unchecked"
        if flag:
            # retrieve item info
            itemInfo = self.get_item_info_peaklist(index, return_row=True)
            self.peaklist_selected.Append(itemInfo)

            self.on_remove_duplicates_peaklist_selected()

    def on_check_for_duplicates_peaklist_selected(self, table_row):
        scan_id = table_row[1]
        scan_id_id = table_row[2]
        scan_title = table_row[-1]

        rows = self.peaklist_selected.GetItemCount()
        if rows == 0:
            return False

        for i in range(rows):
            scan_id_table = self.peaklist_selected.GetItem(i, self._columns_peaklist_selected['scan ID']).GetText()
            scan_id_id_table = self.peaklist_selected.GetItem(i, self._columns_peaklist_selected['ID #']).GetText()
            scan_title_table = self.peaklist_selected.GetItem(i, self._columns_peaklist_selected['title']).GetText()
            if (scan_id == scan_id_table and
                scan_id_id == scan_id_id_table and
                scan_title == scan_title_table):
                return True

        return False

    def on_annotate_items(self, evt):
        tstart = ttime()
        count = self.peaklist_selected.GetItemCount()

        document = self.presenter.documentsDict[self.kwargs['document']]
        if "annotated_item_list" not in document.tandem_spectra:
            document.tandem_spectra['annotated_item_list'] = []

        # iterate over list
        counter = 0
        for i in range(count):
            check = self.peaklist_selected.IsChecked(index=i)
            if check:
                # get fragments
                itemInfo, document, fragments, frag_mass_list, frag_int_list, frag_label_list, frag_full_label_list = self.on_get_fragments(
                    itemID=i, document=document)

                # add fragmentation to document
                if "fragment_annotations" not in document.tandem_spectra[itemInfo['scanID']]:
                    document.tandem_spectra[itemInfo['scanID']]['fragment_annotations'] = {}

                document.tandem_spectra[itemInfo['scanID']]['fragment_annotations'][itemInfo['id_num']] = {
                    'fragment_table':fragments,
                    'fragment_mass_list':frag_mass_list,
                    'fragment_intensity_list':frag_int_list,
                    'fragment_label_list':frag_label_list,
                    'fragment_full_label_list':frag_full_label_list}

                annot_title = "{}:{}".format(itemInfo["scanID"], itemInfo["id_num"])
                document.tandem_spectra['annotated_item_list'].append(annot_title)

                # annotate table
                self.peaklist_selected.SetStringItem(i, self._columns_peaklist_selected['# matched'], str(len(fragments)))
                counter += 1

        # ensure there are no duplicates in the list
        document.tandem_spectra['annotated_item_list'] = list(set(document.tandem_spectra['annotated_item_list']))
        # update document
        self.presenter.OnUpdateDocument(document, 'no_refresh')

        print(("Annotated {} scans in {:.4f} seconds.". format(counter, ttime() - tstart)))

    def on_delete_all_annotations(self, evt):

        dlg = dlgBox(exceptionTitle='Are you sure?',
                     exceptionMsg="Are you sure you want to remove all annotations from the document? This action is irreversible.",
                     type="Question")
        if dlg == wx.ID_NO:
            self._update_status_('Operation was cancelled.')
            return
        else:
            document = self.presenter.documentsDict[self.kwargs['document']]
            count = self.peaklist_selected.GetItemCount()
            for i in range(count):
                itemInfo = self.get_item_info_peaklist_selected(i)
                document.tandem_spectra[itemInfo['scanID']]['fragment_annotations'][itemInfo['id_num']] = {}

                try:
                    annot_title = "{}:{}".format(itemInfo["scanID"], itemInfo["id_num"])
                    scan_idx = document.tandem_spectra['annotated_item_list'].index(annot_title)
                    del document.tandem_spectra['annotated_item_list'][scan_idx]
                except ValueError as e:
                    pass

            # Clear table
            document.tandem_spectra['annotated_item_list'] = []
            self.peaklist_selected.DeleteAllItems()
            self._update_status_('Deleted all items.')

            # update document
            self.presenter.OnUpdateDocument(document, 'no_refresh')

    def on_clear_annotations(self, evt):

        document = self.presenter.documentsDict[self.kwargs['document']]
        count = self.peaklist_selected.GetItemCount()
        # iterate over list
        counter = 0
        for i in range(count):
            check = self.peaklist_selected.IsChecked(index=i)
            if check:
                itemInfo = self.get_item_info_peaklist(i)
                document.tandem_spectra[itemInfo['scanID']]['fragment_annotations'][itemInfo['id_num']] = {}

                # annotate table
                self.peaklist_selected.SetStringItem(i, self._columns_peaklist_selected['# matched'], "0")
                counter += 1

        # update document
        self.presenter.OnUpdateDocument(document, 'no_refresh')

    def peaklist_page_changed(self, evt):
        self.peaklist_page = self.peaklistBook.GetPageText(self.peaklistBook.GetSelection())
        self.on_clear_peptide_table()

    def _update_status_(self, msg, duration=5):
        self.presenter.onThreading(None, (msg, 4, duration), action='updateStatusbar')

    def make_gui(self):

        # make panel
        panel = self.makePanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 5)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

        self.SetSize((685, 800))
        self.Layout()

    def make_peptide_checkbox(self, panel):
        tolerance_label = wx.StaticText(panel, wx.ID_ANY, "Tolerance:")
        self.tolerance_value = wx.SpinCtrlDouble(panel, -1,
                                                 value=str(self.config.fragments_tolerance[self.config.fragments_units]),
                                                 min=self.config.fragments_tolerance_limits[self.config.fragments_units][0],
                                                 max=self.config.fragments_tolerance_limits[self.config.fragments_units][1],
                                                 initial=self.config.fragments_tolerance[self.config.fragments_units],
                                                 inc=self.config.fragments_tolerance_limits[self.config.fragments_units][2],
                                                 size=(90, -1), name="not_update_gui")
        self.tolerance_value.Bind(wx.EVT_TEXT, self.onApply)

        tolerance_units_label = wx.StaticText(panel, wx.ID_ANY, "Tolerance units:")
        self.tolerance_choice = wx.Choice(panel, -1, choices=self.config.fragments_units_choices,
                                          size=(-1, -1))
        self.tolerance_choice.SetStringSelection(self.config.fragments_units)
        self.tolerance_choice.Bind(wx.EVT_CHOICE, self.onApply)
        self.tolerance_choice.Bind(wx.EVT_CHOICE, self.onUpdateGUI)

        max_labels_label = wx.StaticText(panel, wx.ID_ANY, "Maximum labels:")
        self.max_labels_value = wx.SpinCtrlDouble(panel, -1, value=str(self.config.fragments_max_matches), min=1,
                                                 max=5, initial=self.config.fragments_max_matches, inc=1,
                                                 size=(90, -1))
        self.max_labels_value.Bind(wx.EVT_TEXT, self.onApply)

#         fragment_presets_label = wx.StaticText(panel, wx.ID_ANY, u"Presets:")
#         self.fragment_presets_choice = wx.Choice(panel, -1, choices=natsorted(self.config.fragments_common.keys()),
#                                           size=(-1, -1))
#         self.fragment_presets_choice.SetStringSelection("b/y")
#         self.fragment_presets_choice.Bind(wx.EVT_CHOICE, self.onApply)
#         self.fragment_presets_choice.Bind(wx.EVT_CHOICE, self.on_update_presets)

        # pack elements
        tolerance_grid = wx.GridBagSizer(5, 5)
        n = 0
        tolerance_grid.Add(tolerance_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        tolerance_grid.Add(self.tolerance_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        tolerance_grid.Add(tolerance_units_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        tolerance_grid.Add(self.tolerance_choice, (n, 3), wx.GBSpan(1, 1), flag=wx.EXPAND)
        tolerance_grid.Add(max_labels_label, (n, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        tolerance_grid.Add(self.max_labels_value, (n, 5), wx.GBSpan(1, 1), flag=wx.EXPAND)
#         tolerance_grid.Add(fragment_presets_label, (n,6), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
#         tolerance_grid.Add(self.fragment_presets_choice, (n,7), wx.GBSpan(1,1), flag=wx.EXPAND)

        # M-ions
        self.peptide_M_all = makeCheckbox(panel, "P-all")
        self.peptide_M_all.SetValue(self.config.fragments_search['M-ALL'])
        self.peptide_M_all.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_M = makeCheckbox(panel, "P")
        self.peptide_M.SetValue(self.config.fragments_search['M'])
        self.peptide_M.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_M_nH2O = makeCheckbox(panel, "P-nH2O/P°")
        self.peptide_M_nH2O.SetValue(self.config.fragments_search['M-nH2O'])
        self.peptide_M_nH2O.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_M_nNH3 = makeCheckbox(panel, "P-nNH3/P*")
        self.peptide_M_nNH3.SetValue(self.config.fragments_search['M-nNH3'])
        self.peptide_M_nNH3.Bind(wx.EVT_CHECKBOX, self.onApply)

        M_ions_staticBox = makeStaticBox(panel, "Precursor", size=(-1, -1), color=wx.BLACK)
        M_ions_staticBox.SetSize((-1, -1))
        M_ions_box_sizer = wx.StaticBoxSizer(M_ions_staticBox, wx.HORIZONTAL)

        M_ions_grid = wx.GridBagSizer(2, 2)
        M_ions_grid.Add(self.peptide_M_all, (0, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        M_ions_grid.Add(self.peptide_M, (1, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        M_ions_grid.Add(self.peptide_M_nH2O, (2, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        M_ions_grid.Add(self.peptide_M_nNH3, (3, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        M_ions_box_sizer.Add(M_ions_grid, 0, wx.EXPAND, 10)

        # a-ions
        self.peptide_a_all = makeCheckbox(panel, "a-all")
        self.peptide_a_all.SetValue(self.config.fragments_search['a-ALL'])
        self.peptide_a_all.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_a = makeCheckbox(panel, "a")
        self.peptide_a.SetValue(self.config.fragments_search['a'])
        self.peptide_a.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_a_nH2O = makeCheckbox(panel, "a-nH2O/a°")
        self.peptide_a_nH2O.SetValue(self.config.fragments_search['a-nH2O'])
        self.peptide_a_nH2O.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_a_nNH3 = makeCheckbox(panel, "a-nNH3/a*")
        self.peptide_a_nNH3.SetValue(self.config.fragments_search['a-nNH3'])
        self.peptide_a_nNH3.Bind(wx.EVT_CHECKBOX, self.onApply)

        a_ions_staticBox = makeStaticBox(panel, "a-fragments", size=(-1, -1), color=wx.BLACK)
        a_ions_staticBox.SetSize((-1, -1))
        a_ions_box_sizer = wx.StaticBoxSizer(a_ions_staticBox, wx.HORIZONTAL)

        a_ions_grid = wx.GridBagSizer(2, 2)
        a_ions_grid.Add(self.peptide_a_all, (0, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        a_ions_grid.Add(self.peptide_a, (1, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        a_ions_grid.Add(self.peptide_a_nH2O, (2, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        a_ions_grid.Add(self.peptide_a_nNH3, (3, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        a_ions_box_sizer.Add(a_ions_grid, 0, wx.EXPAND, 10)

        self.peptide_b_all = makeCheckbox(panel, "b-all")
        self.peptide_b_all.SetValue(self.config.fragments_search['b-ALL'])
        self.peptide_b_all.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_b = makeCheckbox(panel, "b")
        self.peptide_b.SetValue(self.config.fragments_search['b'])
        self.peptide_b.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_b_nH2O = makeCheckbox(panel, "b-nH2O/b°")
        self.peptide_b_nH2O.SetValue(self.config.fragments_search['b-nH2O'])
        self.peptide_b_nH2O.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_b_nNH3 = makeCheckbox(panel, "b-nNH3/b*")
        self.peptide_b_nNH3.SetValue(self.config.fragments_search['b-nNH3'])
        self.peptide_b_nNH3.Bind(wx.EVT_CHECKBOX, self.onApply)

        # b-ions
        b_ions_staticBox = makeStaticBox(panel, "b-fragments", size=(-1, -1), color=wx.BLACK)
        b_ions_staticBox.SetSize((-1, -1))
        b_ions_box_sizer = wx.StaticBoxSizer(b_ions_staticBox, wx.HORIZONTAL)

        b_ions_grid = wx.GridBagSizer(2, 2)
        b_ions_grid.Add(self.peptide_b_all, (0, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        b_ions_grid.Add(self.peptide_b, (1, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        b_ions_grid.Add(self.peptide_b_nH2O, (2, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        b_ions_grid.Add(self.peptide_b_nNH3, (3, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        b_ions_box_sizer.Add(b_ions_grid, 0, wx.EXPAND, 10)

        self.peptide_c_all = makeCheckbox(panel, "c-all")
        self.peptide_c_all.SetValue(self.config.fragments_search['c-ALL'])
        self.peptide_c_all.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_c = makeCheckbox(panel, "c")
        self.peptide_c.SetValue(self.config.fragments_search['c'])
        self.peptide_c.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_c_nH2O = makeCheckbox(panel, "c-nH2O/c°")
        self.peptide_c_nH2O.SetValue(self.config.fragments_search['c-nH2O'])
        self.peptide_c_nH2O.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_c_nNH3 = makeCheckbox(panel, "c-nNH3/c*")
        self.peptide_c_nNH3.SetValue(self.config.fragments_search['c-nNH3'])
        self.peptide_c_nNH3.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_c_dot = makeCheckbox(panel, "c-dot")
        self.peptide_c_dot.SetValue(self.config.fragments_search['c-dot'])
        self.peptide_c_dot.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_c_add_1_2 = makeCheckbox(panel, "c+1/2")
        self.peptide_c_add_1_2.SetValue(self.config.fragments_search['c+1/2'])
        self.peptide_c_add_1_2.Bind(wx.EVT_CHECKBOX, self.onApply)

        # c-ions
        c_ions_staticBox = makeStaticBox(panel, "c-fragments", size=(-1, -1), color=wx.BLACK)
        c_ions_staticBox.SetSize((-1, -1))
        c_ions_box_sizer = wx.StaticBoxSizer(c_ions_staticBox, wx.HORIZONTAL)

        c_ions_grid = wx.GridBagSizer(2, 2)
        c_ions_grid.Add(self.peptide_c_all, (0, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        c_ions_grid.Add(self.peptide_c, (1, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        c_ions_grid.Add(self.peptide_c_nH2O, (2, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        c_ions_grid.Add(self.peptide_c_nNH3, (3, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        c_ions_grid.Add(self.peptide_c_dot, (4, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        c_ions_grid.Add(self.peptide_c_add_1_2, (5, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        c_ions_box_sizer.Add(c_ions_grid, 0, wx.EXPAND, 10)

        self.peptide_x_all = makeCheckbox(panel, "x-all")
        self.peptide_x_all.SetValue(self.config.fragments_search['x-ALL'])
        self.peptide_x_all.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_x = makeCheckbox(panel, "x")
        self.peptide_x.SetValue(self.config.fragments_search['x'])
        self.peptide_x.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_x_nH2O = makeCheckbox(panel, "x-nH2O/x°")
        self.peptide_x_nH2O.SetValue(self.config.fragments_search['x-nH2O'])
        self.peptide_x_nH2O.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_x_nNH3 = makeCheckbox(panel, "x-nNH3/x*")
        self.peptide_x_nNH3.SetValue(self.config.fragments_search['x-nNH3'])
        self.peptide_x_nNH3.Bind(wx.EVT_CHECKBOX, self.onApply)

        # y-ions
        x_ions_staticBox = makeStaticBox(panel, "x-fragments", size=(-1, -1), color=wx.BLACK)
        x_ions_staticBox.SetSize((-1, -1))
        x_ions_box_sizer = wx.StaticBoxSizer(x_ions_staticBox, wx.HORIZONTAL)

        x_ions_grid = wx.GridBagSizer(2, 2)
        x_ions_grid.Add(self.peptide_x_all, (0, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        x_ions_grid.Add(self.peptide_x, (1, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        x_ions_grid.Add(self.peptide_x_nH2O, (2, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        x_ions_grid.Add(self.peptide_x_nNH3, (3, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        x_ions_box_sizer.Add(x_ions_grid, 0, wx.EXPAND, 10)

        self.peptide_y_all = makeCheckbox(panel, "y-all")
        self.peptide_y_all.SetValue(self.config.fragments_search['y-ALL'])
        self.peptide_y_all.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_y = makeCheckbox(panel, "y")
        self.peptide_y.SetValue(self.config.fragments_search['y'])
        self.peptide_y.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_y_nH2O = makeCheckbox(panel, "y-nH2O/y°")
        self.peptide_y_nH2O.SetValue(self.config.fragments_search['y-nH2O'])
        self.peptide_y_nH2O.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_y_nNH3 = makeCheckbox(panel, "y-nNH3/y*")
        self.peptide_y_nNH3.SetValue(self.config.fragments_search['y-nNH3'])
        self.peptide_y_nNH3.Bind(wx.EVT_CHECKBOX, self.onApply)

        # y-ions
        y_ions_staticBox = makeStaticBox(panel, "y-fragments", size=(-1, -1), color=wx.BLACK)
        y_ions_staticBox.SetSize((-1, -1))
        y_ions_box_sizer = wx.StaticBoxSizer(y_ions_staticBox, wx.HORIZONTAL)

        y_ions_grid = wx.GridBagSizer(2, 2)
        y_ions_grid.Add(self.peptide_y_all, (0, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y_ions_grid.Add(self.peptide_y, (1, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y_ions_grid.Add(self.peptide_y_nH2O, (2, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y_ions_grid.Add(self.peptide_y_nNH3, (3, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y_ions_box_sizer.Add(y_ions_grid, 0, wx.EXPAND, 10)

        self.peptide_z_all = makeCheckbox(panel, "z-all")
        self.peptide_z_all.SetValue(self.config.fragments_search['z-ALL'])
        self.peptide_z_all.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_z = makeCheckbox(panel, "z")
        self.peptide_z.SetValue(self.config.fragments_search['z'])
        self.peptide_z.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_z_nH2O = makeCheckbox(panel, "z-nH2O/z°")
        self.peptide_z_nH2O.SetValue(self.config.fragments_search['z-nH2O'])
        self.peptide_z_nH2O.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_z_nNH3 = makeCheckbox(panel, "z-nNH3/z*")
        self.peptide_z_nNH3.SetValue(self.config.fragments_search['z-nNH3'])
        self.peptide_z_nNH3.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_z_dot = makeCheckbox(panel, "z-dot")
        self.peptide_z_dot.SetValue(self.config.fragments_search['z-dot'])
        self.peptide_z_dot.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.peptide_z_add_1_2 = makeCheckbox(panel, "z+1/2/3")
        self.peptide_z_add_1_2.SetValue(self.config.fragments_search['z+1/2/3'])
        self.peptide_z_add_1_2.Bind(wx.EVT_CHECKBOX, self.onApply)

        # z-ions
        z_ions_staticBox = makeStaticBox(panel, "z-fragments", size=(-1, -1), color=wx.BLACK)
        z_ions_staticBox.SetSize((-1, -1))
        z_ions_box_sizer = wx.StaticBoxSizer(z_ions_staticBox, wx.HORIZONTAL)

        z_ions_grid = wx.GridBagSizer(2, 2)
        z_ions_grid.Add(self.peptide_z_all, (0, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        z_ions_grid.Add(self.peptide_z, (1, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        z_ions_grid.Add(self.peptide_z_nH2O, (2, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        z_ions_grid.Add(self.peptide_z_nNH3, (3, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        z_ions_grid.Add(self.peptide_z_dot, (4, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        z_ions_grid.Add(self.peptide_z_add_1_2, (5, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        z_ions_box_sizer.Add(z_ions_grid, 0, wx.EXPAND, 10)

        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(tolerance_grid, (n, 0), wx.GBSpan(1, 7), flag=wx.EXPAND)
        n = n + 1
        grid.Add(M_ions_box_sizer, (n, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(a_ions_box_sizer, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(b_ions_box_sizer, (n, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(c_ions_box_sizer, (n, 3), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(x_ions_box_sizer, (n, 4), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(y_ions_box_sizer, (n, 5), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(z_ions_box_sizer, (n, 6), wx.GBSpan(1, 1), flag=wx.EXPAND)

        fragment_staticBox = makeStaticBox(panel, "Fragment assignment", size=(-1, -1), color=wx.BLACK)
        fragment_staticBox.SetSize((-1, -1))

        fragment_box_sizer = wx.StaticBoxSizer(fragment_staticBox, wx.HORIZONTAL)
        fragment_box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return fragment_box_sizer

    def make_peptide_list(self, panel):

        self._frag_columns = {'check':0, 'measured m/z':1, 'calculated m/z':2, 'intensity':3, 'delta':4,
                              'charge':5, 'label':6, 'full_label':7, 'peptide':8}

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.fraglist = EditableListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES)
        self.fraglist.SetFont(wx.SMALL_FONT)
        self.fraglist.InsertColumn(0, '', width=25)
        self.fraglist.InsertColumn(1, 'measured m/z', width=86)
        self.fraglist.InsertColumn(2, 'calculated m/z', width=86)
        self.fraglist.InsertColumn(3, 'intensity', width=60)
        self.fraglist.InsertColumn(4, 'Δ error', width=50)
        self.fraglist.InsertColumn(5, 'charge', width=50)
        self.fraglist.InsertColumn(6, 'label', width=70)
        self.fraglist.InsertColumn(7, 'full label', width=90)
        self.fraglist.InsertColumn(8, 'peptide', width=122)

        # bind events
        self.fraglist.Bind(wx.EVT_LIST_COL_CLICK, self.get_column_click_fragments)
        self.fraglist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_fragments)
        self.fraglist.Bind(wx.EVT_LEFT_DCLICK, self.on_zoom_on_spectrum)

        mainSizer.Add(self.fraglist, 1, wx.EXPAND | wx.ALL, 0)
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def make_modification_list(self, panel):

#         self._mod_list = {'check':0, 'delta':1, 'calculated m/z':2, 'intensity':3, 'delta':4,
#                           'charge':5, 'label':6, 'peptide':7}

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.modlist = EditableListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES)
        self.modlist.SetFont(wx.SMALL_FONT)
        self.modlist.InsertColumn(0, '', width=25)
        self.modlist.InsertColumn(1, 'peptide', width=150)
        self.modlist.InsertColumn(2, 'name', width=150)
        self.modlist.InsertColumn(3, 'Δ mass', width=100)
        self.modlist.InsertColumn(4, 'residues', width=100)
        self.modlist.InsertColumn(5, 'location', width=100)

        # bind events
#         self.modlist.Bind(wx.EVT_LIST_COL_CLICK, self.get_column_click_fragments)
#         self.modlist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_fragments)
#         self.modlist.Bind(wx.EVT_LEFT_DCLICK, self.on_zoom_on_spectrum)

        mainSizer.Add(self.modlist, 1, wx.EXPAND | wx.ALL, 0)
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def make_identification_list(self, panel):

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.identlist = EditableListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES)
        self.identlist.SetFont(wx.SMALL_FONT)

        self.identlist.InsertColumn(0, '', width=25)
#         self.identlist.InsertColumn(1,u'measured m/z', width=88)
#         self.identlist.InsertColumn(2,u'calculated m/z', width=88)
#         self.identlist.InsertColumn(3,u'Δ error', width=100)
#         self.identlist.InsertColumn(4,u'charge', width=50)
#         self.identlist.InsertColumn(5,u'label', width=150)
#         self.identlist.InsertColumn(6,u'peptide', width=150)

        # bind events
#         self.identlist.Bind(wx.EVT_LIST_COL_CLICK, self.get_column_click_fragments)

        mainSizer.Add(self.identlist, 1, wx.EXPAND | wx.ALL, 0)
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def make_peaklist_all_list(self, panel):

        self._columns_peaklist = {'check':0, 'scan ID':1, 'ID #':2, 'MSn':3, 'parent m/z':4,
                                  'charge':5, '# peaks':6, 'peptide':7, 'identification':7,
                                  'PTM':8, 'title':9}

        self.peaklist = EditableListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES)
        self.peaklist.SetFont(wx.SMALL_FONT)
        self.peaklist.InsertColumn(0, '', width=25)
        self.peaklist.InsertColumn(1, 'scan ID', width=65)
        self.peaklist.InsertColumn(2, 'ID #', width=30)
        self.peaklist.InsertColumn(3, 'MSn', width=35)
        self.peaklist.InsertColumn(4, 'parent m/z', width=65)
        self.peaklist.InsertColumn(5, 'charge', width=50)
        self.peaklist.InsertColumn(6, '# peaks', width=53)
        self.peaklist.InsertColumn(7, 'peptide', width=110)
        self.peaklist.InsertColumn(8, 'PTM', width=45)
        self.peaklist.InsertColumn(9, 'title', width=157)

        # bind events
        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_peaklist_all)
        self.peaklist.Bind(wx.EVT_LIST_COL_CLICK, self.get_column_click_peaklist)
#         self.peaklist.Bind(wx.EVT_LEFT_DCLICK, self.on_show_spectrum)
#         self.peaklist.Bind(wx.EVT_LIST_KEY_DOWN, self.on_peaklist_all_key_down)
        self.peaklist.Bind(wx.EVT_CONTEXT_MENU, self.onRightClickMenu_peaklist)
        self.peaklist.OnCheckItem = self.on_check_item_peaklist

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.peaklist, 1, wx.EXPAND | wx.ALL, 0)
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def on_peaklist_all_key_down(self, evt):
        self.currentItem = evt.m_itemIndex
        self.on_show_spectrum(evt)

    def make_peaklist_selected_list(self, panel):
        self._columns_peaklist_selected = {'check':0, 'scan ID':1, 'ID #':2, 'MSn':3, 'parent m/z':4,
                                           'charge':5, '# peaks':6, '# matched':7, 'peptide':8, 'identification':9,
                                           'PTM':9, 'title':10}

        self.peaklist_selected = EditableListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES)
        self.peaklist_selected.SetFont(wx.SMALL_FONT)
        self.peaklist_selected.InsertColumn(0, '', width=25)
        self.peaklist_selected.InsertColumn(1, 'scan ID', width=65)
        self.peaklist_selected.InsertColumn(2, 'ID #', width=30)
        self.peaklist_selected.InsertColumn(3, 'MSn', width=35)
        self.peaklist_selected.InsertColumn(4, 'parent m/z', width=65)
        self.peaklist_selected.InsertColumn(5, 'charge', width=50)
        self.peaklist_selected.InsertColumn(6, '# peaks', width=53)
        self.peaklist_selected.InsertColumn(7, '# matched', width=65)
        self.peaklist_selected.InsertColumn(8, 'peptide', width=100)
        self.peaklist_selected.InsertColumn(9, 'PTM', width=45)
        self.peaklist_selected.InsertColumn(10, 'title', width=120)

        # bind events
        self.peaklist_selected.Bind(wx.EVT_LIST_COL_CLICK, self.get_column_click_peaklist)
        self.peaklist_selected.Bind(wx.EVT_LEFT_DCLICK, self.on_show_annotated_spectrum)
        self.peaklist_selected.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_peaklist_selected)

        self.annotate_Btn = wx.Button(panel, -1, "Annotate selected", size=(-1, 25))
        self.annotate_Btn.Bind(wx.EVT_BUTTON, self.on_annotate_items)

        self.clear_Btn = wx.Button(panel, -1, "Clear annotations", size=(-1, 25))
        self.clear_Btn.Bind(wx.EVT_BUTTON, self.on_clear_annotations)

        self.delete_Btn = wx.Button(panel, -1, "Delete all", size=(-1, 25))
        self.delete_Btn.Bind(wx.EVT_BUTTON, self.on_delete_all_annotations)

        btn2_grid = wx.GridBagSizer(5, 5)
        n = 0
        btn2_grid.Add(self.annotate_Btn, (n, 0), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND)
        btn2_grid.Add(self.clear_Btn, (n, 1), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND)
        btn2_grid.Add(self.delete_Btn, (n, 2), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.peaklist_selected, 1, wx.EXPAND | wx.ALL, 0)
        mainSizer.Add(btn2_grid, 0, wx.EXPAND | wx.ALL, 0)
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def makePanel(self):

        panel = wx.Panel(self, -1, size=(-1, -1))

        fragment_box_sizer = self.make_peptide_checkbox(panel)
#         self.statusbar = self.make_statusbar()

        self.peaklistBook = wx.Notebook(panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.NB_MULTILINE)

        self.peaklist_all = wx.Panel(self.peaklistBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.peaklistBook.AddPage(self.make_peaklist_all_list(self.peaklist_all), "All scans", False)

        self.peaklist_selected = wx.Panel(self.peaklistBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.peaklistBook.AddPage(self.make_peaklist_selected_list(self.peaklist_selected), "Selected scans", False)

        self.annotationBook = wx.Notebook(panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=wx.NB_MULTILINE)

        self.annotation_peaklist = wx.Panel(self.annotationBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.annotationBook.AddPage(self.make_peptide_list(self.annotation_peaklist), "Fragment list", False)

        self.annotation_modlist = wx.Panel(self.annotationBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.annotationBook.AddPage(self.make_modification_list(self.annotation_modlist), "Modifications list", False)

        self.peaklistBook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.peaklist_page_changed)

        self.show_next_Btn = wx.Button(panel, -1, "Load {} scans".format(self.config.msms_load_n_scans), size=(-1, 25))
        self.show_next_Btn.Bind(wx.EVT_BUTTON, self.on_load_n_spectra)

        self.show_count_value = wx.SpinCtrlDouble(panel, -1, value=str(self.config.msms_load_n_scans),
                                             min=10, max=999999, inc=500,
                                             initial=self.config.msms_load_n_scans, size=(90, -1))
        self.show_count_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        self.show_all_Btn = wx.Button(panel, -1, "Load all scans", size=(-1, 25))
        self.show_all_Btn.Bind(wx.EVT_BUTTON, self.on_load_all_spectra)

        self.verbose_check = makeCheckbox(panel, "verbose")
        self.verbose_check.SetValue(self.verbose)
        self.verbose_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.butterfly_check = makeCheckbox(panel, "butterfly plot")
        self.butterfly_check.SetValue(self.butterfly_plot)
        self.butterfly_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.actionBtn = wx.Button(panel, wx.ID_OK, "Action ▼", size=(-1, 22))
        self.actionBtn.Bind(wx.EVT_BUTTON, self.onActionTool)

        btn_grid = wx.GridBagSizer(5, 5)
        n = 0
        btn_grid.Add(self.show_next_Btn, (n, 0), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND)
        btn_grid.Add(self.show_count_value, (n, 1), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND)
        btn_grid.Add(self.show_all_Btn, (n, 2), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND)
        btn_grid.Add(self.verbose_check, (n, 3), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND)
        btn_grid.Add(self.butterfly_check, (n, 4), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND)
        btn_grid.Add(self.actionBtn, (n, 5), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(btn_grid, 0, wx.EXPAND, 5)
        mainSizer.Add(fragment_box_sizer, 0, wx.EXPAND, 5)
        mainSizer.Add(self.peaklistBook, 1, wx.EXPAND | wx.ALL, 2)
        mainSizer.Add(self.annotationBook, 1, wx.EXPAND, 0)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def make_statusbar(self):

        statusbar = self.CreateStatusBar(1, wx.STB_SIZEGRIP, wx.ID_ANY)
        statusbar.SetStatusWidths([-1])
        statusbar.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        return statusbar

    def onActionTool(self, evt):
        self.Bind(wx.EVT_MENU, self.onCustomiseParameters, id=ID_tandemPanel_otherSettings)
        self.Bind(wx.EVT_MENU, self.on_show_PTMs_peaklist, id=ID_tandemPanel_showPTMs)
        self.Bind(wx.EVT_MENU, self.on_show_unidentified_peaklist, id=ID_tandemPanel_showUnidentifiedScans)

        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_tandemPanel_otherSettings,
                                     text='Customise plot settings...',
                                     bitmap=self.icons.iconsLib['settings16_2'],
                                     help_text=''))
        menu.AppendSeparator()
        self.show_unidentified_check = menu.AppendCheckItem(ID_tandemPanel_showUnidentifiedScans, "Include scans without identification", help="")
        self.show_unidentified_check.Check(self.config._tandem_show_unidentified_in_table)

        self.show_PTMs_check = menu.AppendCheckItem(ID_tandemPanel_showPTMs, "Include scans with PTMs", help="")
        self.show_PTMs_check.Check(self.config._tandem_show_PTMs_in_table)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_select_fragments(self, evt):
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_UP or key_code == wx.WXK_DOWN:
            self.frag_currentItem = evt.m_itemIndex
        else:
            self.frag_currentItem = evt.m_itemIndex

        if evt != None:
            evt.Skip()

    def on_select_peaklist_all(self, evt):
        key_code = evt.GetKeyCode()

        if key_code == wx.WXK_UP or key_code == wx.WXK_DOWN:
            self.currentItem = evt.m_itemIndex
        else:
            self.currentItem = evt.m_itemIndex

        self.on_show_spectrum(evt)

#         if evt != None:
#             evt.Skip()

    def on_select_peaklist_selected(self, evt):
        self.selected_currentItem = evt.m_itemIndex

    def on_check_all_spectrum_list(self, evt=None, add_selected=False):

        check = not self.check_all
        self.check_all = not self.check_all

        rows = self.peaklist.GetItemCount()
        for row in range(rows):
            self.peaklist.CheckItem(row, check=check)
            if check and add_selected:
                itemInfo = self.get_item_info_peaklist(row, return_row=True)
                self.peaklist_selected.Append(itemInfo)

    def on_remove_duplicates_peaklist_selected(self):
        """
        This function removes duplicates from the list
        Its not very efficient!
        """

        columns = self.peaklist_selected.GetColumnCount()
        rows = self.peaklist_selected.GetItemCount()

        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.peaklist_selected.GetItem(itemId=row, col=col)
                itemText = item.GetText()
                tempRow.append(itemText)
            tempRow.append(self.peaklist_selected.IsChecked(index=row))
            tempData.append(tempRow)

        # Remove duplicates
        tempData = removeListDuplicates(
            input=tempData,
            columnsIn=['', 'scanID', 'id', 'MSn', 'parent_mz', 'charge', 'n_peaks', 'n_matched', 'peptide',
                       'ptm', 'title', 'check'],
            limitedCols=['scanID', 'id', 'title'])

        rows = len(tempData)
        # Clear table
        self.peaklist_selected.DeleteAllItems()

        checkData = []
        for check in tempData:
            checkData.append(check[-1])
            del check[-1]

        # Reinstate data
        rowList = np.arange(len(tempData))
        for row, check in zip(rowList, checkData):
            self.peaklist_selected.Append(tempData[row])
            self.peaklist_selected.CheckItem(row, check)

    def on_check_all_peaklist_selected(self, evt=None):

        check = not self.selected_check_all
        self.selected_check_all = not self.selected_check_all

        rows = self.peaklist_selected.GetItemCount()
        for row in range(rows):
            self.peaklist_selected.CheckItem(row, check=check)

    def _dummy(self, *args, **kwargs):
        pass

    def get_column_click_peaklist(self, evt):
        column = evt.GetColumn()
        self.__gui__['peaklist_all_column'] = column

        if self.peaklist_page == "All scans":
            if column == 0:
                self.peaklist.OnCheckItem = self._dummy
                self.on_check_all_spectrum_list(add_selected=True)
                self.on_remove_duplicates_peaklist_selected()
                self.peaklist.OnCheckItem = self.on_check_item_peaklist
#             elif column == self._columns_peaklist['peptide']:
#                 self.on_tool_menu(None)
            else:
                tstart = ttime()
                self.sort_by_column_peaklist(column=column)
                print(("Sorting took {:.4f} seconds.".format(ttime() - tstart)))
        else:
            if column == 0:
                self.on_check_all_peaklist_selected()
            else:
                tstart = ttime()
                self.sort_by_column_peaklist_selected(column=column)
                print(("Sorting took {:.4f} seconds.".format(ttime() - tstart)))

    def sort_by_column_peaklist(self, column, sort_direction=None, sort_type=None):
        """
        Sort data in peaklist based on pressed column
        """
        # Check if it should be reversed
        if self.lastColumn == None:
            self.lastColumn = column
        elif self.lastColumn == column:
            if self.reverse == True:
                self.reverse = False
            else:
                self.reverse = True
        else:
            self.reverse = False
            self.lastColumn = column

        if sort_direction is None:
            sort_direction = self.reverse

        columns = self.peaklist.GetColumnCount()
        rows = self.peaklist.GetItemCount()

        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.peaklist.GetItem(itemId=row, col=col)
                itemText = item.GetText()
#                 if col == self._columns_peaklist['peptide']:
#                     peptide_length = len(itemText)
                tempRow.append(itemText)
            tempRow.append(self.peaklist.IsChecked(index=row))
#             tempRow.append(peptide_length)
            tempData.append(tempRow)

        # Sort data
#         if sort_type == None:
        tempData = natsorted(tempData, key=itemgetter(column), reverse=sort_direction)
#         elif sort_type == "length":
#             tempData = natsorted(tempData, key=len, reverse=sort_direction)
        # Clear table and reinsert data
        self.peaklist.DeleteAllItems()

        checkData = []
        for check in tempData:
#             del check[-1]
            checkData.append(check[-1])
            del check[-1]

        rowList = np.arange(len(tempData))
        for row, check in zip(rowList, checkData):
            self.peaklist.Append(tempData[row])
            self.peaklist.CheckItem(row, check)

    def sort_by_column_peaklist_selected(self, column, sort_direction=None):
        """
        Sort data in peaklist based on pressed column
        """
        # Check if it should be reversed
        if self.selected_lastColumn == None:
            self.selected_lastColumn = column
        elif self.selected_lastColumn == column:
            if self.selected_reverse == True:
                self.selected_reverse = False
            else:
                self.selected_reverse = True
        else:
            self.selected_reverse = False
            self.selected_lastColumn = column

        if sort_direction is None:
            sort_direction = self.selected_reverse

        columns = self.peaklist_selected.GetColumnCount()
        rows = self.peaklist_selected.GetItemCount()

        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.peaklist_selected.GetItem(itemId=row, col=col)
                itemText = item.GetText()
                tempRow.append(itemText)
            tempRow.append(self.peaklist_selected.IsChecked(index=row))
            tempData.append(tempRow)

        # Sort data
        tempData = natsorted(tempData, key=itemgetter(column), reverse=sort_direction)
        # Clear table and reinsert data
        self.peaklist_selected.DeleteAllItems()

        checkData = []
        for check in tempData:
            checkData.append(check[-1])
            del check[-1]

        rowList = np.arange(len(tempData))
        for row, check in zip(rowList, checkData):
            self.peaklist_selected.Append(tempData[row])
            self.peaklist_selected.CheckItem(row, check)

    def get_item_info_peaklist(self, itemID, return_list=False, return_row=False):
        """
        Helper function to provide information about selected item
        ===
        itemID:    int
            index of item in the table
        return_list:    bool
            should the data be returned as list
        return_row:    bool
            should the data be returned as a row to be inserted into another table
        """
        # get item information
        information = {'scanID':self.peaklist.GetItem(itemID, self._columns_peaklist['scan ID']).GetText(),
                       'MSlevel':str2int(self.peaklist.GetItem(itemID, self._columns_peaklist['MSn']).GetText()),
                       'precursor_mz':self.peaklist.GetItem(itemID, self._columns_peaklist['parent m/z']).GetText(),
                       'precursor_charge':self.peaklist.GetItem(itemID, self._columns_peaklist['charge']).GetText(),
                       'n_peaks':self.peaklist.GetItem(itemID, self._columns_peaklist['# peaks']).GetText(),
                       'peptide':self.peaklist.GetItem(itemID, self._columns_peaklist['peptide']).GetText(),
                       'PTM':str2bool(self.peaklist.GetItem(itemID, self._columns_peaklist['PTM']).GetText()),
                       'title':self.peaklist.GetItem(itemID, self._columns_peaklist['title']).GetText(),
                       'id_num':int(self.peaklist.GetItem(itemID, self._columns_peaklist['ID #']).GetText()) - 1,  # adjust for previously added 1
                       }

        if return_list:
            scanID = information['scanID']
            MSlevel = information['MSlevel']
            precursor_mz = information['precursor_mz']
            precursor_charge = information['precursor_charge']
            n_peaks = information['n_peaks']
            title = information['title']
            ptm = information['PTM']
            peptide = information['peptide']
            return scanID, MSlevel, precursor_mz, precursor_charge, n_peaks, peptide, ptm, title

        if return_row:
            return ["", information['scanID'], information['id_num'] + 1, information['MSlevel'], information['precursor_mz'],
                    information['precursor_charge'], information['n_peaks'], "0", information['peptide'],
                    information['PTM'], information['title']]

        return information

    def get_item_info_peaklist_selected(self, itemID, return_list=False):
        # get item information
        information = {'scanID':self.peaklist_selected.GetItem(itemID, self._columns_peaklist_selected['scan ID']).GetText(),
                       'MSlevel':str2int(self.peaklist_selected.GetItem(itemID, self._columns_peaklist_selected['MSn']).GetText()),
                       'precursor_mz':self.peaklist_selected.GetItem(itemID, self._columns_peaklist_selected['parent m/z']).GetText(),
                       'precursor_charge':self.peaklist_selected.GetItem(itemID, self._columns_peaklist_selected['charge']).GetText(),
                       'n_peaks':self.peaklist_selected.GetItem(itemID, self._columns_peaklist_selected['# peaks']).GetText(),
                       'n_matched':self.peaklist_selected.GetItem(itemID, self._columns_peaklist_selected['# matched']).GetText(),
                       'peptide':self.peaklist_selected.GetItem(itemID, self._columns_peaklist_selected['peptide']).GetText(),
                       'PTM':str2bool(self.peaklist_selected.GetItem(itemID, self._columns_peaklist_selected['PTM']).GetText()),
                       'title':self.peaklist_selected.GetItem(itemID, self._columns_peaklist_selected['title']).GetText(),
                       'id_num':int(self.peaklist_selected.GetItem(itemID, self._columns_peaklist['ID #']).GetText()) - 1,  # adjust for previously added 1

                       }

        if return_list:
            scanID = information['scanID']
            MSlevel = information['MSlevel']
            precursor_mz = information['precursor_mz']
            precursor_charge = information['precursor_charge']
            n_peaks = information['n_peaks']
            title = information['title']
            ptm = information['PTM']
            peptide = information['peptide']
            return scanID, MSlevel, precursor_mz, precursor_charge, n_peaks, peptide, ptm, title

        return information

    def get_item_info_fragments(self, itemID, return_list=False):
        # get item information
        information = {'measured_mz':str2num(self.fraglist.GetItem(itemID, self._frag_columns['measured m/z']).GetText()),
                       'calculated_mz':str2num(self.fraglist.GetItem(itemID, self._frag_columns['calculated m/z']).GetText()),
                       'intensity':str2num(self.fraglist.GetItem(itemID, self._frag_columns['intensity']).GetText()),
                       'delta_mz':str2num(self.fraglist.GetItem(itemID, self._frag_columns['delta']).GetText()),
                       'charge':str2int(self.fraglist.GetItem(itemID, self._frag_columns['charge']).GetText()),
                       'label':self.fraglist.GetItem(itemID, self._frag_columns['label']).GetText(),
                       'full_label':self.fraglist.GetItem(itemID, self._frag_columns['full_label']).GetText(),
                       'peptide':self.fraglist.GetItem(itemID, self._frag_columns['peptide']).GetText(),
                       }
        if return_list:
            measured_mz = information['measured_mz']
            calculated_mz = information['calculated_mz']
            delta_mz = information['delta_mz']
            intensity = information['intensity']
            charge = information['charge']
            label = information['label']
            peptide = information['peptide']
            return measured_mz, calculated_mz, intensity, delta_mz, charge, label, peptide

        return information

    def onApply(self, evt):

        try: source = evt.GetEventObject().GetName()
        except: pass

        self.config.msms_load_n_scans = int(self.show_count_value.GetValue())
        self.show_next_Btn.SetLabel("Load {} scans".format(self.config.msms_load_n_scans))

        self.config.fragments_units = self.tolerance_choice.GetStringSelection()
        self.config.fragments_tolerance[self.config.fragments_units] = self.tolerance_value.GetValue()
        self.verbose = self.verbose_check.GetValue()
        self.butterfly_plot = self.butterfly_check.GetValue()

        _fragments = {"M-ALL":self.peptide_M_all.GetValue(), "M":self.peptide_M.GetValue(),
                      "M-nH2O":self.peptide_M_nH2O.GetValue(), "M-nNH3":self.peptide_M_nNH3.GetValue(),
                      "a-ALL":self.peptide_a_all.GetValue(), "a":self.peptide_a.GetValue(),
                      "a-nH2O":self.peptide_a_nH2O.GetValue(), "a-nNH3":self.peptide_a_nNH3.GetValue(),
                      "b-ALL":self.peptide_b_all.GetValue(), "b":self.peptide_b.GetValue(),
                      "b-nH2O":self.peptide_b_nH2O.GetValue(), "b-nNH3":self.peptide_b_nNH3.GetValue(),
                      "c-ALL":self.peptide_c_all.GetValue(), "c":self.peptide_c.GetValue(),
                      "c-nH2O":self.peptide_c_nH2O.GetValue(), "c-nNH3":self.peptide_c_nNH3.GetValue(),
                      "c-dot":self.peptide_c_dot.GetValue(), "c+1/2":self.peptide_c_add_1_2.GetValue(),
                      "x-ALL":self.peptide_x_all.GetValue(), "x":self.peptide_x.GetValue(),
                      "x-nH2O":self.peptide_x_nH2O.GetValue(), "x-nNH3":self.peptide_x_nNH3.GetValue(),
                      "y-ALL":self.peptide_y_all.GetValue(), "y":self.peptide_y.GetValue(),
                      "y-nH2O":self.peptide_y_nH2O.GetValue(), "y-nNH3":self.peptide_y_nNH3.GetValue(),
                      "z-ALL":self.peptide_z_all.GetValue(), "z":self.peptide_z.GetValue(),
                      "z-nH2O":self.peptide_z_nH2O.GetValue(), "z-nNH3":self.peptide_z_nNH3.GetValue(),
                      "z-dot":self.peptide_z_dot.GetValue(), "z+1/2":self.peptide_z_add_1_2.GetValue(),
                      }
        self.config.fragments_search.update(_fragments)
        self._fragments = self._build_fragment_search_query()
        self.config.fragments_max_matches = int(self.max_labels_value.GetValue())

        # some parameters should not trigger the updater
        if source == "not_update_gui":
            return

        self.onUpdateGUI(evt)

#     def on_update_presets(self, evt):
#         enableList = self.config.fragments_common[self.fragment_presets_choice.GetStringSelection()]
#
#         if "a-all" in enableList: self.peptide_a_all.SetValue(True)
#         if "b-all" in enableList: self.peptide_b_all.SetValue(True)
#         if "c-all" in enableList: self.peptide_c_all.SetValue(True)
#         if "x-all" in enableList: self.peptide_x_all.SetValue(True)
#         if "y-all" in enableList: self.peptide_y_all.SetValue(True)
#         if "z-all" in enableList: self.peptide_z_all.SetValue(True)
#
#         self.onUpdateGUI(None)
#
    def onUpdateGUI(self, evt):
        # fragments units
        self.config.fragments_units = self.tolerance_choice.GetStringSelection()
        self.tolerance_value.SetMin(self.config.fragments_tolerance_limits[self.config.fragments_units][0])
        self.tolerance_value.SetMax(self.config.fragments_tolerance_limits[self.config.fragments_units][1])
        self.tolerance_value.SetIncrement(self.config.fragments_tolerance_limits[self.config.fragments_units][2])
        self.tolerance_value.SetValue(self.config.fragments_tolerance[self.config.fragments_units])

        enableList = []
        if self.peptide_M_all.GetValue():
            enableList.extend([self.peptide_M, self.peptide_M_nH2O, self.peptide_M_nNH3])
        if self.peptide_a_all.GetValue():
            enableList.extend([self.peptide_a, self.peptide_a_nH2O, self.peptide_a_nNH3])
        if self.peptide_b_all.GetValue():
            enableList.extend([self.peptide_b, self.peptide_b_nH2O, self.peptide_b_nNH3])
        if self.peptide_c_all.GetValue():
            enableList.extend([self.peptide_c, self.peptide_c_nH2O, self.peptide_c_nNH3, self.peptide_c_dot, self.peptide_c_add_1_2])
        if self.peptide_x_all.GetValue():
            enableList.extend([self.peptide_x, self.peptide_x_nH2O, self.peptide_x_nNH3])
        if self.peptide_y_all.GetValue():
            enableList.extend([self.peptide_y, self.peptide_y_nH2O, self.peptide_y_nNH3])
        if self.peptide_z_all.GetValue():
            enableList.extend([self.peptide_z, self.peptide_z_nH2O, self.peptide_z_nNH3, self.peptide_z_dot, self.peptide_z_add_1_2])

        for item in enableList:
            item.SetValue(True)

    def on_populate_table(self, show_all=False):

        data = self.kwargs['tandem_spectra']
        n_show = self.config.msms_load_n_scans - 1

        # populate selected table first
        annot_list = []
        if "annotated_item_list" in data:
            annot_list = natsorted(data['annotated_item_list'])
            for scan_id in annot_list:
                scan, id_num = re_split(":", scan_id)
                id_num = int(id_num)
                spectrum = data[scan]
                peptide, ptm = "", False

                if "identification" in spectrum:
                    try: peptide = spectrum['identification'][id_num]['peptide_seq']
                    except: pass
                    try:
                        if len(spectrum['identification'][id_num]['modification_info']) > 0:
                            ptm = True
                    except: pass

                    # check if scans with PTMs should be shown
                    if not self.config._tandem_show_PTMs_in_table and ptm:
                        continue

                    # check if un-identified scans should be shown
                    if not self.config._tandem_show_unidentified_in_table and peptide == "":
                        continue

                    self.peaklist_selected.Append(["",
                                                   scan,
                                                   str(id_num + 1),
                                                   spectrum['scan_info'].get('ms_level', "2"),
                                                   "{:.4f}".format(spectrum['scan_info'].get('precursor_mz', "")),
                                                   spectrum['scan_info'].get('precursor_charge', ""),
                                                   spectrum['scan_info'].get('peak_count', len(spectrum['xvals'])),
                                                   len(spectrum['fragment_annotations'][id_num].get('fragment_table', [])),
                                                   peptide,
                                                   str(ptm),
                                                   spectrum['scan_info'].get('title', ""),
                                                   ])
#                     print("\n\n", spectrum['identification'][id_num])

        for i, scan in enumerate(data):
            # skip keys that are forbidden
            if "Scan " not in scan:
                continue

            spectrum = data[scan]
            n_ids, peptide, ptm = 1, [""], [False]
            if "identification" in spectrum:
                n_ids = len(spectrum['identification'])

                peptide = [""] * n_ids
                ptm = [False] * n_ids
                for n_id in natsorted(spectrum['identification']):

                    try: peptide[n_id] = spectrum['identification'][n_id]['peptide_seq']
                    except: pass
                    try:
                        if len(spectrum['identification'][n_id]['modification_info']) > 0:
                            ptm[n_id] = True
                    except: pass

            for n_id in range(n_ids):
                # check if scans with PTMs should be shown
                if not self.config._tandem_show_PTMs_in_table and ptm[n_id]:
                    continue

                # check if un-identified scans should be shown
                if not self.config._tandem_show_unidentified_in_table and peptide[n_id] == "":
                    continue

                # add to table
                self.peaklist.Append(["", scan, str(n_id + 1),
                                      spectrum['scan_info'].get('ms_level', "2"),
                                      "{:.4f}".format(spectrum['scan_info'].get('precursor_mz', "")),
                                      spectrum['scan_info'].get('precursor_charge', ""),
                                      spectrum['scan_info'].get('peak_count', len(spectrum['xvals'])),
                                      peptide[n_id],
                                      str(ptm[n_id]),
                                      spectrum['scan_info'].get('title', ""),
                                      ])
            if i >= n_show:
                self.n_loaded_scans = self.peaklist.GetItemCount()
                return

        self.n_loaded_scans = self.peaklist.GetItemCount()

    def on_update_table(self, show_all=False):
        data = self.kwargs['tandem_spectra']
        scans = list(self.kwargs['tandem_spectra'].keys())

        n_show = self.config.msms_load_n_scans

        start_scans = self.n_loaded_scans
        end_scans = self.n_loaded_scans + n_show

        if show_all:
            end_scans = len(scans)

        if end_scans > len(scans):
            print("You have already loaded all scans.")
            return

        for i in range(start_scans, end_scans):
            scan = scans[i]
            if "Scan " not in scan:
                continue

            spectrum = data[scan]
            n_ids, peptide, ptm = 1, [""], [False]

            if "identification" in spectrum:
                n_ids = len(spectrum['identification'])

                peptide = [""] * n_ids
                ptm = [False] * n_ids
                for n_id in natsorted(spectrum['identification']):

                    try: peptide[n_id] = spectrum['identification'][n_id]['peptide_seq']
                    except: pass
                    try:
                        if len(spectrum['identification'][n_id]['modification_info']) > 0:
                            ptm[n_id] = True
                    except:
                        pass

            try:
                ms_level = spectrum['scan_info'].get('ms_level', "2")
            except TypeError:
                 self.n_loaded_scans = self.peaklist.GetItemCount()
                 return

            for n_id in range(n_ids):
                # check if scans with PTMs should be shown
                if not self.config._tandem_show_PTMs_in_table and ptm[n_id]:
                    continue

                # check if un-identified scans should be shown
                if not self.config._tandem_show_unidentified_in_table and peptide[n_id] == "":
                    continue

                self.peaklist.Append(["", scan, str(n_id + 1),
                                      ms_level,
                                      "{:.4f}".format(spectrum['scan_info'].get('precursor_mz', "")),
                                      spectrum['scan_info'].get('precursor_charge', ""),
                                      spectrum['scan_info'].get('peak_count', len(spectrum['xvals'])),
                                      peptide[n_id],
                                      str(ptm[n_id]),
                                      spectrum['scan_info'].get('title', ""),
                                      ])

        self.n_loaded_scans = self.peaklist.GetItemCount()

    def on_load_n_spectra(self, evt):
        self.on_update_table()

    def on_load_all_spectra(self, evt):
        self.on_update_table(show_all=True)

    def on_show_spectrum(self, evt):
#         tstart = ttime()
        itemInfo = self.get_item_info_peaklist(self.currentItem)
        data = self.kwargs['tandem_spectra'][itemInfo['scanID']]

        title = "Precursor: {:.4f} [{}]".format(data['scan_info']['precursor_mz'],
                                                data['scan_info']['precursor_charge'])

        self.presenter.view.panelPlots.on_plot_centroid_MS(data['xvals'],
                                                           data['yvals'],
                                                           title=title,
                                                           repaint=False)
        self.on_add_fragments()

#         print("It took {:.4f}".format(ttime()-tstart))

    def on_show_annotated_spectrum(self, evt):
        tstart = ttime()
        itemInfo = self.get_item_info_peaklist_selected(self.selected_currentItem)
        data = self.kwargs['tandem_spectra'][itemInfo['scanID']]

        title = "Precursor: {:.4f} [{}]".format(data['scan_info']['precursor_mz'],
                                                data['scan_info']['precursor_charge'])

        self.presenter.view.panelPlots.on_plot_centroid_MS(data['xvals'],
                                                           data['yvals'],
                                                           title=title,
                                                           repaint=False)
        try:
            self.on_add_annotations(data, id_num=itemInfo['id_num'])
        except KeyError:
            print("Please annotate item first!")
            return

        print(("It took {:.4f}".format(ttime() - tstart)))

    def on_zoom_on_spectrum(self, evt):
        itemInfo = self.get_item_info_fragments(self.frag_currentItem)

        min_mz, max_mz = itemInfo['measured_mz'] - 2, itemInfo['measured_mz'] + 2
        intensity = str2num(itemInfo['intensity']) * 2.

        if not self.butterfly_plot:
            self.presenter.view.panelPlots.on_zoom_1D_x_axis(min_mz, max_mz, intensity)
        else:
            self.presenter.view.panelPlots.on_zoom_1D_xy_axis(min_mz, max_mz, -intensity, intensity)

    def on_add_fragments(self, itemID=None, return_fragments=False):
        tstart = ttime()
        # if itemid is provided, data will most likely be returned
        if itemID is None:
            itemID = self.currentItem

        itemInfo = self.get_item_info_peaklist(itemID)
        document = self.presenter.documentsDict[self.kwargs['document']]
        tandem_spectra = document.tandem_spectra[itemInfo['scanID']]

        kwargs = {"ion_types":self._fragments,
                  "tolerance":self.config.fragments_tolerance[self.config.fragments_units],
                  "tolerance_units":self.config.fragments_units,
                  "max_annotations":self.config.fragments_max_matches,
                  "verbose":self.verbose,
                  "get_calculated_mz":self.butterfly_plot,
                  "id_num":itemInfo["id_num"]}

        fragments, frag_mass_list, frag_int_list, frag_label_list, frag_full_label_list = self.data_processing.on_get_peptide_fragments(
            tandem_spectra, get_lists=True, label_format=self.config._tandem_label_format, **kwargs)

        # add to temporary storage
        self.fragment_ions = {'fragment_table':fragments,
                              'fragment_mass_list':frag_mass_list,
                              'fragment_intensity_list':frag_int_list,
                              'fragment_label_list':frag_label_list,
                              'fragment_full_label_list':frag_full_label_list}

        # rather than plotting data, return it for annotation of an item
        if return_fragments:
            return itemInfo, document, fragments, frag_mass_list, frag_int_list, frag_label_list, frag_full_label_list

        # clear tables
        self.on_clear_peptide_table()
        self.on_clear_modification_table()

        # add modifications
        modifications = tandem_spectra.get('identification', {})
        if len(modifications) > 0:
            peptide = tandem_spectra['identification'][itemInfo["id_num"]].get('peptide_seq', "")
            self.on_populate_modification_table(peptide, modifications, itemInfo["id_num"])

        # plot data
        if len(fragments) > 0:
            self.presenter.view.panelPlots.on_add_centroid_MS_and_labels(
                frag_mass_list, frag_int_list, frag_label_list, frag_full_label_list, butterfly_plot=self.butterfly_plot)
            self.on_populate_peptide_table(fragments)
        else:
            self.presenter.view.panelPlots.plot1.repaint()

        print(("It took {:.4f}".format(ttime() - tstart)))

    def on_get_fragments(self, itemID=None, document=None):
        # if itemid is provided, data will most likely be returned
        if itemID is None:
            itemID = self.currentItem

        itemInfo = self.get_item_info_peaklist_selected(itemID)
        if document is None:
            document = self.presenter.documentsDict[self.kwargs['document']]

        tandem_spectra = document.tandem_spectra[itemInfo['scanID']]

        kwargs = {"ion_types":self._fragments,
                  "tolerance":self.config.fragments_tolerance[self.config.fragments_units],
                  "tolerance_units":self.config.fragments_units,
                  "max_annotations":self.config.fragments_max_matches,
                  "verbose":self.verbose,
                  "get_calculated_mz":self.butterfly_plot,
                  "id_num":itemInfo["id_num"]}
        fragments, frag_mass_list, frag_int_list, frag_label_list, frag_full_label_list = self.data_processing.on_get_peptide_fragments(
            tandem_spectra, get_lists=True, label_format=self.config._tandem_label_format, **kwargs)

        # rather than plotting data, return it for annotation of an item
        return itemInfo, document, fragments, frag_mass_list, frag_int_list, frag_label_list, frag_full_label_list

    def on_add_annotations(self, data, id_num):

        fragments = data['fragment_annotations'][id_num]['fragment_table']
        frag_mass_list = data['fragment_annotations'][id_num]['fragment_mass_list']
        frag_int_list = data['fragment_annotations'][id_num]['fragment_intensity_list']
        frag_label_list = data['fragment_annotations'][id_num]['fragment_label_list']
        frag_full_label_list = data['fragment_annotations'][id_num]['fragment_full_label_list']

        self.on_clear_peptide_table()
        self.on_clear_modification_table()

        # add modifications
        modifications = data.get('identification', {})
        if len(modifications) > 0:
            peptide = data['identification'][id_num].get('peptide_seq', "")
            self.on_populate_modification_table(peptide, modifications, id_num)

        if len(fragments) > 0:
            self.presenter.view.panelPlots.on_add_centroid_MS_and_labels(frag_mass_list,
                                                                         frag_int_list,
                                                                         frag_label_list,
                                                                         frag_full_label_list,
                                                                         butterfly_plot=self.butterfly_plot)

            self.on_populate_peptide_table(fragments)
        else:
            self.presenter.view.panelPlots.plot1.repaint()

    def on_check_all_fragments_list(self, evt=None):

        check = not self.frag_check_all
        self.frag_check_all = not self.frag_check_all

        rows = self.fraglist.GetItemCount()
        for row in range(rows):
            self.fraglist.CheckItem(row, check=check)

    def get_column_click_fragments(self, evt):
        column = evt.GetColumn()
        if column == 0:
            self.on_check_all_fragments_list()
        else:
            tstart = ttime()
            self.sort_by_column_fragments(column=column)
            print(("Sorting took {:.4f} seconds.".format(ttime() - tstart)))

    def sort_by_column_fragments(self, column, sort_direction=None):
        """
        Sort data in peaklist based on pressed column
        """
        # Check if it should be reversed
        if self.frag_lastColumn == None:
            self.frag_lastColumn = column
        elif self.frag_lastColumn == column:
            if self.frag_reverse == True: self.frag_reverse = False
            else: self.frag_reverse = True
        else:
            self.reverse = False
            self.frag_lastColumn = column

        if sort_direction is None: sort_direction = self.frag_reverse

        columns = self.fraglist.GetColumnCount()
        rows = self.fraglist.GetItemCount()

        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.fraglist.GetItem(itemId=row, col=col)
                itemText = item.GetText()
                tempRow.append(itemText)
            tempRow.append(self.fraglist.IsChecked(index=row))
            tempData.append(tempRow)

        # Sort data
        tempData = natsorted(tempData, key=itemgetter(column), reverse=sort_direction)
        # Clear table and reinsert data
        self.fraglist.DeleteAllItems()

        checkData = []
        for check in tempData:
            checkData.append(check[-1])
            del check[-1]

        rowList = np.arange(len(tempData))
        for row, check in zip(rowList, checkData):
            self.fraglist.Append(tempData[row])
            self.fraglist.CheckItem(row, check)

    def on_clear_peptide_table(self):
        self.fraglist.DeleteAllItems()

    def on_populate_peptide_table(self, frag_dict):
        self._frag_columns = {'check':0, 'measured m/z':1, 'calculated m/z':2, 'intensity':3, 'delta':4,
                              'charge':5, 'label':6, 'full_label':7, 'peptide':8}

        for key in frag_dict:
            fragments = frag_dict[key]
            for annot in fragments:
                self.fraglist.Append(["",
                                      str(annot['measured_mz']),
                                      str(annot['calculated_mz']),
                                      str(annot['measured_int']),
                                      str(annot['delta_mz']),
                                      str(annot.get('charge', "")),
                                      annot['label'],
                                      annot.get('full_label', ""),
                                      annot.get('peptide', "")])

    def on_clear_modification_table(self):
        self.modlist.DeleteAllItems()

    def on_populate_modification_table(self, peptide, mod_dict, n_id):
        modifications = mod_dict[n_id]['modification_info']
        for modification in natsorted(modifications):
            name = modifications[modification]['name']
            mass_delta = modifications[modification]['mass_delta']
            residues = ";".join(modifications[modification]['residues'])
            location = modifications[modification]['location']

            self.modlist.Append(["",
                                 str(peptide),
                                 str(name),
                                 str(mass_delta),
                                 str(residues),
                                 str(location)])

    def _build_fragment_search_query(self):
        frag_dict = self.config.fragments_search

        fragments = []

        if frag_dict['M-ALL']: fragments.append('M-all')
        if frag_dict['a-ALL']: fragments.append('a-all')
        if frag_dict['b-ALL']: fragments.append('b-all')
        if frag_dict['c-ALL']: fragments.append('c-all')
        if frag_dict['x-ALL']: fragments.append('x-all')
        if frag_dict['y-ALL']: fragments.append('y-all')
        if frag_dict['z-ALL']: fragments.append('z-all')

        if frag_dict['M']: fragments.append('M')
        if frag_dict['a']: fragments.append('a')
        if frag_dict['b']: fragments.append('b')
        if frag_dict['c']: fragments.append('c')
        if frag_dict['x']: fragments.append('x')
        if frag_dict['y']: fragments.append('y')
        if frag_dict['z']: fragments.append('z')

        if frag_dict['c-dot']: fragments.append('c-dot')
        if frag_dict['z-dot']: fragments.append('z-dot')

        if frag_dict['c+1/2']: fragments.extend(['c+1', 'c+2'])
        if frag_dict['z+1/2/3']: fragments.extend(['z+1', 'z+2', 'z+3'])

        if frag_dict['M-nH2O']: fragments.extend(['M-H2Ox1', 'M-H2Ox2', 'M-H2Ox3', 'M-H2Ox4'])
        if frag_dict['a-nH2O']: fragments.extend(['a-H2Ox1', 'a-H2Ox2', 'a-H2Ox3', 'a-H2Ox4'])
        if frag_dict['b-nH2O']: fragments.extend(['b-H2Ox1', 'b-H2Ox2', 'b-H2Ox3', 'b-H2Ox4'])
        if frag_dict['c-nH2O']: fragments.extend(['c-H2Ox1', 'c-H2Ox2', 'c-H2Ox3', 'c-H2Ox4'])
        if frag_dict['x-nH2O']: fragments.extend(['x-H2Ox1', 'x-H2Ox2', 'x-H2Ox3', 'x-H2Ox4'])
        if frag_dict['y-nH2O']: fragments.extend(['y-H2Ox1', 'y-H2Ox2', 'y-H2Ox3', 'y-H2Ox4'])
        if frag_dict['z-nH2O']: fragments.extend(['z-H2Ox1', 'z-H2Ox2', 'z-H2Ox3', 'z-H2Ox4'])

        if frag_dict['M-nNH3']: fragments.extend(['M-NH3x1', 'M-NH3x2', 'M-NH3x3', 'M-NH3x4'])
        if frag_dict['a-nNH3']: fragments.extend(['a-NH3x1', 'a-NH3x2', 'a-NH3x3', 'a-NH3x4'])
        if frag_dict['b-nNH3']: fragments.extend(['b-NH3x1', 'b-NH3x2', 'b-NH3x3', 'b-NH3x4'])
        if frag_dict['c-nNH3']: fragments.extend(['c-NH3x1', 'c-NH3x2', 'c-NH3x3', 'c-NH3x4'])
        if frag_dict['x-nNH3']: fragments.extend(['x-NH3x1', 'x-NH3x2', 'x-NH3x3', 'x-NH3x4'])
        if frag_dict['y-nNH3']: fragments.extend(['y-NH3x1', 'y-NH3x2', 'y-NH3x3', 'y-NH3x4'])
        if frag_dict['z-nNH3']: fragments.extend(['z-NH3x1', 'z-NH3x2', 'z-NH3x3', 'z-NH3x4'])

        return fragments

    def _build_plot_parameters(self, plotType="label"):
        if plotType == "label":
            kwargs = {'horizontalalignment':self.config.annotation_label_horz,
                      'verticalalignment':self.config.annotation_label_vert}

        return kwargs

