"""Various mixin classes used by the GUI elements"""
# Standard library imports
import logging

# Third-party imports
import wx
from pubsub import pub
from wx.adv import BitmapComboBox
from pubsub.core import TopicNameError

# Local imports
from origami.config.config import CONFIG
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_bitmap_btn
from origami.gui_elements.misc_dialogs import DialogBox
from origami.gui_elements.dialog_color_picker import DialogColorPicker

LOGGER = logging.getLogger(__name__)


class DocumentationMixin:
    """HTML documentation mixin"""

    # documentation attributes
    HELP_MD = None
    HELP_LINK = None
    PANEL_STATUSBAR_COLOR = wx.BLUE

    # attributes
    _icons = None

    # ui elements
    info_btn = None
    settings_btn = None
    display_label = None

    def on_open_info(self, _evt):
        """Open help window to inform user on how to use this window / panel"""
        from origami.gui_elements.panel_html_viewer import PanelHTMLViewer

        if self.HELP_LINK:
            PanelHTMLViewer(self, link=self.HELP_LINK)
        elif self.HELP_MD:
            PanelHTMLViewer(self, md_msg=self.HELP_MD)

    def on_open_popup_settings(self, evt):
        """Open settings popup window"""

    def make_info_button(self, panel):
        """Make clickable information button"""
        if self._icons is None:
            icon = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_BUTTON, wx.Size(16, 16))
        else:
            icon = self._icons.info
        info_btn = make_bitmap_btn(panel, wx.ID_ANY, icon, style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        set_tooltip(info_btn, "Open documentation page about this panel (online)")
        info_btn.Bind(wx.EVT_BUTTON, self.on_open_info)
        return info_btn

    def make_settings_button(self, panel):
        """Make clickable information button"""
        settings_btn = make_bitmap_btn(
            panel, wx.ID_ANY, self._icons.gear, style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        set_tooltip(settings_btn, "Open popup window with settings specific to this panel")
        settings_btn.Bind(wx.EVT_BUTTON, self.on_open_popup_settings)
        return settings_btn

    def make_statusbar(self, panel, position: str = "left"):
        """Make make-shift statusbar"""
        # add info button
        self.info_btn = self.make_info_button(panel)

        self.display_label = wx.StaticText(panel, wx.ID_ANY, "")
        self.display_label.SetForegroundColour(self.PANEL_STATUSBAR_COLOR)

        sizer = wx.BoxSizer()
        if position == "left":
            sizer.Add(self.info_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
            sizer.Add(self.display_label, 1, wx.ALIGN_CENTER_VERTICAL)
        else:
            sizer.Add(self.display_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
            sizer.Add(self.info_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        return sizer

    def set_message(self, msg: str, duration: int = 5000):
        """Set message for a period of time

        Parameters
        ----------
        msg : str
            message to be displayed in the statusbar
        duration : int
            how long the message should be displayed for
        """
        self.display_label.SetLabel(msg)
        if duration > 0:
            wx.CallLater(duration, self.display_label.SetLabel, "")


class ColorPaletteMixin:
    """Mixin class to provide easy setup of color palette combobox"""

    _colormaps = None

    def _set_color_palette(self, widget):
        if not isinstance(widget, BitmapComboBox):
            raise ValueError("Expected `BitmapComboBox` type of widget")
        if self._colormaps is None:
            raise ValueError("Please load colormaps first")
        # add choices
        widget.Append("HLS", bitmap=self._colormaps.cmap_hls)
        widget.Append("HUSL", bitmap=self._colormaps.cmap_husl)
        widget.Append("Cubehelix", bitmap=self._colormaps.cmap_cubehelix)
        widget.Append("Spectral", bitmap=self._colormaps.cmap_spectral)
        widget.Append("Viridis", bitmap=self._colormaps.cmap_viridis)
        widget.Append("Rainbow", bitmap=self._colormaps.cmap_rainbow)
        widget.Append("Inferno", bitmap=self._colormaps.cmap_inferno)
        widget.Append("Cividis", bitmap=self._colormaps.cmap_cividis)
        widget.Append("Winter", bitmap=self._colormaps.cmap_winter)
        widget.Append("Cool", bitmap=self._colormaps.cmap_cool)
        widget.Append("Gray", bitmap=self._colormaps.cmap_gray)
        widget.Append("RdPu", bitmap=self._colormaps.cmap_rdpu)
        widget.Append("Tab20b", bitmap=self._colormaps.cmap_tab20b)
        widget.Append("Tab20c", bitmap=self._colormaps.cmap_tab20c)


class ColorGetterMixin:
    """Mixin class to provide easy retrieval of color(s)"""

    def on_get_color(self, _evt):
        """Convenient method to get new color"""
        dlg = DialogColorPicker(self, CONFIG.custom_colors)
        if dlg.ShowModal() == wx.ID_OK:
            color_255, color_1, font_color = dlg.GetChosenColour()
            CONFIG.custom_colors = dlg.GetCustomColours()

            return color_255, color_1, font_color
        return None, None, None


class ActivityIndicatorMixin:
    """Activity indicator mixin"""

    # ui elements
    activity_indicator = None

    def on_progress(self, is_running: bool, message: str):  # noqa
        """Handle extraction progress"""
        if self.activity_indicator is None:
            LOGGER.warning("Cannot indicate activity - it has not been instantiated in the window")
            return

        # show indicator
        if is_running:
            self.activity_indicator.Show()
            self.activity_indicator.Start()
        else:
            self.activity_indicator.Hide()
            self.activity_indicator.Stop()
        self.Update()  # noqa


class DatasetMixin:
    """Mixin class that detects whether to close the window"""

    PUB_DELETE_ITEM_EVENT = "document.delete.item"
    PUB_RENAME_ITEM_EVENT = "document.rename.item"
    DELETE_ITEM_MSG = "Data object that is shown in this window has been deleted, therefore, this window will close too"
    PANEL_BASE_TITLE = ""
    document_title = None
    dataset_name = None

    def _dataset_mixin_setup(self):
        """Setup mixin class"""
        pub.subscribe(self._evt_delete_item, self.PUB_DELETE_ITEM_EVENT)
        pub.subscribe(self._evt_rename_item, self.PUB_RENAME_ITEM_EVENT)

    def _dataset_mixin_teardown(self):
        """Teardown/cleanup mixin class"""
        try:
            pub.unsubscribe(self._evt_delete_item, self.PUB_DELETE_ITEM_EVENT)
            pub.unsubscribe(self._evt_rename_item, self.PUB_RENAME_ITEM_EVENT)
        except TopicNameError:
            pass

    def _evt_rename_item(self, info):
        """Triggered when document or dataset is renamed"""
        if not isinstance(info, (tuple, list)) and len(info) == 3:
            return

        if self._evt_rename_check(info):
            self.document_title = info[0]
            self.dataset_name = info[2]
            self.update_window_title()
            LOGGER.info("Panel dataset information updated!")

    def _evt_rename_check(self, info):
        """Function to check whether window should be closed - can be overwritten to do another kind of check"""
        document_title, dataset_name, _ = info

        if document_title == self.document_title:
            if dataset_name is not None:
                if not self.dataset_name.startswith(dataset_name) and dataset_name != self.dataset_name:
                    return False
            return True
        return False

    def _evt_delete_item(self, info):
        """Triggered when document or dataset is deleted"""

        if self._evt_delete_check(info):
            DialogBox(title="Dataset was deleted.", msg=self.DELETE_ITEM_MSG)
            self.on_close(None, True)

    def _evt_delete_check(self, info):
        """Function to check whether window should be closed - can be overwritten to do another kind of check"""
        document_title, dataset_name = info

        if document_title == self.document_title:
            if dataset_name is not None:
                if not self.dataset_name.startswith(dataset_name) and dataset_name != self.dataset_name:
                    return False
            return True
        return False

    def on_close(self, evt, force: bool = False):
        """On-close event handler"""
        raise NotImplementedError("Must implement method")

    def update_window_title(self):
        """Update title"""
        title = f"{self.PANEL_BASE_TITLE}: {self.document_title}"
        if self.dataset_name is not None:
            title += f" :: {self.dataset_name}"
        self.SetTitle(title)  # noqa


class ConfigUpdateMixin:
    """Mixin class to automatically handle loaded configuration file(s)"""

    PUB_CONFIG_LOAD_EVENT = "config.loaded"
    import_evt = False

    def _config_mixin_setup(self):
        """Setup mixin class"""
        pub.subscribe(self.on_set_config, self.PUB_CONFIG_LOAD_EVENT)

    def _config_mixin_teardown(self):
        """Teardown/cleanup mixin class"""
        try:
            pub.unsubscribe(self.on_set_config, self.PUB_CONFIG_LOAD_EVENT)
        except TopicNameError:
            pass

    def on_set_config(self):
        """Handle loading of new configuration file"""
        wx.CallAfter(self._on_set_config)

    def _on_set_config(self):
        """Update values from configuration file"""
