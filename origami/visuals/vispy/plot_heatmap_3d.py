"""Plot 3d data"""
# Standard library imports
from typing import Tuple

# Third-party imports
import wx
import numpy as np
import vispy.scene as scene
from vispy import color as vp_color

# Local imports
from origami.utils.ranges import get_min_max
from origami.config.config import CONFIG


class _PlotHeatmap3d(scene.SceneCanvas):
    """Canvas class"""

    node = None
    base_plot = None
    base_xaxis = None
    base_yaxis = None
    base_zaxis = None

    def __init__(self, plot_id="", *args, **kwargs):
        scene.SceneCanvas.__init__(
            self, keys="interactive", show=False, bgcolor=CONFIG.heatmap_3d_background_color, *args, **kwargs
        )  # noqa
        self.unfreeze()
        self.view = self.central_widget.add_view()
        self.show()

        self.plot_id = plot_id
        self._xyz_indicator = None
        self._array, self._x, self._y = None, None, None
        self._x_label, self._y_label, self._z_label = None, None, None
        self.PLOT_TYPE = None

    @staticmethod
    def transform(x: np.ndarray, y: np.ndarray, array: np.ndarray):
        """Transform data to match the expected format"""
        x, y = y, x
        array = np.flipud(array)

        return x, y, array

    def set_opacity(self, opacity: float):
        """Set opacity of the plot"""
        self.base_plot.opacity = opacity
        self.base_plot.update()

    def set_clim(self, clim: Tuple[float, float]):
        """Set min/max of the plot"""
        # Note = this does not seem to do anything...
        self.base_plot.clim = clim
        self.base_plot.update()

    def set_axis_label_margin(self, dimensions: Tuple[str] = None):
        """Set min/max of the plot

        Parameters
        ----------
        dimensions : Tuple[str]
            dimension(s) to be updated. Values can be `x`, `y` or `z`. Values like (`x`, `z`) are permitted
        """
        if dimensions is None:
            return

        if not isinstance(dimensions, (list, tuple)):
            return

        for dimension in dimensions:
            if dimension == "x":
                self.clear_axes(self.base_xaxis)
                self.base_xaxis = None
            elif dimension == "y":
                self.clear_axes(self.base_yaxis)
                self.base_yaxis = None
            elif dimension == "z":
                self.clear_axes(self.base_zaxis)
                self.base_zaxis = None
        self._set_axes(self._array, self._x_label, self._y_label, self._z_label, transform=False, dimensions=dimensions)
        self.base_plot.update()

    def set_axis_font_size(self, font_size: int):
        """Set font size of the label"""
        for axes in [self.base_xaxis, self.base_yaxis, self.base_zaxis]:
            axes.axis_font_size = font_size
        self.base_plot.update()

    def set_axis_tick_size(self, font_size: int):
        """Set font size of the ticks"""
        for axes in [self.base_xaxis, self.base_yaxis, self.base_zaxis]:
            axes.tick_font_size = font_size
        self.base_plot.update()

    def set_axis_color(self, color: Tuple[float, float, float]):
        """Set color of the axes, ticks and label"""
        for axes in [self.base_xaxis, self.base_yaxis, self.base_zaxis]:
            axes.axis_color = color
            axes.tick_color = color
            axes.label_color = color
            axes.parent = self.view.scene
        self.base_plot.update()

    def set_background(self, background_color: Tuple[float, float, float]):
        """Set color of the background"""
        self.bgcolor = background_color  # noqa
        self.update()

    def set_colormap(self, colormap: str):
        """Set colormap on a transform"""
        array = self._array

        # create normalization
        cmap_norm = array / abs(np.amax(array))

        # convert colormap to color list
        c = vp_color.get_colormap(colormap).map(cmap_norm).reshape(array.shape + (-1,))
        c = c.flatten().tolist()
        # convert color list to ensure correct shape and size
        colors = list(map(lambda x, y, z, w: (x, y, z, w), c[0::4], c[1::4], c[2::4], c[3::4]))
        self.base_plot.mesh_data.set_vertex_colors(colors)
        self.base_plot.mesh_data_changed()

    def set_camera(self, center=(0.5, 0.5, 0.0)):
        """Setup camera"""
        # setup camera if one does not exist yet
        if not isinstance(self.view.camera, scene.TurntableCamera):
            self.view.camera = scene.TurntableCamera()
        self.view.camera.center = center

    def set_x_axis(self, label: str, scale_ratio: float):
        """Set x-axis"""
        y = self._y
        min_val, max_val = get_min_max(y)
        if self.base_xaxis is None or not isinstance(self.base_xaxis, scene.Axis):
            self.base_xaxis = scene.Axis(
                pos=[[scale_ratio, 0], [scale_ratio, 1]],
                domain=(min_val, max_val),
                tick_direction=(-1, 0),
                parent=self.view.scene,
                axis_label=label,
                axis_color=CONFIG.heatmap_3d_axis_color,
                tick_color=CONFIG.heatmap_3d_axis_color,
                text_color=CONFIG.heatmap_3d_axis_color,
                font_size=CONFIG.heatmap_3d_axis_font_size,
                tick_font_size=CONFIG.heatmap_3d_axis_tick_size,
                axis_label_margin=-CONFIG.heatmap_3d_axis_x_margin,
            )
        else:
            self.base_xaxis.domain = (min_val, max_val)
            self.base_xaxis.axis_label = label

    def set_y_axis(self, label: str, scale_ratio: float):
        """Set x-axis"""
        x = self._x
        min_val, max_val = get_min_max(x)
        if self.base_yaxis is None or not isinstance(self.base_yaxis, scene.Axis):
            self.base_yaxis = scene.Axis(
                pos=[[0, 0], [scale_ratio, 0]],
                domain=(min_val, max_val),
                tick_direction=(0, 1),
                axis_label=label,
                parent=self.view.scene,
                axis_color=CONFIG.heatmap_3d_axis_color,
                tick_color=CONFIG.heatmap_3d_axis_color,
                text_color=CONFIG.heatmap_3d_axis_color,
                font_size=CONFIG.heatmap_3d_axis_font_size,
                tick_font_size=CONFIG.heatmap_3d_axis_tick_size,
                axis_label_margin=-CONFIG.heatmap_3d_axis_y_margin,
            )
            # set y-axis translations
            self.base_yaxis.transform = scene.transforms.MatrixTransform()  # its actually an inverted xaxis
            self.base_yaxis.transform.rotate(180, (0, -1, 0))
            self.base_yaxis.transform.translate((scale_ratio, 0))
        else:
            self.base_yaxis.domain = (min_val, max_val)
            self.base_yaxis.axis_label = label

    def set_z_axis(self, label: str, scale_ratio: float):
        """Set x-axis"""
        array = self._array
        min_val, max_val = get_min_max(array)

        # always clear z-axis
        self.clear_axes(self.base_zaxis)
        if self.base_zaxis is None or not isinstance(self.base_zaxis, scene.Axis):
            self.base_zaxis = scene.Axis(
                pos=[[0, 0], [-1, 0]],
                domain=(min_val, max_val),
                tick_direction=(0, -1),
                parent=self.view.scene,
                axis_label=label,
                axis_color=CONFIG.heatmap_3d_axis_color,
                tick_color=CONFIG.heatmap_3d_axis_color,
                text_color=CONFIG.heatmap_3d_axis_color,
                font_size=CONFIG.heatmap_3d_axis_font_size,
                tick_font_size=CONFIG.heatmap_3d_axis_tick_size,
                axis_label_margin=-CONFIG.heatmap_3d_axis_z_margin,
            )

            # set z-axis translations
            self.base_zaxis.transform = scene.transforms.MatrixTransform()  # its actually an inverted xaxis
            self.base_zaxis.transform.rotate(90, (0, 1, 0))  # rotate cw around yaxis
            self.base_zaxis.transform.rotate(-45, (0, 0, 1))  # tick direction towards (-1,-1)
            self.base_zaxis.transform.translate((scale_ratio, 0))
        else:
            self.base_zaxis.domain = (min_val, max_val)
            self.base_zaxis.axis_label = label

    def _set_axes(
        self, array, x_label, y_label, z_label, transform: bool = True, dimensions: Tuple[str] = ("x", "y", "z")
    ):

        # calculate size and limits
        x_size, y_size = array.shape
        scale_ratio = x_size / y_size
        z_intensity = array.max()

        if transform:
            self.base_plot.transform = scene.transforms.MatrixTransform()
            self.base_plot.transform.scale([1 / (x_size / scale_ratio), 1 / y_size, 1 / z_intensity])

        # set axes
        if "x" in dimensions:
            self.set_x_axis(x_label, scale_ratio)
        if "y" in dimensions:
            self.set_y_axis(y_label, scale_ratio)
        if "z" in dimensions:
            self.set_z_axis(z_label, scale_ratio)
        self._x_label, self._y_label, self._z_label = x_label, y_label, z_label

    def plot_3d_surface(self, x, y, array, x_label: str = "", y_label: str = "", z_label: str = "", **kwargs):  # noqa
        """Plot data in 3D"""
        # set camera
        self.set_camera((0.5, 0.5, 0))

        # transform data to show it in correct manner
        x, y, array = self.transform(x, y, array)

        self.base_plot = scene.visuals.SurfacePlot(x=x, y=y, z=array, parent=self.view.scene)

        # set data
        self._array, self._x, self._y = array, x, y

        # set colormap
        self.set_colormap(CONFIG.heatmap_3d_colormap)
        self._set_axes(array, x_label, y_label, z_label)
        self.PLOT_TYPE = "heatmap-3d"

    def plot_3d_image(self, x, y, array, x_label: str = "", y_label: str = "", z_label: str = "", **kwargs):  # noqa
        """Plot data in 3D"""
        # set camera
        # self.set_camera((0.5, 0.5, 0))

        # transform data to show it in correct manner
        x, y, array = self.transform(x, y, array)

        self.base_plot = scene.visuals.Image(array, parent=self.view.scene)

        # set data
        self._array, self._x, self._y = array, x, y

        # set colormap
        self.view.camera = scene.PanZoomCamera()
        # self.view.camera.set_range()
        # self.set_colormap(CONFIG.heatmap_3d_colormap)
        self._set_axes(array, x_label, y_label, z_label)
        self.PLOT_TYPE = "heatmap-2d"

    def plot_3d_waterfall(self, x, y, array, x_label: str = "", y_label: str = "", z_label: str = "", **kwargs):  # noqa
        """Plot data in 3D"""
        # set camera
        # self.set_camera((0.5, 0.5, 0))

        # transform data to show it in correct manner
        x, y, array = self.transform(x, y, array)

        for i, _y in enumerate(array):
            line = scene.visuals.Line(np.c_[x, _y + i], parent=self.view.scene)
            line.transform = scene.transforms.STTransform()
        # self.base_plot = scene.visuals.Image(array, parent=self.view.scene)
        #
        # # set data
        # self._array, self._x, self._y = array, x, y
        #
        # # set colormap
        self.view.camera = scene.PanZoomCamera()
        self.view.camera.set_range()
        # self.set_colormap(CONFIG.heatmap_3d_colormap)
        # self._set_axes(array, x_label, y_label, z_label)
        self.PLOT_TYPE = "heatmap-2d"

    def plot_3d_update(self, x, y, array, x_label: str = "", y_label: str = "", z_label: str = "", **kwargs):  # noqa
        """Update plot data in 3D"""
        if self.base_plot is None or self._array is None:
            raise AttributeError("Base plot does not exist")

        if self._array.shape != array.shape:
            self.clear()
            raise AttributeError("Array shapes were different")

        # transform data to show it in correct manner
        x, y, array = self.transform(x, y, array)

        # update data
        self.base_plot.set_data(x, y, array)
        self._array, self._x, self._y = array, x, y

        # set colormap
        self.set_colormap(CONFIG.heatmap_3d_colormap)
        self._set_axes(array, x_label, y_label, z_label)

    def add_axes_indicator(self):
        """Add axes indicator"""
        # this would be quite useful if the indicator was only shown on user rotation/press and was shown in at the
        # center of mass
        if self._xyz_indicator is None:
            self._xyz_indicator = scene.XYZAxis()
            self._xyz_indicator.transform = scene.transforms.MatrixTransform()
            self._xyz_indicator.transform.scale([0.1, 0.1, 0.1])
            self._xyz_indicator.transform.translate((-1, -1, -1))

        self.view.add(self._xyz_indicator)

    @staticmethod
    def clear_axes(axes):
        """Clear axes"""
        if axes:
            axes.parent = None

    def clear(self):
        """Clear plot area"""
        if self.base_plot:
            self.base_plot.parent = None
            self.base_plot = None

        self.clear_axes(self.base_xaxis)
        self.base_xaxis = None
        self.clear_axes(self.base_yaxis)
        self.base_yaxis = None
        self.clear_axes(self.base_zaxis)
        self.base_zaxis = None

        self._array, self._x, self._y = None, None, None
        self._x_label, self._y_label, self._z_label = None, None, None


