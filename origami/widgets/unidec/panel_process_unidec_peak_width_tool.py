"""Utility panel for UniDec panel"""
# Third-party imports
import wx

# Local imports
from origami.styles import MiniFrame
from origami.styles import Validator
from origami.config.config import CONFIG
from origami.utils.converters import str2num
from origami.gui_elements.helpers import make_tooltip
from origami.gui_elements.misc_dialogs import DialogBox
from origami.gui_elements.views.view_spectrum import ViewMassSpectrum

# from origami.processing.unidec_.fitting import isolated_peak_fit


class PanelPeakWidthTool(MiniFrame):
    """Utility tool to estimate peak width in the mass spectrum"""

    # module specific parameters
    HELP_LINK = "https://origami.lukasz-migas.com/"

    # ui elements
    unidec_peak_fcn_choice, unidec_fit_peak_width_value, unidec_error = None, None, None
    unidec_resolution, fit_btn, ok_btn, cancel_btn = None, None, None, None
    view_ms = None

    def __init__(self, parent, presenter, view, mz_obj=None):
        MiniFrame.__init__(
            self,
            parent,
            title="UniDec peak width tool...",
            size=(600, 500),
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),
        )
        self.parent = parent
        self.presenter = presenter
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

    @property
    def panel_plot(self):
        """Return handle to `panel_plot`"""
        return self.view.panelPlots

    def on_key_event(self, evt):
        """Handle key events"""
        key_code = evt.GetKeyCode()

        if key_code == 70:
            self.on_fit_peak(evt=None)
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
            CONFIG._plotSettings["MS"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=False,
            filename="mass-spectrum",
        )

        # self.plotMS = base.PlotBase(, figsize=(6, 3), config=CONFIG)

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

        width = str2num(width)
        self.parent.fit_peak_width_value.SetValue(f"{width:.4f}")
        self.parent.peak_shape_func_choice.SetStringSelection(function)
        self.Destroy()

    def on_crop_data(self):
        """Crop mass spectrum"""
        # xlimits = self.plotMS.plot_base.get_xlim()
        # ms_spectrum = np.transpose([self.kwargs["xvals"], self.kwargs["yvals"]])
        # ms_narrow = get_narrow_data_range(data=ms_spectrum, mzRange=xlimits)
        # return ms_narrow, xlimits

    def on_fit_peak(self, evt):
        """Fit MS peak"""
        # ms_narrow, xlimits = self.on_crop_data()
        # peakfcn = CONFIG.unidec_peakFunction_choices[self.unidec_peakFcn_choice.GetStringSelection()]
        #
        # try:
        #     fitout, fit_yvals = isolated_peak_fit(ms_narrow[:, 0], ms_narrow[:, 1], peakfcn)
        # except RuntimeError:
        #     print("Failed to fit a peak. Try again in larger window")
        #     return
        #
        # fitout = fitout[:, 0]
        # width = fitout[0]
        # resolution = ms_narrow[np.argmax(ms_narrow[:, 1]), 0] / fitout[0]
        # error = np.sum((fit_yvals - ms_narrow[:, 1]) * (fit_yvals - ms_narrow[:, 1]))
        #
        # # setup labels
        # self.unidec_resolution.SetLabel("{:.4f}".format(resolution))
        # self.unidec_error.SetLabel("{:.4f}".format(error))
        # self.unidec_fit_peakWidth_value.SetValue("{:.4f}".format(width))
        # self.on_plot_ms_with_fit(self.kwargs["xvals"], self.kwargs["yvals"], ms_narrow[:, 0], fit_yvals, xlimits)

    def on_plot_ms(self, _evt):
        """Plot mass spectrum"""
        self.view_ms.plot(obj=self.mz_obj)

    def on_plot_ms_with_fit(self, xvals, yvals, fit_xvals, fit_yvals, xlimits=None, **kwargs):  # noqa
        """Plot mass spectrum with fit"""
        print(self)

        # # Build kwargs
        # plt_kwargs = self.presenter.view.panelPlots._buildPlotParameters(plotType="1D")
        #
        # # Plot MS
        # self.plotMS.clear()
        # self.plotMS.plot_1D(
        #     xvals=xvals,
        #     yvals=yvals,
        #     xlabel="m/z",
        #     ylabel="Intensity",
        #     axesSize=[0.1, 0.2, 0.8, 0.75],
        #     plotType="MS",
        #     label="Raw",
        #     allowWheel=False,
        #     **plt_kwargs,
        # )
        # self.plotMS.plot_1D_add(fit_xvals, fit_yvals, color="red", label="Fit", setup_zoom=False)
        #
        # self.plotMS.plot_base.set_xlim(xlimits)
        # self.plotMS.repaint()


def _main():
    app = wx.App()
    ex = PanelPeakWidthTool(None, None, None)
    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
