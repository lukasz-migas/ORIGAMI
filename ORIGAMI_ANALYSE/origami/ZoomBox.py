# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
#
# 	 GitHub : https://github.com/lukasz-migas/ORIGAMI
# 	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
# 	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or
#    modify it under the condition you cite and credit the authors whenever
#    appropriate.
#    The program is distributed in the hope that it will be useful but is
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

import wx
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.text import Text
from pubsub import pub

from toolbox import dir_extra

import logging
logger = logging.getLogger("origami")

# TODO: add dragging in the labels area - should be able to grab and drag so its easier
#       to manipulate plot area


def GetMaxes(axes, xmin=None, xmax=None):
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
        except Exception as _e:
            logger.error(_e)

    for p in axes.collections:
        try:
            xys = np.array(p.get_paths()[0].vertices)
        except IndexError:
            break
        offsets = p.get_offsets()
        if len(offsets) > 1:
            xys = np.array(offsets)

        xdat, ydat = on_check_xys(xys, xmin, xmax)
        try:
            yvals.append([np.amin(ydat), np.amax(ydat)])
            xvals.append([np.amin(xdat), np.amax(xdat)])
        except Exception as _e:
            logger.error(_e)

    for patch in axes.patches:
        try:
            if (patch.get_width()) and (patch.get_height()):
                vertices = patch.get_path().vertices
                if vertices.size > 0:
                    xys = np.array(patch.get_patch_transform().transform(vertices))
                    xdat, ydat = on_check_xys(xys, xmin, xmax)
                    try:
                        yvals.append([np.amin(ydat), np.amax(ydat)])
                        xvals.append([np.amin(xdat), np.amax(xdat)])
                    except Exception as _e:
                        logger.error(_e)
        except Exception as _e:
            try:
                xys = patch.xy
                xdat, ydat = on_check_xys(xys, xmin, xmax)

                yvals.append([np.amin(ydat), np.amax(ydat)])
                xvals.append([np.amin(xdat), np.amax(xdat)])
            except Exception as _e:
                logger.error(_e)

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


def on_check_xys(xys, xmin, xmax):
    ydat = xys[:, 1]
    xdat = xys[:, 0]
    if xmin is not None and xmax is not None:
        bool1 = np.all(np.array([xdat > xmin, xdat < xmax]), axis=0)
        ydat = ydat[bool1]

    return xdat, ydat


def ResetVisible(axes):
    for line in axes.lines:
        line.set_clip_on(True)
    for t in axes.texts:
        t.set_visible(True)


def GetStart(axes):
    outputs = np.array([GetMaxes(axis) for axis in axes])
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


def getMaxFromRange(data, start, end):
    """
    Find and return a narrow data range
    """
    # find values closest to the start/end
    try:
        start = np.argmin(np.abs(data[:, 0] - start))
        end = np.argmin(np.abs(data[:, 0] - end))
    except Exception:
        return 1

    # ensure start/end are in correct order
    if start > end:
        end, start = start, end
    # narrow down the search
    data = data[start:end, :]
    # find maximum
    try:
        ymax = np.amax(data[:, 1])
    except ValueError:
        #         print('Could not find maximum')
        ymax = 1
    return ymax


def xy_range_divider(values=None):
    """ 
    Function to check whether x/y axis labels do not need formatting
    """
    baseDiv = 10
    increment = 10
    divider = baseDiv
    multiplier = 1

    itemShape = values.shape
    # find maximum
    if len(itemShape) > 1:
        maxValue = np.amax(values)
    elif len(itemShape) == 1:
        maxValue = np.max(values)
    else:
        maxValue = values

    # calculate division value
    dValue = maxValue / divider
    while 10 <= dValue <= 1:
        divider = divider * increment
        dValue = maxValue / divider

    mValue = maxValue * multiplier
    while mValue <= 1 and not mValue >= 0.1:
        multiplier = multiplier * increment
        mValue = maxValue * multiplier

    if divider == baseDiv:
        expo = -len(str(multiplier)) - len(str(multiplier).rstrip('0'))
        return multiplier, expo
    else:
        expo = len(str(divider)) - len(str(divider).rstrip('0'))
        return divider, expo


def str2num(string):
    try:
        val = float(string)
        return val
    except (ValueError, TypeError):
        return None


def num2str(val):
    try:
        string = str(val)
        return string
    except (ValueError, TypeError):
        return None


