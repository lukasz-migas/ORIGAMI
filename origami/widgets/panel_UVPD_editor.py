# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import os
from operator import itemgetter
from re import split as re_split
from time import time as ttime

import numpy as np
import processing.utils as pr_utils
import readers.io_waters_raw as io_waters
import wx
import wx.lib.mixins.listctrl as listmix
from gui_elements.dialog_customise_peptide_annotations import DialogCustomisePeptideAnnotations
from gui_elements.misc_dialogs import DialogBox
from gui_elements.panel_htmlViewer import panelHTMLViewer
from ids import ID_uvpd_laser_off_save_chromatogram
from ids import ID_uvpd_laser_off_save_heatmap
from ids import ID_uvpd_laser_off_save_mobiligram
from ids import ID_uvpd_laser_off_show_chromatogram
from ids import ID_uvpd_laser_off_show_heatmap
from ids import ID_uvpd_laser_off_show_mobiligram
from ids import ID_uvpd_laser_off_show_waterfall
from ids import ID_uvpd_laser_on_off_compare_chromatogam
from ids import ID_uvpd_laser_on_off_compare_mobiligram
from ids import ID_uvpd_laser_on_off_mobiligram_show_chromatogram
from ids import ID_uvpd_laser_on_save_chromatogram
from ids import ID_uvpd_laser_on_save_heatmap
from ids import ID_uvpd_laser_on_save_mobiligram
from ids import ID_uvpd_laser_on_show_chromatogram
from ids import ID_uvpd_laser_on_show_heatmap
from ids import ID_uvpd_laser_on_show_mobiligram
from ids import ID_uvpd_laser_on_show_waterfall
from ids import ID_uvpd_monitor_remove
from natsort import natsorted
from styles import makeCheckbox
from styles import makeMenuItem
from styles import makeStaticBox
from styles import validator
from toolbox import saveAsText
from utils.converters import str2int
from utils.converters import str2num


class EditableListCtrl(wx.ListCtrl, listmix.CheckListCtrlMixin):
    """
    Editable list
    """

    def __init__(
        self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
        size=wx.DefaultSize, style=0,
    ):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.CheckListCtrlMixin.__init__(self)


class PanelUVPDEditor(wx.MiniFrame):
    """
    """

    def __init__(self, parent, presenter, config, icons, **kwargs):
        wx.MiniFrame.__init__(
            self, parent, -1, 'UVPD processing...', size=(-1, -1),
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER |
            wx.MAXIMIZE_BOX,
        )

        self.presenter = presenter
        self.view = self.presenter.view
        self.config = config
        self.icons = icons

        self.data_handling = self.presenter.data_handling
        self.data_processing = self.presenter.data_processing

        # get document
        self.document = self.data_processing._on_get_document()

        # present parameters
        self.laser_on_marker = []
        self.laser_on_list = []
        self.laser_off_marker = []
        self.laser_off_list = []
        self.laser_on_data = {}
        self.laser_off_data = {}
        self.legend = {}

        self.current_ion = None

        self.currentItem = None
        self.reverse_peaklist = False
        self.reverse_monitorlist = False

        # make gui items
        self.make_gui()
        self.Centre()
        self.Show(True)
        self.SetFocus()

        # populate table
        try:
            self.populate_table()
        except AttributeError:
            pass

        # bind events
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.onKey, id=wx.ID_ANY)

        self.set_accelerators()

    def set_accelerators(self):
        # add a couple of accelerators
        accelerators = [
            (wx.ACCEL_CTRL, ord('C'), ID_uvpd_laser_on_show_chromatogram),
            (wx.ACCEL_CTRL, ord('H'), ID_uvpd_laser_on_show_heatmap),
            (wx.ACCEL_CTRL, ord('M'), ID_uvpd_laser_on_show_mobiligram),
            (wx.ACCEL_CTRL, ord('W'), ID_uvpd_laser_on_show_waterfall),

            (wx.ACCEL_SHIFT, ord('C'), ID_uvpd_laser_off_show_chromatogram),
            (wx.ACCEL_SHIFT, ord('H'), ID_uvpd_laser_off_show_heatmap),
            (wx.ACCEL_SHIFT, ord('M'), ID_uvpd_laser_off_show_mobiligram),
            (wx.ACCEL_SHIFT, ord('W'), ID_uvpd_laser_off_show_waterfall),
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))

        wx.EVT_MENU(self, ID_uvpd_laser_on_show_chromatogram, self.on_plot_laser_on)
        wx.EVT_MENU(self, ID_uvpd_laser_off_show_chromatogram, self.on_plot_laser_off)
        wx.EVT_MENU(self, ID_uvpd_laser_on_show_heatmap, self.on_plot_laser_on)
        wx.EVT_MENU(self, ID_uvpd_laser_off_show_heatmap, self.on_plot_laser_off)
        wx.EVT_MENU(self, ID_uvpd_laser_on_show_mobiligram, self.on_plot_laser_on)
        wx.EVT_MENU(self, ID_uvpd_laser_off_show_mobiligram, self.on_plot_laser_off)
        wx.EVT_MENU(self, ID_uvpd_laser_on_show_waterfall, self.on_plot_laser_on)
        wx.EVT_MENU(self, ID_uvpd_laser_off_show_waterfall, self.on_plot_laser_off)

    def onKey(self, evt):
        """ Shortcut to navigate through Document Tree """
        key = evt.GetKeyCode()

        evt.Skip()
#         print(key)

