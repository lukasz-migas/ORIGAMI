"""Dialog to select parameters for data export"""
# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.styles import Dialog
from origami.styles import set_tooltip
from origami.styles import make_checkbox
from origami.styles import make_bitmap_btn
from origami.utils.path import check_path_exists
from origami.icons.assets import Icons
from origami.config.config import CONFIG
from origami.utils.converters import convert_cm_to_inch
from origami.utils.converters import convert_inch_to_cm

logger = logging.getLogger(__name__)


class DialogExportFigures(Dialog):
    """Batch export images"""

    folder_path = None
    folder_path_btn = None
    file_format_choice = None
    image_resolution = None

    image_transparency_check = None
    image_tight_check = None
    image_resize_check = None
    left_export_value = None
    bottom_export_value = None
    width_export_value = None
    height_cm_value = None
    width_cm_value = None
    height_inch_value = None
    width_inch_value = None
    height_export_value = None
    save_btn = None
    cancel_btn = None

    def __init__(self, parent, image_axes_size=None, image_axes_inch=None, default_path=None):
        Dialog.__init__(self, parent, title="Export figures....")

        # get screen dpi
        self.screen_dpi = wx.ScreenDC().GetPPI()
        self._icons = Icons()

        self.default_path = default_path

        self.make_gui()
        self.on_toggle_controls(None)

        # setup plot sizes
        self.on_setup_plot_parameters(image_axes_size=image_axes_size, image_axes_inch=image_axes_inch)
        self.on_apply_size_inch(None)
        self.setup()

        # setup layout
        self.CenterOnParent()
        self.Show(True)
        self.SetFocus()

    def setup(self):
        """Setup GUI"""
        if isinstance(self.default_path, str) and check_path_exists(self.default_path):
            self.folder_path.SetLabel(self.default_path)

    def on_close(self, evt, force: bool = False):
        """Destroy this frame"""
        CONFIG.image_folder_path = None
        if self.IsModal():
            self.EndModal(wx.ID_NO)
        else:
            self.Destroy()

    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self, -1, size=(-1, -1))

        self.folder_path = wx.TextCtrl(panel, -1, "", style=wx.TE_CHARWRAP, size=(350, -1))
        self.folder_path.SetLabel(str(CONFIG.data_folder_path))
        self.folder_path.Bind(wx.EVT_TEXT, self.on_apply)
        set_tooltip(self.folder_path, "Specify output path.")

        self.folder_path_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.folder)
        self.folder_path_btn.Bind(wx.EVT_BUTTON, self.on_get_path)
        set_tooltip(self.folder_path_btn, "Select output path.")

        file_format_choice = wx.StaticText(panel, wx.ID_ANY, "File format:")
        self.file_format_choice = wx.Choice(panel, -1, choices=CONFIG.imageFormatType, size=(-1, -1))
        self.file_format_choice.SetStringSelection(CONFIG.imageFormat)
        self.file_format_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        resolution_label = wx.StaticText(panel, wx.ID_ANY, "Resolution (DPI):")
        self.image_resolution = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=50, max=600, initial=0, inc=50, size=(-1, -1)
        )
        self.image_resolution.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.image_resolution.SetValue(CONFIG.dpi)

        transparency_label = wx.StaticText(panel, wx.ID_ANY, "Transparent:")
        self.image_transparency_check = make_checkbox(panel, "")
        self.image_transparency_check.SetValue(CONFIG.transparent)
        self.image_transparency_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.image_transparency_check, "If checked, the background of the image will be transparent.")

        tight_label = wx.StaticText(panel, wx.ID_ANY, "Tight margins:")
        self.image_tight_check = make_checkbox(panel, "")
        self.image_tight_check.SetValue(CONFIG.image_tight)
        self.image_tight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.image_tight_check, "If checked, the white margin around the plot area will be reduced.")

        resize_label = wx.StaticText(panel, wx.ID_ANY, "Resize:")
        self.image_resize_check = make_checkbox(panel, "")
        self.image_resize_check.SetValue(CONFIG.resize)
        self.image_resize_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.image_resize_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)
        set_tooltip(self.image_resize_check, "Tightly control the size and shape of the final plot")

        plot_size_export_label = wx.StaticText(panel, -1, "Export plot size (proportion)")
        left_export_label = wx.StaticText(panel, -1, "Left")
        self.left_export_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.01, size=(120, -1)
        )
        self.left_export_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        bottom_export_label = wx.StaticText(panel, -1, "Bottom")
        self.bottom_export_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.01, size=(120, -1)
        )
        self.bottom_export_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        width_export_label = wx.StaticText(panel, -1, "Width")
        self.width_export_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.05, size=(120, -1)
        )
        self.width_export_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        height_export_label = wx.StaticText(panel, -1, "Height")
        self.height_export_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=1, initial=0, inc=0.05, size=(120, -1)
        )
        self.height_export_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        # inches
        plot_size_inch_label = wx.StaticText(panel, -1, "Plot size (inch)")
        width_inch_label = wx.StaticText(panel, -1, "Width")
        self.width_inch_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=20, initial=0, inc=1, size=(120, -1)
        )
        self.width_inch_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_size_inch)
        self.width_inch_value.SetDigits(2)

        height_inch_label = wx.StaticText(panel, -1, "Height")
        self.height_inch_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=20, initial=0, inc=1, size=(120, -1)
        )
        self.height_inch_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_size_inch)
        self.height_inch_value.SetDigits(2)

        plot_size_cm_label = wx.StaticText(panel, -1, "Plot size (cm)")
        self.width_cm_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=50.8, initial=0, inc=0.5, size=(120, -1)
        )
        self.width_cm_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_size_cm)
        self.width_cm_value.SetDigits(2)

        self.height_cm_value = wx.SpinCtrlDouble(
            panel, -1, value=str(0), min=0.0, max=50.8, initial=0, inc=0.5, size=(120, -1)
        )
        self.height_cm_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply_size_cm)
        self.height_cm_value.SetDigits(2)

        self.save_btn = wx.Button(panel, wx.ID_OK, "Save figures", size=(-1, 22))
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save)

        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.save_btn, (n, 0), flag=wx.EXPAND)
        btn_grid.Add(self.cancel_btn, (n, 1), flag=wx.EXPAND)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(wx.StaticText(panel, -1, "Folder path:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.folder_path, (n, 1), wx.GBSpan(1, 5), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.folder_path_btn, (n, 6), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(file_format_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.file_format_choice, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(resolution_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.image_resolution, (n, 1), flag=wx.EXPAND | wx.ALIGN_LEFT)
        n += 1
        grid.Add(transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.image_transparency_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(tight_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.image_tight_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(resize_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.image_resize_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(left_export_label, (n, 1), flag=wx.ALIGN_CENTER)
        grid.Add(bottom_export_label, (n, 2), flag=wx.ALIGN_CENTER)
        grid.Add(width_export_label, (n, 3), flag=wx.ALIGN_CENTER)
        grid.Add(height_export_label, (n, 4), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(plot_size_export_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.left_export_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.bottom_export_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.width_export_value, (n, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.height_export_value, (n, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(width_inch_label, (n, 1), flag=wx.ALIGN_CENTER)
        grid.Add(height_inch_label, (n, 2), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(plot_size_inch_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.width_inch_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.height_inch_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(plot_size_cm_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.width_cm_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.height_cm_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_setup_plot_parameters(self, **kwargs):
        """Setup plot parameters"""
        image_axes_size = kwargs.get("image_axes_size", None)
        if image_axes_size is None:
            image_axes_size = CONFIG.image_axes_size

        self.left_export_value.SetValue(str(image_axes_size[0]))
        self.bottom_export_value.SetValue(str(image_axes_size[1]))
        self.width_export_value.SetValue(str(image_axes_size[2]))
        self.height_export_value.SetValue(str(image_axes_size[3]))

        image_size_inch = kwargs.get("image_size_inch", None)
        if image_size_inch is None:
            image_size_inch = CONFIG.image_size_inch

        self.width_inch_value.SetValue(str(image_size_inch[0]))
        self.height_inch_value.SetValue(str(image_size_inch[1]))

    def on_save(self, _evt):
        """Save event"""
        if not check_path_exists(CONFIG.image_folder_path):
            from origami.gui_elements.misc_dialogs import DialogBox

            dlg = DialogBox(
                "Incorrect input path",
                f"The folder path is set to `{CONFIG.image_folder_path}` or does not exist."
                + " Are you sure you would like to continue?",
                kind="Question",
            )
            if dlg == wx.ID_NO:
                return

        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Destroy()

    def on_get_path(self, _evt):
        """Get path"""
        dlg = wx.DirDialog(
            self, "Choose a folder where to save images", style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
        )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.folder_path.SetLabel(path)
            CONFIG.image_folder_path = path

    def on_apply(self, evt):
        """Update config"""
        CONFIG.dpi = self.image_resolution.GetValue()
        CONFIG.imageFormat = self.file_format_choice.GetStringSelection()
        CONFIG.transparent = self.image_transparency_check.GetValue()
        CONFIG.resize = self.image_resize_check.GetValue()
        CONFIG.image_folder_path = self.folder_path.GetValue()

        plot_axes_size = [
            self.left_export_value.GetValue(),
            self.bottom_export_value.GetValue(),
            self.width_export_value.GetValue(),
            self.height_export_value.GetValue(),
        ]

        CONFIG.image_axes_size = plot_axes_size

        if evt is not None:
            evt.Skip()

    def on_apply_size_inch(self, _evt):
        """Update plot size in inches"""
        plot_inch_size = [self.width_inch_value.GetValue(), self.height_inch_value.GetValue()]
        plot_cm_size = convert_inch_to_cm(plot_inch_size)

        CONFIG.image_size_inch = plot_inch_size
        CONFIG.image_size_cm = plot_cm_size
        CONFIG.image_size_px = [
            int(plot_inch_size[0] * self.screen_dpi[0]),
            int(plot_inch_size[1] * self.screen_dpi[1]),
        ]

        self.width_cm_value.SetValue(round(plot_cm_size[0], 2))
        self.height_cm_value.SetValue(round(plot_cm_size[1], 2))

    def on_apply_size_cm(self, _evt):
        """Update plot size in centimeters"""
        plot_cm_size = [self.width_cm_value.GetValue(), self.height_cm_value.GetValue()]
        plot_inch_size = convert_cm_to_inch(plot_cm_size)

        CONFIG.image_size_inch = plot_inch_size
        CONFIG.image_size_cm = plot_cm_size
        CONFIG.image_size_px = [
            int(plot_inch_size[0] * self.screen_dpi[0]),
            int(plot_inch_size[1] * self.screen_dpi[1]),
        ]
        self.width_inch_value.SetValue(round(plot_inch_size[0], 2))
        self.height_inch_value.SetValue(round(plot_inch_size[1], 2))

    def on_toggle_controls(self, _evt):
        """Enable/disable controls"""
        CONFIG.resize = self.image_resize_check.GetValue()
        for item in [
            self.left_export_value,
            self.bottom_export_value,
            self.width_export_value,
            self.height_export_value,
            self.width_inch_value,
            self.height_inch_value,
            self.width_cm_value,
            self.height_cm_value,
        ]:
            item.Enable(CONFIG.resize)


def _main():
    app = wx.App()
    ex = DialogExportFigures(None)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
