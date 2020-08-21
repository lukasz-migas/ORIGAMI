"""Utility panel for UniDec panel"""
# Third-party imports
import wx
import numpy as np

# Local imports
from origami.styles import MiniFrame
from origami.styles import Validator
from origami.config.config import CONFIG
from origami.utils.converters import str2num
from origami.utils.exceptions import MessageError
from origami.gui_elements.helpers import make_tooltip
from origami.gui_elements.misc_dialogs import DialogBox
from origami.gui_elements.views.view_spectrum import ViewMassSpectrum
from origami.widgets.unidec.processing.fitting import isolated_peak_fit


class PanelPeakWidthTool(MiniFrame):
    """Utility tool to estimate peak width in the mass spectrum"""

    # module specific parameters
    HELP_LINK = "https://origami.lukasz-migas.com/"

    # ui elements
    unidec_peak_fcn_choice, unidec_fit_peak_width_value, unidec_error = None, None, None
    unidec_resolution, fit_btn, ok_btn, cancel_btn = None, None, None, None
    view_ms = None

    def __init__(self, parent, view, mz_obj=None):
        MiniFrame.__init__(
            self,
            parent,
            title="UniDec peak width tool...",
            size=(600, 500),
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),
        )
        self.parent = parent
        self.view = view
        self.mz_obj = mz_obj

        # make gui items
        self.make_gui()
        self.SetFocus()
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

        if self.mz_obj:
            self.on_plot_ms(None)
            self.on_zoom_on_base_peak()
            self.on_fit_peak(None)

    @property
    def panel_plot(self):
        """Return handle to `panel_plot`"""
        return self.view.panelPlots

    def on_key_event(self, evt):
        """Handle key events"""
        key_code = evt.GetKeyCode()

        if key_code == 70:  # F key
            self.on_fit_peak(None)
        else:
            super(PanelPeakWidthTool, self).on_key_event(evt)

    def on_right_click(self, _evt):
        """Right-click menu"""

        menu = self.view_ms.get_right_click_menu(self)
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def make_panel(self):
        """Make settings panel"""
        panel = wx.Panel(self, -1)

        # mass spectrum
        self.view_ms = ViewMassSpectrum(
            panel,
            (6, 4),  # CONFIG._plotSettings["MS"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=False,
            filename="mass-spectrum",
        )

        msg = (
            "Note:\nIn order to determine peak width, \nplease zoom-in on a desired peak\n"
            + "select the desired fitting shape and press \n``Fit` or enter `F` on your keyboard."
        )
        info_txt = wx.StaticText(panel, wx.ID_ANY, msg)

        unidec_peak_shape_label = wx.StaticText(panel, wx.ID_ANY, "Peak Shape:")
        self.unidec_peak_fcn_choice = wx.Choice(panel, -1, choices=CONFIG.unidec_panel_peak_func_choices, size=(-1, -1))
        self.unidec_peak_fcn_choice.SetStringSelection(CONFIG.unidec_panel_peak_func)
        self.unidec_peak_fcn_choice.Bind(wx.EVT_CHOICE, self.on_fit_peak)

        unidec_peak_width_label = wx.StaticText(panel, wx.ID_ANY, "Peak FWHM (Da):")
        self.unidec_fit_peak_width_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.unidec_fit_peak_width_value.SetToolTip(make_tooltip("Expected peak width at FWHM in Da"))

        unidec_error_label = wx.StaticText(panel, wx.ID_ANY, "Error:")
        self.unidec_error = wx.StaticText(panel, wx.ID_ANY, "")
        unidec_resolution_label = wx.StaticText(panel, wx.ID_ANY, "Resolution (M/FWHM):")
        self.unidec_resolution = wx.StaticText(panel, wx.ID_ANY, "")

        self.fit_btn = wx.Button(panel, -1, "Fit", size=(-1, -1))
        self.fit_btn.SetToolTip(make_tooltip("Fit peak to currently zoomed peak in the spectrum"))
        self.fit_btn.Bind(wx.EVT_BUTTON, self.on_fit_peak)

        self.ok_btn = wx.Button(panel, wx.ID_OK, "OK", size=(-1, -1))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        self.cancel_btn = wx.Button(panel, -1, "Cancel", size=(-1, -1))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        peak_grid = wx.GridBagSizer(2, 2)
        n = 0
        peak_grid.Add(info_txt, (n, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTRE_HORIZONTAL)
        n += 1
        peak_grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        peak_grid.Add(unidec_peak_shape_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_peak_fcn_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        peak_grid.Add(unidec_peak_width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_fit_peak_width_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        peak_grid.Add(unidec_error_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_error, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        peak_grid.Add(unidec_resolution_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_resolution, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        peak_grid.Add(self.fit_btn, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.ok_btn, 0, wx.EXPAND)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.cancel_btn, 0, wx.EXPAND)

        info_sizer = self.make_statusbar(panel, "right")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(peak_grid, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.AddStretchSpacer()
        sizer.Add(info_sizer, 0, wx.EXPAND)

        main_sizer = wx.BoxSizer()
        main_sizer.Add(self.view_ms.panel, 1, wx.EXPAND, 10)
        main_sizer.Add(sizer, 0, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def on_ok(self, evt):
        """Perform normal action"""
        width = self.unidec_fit_peak_width_value.GetValue()
        function = self.unidec_peak_fcn_choice.GetStringSelection()
        if width == "" or width is None:
            DialogBox(title="Error", msg="Could not complete action. `Fit` peaks first")
            return

        if self.parent is not None:
            width = str2num(width)
            self.parent.fit_peak_width_value.SetValue(f"{width:.4f}")
            self.parent.peak_shape_func_choice.SetStringSelection(function)
        super(PanelPeakWidthTool, self).on_ok(evt)

    def on_crop_data(self):
        """Crop mass spectrum"""
        x_min, x_max = self.view_ms.get_current_xlim()
        mz_obj = self.mz_obj.duplicate()
        mz_obj = mz_obj.crop(x_min, x_max)
        return mz_obj, (x_min, x_max)

    def on_fit_peak(self, _evt):
        """Fit MS peak"""
        mz_obj, x_limits = self.on_crop_data()
        peak_fcn = CONFIG.unidec_panel_peak_func_dict[self.unidec_peak_fcn_choice.GetStringSelection()]

        try:
            fit_out, fit_y = isolated_peak_fit(mz_obj.x, mz_obj.y, peak_fcn)
        except RuntimeError:
            raise MessageError("Error", "Failed to fit peak - try again using larger m/z window")

        fit_out = fit_out[:, 0]
        width = fit_out[0]

        xy = mz_obj.xy
        resolution = xy[np.argmax(xy[:, 1]), 0] / fit_out[0]
        error = np.sum((fit_y - xy[:, 1]) * (fit_y - xy[:, 1]))

        # setup labels
        self.unidec_resolution.SetLabel("{:.4f}".format(resolution))
        self.unidec_error.SetLabel("{:.4f}".format(error))
        self.unidec_fit_peak_width_value.SetValue("{:.4f}".format(width))
        self.on_plot_ms_with_fit(xy[:, 0], fit_y, x_limits)

    def on_plot_ms(self, _evt):
        """Plot mass spectrum"""
        self.view_ms.plot(obj=self.mz_obj)

    def on_plot_ms_with_fit(self, fit_x, fit_y, x_limits=None, **kwargs):  # noqa
        """Plot mass spectrum with fit"""
        self.view_ms.add_line(fit_x, fit_y, line_color=(1, 0, 0))

    def on_zoom_on_base_peak(self):
        """Zoom-in on base peak as the panel is loaded"""
        y_idx = np.argmax(self.mz_obj.y)
        x_pos = self.mz_obj.x[y_idx]
        self.view_ms.set_xlim(x_pos - 3, x_pos + 3)


def _main():
    from origami.handlers.load import LoadHandler

    path = r"D:\Data\ORIGAMI\text_files\MS_p27-FL-K31.csv"
    loader = LoadHandler()
    document = loader.load_text_mass_spectrum_document(path)
    mz_obj = document["MassSpectra/Summed Spectrum", True]

    app = wx.App()
    ex = PanelPeakWidthTool(None, None, None, mz_obj)
    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