#         if key == 67: # chromatogram

    def on_close(self, evt):
        """Destroy this frame."""
        # save data to the app dataset
        if self.document is not None:

            self.document.app_data['uvpd_data'] = dict(
                laser_on_marker=self.laser_on_marker,
                laser_on_list=self.laser_on_list,
                laser_off_marker=self.laser_off_marker,
                laser_off_list=self.laser_off_list,
                laser_on_data=self.laser_on_data,
                laser_off_data=self.laser_off_data,
                legend=self.legend,
            )

        self.Destroy()

    def about(self, evt):
        msg = """
        <h3>About UVPD processing</h3>
        <p>This panel permits quick extraction of data from a very specific UVPD experiment where during the experiment a UV laser is switched on and off.</p>
        <h3>How to use</h3>
        <ol>
        <li>In the main window identify ions of interest - extract them to have heatmap information (found under Drift time (2D, EIC) in the document).</li>
        <li>Open the UVPD processing panel (Plugins -&gt; UVPD processing&hellip;).</li>
        <li>Fill-in peak detection parameters and click on <strong>Find peaks</strong>. Make sure you have previously plotted the correct chromatogram in the RT window. (Document Tree -&amp;gt; double-click on Chromatogram).</li>
        <li>Once you are happy with the peak detection, click on <strong>Extract mobiligrams</strong> button. This will only work if there are any items in the peaklist above the button.</li>
        <li>Now, if you right-click on any item in the peaklist you can plot the results.</li>
        <li>If you would like to monitor specific drift-time, you can add the mobility peaks to the monitorlist (right-hand side).</li>
        <li>First, select an item in the peaklist (you can see the currently selected ion in the title of the window). Fill-in the <strong>min dt</strong> and <strong>max dt</strong> fields and click on the <strong>+</strong> button.</li>
        <li>Click on <strong>Monitor features</strong>.</li>
        </ol>
        """.strip()
        kwargs = {
            'msg': msg,
            'title': 'Learn about: Annotating mass spectra',
            'window_size': (600, 450),
        }

        htmlViewer = panelHTMLViewer(self, self.config, **kwargs)
        htmlViewer.Show()

    def on_delete_peaklist(self, evt):
        self.peaklist.DeleteItem(self.currentItem)

    def on_delete_monitorlist(self, evt):
        dt_min = str2int(self.monitorlist.GetItem(self.currentItem, 1).GetText())
        dt_max = str2int(self.monitorlist.GetItem(self.currentItem, 2).GetText())
        ion_name = self.monitorlist.GetItem(self.currentItem, 3).GetText()
        search_item = ['', int(dt_min), int(dt_max), ion_name]

        self.monitorlist.DeleteItem(self.currentItem)

        if 'uvpd_monitor_peaks' in self.document.app_data:
            if search_item in self.document.app_data['uvpd_monitor_peaks']:
                try:
                    index = self.document.app_data['uvpd_monitor_peaks'].index(search_item)
                    del self.document.app_data['uvpd_monitor_peaks'][index]
                except Exception:
                    pass

    def OnRightClickMenu_monitorlist(self, evt):
        # Menu events
        self.Bind(wx.EVT_MENU, self.on_plot_mobility_monitor, id=ID_uvpd_laser_on_off_mobiligram_show_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_delete_monitorlist, id=ID_uvpd_monitor_remove)

        self.currentItem = evt.GetIndex()
        menu = wx.Menu()
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_uvpd_laser_on_off_mobiligram_show_chromatogram,
                text='Compare chromatograms',
                bitmap=None,
            ),
        )
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_uvpd_monitor_remove, text='Remove item from list',
                bitmap=self.icons.iconsLib['bin16'],
            ),
        )
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def OnRightClickMenu_peaklist(self, evt):

        # Menu events
        self.Bind(wx.EVT_MENU, self.on_plot_compare_on_off, id=ID_uvpd_laser_on_off_compare_chromatogam)
        self.Bind(wx.EVT_MENU, self.on_plot_compare_on_off, id=ID_uvpd_laser_on_off_compare_mobiligram)
        self.Bind(wx.EVT_MENU, self.on_plot_laser_on, id=ID_uvpd_laser_on_show_heatmap)
        self.Bind(wx.EVT_MENU, self.on_plot_laser_off, id=ID_uvpd_laser_off_show_heatmap)
        self.Bind(wx.EVT_MENU, self.on_plot_laser_on, id=ID_uvpd_laser_on_show_waterfall)
        self.Bind(wx.EVT_MENU, self.on_plot_laser_off, id=ID_uvpd_laser_off_show_waterfall)
        self.Bind(wx.EVT_MENU, self.on_plot_laser_on, id=ID_uvpd_laser_on_show_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_plot_laser_off, id=ID_uvpd_laser_off_show_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_plot_laser_on, id=ID_uvpd_laser_on_show_mobiligram)
        self.Bind(wx.EVT_MENU, self.on_plot_laser_off, id=ID_uvpd_laser_off_show_mobiligram)

        self.Bind(wx.EVT_MENU, self.on_save_data, id=ID_uvpd_laser_on_save_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_save_data, id=ID_uvpd_laser_on_save_mobiligram)
        self.Bind(wx.EVT_MENU, self.on_save_data_heatmap, id=ID_uvpd_laser_on_save_heatmap)

        self.Bind(wx.EVT_MENU, self.on_save_data, id=ID_uvpd_laser_off_save_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_save_data, id=ID_uvpd_laser_off_save_mobiligram)
        self.Bind(wx.EVT_MENU, self.on_save_data_heatmap, id=ID_uvpd_laser_off_save_heatmap)

        save_laser_on = wx.Menu()
        save_laser_on.Append(ID_uvpd_laser_on_save_chromatogram, 'Save DATASET 1 chromatogram data to file')
        save_laser_on.Append(ID_uvpd_laser_on_save_mobiligram, 'Save DATASET 1 mobiligram data to file')
        save_laser_on.Append(ID_uvpd_laser_on_save_heatmap, 'Save DATASET 1 heatmap data to file')

        save_laser_off = wx.Menu()
        save_laser_off.Append(ID_uvpd_laser_off_save_chromatogram, 'Save DATASET 2 chromatogram data to file')
        save_laser_off.Append(ID_uvpd_laser_off_save_mobiligram, 'Save DATASET 2 mobiligram data to file')
        save_laser_off.Append(ID_uvpd_laser_off_save_heatmap, 'Save DATASET 2 heatmap data to file')

        self.currentItem = evt.GetIndex()
        menu = wx.Menu()
