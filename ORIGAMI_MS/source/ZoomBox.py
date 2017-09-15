from matplotlib.patches import Rectangle
from wx.lib.pubsub import setupkwargs
from wx.lib.pubsub import pub

import numpy as np
import wx

# FIXME: This function doesn't quite work as it should. 
# If we left click and the right click it gets locked for some reason.
# Check why is this happening!
# TODO enable vertical line (i.e. scale low intensity ions!)

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
        else:
            pass
            # line.set_clip_on(False)
        try:
            yvals.append([np.amin(ydat), np.amax(ydat)])
            xvals.append([np.amin(xdat), np.amax(xdat)])
        except Exception, e:
            pass

    for p in axes.collections:
        try:
            xys = np.array(p.get_paths()[0].vertices)
        except IndexError:
            break
        offsets = p.get_offsets()
        if len(offsets) > 1:
            xys = np.array(offsets)
        ydat = xys[:, 1]
        xdat = xys[:, 0]
        if xmin is not None and xmax is not None:
            bool1 = np.all(np.array([xdat > xmin, xdat < xmax]), axis=0)
            ydat = ydat[bool1]
        try:
            yvals.append([np.amin(ydat), np.amax(ydat)])
            xvals.append([np.amin(xdat), np.amax(xdat)])
        except Exception, e:
            pass

    for patch in axes.patches:
        try:
            if (patch.get_width()) and (patch.get_height()):
                vertices = patch.get_path().vertices
                if vertices.size > 0:
                    xys = np.array(patch.get_patch_transform().transform(vertices))
                    ydat = xys[:, 1]
                    xdat = xys[:, 0]
                    if xmin is not None and xmax is not None:
                        bool1 = np.all(np.array([xdat > xmin, xdat < xmax]), axis=0)
                        ydat = ydat[bool1]
                    try:
                        yvals.append([np.amin(ydat), np.amax(ydat)])
                        xvals.append([np.amin(xdat), np.amax(xdat)])
                    except Exception, e:
                        pass
        except Exception, e:
            try:
                xys = patch.xy
                ydat = xys[:, 1]
                xdat = xys[:, 0]
                if xmin is not None and xmax is not None:
                    bool1 = np.all(np.array([xdat > xmin, xdat < xmax]), axis=0)
                    ydat = ydat[bool1]

                yvals.append([np.amin(ydat), np.amax(ydat)])
                xvals.append([np.amin(xdat), np.amax(xdat)])
            except Exception, e:
                pass

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
        if xmin == None or xmax == None:
            xmin = np.amin(np.ravel(xvals))
            xmax = np.amax(np.ravel(xvals))

        if xmin > xmax: xmin, xmax = xmax, xmin
        if ymin > ymax: ymin, ymax = ymax, ymin
        if xmin == xmax: xmax = xmin * 1.0001
        if ymin == ymax: ymax = ymin * 1.0001

        out = [xmin, ymin, xmax, ymax]
    else:
        out = axes.dataLim.bounds
    return out


def ResetVisible(axes):
    for line in axes.lines:
        line.set_clip_on(True)
    for t in axes.texts:
        t.set_visible(True)


def GetStart(axes):
    outputs = np.array([GetMaxes(axis) for axis in axes])
    # print "Outputs",outputs
    xmin = np.amin(outputs[:, 0])
    ymin = np.amin(outputs[:, 1])
    xmax = np.amax(outputs[:, 2])
    ymax = np.amax(outputs[:, 3])

    if xmin > xmax: xmin, xmax = xmax, xmin
    if ymin > ymax: ymin, ymax = ymax, ymin
    if xmin == xmax: xmax = xmin * 1.0001
    if ymin == ymax: ymax = ymin * 1.0001

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
        
        self.new_axes(axes)  

    def new_axes(self, axes):
        

        self.axes = axes
        if self.canvas is not axes[0].figure.canvas:
            for cid in self.cids:
                self.canvas.mpl_disconnect(cid)
                print('disconnected')
            self.canvas = axes[0].figure.canvas      
        
#         print(self.canvas.axes.get_xlim())
        
        for axes in self.axes:
            print(axes.get_xlim())
            
#         print('i am in')


