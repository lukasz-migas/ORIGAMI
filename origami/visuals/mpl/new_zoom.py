# Standard library imports
import logging

# Third-party imports
import wx
import numpy as np
from pubsub import pub
from matplotlib.text import Text
from matplotlib.legend import Legend
from matplotlib.patches import Rectangle

# Local imports
from origami.visuals.mpl.gids import PlotIds

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
            if xmax > x > xmin:
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
    """Check x-axis values"""
    ydat = xys[:, 1]
    xdat = xys[:, 0]
    if xmin is not None and xmax is not None:
        bool1 = np.all(np.array([xdat > xmin, xdat < xmax]), axis=0)
        ydat = ydat[bool1]

    return xdat, ydat


def reset_visible(axes):
    """Reset visible axes"""
    for line in axes.lines:
        line.set_clip_on(True)
    for t in axes.texts:
        t.set_visible(True)


def get_axes_start(axes):
    """Get axes start"""
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

    return [xmin, ymin, xmax, ymax]


class MPLInteraction:
    """
    Main class to enable zoom in 1D, 2D and 3D plots
    """

    def __init__(
        self,
        axes,
        useblit=False,
        button=1,
        plotName=None,
        data_limits=None,
        plot_id: str = None,
        plot_parameters=None,
        allow_wheel=True,
        allow_extraction=True,
        callbacks=None,
        parent=None,
        is_heatmap: bool = False,
        is_joint: bool = False,
        obj=None,
    ):
        self.parent = parent
        self.axes = None
        self.canvas = None
        self.mpl_events = []
        self.plot_id = plot_id
        self.allow_extraction = allow_extraction
        self.is_heatmap = is_heatmap
        self.is_joint = is_joint
        self.data_object = obj
        self._image_scale = 0
        self.plotName = plotName

        self.axes, self._callbacks, data_limits = self.validate_input(axes, callbacks, data_limits)

        self.active = True  # for activation / deactivation
        self.background = None
        self.dragged = None
        self._is_inside_axes = True
        self._last_location = None
        self._last_xy_position = []
        self.current_ymax = None
        self.mark_annotation = False
        self.prevent_sync_zoom = False

        # setup some parameters
        self.plot_parameters = {} if plot_parameters is None else plot_parameters
        self.allow_wheel = allow_wheel
        self.n_mouse_wheel_steps = 3

        self.useblit = useblit

        if button is None or isinstance(button, list):
            self.validButtons = button
        elif isinstance(button, int):
            self.validButtons = [button]

        # flags
        self._trigger_extraction = False
        self._is_label = False
        self._is_legend = False
        self._is_patch = False

        # events
        self._xy_press = []
        self.evt_press = None
        self.evt_release = None
        self.pick_pos = None
        self._ctrl_key = False
        self._alt_key = False
        self._shift_key = False
        self._space_key = False
        self._button_down = False
        self._key_press = False
        self._mouse_wheel = False

        # based on MPL
        self.wx_overlay = None
        self.retinaFix = "wxMac" in wx.PlatformInfo
        self.savedRetinaImage = None
        self.zoomStartX = None
        self.zoomStartY = None
        self.zoomAxes = None
        self.prevZoomRect = None

        self._color_normal = wx.BLACK
        self._color_ctrl = wx.RED

        self.bind_plot_events(axes)
        self.set_data_limits(data_limits)

        # listener to change plot parameters
        pub.subscribe(self.on_update_parameters, "zoom.parameters")

    @property
    def is_multiscale(self):
        """Check whether image is multiscale"""
        if self.data_object:
            if hasattr(self.data_object, "is_multiscale"):
                return self.data_object.is_multiscale()
        return False

    @staticmethod
    def validate_input(axes, callbacks, data_limits):
        """Validate input to ensure correct parameters are being used"""
        if not isinstance(axes, list):
            axes = list(axes)

        if callbacks is None:
            callbacks = dict()
        for key in callbacks:
            if not isinstance(callbacks[key], (list, tuple)):
                callbacks[key] = [callbacks[key]]

        if not all(isinstance(elem, (list, tuple)) for elem in data_limits):
            data_limits = [data_limits]

        return axes, callbacks, data_limits

    def set_data_limits(self, data_limits):
        """Set data limits on the axes object"""
        if len(data_limits) != len(self.axes):
            raise ValueError("Incorrect `data_limits` input")

        for i, _ in enumerate(self.axes):
            self.axes[i].data_limits = data_limits[i]

    def on_update_parameters(self, plot_parameters):
        """Update plotting parameters"""
        self.plot_parameters = plot_parameters

        if "normal" in plot_parameters:
            self._color_normal = wx.Colour(plot_parameters["normal"])
        if "extract" in plot_parameters:
            self._color_ctrl = wx.Colour(plot_parameters["extract"])

    def update_handler(self, data_limits=None, obj=None):
        """Update zoom parameters"""
        self.set_data_limits(data_limits)
        self.data_object = obj

    def update_extents(self, data_limits=None):
        """Update plot extents"""
        if data_limits is not None:
            self.set_data_limits(data_limits)

    def update_mark_state(self, state):
        """Update the state of annotation"""
        self.mark_annotation = state

    def on_pick_event(self, event):
        """Store which text object was picked and were the pick event occurs."""
        self._is_label = False
        self._is_legend = False
        self._is_patch = False

        if isinstance(event.artist, Text):
            self.dragged = event.artist
            self.pick_pos = (event.mouseevent.xdata, event.mouseevent.ydata)
            self._is_label = True
        elif isinstance(event.artist, Legend):
            self.dragged = event.artist
            self._is_legend = True
        elif isinstance(event.artist, Rectangle):
            if event.artist.get_picker():
                self.dragged = event.artist
                self.pick_pos = (self.dragged.get_width() / 2, self.dragged.get_height() / 2)
                self._is_patch = True
        return True

    def bind_plot_events(self, axes):
        """Bind events"""
        # remove any previous events connected to the canvas
        if self.canvas is not axes[0].figure.canvas:
            for event in self.mpl_events:
                self.canvas.mpl_disconnect(event)

        self.canvas = axes[0].figure.canvas

        # pick events
        self.mpl_events.append(self.canvas.mpl_connect("pick_event", self.on_pick_event))

        # button events
        self.mpl_events.append(self.canvas.mpl_connect("button_press_event", self.on_press))
        self.mpl_events.append(self.canvas.mpl_connect("button_release_event", self.on_release))
        self.mpl_events.append(self.canvas.mpl_connect("key_press_event", self.on_key_state))
        self.mpl_events.append(self.canvas.mpl_connect("key_release_event", self.on_key_state))

        # motion events
        self.mpl_events.append(self.canvas.mpl_connect("motion_notify_event", self.on_key_state))
        self.mpl_events.append(self.canvas.mpl_connect("motion_notify_event", self.on_motion))

        # enter events
        self.mpl_events.append(self.canvas.mpl_connect("axes_enter_event", self.on_enter_axes))
        self.mpl_events.append(self.canvas.mpl_connect("axes_leave_event", self.on_leave_axes))

        # scroll events
        self.mpl_events.append(self.canvas.mpl_connect("scroll_event", self.on_mouse_wheel))

        # draw events
        self.mpl_events.append(self.canvas.mpl_connect("draw_event", self.update_background))

        # Pre-set keys
        self._shift_key = False
        self._ctrl_key = False
        self._alt_key = False
        self._mouse_wheel = False
        self._key_press = False
        self._trigger_extraction = False
        self._button_down = False

    def on_enter_axes(self, evt):
        """Flag that mouse has entered the axes"""
        self._last_location = [evt.xdata, evt.ydata]
        self._is_inside_axes = True

    #         pub.sendMessage("view.activate", view_id=self.plot_id)

    def on_leave_axes(self, _evt):
        """Flag that mouse has left the axes"""
        self._is_inside_axes = False

    def on_key_state(self, _evt):
        """Update state of the key"""
        self._ctrl_key = wx.GetKeyState(wx.WXK_CONTROL)
        self._alt_key = wx.GetKeyState(wx.WXK_ALT)
        self._shift_key = wx.GetKeyState(wx.WXK_SHIFT)
        self._space_key = wx.GetKeyState(wx.WXK_SPACE)
        self._trigger_extraction = False

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
        pub.sendMessage("motion_mode", plot_interaction=motion_mode)

    def update_background(self, _evt):
        """force an update of the background"""
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
                elif evt.button == 2 and self.evt_release is None:
                    return True
                else:
                    return False

        # If no button pressed yet or if it was out of the axes, ignore
        if self.evt_press is None:
            return evt.inaxes not in self.axes

        # If a button pressed, check if the on_release-button is the same
        return evt.inaxes not in self.axes or evt.button != self.evt_press.button

    def on_press(self, evt):
        """Event on button press"""
        pub.sendMessage("view.activate", view_id=self.plot_id)

        self.evt_press = evt
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

        # check whether it was a double click
        if not self._is_inside_axes:
            # completely un-zoom
            if evt.dblclick and not self._shift_key:
                self.reset_axes(axis_pos=self._last_location)
            # un-zoom along one of the axes
            elif evt.dblclick and self._shift_key and self._last_location in ["left", "right"]:
                if self.current_ymax is None:
                    return
                for axes in self.axes:
                    axes.set_ylim(0, self.current_ymax)
                self.canvas.draw()
                return

        # dragging annotation
        if self.dragged is not None and not evt.dblclick:
            if self._is_legend or self._is_label:
                return

        # set rect for displaying the zoom
        if not self.retinaFix:
            self.wx_overlay = wx.Overlay()
        else:
            if evt.inaxes is not None:
                self.savedRetinaImage = self.canvas.copy_from_bbox(evt.inaxes.bbox)
                self.zoomAxes = evt.inaxes

        self._button_down = True
        pub.sendMessage("change_x_axis_start", xy_start=xy_start)
        return False

    def on_release(self, evt):
        """Event on button release"""
        if self.evt_press is None or (self.ignore(evt) and not self._button_down):
            return
        self._button_down = False
        pub.sendMessage("change_x_axis_start", xy_start=[None, None])

        # When the mouse is released we reset the overlay and it restores the former content to the window.
        if not self.retinaFix and self.wx_overlay:
            self.wx_overlay.Reset()
            self.wx_overlay = None
        else:
            self.savedRetinaImage = None
            if self.prevZoomRect:
                self.prevZoomRect.pop(0).remove()
                self.prevZoomRect = None
            if self.zoomAxes:
                self.zoomAxes = None

        # When shift is pressed, it won't zoom
        if wx.GetKeyState(wx.WXK_ALT):
            self.evt_press = None  # reset the variables to their
            self.evt_release = None  # inital values
            self.canvas.draw()  # redraw image
            return

        # drag label
        if self.dragged is not None:
            if self._is_label:
                self._drag_label(evt)
            elif self._is_legend:
                self._drag_legend(evt)
            elif self._is_patch:
                self._drag_patch(evt)
            return

        # left-click + ctrl OR double left click reset axes
        if self.evt_press.dblclick:
            self._zoom_out(evt)
            return
        # left-click sends data from current point
        elif self.evt_press.xdata == evt.xdata and self.evt_press.ydata == evt.ydata:
            if not wx.GetKeyState(wx.WXK_CONTROL):
                # Ignore the resize if the control key is down
                if evt.button == 1:
                    pub.sendMessage("left_click", xpos=evt.xdata, ypos=evt.ydata)
                self.canvas.draw()
                return

        # on_release coordinates, button, ...
        self.evt_release = evt

        xmin, xmax, ymin, ymax = self.calculate_new_limits(evt)

        if self._trigger_extraction and self.allow_extraction:
            self.on_callback(xmin, xmax, ymin, ymax, evt)
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
        for last_x, last_y, a in self._xy_press:
            # allow cancellation of the zoom-in if the spatial distance is too small (5 pixels)
            if (abs(x - last_x) < 3 and evt.key != "y") or (abs(y - last_y) < 3 and evt.key != "x"):
                self._xy_press = None
                self.canvas.draw()
                return
            twin_x, twin_y = False, False
            a._set_view_from_bbox((last_x, last_y, x, y), "in", evt.key, twin_x, twin_y)  # noqa
            if self.is_joint:
                self._handle_joint(False)
            if self.is_multiscale:
                self._handle_multiscale(False)
        self.canvas.draw()

        # reset triggers
        if self._trigger_extraction:
            self._trigger_extraction = False

    def on_callback(self, xmin, xmax, ymin, ymax, evt):
        """Process callback"""
        # A dirty way to prevent users from trying to extract data from the wrong places
        if self.mark_annotation:
            return

        # parse extraction limits through cleanup
        xmin, xmax, ymin, ymax = self._parse_extraction_limits(xmin, xmax, ymin, ymax, evt)
        x_labels, y_labels = self.get_labels()

        # process CTRL callbacks
        if self._callbacks.get("CTRL", False) and isinstance(self._callbacks["CTRL"], list):
            for callback in self._callbacks["CTRL"]:
                pub.sendMessage(callback, rect=[xmin, xmax, ymin, ymax], x_labels=x_labels, y_labels=y_labels)
        # process SHIFT callbacks
        elif self._callbacks.get("SHIFT", False) and isinstance(self._callbacks["SHIFT"], list):
            for callback in self._callbacks["SHIFT"]:
                pub.sendMessage(callback, rect=[xmin, xmax, ymin, ymax], x_labels=x_labels, y_labels=y_labels)
        # process ALT callbacks
        elif self._callbacks.get("ALT", False) and isinstance(self._callbacks["ALT"], list):
            for callback in self._callbacks["ALT"]:
                pub.sendMessage(callback, rect=[xmin, xmax, ymin, ymax], x_labels=x_labels, y_labels=y_labels)
        elif self.plotName in ["MSDT", "2D"] and (
            self.evt_press.xdata != evt.xdata and self.evt_press.ydata != evt.ydata
        ):
            pub.sendMessage("extract_from_plot_2D", xy_values=[xmin, xmax, ymin, ymax])

    def _parse_extraction_limits(self, xmin, xmax, ymin, ymax, _evt):
        """Special parsing of x/y-limits for data extraction that supports multi-plot behaviour"""
        # special behaviour for joint plots
        plot_gid = self.evt_press.inaxes.get_gid()

        if self.is_joint:
            # top plot - need to update y-axis
            if plot_gid == PlotIds.PLOT_JOINT_X:
                _, _, ymin, ymax = self.axes[0].plot_limits
            elif plot_gid == PlotIds.PLOT_JOINT_Y:
                xmin, xmax, _, _ = self.axes[0].plot_limits

        return xmin, xmax, ymin, ymax

    def on_motion(self, evt):
        """Event on motion"""
        # send event
        pub.sendMessage("motion_xy", x_pos=evt.xdata, y_pos=evt.ydata, plot_name=self.plotName, plot_id=self.plot_id)

        # drag label
        if self.dragged is not None:
            if self._is_label:
                self._drag_label(evt, False)
            elif self._is_patch:
                self._drag_patch(evt, False)
            return

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

    def draw_rubberband(self, evt, x0, y0, x1, y1):
        """Draw box to highlight the currently selected region"""
        if self.retinaFix:  # On Macs, use the following code
            # wx.DCOverlay does not work properly on Retina displays.
            rubber_band_color = "#C0C0FF"
            if self.prevZoomRect:
                self.prevZoomRect.pop(0).remove()
            self.canvas.restore_region(self.savedRetinaImage)
            X0, X1 = self.zoomStartX, evt.xdata
            Y0, Y1 = self.zoomStartY, evt.ydata
            lineX = (X0, X0, X1, X1, X0)
            lineY = (Y0, Y1, Y1, Y0, Y0)
            self.prevZoomRect = self.zoomAxes.plot(lineX, lineY, "-", color=rubber_band_color)
            self.zoomAxes.draw_artist(self.prevZoomRect[0])
            self.canvas.blit(self.zoomAxes.bbox)
            return

        if not hasattr(self, "wx_overlay"):
            self.wx_overlay = None
            return
        if not self.wx_overlay:
            return

        # Use an Overlay to draw a rubberband-like bounding box.
        dc = wx.ClientDC(self.canvas)
        odc = wx.DCOverlay(self.wx_overlay, dc)
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

        # Set a pen for the border
        # color = wx.Colour(rubber_band_color)
        color = self.get_color(evt)
        dc.SetPen(wx.Pen(color, 1))

        # use the same color, plus alpha for the brush
        r, g, b, a = color.Get()
        color.Set(r, g, b, 0x60)
        dc.SetBrush(wx.Brush(color))
        dc.DrawRectangle(rect)

    def get_color(self, evt):
        """Get appropriate color"""
        if self._ctrl_key:
            return self._color_ctrl
        return self._color_normal

    def _handle_joint(self, zoom_out: bool):
        """Handle joint plot

        This function will automatically update joint plots (x, y) with new data whenever user zooms-in or zooms-out
        """
        if self.data_object is None and len(self.axes) == 3 and self.is_joint:
            return

        # get current limits
        if not zoom_out:
            xmin, xmax = self.axes[0].get_xlim()
            ymin, ymax = self.axes[0].get_ylim()
            ax_x_y = self.data_object.get_x_for_roi(xmin, xmax, ymin, ymax)
            ax_y_y = self.data_object.get_y_for_roi(xmin, xmax, ymin, ymax)
        else:
            ax_x_y = self.data_object.xy
            ax_y_y = self.data_object.yy

        for line in self.axes[1].get_lines():
            gid = line.get_gid()
            if gid == PlotIds.PLOT_JOINT_X:
                _y = ax_x_y if line.get_xdata().shape == ax_x_y.shape else ax_y_y
                line.set_ydata(_y)
                self.axes[1].set_ylim(0, _y.max())
                break

        for line in self.axes[2].get_lines():
            gid = line.get_gid()
            if gid == PlotIds.PLOT_JOINT_Y:
                _x = ax_y_y if line.get_xdata().shape == ax_y_y.shape else ax_x_y
                line.set_xdata(_x)
                self.axes[2].set_xlim(_x.min(), _x.max())
                break

    def _handle_multiscale(self, zoom_out: bool):
        """Handle multi-scale image"""
        pass

    def _zoom_out(self, evt):
        # Check if a zoom out is necessary
        zoomout = False
        for axes in self.axes:
            xmin, ymin, xmax, ymax = self._check_xy_values(*axes.data_limits)
            if axes.get_xlim() != (xmin, xmax) and axes.get_ylim() != (ymin, ymax):
                zoomout = True

        # Register a click if zoomout was not necessary
        if not zoomout:
            if evt.button == 1:
                pub.sendMessage("left_click", xpos=evt.xdata, ypos=evt.ydata)

        for axes in self.axes:
            xmin, ymin, xmax, ymax = self._check_xy_values(*axes.data_limits)

            # reset y-axis
            if wx.GetKeyState(wx.WXK_SHIFT) or evt.key == "y":
                axes.set_ylim(ymin, ymax)
            # reset x-axis
            elif wx.GetKeyState(wx.WXK_CONTROL) or evt.key == "x":
                axes.set_xlim(xmin, xmax)
            # reset both axes
            else:
                axes.set_xlim(xmin, xmax)
                axes.set_ylim(ymin, ymax)
            reset_visible(axes)

        # update axes
        if self.is_joint:
            self._handle_joint(True)

        self.canvas.draw()
        LOGGER.debug("Plot -> Zoom out")

    def _drag_label(self, evt, reset=True):
        """Move label, update its position and reset dragged object"""
        x, y = evt.xdata, evt.ydata

        if evt.key == "x":
            _, y = self.dragged.get_position()
        elif evt.key == "y":
            x, _ = self.dragged.get_position()

        new_pos = (x, y)
        if None not in new_pos:
            self.dragged.set_position(new_pos)
        self.canvas.draw()  # redraw image

        if reset:
            if self.dragged.obj_name is not None:
                if self._callbacks["MOVE_LABEL"]:
                    pub.sendMessage(self._callbacks["MOVE_LABEL"], label_obj=self.dragged)
                else:
                    pub.sendMessage("update_text_position", text_obj=self.dragged)
            self._is_label = False
            self.dragged = None

    def _drag_legend(self, _evt):
        """Drag legend post-event"""
        self._is_legend = False
        self.dragged = None

    def _drag_patch(self, evt, reset=True):
        """Drag patch, update its position and reset dragged object"""
        width, height = self.pick_pos
        x = evt.xdata - width
        y = evt.ydata - height
        if evt.key == "x":
            _, y = self.dragged.get_xy()
        elif evt.key == "y":
            x, _ = self.dragged.get_xy()

        self.dragged.set_xy((x, y))
        self.canvas.draw()  # redraw image

        if reset:
            if self.dragged.obj_name is not None:
                if self._callbacks["MOVE_PATCH"]:
                    pub.sendMessage(self._callbacks["MOVE_PATCH"], patch_obj=self.dragged)
            self._is_patch = False
            self.dragged = None

    def get_labels(self):
        """Collects labels"""
        x_labels, y_labels = [], []
        for axes in self.axes:
            x_label = axes.get_xlabel()
            if x_label:
                x_labels.append(x_label)
            y_label = axes.get_ylabel()
            if y_label:
                y_labels.append(y_label)

        return list(set(x_labels)), list(set(y_labels))

    def calculate_new_limits(self, evt):
        """Calculate new plot limits"""
        # Just grab bounding box
        last_x, last_y, ax = self._xy_press[0]
        x, y = evt.x, evt.y
        twin_x, twin_y = False, False

        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()

        # zoom to rect
        inverse = ax.transData.inverted()
        (last_x, last_y), (x, y) = inverse.transform([(last_x, last_y), (x, y)])

        if twin_x:
            x0, x1 = x_min, x_max
        else:
            if x_min < x_max:
                if x < last_x:
                    x0, x1 = x, last_x
                else:
                    x0, x1 = last_x, x
                if x0 < x_min:
                    x0 = x_min
                if x1 > x_max:
                    x1 = x_max
            else:
                if x > last_x:
                    x0, x1 = x, last_x
                else:
                    x0, x1 = last_x, x
                if x0 > x_min:
                    x0 = x_min
                if x1 < x_max:
                    x1 = x_max

        if twin_y:
            y0, y1 = y_min, y_max
        else:
            if y_min < y_max:
                if y < last_y:
                    y0, y1 = y, last_y
                else:
                    y0, y1 = last_y, y
                if y0 < y_min:
                    y0 = y_min
                if y1 > y_max:
                    y1 = y_max
            else:
                if y > last_y:
                    y0, y1 = y, last_y
                else:
                    y0, y1 = last_y, y
                if y0 > y_min:
                    y0 = y_min
                if y1 < y_max:
                    y1 = y_max

        return x0, x1, y0, y1

    def update(self):
        """draw using newfangled blit or oldfangled draw depending on useblit"""
        if self.useblit:
            if self.background is not None:
                self.canvas.restore_region(self.background)
            # for axes, to_draw in zip(self.axes, self.to_draw):
            #     axes.draw_artist(to_draw)
            self.canvas.blit(self.canvas.figure.bbox)
        else:
            self.canvas.draw_idle()

    def reset_axes(self, axis_pos):
        """Reset plot limits"""
        # Register a click if zoomout was not necessary
        for axes in self.axes:
            xmin, ymin, xmax, ymax = self._check_xy_values(*axes.data_limits)

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

    def on_mouse_wheel(self, evt):
        """Event on mouse-wheel"""
        # _evt = evt.guiEvent
        # print(_evt.GetLinesPerAction(), _evt.GetWheelRotation(), _evt.GetWheelDelta())


