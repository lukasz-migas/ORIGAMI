import wx
import numpy as np
from help_documentation import OrigamiHelp
from visuals import mpl_plots
from styles import makeSuperTip, validator
from unidec_modules.fitting import isolated_peak_fit
from gui_elements.misc_dialogs import dlgBox
from utils.converters import str2num
from processing.utils import get_narrow_data_range


class panelPeakWidthTool(wx.MiniFrame):
    """
    """

    def __init__(self, parent, presenter, config, **kwargs):
        wx.MiniFrame.__init__(self, parent, -1, 'UniDec peak width tool...', size=(600, 500),
                              style=wx.DEFAULT_FRAME_STYLE & ~
                              (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.config = config
        self.presenter = presenter
        self.kwargs = kwargs
        self.help = OrigamiHelp()
        # make gui items
        self.make_gui()
        self.on_plot_MS(kwargs['xvals'], kwargs['yvals'])
        self.SetFocus()
        wx.EVT_CLOSE(self, self.on_close)

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()
    # ----

    def make_gui(self):
        # make panel
        panel = self.makeSelectionPanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 0)

        # bind events
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)
        self.fitBtn.Bind(wx.EVT_BUTTON, self.on_fit_peak)
        self.okBtn.Bind(wx.EVT_BUTTON, self.on_OK)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makeSelectionPanel(self):

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.plotMS = mpl_plots.plots(panel, figsize=(6, 3), config=self.config)

        unidec_peakShape_label = wx.StaticText(panel, wx.ID_ANY, "Peak Shape:")
        self.unidec_peakFcn_choice = wx.Choice(panel, -1, choices=list(self.config.unidec_peakFunction_choices.keys()),
                                               size=(-1, -1))
        self.unidec_peakFcn_choice.SetStringSelection(self.config.unidec_peakFunction)
        self.unidec_peakFcn_choice.Bind(wx.EVT_CHOICE, self.on_fit_peak)

        unidec_peakWidth_label = wx.StaticText(panel, wx.ID_ANY, "Peak FWHM (Da):")
        self.unidec_fit_peakWidth_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                                      validator=validator('floatPos'))
        _tip = makeSuperTip(self.unidec_fit_peakWidth_value, **self.help.unidec_peak_FWHM)

        unidec_error_label = wx.StaticText(panel, wx.ID_ANY, "Error:")
        self.unidec_error = wx.StaticText(panel, wx.ID_ANY, "")
        unidec_resolution_label = wx.StaticText(panel, wx.ID_ANY, "Resolution (M/FWHM):")
        self.unidec_resolution = wx.StaticText(panel, wx.ID_ANY, "")

        self.fitBtn = wx.Button(panel, -1, "Fit", size=(-1, 22))
        msg = "To determine peak width, please zoom-in on a desired peak, \n" + \
              "select peak shape and press fit. When you are finished, press on \n" + \
              "OK and continue."
        help_peak = {'help_title': 'Peak width fitting', 'help_msg': msg,
                     'header_img': None, 'header_line': True,
                     'footer_line': False}
        _tip = makeSuperTip(self.fitBtn, **help_peak)

        self.okBtn = wx.Button(panel, wx.ID_OK, "OK", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        peak_grid = wx.GridBagSizer(2, 2)
        n = 0
        peak_grid.Add(unidec_peakShape_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_peakFcn_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(unidec_peakWidth_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_fit_peakWidth_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(unidec_error_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_error, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(unidec_resolution_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_resolution, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(self.fitBtn, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        grid.Add(self.plotMS, (0, 0), wx.GBSpan(3, 2))
        grid.Add(peak_grid, (0, 3), wx.GBSpan(1, 2))
        grid.Add(self.okBtn, (3, 3), wx.GBSpan(1, 1))
        grid.Add(self.cancelBtn, (3, 4), wx.GBSpan(1, 1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

    def on_OK(self, evt):
        width = self.unidec_fit_peakWidth_value.GetValue()
        function = self.unidec_peakFcn_choice.GetStringSelection()
        if width == "" or width == None:
            dlgBox(exceptionTitle="Error",
                   exceptionMsg="Could not complete action. Pick peaks first?",
                   type="Error")
            return
        else:
            self.parent.unidec_fit_peakWidth_value.SetValue("{:.4f}".format(str2num(width)))
            self.parent.unidec_peakFcn_choice.SetStringSelection(function)
        self.Destroy()

    def on_crop_data(self):
        xlimits = self.plotMS.plotMS.get_xlim()
        ms_spectrum = np.transpose([self.kwargs['xvals'], self.kwargs['yvals']])
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
        self.on_plot_MS_with_Fit(self.kwargs['xvals'], self.kwargs['yvals'], ms_narrow[:, 0], fit_yvals, xlimits)

    def on_plot_MS(self, msX=None, msY=None, xlimits=None, override=True, replot=False,
                   full_repaint=False, e=None):

        # Build kwargs
        plt_kwargs = self.presenter.view.panelPlots._buildPlotParameters(plotType='1D')

        self.plotMS.clearPlot()
        self.plotMS.plot_1D(xvals=msX, yvals=msY,
                            xlimits=xlimits,
                            xlabel="m/z", ylabel="Intensity",
                            axesSize=[0.1, 0.2, 0.8, 0.75],
                            plotType='MS',
                            **plt_kwargs)
        # Show the mass spectrum
        self.plotMS.repaint()

    def on_plot_MS_with_Fit(self, xvals, yvals, fit_xvals, fit_yvals, xlimits=None, **kwargs):
        """

        """

        # Build kwargs
        plt_kwargs = self.presenter.view.panelPlots._buildPlotParameters(plotType='1D')

        # Plot MS
        self.plotMS.clearPlot()
        self.plotMS.plot_1D(xvals=xvals, yvals=yvals,
                            #                             xlimits=xlimits,
                            xlabel="m/z",
                            ylabel="Intensity",
                            axesSize=[0.1, 0.2, 0.8, 0.75],
                            plotType='MS', label="Raw",
                            allowWheel=False,
                            **plt_kwargs)
        self.plotMS.plot_1D_add(fit_xvals, fit_yvals, color="red", label="Fit", setup_zoom=False)

        self.plotMS.plotMS.set_xlim(xlimits)
        self.plotMS.repaint()
