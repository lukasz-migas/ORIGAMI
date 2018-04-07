# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017 Lukasz G. Migas <lukasz.migas@manchester.ac.uk>
# 
#     GitHub : https://github.com/lukasz-migas/ORIGAMI
#     University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#     Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
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
        self.ionPanel_overwrite = {'help_title':'Overwriting previous results', 'help_msg':msg, 
                                   'header_img': None,
                                   'header_line':header_line, 'footer_line':footer_line}
        
        msg = 'If checked, any processing (i.e. combining collision voltage scans)\n' + \
              'will be performed with parameters that are already retained within the\n' + \
              'the ORIGAMI document. If these parameters are NOT present, parameters currently\n' + \
              'entered in the ORIGAMI GUI will be used instead.'
        self.ionPanel_useInternalParams = {'help_title':'Use internal parameters', 'help_msg':msg, 
                                           'header_img': None,
                                           'header_line':header_line, 'footer_line':footer_line}

    # -----------
        # Process panel (Extract)
        msg = "Pusher frequency in microseconds. Only used when drift time values\n" + \
              "are entered in miliseconds as the extraction program expects bins."
        self.extract_pusherFreq = {'help_title':'Pusher frequency', 'help_msg':msg, 
                                   'header_img': None,
                                   'header_line':header_line, 'footer_line':footer_line}
        
        msg = 'Scan time in seconds. Only used when the retention time is entered in\n' + \
              'scans as the extraction program expects minutes.'
        self.extract_scanTime = {'help_title':'Scan time', 'help_msg':msg, 
                                 'header_img': None,
                                 'header_line':header_line, 'footer_line':footer_line}
        
        msg = "If checked, retention time will be assumed to be in scans rather\n" + \
              "than in minutes."
        self.extract_in_scans = {'help_title':'Retention time units', 'help_msg':msg, 
                                 'header_img': None,
                                 'header_line':header_line, 'footer_line':footer_line}
        
        msg = "If checked, drift time will be assumed to be miliseconds\n" + \
              "rather than in bins."
        self.extract_in_ms = {'help_title':'Drift time units', 'help_msg':msg, 
                              'header_img': None,
                              'header_line':header_line, 'footer_line':footer_line}
        
        msg = "Enter retention time values. Values typically in minutes."
        self.extract_rt = {'help_title':'Retention time', 'help_msg':msg, 
                           'header_img': None,
                           'header_line':header_line, 'footer_line':footer_line}
        
        msg = "Enter drift time values. Values typically in bins."
        self.extract_dt = {'help_title':'Drift time', 'help_msg':msg, 
                           'header_img': None,
                           'header_line':header_line, 'footer_line':footer_line}
        
        msg = "Enter m/z values."
        self.extract_mz = {'help_title':'Mass spectra', 'help_msg':msg, 
                           'header_img': None,
                           'header_line':header_line, 'footer_line':footer_line}

    # -----------
        # Process panel (MS)
        msg = 'If checked, when extracting several scans from the\n' + \
              'chromatogram (RT) window, the mass spectra will be\n' + \
              'binned according to the values shown below.'
        self.bin_MS_in_RT = {'help_title':'Binning', 'help_msg':msg, 
                             'header_img': None,
                             'header_line':header_line, 'footer_line':footer_line}

        msg = 'If checked, when loading a list of multiple files,\n' + \
              'the mass spectra will be automatically binned\n' + \
              'according to the values shown below.'
        self.bin_MS_when_loading_MML = {'help_title':'Binning', 'help_msg':msg, 
                                        'header_img': None,
                                        'header_line':header_line, 'footer_line':footer_line}
    # -----------
        # Process panel (peak fitting)
        msg = 'If checked, the algorithm will attempt to predict the charge state of \n' + \
              'found peaks. The algorithm looks for features in a narrow MS window \n' + \
              'which can be usually found if the peak resolution is sufficiently high.'
        self.fit_highRes = {'help_title':'Predict charge states', 'help_msg':msg,
                            'header_img':None,
                            'header_line':header_line, 'footer_line':footer_line}

        msg = 'If checked, isotopic peaks will be shown in the mass spectrum using\n' + \
              'using red circles. Adjust window size, threshold and peak width for best results.'
        self.fit_showIsotopes = {'help_title':'Show isotopic peaks in mass spectrum', 'help_msg':msg,
                                 'header_img':None,
                                 'header_line':header_line, 'footer_line':footer_line}
    # -----------
        # Compare MS panel
        msg = 'If checked, each mass spectrum will be smoothed,\n' + \
              'baseline subtracted and normalised. The type of preprocessing\n' + \
              'depends on the parameters shown in the Process: Mass spectrum panel.\n' + \
              'You can change these to obtain best results.\n'
        self.compareMS_preprocess = {'help_title':'Pre-processing mass spectra', 'help_msg':msg,
                                     'header_img':self.icons.iconsLib['process_ms_16'],
                                     'header_line':header_line, 'footer_line':footer_line}
    # -----------
        msg = 'Opens new window with plot settings.\n'
        self.compareMS_open_plot1D_settings = {'help_title':'Editing plot parameters', 'help_msg':msg,
                                              'header_img':self.icons.iconsLib['panel_plot1D_16'],
                                              'header_line':header_line, 'footer_line':footer_line}
    # -----------
        msg = 'Opens new window with legend settings.\n'
        self.compareMS_open_legend_settings = {'help_title':'Editing legend parameters', 'help_msg':msg,
                                              'header_img':self.icons.iconsLib['panel_legend_16'],
                                              'header_line':header_line, 'footer_line':footer_line}
    # -----------
        msg = 'Opens new window with mass spectrum processing settings.\n'
        self.compareMS_open_processMS_settings = {'help_title':'Editing processing parameters', 'help_msg':msg,
                                                  'header_img':self.icons.iconsLib['process_ms_16'],
                                                  'header_line':header_line, 'footer_line':footer_line}
    # -----------
    # Plotting panel - General settings
        msg = 'Please select which plot you would like to adjust. Names are simply the \n' + \
              'representations shown as the tab names in the Plots panel.'
        self.general_plotName = {'help_title':'Plot options - plot name', 'help_msg':msg,
                                 'header_img':None,
                                 'header_line':header_line, 'footer_line':footer_line}
    
        msg = 'The distance between the edge and the plot. Small values might not show labels.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_leftAxes = {'help_title':'Plot options - left edge', 'help_msg':msg,
                                 'header_img':None,
                                 'header_line':header_line, 'footer_line':footer_line}
        
        msg = 'The distance between the edge and the plot. Small values might not show labels.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_bottomAxes = {'help_title':'Plot options - bottom edge', 'help_msg':msg,
                                   'header_img':None,
                                   'header_line':header_line, 'footer_line':footer_line}
    
        msg = 'The width of the plot. This value compliments the LEFT edge.\n' + \
              ' When combined, it should not be larger than 1.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_widthAxes = {'help_title':'Plot options - width', 'help_msg':msg,
                                  'header_img':None,
                                  'header_line':header_line, 'footer_line':footer_line}
    
        msg = 'The height of the plot. This value compliments the BOTTOM edge.\n' + \
              ' When combined, it should not be larger than 1.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_heightAxes = {'help_title':'Plot options - height', 'help_msg':msg,
                                   'header_img':None,
                                   'header_line':header_line, 'footer_line':footer_line}
        
        msg = 'The distance between the edge and the plot. Small values might not show labels.\n' + \
              'These value differ from the ones shown above, as the figure export size can differ,\n' + \
              'from the one displayed in ORIGAMI GUI.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_leftAxes_export = {'help_title':'Plot options - left edge', 'help_msg':msg,
                                        'header_img':None,
                                        'header_line':header_line, 'footer_line':footer_line}
        
        msg = 'The distance between the edge and the plot. Small values might not show labels.\n' + \
              'These value differ from the ones shown above, as the figure export size can differ,\n' + \
              'from the one displayed in ORIGAMI GUI.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_bottomAxes_export = {'help_title':'Plot options - bottom edge', 'help_msg':msg,
                                          'header_img':None,
                                          'header_line':header_line, 'footer_line':footer_line}
    
        msg = 'The width of the plot. This value compliments the LEFT edge.\n' + \
              'These value differ from the ones shown above, as the figure export size can differ,\n' + \
              'from the one displayed in ORIGAMI GUI.\n' + \
              ' When combined, it should not be larger than 1.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_widthAxes_export = {'help_title':'Plot options - width', 'help_msg':msg,
                                         'header_img':None,
                                         'header_line':header_line, 'footer_line':footer_line}
    
        msg = 'The height of the plot. This value compliments the BOTTOM edge.\n' + \
              'These value differ from the ones shown above, as the figure export size can differ,\n' + \
              'from the one displayed in ORIGAMI GUI.\n' + \
              ' When combined, it should not be larger than 1.\n' + \
              'Values are shown as a proportion of the window (0-1).'
        self.general_heightAxes_export = {'help_title':'Plot options - height', 'help_msg':msg,
                                          'header_img':None,
                                          'header_line':header_line, 'footer_line':footer_line}
        
        msg = 'The width of the plot in inches. Ensures consistent plot size when exporting figures.'
        self.general_widthPlot_inch = {'help_title':'Plot options - width', 'help_msg':msg,
                                       'header_img':None,
                                       'header_line':header_line, 'footer_line':footer_line}
    
        msg = 'The height of the plot. Ensures consistent plot size when exporting figures.'
        self.general_heightPlot_inch = {'help_title':'Plot options - height', 'help_msg':msg,
                                        'header_img':None,
                                        'header_line':header_line, 'footer_line':footer_line}
    
        msg = 'The fraction at which the zooming tool changes from line to rectangle.\n' + \
              'The lower the value, the more sensitive the zooming becomes. Default: 0.03'
        self.general_zoom_crossover = {'help_title':'Zoom crossover sensitivity', 'help_msg':msg,
                                       'header_img':None,
                                       'header_line':header_line, 'footer_line':footer_line}
        
        msg = "When checked, figures will be automatically plotted when an appropriate item\n" + \
              "was selected in the Document Tree."
        self.general_instantPlot = {'help_title':'Instant plot', 'help_msg':msg,
                                    'header_img':None,
                                    'header_line':header_line, 'footer_line':footer_line}
        
        msg = "When checked, some of the 'slower' functions are exectured on a separate CPU thread\n" + \
              "meaning the GUI will not get locked (unusable). While it has been extensively tested\n" + \
              "this can still cause some problems and occasionally cause a crash."
        self.general_multiThreading = {'help_title':'Multi-threading', 'help_msg':msg,
                                    'header_img':None,
                                    'header_line':header_line, 'footer_line':footer_line}

        msg = "When checked, a new log file will appear in the ORIGAMI folder which keeps track of all your\n" + \
              "actions and in some cases, errors or warnings."
        self.general_logToFile = {'help_title':'Log events to file', 'help_msg':msg,
                                    'header_img':None,
                                    'header_line':header_line, 'footer_line':footer_line}
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        