class PlotHeatmap3d(wx.Panel):
    """Plot handler"""

    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        self.SetBackgroundColour(wx.WHITE)
        self.canvas = _PlotHeatmap3d(app="wx", parent=self)

        # ensures size is correct
        self.Bind(wx.EVT_SIZE, self.on_resize)

        self.lock_plot_from_updating = False
        self.resize = False
        self.PLOT_TYPE = None

    def on_resize(self, evt):
        """Resize canvas"""
        w, h = self.GetSize()
        self.canvas.size = (w, h)
        evt.Skip()

    def clear(self):
        """Clear plot area"""
        self.canvas.clear()

    def repaint(self, repaint: bool = True):
        """Repaint plot"""
        if repaint:
            self.canvas.update()

    def can_update(self):
        """Check whether plot can be updated"""
        return self.canvas.base_plot is not None

    def savefig(self, path: str, **kwargs):  # noqa
        """Save figure"""
        from vispy.io import imsave

        image = self.canvas.render()
        extension = path.split(".")[-1]
        if extension in ["jpg", "jpeg", "pdf"]:
            image = image[:, :, 0:3]
        imsave(path, image)

    def copy_to_clipboard(self):
        """Copy figure buffer to clipboard"""
        raise ValueError("Not supported yet")


#         from PIL import Image
#         from io import BytesIO
#
#         with BytesIO() as bitmap:
#             with Image.fromarray(self.canvas.render()) as img:
#                 img.save(bitmap, "BMP")
#             bitmap = bitmap.getvalue()
#
#         bmp_obj = wx.BitmapDataObject()
#         bmp_obj.SetBitmap(bitmap)
#
#         array = self.canvas.render()
#         h, w, _ = array.shape
#
#         bitmap = wx.EmptyImage(w, h)
#         bitmap.SetData(array.tostring())
#
#         bmp_obj = wx.BitmapDataObject()
#         bmp_obj.SetBitmap(bitmap.ConvertToBitmap())
#
#         if not wx.TheClipboard.IsOpened():
#             open_success = wx.TheClipboard.Open()
#             if open_success:
#                 wx.TheClipboard.SetData(bmp_obj)
#                 wx.TheClipboard.Close()
#                 wx.TheClipboard.Flush()


def _main():
    class TestPanel(wx.Dialog):
        """Test panel"""

        btn_1 = None
        btn_2 = None

        def __init__(self, parent):
            wx.Dialog.__init__(self, parent, wx.ID_ANY, title="TEST DIALOG")

            plot_panel = wx.Panel(self)
            plot_window = PlotHeatmap3d(plot_panel)  # , plot_id=self.NAME)

            main_sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.Add(plot_window, 1, wx.EXPAND)
            plot_panel.SetSizer(main_sizer)
            main_sizer.Fit(plot_panel)

            main_sizer.Fit(self)
            self.SetSizerAndFit(main_sizer)
            self.CenterOnScreen()
            self.Show()

            array = np.random.randint(0, 1, (200, 200))
            array = array.astype(np.float32)

            x = np.arange(array.shape[0])
            y = np.arange(array.shape[1])
            plot_window.canvas.plot_3d_image(x, y, array)

    app = wx.App()
    frame = wx.Frame(None, -1)
    panel = TestPanel(frame)
    panel.ShowModal()
    app.MainLoop()


if __name__ == "__main__":
    _main()
