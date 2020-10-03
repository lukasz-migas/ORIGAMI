"""Base class for plot settings"""
# Standard library imports
import logging
from typing import Dict

# Third-party imports
import wx
import wx.lib.scrolledpanel
from pubsub import pub
from pubsub.core import TopicNameError

# Local imports
from origami.icons.assets import Colormaps
from origami.utils.system import running_under_pytest
from origami.gui_elements.mixins import ColorGetterMixin
from origami.gui_elements.mixins import ColorPaletteMixin
from origami.widgets.interactive.utilities import PUB_EVENT_CONFIG_UPDATE

LOGGER = logging.getLogger(__name__)


class PanelSettingsBase(wx.lib.scrolledpanel.ScrolledPanel, ColorGetterMixin, ColorPaletteMixin):
    """Base panel"""

    def __init__(self, parent, view):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent)
        self.view = view
        self._colormaps = Colormaps()
        self.import_evt = True

        self.make_panel()
        self.on_toggle_controls(evt=None)
        if not running_under_pytest():
            self.SetupScrolling()
        self.import_evt = False

        self.config_mixin_setup()

    def config_mixin_setup(self):
        """Setup mixin class"""
        pub.subscribe(self.on_set_config, PUB_EVENT_CONFIG_UPDATE)

    def config_mixin_teardown(self):
        """Teardown/cleanup mixin class"""
        try:
            pub.unsubscribe(self.on_set_config, PUB_EVENT_CONFIG_UPDATE)
        except TopicNameError:
            print("Failed to unsubscribe")

    @staticmethod
    def _parse_evt(evt):
        """Parse event"""
        if evt is not None:
            evt.Skip()

    @staticmethod
    def _preparse_evt(evt):
        """Pre-parse event"""
        source = None
        if hasattr(evt, "GetEventObject"):
            source = evt.GetEventObject()
            if hasattr(source, "GetName"):
                source = source.GetName()
        if source is None:
            source = ""
        return evt, source

    def make_panel(self):
        """Make UI"""

    def on_apply(self, evt):
        """Apply changes"""
        self._parse_evt(evt)

    @staticmethod
    def get_config() -> Dict:
        """Get configuration data"""
        return dict()

    def on_toggle_controls(self, evt):
        """Update controls"""
        self._parse_evt(evt)

    def _on_assign_color(self, evt):
        if self.import_evt:
            return None, None, None

        # get id and source
        source = evt.GetEventObject().GetName()

        # get color
        color_255, color_1, _ = self.on_get_color(None)
        if color_1 is None:
            return None, None, None

        return source, color_255, color_1

    def on_set_config(self, config):
        """Handle loading of new configuration file"""
        wx.CallAfter(self._on_set_config, config)

    def _on_set_config(self, config):
        """Update values from configuration file"""
