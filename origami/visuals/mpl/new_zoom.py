# Standard library imports
import logging

# Third-party imports
import wx
import numpy as np
from pubsub import pub
from matplotlib.text import Text
from matplotlib.patches import Rectangle

LOGGER = logging.getLogger(__name__)


def get_axes_limits(axes, xmin=None, xmax=None):
    yvals = []
    xvals = []
    for line in axes.lines:
        ydat = line.get_ydata()
        xdat = line.get_xdata()
        if xmin is not None and xmax is not None:
            bool1 = np.all(np.array([xdat > xmin, xdat < xmax]), axis=0)
            ydat = ydat[bool1]
            line.set_clip_on(True)

        try:
            yvals.append([np.amin(ydat), np.amax(ydat)])
            xvals.append([np.amin(xdat), np.amax(xdat)])
        except Exception as err:
            LOGGER.error(err)

    for p in axes.collections:
        try:
            xys = np.array(p.get_paths()[0].vertices)
        except IndexError:
            break
        offsets = p.get_offsets()
        if len(offsets) > 1:
            xys = np.array(offsets)

        xdat, ydat = on_check_x_values(xys, xmin, xmax)
        try:
            yvals.append([np.amin(ydat), np.amax(ydat)])
            xvals.append([np.amin(xdat), np.amax(xdat)])
        except Exception as err:
            LOGGER.error(err)

    for patch in axes.patches:
        try:
            if (patch.get_width()) and (patch.get_height()):
                vertices = patch.get_path().vertices
                if vertices.size > 0:
                    xys = np.array(patch.get_patch_transform().transform(vertices))
                    xdat, ydat = on_check_x_values(xys, xmin, xmax)
                    try:
                        yvals.append([np.amin(ydat), np.amax(ydat)])
                        xvals.append([np.amin(xdat), np.amax(xdat)])
                    except Exception as err:
                        LOGGER.error(err)
        except Exception as err:
            try:
                xys = patch.xy
                xdat, ydat = on_check_x_values(xys, xmin, xmax)

                yvals.append([np.amin(ydat), np.amax(ydat)])
                xvals.append([np.amin(xdat), np.amax(xdat)])
            except Exception as err:
                LOGGER.error(err)

    for t in axes.texts:
        x, y = t.get_position()
        y = y * 1.01
        if xmin is not None and xmax is not None:
            if x < xmax and x > xmin:
                t.set_visible(True)
                yvals.append([y, y])
                xvals.append([x, x])
            else:
                t.set_visible(False)
        else:
            yvals.append([y, y])
            xvals.append([x, x])

    if len(yvals) != 0 and len(xvals) != 0:
        ymin = np.amin(np.ravel(yvals))
        ymax = np.amax(np.ravel(yvals))
        if xmin is None or xmax is None:
            xmin = np.amin(np.ravel(xvals))
            xmax = np.amax(np.ravel(xvals))

        if xmin > xmax:
            xmin, xmax = xmax, xmin
        if ymin > ymax:
            ymin, ymax = ymax, ymin
        if xmin == xmax:
            xmax = xmin * 1.0001
        if ymin == ymax:
            ymax = ymin * 1.0001

        out = [xmin, ymin, xmax, ymax]
    else:
        out = axes.dataLim.bounds
    return out


def on_check_x_values(xys, xmin, xmax):
    ydat = xys[:, 1]
    xdat = xys[:, 0]
    if xmin is not None and xmax is not None:
        bool1 = np.all(np.array([xdat > xmin, xdat < xmax]), axis=0)
        ydat = ydat[bool1]

    return xdat, ydat


def reset_visible(axes):
    for line in axes.lines:
        line.set_clip_on(True)
    for t in axes.texts:
        t.set_visible(True)


