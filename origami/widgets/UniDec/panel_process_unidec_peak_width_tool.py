# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import numpy as np
import wx
from gui_elements.misc_dialogs import DialogBox
from help_documentation import OrigamiHelp
from processing.UniDec.unidec_modules.fitting import isolated_peak_fit
from processing.utils import get_narrow_data_range
from styles import makeTooltip
from styles import validator
from utils.converters import str2num
from visuals import mpl_plots


class PanelPeakWidthTool(wx.MiniFrame):
    """
    """

    def __init__(self, parent, presenter, config, **kwargs):
        wx.MiniFrame.__init__(
            self,
            parent,
            -1,
            "UniDec peak width tool...",
            size=(600, 500),
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),
        )
        self.config = config
        self.parent = parent
        self.presenter = presenter
        self.view = presenter.view
        self.panel_plot = self.view.panelPlots

        self.kwargs = kwargs
        self.help = OrigamiHelp()
        # make gui items
        self.make_gui()
        self.on_plot_MS(kwargs["xvals"], kwargs["yvals"])
        self.SetFocus()
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

    def on_key_event(self, evt):
        key_code = evt.GetKeyCode()
        # exit window
        if key_code == wx.WXK_ESCAPE:
            self.on_close(evt=None)
        elif key_code == 70:
            self.on_fit_peak(evt=None)

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def make_gui(self):
        # make panel
        panel = self.make_settings_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 0, wx.EXPAND, 0)

        # bind events
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)
        self.fitBtn.Bind(wx.EVT_BUTTON, self.on_fit_peak)
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

    def make_settings_panel(self):
        panel = wx.Panel(self, -1)

        self.plotMS = mpl_plots.plots(panel, figsize=(6, 3), config=self.config)

        msg = (
            "Note:\nIn order to determine peak width, \nplease zoom-in on a desired peak\n"
            + "select the desired fitting shape and press \n``Fit` or enter `F` on your keyboard."
        )
        info_txt = wx.StaticText(panel, wx.ID_ANY, msg)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        unidec_peakShape_label = wx.StaticText(panel, wx.ID_ANY, "Peak Shape:")
        self.unidec_peakFcn_choice = wx.Choice(
            panel, -1, choices=list(self.config.unidec_peakFunction_choices.keys()), size=(-1, -1)
        )
        self.unidec_peakFcn_choice.SetStringSelection(self.config.unidec_peakFunction)
        self.unidec_peakFcn_choice.Bind(wx.EVT_CHOICE, self.on_fit_peak)

        unidec_peakWidth_label = wx.StaticText(panel, wx.ID_ANY, "Peak FWHM (Da):")
        self.unidec_fit_peakWidth_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.unidec_fit_peakWidth_value.SetToolTip(makeTooltip("Expected peak width at FWHM in Da"))

        unidec_error_label = wx.StaticText(panel, wx.ID_ANY, "Error:")
        self.unidec_error = wx.StaticText(panel, wx.ID_ANY, "")
        unidec_resolution_label = wx.StaticText(panel, wx.ID_ANY, "Resolution (M/FWHM):")
        self.unidec_resolution = wx.StaticText(panel, wx.ID_ANY, "")

        self.fitBtn = wx.Button(panel, -1, "Fit", size=(-1, 22))
        self.fitBtn.SetToolTip(makeTooltip("Fit peak to currently zoomed peak in the spectrum"))

        self.ok_btn = wx.Button(panel, wx.ID_OK, "OK", size=(-1, 22))
        self.cancel_btn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        peak_grid = wx.GridBagSizer(2, 2)
        n = 0
        peak_grid.Add(info_txt, (n, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTRE_HORIZONTAL)
        n += 1
        peak_grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        peak_grid.Add(unidec_peakShape_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_peakFcn_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        peak_grid.Add(unidec_peakWidth_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_fit_peakWidth_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        peak_grid.Add(unidec_error_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_error, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        peak_grid.Add(unidec_resolution_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_resolution, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        peak_grid.Add(self.fitBtn, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.ok_btn, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        btn_grid.Add(self.cancel_btn, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(peak_grid, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(btn_grid, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(self.plotMS, 1, wx.ALIGN_CENTER | wx.EXPAND, 10)
        main_sizer.Add(sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_TOP, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def on_ok(self, evt):
        width = self.unidec_fit_peakWidth_value.GetValue()
        function = self.unidec_peakFcn_choice.GetStringSelection()
        if width == "" or width is None:
            DialogBox(exceptionTitle="Error", exceptionMsg="Could not complete action. `Fit` peaks first", type="Error")
            return

        width = str2num(width)
        self.parent.unidec_fit_peakWidth_value.SetValue(f"{width:.4f}")
        self.parent.unidec_peakFcn_choice.SetStringSelection(function)
        self.Destroy()

    def on_crop_data(self):
        xlimits = self.plotMS.plotMS.get_xlim()
        ms_spectrum = np.transpose([self.kwargs["xvals"], self.kwargs["yvals"]])
        ms_narrow = get_narrow_data_range(data=ms_spectrum, mzRange=xlimits)
        return ms_narrow, xlimits

    def on_fit_peak(self, evt):
        ms_narrow, xlimits = self.on_crop_data()
        peakfcn = self.config.unidec_peakFunction_choices[self.unidec_peakFcn_choice.GetStringSelection()]

        try:
            fitout, fit_yvals = isolated_peak_fit(ms_narrow[:, 0], ms_narrow[:, 1], peakfcn)
        except RuntimeError:
            print("Failed to fit a peak. Try again in larger window")
            return

        fitout = fitout[:, 0]
        width = fitout[0]
        resolution = ms_narrow[np.argmax(ms_narrow[:, 1]), 0] / fitout[0]
        error = np.sum((fit_yvals - ms_narrow[:, 1]) * (fit_yvals - ms_narrow[:, 1]))

        # setup labels
        self.unidec_resolution.SetLabel("{:.4f}".format(resolution))
        self.unidec_error.SetLabel("{:.4f}".format(error))
        self.unidec_fit_peakWidth_value.SetValue("{:.4f}".format(width))
        self.on_plot_MS_with_Fit(self.kwargs["xvals"], self.kwargs["yvals"], ms_narrow[:, 0], fit_yvals, xlimits)

    def on_plot_MS(self, msX, msY):
        # Build kwargs
        plt_kwargs = self.panel_plot._buildPlotParameters(plotType="1D")

        self.plotMS.clearPlot()
        self.plotMS.plot_1D(
            xvals=msX,
            yvals=msY,
            xlabel="m/z",
            #             ylabel='Intensity',
            axesSize=[0.15, 0.2, 0.7, 0.75],
            plotType="MS",
            **plt_kwargs,
        )
        self.plotMS.repaint()

    def on_plot_MS_with_Fit(self, xvals, yvals, fit_xvals, fit_yvals, xlimits=None, **kwargs):
        """
        """

        # Build kwargs
        plt_kwargs = self.presenter.view.panelPlots._buildPlotParameters(plotType="1D")

        # Plot MS
        self.plotMS.clearPlot()
        self.plotMS.plot_1D(
            xvals=xvals,
            yvals=yvals,
            xlabel="m/z",
            ylabel="Intensity",
            axesSize=[0.1, 0.2, 0.8, 0.75],
            plotType="MS",
            label="Raw",
            allowWheel=False,
            **plt_kwargs,
        )
        self.plotMS.plot_1D_add(fit_xvals, fit_yvals, color="red", label="Fit", setup_zoom=False)

        self.plotMS.plotMS.set_xlim(xlimits)
        self.plotMS.repaint()
