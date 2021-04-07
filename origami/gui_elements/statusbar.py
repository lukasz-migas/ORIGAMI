"""Main window statusbar"""
# Standard library imports
from typing import List

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.gui_elements.helpers import set_tooltip


class StatusbarField:
    def __init__(self, pos, size):
        self.pos = pos
        self.size = size


class StatusbarFields:
    """Statusbar field positions"""

    xy = StatusbarField(0, 250)
    mz_range = StatusbarField(1, 100)
    msms = StatusbarField(2, 150)
    action = StatusbarField(3, 150)
    status = StatusbarField(4, -1)
    queue = StatusbarField(5, 100)
    ram = StatusbarField(6, 50)
    cpu = StatusbarField(7, 50)

    def get_widths(self):
        return [
            getattr(self, field).size for field in ["xy", "mz_range", "msms", "action", "status", "queue", "ram", "cpu"]
        ]


class StatusbarTimerWidget(wx.Panel):
    """Timer"""

    INTERVAL = 2000
    TOOLTIP = ""
    label = None
    img = None
    value = 0

    def __init__(self, parent, icon=None):
        wx.Panel.__init__(self, parent)

        # setup UI
        if icon:
            self.img = wx.StaticBitmap(self, wx.ID_ANY, icon)
            set_tooltip(self.img, self.get_tooltip())
        self.label = wx.StaticText(self, wx.ID_ANY, "", style=wx.ALIGN_RIGHT)
        set_tooltip(self.label, self.get_tooltip())

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if self.img:
            sizer.Add(self.img)
        sizer.Add(self.label)
        sizer.Fit(self)
        self.SetSizer(sizer)
        self.Layout()

        self._timer = wx.Timer(self, True)
        self.Bind(wx.EVT_TIMER, self.update_status, self._timer)
        self._timer.Start(self.INTERVAL)

    def get_value(self):
        """Return value"""
        return ""

    def get_tooltip(self):
        """Return tooltip"""
        return self.TOOLTIP

    def set_interval(self, interval: int):
        """Update interval"""
        if not isinstance(interval, int):
            raise ValueError("Timer interval must be an integer")
        self.INTERVAL = interval

        # the  timer will only be restarted if its already running
        if self._timer.IsRunning():
            self._timer.Stop()
            self._timer.Start(self.INTERVAL)

    def update_status(self, _evt):
        """Update status label widget, if widget is visible."""
        if self.IsShown():
            self.label.SetLabel(self.get_value())

    def set_value(self, value):
        """Set value and update marker immediately"""
        self.value = value
        self.update_status(None)


class MemoryStatusWidget(StatusbarTimerWidget):
    """RAM widget"""

    TOOLTIP = "Memory usage"

    def __init__(self, parent, icon):
        super().__init__(parent, icon)

    def get_value(self):
        """Return value"""

        from origami.utils.system import memory_usage

        text = "%d%%" % memory_usage()
        return " " + text.rjust(3)


class CPUStatusWidget(StatusbarTimerWidget):
    """RAM widget"""

    TOOLTIP = "CPU usage"

    def __init__(self, parent, icon):
        super().__init__(parent, icon)

    def get_value(self):
        """Return value"""

        import psutil

        value = psutil.cpu_percent(interval=0)
        text = "%d%%" % value
        return " " + text.rjust(3)


class QueueStatusWidget(StatusbarTimerWidget):
    """RAM widget"""

    TOOLTIP = "Number of elements in the queue"

    def __init__(self, parent, icon):
        super().__init__(parent, icon)

    def get_value(self):
        """Return value"""
        text = " %d item" % self.value
        if self.value != 0:
            text += "s"
        return text