class GetXValues:

    def __init__(self, axes):
        """
        This function retrieves the x-axis info
        """
        self.axes = None
        self.canvas = None
        self.cids = []

        self.new_axes(axes)

    def new_axes(self, axes):
        self.axes = axes
        if self.canvas is not axes[0].figure.canvas:
            for cid in self.cids:
                self.canvas.mpl_disconnect(cid)
                print('disconnected')
            self.canvas = axes[0].figure.canvas


class ZoomBox:
    """
    Main class to enable zoom in 1D, 2D and 3D plots
    """

    def __init__(self, axes, onselect, drawtype='box',
                 minspanx=None,
                 minspany=None,
                 useblit=False,
                 lineprops=None,
                 rectprops=None,
                 onmove_callback=None,
                 spancoords='data',
                 button=None,
                 data_lims=None,
                 plotName=None,
                 plotParameters=None,
                 allowWheel=True,
                 preventExtraction=True):

        """
        Create a selector in axes.  When a selection is made, clear
        the span and call onselect with

          onselect(pos_1, pos_2)

        and clear the drawn box/line. There pos_i are arrays of length 2
        containing the x- and y-coordinate.

        If minspanx is not None then events smaller than minspanx
        in x direction are ignored(it's the same for y).

        The rect is drawn with rectprops; default
          rectprops = dict(facecolor='red', edgecolor = 'black',
                           alpha=0.5, fill=False)

        The line is drawn with lineprops; default
          lineprops = dict(color='black', linestyle='-',
                           linewidth = 2, alpha=0.5)

        Use type if you want the mouse to draw a line, a box or nothing
        between click and actual position ny setting

        drawtype = 'line', drawtype='box' or drawtype = 'none'.

        spancoords is one of 'data' or 'pixels'.  If 'data', minspanx
        and minspanx will be interpreted in the same coordinates as
        the x and y axis, if 'pixels', they are in pixels

        button is a list of integers indicating which mouse buttons should
        be used for rectangle selection.  You can also specify a single
        integer if only a single button is desired.  Default is None, which
        does not limit which button can be used.
        Note, typically:
         1 = left mouse button
         2 = center mouse button (scroll wheel)
         3 = right mouse button
        """
        if plotParameters == None: self.plot_parameters = {}
        else: self.plot_parameters = plotParameters

        self.crossoverpercent = self.plot_parameters['zoom_crossover_sensitivity']
        self.wheelStepSize = 3
        self.axes = None
        self.canvas = None
        self.visible = True
        self.cids = []
        self.plotName = plotName
        self.preventExtraction = preventExtraction

        self.active = True  # for activation / deactivation
        self.to_draw = []
        self.background = None
        self.dragged = None

        self.insideAxes = True
        self.insideFigure = True
        self.exitLoc = None
        self.span = None
        self.lastXY = []
        self.current_ymax = None
        self.allowWheel = allowWheel
        self.mark_annotation = False
        self.prevent_sync_zoom = False

        # setup some parameters
        self.show_cursor_cross = self.plot_parameters['grid_show']

        self.onselect = onselect
        self.onmove_callback = onmove_callback

        self.useblit = useblit
        self.minspanx = minspanx
        self.minspany = minspany

        self.horz_line = None
        self.vert_line = None

        if button is None or isinstance(button, list): self.validButtons = button
        elif isinstance(button, int): self.validButtons = [button]

        assert (spancoords in ('data', 'pixels'))

        self.pick_pos = None
        self.addToTable = False
        self.ctrlKey = False
        self.altKey = False
        self.shiftKey = False
        self.buttonDown = False
        self.keyPress = False
        self.spancoords = spancoords
        self.eventpress = None
        self.eventrelease = None
        self.new_axes(axes, rectprops)

        try:
            if data_lims is None:
                self.data_lims = GetStart(self.axes)
            else:
                self.data_lims = data_lims
            xmin, ymin, xmax, ymax = self.data_lims
            if xmin > xmax: xmin, xmax = xmax, xmin
            if ymin > ymax: ymin, ymax = ymax, ymin
            # assure that x and y values are not equal
            if xmin == xmax: xmax = xmin * 1.0001
            if ymin == ymax: ymax = ymin * 1.0001
            for axes in self.axes:
                axes.set_xlim(xmin, xmax)
                axes.set_ylim(ymin, ymax)
        except Exception:
            for i in range(len(self.axes)):
                self.axes[i].data_lims = data_lims[i]
            self.prevent_sync_zoom = True
            self.data_lims = None

        # listener to change plot parameters
        pub.subscribe(self.onUpdateParameters, 'plot_parameters')

    def onUpdateParameters(self, plot_parameters):
        self.plot_parameters = plot_parameters

        lineprops = {}
        lineprops['color'] = self.plot_parameters['grid_color']
        lineprops['linewidth'] = self.plot_parameters['grid_line_width']

        if self.show_cursor_cross:
            try:
                self.horz_line.set_visible(False)
            except AttributeError:
                for axes in self.axes:
                    self.horz_line = axes.axhline(axes.get_ybound()[0], visible=False, **lineprops)

            try:
                self.vert_line.set_visible(False)
            except AttributeError:
                for axes in self.axes:
                    self.vert_line = axes.axvline(axes.get_xbound()[0], visible=False, **lineprops)

            self.horz_line.set_color(self.plot_parameters['grid_color'])
            self.horz_line.set_linewidth(self.plot_parameters['grid_line_width'])
            self.vert_line.set_color(self.plot_parameters['grid_color'])
            self.vert_line.set_linewidth(self.plot_parameters['grid_line_width'])

        self.show_cursor_cross = self.plot_parameters['grid_show']
        self.crossoverpercent = self.plot_parameters['zoom_crossover_sensitivity']

    def update_extents(self, data_lims=None):
        if data_lims is None:
            self.data_lims = GetStart(self.axes)
        else:
            self.data_lims = data_lims

    def update_y_extents(self, y_min, y_max):
        self.data_lims[1] = y_min
        self.data_lims[3] = y_max

    def update_mark_state(self, state):
        self.mark_annotation = state

    def on_pick_event(self, event):
        " Store which text object was picked and were the pick event occurs."

        if isinstance(event.artist, Text):
            self.dragged = event.artist
            self.pick_pos = (event.mouseevent.xdata, event.mouseevent.ydata)

        return True

    def new_axes(self, axes, rectprops=None):
        self.axes = axes
        if self.canvas is not axes[0].figure.canvas:
            for cid in self.cids:
                self.canvas.mpl_disconnect(cid)
            self.canvas = axes[0].figure.canvas

            self.cids.append(self.canvas.mpl_connect('pick_event', self.on_pick_event))

            self.cids.append(self.canvas.mpl_connect('button_press_event', self.press))
            self.cids.append(self.canvas.mpl_connect('button_release_event', self.release))
            self.cids.append(self.canvas.mpl_connect('draw_event', self.update_background))
            self.cids.append(self.canvas.mpl_connect('motion_notify_event', self.OnMotion))
            self.cids.append(self.canvas.mpl_connect('motion_notify_event', self.onKeyState))

            self.cids.append(self.canvas.mpl_connect('key_press_event', self.onKeyState))
            self.cids.append(self.canvas.mpl_connect('key_release_event', self.onKeyState))

            # new
            self.cids.append(self.canvas.mpl_connect('axes_enter_event', self.onEnterAxes))
            self.cids.append(self.canvas.mpl_connect('axes_leave_event', self.onLeaveAxes))
            self.cids.append(self.canvas.mpl_connect('scroll_event', self.onWheelEvent))

        if rectprops is None:
            rectprops = dict(facecolor='white',
                             edgecolor='black',
                             alpha=0.5,
                             fill=False)
        self.rectprops = rectprops

        # Pre-set keys
        self.shiftKey = False
        self.ctrlKey = False
        self.altKey = False
        self.wheel = False
        self.keyPress = False
        self.addToTable = False
        self.buttonDown = False

        for axes in self.axes:
            self.to_draw.append(Rectangle((0, 0), 0, 1, visible=False, **self.rectprops))

        self.show_cursor_cross = self.plot_parameters['grid_show']
