"""Panel for LESA datasets"""
# Standard library imports
import logging
from enum import IntEnum
from typing import List

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.styles import MiniFrame
from origami.styles import set_tooltip
from origami.styles import make_menu_item
from origami.icons.assets import Icons
from origami.utils.screen import calculate_window_size
from origami.config.config import CONFIG
from origami.utils.exceptions import MessageError
from origami.config.environment import ENV
from origami.gui_elements.panel_base import TableMixin
from origami.gui_elements.panel_base import DatasetMixin
from origami.gui_elements.popup_view import PopupMobilogramView
from origami.gui_elements.views.view_heatmap import ViewImagingIonHeatmap
from origami.gui_elements.views.view_spectrum import ViewMassSpectrum

# Module globals
LOGGER = logging.getLogger(__name__)


class TableColumnIndex(IntEnum):
    """Table indexer"""

    check = 0
    ion_name = 1
    color = 2
    colormap = 3
    label = 4


class PanelImagingLESAViewer(MiniFrame, TableMixin, DatasetMixin):
    """LESA viewer and editor"""

    TABLE_DICT = {
        0: {
            "name": "",
            "tag": "check",
            "type": "bool",
            "show": True,
            "width": 20,
            "order": 0,
            "id": wx.NewIdRef(),
            "hidden": True,
        },
        1: {
            "name": "ion name",
            "tag": "ion_name",
            "type": "str",
            "show": True,
            "width": 120,
            "order": 1,
            "id": wx.NewIdRef(),
        },
        2: {
            "name": "color",
            "tag": "color",
            "type": "color",
            "show": True,
            "width": 80,
            "order": 2,
            "id": wx.NewIdRef(),
        },
        3: {
            "name": "colormap",
            "tag": "colormap",
            "type": "str",
            "show": True,
            "width": 80,
            "order": 3,
            "id": wx.NewIdRef(),
        },
        4: {"name": "label", "tag": "label", "type": "str", "show": True, "width": 70, "order": 4, "id": wx.NewIdRef()},
    }
    TABLE_COLUMN_INDEX = TableColumnIndex
    USE_COLOR = True
    HELP_LINK = r"https://origami.lukasz-migas.com/"
    PANEL_BASE_TITLE = "LESA - Viewer"

    # ui elements
    spectrum_choice = None
    normalization_choice = None
    item_name = None
    label_value = None
    item_color_btn = None
    colormap_value = None
    lock_plot_check = None
    resize_plot_check = None
    view_ms = None
    plot_ms = None
    panel_top_ms = None
    view_img = None
    plot_img = None
    panel_bottom_img = None
    _settings_panel_size = None
    popup = None

    def __init__(
        self, parent, presenter, document_title: str = None, spectrum_list: List[str] = None, debug: bool = False
    ):
        MiniFrame.__init__(
            self,
            parent,
            title="Imaging: LESA",
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
            bind_key_events=False,
        )
        TableMixin.__init__(self)

        self.view = parent
        self.presenter = presenter

        # create instance of the icons
        self._icons = Icons()

        # view
        screen_size = wx.GetDisplaySize()
        if parent is not None:
            screen_size = self.parent.GetSize()
        self._display_size = screen_size
        self._display_resolution = wx.ScreenDC().GetPPI()
        if parent is None:
            self._window_size = calculate_window_size(self._display_size, 0.4)
        else:
            self._window_size = calculate_window_size(self._display_size, 0.8)

        self.item_loading_lock = False
        self.document_title = document_title

        # make gui items
        self.make_gui()

        # load document
        self._spectrum_list = spectrum_list
        self.clipboard = dict()
        self.clipboard_last = None
        self.setup()

        if not debug:
            self.on_select_document()

        # bind
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

    @property
    def data_handling(self):
        """Return handle to `data_handling`"""
        return self.presenter.data_handling

    @property
    def document_tree(self):
        """Return handle to `document_tree`"""
        return self.presenter.view.panelDocuments.documents

    @property
    def panel_plot(self):
        """Return handle to `panel_plot`"""
        return self.presenter.view.panelPlots

    @property
    def document(self):
        """Return instance of the document"""
        if self.document_title is not None:
            return ENV.on_get_document(self.document_title)

    def make_gui(self):
        """Make UI"""
        # make panel
        settings_panel = self.make_settings_panel(self)
        self._settings_panel_size = settings_panel.GetSize()
        settings_panel.SetMinSize((400, -1))

        plot_panel = self.make_plot_panel(self)

        # pack elements
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(plot_panel, 1, wx.EXPAND, 0)
        main_sizer.Add(settings_panel, 0, wx.EXPAND, 0)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)
        self.SetSize(self._window_size)
        self.Layout()
        self.Show(True)

        self.CentreOnParent()
        self.SetFocus()

    def make_settings_panel(self, split_panel):
        """Make settings panel"""
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        # add spectrum controls
        self.spectrum_choice = wx.ComboBox(panel, choices=[], style=wx.CB_READONLY)
        self.spectrum_choice.Bind(wx.EVT_COMBOBOX, self.on_plot_spectrum)

        # add image controls
        choices = self.get_normalization_list()

        self.normalization_choice = wx.ComboBox(panel, choices=choices, style=wx.CB_READONLY)
        self.normalization_choice.SetStringSelection("None")
        self.normalization_choice.Bind(wx.EVT_COMBOBOX, self.on_update_normalization)

        # add item controls
        self.item_name = wx.StaticText(panel, wx.ID_ANY)

        self.label_value = wx.TextCtrl(panel, -1, "")
        self.label_value.Bind(wx.EVT_TEXT, self.on_update_item)
        set_tooltip(self.label_value, "Select label for current item")

        self.item_color_btn = wx.Button(panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="color.label")
        self.item_color_btn.SetBackgroundColour([0, 0, 0])
        self.item_color_btn.Bind(wx.EVT_BUTTON, self.on_change_color)
        set_tooltip(self.item_color_btn, "Select color for current item")

        self.colormap_value = wx.Choice(panel, -1, choices=CONFIG.cmaps2, size=(-1, -1))
        self.colormap_value.Bind(wx.EVT_CHOICE, self.on_update_item)
        set_tooltip(self.colormap_value, "Select colormap for current item")

        # make peaklist
        self.peaklist = self.make_table(self.TABLE_DICT, panel)

        # add buttons
        self.info_btn = self.make_info_button(panel)
        self.settings_btn = self.make_settings_button(panel)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(self.settings_btn, 0)
        btn_sizer.Add(self.info_btn, 0)

        # pack heatmap items
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(wx.StaticText(panel, -1, "Mass spectrum:"), (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.spectrum_choice, (n, 1), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, -1, "Normalization:"), (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.normalization_choice, (n, 1), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), (1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, wx.ID_ANY, "Item name:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.item_name, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, -1, "Label:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, -1, "Colormap:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colormap_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.item_color_btn, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)

        # setup growable column
        grid.AddGrowableCol(2, 1)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 3)
        main_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)
        panel.Layout()

        return panel

    def make_plot_panel(self, split_panel):
        """Make plot panel"""
        panel = wx.SplitterWindow(split_panel, wx.ID_ANY, style=wx.TAB_TRAVERSAL | wx.SP_3DSASH, name="plot")

        self.view_ms = ViewMassSpectrum(
            panel,
            (8, 2.5),  # noqa
            CONFIG,
            allow_extraction=True,
            axes_size=(0.15, 0.25, 0.8, 0.6),
            callbacks=dict(CTRL="widget.imaging.lesa.extract.image.spectrum"),
        )
        self.panel_top_ms = self.view_ms.panel
        self.plot_ms = self.view_ms.figure

        self.view_img = ViewImagingIonHeatmap(
            panel,
            (6, 6),
            CONFIG,
            allow_extraction=True,
            axes_size=(0.3, 0.3, 0.6, 0.6),
            callbacks=dict(CTRL="widget.imaging.lesa.extract.spectrum.image"),
        )
        self.panel_bottom_img = self.view_img.panel
        self.plot_img = self.view_img.figure

        panel.SplitHorizontally(self.panel_top_ms, self.panel_bottom_img)
        panel.SetMinimumPaneSize(300)
        panel.SetSashGravity(0.5)

        return panel

    def setup(self):
        """Setup"""
        # setup spectrum maximum size to prevent it changing size as the user resized the window
        self.spectrum_choice.SetMaxSize(self.spectrum_choice.GetSize())

        # setup pubsub events
        pub.subscribe(self.on_extract_image_from_spectrum, "widget.imaging.lesa.extract.image.spectrum")
        pub.subscribe(self.on_extract_image_from_mobilogram, "widget.imaging.lesa.extract.image.mobilogram")
        pub.subscribe(self.on_extract_spectrum_from_image, "widget.imaging.lesa.extract.spectrum.image")

        # setup dataset mixin
        self._dataset_mixin_setup()

        # setup listctrl events
        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_item)

    def on_close(self, evt, force: bool = False):
        """Destroy this frame"""
        n_clipboard_items = len(self.clipboard)
        if n_clipboard_items > 0 and not force:
            from origami.gui_elements.dialog_review_ask import DialogAskReview

            msg = (
                f"Found {n_clipboard_items} item(s) in the clipboard. Closing this window will lose"
                + " your extracted data. \nWould you like to continue?"
            )

            dlg = DialogAskReview(self.view, msg)
            res = dlg.ShowModal()
            if res == wx.ID_SAVE:
                self.on_review()
            elif res == wx.ID_NO:
                LOGGER.warning("Action was cancelled")
                return

        self._dataset_mixin_teardown()
        pub.unsubscribe(self.on_extract_image_from_spectrum, "widget.imaging.lesa.extract.image.spectrum")
        pub.unsubscribe(self.on_extract_image_from_mobilogram, "widget.imaging.lesa.extract.image.mobilogram")
        pub.unsubscribe(self.on_extract_spectrum_from_image, "widget.imaging.lesa.extract.spectrum.image")
        self.Destroy()

    def on_review(self):
        """Review all data that is present in the dataset"""
        from origami.gui_elements.dialog_review_editor import DialogReviewEditorExtract

        # generate item list
        item_list = []
        for name, values in self.clipboard.items():
            if values.get("mobilogram"):
                item_list.append(["Mobilogram", "Mobilograms/" + name])
            if values.get("image"):
                item_list.append(["Heatmap", "IonHeatmaps/" + name])

        dlg = DialogReviewEditorExtract(self, item_list)
        dlg.ShowModal()

        output_list = dlg.output_list
        self.on_add_to_document(output_list)

    def on_add_to_document(self, output_list: List[str]):
        """Add data to document and update document view"""
        document = ENV.on_get_document(self.document_title)

        for name in output_list:
            obj_type, name = name.split("/")
            values = self.clipboard[name]
            item_id = self.on_find_item("ion_name", name)
            item_info = self.on_get_item_information(item_id)
            if obj_type == "Mobilograms":
                dt_obj = values["mobilogram"]
                dt_obj.set_metadata(
                    {"label": item_info["label"], "colormap": item_info["colormap"], "color": item_info["color_255to1"]}
                )
                dt_obj = document.add_mobilogram(name, dt_obj)
                self.document_tree.on_update_document(dt_obj.DOCUMENT_KEY, name, self.document_title)
            elif obj_type == "IonHeatmaps":
                heatmap_obj = values["image"]
                heatmap_obj.set_metadata(
                    {"label": item_info["label"], "colormap": item_info["colormap"], "color": item_info["color_255to1"]}
                )
                heatmap_obj = document.add_heatmap(name, heatmap_obj)
                self.document_tree.on_update_document(heatmap_obj.DOCUMENT_KEY, name, self.document_title)

    def on_right_click(self, evt):
        """Event on right-click"""
        # ensure that user clicked inside the plot area
        menu = wx.Menu()
        if hasattr(evt.EventObject, "figure"):

            # get plot
            plot_obj = self.get_plot_obj()

            menu_action_customise_plot = make_menu_item(
                parent=menu, text="Customise plot...", bitmap=self._icons.x_label
            )
            menu.AppendItem(menu_action_customise_plot)
            self.lock_plot_check = menu.AppendCheckItem(wx.ID_ANY, "Lock plot", help="")
            self.lock_plot_check.Check(plot_obj.figure.lock_plot_from_updating)
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(-1, "Resize on saving")
            self.resize_plot_check.Check(CONFIG.resize)
            save_figure_menu_item = make_menu_item(
                menu, evt_id=wx.ID_ANY, text="Save figure as...", bitmap=self._icons.save
            )
            menu.AppendItem(save_figure_menu_item)
            menu_action_copy_to_clipboard = make_menu_item(
                parent=menu, evt_id=wx.ID_ANY, text="Copy plot to clipboard", bitmap=self._icons.filelist
            )
            menu.AppendItem(menu_action_copy_to_clipboard)

            menu.AppendSeparator()
            reset_plot_menu_item = make_menu_item(menu, evt_id=wx.ID_ANY, text="Reset plot zoom")
            menu.AppendItem(reset_plot_menu_item)

            clear_plot_menu_item = make_menu_item(menu, evt_id=wx.ID_ANY, text="Clear plot", bitmap=self._icons.clear)
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

    def get_normalization_list(self):
        """Get list of normalizations for the currently selected document"""
        document = self.document
        normalizations_list = []
        if document is not None:
            normalizations_list = document.get_normalization_list()
        return normalizations_list

    def get_plot_obj(self):
        """Return current plot object"""
        plot_dict = {self.view_ms.NAME: self.view_ms, self.view_img.NAME: self.view_img}
        return plot_dict[self.view.plot_id]

    def on_clear_plot(self, _evt):
        """Clear plot"""
        plot_obj = self.get_plot_obj()
        plot_obj.figure.clear()

    def on_reset_plot(self, _evt):
        """Reset plot"""
        plot_obj = self.get_plot_obj()
        plot_obj.figure.on_reset_zoom()

    def on_resize_check(self, _evt):
        """Toggle resize check in the plot"""
        self.panel_plot.on_resize_check(None)

    def on_copy_to_clipboard(self, _evt):
        """Copy plot object to clipboard"""
        plot_obj = self.get_plot_obj()
        plot_obj.copy_to_clipboard()

    def on_customise_plot(self, _evt):
        """Customise plot parameters"""
        plot_obj = self.get_plot_obj()
        self.panel_plot.on_customise_plot(None, plot="Imaging: LESA...", plot_obj=plot_obj)

    def on_save_figure(self, _evt):
        """Save figure"""
        plot_obj = self.get_plot_obj()
        plot_obj.save_figure()

    def on_lock_plot(self, _evt):
        """Lock/unlock plot"""
        plot_obj = self.get_plot_obj()
        plot_obj.figure.lock_plot_from_updating = not plot_obj.figure.lock_plot_from_updating

    def on_populate_item(self, item_info):
        """Populate values in the gui"""
        self.item_name.SetLabel(item_info["ion_name"])
        self.label_value.SetValue(item_info["label"])
        self.colormap_value.SetStringSelection(item_info["colormap"])
        self.item_color_btn.SetBackgroundColour(item_info["color"])

    def on_change_color(self, evt):
        """Update color"""
        if self.peaklist.item_id is None:
            return

        color_255, _, _ = self.on_get_color(evt)
        if color_255 is None:
            return

        # update button
        self.item_color_btn.SetBackgroundColour(color_255)
        self.on_update_value_in_peaklist(self.peaklist.item_id, "color_text", color_255)

    def on_update_item(self, _evt):
        """Update info"""
        if self.item_loading_lock:
            return

        name = self.item_name.GetLabel()
        # get item index
        item_id = self.on_find_item("ion_name", name)

        self.on_update_value_in_peaklist(item_id, "label", self.label_value.GetValue())
        self.on_update_value_in_peaklist(item_id, "colormap", self.colormap_value.GetStringSelection())

    def on_extract_tic_image(self):
        """Load TIC image"""
        _, img_obj = self.data_handling.document_extract_lesa_image_from_ms(0, 99999, self.document_title)
        self.on_plot_image(img_obj)

    def on_extract_image_from_mobilogram(self, rect, x_labels, y_labels):  # noqa
        """Extract mobilogram for particular image"""
        y_min, y_max, _, _ = rect
        del rect, x_labels, y_labels

        item_info = self.on_get_item_information(None)
        x_min, x_max = self._get_mz_from_label(item_info["ion_name"])

        # pre-generate name in case data has been previously extracted
        name = f"MZ_{x_min:.2f}-{x_max:.2f}_DT_{int(y_min)}-{int(y_max)}"
        if name in self.clipboard:
            img_obj = self.clipboard[name]["image"]
        else:
            name, img_obj = self.data_handling.document_extract_lesa_image_from_dt(
                x_min, x_max, y_min, y_max, self.document_title
            )
            self.clipboard[name] = dict(image=img_obj, mobilogram=None)
        self.on_plot_image(img_obj)

    def on_extract_image_from_spectrum(self, rect, x_labels, y_labels):  # noqa
        """extract image from mass spectrum"""
        x_min, x_max, _, _ = rect
        del rect, x_labels, y_labels
        name = f"MZ_{x_min:.2f}-{x_max:.2f}"
        if name in self.clipboard:
            img_obj = self.clipboard[name]["image"]
        else:
            name, img_obj = self.data_handling.document_extract_lesa_image_from_ms(x_min, x_max, self.document_title)
            x_min, x_max = self._get_mz_from_label(name)
            self.view_ms.add_patch(x_min, 0, (x_max - x_min), None, pickable=False)

            self.on_add_to_table(
                dict(
                    ion_name=name,
                    color=next(CONFIG.custom_color_cycle),
                    colormap=next(CONFIG.overlay_cmap_cycle),
                    label=name,
                )
            )
            self.clipboard[name] = dict(image=img_obj, mobilogram=None)
        self.clipboard_last = name
        self.on_plot_image(img_obj)

    def on_extract_spectrum_from_image(self, rect, x_labels, y_labels):
        """Extract mass spectrum image"""
        raise MessageError("Error", "Data extraction in the image is currently disabled")

    #         x_min, x_max, y_min, y_max = rect
    #         self.view_img.add_patch(x_min, y_min, (x_max - x_min), (y_max - y_min))

    def on_update_normalization(self, _evt):
        """Update normalization in the plot"""
        from copy import deepcopy

        if self.clipboard_last is None:
            raise MessageError("Error", "Could not retrieve last ion image - try extracting data first")

        # get image
        img_obj = self.clipboard[self.clipboard_last]["image"]

        # get normalization object
        if self.normalization_choice.GetStringSelection() == "None":
            self.on_plot_image(img_obj)
        else:
            self.on_plot_image(deepcopy(img_obj))

    def on_plot_image(self, img_obj):
        """Plot image"""

        normalization = self.normalization_choice.GetStringSelection()
        if normalization != "None":
            normalizer = self.document.get_normalization(normalization)
            img_obj = normalizer(img_obj=img_obj)

        self.view_img.plot(obj=img_obj)

    def on_plot_spectrum(self, _evt):
        """Plot mass spectrum"""
        _, mz_obj = self.data_handling.get_spectrum_data(
            [self.document_title, self.spectrum_choice.GetStringSelection()]
        )
        self.view_ms.plot(obj=mz_obj)

    def on_plot_mobilogram(self, evt, dt_obj, title: str):
        """Plot mobilogram"""
        if not self.popup:
            self.popup = PopupMobilogramView(
                self, allow_extraction=True, callbacks=dict(CTRL="widget.imaging.lesa.extract.image.mobilogram")
            )
            self.popup.position_on_event(evt, 500, 0)
        self.popup.Show()
        self.popup.plot(dt_obj)
        self.popup.set_title(title)

    def on_select_document(self):
        """Select document"""
        if self._spectrum_list:
            self.spectrum_choice.SetItems(self._spectrum_list)
            self.spectrum_choice.SetStringSelection(self._spectrum_list[-1])
            self.on_extract_tic_image()
            self.on_plot_spectrum(None)

    def on_select_item(self, evt):
        """Select-event in the list"""
        # trigger the parent item to sync
        self.item_loading_lock = True

        self.peaklist.on_select_item(evt)
        item_info = self.on_get_item_information(None)
        self.on_populate_item(item_info)

        # already present
        if item_info["ion_name"] in self.clipboard:
            img_obj = self.clipboard[item_info["ion_name"]]["image"]
            self.on_plot_image(img_obj)

        self.item_loading_lock = False

    def on_double_click_on_item(self, evt):
        """Select item in list"""
        self.item_loading_lock = True
        item_info = self.on_get_item_information(None)

        # get dt data
        name = item_info["ion_name"]

        # check whether there is pre-computed mobilogram
        if self.clipboard[name]["mobilogram"] is not None:
            dt_obj = self.clipboard[name]["mobilogram"]
        else:
            mz_min, mz_max = self._get_mz_from_label(name)
            _, dt_obj = self.data_handling.document_extract_dt_from_msdt_multifile(mz_min, mz_max, self.document_title)
            self.clipboard[name].update(mobilogram=dt_obj)

        self.on_plot_mobilogram(evt, dt_obj, f"Item: {name}")
        self.item_loading_lock = False

    @staticmethod
    def _get_mz_from_label(label):
        """Extract m/z range from current item"""
        label = label.split("MZ_")[-1]
        mz_min, mz_max = map(float, label.split("-"))
        return mz_min, mz_max


def _main():

    app = wx.App()
    ex = PanelImagingLESAViewer(None, None, debug=True)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