#         self.average_data =  menu.AppendCheckItem(-1, "Average/sum data when plotting",
#                                                  help="When checked, data will be averaged.")
#         self.normalize_data =  menu.AppendCheckItem(-1, "Normalize",
#                                                  help="")
#         menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_uvpd_laser_on_off_compare_chromatogam,
                text='Compare chromatograms',
                bitmap=None,
            ),
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_uvpd_laser_on_off_compare_mobiligram,
                text='Compare mobiligrams',
                bitmap=None,
            ),
        )
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_uvpd_laser_on_show_chromatogram,
                text='Show DATASET 1 data as chromatogram\tCtrl+C',
                bitmap=None,
            ),
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_uvpd_laser_on_show_mobiligram,
                text='Show DATASET 1 data as mobiligram\tCtrl+M',
                bitmap=None,
            ),
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_uvpd_laser_on_show_heatmap,
                text='Show DATASET 1 data as heatmap\tCtrl+H',
                bitmap=None,
            ),
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_uvpd_laser_on_show_waterfall,
                text='Show DATASET 1 data as waterfall\tCtrl+W',
                bitmap=None,
            ),
        )
        menu.AppendMenu(wx.ID_ANY, 'Save data...', save_laser_on)
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_uvpd_laser_off_show_chromatogram,
                text='Show laser-off data as chromatogram\tShift+C',
                bitmap=None,
            ),
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_uvpd_laser_off_show_mobiligram,
                text='Show DATASET 2 data as summed mobiligram\tShift+M',
                bitmap=None,
            ),
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_uvpd_laser_off_show_heatmap,
                text='Show DATASET 2 data as heatmap\tShift+H',
                bitmap=None,
            ),
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_uvpd_laser_off_show_waterfall,
                text='Show DATASET 2 data as waterfall\tShift+W',
                bitmap=None,
            ),
        )
        menu.AppendMenu(wx.ID_ANY, 'Save data...', save_laser_off)
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def onCustomiseParameters(self, evt):

        dlg = DialogCustomisePeptideAnnotations(self, self.config)
        dlg.ShowModal()

    def populate_table(self):

        ions = list(self.document.IMS2Dions.keys())
        for ion in ions:
            min_mz, max_mz = re_split('-|,|:|__', ion)

            self.peaklist.Append(['', min_mz, max_mz])

        if 'uvpd_monitor_peaks' in self.document.app_data:
            for row in self.document.app_data['uvpd_monitor_peaks']:
                print(row)
                self.monitorlist.Append(row)

        if 'uvpd_data' in self.document.app_data:
            self.laser_on_marker = self.document.app_data['uvpd_data'].get('laser_on_marker', {})
            self.laser_on_list = self.document.app_data['uvpd_data'].get('laser_on_list', {})
            self.laser_off_marker = self.document.app_data['uvpd_data'].get('laser_off_marker', {})
            self.laser_off_list = self.document.app_data['uvpd_data'].get('laser_off_list', {})
            self.laser_on_data = self.document.app_data['uvpd_data'].get('laser_on_data', {})
            self.laser_off_data = self.document.app_data['uvpd_data'].get('laser_off_data', {})
            self.legend = self.document.app_data['uvpd_data'].get('legend', {})

            self.extract_features.Enable()
            self.monitor_features.Enable()

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 1, wx.EXPAND, 5)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

        self.SetSize((450, 450))
        self.Layout()

    def make_peak_finding_panel(self, panel):
        threshold_value = wx.StaticText(panel, wx.ID_ANY, 'Threshold:')
        self.threshold_value = wx.SpinCtrlDouble(
            panel, -1, min=0, max=1, inc=0.05,
            value=str(self.config.uvpd_peak_finding_threshold),
            initial=self.config.uvpd_peak_finding_threshold,
            size=(60, -1),
        )
        self.threshold_value.Bind(wx.EVT_TEXT, self.on_apply)

        buffer_size_value = wx.StaticText(panel, wx.ID_ANY, 'Buffer size:')
        self.buffer_size_value = wx.SpinCtrlDouble(
            panel, -1, min=0, max=100, inc=1,
            value=str(self.config.uvpd_peak_buffer_width),
            initial=self.config.uvpd_peak_buffer_width,
            size=(60, -1),
        )
        self.buffer_size_value.Bind(wx.EVT_TEXT, self.on_apply)

        first_index_value = wx.StaticText(panel, wx.ID_ANY, 'First index:')
        self.first_index_value = wx.SpinCtrlDouble(
            panel, -1, min=0, max=10000, inc=1,
            value=str(self.config.uvpd_peak_first_index),
            initial=self.config.uvpd_peak_first_index,
            size=(60, -1),
        )
        self.first_index_value.Bind(wx.EVT_TEXT, self.on_apply)

        show_markers = wx.StaticText(panel, wx.ID_ANY, 'Show on plot:')
        self.show_labels = makeCheckbox(panel, 'labels')
        self.show_labels.SetValue(self.config.uvpd_peak_show_labels)
        self.show_labels.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.show_labels.Disable()

        self.show_markers = makeCheckbox(panel, 'markers')
        self.show_markers.SetValue(self.config.uvpd_peak_show_markers)
        self.show_markers.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.show_patches = makeCheckbox(panel, 'patches')
        self.show_patches.SetValue(self.config.uvpd_peak_show_patches)
        self.show_patches.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.find_peaks_btn = wx.Button(panel, wx.ID_OK, 'Find peaks', size=(-1, 22))
        self.find_peaks_btn.Bind(wx.EVT_BUTTON, self.on_find_peaks)

        self.extract_MS_btn = wx.Button(panel, wx.ID_OK, 'Extract spectra', size=(-1, 22))
        self.extract_MS_btn.Bind(wx.EVT_BUTTON, self.on_extract_mass_spectra)

        self.msg_bar = wx.StaticText(panel, -1, '')
        self.msg_bar.SetLabel('')

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(threshold_value, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.threshold_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(buffer_size_value, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.buffer_size_value, (n, 3), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(first_index_value, (n, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.first_index_value, (n, 5), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(show_markers, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.show_labels, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.show_markers, (n, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.show_patches, (n, 3), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.find_peaks_btn, (n, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.extract_MS_btn, (n, 2), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        n = n + 1
        grid.Add(self.msg_bar, (n, 0), wx.GBSpan(1, 6), flag=wx.EXPAND)

        staticBox = makeStaticBox(panel, 'Detect peaks', size=(-1, -1), color=wx.BLACK)
        staticBox.SetSize((-1, -1))

        box_sizer = wx.StaticBoxSizer(staticBox, wx.HORIZONTAL)
        box_sizer.Add(grid, 0, wx.EXPAND, 10)

        return box_sizer

    def make_extract_panel(self, panel):

        self.extract_features = wx.Button(panel, wx.ID_OK, 'Extract mobiligrams', size=(-1, 22))
        self.extract_features.Bind(wx.EVT_BUTTON, self.on_extract_mobility_for_ions)
        self.extract_features.Disable()

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(self.extract_features, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)

        return grid

    def make_monitor_panel(self, panel):

        self.monitor_features = wx.Button(panel, wx.ID_OK, 'Monitor features', size=(-1, 22))
        self.monitor_features.Bind(wx.EVT_BUTTON, self.on_monitor_mobility_for_ions)
        self.monitor_features.Disable()

        self.about_button = wx.Button(panel, wx.ID_OK, 'About...', size=(-1, 22))
        self.about_button.Bind(wx.EVT_BUTTON, self.about)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(self.monitor_features, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.about_button, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)

        return grid

    def make_panel(self):

        panel = wx.Panel(self, -1, size=(-1, -1))

        peakFinding_boxSizer = self.make_peak_finding_panel(panel)
        extract_grid = self.make_extract_panel(panel)
        detect_grid = self.make_monitor_panel(panel)

        min_mz_value = wx.StaticText(panel, wx.ID_ANY, 'min m/z:')
        self.min_mz_value = wx.TextCtrl(
            panel, -1, '', size=(45, -1),
            validator=validator('floatPos'),
        )
        self.min_mz_value.Bind(wx.EVT_TEXT, self.on_apply)

        max_mz_value = wx.StaticText(panel, wx.ID_ANY, 'max m/z:')
        self.max_mz_value = wx.TextCtrl(
            panel, -1, '', size=(45, -1),
            validator=validator('floatPos'),
        )
        self.max_mz_value.Bind(wx.EVT_TEXT, self.on_apply)

        frag_add = wx.BitmapButton(
            panel, -1, self.icons.iconsLib['add16'],
            size=(16, 16), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        frag_add.Bind(wx.EVT_BUTTON, self.on_add_fragment_ion)

        frag_toolbar_grid = wx.GridBagSizer(1, 1)
        frag_toolbar_grid.Add(min_mz_value, (0, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        frag_toolbar_grid.Add(self.min_mz_value, (0, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        frag_toolbar_grid.Add(max_mz_value, (0, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        frag_toolbar_grid.Add(self.max_mz_value, (0, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        frag_toolbar_grid.Add(frag_add, (0, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)

        self.peaklist = EditableListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES)
        self.peaklist.SetFont(wx.SMALL_FONT)
        self.peaklist.InsertColumn(0, '', width=25)
        self.peaklist.InsertColumn(1, 'min m/z', width=60)
        self.peaklist.InsertColumn(2, 'max m/z', width=60)

        # bind events
        self.peaklist.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickMenu_peaklist)
        self.peaklist.Bind(wx.EVT_LIST_KEY_DOWN, self.onSelectItem_peaklist)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelectItem_peaklist)
        self.peaklist.Bind(wx.EVT_LIST_COL_CLICK, self.get_column_click_peaklist)

        min_dt_value = wx.StaticText(panel, wx.ID_ANY, 'min dt:')
        self.min_dt_value = wx.TextCtrl(
            panel, -1, '', size=(45, -1),
            validator=validator('intPos'),
        )
        self.min_dt_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.min_dt_value.Disable()

        max_dt_value = wx.StaticText(panel, wx.ID_ANY, 'max dt:')
        self.max_dt_value = wx.TextCtrl(
            panel, -1, '', size=(45, -1),
            validator=validator('intPos'),
        )
        self.max_dt_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.max_dt_value.Disable()

        monitor_add = wx.BitmapButton(
            panel, -1, self.icons.iconsLib['add16'],
            size=(16, 16), style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL,
        )
        monitor_add.Bind(wx.EVT_BUTTON, self.on_add_mobility_peak)

        monitor_toolbar_grid = wx.GridBagSizer(1, 1)
        monitor_toolbar_grid.Add(min_dt_value, (0, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        monitor_toolbar_grid.Add(
            self.min_dt_value, (0, 1), wx.GBSpan(1, 1),
            flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL,
        )
        monitor_toolbar_grid.Add(max_dt_value, (0, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        monitor_toolbar_grid.Add(
            self.max_dt_value, (0, 3), wx.GBSpan(1, 1),
            flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL,
        )
        monitor_toolbar_grid.Add(monitor_add, (0, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)

        self.monitorlist = EditableListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES)
        self.monitorlist.SetFont(wx.SMALL_FONT)
        self.monitorlist.InsertColumn(0, '', width=25)
        self.monitorlist.InsertColumn(1, 'min dt', width=45)
        self.monitorlist.InsertColumn(2, 'max dt', width=45)
        self.monitorlist.InsertColumn(3, 'ion name', width=95)
        self.monitorlist.Disable()

        # bind events
        self.monitorlist.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickMenu_monitorlist)
        self.monitorlist.Bind(wx.EVT_LIST_COL_CLICK, self.get_column_click_monitorlist)

        fragSizer = wx.BoxSizer(wx.VERTICAL)
        fragSizer.Add(frag_toolbar_grid, 0, wx.EXPAND | wx.ALL, 2)
        fragSizer.Add(self.peaklist, 1, wx.EXPAND | wx.ALL, 2)
        fragSizer.Add(extract_grid, 0, wx.EXPAND, 0)

        monitorSizer = wx.BoxSizer(wx.VERTICAL)
        monitorSizer.Add(monitor_toolbar_grid, 0, wx.EXPAND | wx.ALL, 2)
        monitorSizer.Add(self.monitorlist, 1, wx.EXPAND | wx.ALL, 2)
        monitorSizer.Add(detect_grid, 0, wx.EXPAND, 0)

        tableSizer = wx.BoxSizer(wx.HORIZONTAL)
        tableSizer.Add(fragSizer, 1, wx.EXPAND | wx.ALL, 2)
        tableSizer.Add(monitorSizer, 1, wx.EXPAND | wx.ALL, 2)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(peakFinding_boxSizer, 0, wx.EXPAND, 0)
        main_sizer.Add(tableSizer, 1, wx.EXPAND, 0)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def onSelectItem_peaklist(self, evt):
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_UP or key_code == wx.WXK_DOWN:
            self.currentItem = evt.m_itemIndex
        else:
            self.currentItem = evt.m_itemIndex

        self.current_ion = self.get_ion_name(self.currentItem)

        self.SetTitle('UVPD processing... | current ion: {}'.format(self.current_ion))

        if self.current_ion is not None:
            self.monitorlist.Enable()
            self.min_dt_value.Enable()
            self.max_dt_value.Enable()

        if evt is not None:
            evt.Skip()

    def get_column_click_peaklist(self, evt):
        self.sort_by_column_peaklist(column=evt.GetColumn())

    def sort_by_column_peaklist(self, column, sort_direction=None):
        """
        Sort data in peaklist based on pressed column
        """
        # Check if it should be reversed
        if sort_direction is None:
            sort_direction = self.reverse_peaklist

        self.reverse_peaklist = not self.reverse_peaklist

        columns = self.peaklist.GetColumnCount()
        rows = self.peaklist.GetItemCount()

        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.peaklist.GetItem(itemId=row, col=col)
                itemText = item.GetText()
                tempRow.append(itemText)
            tempRow.append(self.peaklist.IsChecked(index=row))
            tempData.append(tempRow)

        # Sort data
        tempData = natsorted(tempData, key=itemgetter(column), reverse=sort_direction)
        # Clear table and reinsert data
        self.peaklist.DeleteAllItems()

        checkData = []
        for check in tempData:
            checkData.append(check[-1])
            del check[-1]

        rowList = np.arange(len(tempData))
        for row, check in zip(rowList, checkData):
            self.peaklist.Append(tempData[row])
            self.peaklist.CheckItem(row, check)

    def get_column_click_monitorlist(self, evt):
        self.sort_by_column_monitorlist(column=evt.GetColumn())

    def sort_by_column_monitorlist(self, column, sort_direction=None):
        """
        Sort data in peaklist based on pressed column
        """
        # Check if it should be reversed
        if sort_direction is None:
            sort_direction = self.reverse_monitorlist

        self.reverse_monitorlist = not self.reverse_monitorlist

        columns = self.monitorlist.GetColumnCount()
        rows = self.monitorlist.GetItemCount()

        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.monitorlist.GetItem(itemId=row, col=col)
                itemText = item.GetText()
                tempRow.append(itemText)
            tempRow.append(self.monitorlist.IsChecked(index=row))
            tempData.append(tempRow)

        # Sort data
        tempData = natsorted(tempData, key=itemgetter(column), reverse=sort_direction)
        # Clear table and reinsert data
        self.monitorlist.DeleteAllItems()

        checkData = []
        for check in tempData:
            checkData.append(check[-1])
            del check[-1]

        rowList = np.arange(len(tempData))
        for row, check in zip(rowList, checkData):
            self.monitorlist.Append(tempData[row])
            self.monitorlist.CheckItem(row, check)

    def on_apply(self, evt):

        try:
            source = evt.GetEventObject().GetName()
        except Exception:
            pass

        self.config.uvpd_peak_finding_threshold = self.threshold_value.GetValue()
        self.config.uvpd_peak_buffer_width = int(self.buffer_size_value.GetValue())
        self.config.uvpd_peak_first_index = int(self.first_index_value.GetValue())
        self.config.uvpd_peak_show_markers = self.show_markers.GetValue()
        self.config.uvpd_peak_show_patches = self.show_patches.GetValue()
        self.config.uvpd_peak_show_labels = self.show_labels.GetValue()

    def on_find_peaks(self, evt):
        tstart = ttime()
        height = 100000000000
        ymin = 0

        # Prepare data first
        try:
            rtList = np.transpose([self.document.RT['xvals'], self.document.RT['yvals']])
        except AttributeError:
            DialogBox(
                exceptionTitle='Error', exceptionMsg='Please load document first',
                type='Error',
            )
            return

        # Detect peaks
        peakList, tablelist, apexlist = pr_utils.detect_peaks_chromatogram(
            rtList, self.config.uvpd_peak_finding_threshold,
            add_buffer=self.config.uvpd_peak_buffer_width,
        )

        # clear plots
        self.view.panelPlots.on_clear_patches('RT', False)
        self.view.panelPlots.on_clear_markers('RT', False)
        self.view.panelPlots.on_clear_legend('RT', False)

        # generate legend
        # first value is even then dataset 1 is red, and 2 is blue
        if self.config.uvpd_peak_first_index % 2:
            labels, colors = ['Dataset 1', 'Dataset 2'], [(1, 0, 0), (0, 0, 1)]
        else:
            # first value is odd then dataset is blue and 2 is red
            labels, colors = ['Dataset 1', 'Dataset 2'], [(0, 0, 1), (1, 0, 0)]

        self.legend = {'colors': colors, 'labels': labels}

        # get data
        # separate into dataset 1 and 2 (widths)
        short_list = tablelist[self.config.uvpd_peak_first_index::]
        self.laser_on_list = short_list[0::2]
        self.laser_off_list = short_list[1::2]

        # separate into dataset 1 and 2 (apex peaks)
        short_markers_list = apexlist[self.config.uvpd_peak_first_index - 1::]
        self.laser_on_marker = short_markers_list[0::2]
        self.laser_off_marker = short_markers_list[1::2]

        # add markers
        if self.config.uvpd_peak_show_markers:
            self.view.panelPlots.on_add_marker(
                xvals=self.laser_on_marker[:, 0],
                yvals=self.laser_on_marker[:, 1],
                color=colors[0],
                marker=self.config.markerShape_1D,
                size=self.config.markerSize_1D,
                plot='RT', repaint=False,
            )

            self.view.panelPlots.on_add_marker(
                xvals=self.laser_off_marker[:, 0],
                yvals=self.laser_off_marker[:, 1],
                color=colors[1],
                marker=self.config.markerShape_1D,
                size=self.config.markerSize_1D,
                plot='RT', repaint=False,
            )

        # add patches
        if self.config.uvpd_peak_show_patches:
            for row in self.laser_on_list:
                xmin = row[0]
                width = row[1] - xmin + 1
                self.view.panelPlots.on_add_patch(
                    xmin, ymin, width, height,
                    color=colors[0],
                    plot='RT', repaint=False,
                )

            for row in self.laser_off_list:
                xmin = row[0]
                width = row[1] - xmin + 1
                self.view.panelPlots.on_add_patch(
                    xmin, ymin, width, height,
                    color=colors[1],
                    plot='RT', repaint=False,
                )

        if self.config.uvpd_peak_show_markers or self.config.uvpd_peak_show_patches:
            self.view.panelPlots.on_add_legend(labels, colors, plot='RT')

        self.view.panelPlots.plotRT.repaint()

        msg = 'Found {} regions - skipping # peaks {}; #1: {} | #2: {}'.format(
            len(tablelist), self.config.uvpd_peak_first_index, len(self.laser_on_list),
            len(self.laser_off_list),
        )
        self.msg_bar.SetLabel(msg)
        self.msg_bar.SetForegroundColour(wx.BLUE)

        print('Found {} regions. It took {:.4f} seconds'.format(len(tablelist), ttime() - tstart))

        # enable feature extraction
        self.extract_features.Enable()

    def on_add_fragment_ion(self, evt):
        min_mz = str2num(self.min_mz_value.GetValue())
        max_mz = str2num(self.max_mz_value.GetValue())

        if min_mz in [None, 'None', '']:
            DialogBox(
                exceptionTitle='Error', exceptionMsg='Incorrect value of min m/z. Try again.',
                type='Error',
            )
            return
        if max_mz in [None, 'None', '']:
            DialogBox(
                exceptionTitle='Error', exceptionMsg='Incorrect value of max m/z. Try again.',
                type='Error',
            )
            return

        self.peaklist.Append(['', min_mz, max_mz])

    def on_add_mobility_peak(self, evt):

        min_dt = str2int(self.min_dt_value.GetValue())
        max_dt = str2int(self.max_dt_value.GetValue())

        if min_dt in [None, 'None', '']:
            DialogBox(
                exceptionTitle='Error', exceptionMsg='Incorrect value of min dt. Try again.',
                type='Error',
            )
            return
        if max_dt in [None, 'None', '']:
            DialogBox(
                exceptionTitle='Error', exceptionMsg='Incorrect value of max dt. Try again.',
                type='Error',
            )
            return

        self.monitorlist.Append(['', min_dt, max_dt, self.current_ion])

        if 'uvpd_monitor_peaks' not in self.document.app_data:
            self.document.app_data['uvpd_monitor_peaks'] = []

        self.document.app_data['uvpd_monitor_peaks'].append(['', min_dt, max_dt, self.current_ion])

    def get_ion_list(self):
        count = self.peaklist.GetItemCount()

        ion_list = []
        for i in range(count):
            mz_min = self.peaklist.GetItem(i, 1).GetText()
            mz_max = self.peaklist.GetItem(i, 2).GetText()
            ion_list.append([mz_min, mz_max])

        return ion_list

    def get_ion_name(self, itemID):
        mz_min = self.peaklist.GetItem(itemID, 1).GetText()
        mz_max = self.peaklist.GetItem(itemID, 2).GetText()

        return '{}-{}'.format(mz_min, mz_max)

    def on_extract_mobility_for_ions(self, evt):

        ion_list = self.get_ion_list()

        if len(ion_list) == 0:
            DialogBox(
                exceptionTitle='Error', exceptionMsg='Please extract data for some ions first!',
                type='Error',
            )
            return

        if len(self.laser_on_list) == 0 or len(self.laser_off_list) == 0:
            DialogBox(
                exceptionTitle='Error',
                exceptionMsg='Please detect regions of interest first using the Find peaks button above',
                type='Error',
            )
            return

        laser_on_data, laser_off_data = {}, {}
        for mz_region in ion_list:
            mzStart, mzEnd = mz_region
            ion_name = '{}-{}'.format(mzStart, mzEnd)
            laser_on_data[ion_name] = np.zeros(shape=(len(self.laser_on_list), 200))
            laser_off_data[ion_name] = np.zeros(shape=(len(self.laser_off_list), 200))

            # Data needs to be present in the document
            try:
                ion_data = self.document.IMS2Dions[ion_name]['zvals']
            except KeyError:
                print(
                    'Data was missing for {} ion. This take might few seconds longer...'.format(
                        ion_name,
                    ),
                )

                extract_kwargs = {'return_data': True}
                path = self.document.path
                ion_data = io_waters.driftscope_extract_2D(
                    path=path, driftscope_path=self.config.driftscopePath,
                    mz_start=mzStart, mz_end=mzEnd, **extract_kwargs
                )

            # retrieve laser-on data
            for i, rt_region in enumerate(self.laser_on_list):
                startScan, endScan = rt_region
                imsData1D = np.sum(ion_data[:, startScan:endScan], axis=1)
                laser_on_data[ion_name][i] = imsData1D

            # retrieve laser-off data
            for i, rt_region in enumerate(self.laser_off_list):
                startScan, endScan = rt_region
                imsData1D = np.sum(ion_data[:, startScan:endScan], axis=1)
                laser_off_data[ion_name][i] = imsData1D

            zvals = np.rot90(laser_on_data[ion_name], k=3)
            xvals = 1 + np.arange(len(zvals[1, :]))
            yvals = 1 + np.arange(len(zvals[:, 1]))

            self.laser_on_data[ion_name] = dict(
                zvals=zvals, xvals=xvals,
                yvals=yvals, xlabel='Laser shots',
                ylabel='Drift time (bins)',
            )

            zvals = np.rot90(laser_off_data[ion_name], k=3)
            xvals = 1 + np.arange(len(zvals[1, :]))
            yvals = 1 + np.arange(len(zvals[:, 1]))

            self.laser_off_data[ion_name] = dict(
                zvals=zvals, xvals=xvals,
                yvals=yvals, xlabel='Laser shots',
                ylabel='Drift time (bins)',
            )

            print('Extracted data for {}-{} ion'.format(mzStart, mzEnd))

            self.view.panelPlots.on_plot_2D(zvals, xvals, yvals, 'Laser shots', 'Drift time (bins)', override=False)

        # enable feature extraction
        self.monitor_features.Enable()

    def get_laser_on_ion_data(self):
        ion_name = self.get_ion_name(self.currentItem)

        ion_data = self.laser_on_data[ion_name]
        zvals = ion_data['zvals']
        xvals = ion_data['xvals']
        yvals = ion_data['yvals']
        xlabel = ion_data['xlabel']
        ylabel = ion_data['ylabel']

        return zvals, xvals, yvals, xlabel, ylabel

    def get_laser_off_ion_data(self):
        ion_name = self.get_ion_name(self.currentItem)

        ion_data = self.laser_off_data[ion_name]
        zvals = ion_data['zvals']
        xvals = ion_data['xvals']
        yvals = ion_data['yvals']
        xlabel = ion_data['xlabel']
        ylabel = ion_data['ylabel']

        return zvals, xvals, yvals, xlabel, ylabel

    def get_mobility_list(self):
        count = self.monitorlist.GetItemCount()

        mobility_list = []
        for i in range(count):
            dt_min = str2int(self.monitorlist.GetItem(i, 1).GetText())
            dt_max = str2int(self.monitorlist.GetItem(i, 2).GetText())
            ion_name = self.monitorlist.GetItem(i, 3).GetText()
            mobility_list.append([dt_min, dt_max, ion_name])

        return mobility_list

    def get_mobility_name(self, itemID):
        dt_min = str2int(self.monitorlist.GetItem(itemID, 1).GetText())
        dt_max = str2int(self.monitorlist.GetItem(itemID, 2).GetText())
        ion_name = self.monitorlist.GetItem(itemID, 3).GetText()

        return '{}-{}'.format(dt_min, dt_max), ion_name

    def on_monitor_mobility_for_ions(self, evt):
        mobility_list = self.get_mobility_list()

        if len(mobility_list) == 0:
            DialogBox(
                exceptionTitle='Error', exceptionMsg='Please add mobility regions first!',
                type='Error',
            )
            return

        ion_list = self.get_ion_list()

        if len(ion_list) == 0:
            DialogBox(
                exceptionTitle='Error', exceptionMsg='Please extract data for some ions first!',
                type='Error',
            )
            return

        for mz_region in ion_list:
            mzStart, mzEnd = mz_region
            ion_name = '{}-{}'.format(mzStart, mzEnd)
            self.laser_on_data[ion_name]['dt_extract'] = {}
            self.laser_off_data[ion_name]['dt_extract'] = {}

            for dt_region in mobility_list:
                dtStart, dtEnd, allowed_ion_name = dt_region
                if ion_name != allowed_ion_name:
                    continue

                dt_name = '{}-{}'.format(dtStart, dtEnd)

                ion_data = self.laser_on_data[ion_name]
                zvals = ion_data['zvals']

                mobility_slice = zvals[dtStart:dtEnd, :]
                sum_mobility_slide = np.sum(mobility_slice, axis=0)
                xvals = 1 + np.arange(len(sum_mobility_slide))
                self.laser_on_data[ion_name]['dt_extract'][dt_name] = {
                    'xvals': xvals, 'yvals': sum_mobility_slide,
                }

                ion_data = self.laser_off_data[ion_name]
                zvals = ion_data['zvals']

                mobility_slice = zvals[dtStart:dtEnd, :]
                sum_mobility_slide = np.sum(mobility_slice, axis=0)
                xvals = 1 + np.arange(len(sum_mobility_slide))
                self.laser_off_data[ion_name]['dt_extract'][dt_name] = {
                    'xvals': xvals, 'yvals': sum_mobility_slide,
                }

                print(
                    'Extracted data for dt: {} for ion: {}'.format(
                        dt_name, ion_name,
                    ),
                )

    def on_plot_laser_on(self, evt):

        evtID = evt.GetId()

        try:
            zvals, xvals, yvals, xlabel, ylabel = self.get_laser_on_ion_data()
        except KeyError:
            DialogBox(
                exceptionTitle='Error', exceptionMsg='Please extract data first!',
                type='Error',
            )
            return

        if evtID == ID_uvpd_laser_on_show_heatmap:
            self.view.panelPlots.on_plot_2D(
                zvals, xvals, yvals, xlabel, ylabel,
                override=False, set_page=True,
            )

        elif evtID == ID_uvpd_laser_on_show_waterfall:
            self.view.panelPlots.on_plot_waterfall(
                yvals=xvals, xvals=yvals, zvals=zvals,
                xlabel=xlabel, ylabel=ylabel, set_page=True,
            )

        elif evtID == ID_uvpd_laser_on_show_chromatogram:
            yvalsRT = np.average(zvals, axis=0)
            self.view.panelPlots.on_plot_RT(xvals, yvalsRT, 'Laser shots', 'Intensity', set_page=True)

        elif evtID == ID_uvpd_laser_on_show_mobiligram:
            yvalsDT = np.average(zvals, axis=1)
            self.view.panelPlots.on_plot_1D(yvals, yvalsDT, 'Drift time (bins)', ylabel, set_page=True)

        self.SetFocus()

    def on_plot_laser_off(self, evt):

        evtID = evt.GetId()

        try:
            zvals, xvals, yvals, xlabel, ylabel = self.get_laser_off_ion_data()
        except KeyError:
            DialogBox(
                exceptionTitle='Error', exceptionMsg='Please extract data first!',
                type='Error',
            )
            return

        if evtID == ID_uvpd_laser_off_show_heatmap:
            self.view.panelPlots.on_plot_2D(
                zvals, xvals, yvals, xlabel, ylabel,
                override=False, set_page=True,
            )

        elif evtID == ID_uvpd_laser_off_show_waterfall:
            self.view.panelPlots.on_plot_waterfall(
                yvals=xvals, xvals=yvals, zvals=zvals,
                xlabel=xlabel, ylabel=ylabel, set_page=True,
            )

        elif evtID == ID_uvpd_laser_off_show_chromatogram:
            yvalsRT = np.sum(zvals, axis=0)
            self.view.panelPlots.on_plot_RT(xvals, yvalsRT, 'Laser shots', 'Intensity', set_page=True)

        elif evtID == ID_uvpd_laser_off_show_mobiligram:
            yvalsDT = np.average(zvals, axis=1)
            self.view.panelPlots.on_plot_1D(yvals, yvalsDT, 'Drift time (bins)', ylabel, set_page=True)

        self.SetFocus()

    def on_plot_compare_on_off(self, evt):

        evtID = evt.GetId()
        try:
            zvals_on, xvals_on, yvals_on, xlabel_on, ylabel_on = self.get_laser_on_ion_data()
            zvals_off, xvals_off, yvals_off, xlabel_off, ylabel_off = self.get_laser_off_ion_data()
        except KeyError:
            DialogBox(
                exceptionTitle='Error', exceptionMsg='Please extract data first!',
                type='Error',
            )
            return

        colors = self.legend['colors']
        labels = self.legend['labels']

        xvals, yvals = [], []

        if evtID == ID_uvpd_laser_on_off_compare_chromatogam:
            xvals.append(xvals_on)
            xvals.append(xvals_off)

            yvalsRT_on = np.average(zvals_on, axis=0)
            yvalsRT_off = np.average(zvals_off, axis=0)
            yvals.append(yvalsRT_on)
            yvals.append(yvalsRT_off)

            self.view.panelPlots.on_plot_overlay_RT(
                xvals=xvals, yvals=yvals, xlabel='Laser shots',
                colors=colors, xlimits=None, labels=labels,
                set_page=True,
            )

        elif evtID == ID_uvpd_laser_on_off_compare_mobiligram:
            xvals.append(yvals_on)
            xvals.append(yvals_off)

            yvalsDT_on = np.average(zvals_on, axis=1)
            yvalsDT_off = np.average(zvals_off, axis=1)
            yvals.append(yvalsDT_on)
            yvals.append(yvalsDT_off)

            self.view.panelPlots.on_plot_overlay_DT(
                xvals=xvals, yvals=yvals, xlabel='Laser shots',
                colors=colors, xlimits=None, labels=labels,
                set_page=True,
            )

    def on_save_data_heatmap(self, evt):
        evtID = evt.GetId()
        ion_name = self.get_ion_name(self.currentItem)

        if evtID in [ID_uvpd_laser_on_save_heatmap]:
            laser_dataset = 'dataset_1'
            ion_data = self.laser_on_data[ion_name]
            zvals = ion_data['zvals']
            xvals = self.laser_on_marker[:, 0]
            yvals = ion_data['yvals']
        elif evtID == ID_uvpd_laser_off_save_heatmap:
            laser_dataset = 'dataset_2'
            ion_data = self.laser_off_data[ion_name]
            zvals = ion_data['zvals']
            xvals = self.laser_off_marker[:, 0]
            yvals = ion_data['yvals']

        saveData = np.vstack((yvals, zvals.T))

        xvals = list(map(str, xvals.tolist()))
        labels = ['DT']
        for label in xvals:
            labels.append(label)

        # Save 2D array
        kwargs = {'default_name': '{}_{}'.format(ion_name, laser_dataset)}
        self.save_data_to_file(
            data=saveData, labels=labels,
            data_format='%.4f', **kwargs
        )

    def on_save_data(self, evt):
        evtID = evt.GetId()
        ion_name = self.get_ion_name(self.currentItem)

        if evtID in [
            ID_uvpd_laser_on_save_chromatogram,
            ID_uvpd_laser_on_save_mobiligram,
        ]:
            laser_dataset = 'dataset_1'
            ion_data = self.laser_on_data[ion_name]
            if evtID == ID_uvpd_laser_on_save_chromatogram:
                yvals = np.average(ion_data['zvals'], axis=0)
                xvals = self.laser_on_marker[:, 0]
                xlabel, ylabel = 'Laser shot', 'Average intensity'
                name_modifier = 'RT'
            else:
                yvals = np.average(ion_data['zvals'], axis=1)
                xvals = 1 + np.arange(len(yvals))
                xlabel, ylabel = 'Drift time (bins)', 'Average intensity'
                name_modifier = 'DT'

        elif evtID in [
            ID_uvpd_laser_off_save_chromatogram,
            ID_uvpd_laser_off_save_mobiligram,
        ]:
            laser_dataset = 'dataset_2'
            ion_data = self.laser_off_data[ion_name]
            if evtID == ID_uvpd_laser_off_save_chromatogram:
                yvals = np.average(ion_data['zvals'], axis=0)
                xvals = self.laser_off_marker[:, 0]
                xlabel, ylabel = 'Laser shot', 'Average intensity'
                name_modifier = 'RT'
            else:
                yvals = np.average(ion_data['zvals'], axis=1)
                xvals = 1 + np.arange(len(yvals))
                xlabel, ylabel = 'Drift time (bins)', 'Average intensity'
                name_modifier = 'DT'

        data = [xvals, yvals]
        labels = [xlabel, ylabel]
        # Save data
        kwargs = {'default_name': '{}_{}_{}'.format(name_modifier, ion_name, laser_dataset)}
        self.save_data_to_file(
            data=data, labels=labels,
            data_format='%.4f', **kwargs
        )

    def save_data_to_file(self, data=None, labels=None, data_format='%.4f', **kwargs):
        """
        Helper function to save data in consistent manner
        """

        wildcard = 'CSV (Comma delimited) (*.csv)|*.csv|' + \
                   'Text (Tab delimited) (*.txt)|*.txt|' + \
                   'Text (Space delimited (*.txt)|*.txt'

        wildcard_dict = {',': 0, '\t': 1, ' ': 2}

        if kwargs.get('ask_permission', False):
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        else:
            style = wx.FD_SAVE

        dlg = wx.FileDialog(
            self.presenter.view,
            'Please select a name for the file',
            '', '',
            wildcard=wildcard, style=style,
        )
        dlg.CentreOnParent()

        if 'default_name' in kwargs:
            defaultName = kwargs.pop('default_name')
        else:
            defaultName = ''
        defaultName = defaultName.replace(' ', '').replace(':', '').replace(' ', '').replace(
            '.csv', '',
        ).replace('.txt', '').replace('.raw', '').replace('.d', '').replace('.', '_')

        dlg.SetFilename(defaultName)

        try:
            dlg.SetFilterIndex(wildcard_dict[self.config.saveDelimiter])
        except Exception:
            pass

        if not kwargs.get('return_filename', False):
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                __, extension = os.path.splitext(filename)
                self.config.saveExtension = extension
                self.config.saveDelimiter = list(wildcard_dict.keys())[
                    list(
                        wildcard_dict.values(),
                    ).index(dlg.GetFilterIndex())
                ]
                saveAsText(
                    filename=filename,
                    data=data,
                    format=data_format,
                    delimiter=self.config.saveDelimiter,
                    header=self.config.saveDelimiter.join(labels),
                )
            else:
                self.presenter.onThreading(None, ('Cancelled operation', 4, 5), action='updateStatusbar')
        else:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                basename, extension = os.path.splitext(filename)

                return filename, basename, extension
            else:
                return None, None, None

    def on_plot_mobility_monitor(self, evt):

        ion_list = self.get_ion_list()

        if len(ion_list) == 0:
            DialogBox(
                exceptionTitle='Error', exceptionMsg='Please extract data for some ions first!',
                type='Error',
            )
            return

        dt_name, ion_name = self.get_mobility_name(self.currentItem)

        xvals, yvals = [], []
        xvals.append(self.laser_on_data[ion_name]['dt_extract'][dt_name]['xvals'])
        xvals.append(self.laser_off_data[ion_name]['dt_extract'][dt_name]['xvals'])

        yvals.append(self.laser_on_data[ion_name]['dt_extract'][dt_name]['yvals'])
        yvals.append(self.laser_off_data[ion_name]['dt_extract'][dt_name]['yvals'])

        colors = self.legend['colors']
        labels = self.legend['labels']

        self.view.panelPlots.on_plot_overlay_RT(
            xvals=xvals,
            yvals=yvals,
            xlabel='Laser shots',
            colors=colors,
            xlimits=None,
            labels=labels,
            set_page=True,
        )

    def on_extract_mass_spectra(self, evt):
        import gc
        tstart = ttime()

        if len(self.laser_on_list) == 0 or len(self.laser_off_list) == 0:
            DialogBox(
                exceptionTitle='Error', exceptionMsg='Please find peaks first!',
                type='Error',
            )
            return

        # get document
        document = self.document
        # prepare mass range and linearization parameters
        xlimits = [document.parameters['startMS'], document.parameters['endMS']]
        kwargs = {
            'auto_range': self.config.ms_auto_range,
            'mz_min': xlimits[0], 'mz_max': xlimits[1],
            'linearization_mode': self.config.ms_linearization_mode,
        }

        # extract dataset 1 mass spectra
        msX_on, msY_on = self._extract_mass_spectrum(document.path, self.laser_on_list, **kwargs)
        self.view.panelPlots.on_plot_MS(msX_on, msY_on, 'm/z', 'Intensity', set_page=True)
        document.multipleMassSpectrum['UVPD - dataset 1'] = {
            'xvals': msX_on, 'yvals': msY_on, 'xlabels': 'm/z (Da)', 'scan_list': self.laser_on_list,
            'xlimits': xlimits,
        }

        # extract dataset 2 mass spectra
        msX_off, msY_off = self._extract_mass_spectrum(document.path, self.laser_off_list, **kwargs)
        self.view.panelPlots.on_plot_MS(msX_off, msY_off, 'm/z', 'Intensity', set_page=True)
        document.multipleMassSpectrum['UVPD - dataset 2'] = {
            'xvals': msX_off, 'yvals': msY_off, 'xlabels': 'm/z (Da)', 'scan_list': self.laser_off_list,
            'xlimits': xlimits,
        }

        # add to document
        document.gotMultipleMS = True

        # Update document
        self.data_handling.on_update_document(document, 'mass_spectra')
        gc.collect()

        print('In total, it took {:.4f} seconds.'.format(ttime() - tstart))

    def _extract_mass_spectrum(self, document_path, scan_list, **kwargs):
        from processing.spectra import sum_1D_dictionary

        for counter, item in enumerate(scan_list):
            msDict = io_waters.rawMassLynx_MS_bin(
                filename=str(document_path),
                function=1,
                startScan=item[0], endScan=item[1],
                binData=self.config.import_binOnImport,
                mzStart=self.config.ms_mzStart,
                mzEnd=self.config.ms_mzEnd,
                binsize=self.config.ms_mzBinSize,
                **kwargs
            )
            msX, msY = sum_1D_dictionary(ydict=msDict)

            if counter == 0:
                tempArray = msY
            else:
                tempArray = np.add(tempArray, msY)

#         msY_array = tempArray.reshape((len(msY), int(counter+1)), order='F')
#         msY = np.sum(msY_array, axis=1)

        return msX, msY
