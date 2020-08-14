"""Base class for plot settings"""
# Third-party imports
import wx
import wx.lib.scrolledpanel

# Local imports
from origami.icons.assets import Colormaps
from origami.gui_elements.mixins import ColorGetterMixin
from origami.gui_elements.mixins import ColorPaletteMixin
from origami.gui_elements.mixins import ConfigUpdateMixin


class PanelSettingsBase(wx.lib.scrolledpanel.ScrolledPanel, ColorGetterMixin, ConfigUpdateMixin, ColorPaletteMixin):
    """Base panel"""

    def __init__(self, parent, view):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent)
        self.view = view
        self._colormaps = Colormaps()
        self.import_evt = True

        self.make_panel()
        self._on_set_config()
        self.on_toggle_controls(evt=None)
        self.SetupScrolling()
        self.import_evt = False

        self._config_mixin_setup()

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

    @property
    def panel_plot(self):
        """Return handle to `panel_plot`"""
        return self.view.panelPlots

    def make_panel(self):
        """Make UI"""

    def on_update(self, evt):
        """Update plot data"""
        self._parse_evt(evt)

    def on_apply(self, evt):
        """Apply changes"""
        self._parse_evt(evt)

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
