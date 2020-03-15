# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
# Local imports
# Local imports
# Local imports
from origami.icons.icons import IconContainer


class OrigamiHelp:
    def __init__(self):
        """
        Initilize help
        """
        # load icons
        self.icons = IconContainer()

        self._tool_tip_help()
        self._super_tip_help()

    def _tool_tip_help(self):

        msg = "A new window/tab in your prefered browser will open the playlist" + " with most recent ORIGAMI videos."
        self.link_youtube = msg

    def _super_tip_help(self):
        # some presets
        header_line = True
        footer_line = False

        # -----------
        # Peaklist panel
        msg = (
            "If checked, any data that was previously generated (i.e. combined)\n"
            + "will be overwritten with new dataset based on the selected parameters."
        )
        self.ionPanel_overwrite = {
            "help_title": "Overwriting previous results",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "If checked, any processing (i.e. combining collision voltage scans)\n"
            + "will be performed with parameters that are already retained within the\n"
            + "the ORIGAMI document. If these parameters are NOT present, parameters currently\n"
            + "entered in the ORIGAMI GUI will be used instead."
        )
        self.ionPanel_useInternalParams = {
            "help_title": "Use internal parameters",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }
        # -----------
        # Tandem MS panel
        msg = (
            "If checked, a mirror/butterfly plot will be generated with the\n"
            + "tandem MS on the top and a predicted spectrum on the bottom.\n"
            + "Fragments are annotated and the difference in m/z between the calculated\n"
            + "and measured peak is due to the error (always < than selected tolerance)."
        )
        self.tandem_butterfly = {
            "help_title": "Butterfly plots",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "Maximum number of labels that will be predicted for each m/z value in the peaklist.\n"
            + "If the value is above 1 (default), more than one fragment can corresponded to particular m/z\n"
            + "so please make sure that you've selected appropriate tolerance value!"
        )
        self.tandem_max_labels = {
            "help_title": "Butterfly plots",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        # -----------
        # Process panel (Extract)
        msg = (
            "Pusher frequency in microseconds. Only used when drift time values\n"
            + "are entered in miliseconds as the extraction program expects bins."
        )
        self.extract_pusherFreq = {
            "help_title": "Pusher frequency",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "Scan time in seconds. Only used when the retention time is entered in\n"
            + "scans as the extraction program expects minutes."
        )
        self.extract_scanTime = {
            "help_title": "Scan time",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "If checked, retention time will be assumed to be in scans rather\n" + "than in minutes."
        self.extract_in_scans = {
            "help_title": "Retention time units",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "If checked, drift time will be assumed to be miliseconds\n" + "rather than in bins."
        self.extract_in_ms = {
            "help_title": "Drift time units",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "Enter retention time values. Values typically in minutes."
        self.extract_rt = {
            "help_title": "Retention time",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "Enter drift time values. Values typically in bins."
        self.extract_dt = {
            "help_title": "Drift time",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "Enter m/z values."
        self.extract_mz = {
            "help_title": "Mass spectra",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        # -----------
        # Process panel (UniDec)
        msg = "Open a new HTML window with information about UniDec\n"
        self.unidec_about = {
            "help_title": "About UniDec",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "Minimum m/z of the data\n"
        self.unidec_min_mz = {
            "help_title": "Minimum m/z",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "Maximum m/z of the data\n"
        self.unidec_max_mz = {
            "help_title": "Maximum m/z",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "Minimum allowed charge state in the deconvolution\n"
        self.unidec_min_z = {
            "help_title": "Minimum charge state",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "Maximum allowed charge state in the deconvolution\n"
        self.unidec_max_z = {
            "help_title": "Maximum charge state",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "Minimum allowed mass in deconvolution\n"
        self.unidec_min_mw = {
            "help_title": "Minimum molecular weight",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "Maximum allowed mass in deconvolution\n"
        self.unidec_max_mw = {
            "help_title": "Maximum molecular weight",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "Sets the resolution of the zero-charge mass spectrum\n"
        self.unidec_mw_resolution = {
            "help_title": "Zero-charge spectrum resolution",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "Controls Linearization.\nConstant bin size (Da) for Linear m/z\nMinimum bin size (Da)"
            + " for Linear Resolution\nNumber of data points compressed together for Nonlinear\n"
        )
        self.unidec_linearization = {
            "help_title": "Linearization information",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "Expected peak at full width half maximum in m/z (Da)\n"
        self.unidec_peak_FWHM = {
            "help_title": "Peak width",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "Sort mass list by molecular weight or relative percentage"
        self.unidec_sort_mw_list = {
            "help_title": "Sort molecular weight list",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        # -----------
        # Process panel (MS)
        msg = (
            "If checked, when extracting several scans from the\n"
            + "chromatogram (RT) window, the mass spectra will be\n"
            + "binned according to the values shown below."
        )
        self.bin_MS_in_RT = {
            "help_title": "Linearization in chromatogram window",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "If checked, when loading a list of multiple files,\n"
            + "the mass spectra will be automatically binned\n"
            + "according to the values shown below."
        )
        self.bin_MS_when_loading_MML = {
            "help_title": "Linearization during loading Manual CIU dataset",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "The 'Process' button will use the currently selected dataset\n"
            + "and using the selected processing settings generate a new dataset which\n"
            + "will be added to the document."
        )
        self.process_mass_spectra_processesBtn = {
            "help_title": "Processing mass spectra...",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "The 'Replot' button will use the currently selected dataset\n"
            + "and replot the data while also applying the processing parameters.\n"
            + "This data will not be added to the document.\n"
        )
        self.process_mass_spectra_replotBtn = {
            "help_title": "Replotting mass spectra...",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }
        # -----------
        # Process panel (peak fitting)
        msg = (
            "If checked, the algorithm will attempt to predict the charge state of \n"
            + "found peaks. The algorithm looks for features in a narrow MS window \n"
            + "which can be usually found if the peak resolution is sufficiently high."
        )
        self.fit_highRes = {
            "help_title": "Predict charge states",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "If checked, isotopic peaks will be shown in the mass spectrum using\n"
            + "using red circles. Adjust window size, threshold and peak width for best results."
        )
        self.fit_showIsotopes = {
            "help_title": "Show isotopic peaks in mass spectrum",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }
        # -----------
        # Compare MS panel
        msg = (
            "If checked, each mass spectrum will be smoothed,\n"
            + "baseline subtracted and normalised. The type of preprocessing\n"
            + "depends on the parameters shown in the Process: Mass spectrum panel.\n"
            + "You can change these to obtain best results.\n"
        )
        self.compareMS_preprocess = {
            "help_title": "Pre-processing mass spectra",
            "help_msg": msg,
            "header_img": self.icons.iconsLib["process_ms_16"],
            "header_line": header_line,
            "footer_line": footer_line,
        }
        # -----------
        msg = "Opens new window with plot settings.\n"
        self.compareMS_open_plot1D_settings = {
            "help_title": "Editing plot parameters",
            "help_msg": msg,
            "header_img": self.icons.iconsLib["panel_plot1D_16"],
            "header_line": header_line,
            "footer_line": footer_line,
        }
        # -----------
        msg = "Opens new window with legend settings.\n"
        self.compareMS_open_legend_settings = {
            "help_title": "Editing legend parameters",
            "help_msg": msg,
            "header_img": self.icons.iconsLib["panel_legend_16"],
            "header_line": header_line,
            "footer_line": footer_line,
        }
        # -----------
        msg = "Opens new window with mass spectrum processing settings.\n"
        self.compareMS_open_processMS_settings = {
            "help_title": "Editing processing parameters",
            "help_msg": msg,
            "header_img": self.icons.iconsLib["process_ms_16"],
            "header_line": header_line,
            "footer_line": footer_line,
        }
        # -----------
        # Plotting panel - General settings
        msg = (
            "Please select which plot you would like to adjust. Names are simply the \n"
            + "representations shown as the tab names in the Plots panel."
        )
        self.general_plotName = {
            "help_title": "Plot options - plot name",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "The distance between the edge and the plot. Small values might not show labels.\n"
            + "Values are shown as a proportion of the window (0-1)."
        )
        self.general_leftAxes = {
            "help_title": "Plot options - left edge",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "The distance between the edge and the plot. Small values might not show labels.\n"
            + "Values are shown as a proportion of the window (0-1)."
        )
        self.general_bottomAxes = {
            "help_title": "Plot options - bottom edge",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "The width of the plot. This value compliments the LEFT edge.\n"
            + " When combined, it should not be larger than 1.\n"
            + "Values are shown as a proportion of the window (0-1)."
        )
        self.general_widthAxes = {
            "help_title": "Plot options - width",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "The height of the plot. This value compliments the BOTTOM edge.\n"
            + " When combined, it should not be larger than 1.\n"
            + "Values are shown as a proportion of the window (0-1)."
        )
        self.general_heightAxes = {
            "help_title": "Plot options - height",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "The distance between the edge and the plot. Small values might not show labels.\n"
            + "These value differ from the ones shown above, as the figure export size can differ,\n"
            + "from the one displayed in ORIGAMI GUI.\n"
            + "Values are shown as a proportion of the window (0-1)."
        )
        self.general_leftAxes_export = {
            "help_title": "Plot options - left edge",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "The distance between the edge and the plot. Small values might not show labels.\n"
            + "These value differ from the ones shown above, as the figure export size can differ,\n"
            + "from the one displayed in ORIGAMI GUI.\n"
            + "Values are shown as a proportion of the window (0-1)."
        )
        self.general_bottomAxes_export = {
            "help_title": "Plot options - bottom edge",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "The width of the plot. This value compliments the LEFT edge.\n"
            + "These value differ from the ones shown above, as the figure export size can differ,\n"
            + "from the one displayed in ORIGAMI GUI.\n"
            + " When combined, it should not be larger than 1.\n"
            + "Values are shown as a proportion of the window (0-1)."
        )
        self.general_widthAxes_export = {
            "help_title": "Plot options - width",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "The height of the plot. This value compliments the BOTTOM edge.\n"
            + "These value differ from the ones shown above, as the figure export size can differ,\n"
            + "from the one displayed in ORIGAMI GUI.\n"
            + " When combined, it should not be larger than 1.\n"
            + "Values are shown as a proportion of the window (0-1)."
        )
        self.general_heightAxes_export = {
            "help_title": "Plot options - height",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "The width of the plot in inches. Ensures consistent plot size when exporting figures."
        self.general_widthPlot_inch = {
            "help_title": "Plot options - width",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = "The height of the plot. Ensures consistent plot size when exporting figures."
        self.general_heightPlot_inch = {
            "help_title": "Plot options - height",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "The fraction at which the zooming tool changes from line to rectangle.\n"
            + "The lower the value, the more sensitive the zooming becomes. Default: 0.03"
        )
        self.general_zoom_crossover = {
            "help_title": "Zoom crossover sensitivity",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "When checked, figures will be automatically plotted when an appropriate item\n"
            + "was selected in the Document Tree."
        )
        self.general_instantPlot = {
            "help_title": "Instant plot",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "When checked, some of the 'slower' functions are exectured on a separate CPU thread\n"
            + "meaning the GUI will not get locked (unusable). While it has been extensively tested\n"
            + "this can still cause some problems and occasionally cause a crash."
        )
        self.general_multiThreading = {
            "help_title": "Multi-threading",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "When checked, a new log file will appear in the ORIGAMI folder which keeps track of all your\n"
            + "actions and in some cases, errors or warnings."
        )
        self.general_logToFile = {
            "help_title": "Log events to file",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }

        msg = (
            "When checked, settings will be automatically saved in the ORIGAMI directory\n"
            + "with the file name configOut.xml"
        )
        self.general_autoSaveSettings = {
            "help_title": "Auto-save settings",
            "help_msg": msg,
            "header_img": None,
            "header_line": header_line,
            "footer_line": footer_line,
        }


class HTMLHelp:
    def __init__(self):
        self.helpPages()

    def helpPages(self):
        fail_msg = """
        <h1>Not implemented yet</h1>
        <p><img src="images/fail.gif" width="404" height="313" /></p>
        """.strip()

        msg = """
        <p><strong>Overlaying items</strong></p>
        <p>ORIGAMI enables multiple overlay and comparison functions for mobilograms, chromatograms, mass spectra and
        two-dimensional heatmaps. These items are added to <strong>Comparison</strong> document which holds the
        input and output datasets, often pooled from multiple sources.</p>
        <p><strong>Overlaying mass spectra</strong></p>
        <p>Mass spectra can be overlayed from within the Multiple files panel where you can view either the
        <strong>raw</strong> data or pre-processed (just check the <strong>Pre-process mass spectra</strong>).
        Pre-processing parameters can be found under the Process -&gt;
        Settings: Process mass spectra (<strong>Shift + 3</strong>). In addition to overlaying raw spectra,
        you can also visualise multiple UniDec results.</p>
        <p><img src="images/plot_overlay_waterfall_MS.png" alt="" width="910" height="371" /></p>
        <p><strong>Overlaying mobilograms and chromatograms<br /></strong></p>
        <p>These can be created from within the Peak list panel or Text list panel and generate 1D overlay plots
        for selected items.</p>
        <p><strong>Figure 2. Overlayed mobilogram from Herceptin
        mAb (<span data-dobid="hdw">courtesy</span> of Rosie Upton).</strong></p>
        <p><img src="images/plot_origami_compare_mobilograms.png" alt="" width="1243" height="527" /></p>
        <p>&nbsp;</p>
        <p><strong>Overlaying heatmaps</strong></p>
        <p>These can be created from within the Peak list panel or Text list panel. There are
        multiple overlay functions, some of which are shown below. You can change various parameters like
        colormap colour, line thickness in Plot --&gt; Settings: Plot 1D/2D/Legend etc.</p>
        <p><strong>Figure 3. Overlay method - MASK</strong></p>
        <p><img src="images/plot_origami_compare_mask.png" alt="" width="1017" height="903" /></p>
        <p><strong>Figure 4. Overlay method - TRANSPARENT</strong></p>
        <p><strong><img src="images/plot_origami_compare_transparent.png" alt="" width="960" height="906" />
        </strong></p>
        <p><strong>Figure 5. Overlay method - RGB</strong></p>
        <p><strong><img src="images/plot_origami_compare_rgb.png" alt="" width="956" height="910" /></strong></p>
        <p><strong>Figure 6. Overlay method - RMSD</strong></p>
        <p><strong><img src="images/plot_origami_compare_rmsd.png" alt="" width="987" height="911" /></strong></p>
        <p><strong>Figure 7. Overlay method - RMSD/RMSF</strong></p>
        <p><strong><img src="images/plot_origami_compare_rmsdf.png" alt="" width="1031" height="941" /></strong></p>
        <p><strong>Figure 8. Overlay method - GRID (n x n)<br /></strong></p>
        <p><strong><img src="images/plot_origami_compare_gridNxN.png" alt="" width="1047" height="933" /></strong></p>
        <p>&nbsp;</p>
        """.strip()
        self.page_overlay_info = {"msg": msg, "title": "Learn about: Overlaying items", "window_size": (1250, 800)}

        msg = """
        <h2><strong>Loading of non-MS datasets ("other" data)</strong></h2>
        <hr />
        <p><strong>Disclaimer:</strong></p>
        <p>This is only an experimental feature and might not work perfectly! I've tried to implement all tags into
        various plotting functions but it is likely I forgot. I know for a fact that specifying xlimits/ylimits might
        not work everywhere.</p>
        <hr />
        <p>Since version 1.1.2 it is possible to load a number of data formats that are not mass spectrometry related,
        for instance, molecular dynamics results, machine learning, HDX, cross-linking and many others that comply with
        the data format requirements.A bit like in OriginPro or Excel, data can be loaded from a comma-delimited file
        that has been appropriately labeled with some of the allowed tags. The list of tags is found below and you also
        have a look online
        <strong><a href="https://github.com/lukasz-migas/ORIGAMI/tree/master/ORIGAMI_ANALYSE/other_datasets">here</a>
        </strong>to see some example files for datasets previously published by myself or members of the Barran group.
        The file must have metadata (found at the top of the file) and plot data (below the metadata).</p>
        <h3>Allowed tags in the metadata section:</h3>
        <p><strong>title</strong> = dataset title</p>
        <p><strong>plot_type</strong> = type of plot ORIGAMI should display. Allowed types: <em>line,
        </em><em>multi-line</em>, <em>scatter</em>, <em>vertical-bar, horizontal-bar, grid-line, waterfall</em></p>
        <p><strong>x_label</strong> = x-axis label</p>
        <p><strong>y_label</strong> = y-axis label</p>
        <p><strong>label </strong>or <strong>labels</strong> = y-axis labels. In general, number of
        labels must match number of columns with the <strong>axis_y</strong> tag.</p>
        <p><strong>color</strong> or <strong>colors</strong> = colors to be associated with dataset. Color
        must be in HEX representation (i.e. #000000). In general, number of colors must match number of columns
        with the <strong>axis_y</strong> tag.</p>
        <p><strong>x</strong><strong>limits</strong> = specify the minimum and maximum values for x-axis of the
        dataset. Must have two values.</p>
        <p><strong>ylimits</strong> = specify the minimum and maximum values for y-axis of the dataset. Must have
        two values.</p>
        <p><strong>legend_labels</strong> = for certain datasets (i.e. vertical/horizontal bar) it is necessary to
        add legend. Just put the desired label in.</p>
        <p><strong>legend_colors</strong> = associated with legend_labels. Must have same number of colors as
        number of labels. Color must be in HEX representation.</p>
        <p><strong>hover_labels</strong> = labels associated with columns with the <strong>axis_label </strong>tag.
        The number of hover_labels must match number of columns with axis_label tag.</p>
        <h4>Allowed tags in the plot data section:</h4>
        <p><strong>axis_x</strong> = columns associated with x-axis data.</p>
        <p><strong>axis_y</strong> = columns associated with y-axis data.</p>
        <p><strong>axis_xerr</strong> = columns associated with x-axis error data. Only used for scatter plot types.</p>
        <p><strong>axis_yerr</strong> = columns associated with y-axis error data. Only used for scatter plot types.</p>
        <p><strong>axis_color</strong> = columns with colors for each item in the x/y-axis. Color must be in
        HEX representation (i.e. #000000). Only used for scatter plot types.</p>
        <p><strong>axis_y_min </strong>= columns associated with x-axis data. Only used for vertical/horizontalbar
        plot types.</p>
        <p><strong>axis_y_max </strong>= columns associated with x-axis data. Only used for vertical/horizontalbar
        plot types.</p>
        <p><strong>axis_label </strong>= columns associated with x/y-axis data. Used in hover tooltip. Can add hover
        tooltip labels using the <strong>hover_labels</strong>.</p>
        <p><strong>axis_note </strong>= columns associated with x/y-axis data.</p>
        <h3>Requirements on per-plot basis:</h3>
        <p><em>line </em>- should only have two columns with labels <strong>axis_x</strong>, <strong>axis_y</strong></p>
        <p><em>multi-line </em>- should have as many columns as desired. You either provide one common column with the
        <strong>axis_x</strong> tag and multiple columns with <strong>axis_y</strong> (must have the same length as
        <strong>axis_x</strong>) or provide multiple combinations of <strong>axis_x</strong> and
        <strong>axis_y</strong>.
         There must be equal number of axis_x and axis_y columns in this case. You can specify colors and labels using
          the <strong>color/colors</strong> and <strong>label/labels</strong> tag in the metadata section.</p>
        <p><em>scatter - </em>should have as many columns as desired. You either provide one common column with the
        <strong>axis_x</strong> tag and multiple columns with <strong>axis_y</strong> (must have the same length as
        <strong>axis_x</strong>) or provide multiple combinations of <strong>axis_x</strong> and
        <strong>axis_y</strong>.
        You can also specify colors for each dataset using the <strong>color/colors</strong> tag in the metadata section
        or by providing <strong>axis_color</strong> column where color is specified for each item in the list. Currently
        only supported for datasets of the same length.<em><br /></em></p>
        <p><em>vertical-bar&nbsp; - </em>should have as many columns as desired. You either provide one common column
        with <strong>axis_x</strong> tag and multiple columns with <strong>axis_y_min</strong> and
        <strong>axis_y_max</strong> (must have the same length as <strong>axis_x</strong>) or provide multiple
        combinations of axis_x and axis_y_min and axis_y_max. You can specify colors for individual items using
        the <strong>axis_color</strong> tag or using the <strong>color/colors</strong> tag.
        You can also specify labels for individual datasets using the <strong>axis_label</strong>.</p>
        <p><em>horizontal-bar </em>- same as above.</p>
        <p><em>grid-line </em>- same as <em>multi-line</em> with different plot name.<em><br /></em></p>
        <p><em>waterfall</em> - same as <em>multi-line </em>with different plot name<em>.<br /></em></p>
        <p>&nbsp;</p>
        <h3>Allowed tags in the plot data section:</h3>
        <p>Labels, annotations, hover information etc can include 'unicode' labels. For intance if you would
        like to make a "&Aring;&sup2;" label/unit you can use "AA^2". Other currently supported units are:</p>
        <p>Superscript numbers: ^N where N is the number. If N is i.e. 23 then ^2^3 is required.</p>
        <p>Subscript numbers: *N where N is the number. If N is i.e. 23 then *2*3 is required.</p>
        <p>Supported labels:</p>
        <p>&Aring; = ang, AA, u212B</p>
        <p>&alpha; = alpha, aa, u03B1</p>
        <p>&beta; = beta, bb, u03B2</p>
        <p>&kappa; = kappa, kk, u03BA</p>
        <p>&Delta; = delta, dd, u0394</p>
        <h4><strong>Example figures:</strong></h4>
        <p><img src="images/plot_other_data_examples.png" alt="" width="1485" height="1615" /></p>
        <p>&nbsp;</p>
        """.strip()
        self.page_other_data_info = {"msg": msg, "title": "Learn about: Annotated datasets", "window_size": (1250, 800)}

        # ignore for now
        self.page_ccs_calibration_info = {
            "msg": fail_msg,
            "title": "Learn about: CCS calibration",
            "window_size": (1250, 800),
        }

        self.page_linear_dt_info = {
            "msg": fail_msg,
            "title": "Learn about: Linear drift-time analysis",
            "window_size": (1250, 800),
        }