class ZoomBox:
    """
    Select a min/max range of the x axes for a matplotlib Axes

    Example usage::

        from matplotlib.widgets import  RectangleSelector
        from pylab import *

        def onselect(xmin, xmax, value, ymin, ymax):
          'eclick and erelease are matplotlib events at press and release'
          print ' x,y min position : (%f, %f)' % (xmin, ymin)
          print ' x,y max position   : (%f, %f)' % (xmax, ymax)
          print ' used button   : ', eclick.button

        def toggle_selector(evt):
            print ' Key pressed.'
            if evt.key in ['Q', 'q'] and toggle_selector.RS.active:
                print ' RectangleSelector deactivated.'
                toggle_selector.RS.set_active(False)
            if evt.key in ['A', 'a'] and not toggle_selector.RS.active:
                print ' RectangleSelector activated.'
                toggle_selector.RS.set_active(True)

        x = arange(100)/(99.0)
        y = sin(x)
        fig = figure
        axes = subplot(111)
        axes.plot(x,y)

        toggle_selector.RS = ZoomBox(axes, onselect, drawtype='line')
        connect('key_press_event', toggle_selector)
        show()
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
                 data_lims=None):
#                  integrate=0, smash=0):

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
        self.crossoverpercent = 0.06
        self.axes = None
        self.canvas = None
        self.visible = True
        self.cids = []

        self.active = True  # for activation / deactivation
        self.to_draw = []
        self.background = None

        self.onselect = onselect
        self.onmove_callback = onmove_callback

        self.useblit = useblit
        self.minspanx = minspanx
        self.minspany = minspany

#         self.integrate = integrate
#         self.smash = smash

        if button is None or isinstance(button, list):
            self.validButtons = button
        elif isinstance(button, int):
            self.validButtons = [button]

        assert (spancoords in ('data', 'pixels'))

        self.spancoords = spancoords
        self.eventpress = None 
        self.eventrelease = None 

        self.new_axes(axes, rectprops)
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
#             print self.data_lims

    def new_axes(self, axes, rectprops=None):
        self.axes = axes
        if self.canvas is not axes[0].figure.canvas:
            for cid in self.cids:
                self.canvas.mpl_disconnect(cid)
                print('disconnected')
            self.canvas = axes[0].figure.canvas
#             self.cids.append(self.canvas.mpl_connect('motion_notify_event', self.OnMotion))
            self.cids.append(self.canvas.mpl_connect('button_press_event', self.press))
            self.cids.append(self.canvas.mpl_connect('button_release_event', self.release))
            self.cids.append(self.canvas.mpl_connect('draw_event', self.update_background))
            self.cids.append(self.canvas.mpl_connect('motion_notify_event', self.OnMotion))

        if rectprops is None:
            rectprops = dict(facecolor='white',
                             edgecolor='black',
                             alpha=0.5,
                             fill=False)
        self.rectprops = rectprops

        for axes in self.axes:
            self.to_draw.append(Rectangle((0, 0), 0, 1, visible=False, **self.rectprops))

        for axes, to_draw in zip(self.axes, self.to_draw):
            axes.add_patch(to_draw)

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
        
        
        # TO DO: When right click, enable extraction of mz or dt
        if self.validButtons is not None:
            if not evt.button in self.validButtons:
                if evt.button == 3:
#                     print('right click'); 
                    return True;
                elif evt.button == 2 and self.eventrelease is None:
#                     for axes in self.axes:
                    axes = self.axes[0]
                    Xvalues = axes.get_xlim()
                    Yvalues = axes.get_ylim()
                    
                    # Sends message to add data to table
                    pub.sendMessage('add2table', xvalsMin=Xvalues[0], xvalsMax=Xvalues[1], yvalsMax=Yvalues[1])
#                     pub.sendMessage('add2table', ((values)))
#                         pub.sendMessage('add2table', values[0], )
                    return True;
                else:
                    return False
                
                
#         # Only do selection if event was triggered with a desired button
#         if self.validButtons is not None:
#             if not evt.button in self.validButtons:
#                 if evt.button == 3 and self.integrate == 1:
#                     # print "rightclick"
#                     pub.sendMessage('integrate')
#                 elif evt.button == 3 and self.smash == 1:
#                     if evt.dblclick:
#                         pub.sendMessage('smash')
#                     else:
#                         pub.sendMessage('mzlimits')
#                 elif evt.button == 2:
#                     pub.sendMessage('middle_click')
#                 return True

        # If no button pressed yet or if it was out of the axes, ignore
        if self.eventpress is None:
            return evt.inaxes not in self.axes

        # If a button pressed, check if the release-button is the same
        return (evt.inaxes not in self.axes or
                evt.button != self.eventpress.button)

    def press(self, evt):
        'on button press event'
        # Is the correct button pressed within the correct axes?
        if self.ignore(evt): return

        self.buttonDown = True

        # make the drawed box/line visible get the click-coordinates,
        # button, ...
        for to_draw in self.to_draw:
            to_draw.set_visible(self.visible)
        self.eventpress = evt
        return False

    def release(self, evt):
        'on button release event'
        if self.eventpress is None or (self.ignore(evt) and not self.buttonDown): return
        self.buttonDown = False

        # make the box/line invisible again
        for to_draw in self.to_draw:
            to_draw.set_visible(False)

        # left-click in place resets the x-axis or y-axis
        if self.eventpress.xdata == evt.xdata and self.eventpress.ydata == evt.ydata:

            if wx.GetKeyState(wx.WXK_CONTROL):
                # Ignore the resize if the control key is down
                if evt.button == 1: #and self.smash == 1:
                    pub.sendMessage('left_click', xpos=evt.xdata, ypos=evt.ydata)
                return
            # x0,y0,x1,y1=GetMaxes(evt.inaxes)
            # print GetMaxes(evt.inaxes)

            xmin, ymin, xmax, ymax = self.data_lims
            if xmin > xmax: xmin, xmax = xmax, xmin
            if ymin > ymax: ymin, ymax = ymax, ymin
            # assure that x and y values are not equal
            if xmin == xmax: xmax = xmin * 1.0001
            if ymin == ymax: ymax = ymin * 1.0001

            # Check if a zoom out is necessary
            zoomout = False
            for axes in self.axes:
                if axes.get_xlim() != (xmin, xmax) and axes.get_ylim() != (ymin, ymax):
                    zoomout = True
            # Register a click if zoomout was not necessary
            if not zoomout:
                if evt.button == 1:  #and self.smash == 1:
                    pub.sendMessage('left_click', xpos=evt.xdata, ypos=evt.ydata)

            for axes in self.axes:
                axes.set_xlim(xmin, xmax)
                axes.set_ylim(ymin, ymax)
                ResetVisible(axes)

            self.canvas.draw()
            return

        self.canvas.draw()
        # release coordinates, button, ...
        self.eventrelease = evt

        if self.spancoords == 'data':
            xmin, ymin = self.eventpress.xdata, self.eventpress.ydata
            # xmax, ymax = self.eventrelease.xdata, self.eventrelease.ydata
            # fix for if drag outside axes boundaries
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
        try:
            y0, y1 = evt.inaxes.get_ylim()
        except Exception, e:
            y0, y1 = self.data_lims[1], self.data_lims[3]
        if ymax - ymin < (y1 - y0) * self.crossoverpercent:
            # print ymax,ymin,ymax-ymin,(y1-y0)*self.crossoverpercent
            ymax = y1
            ymin = y0
            spanflag = 1
        else:
            spanflag = 0

        spanx = xmax - xmin
        spany = ymax - ymin
        xproblems = self.minspanx is not None and spanx < self.minspanx
        yproblems = self.minspany is not None and spany < self.minspany
        if xproblems or yproblems:
            """Box too small"""  # check if drawed distance (if it exists) is
            return  # not to small in neither x nor y-direction

#         if wx.GetKeyState(wx.WXK_CONTROL):
#             # TODO: Send this signal up and drop it in a main GUI
#             # if the ctrl key is down, print out the difference and a guess for the Nanodisc mass assuming POPC
#             lmass = 760.076
#             charge = lmass / spanx
#             print spanx, charge, charge * xmax
#             return

        for axes in self.axes:
            axes.set_xlim((xmin, xmax))
            if spanflag == 1:
                xmin, ymin, xmax, ymax = GetMaxes(axes, xmin=xmin, xmax=xmax)
            axes.set_ylim((ymin, ymax))

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
        return False

    def update(self):
        'draw using newfangled blit or oldfangled draw depending on useblit'
        if self.useblit:
            if self.background is not None:
                self.canvas.restore_region(self.background)
            for axes, to_draw in zip(self.axes, self.to_draw):
                axes.draw_artist(to_draw)
            self.canvas.blit(self.canvas.figure.bbox)
        else:
            self.canvas.draw_idle()
        return False

    def OnMotion(self, evt):
#         pub.sendMessage('newxy', xpos=evt.xdata, ypos=evt.ydata)
        
        'on motion notify event if box/line is wanted'
        if self.eventpress is None or self.ignore(evt): return
        x, y = evt.xdata, evt.ydata  # actual position (with
        #   (button still pressed)

        self.prev = x, y

        minx, maxx = self.eventpress.xdata, x  # click-x and actual mouse-x
        miny, maxy = self.eventpress.ydata, y  # click-y and actual mouse-y
        if minx > maxx: minx, maxx = maxx, minx  # get them in the right order
        if miny > maxy: miny, maxy = maxy, miny
        
        # Checks whether values are not empty (or are float)
        if not isinstance(minx, float) or not isinstance(maxx, float): return
        if not isinstance(miny, float) or not isinstance(maxy, float): return
        
        # Changes from a yellow box to a colored line
        for axes in self.axes:
            y0, y1 = axes.get_ylim()
            
        if abs(maxy - miny) < abs(y1 - y0) * self.crossoverpercent:
            # print self.to_draw
            # print miny,maxy,y
            avg = (miny + maxy) / 2
            if y > miny:
                avg = miny
            else:
                avg = maxy
            miny = avg
            maxy = avg
            for to_draw in self.to_draw:
                to_draw.set_edgecolor('m')
                to_draw.set_linewidth(2.5)                
                to_draw.set_alpha(0.9)
        else:
            for to_draw in self.to_draw:
                to_draw.set_edgecolor('k')
                to_draw.set_alpha(0.2)
        for to_draw in self.to_draw:
            to_draw.set_x(minx)  # set lower left of box
            to_draw.set_y(miny)
            to_draw.set_width(maxx - minx)  # set width and height of box
            to_draw.set_height(maxy - miny)

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
