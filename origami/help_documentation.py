# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
#
#	 GitHub : https://github.com/lukasz-migas/ORIGAMI
#	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or
#    modify it under the condition you cite and credit the authors whenever
#    appropriate.
#    The program is distributed in the hope that it will be useful but is
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

from icons import IconContainer as icons


class OrigamiHelp:
    def __init__(self):
        """
        Initilize help
        """
        # load icons
        self.icons = icons()

        self._tool_tip_help()
        self._super_tip_help()

    def _tool_tip_help(self):

        msg = "A new window/tab in your prefered browser will open the playlist" + \
              " with most recent ORIGAMI videos."
        self.link_youtube = msg

    def _super_tip_help(self):
        # some presets
        header_line = True
        footer_line = False

    # -----------
        # Peaklist panel
        msg = 'If checked, any data that was previously generated (i.e. combined)\n' + \
              'will be overwritten with new dataset based on the selected parameters.'
        self.ionPanel_overwrite = {'help_title': 'Overwriting previous results', 'help_msg': msg,
                                   'header_img': None,
                                   'header_line': header_line, 'footer_line': footer_line}

        msg = 'If checked, any processing (i.e. combining collision voltage scans)\n' + \
              'will be performed with parameters that are already retained within the\n' + \
              'the ORIGAMI document. If these parameters are NOT present, parameters currently\n' + \
              'entered in the ORIGAMI GUI will be used instead.'
        self.ionPanel_useInternalParams = {'help_title': 'Use internal parameters', 'help_msg': msg,
                                           'header_img': None,
                                           'header_line': header_line, 'footer_line': footer_line}
    # -----------
        # Tandem MS panel
        msg = "If checked, a mirror/butterfly plot will be generated with the\n" + \
              "tandem MS on the top and a predicted spectrum on the bottom.\n" + \
              "Fragments are annotated and the difference in m/z between the calculated\n" + \
              "and measured peak is due to the error (always < than selected tolerance)."
        self.tandem_butterfly = {'help_title': 'Butterfly plots', 'help_msg': msg,
                                 'header_img': None,
                                 'header_line': header_line, 'footer_line': footer_line}

        msg = "Maximum number of labels that will be predicted for each m/z value in the peaklist.\n" + \
              "If the value is above 1 (default), more than one fragment can corresponded to particular m/z\n" + \
              "so please make sure that you've selected appropriate tolerance value!"
        self.tandem_max_labels = {'help_title': 'Butterfly plots', 'help_msg': msg,
                                  'header_img': None,
                                  'header_line': header_line, 'footer_line': footer_line}

    # -----------
        # Process panel (Extract)
        msg = "Pusher frequency in microseconds. Only used when drift time values\n" + \
              "are entered in miliseconds as the extraction program expects bins."
        self.extract_pusherFreq = {'help_title': 'Pusher frequency', 'help_msg': msg,
                                   'header_img': None,
                                   'header_line': header_line, 'footer_line': footer_line}

        msg = 'Scan time in seconds. Only used when the retention time is entered in\n' + \
              'scans as the extraction program expects minutes.'
        self.extract_scanTime = {'help_title': 'Scan time', 'help_msg': msg,
                                 'header_img': None,
                                 'header_line': header_line, 'footer_line': footer_line}

        msg = "If checked, retention time will be assumed to be in scans rather\n" + \
              "than in minutes."
        self.extract_in_scans = {'help_title': 'Retention time units', 'help_msg': msg,
                                 'header_img': None,
                                 'header_line': header_line, 'footer_line': footer_line}

        msg = "If checked, drift time will be assumed to be miliseconds\n" + \
              "rather than in bins."
        self.extract_in_ms = {'help_title': 'Drift time units', 'help_msg': msg,
                              'header_img': None,
                              'header_line': header_line, 'footer_line': footer_line}

        msg = "Enter retention time values. Values typically in minutes."
        self.extract_rt = {'help_title': 'Retention time', 'help_msg': msg,
                           'header_img': None,
                           'header_line': header_line, 'footer_line': footer_line}

        msg = "Enter drift time values. Values typically in bins."
        self.extract_dt = {'help_title': 'Drift time', 'help_msg': msg,
                           'header_img': None,
                           'header_line': header_line, 'footer_line': footer_line}

        msg = "Enter m/z values."
        self.extract_mz = {'help_title': 'Mass spectra', 'help_msg': msg,
                           'header_img': None,
                           'header_line': header_line, 'footer_line': footer_line}

    # -----------
        # Process panel (UniDec)
        msg = "Open a new HTML window with information about UniDec\n"
        self.unidec_about = {'help_title': 'About UniDec', 'help_msg': msg,
                             'header_img': None,
                             'header_line': header_line, 'footer_line': footer_line}

        msg = "Minimum m/z of the data\n"
        self.unidec_min_mz = {'help_title': 'Minimum m/z', 'help_msg': msg,
                              'header_img': None,
                              'header_line': header_line, 'footer_line': footer_line}

        msg = "Maximum m/z of the data\n"
        self.unidec_max_mz = {'help_title': 'Maximum m/z', 'help_msg': msg,
                              'header_img': None,
                              'header_line': header_line, 'footer_line': footer_line}

        msg = "Minimum allowed charge state in the deconvolution\n"
        self.unidec_min_z = {'help_title': 'Minimum charge state', 'help_msg': msg,
                             'header_img': None,
                             'header_line': header_line, 'footer_line': footer_line}

        msg = "Maximum allowed charge state in the deconvolution\n"
        self.unidec_max_z = {'help_title': 'Maximum charge state', 'help_msg': msg,
                             'header_img': None,
                             'header_line': header_line, 'footer_line': footer_line}

        msg = "Minimum allowed mass in deconvolution\n"
        self.unidec_min_mw = {'help_title': 'Minimum molecular weight', 'help_msg': msg,
                              'header_img': None,
                              'header_line': header_line, 'footer_line': footer_line}

        msg = "Maximum allowed mass in deconvolution\n"
        self.unidec_max_mw = {'help_title': 'Maximum molecular weight', 'help_msg': msg,
                              'header_img': None,
                              'header_line': header_line, 'footer_line': footer_line}

        msg = "Sets the resolution of the zero-charge mass spectrum\n"
        self.unidec_mw_resolution = {'help_title': 'Zero-charge spectrum resolution', 'help_msg': msg,
                                     'header_img': None,
                                     'header_line': header_line, 'footer_line': footer_line}

        msg = "Controls Linearization.\nConstant bin size (Da) for Linear m/z\nMinimum bin size (Da) for Linear Resolution\nNumber of data points compressed together for Nonlinear\n"
        self.unidec_linearization = {'help_title': 'Linearization information', 'help_msg': msg,
                                     'header_img': None,
                                     'header_line': header_line, 'footer_line': footer_line}

        msg = "Expected peak at full width half maximum in m/z (Da)\n"
        self.unidec_peak_FWHM = {'help_title': 'Peak width', 'help_msg': msg,
                                 'header_img': None,
                                 'header_line': header_line, 'footer_line': footer_line}

        msg = "Sort mass list by molecular weight or relative percentage"
        self.unidec_sort_mw_list = {'help_title': 'Sort molecular weight list', 'help_msg': msg,
                                    'header_img': None,
                                    'header_line': header_line, 'footer_line': footer_line}

    # -----------
        # Process panel (MS)
        msg = 'If checked, when extracting several scans from the\n' + \
              'chromatogram (RT) window, the mass spectra will be\n' + \
              'binned according to the values shown below.'
        self.bin_MS_in_RT = {'help_title': 'Linearization in chromatogram window', 'help_msg': msg,
                             'header_img': None,
                             'header_line': header_line, 'footer_line': footer_line}

        msg = 'If checked, when loading a list of multiple files,\n' + \
              'the mass spectra will be automatically binned\n' + \
              'according to the values shown below.'
        self.bin_MS_when_loading_MML = {
            'help_title': 'Linearization during loading Manual CIU dataset',
            'help_msg': msg,
            'header_img': None,
            'header_line': header_line,
            'footer_line': footer_line}

        msg = "The 'Process' button will use the currently selected dataset\n" + \
              "and using the selected processing settings generate a new dataset which\n" + \
              "will be added to the document."
        self.process_mass_spectra_processesBtn = {'help_title': 'Processing mass spectra...', 'help_msg': msg,
                                                  'header_img': None,
                                                  'header_line': header_line, 'footer_line': footer_line}

        msg = "The 'Replot' button will use the currently selected dataset\n" + \
              "and replot the data while also applying the processing parameters.\n" + \
              "This data will not be added to the document.\n"
        self.process_mass_spectra_replotBtn = {'help_title': 'Replotting mass spectra...', 'help_msg': msg,
                                               'header_img': None,
                                               'header_line': header_line, 'footer_line': footer_line}
    # -----------
        # Process panel (peak fitting)
        msg = 'If checked, the algorithm will attempt to predict the charge state of \n' + \
              'found peaks. The algorithm looks for features in a narrow MS window \n' + \
              'which can be usually found if the peak resolution is sufficiently high.'
        self.fit_highRes = {'help_title': 'Predict charge states', 'help_msg': msg,
                            'header_img': None,
                            'header_line': header_line, 'footer_line': footer_line}

        msg = 'If checked, isotopic peaks will be shown in the mass spectrum using\n' + \
              'using red circles. Adjust window size, threshold and peak width for best results.'
        self.fit_showIsotopes = {'help_title': 'Show isotopic peaks in mass spectrum', 'help_msg': msg,
                                 'header_img': None,
                                 'header_line': header_line, 'footer_line': footer_line}
    # -----------
        # Compare MS panel
        msg = 'If checked, each mass spectrum will be smoothed,\n' + \
              'baseline subtracted and normalised. The type of preprocessing\n' + \
              'depends on the parameters shown in the Process: Mass spectrum panel.\n' + \
              'You can change these to obtain best results.\n'
        self.compareMS_preprocess = {'help_title': 'Pre-processing mass spectra', 'help_msg': msg,
                                     'header_img': self.icons.iconsLib['process_ms_16'],
                                     'header_line': header_line, 'footer_line': footer_line}
    # -----------
        msg = 'Opens new window with plot settings.\n'
        self.compareMS_open_plot1D_settings = {'help_title': 'Editing plot parameters', 'help_msg': msg,
                                               'header_img': self.icons.iconsLib['panel_plot1D_16'],
                                               'header_line': header_line, 'footer_line': footer_line}
    # -----------
        msg = 'Opens new window with legend settings.\n'
        self.compareMS_open_legend_settings = {'help_title': 'Editing legend parameters', 'help_msg': msg,
                                               'header_img': self.icons.iconsLib['panel_legend_16'],
                                               'header_line': header_line, 'footer_line': footer_line}
    # -----------
        msg = 'Opens new window with mass spectrum processing settings.\n'
        self.compareMS_open_processMS_settings = {'help_title': 'Editing processing parameters', 'help_msg': msg,
                                                  'header_img': self.icons.iconsLib['process_ms_16'],
                                                  'header_line': header_line, 'footer_line': footer_line}
    # -----------
    # Plotting panel - General settings
        msg = 'Please select which plot you would like to adjust. Names are simply the \n' + \
              'representations shown as the tab names in the Plots panel.'
        self.general_plotName = {'help_title': 'Plot options - plot name', 'help_msg': msg,
                                 'header_img': None,
                                 'header_line': header_line, 'footer_line': footer_line}

        msg = 'The distance between the edge and the plot. Small values might not show labels.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_leftAxes = {'help_title': 'Plot options - left edge', 'help_msg': msg,
                                 'header_img': None,
                                 'header_line': header_line, 'footer_line': footer_line}

        msg = 'The distance between the edge and the plot. Small values might not show labels.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_bottomAxes = {'help_title': 'Plot options - bottom edge', 'help_msg': msg,
                                   'header_img': None,
                                   'header_line': header_line, 'footer_line': footer_line}

        msg = 'The width of the plot. This value compliments the LEFT edge.\n' + \
              ' When combined, it should not be larger than 1.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_widthAxes = {'help_title': 'Plot options - width', 'help_msg': msg,
                                  'header_img': None,
                                  'header_line': header_line, 'footer_line': footer_line}

        msg = 'The height of the plot. This value compliments the BOTTOM edge.\n' + \
              ' When combined, it should not be larger than 1.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_heightAxes = {'help_title': 'Plot options - height', 'help_msg': msg,
                                   'header_img': None,
                                   'header_line': header_line, 'footer_line': footer_line}

        msg = 'The distance between the edge and the plot. Small values might not show labels.\n' + \
              'These value differ from the ones shown above, as the figure export size can differ,\n' + \
              'from the one displayed in ORIGAMI GUI.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_leftAxes_export = {'help_title': 'Plot options - left edge', 'help_msg': msg,
                                        'header_img': None,
                                        'header_line': header_line, 'footer_line': footer_line}

        msg = 'The distance between the edge and the plot. Small values might not show labels.\n' + \
              'These value differ from the ones shown above, as the figure export size can differ,\n' + \
              'from the one displayed in ORIGAMI GUI.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_bottomAxes_export = {'help_title': 'Plot options - bottom edge', 'help_msg': msg,
                                          'header_img': None,
                                          'header_line': header_line, 'footer_line': footer_line}

        msg = 'The width of the plot. This value compliments the LEFT edge.\n' + \
              'These value differ from the ones shown above, as the figure export size can differ,\n' + \
              'from the one displayed in ORIGAMI GUI.\n' + \
              ' When combined, it should not be larger than 1.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_widthAxes_export = {'help_title': 'Plot options - width', 'help_msg': msg,
                                         'header_img': None,
                                         'header_line': header_line, 'footer_line': footer_line}

        msg = 'The height of the plot. This value compliments the BOTTOM edge.\n' + \
              'These value differ from the ones shown above, as the figure export size can differ,\n' + \
              'from the one displayed in ORIGAMI GUI.\n' + \
              ' When combined, it should not be larger than 1.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_heightAxes_export = {'help_title': 'Plot options - height', 'help_msg': msg,
                                          'header_img': None,
                                          'header_line': header_line, 'footer_line': footer_line}

        msg = 'The width of the plot in inches. Ensures consistent plot size when exporting figures.'
        self.general_widthPlot_inch = {'help_title': 'Plot options - width', 'help_msg': msg,
                                       'header_img': None,
                                       'header_line': header_line, 'footer_line': footer_line}

        msg = 'The height of the plot. Ensures consistent plot size when exporting figures.'
        self.general_heightPlot_inch = {'help_title': 'Plot options - height', 'help_msg': msg,
                                        'header_img': None,
                                        'header_line': header_line, 'footer_line': footer_line}

        msg = 'The fraction at which the zooming tool changes from line to rectangle.\n' + \
              'The lower the value, the more sensitive the zooming becomes. Default: 0.03'
        self.general_zoom_crossover = {'help_title': 'Zoom crossover sensitivity', 'help_msg': msg,
                                       'header_img': None,
                                       'header_line': header_line, 'footer_line': footer_line}

        msg = "When checked, figures will be automatically plotted when an appropriate item\n" + \
              "was selected in the Document Tree."
        self.general_instantPlot = {'help_title': 'Instant plot', 'help_msg': msg,
                                    'header_img': None,
                                    'header_line': header_line, 'footer_line': footer_line}

        msg = "When checked, some of the 'slower' functions are exectured on a separate CPU thread\n" + \
              "meaning the GUI will not get locked (unusable). While it has been extensively tested\n" + \
              "this can still cause some problems and occasionally cause a crash."
        self.general_multiThreading = {'help_title': 'Multi-threading', 'help_msg': msg,
                                       'header_img': None,
                                       'header_line': header_line, 'footer_line': footer_line}

        msg = "When checked, a new log file will appear in the ORIGAMI folder which keeps track of all your\n" + \
              "actions and in some cases, errors or warnings."
        self.general_logToFile = {'help_title': 'Log events to file', 'help_msg': msg,
                                  'header_img': None,
                                  'header_line': header_line, 'footer_line': footer_line}

        msg = "When checked, settings will be automatically saved in the ORIGAMI directory\n" + \
              "with the file name configOut.xml"
        self.general_autoSaveSettings = {'help_title': 'Auto-save settings', 'help_msg': msg,
                                         'header_img': None,
                                         'header_line': header_line, 'footer_line': footer_line}