#         if self.show_cursor_cross:
        lineprops = {}
        if self.useblit:
            lineprops['animated'] = True
        lineprops['color'] = self.plot_parameters['grid_color']
        lineprops['linewidth'] = self.plot_parameters['grid_line_width']

        for axes in self.axes:
            self.horz_line = axes.axhline(axes.get_ybound()[0], visible=False, **lineprops)
            self.vert_line = axes.axvline(axes.get_xbound()[0], visible=False, **lineprops)

        for axes, to_draw in zip(self.axes, self.to_draw):
            axes.add_patch(to_draw)

    def onEnterAxes(self, evt=None):
        self.insideAxes = True

    def onLeaveAxes(self, evt=None):
        self.insideAxes = False
        for axes in self.axes:
            xmin, xmax = axes.get_xlim()
            ymin, ymax = axes.get_ylim()
        x_diff = xmax - xmin
        y_diff = ymax - ymin

        x_left = ((xmax - evt.xdata) / x_diff)
        x_right = ((evt.xdata - xmin) / x_diff)
        y_bottom = ((ymax - evt.ydata) / y_diff)
        y_top = ((evt.ydata - ymin) / y_diff)

        max_value = np.max([x_right, x_left, y_bottom, y_top])

        if len(self.lastXY) != 0:
            if x_right == max_value:
                self.exitLoc = 'right'
                self.lastXY[1] = xmax
            elif x_left == max_value:
                self.exitLoc = 'left'
                self.lastXY[0] = xmin
            elif y_bottom == max_value:
                self.exitLoc = 'bottom'
                self.lastXY[2] = ymin
            elif y_top == max_value:
                self.exitLoc = 'top'
                self.lastXY[3] = ymax

        # find ymax for specific x axis range
        if not self.plotName in ['2D', 'RMSD', 'RMSF', 'Matrix']:
            try:
                for axes in self.axes:
                    xmin, xmax = axes.get_xlim()
                    # use first line only
                    line = axes.lines[0]
                    xlist = line.get_xdata()
                    ylist = line.get_ydata()
                    xylist = np.rot90(np.array([xlist, ylist]))
                    self.current_ymax = getMaxFromRange(xylist, xmin, xmax)
            except Exception:
                pass

    def onWheelEvent(self, evt):

        # Ignore wheel if trying to measure
        if wx.GetKeyState(wx.WXK_ALT) or not self.insideAxes:
            return

        # Update cursor
        motion_mode = [self.shiftKey, self.ctrlKey, self.altKey,
                       self.addToTable, True, self.buttonDown,
                       self.dragged]
        pub.sendMessage('motion_mode', dataOut=motion_mode)

        if self.allowWheel:
            # The actual work
            for axes in self.axes:
                x0, x1 = axes.get_xlim()
                y0, y1 = axes.get_ylim()

                if self.data_lims is not None:
                    xmin, ymin, xmax, ymax = self.data_lims
                else:
                    xmin, ymin, xmax, ymax = axes.data_lims

                # Zoom in X-axis only
                if not wx.GetKeyState(wx.WXK_SHIFT):
                    # calculate diff
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
                        pub.sendMessage('change_zoom_dtms', xmin=newXmin, xmax=newXmax, ymin=ymin, ymax=ymax)

                # Zoom in Y-axis only
                elif wx.GetKeyState(wx.WXK_SHIFT):
                    # Check if its 1D plot
                    if self.plotName in ['1D', 'CalibrationDT', 'MS']:
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
                    elif self.plotName != '1D':
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

    def onRebootKeyState(self, evt):
        """
        This function is only necessary in cases where the keys get stuck.
        """

        self.ctrlKey = False
        self.altKey = False
        self.shiftKey = False
        self.buttonDown = False
        self.addToTable = False

        if evt != None:
            evt.Skip()

    def onKeyState(self, evt):

        # check keys
        self.ctrlKey = wx.GetKeyState(wx.WXK_CONTROL)
        self.altKey = wx.GetKeyState(wx.WXK_ALT)
        self.shiftKey = wx.GetKeyState(wx.WXK_SHIFT)
        self.addToTable = False
        self.crossoverpercent = self.plot_parameters['zoom_crossover_sensitivity']

        if self.ctrlKey:
            if self.plotName in ['1D', 'MS']:
                self.crossoverpercent = self.plot_parameters['extract_crossover_sensitivity_1D']
            else:
                self.crossoverpercent = self.plot_parameters['extract_crossover_sensitivity_2D']

        self.keyPress = False
        if any((self.ctrlKey, self.shiftKey, self.altKey)):
            self.keyPress = True

        motion_mode = [self.shiftKey, self.ctrlKey, self.altKey,
                       self.addToTable, self.wheel, self.buttonDown,
                       self.dragged]
        pub.sendMessage('motion_mode', dataOut=motion_mode)

