"""Class to keep track of all the views used throughout ORIGAMI"""
# Standard library imports
import logging

# Third-party imports
from pubsub import pub

# Local imports
from origami.gui_elements.views.view_base import ViewBase

LOGGER = logging.getLogger(__name__)


class ViewRegister:
    """Register"""

    def __init__(self):
        self._views = dict()
        self._active = None

        pub.subscribe(self.register, "view.register")
        pub.subscribe(self.unregister, "view.unregister")
        pub.subscribe(self.activate, "view.activate")

    @property
    def active(self):
        """Return currently active view"""
        return self._active

    @active.setter
    def active(self, value):
        self._active = value

    def register(self, view_id: str, view: ViewBase):
        """Register view to keep track of the view"""
        if view_id in self._views:
            LOGGER.warning(f"View `{view_id}` already in the register")
            return
        if not isinstance(view, ViewBase):
            raise ValueError("Incorrect view input. Value should be derived from `ViewBase`")
        if not isinstance(view_id, str):
            raise ValueError(f"Incorrect view_id input. Value should be a `str` and not `{type(view_id)}`")
        self._views[view_id] = view
        LOGGER.debug(f"Registered view `{view_id}`")

    def unregister(self, view_id: str):
        """Unregister view, perhaps because its deleted or the window is closed"""
        if view_id not in self._views:
            LOGGER.warning(f"View `{view_id}` is not in the register")
            return

        del self._views[view_id]
        if self.active == view_id:
            self.active = None
        LOGGER.debug(f"Unregistered view `{view_id}`")

    def activate(self, view_id: str):
        """Activate view"""
        if view_id not in self._views:
            LOGGER.warning(f"View `{view_id}` is not in the register")
            return
        if self.active == view_id:
            return
        self.active = view_id
        LOGGER.debug(f"Activated `{view_id}`")


VIEW_REG = ViewRegister()