class Statusbar(wx.StatusBar):
    """Custom statusbar with additional widgets"""

    _size_changed = False
    _clean_field = None
    STATUSBAR_FIELDS = StatusbarFields()

    def __init__(self, parent, icons):
        """The statusbar should be composed of several components

        1. x/y position of the mouse in the plot area
        2. m/z range for particular dataset that is currently selected
        3. the MSMS mass
        4. action
        5. status message
        6. RAM usage
        7. CPU usage
        8. queue size - flat button
        """
        wx.StatusBar.__init__(self, parent, -1)
        self.parent = parent
        self._icons = icons

        # set field count
        self.SetFieldsCount(8)
        self.SetStatusWidths(self.STATUSBAR_FIELDS.get_widths())

        # setup font
        self.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        # set widgets
        self.mem_widget = MemoryStatusWidget(self, self._icons.ram)
        self.cpu_widget = CPUStatusWidget(self, self._icons.cpu)
        self.queue_widget = QueueStatusWidget(self, self._icons.tasks)
        self.fix_widgets()

        # setup timer to enable sporadic cleanup of messages
        self._timer = wx.Timer(self, True)
        self.Bind(wx.EVT_TIMER, self.on_cleanup, self._timer)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_IDLE, self.on_idle)

        # Setup listeners
        pub.subscribe(self.on_motion, "motion_xy")
        pub.subscribe(self.motion_range, "motion_range")
        pub.subscribe(self.on_distance, "change_x_axis_start")
        pub.subscribe(self.on_event_mode, "motion_mode")
        pub.subscribe(self.on_queue_change, "statusbar.update.queue")

    def set_message(self, message: str, field: int, delay: int = 3000):
        """Set message in the statusbar"""
        self._clean_field = field
        self.SetStatusText(message, field)

        # set timer
        if not isinstance(delay, int):
            return
        self._timer.StartOnce(delay)

    def on_cleanup(self, _evt):
        """Cleanup event of the last message"""
        if not isinstance(self._clean_field, int):
            return
        self.SetStatusText("", self._clean_field)
        self._clean_field = None

    def on_size(self, evt):
        """Trigger on-size event"""
        evt.Skip()
        self.fix_widgets()  # for normal size events

        # Set a flag so the idle time handler will also do the repositioning.
        # It is done this way to get around a bug where GetFieldRect is not
        # accurate during the EVT_SIZE resulting from a frame maximize.
        self._size_changed = True

    def on_idle(self, _evt):
        """Fix widget position when application is idle"""
        if self._size_changed:
            self.fix_widgets()

    def fix_widgets(self):
        """Fix widget positions"""

        def _fix_widget(widget, field):
            rect = self.GetFieldRect(field)
            rect.x += 1
            rect.y += 1
            widget.SetRect(rect)

        _fix_widget(self.mem_widget, self.STATUSBAR_FIELDS.ram.pos)
        _fix_widget(self.cpu_widget, self.STATUSBAR_FIELDS.cpu.pos)
        _fix_widget(self.queue_widget, self.STATUSBAR_FIELDS.queue.pos)
        self._size_changed = False

    def update_interval(self, interval: int):
        """Update frequency of updates in the statusbar"""
        for widget in [self.mem_widget, self.cpu_widget, self.queue_widget]:
            widget.set_interval(interval)

    def on_distance(self, xy_start: List[float]):
        """Update the start position of when event has started

        Parameters
        ----------
        xy_start : List[float]
            starting position in the x- and y-dimension
        """
        self.parent.xy_start = xy_start

    def on_queue_change(self, value: int):
        """Update size of the queue

        Parameters
        ----------
        value : int
            length of the queue
        """
        self.queue_widget.set_value(value)

    def on_event_mode(self, plot_interaction):
        """Changed cursor based on which key is pressed"""
        shift, ctrl, alt, add_to_table, wheel, zoom, dragged = plot_interaction
        cursor = wx.Cursor(wx.CURSOR_ARROW)

        mode = ""
        if alt:
            mode = "Measure"
            cursor = wx.Cursor(wx.CURSOR_MAGNIFIER)
        elif ctrl:
            mode = "Extract"
            cursor = wx.Cursor(wx.CURSOR_CROSS)
        elif add_to_table:
            mode = "Extract"
            cursor = wx.Cursor(wx.CURSOR_CROSS)
        elif dragged is not None:
            mode = "Drag"
            cursor = wx.Cursor(wx.CURSOR_HAND)
        elif zoom:
            mode = "Zoom"
            cursor = wx.Cursor(wx.CURSOR_MAGNIFIER)

        self.parent.mode = mode
        self.parent.SetCursor(cursor)
        self.SetStatusText(mode, self.STATUSBAR_FIELDS.action)

    def on_motion(self, x_pos: float, y_pos: float, plot_name: str, plot_id: str):
        """Updates the x/y values shown in the window based on where in the plot area the mouse is found

        Parameters
        ----------
        x_pos : float
            x-axis position of the mouse in the plot area
        y_pos : float
            y-axis position of the mouse in the plot area
        plot_name : str
            plot name
        plot_id : str
            unique id for particular plotting window
        """

        self.parent.plot_name = plot_name
        self.parent.plot_id = plot_id

        if x_pos is None or y_pos is None:
            msg = ""
        else:
            msg = "x={:.4f} y={:.4f}".format(x_pos, y_pos)
        self.SetStatusText(msg, self.STATUSBAR_FIELDS.xy)

    def motion_range(self, xmin, xmax, ymin, ymax):
        """Change motion information"""
        msg = ""
        if self.parent.mode == "Add data":
            msg = f"X={xmin:.3f}:{xmax:.3f} | Y={ymin:.3f}:{ymax:.3f}"
        self.SetStatusText(msg, self.STATUSBAR_FIELDS.status)


class TestCustomStatusBar(wx.Frame):
    """Test statusbar"""

    def __init__(self, parent, icons):
        wx.Frame.__init__(self, parent, -1, "Test Custom StatusBar")

        self.sb = Statusbar(self, icons)
        self.SetStatusBar(self.sb)
        _ = wx.TextCtrl(self, -1, "", style=wx.TE_READONLY | wx.TE_MULTILINE)

        self.SetSize((1920, 1080))


def _main():

    from origami.app import App
    from origami.icons.assets import Icons

    app = App()

    icons = Icons()
    ex = TestCustomStatusBar(None, icons)
    ex.Show()
    app.MainLoop()


if __name__ == "__main__":  # pragma: no cover
    _main()
