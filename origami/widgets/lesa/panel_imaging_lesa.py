# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
# Load libraries
import logging

import wx
from styles import ListCtrl
from styles import make_menu_item
from styles import MiniFrame
from utils.screen import calculate_window_size

logger = logging.getLogger("origami")


class PanelImagingLESAViewer(MiniFrame):
    """LESA viewer and editor"""

    _peaklist_peaklist = {
        0: {"name": "", "tag": "check", "type": "bool", "show": True, "width": 20},
        1: {"name": "ion name", "tag": "ion_name", "type": "str", "show": True, "width": 80},
        2: {"name": "z", "tag": "charge", "type": "int", "show": True, "width": 35},
        3: {"name": "int", "tag": "intensity", "type": "float", "show": True, "width": 50},
        4: {"name": "color", "tag": "color", "type": "color", "show": True, "width": 80},
        5: {"name": "colormap", "tag": "colormap", "type": "str", "show": True, "width": 80},
        6: {"name": "label", "tag": "label", "type": "str", "show": True, "width": 70},
        7: {"name": "document", "tag": "document", "type": "str", "show": True, "width": 70},
    }

    keyword_alias = {"colormap": "cmap"}

    def __init__(self, parent, presenter, config, icons, **kwargs):
        MiniFrame.__init__(
            self,
            parent,
            title="Imaging: LESA",
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
            bind_key_events=False,
        )

        self.parent = parent
        self.presenter = presenter
        self.view = presenter.view
        self.config = config
        self.icons = icons

        self.data_handling = presenter.data_handling
        self.data_processing = presenter.data_processing
        self.data_visualisation = presenter.data_visualisation

        self.panel_plot = self.presenter.view.panelPlots
        self.document_tree = self.presenter.view.panelDocuments.documents

        self._display_size = wx.GetDisplaySize()
        self._display_resolution = wx.ScreenDC().GetPPI()
        self._window_size = calculate_window_size(self._display_size, 0.9)

        # make gui items
        self.make_gui()

        # load document
        self.document_title = None
        self.on_select_document()

        # bind
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

    def on_right_click(self, evt):
        # ensure that user clicked inside the plot area
        if not hasattr(evt.EventObject, "figure"):
            return

    #         menu = wx.Menu()
    #         menu_action_customise_plot = make_menu_item(
    #             parent=menu, text="Customise plot...", bitmap=self.icons.iconsLib["change_xlabels_16"]
    #         )
    #         menu.AppendItem(menu_action_customise_plot)
    #         menu.AppendSeparator()
    #         self.resize_plot_check = menu.AppendCheckItem(-1, "Resize on saving")
    #         self.resize_plot_check.Check(self.config.resize)
    #         save_figure_menu_item = make_menu_item(
    #             menu, id=wx.ID_ANY, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
    #         )
    #         menu.AppendItem(save_figure_menu_item)
    #         menu_action_copy_to_clipboard = make_menu_item(
    #             parent=menu, id=wx.ID_ANY, text="Copy plot to clipboard", bitmap=self.icons.iconsLib["filelist_16"]
    #         )
    #         menu.AppendItem(menu_action_copy_to_clipboard)
    #
    #         menu.AppendSeparator()
    #         clear_plot_menu_item = make_menu_item(
    #             menu, id=wx.ID_ANY, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
    #         )
    #         menu.AppendItem(clear_plot_menu_item)
    #
    #         self.Bind(wx.EVT_MENU, self.on_resize_check, self.resize_plot_check)
    #         self.Bind(wx.EVT_MENU, self.on_customise_plot, menu_action_customise_plot)
    #         self.Bind(wx.EVT_MENU, self.on_save_figure, save_figure_menu_item)
    #         self.Bind(wx.EVT_MENU, self.on_copy_to_clipboard, menu_action_copy_to_clipboard)
    #         self.Bind(wx.EVT_MENU, self.on_clear_plot, clear_plot_menu_item)
    #
    #         self.PopupMenu(menu)
    #         menu.Destroy()
    #         self.SetFocus()

    def on_close(self, evt):
        """Destroy this frame"""
        self.Destroy()

    def on_clear_plot(self, evt):
        self.plot_window.clearPlot()

    def on_resize_check(self, evt):
        self.panel_plot.on_resize_check(None)

    def on_copy_to_clipboard(self, evt):
        self.plot_window.copy_to_clipboard()

    def on_customise_plot(self, evt):
        self.panel_plot.on_customise_plot(None, plot="Overlay...", plot_obj=self.plot_window)

    def on_save_figure(self, evt):
        plot_title = "overlay"
        self.panel_plot.save_images(None, None, plot_obj=self.plot_window, image_name=plot_title)

    def make_gui(self):

        # make panel
        settings_panel = self.make_settings_panel(self)
        self._settings_panel_size = settings_panel.GetSize()
        settings_panel.SetMinSize((400, -1))

        plot_panel = self.make_plot_panel(self)

        # pack elements
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(plot_panel, 1, wx.EXPAND, 0)
        self.main_sizer.Add(settings_panel, 0, wx.EXPAND, 0)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)
        self.SetSize(self._window_size)
        self.Layout()
        self.Show(True)

        self.CentreOnScreen()
        self.SetFocus()

    def on_apply(self, evt):
        print("on_apply")

        if evt is not None:
            evt.Skip()

    def on_select_spectrum(self, evt):
        # get data
        spectrum_name = self.spectrum_choice.GetStringSelection()
        __, mz_data = self.data_handling.get_spectrum_data([self.document_title, spectrum_name])

        # show plot
        self.panel_plot.on_plot_MS(
            mz_data["xvals"], mz_data["yvals"], show_in_window="lesa", plot_obj=self.plot_window_MS, override=False
        )

    def on_select_document(self):
        document = self.data_handling._get_document_of_type("Type: Imaging")
        if document:
            self.document_title = document.title
            itemlist = self.data_handling.generate_item_list_mass_spectra("comparison")
            spectrum_list = itemlist.get(document.title, [])
            if spectrum_list:
                self.spectrum_choice.SetItems(spectrum_list)
                self.spectrum_choice.SetStringSelection(spectrum_list[0])

    def make_settings_panel(self, split_panel):

        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        # add spectrum controls
        spectrum_choice = wx.StaticText(panel, -1, "Spectrum:")
        self.spectrum_choice = wx.ComboBox(panel, choices=[], style=wx.CB_READONLY)
        self.spectrum_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)
        self.spectrum_choice.Bind(wx.EVT_COMBOBOX, self.on_select_spectrum)

        # add image controls
        normalization_choice = wx.StaticText(panel, -1, "Normalization:")
        self.normalization_choice = wx.ComboBox(panel, choices=["None"], style=wx.CB_READONLY)
        self.normalization_choice.SetStringSelection("None")
        self.normalization_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)
        #         self.normalization_choice.Bind(wx.EVT_COMBOBOX, self.on_select_spectrum)

        # make listctrl
        self.make_listctrl_panel(panel)

        horizontal_line_0 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        # pack buttons
        #         btn_grid = wx.GridBagSizer(2, 2)
        #         n = 0
        #         btn_grid.Add(self.action_btn, (n, 0), flag=wx.ALIGN_CENTER)
        #         btn_grid.Add(self.plot_btn, (n, 1), flag=wx.ALIGN_CENTER)
        #         btn_grid.Add(self.add_to_document_btn, (n, 2), flag=wx.ALIGN_CENTER)
        #         btn_grid.Add(self.cancel_btn, (n, 3), flag=wx.ALIGN_CENTER)
        #         btn_grid.Add(self.hot_plot_check, (n, 4), flag=wx.ALIGN_CENTER)

        # pack heatmap items
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(spectrum_choice, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.spectrum_choice, (n, 1), (1, 3), flag=wx.ALIGN_CENTER | wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_1, (n, 0), (1, 5), flag=wx.ALIGN_CENTER | wx.EXPAND)
        n += 1
        grid.Add(normalization_choice, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.normalization_choice, (n, 1), (1, 2), flag=wx.ALIGN_CENTER | wx.EXPAND)

        # setup growable column
        grid.AddGrowableCol(3)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 5)
        main_sizer.Add(horizontal_line_0, 0, wx.EXPAND, 10)
        #         main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTRE_HORIZONTAL, 10)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND, 10)
        #
        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_plot_panel(self, split_panel):
        panel = wx.SplitterWindow(split_panel, wx.ID_ANY, style=wx.TAB_TRAVERSAL | wx.SP_3DSASH, name="plot")

        self.plot_panel_MS, self.plot_window_MS, __ = self.panel_plot.make_plot(
            panel, self.config._plotSettings["RT"]["gui_size"]
        )
        self.plot_panel_img, self.plot_window_img, __ = self.panel_plot.make_plot(
            panel, self.config._plotSettings["2D"]["gui_size"]
        )

        panel.SplitHorizontally(self.plot_panel_MS, self.plot_panel_img)
        panel.SetMinimumPaneSize(300)
        panel.SetSashGravity(0.5)
        panel.SetSashSize(5)

        return panel

    def make_listctrl_panel(self, panel):

        self.peaklist = ListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES, column_info=self._peaklist_peaklist)
        for col in range(len(self._peaklist_peaklist)):
            item = self._peaklist_peaklist[col]
            order = col
            name = item["name"]
            width = 0
            if item["show"]:
                width = item["width"]
            self.peaklist.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_CENTER)
            self.peaklist.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        max_peaklist_size = (int(self._window_size[0] * 0.3), -1)
        self.peaklist.SetMaxClientSize(max_peaklist_size)

        self.peaklist.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click_on_item)

    def on_double_click_on_item(self, evt):
        """Create annotation for activated peak."""
        pass

    def on_action_tools(self, evt):

        menu = wx.Menu()

        menu_action_create_blank_document = make_menu_item(
            parent=menu,
            text="Create blank IMAGING document",
            bitmap=self.icons.iconsLib["new_document_16"],
            help_text="",
        )

        menu.AppendItem(menu_action_create_blank_document)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_create_blank_document, menu_action_create_blank_document)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_create_blank_document(self, evt):
        self.data_handling.create_new_document_of_type(document_type="imaging")

    def on_get_item_information(self, item_id):
        information = self.peaklist.on_get_item_information(item_id)
        return information