#         print(evt.xdata)
#         print(dir(evt))

#         if wx.GetKeyState(wx.WXK_ALT) or not self._is_inside_axes:
#             return

#         if not self.allow_wheel:
#             return
#
#         # Update cursor
#         motion_mode = [
#             self._shift_key,
#             self._ctrl_key,
#             self._alt_key,
#             self._trigger_extraction,
#             True,
#             self._button_down,
#             self.dragged,
#         ]
#         pub.sendMessage("motion_mode", dataOut=motion_mode)
#
#         # The actual work
#         for axes in self.axes:
#             x0, x1, y0, y1 = self.get_axes_limits(axes)
#
# #             x0_diff, x1_diff = evt.xdata - x0, x1 - evt.xdata
# #             y0_diff, y1_diff = evt.ydata - x0, x1 - evt.ydata
#             print(x0, x1, y0, y1)
#             print(dir(evt), evt.xdata, evt.ydata, evt)

#             shift_key = wx.GetKeyState(wx.WXK_SHIFT)
#
#             if self.data_limits is not None:
#                 xmin, ymin, xmax, ymax = self.data_limits
#             else:
#                 xmin, ymin, xmax, ymax = axes.data_limits
#
#             # Zoom in X-axis only
#             if not shift_key:
#                 # calculate difference
#                 try:
#                     x0_diff, x1_diff = evt.xdata - x0, x1 - evt.xdata
#                     x_sum = x0_diff + x1_diff
#                 except Exception:
#                     return
#                 stepSize = evt.step * ((x1 - x0) / 50)
#                 newXmin = x0 - (stepSize * (x0_diff / x_sum))
#                 newXmax = x1 + (stepSize * (x1_diff / x_sum))
#                 # Check if the X-values are off the data lims
#                 if newXmin < xmin:
#                     newXmin = xmin
#                 if newXmax > xmax:
#                     newXmax = xmax
#                 axes.set_xlim((newXmin, newXmax))
#                 if self.plotName == "MSDT":
#                     pub.sendMessage("change_zoom_dtms", xmin=newXmin, xmax=newXmax, ymin=ymin, ymax=ymax)
#
#             # Zoom in Y-axis only
#             elif shift_key:
#                 # Check if its 1D plot
#                 if self.plotName in ["1D", "CalibrationDT", "MS"]:
#                     stepSize = evt.step * ((y1 - y0) / 25)
#                     axes.set_ylim((0, y1 + stepSize))
#                 elif self.plotName == "MSDT":
#                     try:
#                         y0_diff, y1_diff = evt.ydata - y0, y1 - evt.ydata
#                         y_sum = y0_diff + y1_diff
#                     except Exception:
#                         return
#
#                     stepSize = evt.step * ((y1 - y0) / 50)
#                     newYmin = y0 - (stepSize * (y0_diff / y_sum))
#                     newYmax = y1 + (stepSize * (y1_diff / y_sum))
#                     # Check if the Y-values are off the data lims
#                     if newYmin < ymin:
#                         newYmin = ymin
#                     if newYmax > ymax:
#                         newYmax = ymax
#                     axes.set_ylim((newYmin, newYmax))
#                 elif self.plotName != "1D":
#                     try:
#                         y0_diff, y1_diff = evt.xdata - y0, y1 - evt.xdata
#                         y_sum = y0_diff + y1_diff
#                     except Exception:
#                         return
#
#                     stepSize = evt.step * ((y1 - y0) / 50)
#                     newYmin = y0 - (stepSize * (y0_diff / y_sum))
#                     newYmax = y1 + (stepSize * (y1_diff / y_sum))
#                     # Check if the Y-values are off the data lims
#                     if newYmin < ymin:
#                         newYmin = ymin
#                     if newYmax > ymax:
#                         newYmax = ymax
#                     axes.set_ylim((newYmin, newYmax))
#
#             self.canvas.draw()