class HTMLHelp:
    def __init__(self):
        self.helpPages()

    def helpPages(self):
        fail_msg = """
        <h1>Not implemented yet</h1>
        <p><img src="images/fail.gif" width="404" height="313" /></p>
        """.strip()

        msg = """
        <p>UniDec is a Bayesian deconvolution program for deconvolution of mass spectra and ion mobility-mass spectra developed by Dr. Michael Marty and is available under a modified BSD licence.</p>
        <p>If you have used UniDec while using ORIGAMI, please cite:</p>
        <p><a href="http://pubs.acs.org/doi/abs/10.1021/acs.analchem.5b00140" rel="nofollow">M. T. Marty, A. J. Baldwin, E. G. Marklund, G. K. A. Hochberg, J. L. P. Benesch, C. V. Robinson, Anal. Chem. 2015, 87, 4370-4376.</a></p>
        <p>This is 'limited' but functional version of UniDec and it might lack certain features so for full version I would highly recommend downloading UniDec to give it a try yourself. It is available from <a href="https://github.com/michaelmarty/UniDec/releases">here</a>.</p>
        <p><strong>UniDec engine version 2.6.7.</strong></p>
        """.strip()
        self.page_UniDec_info = {'msg': msg,
                                 'title': "About UniDec...",
                                 'window_size': (550, 300)}

        msg = """
        """.strip()
        self.page_data_getting_started = {'msg': msg,
                                          'title': "Learn about: Getting started",
                                          'window_size': (1250, 800)}

        msg = """
        <p><strong>Loading data</strong></p>
        <p>There are several ways you can load MS or IM-MS data.</p>
        <p>1) Use the file menu. Select appropriate option and continue to select your file</p>
        <p>2) Use the toolbar. Click on any of the available buttons to load data</p>
        <p>3) Use a keyboard shortcut.</p>
        <p>4) Load from within individual panels</p>
        <p>5) Drag and drop files in the window.</p>
        <p><strong>Supported formats</strong></p>
        <p>ORIGAMI supports several file formats:</p>
        <ul>
        <li>Waters .raw files - MS and IM-MS</li>
        <li>Text .csv/.txt/.tab - MS, 1D, 2D, RT</li>
        <li>Clipboard - MS only</li>
        </ul>
        <p>Currently being examined for implementation:</p>
        <ul>
        <li>mzML</li>
        <li>Agilent .d files</li>
        <li>Thermo .raw files</li>
        </ul>
        <p>Some of these files can be directly dropped in the main window and they will be loaded and pre-processed. Thats usually the quickest way to load files.</p>
        <p>Certain files, i.e. those belonging to manually acquired CIU dataset, should be dropped simultaneously in the <strong>Manual Files panel.</strong></p>
        <p>&nbsp;<strong>Dataset support</strong></p>
        <ul>
        <li>MS</li>
        <li>IM-MS</li>
        <li>CIU (manual and ORIGAMI-acquired)</li>
        <li>SID</li>
        <li>UVPD</li>
        <li>IRMPD</li>
        <li>DT-IM-MS - kind of limited and needs work</li>
        <li>CCS calibrations (TWIMS) - kind of limited and needs work</li>
        </ul>
        <p>&nbsp;</p>
        <p><strong>Please let me know if I should include anAnnotated data format.</strong></p>
        """.strip()
        self.page_data_loading_info = {'msg': msg,
                                       'title': "Learn about: Loading data",
                                       'window_size': (1250, 800)}

        msg = """
        <p><strong>Data extraction<br /></strong></p>
        <p>Interrogation of files and data extraction is relatively straightforward. You simply load file(s), select region of interest in the mass spectrum, chromatogram, mobiligram or two-dimensional heatmap, hold&nbsp;<strong>CTRL</strong> and left-mouse drag in the area. Data is either automatically extracted or added to one of several panels.</p>
        <p><strong>Extraction in MS window</strong></p>
        <ol>
        <li>Load file with mass spectrum in it (i.e. Waters .raw)</li>
        <li>Select region of interest and hold <strong>CTRL</strong> and left-click and drag over a peak(s).</li>
        <li>Ion information will appear a Peak list panel which allows you to extract and compare several ions together.</li>
        <li>Once ion is added to the table, in the toolbar of the Peaklist panel click on the Extract button and select Extract... Data will be automatically added to your document.</li>
        <li>Extracted data typically include chromatogram, mobiligram and 2D heatmap for selected peak.</li>
        <li>See <strong>Figure 1</strong> for example of selected peaks.</li>
        </ol>
        <p><strong>Extraction in RT window</strong></p>
        <ol>
        <li>Load file with chromatogram (i.e. Waters .raw)</li>
        <li>Select region of interest and hold <strong>CTRL</strong> and left-click and drag over it.</li>
        <li>Data will be automatically added to the document.</li>
        <li>Extracted data includes mass spectrum for specified chromatographic region.</li>
        </ol>
        <p><strong>Extracted in 1D window</strong></p>
        <ol>
        <li>Load file with mobiligram (i.e. Waters .raw)</li>
        <li>Select region of interest and hold <strong>CTRL</strong> and left-click and drag over it.</li>
        <li>Data will be automatically added to the document.</li>
        <li>Extracted data includes mass spectrum for specified drift time region.</li>
        </ol>
        <p><strong>Extracted using Extraction panel</strong></p>
        <p>The extraction panel (accessible via shortcut <strong>SHIFT+1</strong>) allows extraction MS, RT, 1D and 2D data from any allowed file (i.e. Waters .raw). In the panel you can specify m/z, chromatographic and drift-time range and specify which you would like to use as base for extraction. See <strong>Figure 2</strong> for more details.</p>
        <p><strong>Figure 1. Peak list panel</strong></p>
        <p><strong><img src="images/panel_peaklist.png" alt="" width="676" height="320" /></strong></p>
        <p><strong>Figure 2. Extraction panel</strong></p>
        <p><strong><img src="images/panel_process_data_extraction.png" width="470" height="390" /></strong></p>
        """.strip()
        self.page_data_extraction_info = {'msg': msg,
                                          'title': "Learn about: Extracting data",
                                          'window_size': (750, 800)}

        msg = """
        <p><strong>About UniDec</strong></p>
        <p>UniDec is a Bayesian deconvolution algorithm used with MS and IM-MS datasets. You can find out more about UniDec <a href="https://pubs.acs.org/doi/abs/10.1021/acs.analchem.5b00140">here</a>.</p>
        <p><strong>Settings panel</strong></p>
        <p><img src="images/panel_process_unidec.png" width="740" height="474" /></p>
        <p><strong>How to use</strong></p>
        <ol>
        <p><strong>Interactive document with UniDec results</strong></p>
        <p><a href="http://htmlpreview.github.io/?https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_ANALYSE/v1.1.1/p27FL_UniDec.html">Analysis of p27-FL IDP protein using UniDec deconvolution engine</a></p>
        <li>Load or create document with mass spectra</li>
        <li>Fill-in details in the pre-processing step. Specify m/z range, bin size, linearization mode and press <strong>Pre-process</strong></li>
        <li>Fill-in deconvolution details. Please specify charge state range, molecular weight range (in Da) and sampling frequency (window width).</li>
        <li>Fill-in peak FWHM. You can either automatically 'guess' the value or fit one yourself. To fit the mass spectrum, untick <strong>Auto</strong> and press on the <strong>Peak width tool</strong></li>
        <li>Select peak shape and click on <strong>Run UniDec </strong>button.</li>
        <li>If you would like to fit charge state peaks, click on the Detect peaks. You can change the peak detection window, peak threshold and other parameters.</li>
        <li>Results from all steps will automatically appear in the UniDec panel in the ORIGAMI main window.</li>
        <li>You can easily annotate peaks in the spectrum by selecting molecular weight in the Plotting section. Once selected, click on the <strong><strong>Label charges</strong></strong></li>
        </ol>
        <p><strong>UniDec results in ORIGAMI<br /></strong></p>
        <p><img src="/images/unidec_continuous_results.png" width="1149" height="845" /></p>
        <p>&nbsp;</p>
        <p>&nbsp;</p>
        """.strip()
        self.page_deconvolution_info = {'msg': msg,
                                        'title': "Learn about: MS deconvolution using UniDec",
                                        'window_size': (1250, 800)}

        msg = """
        <p><strong>Manual CIU datasets<br /></strong></p>
        <p>Unlike ORIGAMI-MS, manual CIU datasets consist of several files, usually varying in the collision or cone voltage. ORIGAMI can load multiple files without any problems and stitches appropriate information together to generate a all-in-one document.</p>
        <p>Files do not have to differ in collision voltage, they can be different based on solvent composition, travelling wave height, IRMPD wavelength, SID energy or others.</p>
        <p><strong>Loading data</strong></p>
        <ul>
        <li>Click on the <strong>M+ button</strong> in the toolbar to load multiple MassLynx files</li>
        <li>Click on <strong>File--&gt; Open multiple MassLynx (.raw) files</strong></li>
        <li>Drag and drop .raw files in the Multiple files panel (activated by using shortcut (<strong>Ctrl + 5</strong>)</li>
        </ul>
        <p>In any case, you will be asked to select name and directory path to associate with the ORIGAMI document.</p>
        <p>&nbsp;<strong>Analysis procedure<br /></strong></p>
        <ol>
        <li>Once you've loaded MassLynx data, you can annotate it in the Multiple files table by double-clicking in the <strong>energy</strong> column. This will allow you to sort your data based on some pre-defined parameter (<strong>Figure 1</strong>)</li>
        <li>Right-clicking on any item will reveal a small menu which allows you visualise your loaded data (<strong>Figure 2</strong>)</li>
        <li>Now that you have created the document, you can easily analyse it by selecting mass spectrum of interest and extracting ion information. To do this, hold <strong>Ctrl</strong> on your keyboard and drag-click in the mass spectrum window (MS) on ion of interest. The ion information will appear in the Peak list panel and from there you can extract data which will be automatically reshaped to form a 2D IM-MS heatmap. (<strong>Figure 3</strong>)</li>
        <li>To extract data, you must click on the extraction tool. (<strong>Figure 4</strong>)</li>
        <li>Once you have extracted data, you can overlay species together, export as text or in interactive format or create figures directly in ORIGAMI.</li>
        <li>All the data associated with this document is shown in the Documents panel (<strong>Figure 5</strong>)</li>
        </ol>
        <p><strong>Additional analyses</strong></p>
        <ul>
        <li>MS comparison panel</li>
        </ul>
        <ol>
        <li>Double-click on the Mass Spectra item in the documents view (or right-click and select Compare mass spectra...</li>
        <li>A new window will appear which will allow you to select two components to compare against each other. (<strong>Figure 6</strong>)</li>
        </ol>
        <ul>
        <li>Overlay 1D, RT or 2D ions</li>
        </ul>
        <ol>
        <li>&nbsp;Select species in the Peak list panel</li>
        <li>Click on the Overlay tool in the Peak list panel and select desired method</li>
        <li>Once clicked, you will be prompted to create a new document (Overlay document) which holds all overlay information</li>
        <li>Once created, your images and data will appear in that document</li>
        <li>An example of several overlay methods is shown in <strong>Figure 7</strong></li>
        </ol>
        <p><strong>Figure 1. Multiple files panel</strong></p>
        <p>&nbsp;<img src="images/panel_multiple_files.png" alt="" width="385" height="207" /></p>
        <p><strong>Figure 2. Right-click menu in Multiple files panel</strong></p>
        <p>&nbsp;<img src="images/panel_multiple_files_right_click_menu.png" alt="" width="273" height="132" /></p>
        <p><strong>Figure 3. Spectrum and ion list</strong></p>
        <p><img src="images/panel_spectrum_peak_list.png" alt="" width="745" height="193" /></p>
        <p><strong>Figure 4. Extraction of data</strong></p>
        <p><img src="images/panel_peaklist_extract_menu.png" alt="" width="230" height="101" /></p>
        <p><strong>Figure 5. Document view</strong></p>
        <p><img src="images/panel_document_tree.png" alt="" width="250" height="597" /></p>
        <p><strong>Figure 6. MS comparison panel</strong></p>
        <p><img src="images/panel_spectrum_compareMS.png" alt="" width="1137" height="371" /></p>
        <p><strong>Figure 7. Mass spectrum waterfall</strong></p>
        <p><strong><img src="images/plot_mass_spectrum_waterfall.png" alt="" width="426" height="359" /></strong></p>
        <p><strong>Figure 8. Overlay examples</strong></p>
        <p><strong><img src="images/multiple_export_overlay.png" alt="" width="601" height="941" /></strong></p>
        """.strip()
        self.page_multiple_files_info = {'msg': msg,
                                         'title': "Learn about: Manual CIU (multiple files)",
                                         'window_size': (1210, 800)}

        msg = """
        <p><strong>Interactive output<br /></strong></p>
        <p>ORIGAMI enables creation of HTML/JavaScript webpages which include any or all of MS, RT, 1D, 2D and Annotated data formats. Interactive plots are generated by utilizing a modern open-source plotting library (Bokeh) which enables embedding JavaScript plots in a .HTML document.&nbsp;</p>
        <p>Any plot that is available in ORIGAMI can be exported in an interactive format and therefore shared with the scientific community, your collaborators and saved for future use. While this might seem like a gimmick, there has been some progress in making boring, static images in journals more interactive (see <a href="https://www.nature.com/articles/d41586-018-01322-9">here</a> and <a href="http://journals.plos.org/plosbiology/article/file?id=10.1371/journal.pbio.1002484&amp;type=printable">here</a>). I so often feel that figures in papers are so small or illegible that they might as well be missed and would much rather explore it in more detail on my phone or my laptop!</p>
        <p><strong>Get started</strong></p>
        <ol>
        <li>Create or load document with any data</li>
        <li>Click on the colourful icon in the toolbar and a new window should appear with large table that combines all data available in your currently opened documents as well as an editor window.</li>
        <li>Select any number of items in that table and click on the <strong>Export HTML </strong>button. If you have not set-up file path for the interactive document, you will be prompted to do so.</li>
        <li>Once exported, your .HTML document can be opened with any modern browser and shared onlineHTML</li>
        </ol>
        <p><strong>Examples of generated documents</strong></p>
        <p><a href="http://htmlpreview.github.io/?https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_ANALYSE/v1.1.1/origami_article_interactive_document.html">Interactive document associated with ORIGAMI publication (opens in the browser)</a></p>
        <p><a href="http://htmlpreview.github.io/?https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_ANALYSE/v1.1.1/p27FL_UniDec.html">Analysis of p27-FL IDP protein using UniDec deconvolution engine&nbsp;</a><a href="http://htmlpreview.github.io/?https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_ANALYSE/v1.1.1/origami_article_interactive_document.html">(opens in the browser)</a></p>
        <p><a href="http://htmlpreview.github.io/?https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_ANALYSE/v1.1.1/prt_interactive_grid.html">Visualization of multiple 2D datasets simultaneously</a> <a href="http://htmlpreview.github.io/?https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_ANALYSE/v1.1.1/origami_article_interactive_document.html">(opens in the browser)</a></p>
        <p><a href="http://htmlpreview.github.io/?https://github.com/BarranLab/Upton_mAbs_2018/blob/master/Figure_4.html">Interactive barplot from custom dataset (opens in the browser)</a></p>
        <p><a href="http://htmlpreview.github.io/?https://github.com/BarranLab/Upton_mAbs_2018/blob/master/Figure_S3.html">Fully annotated mass spectrum of mAb (opens in the browser)</a></p>
        <p><a href="http://htmlpreview.github.io/?https://github.com/BarranLab/Beveridge_Migas_p27_2018/blob/master/Figure_2.html">Grid-like assembly of collision cross section distributions (opens in the browser)</a></p>
        <p><a href="http://htmlpreview.github.io/?https://github.com/BarranLab/Beveridge_Migas_p27_2018/blob/master/Figure_S9.html">Grid-like assembly of molecular dynamics results (opens in the browser)</a></p>
        <p><a href="http://htmlpreview.github.io/?https://github.com/BarranLab/Beveridge_Migas_p27_2018/blob/master/Figure_1c.html">A number of waterfall-like plots (opens in the browser)</a></p>
        <p><strong>Annotating items</strong></p>
        <p>Another advantage of making interactive figures, is that ability to add additional information to each plot, including experimental conditions, who acquired that data, how was it processed, links to previous publications and so much more!</p>
        <ol>
        <li>To annotate items, select an item in the table and the fields of title, header and footnote (and many others!) will be automatically populated.</li>
        <li>Once you've selected an item, you can type in the information you would like to include. This allows insertion of either standard text or one embellished with HTML or markdown tags. If you are not familiar with this sort of text format, use the&nbsp;<strong>online HTML editor&nbsp;</strong>to generate enriched text. This text (the html format!) can be copied and pasted in appropriate fields in the Interactive panel.&nbsp;</li>
        <li>You can also annotate directly in the table by double-clicking on <strong>certain</strong> columns. This can be useful to speed things up.</li>
        </ol>
        <p><strong>Using the toolbar</strong></p>
        <p>As you might have noticed, the toolbar section of this panel is very busy! This is to make your life a little easier and quicker to quickly apply common settings (i.e. toolset or page selection). In the toolbar you can also filter table based on either document, data type or both criteria.</p>
        <p><img src="images/panel_interactive_toolbar.png" alt="" width="715" height="44" /></p>
        <p><strong>Selecting tools</strong></p>
        <p>You would have noticed there is a column named <strong>tools</strong> which keeps the selected toolset for each item. A toolset is basically a collection of available tools (zooming, panning, mouse wheel support, resizing etc) and can be modified in the <strong>Properties tab</strong> in the Interactive editor window. You can create new toolsets by clicking on the <strong>+ </strong>button in the <strong>Interactive tools section</strong> and selecting a number of tools you would like to include. That toolset will then appear in the various combo-boxes which allow you to select it for specified items</p>
        <p><strong>Selecting page</strong></p>
        <p>Again, there is a column called <strong>page</strong> which controls which page the selected item will be exported on. If you see page named <strong>None</strong> it indicates that each plot with that designation will have a new tab created for it. If you see one named <strong>Columns</strong>, those selected items will appear in a column format and <strong>Rows</strong> will means items appear next to each other. Once again, you can create your new pages which can hold as few or as many items simultaneously. To do so, in the Properties -&gt;Page layout click on the <strong>+</strong> button and create new page. You can then select what layout you would like it to have.</p>
        <p><strong>Figure 1. Peaklist window<br /></strong></p>
        <p><img src="images/panel_interactive_list.png" width="718" height="375" /></p>
        <p><strong>Figure 2. HTML annotation window</strong></p>
        <p><strong><img src="images/panel_interactive_html.png" width="642" height="522" /></strong></p>
        <p><strong>Figure 3. Parameters window<br /></strong></p>
        <p><img src="images/panel_interactive_default_settings.png" width="651" height="625" /></p>
        <p><strong>Figure 4. Example output</strong></p>
        <p><img src="images/html_example.png" alt="" width="802" height="870" /></p>
        <p><strong>Figure 5. With added widgets</strong></p>
        <p><strong><img src="images/html_waterfall.png" alt="" width="1148" height="518" /></strong></p>
        <p><strong>Figure 6. Scatter plot</strong></p>
        <p><strong><img src="images/html_scatter.png" alt="" width="1197" height="604" /></strong></p>
        <p><strong>Figure 7. Barplot</strong></p>
        <p><strong><img src="images/html_barplot.png" alt="" /></strong></p>
        """.strip()
        self.page_interactive_output_info = {'msg': msg,
                                             'title': "Learn about: Interactive documents",
                                             'window_size': (1100, 800)}

        msg = """
        <p><strong>ORIGAMI-MS format and its analysis</strong></p>
        <p>ORIGAMI-MS acquired files are simply CIU datasets that were acquired within a single file in which the collision voltage (or cone voltage) are slowly ramped to increase the activation energy. The acquisition within a single file allows smaller step sizes, fewer files and significant speed-ups in the acquisition process!</p>
        <p><strong>ORIGAMI-MS method</strong></p>
        <ul>
        <li><strong>Linear </strong>&ndash; the collision voltage is ramped between <strong>Start Voltage</strong> and <strong>End Voltage </strong>with a defined <strong>Step Voltage</strong> and a pre-defined number of scans per voltage (<strong>SPV</strong>).</li>
        <li><strong>Exponential </strong>&ndash; the collision voltage is ramped between <strong>Start Voltage</strong> and <strong>End Voltage </strong>with a defined <strong>Step Voltage</strong>, however the number of <strong>SPVs </strong>increases as a function of an exponential function. The user specifies to additional parameters <strong>Exponential %</strong> and <strong>Exponential Increment</strong> which determine the rate of the increase.</li>
        <li><strong>Fitted </strong>&ndash; the collision voltage is ramped between <strong>Start Voltage</strong> and <strong>End Voltage </strong>with a defined <strong>Step Voltage</strong>, however the number of <strong>SPVs </strong>increases as a function of a Boltzmann function. The user specifies to additional parameter <strong>Boltzmann Offset</strong> which determines at which point the rate of SPVs should increase.</li>
        <li><strong>User-defined </strong>&ndash; the user provides a list of collision voltages and SPVs which are used during the acquisition.</li>
        </ul>
        <p>The list in the format:</p>
        <p><img src="images/origami_spv_cv_format.png" alt="" width="239" height="191" /></p>
        <p><strong>How to open ORIGAMI files<br /></strong></p>
        <ul>
        <li>Click on the <strong>O</strong> button in the toolbar to load single ORIGAMI file (shortcut <strong>CTRL+R</strong>)</li>
        <li>Click on File...-&gt; Open ORIGAMI MassLynx (.raw) file</li>
        <li>Drag and drop single MassLynx file in the main window</li>
        </ul>
        <p><strong>How to determining first scan<br /></strong></p>
        <ol>
        <li>Change the view to the RT tab</li>
        <li>Zoom-in on the &lsquo;reporter&rsquo; region in the retention time plot. The first value after the break is the start scan. In this case, the start scan is 7 (<em>e</em>. the first collision voltage in your experiment was applied on the 7<sup>th</sup> scan).</li>
        </ol>
        <p><strong>Figure 1. Chromatogram window with ORIGAMI-MS reporter region</strong></p>
        <p><img src="images/plot_origami_chromatogram.png" alt="" width="1179" height="635" /></p>
        <p><strong>How to determine ORIGAMI parameters</strong></p>
        <p>There are only two ways you can figure out your parameters:</p>
        <ul>
        <li>You saved them in your lab book or in the header of the MassLynx file (recommended)</li>
        <li>You have saved them inside MassLynx file using the Save parameters button in <strong>ORIGAMI<sup>MS</sup></strong> GUI</li>
        </ul>
        <p>If you have not done either of these ways, you can try to figure out your parameters by going to the folder containing <strong>ORIGAMI<sup>MS </sup></strong>program and looking for the appropriate <em>ORIGAMI_log_DATE_TIME.log</em> file which contains <strong><em>all</em></strong> commands executed in in <strong>ORIGAMI<sup>MS</sup></strong> GUI.</p>
        <p><strong>How to extract ions</strong></p>
        <p>Please have a look at the other help page (<strong>Help -&gt; Help pages -&gt; Data extraction</strong>)</p>
        <p><strong>How to combine collision voltages</strong></p>
        <ol>
        <li>Fill-in ORIGAMI-MS parameters in the <strong>Process-&gt;Settings: ORIGAMI</strong> panel (shortcut <strong>SHIFT+2</strong>)</li>
        <li>Extract ion mobility data for each ion</li>
        <li>Select some or all ions in the peaklist</li>
        <li>In the toolbar click on the Process -&gt; Combine CVs for all/selected ions...</li>
        <li>Now, you should see appropriate data in the document panel</li>
        </ol>
        <p><strong>Figure 2. Processing panel where you enter ORIGAMI-MS parameters</strong></p>
        <p><img src="images/panel_process_origami.png" alt="" width="412" height="366" /></p>
        <p><strong>Figure 3.</strong> <strong> Toolbar menu for combing collision voltages</strong></p>
        <p><strong><img src="images/panel_peaklist_combine_menu.png" alt="" width="423" height="200" /></strong></p>
        <p><strong>How to process ions</strong></p>
        <p class="ORIGAMIstyle2" style="text-align: justify;"><span style="font-weight: normal; text-decoration: none; text-underline: none;">In some cases, it might be necessary to process single or multiple ions at once, in order to either improve their aIM-MS map or compare to one another. Processing can involve thresholding (noise removal), smoothing and/or normalisation. </span></p>
        <ol>
        <li class="ORIGAMIstyle2" style="text-align: justify;"><span style="font-weight: normal; text-decoration: none; text-underline: none;">Before you can process ions, you must choose desired settings in the <strong>Process -&gt; Settings: Process 2D heatmaps</strong> (shortcut <strong>SHIFT+4</strong>). <br /></span></li>
        <li class="ORIGAMIstyle2" style="text-align: justify;"><span style="font-weight: normal; text-decoration: none; text-underline: none;">Select some or all ions in the peaklist</span></li>
        <li class="ORIGAMIstyle2" style="text-align: justify;"><span style="font-weight: normal; text-decoration: none; text-underline: none;">In the toolbar click on the <strong>Process...-&gt;Process selected/all ions</strong></span></li>
        <li class="ORIGAMIstyle2" style="text-align: justify;"><span style="font-weight: normal; text-decoration: none; text-underline: none;">Now you should see appropriate data in the document view (look for branches Drift time (2D, EIC) and ions with (processed) in the name)</span></li>
        </ol>
        <p><strong>Figure 4. Processing heatmaps panel</strong></p>
        <p><strong><img src="images/panel_process_2D.png" alt="" width="412" height="268" /></strong></p>
        <p><strong>Extracting mass spectra for each collision voltage</strong></p>
        <p>Once you have associated ORIGAMI-MS parameters with the opened file, you can extract the mass spectrum for each collision voltage. To do so:</p>
        <ol>
        <li>Provide ORIGAMI-MS parameters</li>
        <li>In the peaklist toolbar click on the <strong>Process... -&gt; Extract mass spectra for each collision voltage</strong>. These can be in .raw (non linear) or as binned spectra. [Please be patient! It can take a while to do this operation sometimes!)</li>
        <li>A new branch will appear in your document called <strong>Mass Spectra</strong> which have been named in the style</li>
        <li><strong>Scans: n-n+SPV | CV: value V</strong></li>
        </ol>
        <p><strong>Figure 6. Document view of the mass spectra list</strong></p>
        <p><strong><img src="images/panel_document_tree_ms_data.png" alt="" width="199" height="175" /></strong></p>
        <p><strong>Figure 7. Waterfall view of each collision voltage</strong></p>
        <p><strong><img src="images/plot_origami_ms_waterfall.png" alt="" width="511" height="498" /></strong></p>
        <p><strong>Document view for ORIGAMI files</strong></p>
        <p>Documents hold all necessary information for opened files and in the case of ORIGAMI, there is a lot of data regarding each extracted ion. Figure 8 shows the typical view which contains information about mass spectra, chromatograms, mobiligrams and heatmaps. Those associated with the 'process' tag have been normalized and smoothed (for instance).</p>
        <p><strong>Figure 8. Document panel view of analysed ORIGAMI file</strong></p>
        <p><strong><img src="images/panel_document_tree_data.png" width="270" height="596" /></strong></p>
        """.strip()
        self.page_origami_info = {'msg': msg,
                                  'title': "Learn about: Automated CIU (ORIGAMI-MS)",
                                  'window_size': (1250, 800)}

        msg = """
        <p><strong>Overlaying items</strong></p>
        <p>ORIGAMI enables multiple overlay and comparison functions for mobiligrams, chromatograms, mass spectra and two-dimensional heatmaps. These items are added to <strong>Comparison</strong> document which holds the input and output datasets, often pooled from multiple sources.</p>
        <p><strong>Overlaying mass spectra</strong></p>
        <p>Mass spectra can be overlayed from within the Multiple files panel where you can view either the <strong>raw</strong> data or pre-processed (just check the <strong>Pre-process mass spectra</strong>). Pre-processing parameters can be found under the Process -&gt; Settings: Process mass spectra (<strong>Shift + 3</strong>). In addition to overlaying raw spectra, you can also visualise multiple UniDec results.</p>
        <p><img src="images/plot_overlay_waterfall_MS.png" alt="" width="910" height="371" /></p>
        <p><strong>Overlaying mobiligrams and chromatograms<br /></strong></p>
        <p>These can be created from within the Peak list panel or Text list panel and generate 1D overlay plots for selected items.</p>
        <p><strong>Figure 2. Overlayed mobiligram from Herceptin mAb (<span data-dobid="hdw">courtesy</span> of Rosie Upton).</strong></p>
        <p><img src="images/plot_origami_compare_mobiligrams.png" alt="" width="1243" height="527" /></p>
        <p>&nbsp;</p>
        <p><strong>Overlaying heatmaps</strong></p>
        <p>These can be created from within the Peak list panel or Text list panel. There are multiple overlay functions, some of which are shown below. You can change various parameters like colormap colour, line thickness in Plot --&gt; Settings: Plot 1D/2D/Legend etc.</p>
        <p><strong>Figure 3. Overlay method - MASK</strong></p>
        <p><img src="images/plot_origami_compare_mask.png" alt="" width="1017" height="903" /></p>
        <p><strong>Figure 4. Overlay method - TRANSPARENT</strong></p>
        <p><strong><img src="images/plot_origami_compare_transparent.png" alt="" width="960" height="906" /></strong></p>
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
        self.page_overlay_info = {'msg': msg,
                                  'title': "Learn about: Overlaying items",
                                  'window_size': (1250, 800)}

        msg = """
        <h2><strong>Loading of non-MS datasets ("other" data)</strong></h2>
        <hr />
        <p><strong>Disclaimer:</strong></p>
        <p>This is only an experimental feature and might not work perfectly! I've tried to implement all tags into various plotting functions but it is likely I forgot. I know for a fact that specifying xlimits/ylimits might not work everywhere.</p>
        <hr />
        <p>Since version 1.1.2 it is possible to load a number of data formats that are not mass spectrometry related, for instance, molecular dynamics results, machine learning, HDX, cross-linking and many others that comply with the data format requirements.A bit like in OriginPro or Excel, data can be loaded from a comma-delimited file that has been appropriately labeled with some of the allowed tags. The list of tags is found below and you also have a look online <strong><a href="https://github.com/lukasz-migas/ORIGAMI/tree/master/ORIGAMI_ANALYSE/other_datasets">here</a> </strong>to see some example files for datasets previously published by myself or members of the Barran group. The file must have metadata (found at the top of the file) and plot data (below the metadata).</p>
        <h3>Allowed tags in the metadata section:</h3>
        <p><strong>title</strong> = dataset title</p>
        <p><strong>plot_type</strong> = type of plot ORIGAMI should display. Allowed types: <em>line, </em><em>multi-line</em>, <em>scatter</em>, <em>vertical-bar, horizontal-bar, grid-line, waterfall</em></p>
        <p><strong>x_label</strong> = x-axis label</p>
        <p><strong>y_label</strong> = y-axis label</p>
        <p><strong>label </strong>or <strong>labels</strong> = y-axis labels. In general, number of labels must match number of columns with the <strong>axis_y</strong> tag.</p>
        <p><strong>color</strong> or <strong>colors</strong> = colors to be associated with dataset. Color must be in HEX representation (i.e. #000000). In general, number of colors must match number of columns with the <strong>axis_y</strong> tag.</p>
        <p><strong>x</strong><strong>limits</strong> = specify the minimum and maximum values for x-axis of the dataset. Must have two values.</p>
        <p><strong>ylimits</strong> = specify the minimum and maximum values for y-axis of the dataset. Must have two values.</p>
        <p><strong>legend_labels</strong> = for certain datasets (i.e. vertical/horizontal bar) it is necessary to add legend. Just put the desired label in.</p>
        <p><strong>legend_colors</strong> = associated with legend_labels. Must have same number of colors as number of labels. Color must be in HEX representation.</p>
        <p><strong>hover_labels</strong> = labels associated with columns with the <strong>axis_label </strong>tag. The number of hover_labels must match number of columns with axis_label tag.</p>
        <h4>Allowed tags in the plot data section:</h4>
        <p><strong>axis_x</strong> = columns associated with x-axis data.</p>
        <p><strong>axis_y</strong> = columns associated with y-axis data.</p>
        <p><strong>axis_xerr</strong> = columns associated with x-axis error data. Only used for scatter plot types.</p>
        <p><strong>axis_yerr</strong> = columns associated with y-axis error data. Only used for scatter plot types.</p>
        <p><strong>axis_color</strong> = columns with colors for each item in the x/y-axis. Color must be in HEX representation (i.e. #000000). Only used for scatter plot types.</p>
        <p><strong>axis_y_min </strong>= columns associated with x-axis data. Only used for vertical/horizontalbar plot types.</p>
        <p><strong>axis_y_max </strong>= columns associated with x-axis data. Only used for vertical/horizontalbar plot types.</p>
        <p><strong>axis_label </strong>= columns associated with x/y-axis data. Used in hover tooltip. Can add hover tooltip labels using the <strong>hover_labels</strong>.</p>
        <p><strong>axis_note </strong>= columns associated with x/y-axis data.</p>
        <h3>Requirements on per-plot basis:</h3>
        <p><em>line </em>- should only have two columns with labels <strong>axis_x</strong>, <strong>axis_y</strong></p>
        <p><em>multi-line </em>- should have as many columns as desired. You either provide one common column with the <strong>axis_x</strong> tag and multiple columns with <strong>axis_y</strong> (must have the same length as <strong>axis_x</strong>) or provide multiple combinations of <strong>axis_x</strong> and <strong>axis_y</strong>. There must be equal number of axis_x and axis_y columns in this case. You can specify colors and labels using the <strong>color/colors</strong> and <strong>label/labels</strong> tag in the metadata section.</p>
        <p><em>scatter - </em>should have as many columns as desired. You either provide one common column with the <strong>axis_x</strong> tag and multiple columns with <strong>axis_y</strong> (must have the same length as <strong>axis_x</strong>) or provide multiple combinations of <strong>axis_x</strong> and <strong>axis_y</strong>. You can also specify colors for each dataset using the <strong>color/colors</strong> tag in the metadata section or by providing <strong>axis_color</strong> column where color is specified for each item in the list. Currently only supported for datasets of the same length.<em><br /></em></p>
        <p><em>vertical-bar&nbsp; - </em>should have as many columns as desired. You either provide one common column with <strong>axis_x</strong> tag and multiple columns with <strong>axis_y_min</strong> and <strong>axis_y_max</strong> (must have the same length as <strong>axis_x</strong>) or provide multiple combinations of axis_x and axis_y_min and axis_y_max. You can specify colors for individual items using the <strong>axis_color</strong> tag or using the <strong>color/colors</strong> tag. You can also specify labels for individual datasets using the <strong>axis_label</strong>.</p>
        <p><em>horizontal-bar </em>- same as above.</p>
        <p><em>grid-line </em>- same as <em>multi-line</em> with different plot name.<em><br /></em></p>
        <p><em>waterfall</em> - same as <em>multi-line </em>with different plot name<em>.<br /></em></p>
        <p>&nbsp;</p>
        <h3>Allowed tags in the plot data section:</h3>
        <p>Labels, annotations, hover information etc can include 'unicode' labels. For intance if you would like to make a "&Aring;&sup2;" label/unit you can use "AA^2". Other currently supported units are:</p>
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
        self.page_other_data_info = {'msg': msg,
                                     'title': "Learn about: Annotated datasets",
                                     'window_size': (1250, 800)}

        msg = """
        <h3>Annotating mass spectra</h3>
        <p>Since version 1.1.2, it is possible to annotate mass spectra with custom labels (i.e. charge state, protein name, contaminant name, etc). It is relatively straightforward and only requires a couple of clicks.</p>
        <ol>
        <li>Open a document with mass spectra/spectrum.</li>
        <li>Plot the mass spectrum by double-clicking on it in the <strong>Document tree</strong></li>
        <li>Right-click on the same spectrum and select Add/show annotations... This will open a new window, as shown in Figure 1.</li>
        <li>There are four ways in which you can add annotations for any file.:
        <ol>
        <li>Manually enter values of min, max, position, charge and label and click on the "<strong>Add annotation</strong>" button.</li>
        <li>Click on the button "<strong>Annotating: Off</strong>" and toggle it to turn blue and display "<strong>Annotating: On</strong>". This will ensure that any events of you dragging the mouse (while holding Ctrl on your keyboard) in the mass spectrum are caught by the annotation panel. Otherwise, if it is not enabled, the Ctrl+drag will be caught by the main window and the peak will be added to the Peaklist.</li>
        <li>Loading a peaklist file with specified peaks + labels. An example of one is shown in Figure 2 and also available as an example in ORIGAMI home directory (example_files/annotation_peaklist.csv). Columns min, max and charge are mandatory. To load a list, click on the <strong>"Action"</strong> button and select "<strong>Add list of ions (.csv/.txt)</strong>" and open an appropriate file.</li>
        <li>Find peaks in the Peak finding tool. When doing so, ensure the "Add peaks tp annotations" checkbox is checked. Any peaks alongside predicted charge state and intensity will be added to the file's annotations container. ORIGAMI will by default select the last plotted file as the one you want to add peaks to.</li>
        </ol>
        </li>
        <li>Once you are happy, close the panel</li>
        </ol>
        <p>Notes:</p>
        <ul>
        <li>It is possible to edit already create annotation. Simply select it in the table and change the desired values. After you finished, click on the "<strong>Add annotation</strong>" button.</li>
        <li>A number of actions is available in order to speed-up operation. To perform any of them, click on the "<strong>Action</strong>" button.
        <ul>
        <li>Set color for selected items</li>
        <li>Set charge state for selected items</li>
        <li>Auto generate labels (i.e. M+nH]<sup>n</sup></li>
        <li>Fix intensity for selected items. This basically selects a narrow range of the mass spectrum based on the min/max value in the peaklist and finds the maximum intensity. Useful when dealing with duplicated annotations.</li>
        <li>Save peaks to file. Exports the list of peaks to a .csv/.txt file. Cannot deal with unicode labels yet.</li>
        </ul>
        </li>
        <li>Duplicate annotations to different spectrum. Simply right-click in the <strong>Document </strong><strong>tree</strong> on the mass spectrum (which has annotations) and select "Duplicate annotations". A new window will appear which will ask you to select document and the desired mass spectrum.</li>
        </ul>
        <h3>Annotations in an interactive spectrum:</h3>
        <p>When exporting mass spectra, it is now possible to export the spectrum annotations in the interactive format. A number of examples are available online (see supplementary figures for recently submitted paper from the Barran group, availble <a href="https://github.com/BarranLab/Upton_mAbs_2018">here</a>).</p>
        <p>It is extremely easy to export mass spectra with annotations, you just have to ensure to select the '<strong>Show annotations</strong>' in the '<strong>Data (1D) settings</strong>' associated with the mass spectra in the interactive panel. Example of annotated spectrum is shown in Figure 4. Annotations can be customised (i.e. font size, rotation, X/Y-offset and color). Just change settings in the <strong>Annotations</strong> panel, as shown in Figure 5 and 6.</p>
        <p><strong>Known issues:</strong></p>
        <p>On a vary rare occasion, annotation windows don't work as they are intended and you cannot use the interactive annotation function. The best way to fix that is to clear the mass spectrum, replot the desired spectrum and open a new instance of the annotation panel. It does not always work but it does in most occasions. This is caused when the annotation window is closed inappropriately (not your fault but Pythons...).</p>
        <p><strong>Figure 1. Annotation window</strong></p>
        <p><img src="images/panel_annotations.png" width="728" height="500" /></p>
        <p><strong>Figure 2. Example file</strong></p>
        <p><img src="images/annotations_peaklist.png" alt="" width="393" height="182" /></p>
        <p><strong>Figure 3. Annotated peaks on plot</strong></p>
        <p><img src="images/plot_mass_spectrum_with_annotations.png" width="1149" height="422" /></p>
        <p><strong>Figure 4. Annotations in an interactive output</strong></p>
        <p><img src="images/html_spectrum_with_annotations.png" alt="" width="1132" height="459" /></p>
        <p>Figure 5. Enable annotations in the HTML window.</p>
        <p><img src="images/panel_interactive_enable_annotations.png" alt="" width="223" height="64" /></p>
        <p>Figure 6. Change annotation settings in the Annotations window.</p>
        <p><img src="images/panel_interactive_text_annotations_settings.png" width="304" height="98" /></p>

        """.strip()
        self.page_annotating_mass_spectra = {'msg': msg,
                                             'title': "Learn about: Annotating mass spectra",
                                             'window_size': (1250, 800)}

        # ignore for now
        self.page_ccs_calibration_info = {'msg': fail_msg,
                                          'title': "Learn about: CCS calibration",
                                          'window_size': (1250, 800)}

        self.page_linear_dt_info = {'msg': fail_msg,
                                    'title': "Learn about: Linear drift-time analysis",
                                    'window_size': (1250, 800)}