def get_axes_start(axes):
    outputs = np.array([get_axes_limits(axis) for axis in axes])
    xmin = np.amin(outputs[:, 0])
    ymin = np.amin(outputs[:, 1])
    xmax = np.amax(outputs[:, 2])
    ymax = np.amax(outputs[:, 3])

    if xmin > xmax:
        xmin, xmax = xmax, xmin
    if ymin > ymax:
        ymin, ymax = ymax, ymin
    if xmin == xmax:
        xmax = xmin * 1.0001
    if ymin == ymax:
        ymax = ymin * 1.0001

    out = [xmin, ymin, xmax, ymax]

    return out


class GetXValues:
    def __init__(self, axes):
        """
        This function retrieves the x-axis info
        """
        self.axes = None
        self.canvas = None
        self.cids = []

        self.create_new_patch(axes)

    def create_new_patch(self, axes):
        self.axes = axes
        if self.canvas is not axes[0].figure.canvas:
            for cid in self.cids:
                self.canvas.mpl_disconnect(cid)
                print("disconnected")
            self.canvas = axes[0].figure.canvas


class MPLInteraction:
    """
    Main class to enable zoom in 1D, 2D and 3D plots
    """

    def __init__(
        self,
        axes,
        useblit=False,
        patch_kwargs=None,
        button=1,
        data_limits=None,
        plotName=None,
        plot_parameters=None,
        allow_wheel=True,
        allow_extraction=True,
        callbacks=None,
    ):
        if callbacks is None:
            callbacks = dict()

        self.axes = None
        self.canvas = None
        self.visible = True
        self.cids = []
        self.plotName = plotName
        self.allow_extraction = allow_extraction

        self.active = True  # for activation / deactivation
        self.to_draw = []
        self.background = None
        self.dragged = None
        self.span = None

        self._is_inside_axes = True
        self._last_location = None
        self._last_xy_position = []
        self.current_ymax = None

        self.mark_annotation = False
        self.prevent_sync_zoom = False

        # setup some parameters
        self.plot_parameters = {} if plot_parameters is None else plot_parameters
        self.crossover_percent = self.plot_parameters["zoom_crossover_sensitivity"]
        self.show_cursor_cross = self.plot_parameters["grid_show"]
        self.allow_wheel = allow_wheel
        self.n_mouse_wheel_steps = 3

        self.useblit = useblit
        self._xy_press = []
        self.eventpress = None
        self.eventrelease = None

        if button is None or isinstance(button, list):
            self.validButtons = button
        elif isinstance(button, int):
            self.validButtons = [button]

        self._trigger_extraction = False
        self.pick_pos = None
        self._ctrl_key = False
        self._alt_key = False
        self._shift_key = False
        self._button_down = False
        self._key_press = False
        self._mouse_wheel = False
        self._callbacks = callbacks

        # based on MPL
        self.wxoverlay = None
        self.retinaFix = "wxMac" in wx.PlatformInfo
        self.savedRetinaImage = None
        self.zoomStartX = None
        self.zoomStartY = None
        self.zoomAxes = None
        self.prevZoomRect = None

        self.create_new_patch(axes, patch_kwargs)

        try:
            if data_limits is None:
                self.data_limits = get_axes_start(self.axes)
            else:
                self.data_limits = data_limits
            xmin, ymin, xmax, ymax = self.data_limits
            if xmin > xmax:
                xmin, xmax = xmax, xmin
            if ymin > ymax:
                ymin, ymax = ymax, ymin
            # assure that x and y values are not equal
            if xmin == xmax:
                xmax = xmin * 1.0001
            if ymin == ymax:
                ymax = ymin * 1.0001
            for axes in self.axes:
                axes.set_xlim(xmin, xmax)
                axes.set_ylim(ymin, ymax)
        except Exception:
            for i in range(len(self.axes)):
                self.axes[i].data_limits = data_limits[i]
            self.prevent_sync_zoom = True
            self.data_limits = None

        # listener to change plot parameters
        pub.subscribe(self.on_update_parameters, "plot_parameters")

    def on_update_parameters(self, plot_parameters):
        self.plot_parameters = plot_parameters

        self.show_cursor_cross = self.plot_parameters["grid_show"]
        self.crossover_percent = self.plot_parameters["zoom_crossover_sensitivity"]

    def update_extents(self, data_limits=None):
        """Update plot extents"""
        self.data_limits = data_limits if data_limits is not None else get_axes_start(self.axes)

    def update_x_extents(self, x_min, x_max):
        """Update x-axis extents"""
        self.data_limits[0] = x_min
        self.data_limits[2] = x_max

    def update_y_extents(self, y_min, y_max):
        """Update y-axis extents"""
        self.data_limits[1] = y_min
        self.data_limits[3] = y_max

    def update_mark_state(self, state):
        """Update the state of annotation"""
        self.mark_annotation = state

    def on_pick_event(self, event):
        """Store which text object was picked and were the pick event occurs."""

        if isinstance(event.artist, Text):
            self.dragged = event.artist
            self.pick_pos = (event.mouseevent.xdata, event.mouseevent.ydata)

        return True

    def create_new_patch(self, axes, patch_kwargs=None):
        self.axes = axes
        if self.canvas is not axes[0].figure.canvas:
            for cid in self.cids:
                self.canvas.mpl_disconnect(cid)
            self.canvas = axes[0].figure.canvas

            # pick events
            self.cids.append(self.canvas.mpl_connect("pick_event", self.on_pick_event))

            # button events
            self.cids.append(self.canvas.mpl_connect("button_press_event", self.on_press))
            self.cids.append(self.canvas.mpl_connect("button_release_event", self.on_release))
            self.cids.append(self.canvas.mpl_connect("key_press_event", self.on_key_state))
            self.cids.append(self.canvas.mpl_connect("key_release_event", self.on_key_state))

            # motion events
            self.cids.append(self.canvas.mpl_connect("motion_notify_event", self.on_key_state))
            self.cids.append(self.canvas.mpl_connect("motion_notify_event", self.on_motion))

            # enter events
            self.cids.append(self.canvas.mpl_connect("axes_enter_event", self.on_enter_axes))
            self.cids.append(self.canvas.mpl_connect("axes_leave_event", self.on_leave_axes))

            # scroll events
            self.cids.append(self.canvas.mpl_connect("scroll_event", self.on_mouse_wheel))

            # draw events
            self.cids.append(self.canvas.mpl_connect("draw_event", self.update_background))

        if patch_kwargs is None:
            patch_kwargs = dict(facecolor="white", edgecolor="black", alpha=0.5, fill=False)
        self.patch_kwargs = patch_kwargs

        # Pre-set keys
        self._shift_key = False
        self._ctrl_key = False
        self._alt_key = False
        self._mouse_wheel = False
        self._key_press = False
        self._trigger_extraction = False
        self._button_down = False

        for _ in self.axes:
            self.to_draw.append(Rectangle((0, 0), 0, 1, visible=False, **self.patch_kwargs))

        self.show_cursor_cross = self.plot_parameters["grid_show"]

        for axes, to_draw in zip(self.axes, self.to_draw):
            axes.add_patch(to_draw)

    def on_enter_axes(self, evt=None):
        self._last_location = [evt.xdata, evt.ydata]
        self._is_inside_axes = True

    def on_leave_axes(self, evt=None):
        self._is_inside_axes = False

    @staticmethod
    def get_axes_limits(axes):
        x0, x1 = axes.get_xlim()
        y0, y1 = axes.get_ylim()

        return x0, x1, y0, y1

    def on_mouse_wheel(self, evt):
        """Event on mouse-wheel"""
        if wx.GetKeyState(wx.WXK_ALT) or not self._is_inside_axes:
            return

        if not self.allow_wheel:
            return

        # Update cursor
        motion_mode = [
            self._shift_key,
            self._ctrl_key,
            self._alt_key,
            self._trigger_extraction,
            True,
            self._button_down,
            self.dragged,
        ]
        pub.sendMessage("motion_mode", dataOut=motion_mode)

        # The actual work
        for axes in self.axes:
            x0, x1, y0, y1 = self.get_axes_limits(axes)

            shift_key = wx.GetKeyState(wx.WXK_SHIFT)

            if self.data_limits is not None:
                xmin, ymin, xmax, ymax = self.data_limits
            else:
                xmin, ymin, xmax, ymax = axes.data_limits

            # Zoom in X-axis only
            if not shift_key:
                # calculate difference
                try:
                    x0_diff, x1_diff = evt.xdata - x0, x1 - evt.xdata
                    x_sum = x0_diff + x1_diff
                except Exception:
                    return
                stepSize = evt.step * ((x1 - x0) / 50)
                newXmin = x0 - (stepSize * (x0_diff / x_sum))
                newXmax = x1 + (stepSize * (x1_diff / x_sum))
                # Check if the X-values are off the data lims
                if newXmin < xmin:
                    newXmin = xmin
                if newXmax > xmax:
                    newXmax = xmax
                axes.set_xlim((newXmin, newXmax))
                if self.plotName == "MSDT":
                    pub.sendMessage("change_zoom_dtms", xmin=newXmin, xmax=newXmax, ymin=ymin, ymax=ymax)

            # Zoom in Y-axis only
            elif shift_key:
                # Check if its 1D plot
                if self.plotName in ["1D", "CalibrationDT", "MS"]:
                    stepSize = evt.step * ((y1 - y0) / 25)
                    axes.set_ylim((0, y1 + stepSize))
                elif self.plotName == "MSDT":
                    try:
                        y0_diff, y1_diff = evt.ydata - y0, y1 - evt.ydata
                        y_sum = y0_diff + y1_diff
                    except Exception:
                        return

                    stepSize = evt.step * ((y1 - y0) / 50)
                    newYmin = y0 - (stepSize * (y0_diff / y_sum))
                    newYmax = y1 + (stepSize * (y1_diff / y_sum))
                    # Check if the Y-values are off the data lims
                    if newYmin < ymin:
                        newYmin = ymin
                    if newYmax > ymax:
                        newYmax = ymax
                    axes.set_ylim((newYmin, newYmax))
                elif self.plotName != "1D":
                    try:
                        y0_diff, y1_diff = evt.xdata - y0, y1 - evt.xdata
                        y_sum = y0_diff + y1_diff
                    except Exception:
                        return

                    stepSize = evt.step * ((y1 - y0) / 50)
                    newYmin = y0 - (stepSize * (y0_diff / y_sum))
                    newYmax = y1 + (stepSize * (y1_diff / y_sum))
                    # Check if the Y-values are off the data lims
                    if newYmin < ymin:
                        newYmin = ymin
                    if newYmax > ymax:
                        newYmax = ymax
                    axes.set_ylim((newYmin, newYmax))

            self.canvas.draw()

    def on_key_state(self, evt):
        """Update state of the key"""
        self._ctrl_key = wx.GetKeyState(wx.WXK_CONTROL)
        self._alt_key = wx.GetKeyState(wx.WXK_ALT)
        self._shift_key = wx.GetKeyState(wx.WXK_SHIFT)
        self._trigger_extraction = False
        self.crossover_percent = self.plot_parameters["zoom_crossover_sensitivity"]

        if self._ctrl_key:
            if self.plotName in ["1D", "MS"]:
                self.crossover_percent = self.plot_parameters["extract_crossover_sensitivity_1D"]
            else:
                self.crossover_percent = self.plot_parameters["extract_crossover_sensitivity_2D"]

        self._key_press = False
        if any((self._ctrl_key, self._shift_key, self._alt_key)):
            self._key_press = True

        motion_mode = [
            self._shift_key,
            self._ctrl_key,
            self._alt_key,
            self._trigger_extraction,
            self._mouse_wheel,
            self._button_down,
            self.dragged,
        ]
        pub.sendMessage("motion_mode", dataOut=motion_mode)

    def update_background(self, evt):
        "force an update of the background"
        if self.useblit:
            self.background = self.canvas.copy_from_bbox(self.canvas.figure.bbox)

    def ignore(self, evt):
        """Check whether an event should be ignored"""

        # If ZoomBox is not active :
        if not self.active:
            return True

        # If canvas was locked
        if not self.canvas.widgetlock.available(self):
            return True

        if self.validButtons is not None:
            if evt.button in self.validButtons and not self._key_press:
                pass
            elif evt.button in self.validButtons and self._ctrl_key:
                self._trigger_extraction = True
            else:
                if evt.button == 3:
                    return True
                elif evt.button == 2 and self.eventrelease is None:
                    return True
                else:
                    return False

        # If no button pressed yet or if it was out of the axes, ignore
        if self.eventpress is None:
            return evt.inaxes not in self.axes

        # If a button pressed, check if the on_release-button is the same
        return evt.inaxes not in self.axes or evt.button != self.eventpress.button

    def on_press(self, evt):
        """Event on button press"""

        self.eventpress = evt
        # Is the correct button pressed within the correct axes?
        if self.ignore(evt):
            return

        x, y = evt.x, evt.y

        # keep track of where the user clicked first
        self._xy_press = []
        for a in self.canvas.figure.get_axes():
            if x is not None and y is not None and a.in_axes(evt) and a.get_navigate() and a.can_zoom():
                self._xy_press.append((x, y, a))

        xy_start = [evt.xdata, evt.ydata]

        # set rect for displaying the zoom
        if not self.retinaFix:
            self.wxoverlay = wx.Overlay()
        else:
            if evt.inaxes is not None:
                self.savedRetinaImage = self.canvas.copy_from_bbox(evt.inaxes.bbox)
                self.zoomAxes = evt.inaxes

        # check whether it was a double click
        if not self._is_inside_axes:
            # completely unzoom
            if evt.dblclick and not self._shift_key:
                self.reset_axes(axis_pos=self._last_location)
            # unzum along one of the axes
            elif evt.dblclick and self._shift_key and self._last_location in ["left", "right"]:
                if self.current_ymax is None:
                    return
                for axes in self.axes:
                    axes.set_ylim(0, self.current_ymax)
                self.canvas.draw()
                return

        # dragging annotation
        if self.dragged is not None:
            pass

        self._button_down = True
        pub.sendMessage("change_x_axis_start", xy_start=xy_start)

        # make the box/line visible get the click-coordinates, button, ...
        # for to_draw in self.to_draw:
        #     to_draw.set_visible(self.visible)
        return False

    def _zoom_out(self, evt):
        if self.data_limits is not None:
            xmin, ymin, xmax, ymax = self.data_limits
            xmin, ymin, xmax, ymax = self._check_xy_values(xmin, ymin, xmax, ymax)
            print(self.data_limits)

        # Check if a zoom out is necessary
        zoomout = False
        for axes in self.axes:
            if self.data_limits is None:
                xmin, ymin, xmax, ymax = axes.data_limits
                xmin, ymin, xmax, ymax = self._check_xy_values(xmin, ymin, xmax, ymax)
            if axes.get_xlim() != (xmin, xmax) and axes.get_ylim() != (ymin, ymax):
                zoomout = True

        # Register a click if zoomout was not necessary
        if not zoomout:
            if evt.button == 1:
                pub.sendMessage("left_click", xpos=evt.xdata, ypos=evt.ydata)

        for axes in self.axes:
            if self.data_limits is None:
                xmin, ymin, xmax, ymax = axes.data_limits
                xmin, ymin, xmax, ymax = self._check_xy_values(xmin, ymin, xmax, ymax)

            # reset y-axis
            if wx.GetKeyState(wx.WXK_SHIFT):
                axes.set_ylim(ymin, ymax)
            # reset x-axis
            elif wx.GetKeyState(wx.WXK_CONTROL):
                axes.set_xlim(xmin, xmax)
            # reset both axes
            else:
                axes.set_xlim(xmin, xmax)
                axes.set_ylim(ymin, ymax)
            reset_visible(axes)

        #     if self.plotName == "RMSF":
        #         pub.sendMessage("change_zoom_rmsd", xmin=xmin, xmax=xmax)
        #     elif self.plotName == "MSDT":
        #         pub.sendMessage("change_zoom_dtms", xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)
        #
        self.canvas.draw()
        LOGGER.debug("Plot -> Zoom out")

    def _drag_label(self, evt):
        old_pos = self.dragged.get_position()
        new_pos = (old_pos[0] + evt.xdata - self.pick_pos[0], old_pos[1] + evt.ydata - self.pick_pos[1])
        self.dragged.set_position(new_pos)
        if self.dragged.obj_name is not None:
            pub.sendMessage("update_text_position", text_obj=self.dragged)
        self.dragged = None
        self.canvas.draw()  # redraw image

    def get_labels(self):
        """Collects labels"""
        x_labels, y_labels = [], []
        for axes in self.axes:
            x_labels.append(axes.get_xlabel())
            y_labels.append(axes.get_ylabel())

        return list(set(x_labels)), list(set(y_labels))

    def calculate_new_limits(self, evt):
        # Just grab bounding box
        lastx, lasty, ax = self._xy_press[0]
        x, y = evt.x, evt.y
        twinx, twiny = False, False

        Xmin, Xmax = ax.get_xlim()
        Ymin, Ymax = ax.get_ylim()

        # zoom to rect
        inverse = ax.transData.inverted()
        (lastx, lasty), (x, y) = inverse.transform([(lastx, lasty), (x, y)])

        if twinx:
            x0, x1 = Xmin, Xmax
        else:
            if Xmin < Xmax:
                if x < lastx:
                    x0, x1 = x, lastx
                else:
                    x0, x1 = lastx, x
                if x0 < Xmin:
                    x0 = Xmin
                if x1 > Xmax:
                    x1 = Xmax
            else:
                if x > lastx:
                    x0, x1 = x, lastx
                else:
                    x0, x1 = lastx, x
                if x0 > Xmin:
                    x0 = Xmin
                if x1 < Xmax:
                    x1 = Xmax

        if twiny:
            y0, y1 = Ymin, Ymax
        else:
            if Ymin < Ymax:
                if y < lasty:
                    y0, y1 = y, lasty
                else:
                    y0, y1 = lasty, y
                if y0 < Ymin:
                    y0 = Ymin
                if y1 > Ymax:
                    y1 = Ymax
            else:
                if y > lasty:
                    y0, y1 = y, lasty
                else:
                    y0, y1 = lasty, y
                if y0 > Ymin:
                    y0 = Ymin
                if y1 < Ymax:
                    y1 = Ymax

        return x0, x1, y0, y1

    def on_release(self, evt):
        """Event on button release"""
        if self.eventpress is None or (self.ignore(evt) and not self._button_down):
            return
        self._button_down = False
        pub.sendMessage("change_x_axis_start", xy_start=[None, None])

        # When the mouse is released we reset the overlay and it restores the former content to the window.
        if not self.retinaFix:
            self.wxoverlay.Reset()
            del self.wxoverlay
        else:
            self.savedRetinaImage = None
            if self.prevZoomRect:
                self.prevZoomRect.pop(0).remove()
                self.prevZoomRect = None
            if self.zoomAxes:
                self.zoomAxes = None

        # When shift is pressed, it won't zoom
        if wx.GetKeyState(wx.WXK_ALT):
            self.eventpress = None  # reset the variables to their
            self.eventrelease = None  # inital values
            self.canvas.draw()  # redraw image
            return

        # drag label
        if self.dragged is not None:
            self._drag_label(evt)
            return

        # left-click + ctrl OR double left click reset axes
        if self.eventpress.dblclick:
            self._zoom_out(evt)
            return
        # left-click sends data from current point
        elif self.eventpress.xdata == evt.xdata and self.eventpress.ydata == evt.ydata:
            if not wx.GetKeyState(wx.WXK_CONTROL):
                # Ignore the resize if the control key is down
                if evt.button == 1:
                    pub.sendMessage("left_click", xpos=evt.xdata, ypos=evt.ydata)
                self.canvas.draw()
                return

        # on_release coordinates, button, ...
        self.eventrelease = evt

        # xmin, ymin = self.eventpress.xdata, self.eventpress.ydata
        # xmax, ymax = evt.xdata, evt.ydata

        xmin, xmax, ymin, ymax = self.calculate_new_limits(evt)

        if self._trigger_extraction and self.allow_extraction:
            # A dirty way to prevent users from trying to extract data from the wrong places
            if not self.mark_annotation:
                if self._callbacks.get("CTRL", False) and isinstance(self._callbacks["CTRL"], str):
                    x_labels, y_labels = self.get_labels()
                    pub.sendMessage(
                        self._callbacks["CTRL"], rect=[xmin, xmax, ymin, ymax], x_labels=x_labels, y_labels=y_labels
                    )
                elif self.plotName in ["MSDT", "2D"] and (
                    self.eventpress.xdata != evt.xdata and self.eventpress.ydata != evt.ydata
                ):
                    pub.sendMessage("extract_from_plot_2D", xy_values=[xmin, xmax, ymin, ymax])
                # elif self.plotName != "CalibrationDT" and self.eventpress.xdata != evt.xdata:
                #     pub.sendMessage("extract_from_plot_1D", xmin=xmin, xmax=xmax, ymax=ymax)
            self.canvas.draw()
            return
        elif self._trigger_extraction and not self.allow_extraction:
            LOGGER.warning("Cannot extract data at this moment...")
            self.canvas.draw()
            return

        # send annotation
        if self._trigger_extraction and not self.allow_extraction and self.mark_annotation:
            pub.sendMessage("editor.mark.annotation", xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

        # zoom in the plot area
        x, y = evt.x, evt.y
        for lastx, lasty, a in self._xy_press:
            # allow cancellation of the zoom-in if the spatial distance is too small (5 pixels)
            if (abs(x - lastx) < 3 and evt.key != "y") or (abs(y - lasty) < 3 and evt.key != "x"):
                self._xypress = None
                self.canvas.draw()
                return
            twinx, twiny = False, False
            a._set_view_from_bbox((lastx, lasty, x, y), "in", evt.key, twinx, twiny)
        self.canvas.draw()

        #         xmin, xmax, ymin, ymax = self.get_axes_limits(a)

        if self.plotName == "RMSF":
            pub.sendMessage("change_zoom_rmsd", xmin=xmin, xmax=xmax)
        elif self.plotName == "MSDT" and not self._trigger_extraction:
            pub.sendMessage("change_zoom_dtms", xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

        # reset triggers
        if self._trigger_extraction:
            self._trigger_extraction = False

    def draw_rubberband(self, evt, x0, y0, x1, y1):
        if self.retinaFix:  # On Macs, use the following code
            # wx.DCOverlay does not work properly on Retina displays.
            rubberBandColor = "#C0C0FF"
            if self.prevZoomRect:
                self.prevZoomRect.pop(0).remove()
            self.canvas.restore_region(self.savedRetinaImage)
            X0, X1 = self.zoomStartX, evt.xdata
            Y0, Y1 = self.zoomStartY, evt.ydata
            lineX = (X0, X0, X1, X1, X0)
            lineY = (Y0, Y1, Y1, Y0, Y0)
            self.prevZoomRect = self.zoomAxes.plot(lineX, lineY, "-", color=rubberBandColor)
            self.zoomAxes.draw_artist(self.prevZoomRect[0])
            self.canvas.blit(self.zoomAxes.bbox)
            return

        if not hasattr(self, "wxoverlay"):
            self.wxoverlay = None
            return
        if not self.wxoverlay:
            return

        # Use an Overlay to draw a rubberband-like bounding box.
        dc = wx.ClientDC(self.canvas)
        odc = wx.DCOverlay(self.wxoverlay, dc)
        odc.Clear()

        # Mac's DC is already the same as a GCDC, and it causes
        # problems with the overlay if we try to use an actual
        # wx.GCDC so don't try it.
        if "wxMac" not in wx.PlatformInfo:
            dc = wx.GCDC(dc)

        height = self.canvas.figure.bbox.height
        y1 = height - y1
        y0 = height - y0

        if y1 < y0:
            y0, y1 = y1, y0
        if x1 < x0:
            x0, x1 = x1, x0

        w = x1 - x0
        h = y1 - y0
        rect = wx.Rect(x0, y0, w, h)

        rubberBandColor = "#FF00FF"  # or load from config?

        # Set a pen for the border
        color = wx.Colour(rubberBandColor)
        dc.SetPen(wx.Pen(color, 1))

        # use the same color, plus alpha for the brush
        r, g, b, a = color.Get(True)
        color.Set(r, g, b, 0x60)
        dc.SetBrush(wx.Brush(color))
        dc.DrawRectangle(rect)

    def on_motion(self, evt):
        """Event on motion"""
        # send event
        pub.sendMessage("motion_xy", xpos=evt.xdata, ypos=evt.ydata, plotname=self.plotName)

        # print(evt.xdata, evt.ydata, evt.key, evt.button)

        # show rubberband
        # if evt.key in ["x", "y", "ctrl+control"] or evt.button is not None:
        if evt.button == 1 and self._xy_press:  # and not self.mark_annotation:
            x, y = evt.x, evt.y
            lastx, lasty, a = self._xy_press[0]
            (x1, y1), (x2, y2) = np.clip([[lastx, lasty], [x, y]], a.bbox.min, a.bbox.max)
            if evt.key is not None:
                if "x" in evt.key or "alt" in evt.key:
                    y1, y2 = a.bbox.intervaly
                elif "y" in evt.key or "shift" in evt.key:
                    x1, x2 = a.bbox.intervalx
            self.draw_rubberband(evt, x1, y1, x2, y2)

    def update(self):
        """draw using newfangled blit or oldfangled draw depending on useblit"""
        if self.useblit:
            if self.background is not None:
                self.canvas.restore_region(self.background)
            for axes, to_draw in zip(self.axes, self.to_draw):
                axes.draw_artist(to_draw)
            self.canvas.blit(self.canvas.figure.bbox)
        else:
            self.canvas.draw_idle()

    def reset_axes(self, axis_pos):
        """Reset plot limits"""
        if self.data_limits is not None:
            xmin, ymin, xmax, ymax = self.data_limits
            xmin, ymin, xmax, ymax = self._check_xy_values(xmin, ymin, xmax, ymax)

        # Register a click if zoomout was not necessary
        for axes in self.axes:
            if self.data_limits is None:
                xmin, ymin, xmax, ymax = axes.data_limits
                xmin, ymin, xmax, ymax = self._check_xy_values(xmin, ymin, xmax, ymax)

            if axis_pos in ["left", "right"]:
                axes.set_ylim(ymin, ymax)
            elif axis_pos in ["top", "bottom"]:
                axes.set_xlim(xmin, xmax)
                if self.plotName == "RMSF":
                    pub.sendMessage("change_zoom_rmsd", xmin=xmin, xmax=xmax)
            reset_visible(axes)
            self.canvas.draw()

    @staticmethod
    def _check_xy_values(xmin, ymin, xmax, ymax):
        if xmin > xmax:
            xmin, xmax = xmax, xmin
        if ymin > ymax:
            ymin, ymax = ymax, ymin
        # assure that x and y values are not equal
        if xmin == xmax:
            xmax = xmin * 1.0001
        if ymin == ymax:
            ymax = ymin * 1.0001

        return xmin, ymin, xmax, ymax
