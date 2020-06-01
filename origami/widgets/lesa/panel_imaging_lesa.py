"""Panel for LESA datasets"""
# Standard library imports
import logging

# Third-party imports
import wx
import numpy as np
from pubsub import pub

# Local imports
from origami.styles import ListCtrl
from origami.styles import MiniFrame
from origami.styles import validator
from origami.styles import make_menu_item
from origami.utils.check import check_value_order
from origami.utils.screen import calculate_window_size
from origami.processing.utils import get_maximum_value_in_range
from origami.utils.decorators import Timer

# Module globals
logger = logging.getLogger(__name__)


class PanelImagingLESAViewer(MiniFrame):
    """LESA viewer and editor"""

    _peaklist_peaklist = {
        0: {"name": "", "tag": "check", "type": "bool", "show": True, "width": 20},
        1: {"name": "ion name", "tag": "ion_name", "type": "str", "show": True, "width": 120},
        2: {"name": "z", "tag": "charge", "type": "int", "show": True, "width": 25},
        3: {"name": "int", "tag": "intensity", "type": "float", "show": True, "width": 75},
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

        self._display_size = self.parent.GetSize()
        self._display_resolution = wx.ScreenDC().GetPPI()
        self._window_size = calculate_window_size(self._display_size, 0.9)

        self.item_loading_lock = False

        # make gui items
        self.make_gui()
        self.subscribe()

        # load document
        self.document_title = None
        self.mz_data = None
        self.img_data = None
        self.clipboard = dict()
        self.on_select_document()
        self.on_select_spectrum(None)

        # bind
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

    def on_close(self, evt):
        """Destroy this frame"""
        n_clipboard_items = len(self.clipboard)
        if n_clipboard_items > 0:
            from origami.gui_elements.misc_dialogs import DialogBox

            msg = (
                f"Found {n_clipboard_items} item(s) in the clipboard. Closing this window will lose"
                + " your extracted data. Would you like to continue?"
            )
            dlg = DialogBox(title="Clipboard is not empty", msg=msg, kind="Question")
            if dlg == wx.ID_NO:
                msg = "Action was cancelled"
                return

        pub.unsubscribe(self.on_extract_image_from_spectrum, "widget.imaging.lesa.extract.image.spectrum")
        pub.unsubscribe(self.on_extract_image_from_mobilogram, "widget.imaging.lesa.extract.image.mobilogram")
        pub.unsubscribe(self.on_extract_spectrum_from_image, "widget.imaging.lesa.extract.spectrum.image")
        self.Destroy()

    def subscribe(self):
        """Initilize pubsub subscribers"""
        pub.subscribe(self.on_extract_image_from_spectrum, "widget.imaging.lesa.extract.image.spectrum")
        pub.subscribe(self.on_extract_image_from_mobilogram, "widget.imaging.lesa.extract.image.mobilogram")
        pub.subscribe(self.on_extract_spectrum_from_image, "widget.imaging.lesa.extract.spectrum.image")

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

    def on_action_tools(self, evt):
        """Action tools dropdown menu"""
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

    def on_right_click(self, evt):
        """Event on right-click"""
        # ensure that user clicked inside the plot area
        if not hasattr(evt.EventObject, "figure"):
            return

        # get plot
        plot_obj = self.get_plot_obj()

        menu = wx.Menu()
        menu_action_customise_plot = make_menu_item(
            parent=menu, text="Customise plot...", bitmap=self.icons.iconsLib["change_xlabels_16"]
        )
        menu.AppendItem(menu_action_customise_plot)
        self.lock_plot_check = menu.AppendCheckItem(wx.ID_ANY, "Lock plot", help="")
        self.lock_plot_check.Check(plot_obj.lock_plot_from_updating)
        menu.AppendSeparator()
        self.resize_plot_check = menu.AppendCheckItem(-1, "Resize on saving")
        self.resize_plot_check.Check(self.config.resize)
        save_figure_menu_item = make_menu_item(
            menu, evt_id=wx.ID_ANY, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
        )
        menu.AppendItem(save_figure_menu_item)
        menu_action_copy_to_clipboard = make_menu_item(
            parent=menu, evt_id=wx.ID_ANY, text="Copy plot to clipboard", bitmap=self.icons.iconsLib["filelist_16"]
        )
        menu.AppendItem(menu_action_copy_to_clipboard)

        menu.AppendSeparator()
        reset_plot_menu_item = make_menu_item(menu, evt_id=wx.ID_ANY, text="Reset plot zoom")
        menu.AppendItem(reset_plot_menu_item)

        clear_plot_menu_item = make_menu_item(
            menu, evt_id=wx.ID_ANY, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
        )
        menu.AppendItem(clear_plot_menu_item)

        self.Bind(wx.EVT_MENU, self.on_resize_check, self.resize_plot_check)
        self.Bind(wx.EVT_MENU, self.on_customise_plot, menu_action_customise_plot)
        self.Bind(wx.EVT_MENU, self.on_save_figure, save_figure_menu_item)
        self.Bind(wx.EVT_MENU, self.on_copy_to_clipboard, menu_action_copy_to_clipboard)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, clear_plot_menu_item)
        self.Bind(wx.EVT_MENU, self.on_reset_plot, reset_plot_menu_item)
        self.Bind(wx.EVT_MENU, self.on_lock_plot, self.lock_plot_check)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def make_settings_panel(self, split_panel):
        """Make settings panel"""
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        # add spectrum controls
        spectrum_choice = wx.StaticText(panel, -1, "Spectrum:")
        self.spectrum_choice = wx.ComboBox(panel, choices=[], style=wx.CB_READONLY)
        self.spectrum_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)
        self.spectrum_choice.Bind(wx.EVT_COMBOBOX, self.on_select_spectrum)

        # add image controls
        choices = ["None", "Total Intensity", "Root Mean Square", "Median", "L2"]

        normalization_choice = wx.StaticText(panel, -1, "Normalization:")
        self.normalization_choice = wx.ComboBox(panel, choices=choices, style=wx.CB_READONLY)
        self.normalization_choice.SetStringSelection("None")
        self.normalization_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)
        self.normalization_choice.Bind(wx.EVT_COMBOBOX, self.on_update_normalization)

        # add item controls
        item_name = wx.StaticText(panel, wx.ID_ANY, "Item name:")
        self.item_name = wx.TextCtrl(panel, wx.ID_ANY, "", style=wx.TE_READONLY)

        label_value = wx.StaticText(panel, -1, "label:")
        self.label_value = wx.TextCtrl(panel, -1, "")
        self.label_value.Bind(wx.EVT_TEXT, self.on_update_item)

        charge_value = wx.StaticText(panel, -1, "charge:")
        self.charge_value = wx.TextCtrl(panel, -1, "", validator=validator("int"))
        self.charge_value.Bind(wx.EVT_TEXT, self.on_update_item)

        item_color = wx.StaticText(panel, -1, "color:")
        self.item_color_btn = wx.Button(panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="color.label")
        self.item_color_btn.SetBackgroundColour([0, 0, 0])
        self.item_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        colormap_label = wx.StaticText(panel, -1, "colormap:")
        self.colormap_value = wx.Choice(panel, -1, choices=self.config.cmaps2, size=(-1, -1))
        self.colormap_value.Bind(wx.EVT_CHOICE, self.on_update_item)

        # make listctrl
        self.make_listctrl_panel(panel)
        self.make_dt_plot_panel(panel)

        horizontal_line_0 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

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
        n += 1
        grid.Add(horizontal_line_2, (n, 0), (1, 5), flag=wx.ALIGN_CENTER | wx.EXPAND)
        n += 1
        grid.Add(item_name, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.item_name, (n, 1), wx.GBSpan(1, 3), flag=wx.ALIGN_CENTER | wx.EXPAND)
        n += 1
        grid.Add(label_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_value, (n, 1), wx.GBSpan(1, 3), flag=wx.ALIGN_CENTER | wx.EXPAND)
        n += 1
        grid.Add(charge_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.charge_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(item_color, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.item_color_btn, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(colormap_label, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colormap_value, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)

        # setup growable column
        grid.AddGrowableCol(3)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 5)
        main_sizer.Add(horizontal_line_0, 0, wx.EXPAND, 10)
        main_sizer.Add(self.plot_panel_DT, 1, wx.EXPAND, 10)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND, 10)
        #
        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_plot_panel(self, split_panel):
        """Make plot panel"""
        panel = wx.SplitterWindow(split_panel, wx.ID_ANY, style=wx.TAB_TRAVERSAL | wx.SP_3DSASH, name="plot")

        self.plot_panel_MS, self.plot_window_MS, __ = self.panel_plot.make_base_plot(
            panel, self.config._plotSettings["RT"]["gui_size"]
        )

        self.plot_panel_img, self.plot_window_img, __ = self.panel_plot.make_base_plot(
            panel, self.config._plotSettings["2D"]["gui_size"]
        )

        panel.SplitHorizontally(self.plot_panel_MS, self.plot_panel_img)
        panel.SetMinimumPaneSize(400)
        panel.SetSashGravity(0.5)
        panel.SetSashSize(5)

        return panel

    def make_listctrl_panel(self, panel):
        """Initilize table"""
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

    def make_dt_plot_panel(self, panel):
        """Make DT plot and hide it"""

        self.plot_panel_DT, self.plot_window_DT, __ = self.panel_plot.make_base_plot(
            panel, self.config._plotSettings["DT"]["gui_size"]
        )
        self.plot_panel_DT.Show(False)

    def on_update_item(self, evt):
        if self.item_loading_lock:
            return

        print("on_update_item")

    def get_plot_obj(self):
        plot_obj = {"MS": self.plot_window_MS, "2D": self.plot_window_img, "1D": self.plot_window_DT}[
            self.view.plot_name
        ]
        return plot_obj

    def on_clear_plot(self, evt):
        """Clear plot"""
        plot_obj = self.get_plot_obj()
        plot_obj.clear()

    def on_reset_plot(self, evt):
        """Reset plot"""
        plot_obj = self.get_plot_obj()
        plot_obj.on_reset_zoom()

    def on_resize_check(self, evt):
        """Toggle resize check in the plot"""
        self.panel_plot.on_resize_check(None)

    def on_copy_to_clipboard(self, evt):
        """Copy plot object to clipboard"""
        plot_obj = self.get_plot_obj()
        plot_obj.copy_to_clipboard()

    def on_customise_plot(self, evt):
        plot_obj = self.get_plot_obj()
        self.panel_plot.on_customise_plot(None, plot="Imaging: LESA...", plot_obj=plot_obj)

    def on_save_figure(self, evt):
        plot_title = "MS" if self.view.plot_name == "MS" else "image"
        plot_obj = self.get_plot_obj()
        self.panel_plot.save_images(None, None, plot_obj=plot_obj, image_name=plot_title)

    def on_lock_plot(self, evt):
        """Lock/unlock plot"""
        plot_obj = self.get_plot_obj()
        plot_obj.lock_plot_from_updating = not plot_obj.lock_plot_from_updating

    def on_apply(self, evt):
        print("on_apply")

        if evt is not None:
            evt.Skip()

    def on_assign_color(self, evt):
        """Assign new color to the item"""
        from origami.gui_elements.dialog_color_picker import DialogColorPicker

        dlg = DialogColorPicker(self, self.config.customColors)
        if dlg.ShowModal() == "ok":
            color_255, __, __ = dlg.GetChosenColour()
            self.config.customColors = dlg.GetCustomColours()
        else:
            return

        # update button
        self.item_color_btn.SetBackgroundColour(color_255)

        # update peaklist

    #             rows = self.peaklist.GetItemCount()
    #             for row in range(rows):
    #                 if self.peaklist.IsChecked(index=row):
    # #                     self.on_update_annotation(row, update_item, **update_dict)
    #
    #                 # replot annotation after its been altered
    #                 __, annotation_obj = self.on_get_annotation_obj(row)
    #                 self.on_add_label_to_plot(annotation_obj)

    def on_extract_tic_image(self):
        """Load TIC image"""
        self.on_extract_image_from_spectrum([None, None, None, None])

    def on_extract_image_from_mobilogram(self, rect):
        zvals = self.data_handling.on_extract_LESA_img_from_mobilogram(
            rect[0], rect[1], self.clipboard[self.img_data]["zvals_dt"]
        )

    def on_extract_image_from_spectrum(self, rect):
        def plot():
            # update plots
            self.on_plot_image(self.clipboard[ion_name])
            self.on_plot_mobilogram(self.clipboard[ion_name])

        xmin, xmax, __, __ = rect

        if xmin is None or xmax is None:
            xmin, xmax = 0, 99999
            add_to_table = False
            ion_name = None
        else:
            ion_name = f"{xmin:.2f}-{xmax:.2f}"
            add_to_table, _ = self.find_item(ion_name)

        if ion_name in self.clipboard:
            logger.info("Found item in the clipboard...")
            plot()
            return

        xmin, xmax = check_value_order(xmin, xmax)
        if self.mz_data is not None:
            mz_x = self.mz_data["xvals"]
            mz_y = self.mz_data["yvals"]

            mz_xy = np.transpose([mz_x, mz_y])
            mz_y_max = np.round(get_maximum_value_in_range(mz_xy, mz_range=(xmin, xmax)) * 100, 2)

            # predict charge state
            charge = self.data_processing.predict_charge_state(mz_xy[:, 0], mz_xy[:, 1], (xmin - 0, xmax + 3))

            # get color
            color = next(self.config.custom_color_cycle)

            # add to table
            if add_to_table and ion_name is not None:
                self.on_add_to_table(
                    ion_name=ion_name, charge=charge, intensity=mz_y_max, color=color, label=f"ion={ion_name}"
                )

        # get data
        method = {"Total Intensity": "total", "Root Mean Square": "sqrt", "Median": "median", "L2": "l2"}.get(
            self.normalization_choice.GetStringSelection(), "None"
        )

        # get image data
        zvals = self.data_handling.on_extract_LESA_img_from_mass_range_norm(xmin, xmax, self.document_title, method)
        xvals = np.arange(zvals.shape[0]) + 1
        yvals = np.arange(zvals.shape[1]) + 1

        self.img_data = ion_name
        self.clipboard[ion_name] = dict(
            zvals=zvals, xvals=xvals, yvals=yvals, extract_range=[xmin, xmax], ion_name=ion_name
        )

        # get mobilogram data
        # TODO: should check whether IM data exists
        xvals_dt, yvals_dt, zvals_dt = self.data_handling.on_extract_LESA_mobilogram_from_mass_range(
            xmin, xmax, self.document_title
        )
        self.clipboard[ion_name].update(xvals_dt=xvals_dt, yvals_dt=yvals_dt, zvals_dt=zvals_dt)

        plot()

    def on_plot_image(self, img_data):
        self.panel_plot.on_plot_image(
            img_data["zvals"],
            img_data["xvals"],
            img_data["yvals"],
            plot_obj=self.plot_window_img,
            callbacks=dict(CTRL="widget.imaging.lesa.extract.spectrum.image"),
        )

    def on_plot_spectrum(self):
        self.panel_plot.on_plot_MS(
            self.mz_data["xvals"],
            self.mz_data["yvals"],
            show_in_window="LESA",
            plot_obj=self.plot_window_MS,
            override=False,
            callbacks=dict(CTRL="widget.imaging.lesa.extract.image.spectrum"),
        )

    def on_plot_mobilogram(self, img_data):
        self.panel_plot.on_plot_1D(
            img_data["xvals_dt"],
            img_data["yvals_dt"],
            xlabel="Drift time (bins)",
            show_in_window="LESA",
            plot_obj=self.plot_window_DT,
            override=False,
            callbacks=dict(CTRL="widget.imaging.lesa.extract.image.mobilogram"),
        )

    def on_add_to_table(self, **add_dict):
        from origami.utils.color import round_rgb
        from origami.utils.color import convert_rgb_255_to_1
        from origami.utils.color import get_font_color

        color = add_dict["color"]

        self.peaklist.Append(
            [
                "",
                str(add_dict["ion_name"]),
                str(add_dict["charge"]),
                f"{add_dict['intensity']:.2f}",
                str(round_rgb(convert_rgb_255_to_1(color))),
                next(self.config.overlay_cmap_cycle),
                str(add_dict.get("label", "")),
                self.document_title,
            ]
        )
        self.peaklist.SetItemBackgroundColour(self.peaklist.GetItemCount() - 1, color)
        self.peaklist.SetItemTextColour(self.peaklist.GetItemCount() - 1, get_font_color(color, return_rgb=True))

    def on_extract_spectrum_from_image(self, rect):
        xmin, xmax, ymin, ymax = rect

    def on_update_normalization(self, evt):
        from origami.processing.heatmap import normalize_2D
        from copy import deepcopy

        # get method
        method = {"Total Intensity": "total", "Root Mean Square": "sqrt", "Median": "median", "L2": "l2"}.get(
            self.normalization_choice.GetStringSelection(), "None"
        )

        # cancel if no data is available
        if not self.img_data:
            logger.warning("No imaging data available!")
            return

        img_data = deepcopy(self.clipboard[self.img_data])
        try:
            xmin, xmax = img_data["extract_range"]
            img_data["zvals"] = self.data_handling.on_extract_LESA_img_from_mass_range_norm(
                xmin, xmax, self.document_title, method
            )
        except KeyError:
            img_data["zvals"] = normalize_2D(img_data["zvals"], self.normalization_choice.GetStringSelection(), p=0.1)

        self.on_plot_image(img_data)
        logger.info(f"Updated image with '{method}' normalization")

    @Timer
    def on_select_spectrum(self, evt):
        # get data
        spectrum_name = self.spectrum_choice.GetStringSelection()
        __, mz_data = self.data_handling.get_spectrum_data([self.document_title, spectrum_name])
        self.mz_data = mz_data

        if spectrum_name == "Mass Spectrum":
            self.on_extract_tic_image()

        # show plot
        self.on_plot_spectrum()

    def on_select_document(self):
        document = self.data_handling._get_document_of_type("Type: Imaging", allow_creation=False)
        if document:
            self.document_title = document.title
            itemlist = self.data_handling.generate_item_list_mass_spectra("comparison")
            spectrum_list = itemlist.get(document.title, [])
            if spectrum_list:
                self.spectrum_choice.SetItems(spectrum_list)
                self.spectrum_choice.SetStringSelection(spectrum_list[0])

    def on_double_click_on_item(self, evt):
        """Select item in list"""

        def get_ion_range(ion_name):
            # TODO: add dt support
            mz_min, mz_max = ion_name.split("-")
            return float(mz_min), float(mz_max)

        self.item_loading_lock = True
        item_info = self.on_get_item_information(None)

        # already present
        if item_info["ion_name"] == self.img_data:
            self.on_update_normalization(None)
        # need to retrieve again
        else:
            xmin, xmax = get_ion_range(item_info["ion_name"])
            self.on_extract_image_from_spectrum([xmin, xmax, None, None])

        self.on_populate_item(item_info)
        self.on_toggle_dt_plot()
        self.item_loading_lock = True

    def on_populate_item(self, item_info):
        """Populate values in the gui"""
        self.charge_value.SetValue(str(item_info["charge"]))
        self.label_value.SetValue(item_info["label"])
        self.item_name.SetValue(item_info["ion_name"])
        self.colormap_value.SetStringSelection(item_info["colormap"])
        self.item_color_btn.SetBackgroundColour(item_info["color"])

    def on_create_blank_document(self, evt):
        self.data_handling.create_new_document_of_type(document_type="imaging")

    def on_get_item_information(self, item_id):
        if item_id is None:
            item_id = self.peaklist.item_id

        information = self.peaklist.on_get_item_information(item_id)
        return information

    def find_item(self, name):
        """Check for duplicate items with the same name"""
        count = self.peaklist.GetItemCount()
        for i in range(count):
            information = self.on_get_item_information(i)

            if information["ion_name"] == name:
                return False, i

        return True, -1

    def on_toggle_dt_plot(self, show=True):
        #         show = not self.plot_panel_DT.IsShown()
        self.plot_panel_DT.Show(show)
        self.Layout()