#     def onChangeLabels(self):
#         # get labels
#         for axes in self.axes:
#             xlabel = axes.get_xlabel()
#             xticks = axes.get_xticklabels()
#             ylabel = axes.get_ylabel()
#             yticks = axes.get_yticklabels()
#
#         yvals = []
#         ypositions = []
#         for ytick in yticks:
#             yvals.append(str2num(ytick.get_text()))
#             ypositions.append(ytick.get_position())
# #             print(ytick.get_text(), ytick.get_position())
#
#         yvals = np.asarray(yvals)
#         yscaler, expo = xy_range_divider(values=yvals)
#
#         for axes in self.axes:
#             axes.set_yticklabels(yvals * yscaler)
#
#         self.canvas.draw()

    def update_background(self, evt):
        'force an update of the background'
        if self.useblit:
            self.background = self.canvas.copy_from_bbox(self.canvas.figure.bbox)

    def ignore(self, evt):
        'return True if event should be ignored'

        # If ZoomBox is not active :
        if not self.active:
            return True

        # If canvas was locked
        if not self.canvas.widgetlock.available(self):
            return True

        if self.validButtons is not None:
            if evt.button in self.validButtons and not self.keyPress:
                pass
            elif evt.button in self.validButtons and self.ctrlKey:
                self.addToTable = True
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

        # If a button pressed, check if the release-button is the same
        return (evt.inaxes not in self.axes or
                evt.button != self.eventpress.button)

    def press(self, evt):
        'on button press event'

        if not self.insideAxes:
            if evt.dblclick and not self.shiftKey:
                self.reset_axes(axis_pos=self.exitLoc)
            elif evt.dblclick and self.shiftKey and self.exitLoc in ['left', 'right']:
                if self.current_ymax == None:
                    return
                for axes in self.axes:
                    axes.set_ylim(0, self.current_ymax)
                self.canvas.draw()
                return

        if self.dragged is not None: pass

        # Is the correct button pressed within the correct axes?
        if self.ignore(evt):
            return

        self.buttonDown = True

        pub.sendMessage('change_x_axis_start', startX=evt.xdata)
        self.startX = evt.xdata

        # make the drawed box/line visible get the click-coordinates, button, ...
        for to_draw in self.to_draw:
            to_draw.set_visible(self.visible)

        self.eventpress = evt

        return False

    def reset_axes(self, axis_pos):
        if self.data_lims is not None:
            xmin, ymin, xmax, ymax = self.data_lims
            xmin, ymin, xmax, ymax = self._check_xy_values(xmin, ymin, xmax, ymax)

        # Register a click if zoomout was not necessary
        for axes in self.axes:
            if self.data_lims is None:
                xmin, ymin, xmax, ymax = axes.data_lims
                xmin, ymin, xmax, ymax = self._check_xy_values(xmin, ymin, xmax, ymax)

            if axis_pos in ['left', 'right']:
                axes.set_ylim(ymin, ymax)
            elif axis_pos in ['top', 'bottom']:
                axes.set_xlim(xmin, xmax)
                if self.plotName == 'RMSF':
                    pub.sendMessage('change_zoom_rmsd', xmin=xmin, xmax=xmax)
            ResetVisible(axes)
            self.canvas.draw()

    def _check_xy_values(self, xmin, ymin, xmax, ymax):
        if xmin > xmax: xmin, xmax = xmax, xmin
        if ymin > ymax: ymin, ymax = ymax, ymin
        # assure that x and y values are not equal
        if xmin == xmax: xmax = xmin * 1.0001
        if ymin == ymax: ymax = ymin * 1.0001

        return xmin, ymin, xmax, ymax

    def release(self, evt):
        'on button release event'
        if self.eventpress is None or (self.ignore(evt) and not self.buttonDown):
            return
        self.buttonDown = False

        pub.sendMessage('change_x_axis_start', startX=None)

        # make the box/line invisible again
        for to_draw in self.to_draw:
            to_draw.set_visible(False)

        # When shift is pressed, it won't zoom
        if wx.GetKeyState(wx.WXK_ALT):
            self.eventpress = None  # reset the variables to their
            self.eventrelease = None  # inital values
            self.canvas.draw()  # redraw image
            return

        try:
            if self.dragged is not None:
                old_pos = self.dragged.get_position()
                new_pos = (old_pos[0] + evt.xdata - self.pick_pos[0],
                           old_pos[1] + evt.ydata - self.pick_pos[1])
                self.dragged.set_position(new_pos)
                if self.dragged.obj_name is not None:
                    pub.sendMessage('update_text_position', text_obj=self.dragged)
                self.dragged = None
                self.canvas.draw()  # redraw image
                return
        except Exception as e:
            self.dragged = None
            self.canvas.draw()  # redraw image

        # left-click + ctrl OR double left click reset axes
        if self.eventpress.dblclick:

            if self.data_lims is not None:
                xmin, ymin, xmax, ymax = self.data_lims
                xmin, ymin, xmax, ymax = self._check_xy_values(xmin, ymin, xmax, ymax)

            # Check if a zoom out is necessary
            zoomout = False
            for axes in self.axes:
                if self.data_lims is None:
                    xmin, ymin, xmax, ymax = axes.data_lims
                    xmin, ymin, xmax, ymax = self._check_xy_values(xmin, ymin, xmax, ymax)
                if axes.get_xlim() != (xmin, xmax) and axes.get_ylim() != (ymin, ymax):
                    zoomout = True
            # Register a click if zoomout was not necessary
            if not zoomout:
                if evt.button == 1:
                    pub.sendMessage('left_click', xpos=evt.xdata, ypos=evt.ydata)

            for axes in self.axes:
                if self.data_lims is None:
                    xmin, ymin, xmax, ymax = axes.data_lims
                    xmin, ymin, xmax, ymax = self._check_xy_values(xmin, ymin, xmax, ymax)

                if wx.GetKeyState(wx.WXK_SHIFT):
                    axes.set_ylim(ymin, ymax)
                elif wx.GetKeyState(wx.WXK_CONTROL):
                    axes.set_xlim(xmin, xmax)
                else:
                    axes.set_xlim(xmin, xmax)
                    axes.set_ylim(ymin, ymax)
                ResetVisible(axes)

            if self.plotName == 'RMSF':
                pub.sendMessage('change_zoom_rmsd', xmin=xmin, xmax=xmax)
            elif self.plotName == "MSDT":
                pub.sendMessage('change_zoom_dtms', xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

            self.canvas.draw()
            return

        # left-click sends data from current point
        elif self.eventpress.xdata == evt.xdata and self.eventpress.ydata == evt.ydata:
            if not wx.GetKeyState(wx.WXK_CONTROL):
                # Ignore the resize if the control key is down
                if evt.button == 1:
                    pub.sendMessage('left_click', xpos=evt.xdata, ypos=evt.ydata)
                return

        self.canvas.draw()
        # release coordinates, button, ...
        self.eventrelease = evt

        if self.addToTable and not self.preventExtraction:
            xmin, ymin = self.eventpress.xdata, self.eventpress.ydata
            xmax, ymax = self.eventrelease.xdata, self.eventrelease.ydata

            # A dirty way to prevent users from trying to extract data from the wrong places
            if not self.mark_annotation:
                if self.plotName in ['MSDT', "2D"] and (self.eventpress.xdata != evt.xdata and
                                                        self.eventpress.ydata != evt.ydata):
                    pub.sendMessage('extract_from_plot_2D', dataOut=[xmin, xmax, ymin, ymax])
                elif self.plotName != 'CalibrationDT' and self.eventpress.xdata != evt.xdata:
                    pub.sendMessage('extract_from_plot_1D', xvalsMin=xmin, xvalsMax=xmax, yvalsMax=ymax)
            else:
                pub.sendMessage('mark_annotation', xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

        if self.spancoords == 'data':
            xmin, ymin = self.eventpress.xdata, self.eventpress.ydata
            xmax, ymax = self.eventrelease.xdata or self.prev[0], self.eventrelease.ydata or self.prev[1]
        elif self.spancoords == 'pixels':
            xmin, ymin = self.eventpress.x, self.eventpress.y
            xmax, ymax = self.eventrelease.x, self.eventrelease.y
        else:
            raise ValueError('spancoords must be "data" or "pixels"')

        # assure that min<max values
        if xmin > xmax: xmin, xmax = xmax, xmin
        if ymin > ymax: ymin, ymax = ymax, ymin
        # assure that x and y values are not equal
        if xmin == xmax: xmax = xmin * 1.0001
        if ymin == ymax: ymax = ymin * 1.0001

        # Switch to span if a small delta y is used
        # Note: trying something new - if mouse exits the plot area,
        #       the values won't be fully reset to the data limits but
        #       the last values
        try:
            y0, y1 = evt.inaxes.get_ylim()
        except Exception as __:
            for axes in self.axes:
                y0, y1 = axes.get_ylim()

        # new
        try:
            x0, x1 = evt.inaxes.get_xlim()
        except Exception as __:
            for axes in self.axes:
                x0, x1 = axes.get_xlim()

        if ymin == None:
            ymin = self.data_lims[1]
        if xmin == None:
            xmin = self.data_lims[0]

        if not self.insideAxes:
            if self.exitLoc == 'left':
                xmin = self.lastXY[0]
            elif self.exitLoc == 'right':
                xmax = self.lastXY[1]
            elif self.exitLoc == 'bottom':
                ymin = self.lastXY[2]
            elif self.exitLoc == 'top':
                ymax = self.lastXY[3]

        # Check if crossover is large enough
        if ymax - ymin < (y1 - y0) * self.crossoverpercent:
            ymax = y1
            ymin = y0
        elif xmax - xmin < (x1 - x0) * self.crossoverpercent:
            xmax = x1
            xmin = x0

        spanx = xmax - xmin
        spany = ymax - ymin
        xproblems = self.minspanx is not None and spanx < self.minspanx
        yproblems = self.minspany is not None and spany < self.minspany
        if (xproblems or yproblems):
            """Box too small"""
            # check if shown distance (if it exists) is
            print('Distance too small')
            return

        # This controls whether we will zoom in
        # If addToTable is true, we wont zoom but will show span/box
        if not self.addToTable:
            for axes in self.axes:
                # Box zoom
                if self.span == 'box':
                    axes.set_xlim((xmin, xmax))
                    axes.set_ylim((ymin, ymax))
                elif self.span == 'horizontal':
                    axes.set_xlim((xmin, xmax))
                elif self.span == 'vertical':
                    axes.set_ylim((ymin, ymax))

        if self.plotName == 'RMSF':
            pub.sendMessage('change_zoom_rmsd', xmin=xmin, xmax=xmax)
        elif self.plotName == "MSDT" and not self.addToTable:
            pub.sendMessage('change_zoom_dtms', xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

        self.canvas.draw()

        value = 0.0
        if self.onselect is not None and evt.inaxes.lines != []:
            # gather the values to report in a selection event
            value = []
            x0, y0, x1, y1 = evt.inaxes.dataLim.bounds
            dat = evt.inaxes.lines[0].get_ydata()
            npts = len(dat)
            indx = int(round((npts - 1) * (evt.xdata - x0) / (x1 - x0)))
            if indx > (npts - 1): indx = npts - 1
            if indx < 0: indx = 0
            for line in evt.inaxes.lines:
                dat = line.get_ydata()
                if indx < len(dat):
                    value.append(dat[indx])
            if value == []: value = 0.0

            self.onselect(xmin, xmax, value, ymin, ymax)  # zeros are for consistency with box zoom

        self.eventpress = None  # reset the variables to their
        self.eventrelease = None  # inital values

        # Reset zoom
        if self.addToTable:
            self.addToTable = False

        return False

    def update(self):
        'draw using newfangled blit or oldfangled draw depending on useblit'
        if self.useblit:
            if self.background is not None:
                self.canvas.restore_region(self.background)
            for axes, to_draw in zip(self.axes, self.to_draw):
                axes.draw_artist(to_draw)

            if self.show_cursor_cross:
                try:
                    for axes in self.axes:
                        axes.draw_artist(self.horz_line)
                        axes.draw_artist(self.vert_line)
                except Exception:
                    pass
            self.canvas.blit(self.canvas.figure.bbox)
        else:
            self.canvas.draw_idle()
        return False

    def OnMotion(self, evt):
        'on motion notify event if box/line is wanted'

        # send event
        pub.sendMessage('motion_xy', xpos=evt.xdata, ypos=evt.ydata, plotname=self.plotName)

        if self.eventpress is None or self.ignore(evt):
            return

        # actual position (with button still pressed)
        x, y = evt.xdata, evt.ydata

        if self.show_cursor_cross and (x is not None and y is not None):
            try:
                for axes in self.axes:
                    self.horz_line.set_ydata((y, y))
                    self.horz_line.set_visible(True)
                    self.vert_line.set_xdata((x, x))
                    self.vert_line.set_visible(True)
            except Exception:
                pass

        self.prev = x, y

        minx, maxx = self.eventpress.xdata, x  # click-x and actual mouse-x
        miny, maxy = self.eventpress.ydata, y  # click-y and actual mouse-y

        if minx is not None and maxx is not None and minx > maxx:
            minx, maxx = maxx, minx
        if miny is not None and maxy is not None and miny > maxy:
            miny, maxy = maxy, miny

        if self.insideAxes:
            self.lastXY = [minx, maxx, miny, maxy]
        else:
            try: minx, maxx, miny, maxy = self.lastXY
            except ValueError: return

        # Checks whether values are not empty (or are float)
        if not isinstance(minx, float) or not isinstance(maxx, float):
            return
        if not isinstance(miny, float) or not isinstance(maxy, float):
            return

        # Changes from a yellow box to a colored line
        for axes in self.axes:
            y0, y1 = axes.get_ylim()
            x0, x1 = axes.get_xlim()

        # X-axis line
        if abs(maxy - miny) < abs(y1 - y0) * self.crossoverpercent:
            self.span = 'horizontal'
            avg = (miny + maxy) / 2
            if y is not None and y > miny:
                avg = miny
            else:
                avg = maxy
            miny = avg
            maxy = avg
            for to_draw in self.to_draw:
                if wx.GetKeyState(wx.WXK_CONTROL):
                    to_draw.set_edgecolor(self.plot_parameters['extract_color'])
                    to_draw.set_linewidth(self.plot_parameters['extract_line_width'])
                    to_draw.set_alpha(0.9)
                    to_draw.set_linestyle('-')
                else:
                    to_draw.set_edgecolor(self.plot_parameters['zoom_color_horizontal'])
                    to_draw.set_linewidth(self.plot_parameters['zoom_line_width'])
                    to_draw.set_alpha(0.9)
                    to_draw.set_linestyle('-')

        # Y-axis line
        elif abs(maxx - minx) < abs(x1 - x0) * self.crossoverpercent:
            self.span = 'vertical'
            avg = (minx + maxx) / 2
            if x is not None and x > minx:
                avg = minx
            else:
                avg = maxx
            minx = avg
            maxx = avg
            for to_draw in self.to_draw:
                to_draw.set_edgecolor(self.plot_parameters['zoom_color_vertical'])
                to_draw.set_linewidth(self.plot_parameters['zoom_line_width'])
                to_draw.set_alpha(0.9)
                to_draw.set_linestyle('-')
        # box
        else:
            self.span = 'box'
            for to_draw in self.to_draw:
                if wx.GetKeyState(wx.WXK_CONTROL):
                    to_draw.set_edgecolor(self.plot_parameters['extract_color'])
                    to_draw.set_facecolor(self.plot_parameters['extract_color'])
                    to_draw.set_linewidth(self.plot_parameters['extract_line_width'])
                    to_draw.set_alpha(0.4)
                    to_draw.set_linestyle('--')
                else:
                    to_draw.set_edgecolor(self.plot_parameters['zoom_color_box'])
                    to_draw.set_facecolor(self.plot_parameters['zoom_color_box'])
                    to_draw.set_linewidth(self.plot_parameters['zoom_line_width'])
                    to_draw.set_alpha(0.2)
                    to_draw.set_linestyle('-')

        # set size parameters
        for to_draw in self.to_draw:
            to_draw.set_x(minx)  # set lower left of box
            to_draw.set_y(miny)
            to_draw.set_width(maxx - minx)  # set width and height of box
            to_draw.set_height(maxy - miny)

            # Send to main window
            pub.sendMessage('motion_range', dataOut=[minx, maxx, miny, maxy])

        value = 0.0
        if self.onmove_callback is not None and evt.inaxes.lines != []:
            # gather the values to report in a selection event
            value = []
            x0, y0, x1, y1 = evt.inaxes.dataLim.bounds
            dat = evt.inaxes.lines[0].get_ydata()
            npts = len(dat)
            indx = int(round((npts - 1) * (evt.xdata - x0) / (x1 - x0)))
            if indx > (npts - 1): indx = npts - 1
            if indx < 0: indx = 0
            for line in evt.inaxes.lines:
                dat = line.get_ydata()
                if indx < len(dat):
                    value.append(dat[indx])
            if value == []: value = 0.0
            self.onmove_callback(minx, maxx, value, miny, maxy)  # zeros are for consistency with box zoom

        self.update()
        return False

    def set_active(self, active):
        """ Use this to activate / deactivate the RectangleSelector

            from your program with an boolean variable 'active'.
        """
        self.active = active

    def get_active(self):
        """ to get status of active mode (boolean variable)"""
        return self.active

