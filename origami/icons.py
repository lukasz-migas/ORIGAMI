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

import wx
from wx.lib.embeddedimage import PyEmbeddedImage

class IconContainer:
    def __init__(self):
        
        self.icons()
        self.loadBullets()
        self.loadIcons()
         
    def icons(self):
        
        origamiLogo = PyEmbeddedImage(
        "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"
        "JSGEEDImIv8fYJkezyZa7LkAAAAASUVORK5CYII=")
        self.getLogo = origamiLogo.GetBitmap()


        
        
        #----------------------------------------------------------------------
        bullets = PyEmbeddedImage(
        "iVBORw0KGgoAAAANSUhEUgAAAI8AAAAYCAYAAADDAK5oAAAAAXNSR0IArs4c6QAAAARnQU1B"
        "AACxjwv8YQUAAAAJcEhZcwAADsIAAA7CARUoSoAAAAL5SURBVGhD7Zk7khMxEIZtAh8AUjaD"
        "jAxyCJd0T8kNIIQcTgAZpHAAJ8v8g37T09ut52i8LuurkkfS9EutHnlc3t9P7AaDChbFs9/v"
        "Q2/JqK//udG58HKmkXpb6fTmQfFYzr35VpiQLRdcg944GW9ObrRMSsfKS42f3jzBB5wyYPY5"
        "7gXsY6FoMV9bxePBOEuQMZfGXeKvxc8azMUDuJGylQTUM3jEAkoSdTgcTk3izVvAj84DY0nB"
        "HObKA/orocbPWpyKB3BjZLJqidnQSUI/5VMnKSaPwjgej2H0b8yrNW/BGKUf+vaAbGodHvSX"
        "Q4ufNVkUDzcndxHngvExiVYidWHIAkoBe/Ah7ebmpCZ/9FeC9OPloDdNJ48lt9UimDyZxBjy"
        "xMlBriNlvyRnGujlxA+0HznOtbEmF3nypNCFwrE3HyMnF7V5KykcjSyaWhutzD/VvUUwQODd"
        "5zz7+qrx5oF1Lya/NvAFSvzlxKdlcvxYOqV+enMqHg8vmJiOROpvpbMl15yH8ffEoJrFO89g"
        "UMLi5Plz8zL0ljz9+T30rhd+beiDenxtBVA8VqF4862wWB97ceqN05ua2jAtk9J59/7b7sun"
        "N81+ejMXT+rE6VE80mbMPhLy+/mLuX+OIuOG4ErkBlkbpvP57NePpA5hLrRMjZ/uTM7up83B"
        "5QGc9+5LcmQkUj6mG0KcZWRL4cl68xb0jSubxprTtrWMpQPe3n4NvTydlJ/eLF6YUclsrcgn"
        "VcOni6Cf8gkZNhCT1/Yp681b8EmX68A4BuzFbMaA3uePr8MoToufNVkUj96gxwrjYxKtROo5"
        "ji1ZTU3hkJr84R2nVEf6gT7a1jSdPFbAsRNnTZg8mcQYOTKSSzhxZNHk2liTizx5Uuj4Ofbm"
        "Y+ScOLDDVgI2vkTn7tWHU5NFc47CmZmS47488sXSuy9f8CgTTJ6uGs8WsO55dnoQW6tHTnxa"
        "BuOUH0snRY7MmkR/qgPvycj9eprMh952OltyzXkY/20NKtnt/gKxElRx0ovSxgAAAABJRU5E"
        "rkJggg==")
        self.getBulletsOnData = bullets.GetData
        self.getBulletsOnImage = bullets.GetImage
        self.getBulletsOnBitmap = bullets.GetBitmap
        
        icons_16 = PyEmbeddedImage(
        "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"
        "AABJRU5ErkJggg==")
        self.getIcons16Data = icons_16.GetData
        self.getIcons16Image = icons_16.GetImage
        self.getIcons16Bitmap = icons_16.GetBitmap


        
    #----------------------------------------------------------------------
        BgrToolbar = PyEmbeddedImage(
        "iVBORw0KGgoAAAANSUhEUgAAACMAAAAkCAYAAAAD3IPhAAAAGXRFWHRTb2Z0d2FyZQBBZG9i"
        "ZSBJbWFnZVJlYWR5ccllPAAAAD1JREFUeNrs0LEJACAUQ0E/OLibRytnSHGB1x+ZJKtlAwMD"
        "AwMDAwMDAwMDAwMDAwMD8zGv04LZTc9cAQYAXRFpP7LCOH4AAAAASUVORK5CYII=")
        self.getBgrToolbarData = BgrToolbar.GetData
        self.getBgrToolbarImage = BgrToolbar.GetImage
        self.getBgrToolbarBitmap = BgrToolbar.GetBitmap
        
    def loadBullets(self):
        self.bulletsLib = {}
        bulletsOn = self.getBulletsOnBitmap()
        self.bulletsLib['bulletsDoc'] = bulletsOn.GetSubBitmap(wx.Rect(0,0,13,12)) # 0
        self.bulletsLib['bulletsMS'] = bulletsOn.GetSubBitmap(wx.Rect(13,0,13,12)) # 1
        self.bulletsLib['bulletsDT'] = bulletsOn.GetSubBitmap(wx.Rect(26,0,13,12)) # 2
        self.bulletsLib['bulletsRT'] = bulletsOn.GetSubBitmap(wx.Rect(39,0,13,12)) # 3
        self.bulletsLib['bulletsDot'] = bulletsOn.GetSubBitmap(wx.Rect(52,0,13,12)) # 4
        self.bulletsLib['bulletsAnnot'] = bulletsOn.GetSubBitmap(wx.Rect(66,0,13,12)) # 5
        self.bulletsLib['bullets2DT'] = bulletsOn.GetSubBitmap(wx.Rect(79,0,13,12)) # 6
        self.bulletsLib['bulletsCalibration'] = bulletsOn.GetSubBitmap(wx.Rect(92,0,13,12)) # 7
        self.bulletsLib['bulletsOverlay'] = bulletsOn.GetSubBitmap(wx.Rect(105,0,13,12)) # 8
        
        self.bulletsLib['bulletsDocOn'] = bulletsOn.GetSubBitmap(wx.Rect(0,11,13,12)) # 9
        self.bulletsLib['bulletsMSIon'] = bulletsOn.GetSubBitmap(wx.Rect(13,11,13,12)) # 10
        self.bulletsLib['bulletsDTIon'] = bulletsOn.GetSubBitmap(wx.Rect(26,11,13,12)) # 11
        self.bulletsLib['bulletsRTIon'] = bulletsOn.GetSubBitmap(wx.Rect(39,11,13,12)) # 12
        self.bulletsLib['bulletsDotOn'] = bulletsOn.GetSubBitmap(wx.Rect(52,11,13,12)) # 13
        self.bulletsLib['bulletsAnnotIon'] = bulletsOn.GetSubBitmap(wx.Rect(66,11,13,12)) # 14
        self.bulletsLib['bullets2DTIon'] = bulletsOn.GetSubBitmap(wx.Rect(79,11,13,12)) # 15
        self.bulletsLib['bulletsCalibrationIon'] = bulletsOn.GetSubBitmap(wx.Rect(92,11,13,12)) # 16
        self.bulletsLib['bulletsOverlayIon'] = bulletsOn.GetSubBitmap(wx.Rect(105,11,13,12)) # 17
        
    def loadIcons(self):
        self.iconsLib = {}
        icons16 = self.getIcons16Bitmap()
        
        self.iconsLib['blank_16'] = icons16.GetSubBitmap(wx.Rect(0,212,16,16))
        
        # LINE 1
        self.iconsLib['open16'] = icons16.GetSubBitmap(wx.Rect(0,0,16,16))
        self.iconsLib['extract16'] = icons16.GetSubBitmap(wx.Rect(17,0,16,16))
        self.iconsLib['add16'] = icons16.GetSubBitmap(wx.Rect(34,0,16,16))
        self.iconsLib['remove16'] = icons16.GetSubBitmap(wx.Rect(51,0,16,16))
        self.iconsLib['bin16'] = icons16.GetSubBitmap(wx.Rect(68,0,16,16))
        self.iconsLib['overlay16'] = icons16.GetSubBitmap(wx.Rect(85,0,16,16))
        self.iconsLib['save16'] = icons16.GetSubBitmap(wx.Rect(102,0,16,16))
        self.iconsLib['scatter16'] = icons16.GetSubBitmap(wx.Rect(119,0,16,16))
        self.iconsLib['process16'] = icons16.GetSubBitmap(wx.Rect(136,0,16,16))
        self.iconsLib['filter16'] = icons16.GetSubBitmap(wx.Rect(153,0,16,16))
        self.iconsLib['print16'] = icons16.GetSubBitmap(wx.Rect(170,0,16,16))
        self.iconsLib['combine16'] = icons16.GetSubBitmap(wx.Rect(187,0,16,16))
        self.iconsLib['examine16'] = icons16.GetSubBitmap(wx.Rect(204,0,16,16))
        self.iconsLib['refresh16'] = icons16.GetSubBitmap(wx.Rect(221,0,16,16))
        self.iconsLib['process_extract_16'] = icons16.GetSubBitmap(wx.Rect(238,0,16,16))
        self.iconsLib['process_ms_16'] = icons16.GetSubBitmap(wx.Rect(255,0,16,16))
        self.iconsLib['process_2d_16'] = icons16.GetSubBitmap(wx.Rect(272,0,16,16))
        self.iconsLib['process_origami_16'] = icons16.GetSubBitmap(wx.Rect(289,0,16,16))
        self.iconsLib['process_fit_16'] = icons16.GetSubBitmap(wx.Rect(306,0,16,16))
        self.iconsLib['process_extract2_16'] = icons16.GetSubBitmap(wx.Rect(323,0,16,16))
        self.iconsLib['save_as_16'] = icons16.GetSubBitmap(wx.Rect(340,0,16,16))
        self.iconsLib['save_multiple_16'] = icons16.GetSubBitmap(wx.Rect(357,0,16,16))
        self.iconsLib['save_png_16'] = icons16.GetSubBitmap(wx.Rect(374,0,16,16))
        self.iconsLib['mask_16'] = icons16.GetSubBitmap(wx.Rect(391,0,16,16))
        self.iconsLib['new_document_16'] = icons16.GetSubBitmap(wx.Rect(408,0,16,16))
        self.iconsLib['highlight_16'] = icons16.GetSubBitmap(wx.Rect(425,0,16,16))
        self.iconsLib['web_access_16'] = icons16.GetSubBitmap(wx.Rect(442,0,16,16))
        self.iconsLib['export_config_16'] = icons16.GetSubBitmap(wx.Rect(459,0,16,16))
        self.iconsLib['import_config_16'] = icons16.GetSubBitmap(wx.Rect(476,0,16,16))
        self.iconsLib['heatmap_grid_16'] = icons16.GetSubBitmap(wx.Rect(493,0,16,16))
        
        # LINE 2
        self.iconsLib['calibration16'] = icons16.GetSubBitmap(wx.Rect(0,17,16,16))
        self.iconsLib['ms16'] = icons16.GetSubBitmap(wx.Rect(17,17,16,16))
        self.iconsLib['rt16'] = icons16.GetSubBitmap(wx.Rect(34,17,16,16))
        self.iconsLib['annotate16'] = icons16.GetSubBitmap(wx.Rect(51,17,16,16))
        self.iconsLib['document16'] = icons16.GetSubBitmap(wx.Rect(68,17,16,16))
        self.iconsLib['info16'] = icons16.GetSubBitmap(wx.Rect(85,17,16,16))
        self.iconsLib['tick16'] = icons16.GetSubBitmap(wx.Rect(102,17,16,16))
        self.iconsLib['cross16'] = icons16.GetSubBitmap(wx.Rect(119,17,16,16))
        self.iconsLib['folder16'] = icons16.GetSubBitmap(wx.Rect(136,17,16,16))
        self.iconsLib['idea16'] = icons16.GetSubBitmap(wx.Rect(153,17,16,16))
        self.iconsLib['setting16'] = icons16.GetSubBitmap(wx.Rect(170,17,16,16))
        self.iconsLib['bars16'] = icons16.GetSubBitmap(wx.Rect(187,17,16,16))
        self.iconsLib['chromeBW16'] = icons16.GetSubBitmap(wx.Rect(204,17,16,16))
        self.iconsLib['ieBW16'] = icons16.GetSubBitmap(wx.Rect(221,17,16,16))
        self.iconsLib['panel_ccs_16'] = icons16.GetSubBitmap(wx.Rect(238,17,16,16))
        self.iconsLib['panel_dt_16'] = icons16.GetSubBitmap(wx.Rect(255,17,16,16))
        self.iconsLib['panel_ion_16'] = icons16.GetSubBitmap(wx.Rect(272,17,16,16))
        self.iconsLib['panel_mll__16'] = icons16.GetSubBitmap(wx.Rect(289,17,16,16))
        self.iconsLib['panel_text_16'] = icons16.GetSubBitmap(wx.Rect(306,17,16,16))
        self.iconsLib['panel_params_16'] = icons16.GetSubBitmap(wx.Rect(323,17,16,16))
        self.iconsLib['panel_doc_16'] = icons16.GetSubBitmap(wx.Rect(340,17,16,16))
        self.iconsLib['show_table_16'] = icons16.GetSubBitmap(wx.Rect(357,17,16,16))
        self.iconsLib['hide_table_16'] = icons16.GetSubBitmap(wx.Rect(374,17,16,16))
        self.iconsLib['color_panel_16'] = icons16.GetSubBitmap(wx.Rect(391,17,16,16))
        self.iconsLib['zoom_16'] = icons16.GetSubBitmap(wx.Rect(408,17,16,16))
        self.iconsLib['filelist_16'] = icons16.GetSubBitmap(wx.Rect(425,17,16,16))
        self.iconsLib['color_palette_16'] = icons16.GetSubBitmap(wx.Rect(442,17,16,16))
        self.iconsLib['driftscope_16'] = icons16.GetSubBitmap(wx.Rect(459,17,16,16))
        self.iconsLib['masslynx_16'] = icons16.GetSubBitmap(wx.Rect(476,17,16,16))
        self.iconsLib['panel_general2_16'] = icons16.GetSubBitmap(wx.Rect(493,17,16,16))

        # LINE 3
        self.iconsLib['check16'] = icons16.GetSubBitmap(wx.Rect(0,34,16,16))
        self.iconsLib['origamiLogo16'] = icons16.GetSubBitmap(wx.Rect(17,34,16,16))
        self.iconsLib['plotIMS16'] = icons16.GetSubBitmap(wx.Rect(34,34,16,16))
        self.iconsLib['plotIMSoverlay16'] = icons16.GetSubBitmap(wx.Rect(51,34,16,16))
        self.iconsLib['plotCalibration16'] = icons16.GetSubBitmap(wx.Rect(68,34,16,16))
        self.iconsLib['documentTwo16'] = icons16.GetSubBitmap(wx.Rect(102,34,16,16))
        self.iconsLib['settings16_2'] = icons16.GetSubBitmap(wx.Rect(119,34,16,16))
        self.iconsLib['reload16'] = icons16.GetSubBitmap(wx.Rect(136,34,16,16))
        self.iconsLib['load16'] = icons16.GetSubBitmap(wx.Rect(153,34,16,16))       
        self.iconsLib['github16'] = icons16.GetSubBitmap(wx.Rect(170,34,16,16))
        self.iconsLib['youtube16'] = icons16.GetSubBitmap(wx.Rect(187,34,16,16))
        self.iconsLib['chromeC16'] = icons16.GetSubBitmap(wx.Rect(204,34,16,16))
        self.iconsLib['ieC16'] = icons16.GetSubBitmap(wx.Rect(221,34,16,16))
        self.iconsLib['open_origami_16'] = icons16.GetSubBitmap(wx.Rect(238,34,16,16))
        self.iconsLib['open_masslynx_16'] = icons16.GetSubBitmap(wx.Rect(255,34,16,16))
        self.iconsLib['open_project_16'] = icons16.GetSubBitmap(wx.Rect(272,34,16,16))
        self.iconsLib['open_text_16'] = icons16.GetSubBitmap(wx.Rect(289,34,16,16))
        self.iconsLib['open_agilent_16'] = icons16.GetSubBitmap(wx.Rect(306,34,16,16))
        self.iconsLib['maximize_16'] = icons16.GetSubBitmap(wx.Rect(323,34,16,16))
        self.iconsLib['minimize_16'] = icons16.GetSubBitmap(wx.Rect(340,34,16,16))
        self.iconsLib['clear_16'] = icons16.GetSubBitmap(wx.Rect(357,34,16,16))
        self.iconsLib['mobiligram_16'] = icons16.GetSubBitmap(wx.Rect(408,34,16,16))
        self.iconsLib['mass_spectrum_16'] = icons16.GetSubBitmap(wx.Rect(425,34,16,16))
        self.iconsLib['heatmap_16'] = icons16.GetSubBitmap(wx.Rect(442,34,16,16))
        self.iconsLib['export2_config_16'] = icons16.GetSubBitmap(wx.Rect(459,34,16,16))
        self.iconsLib['import2_config_16'] = icons16.GetSubBitmap(wx.Rect(476,34,16,16))
        self.iconsLib['folder_path_16'] = icons16.GetSubBitmap(wx.Rect(493,34,16,16))
        
        # LINE 4
        self.iconsLib['rmsdBottomLeft'] = icons16.GetSubBitmap(wx.Rect(0,51,16,16))
        self.iconsLib['rmsdTopLeft'] = icons16.GetSubBitmap(wx.Rect(17,51,16,16))
        self.iconsLib['rmsdTopRight'] = icons16.GetSubBitmap(wx.Rect(34,51,16,16))
        self.iconsLib['rmsdBottomRight'] = icons16.GetSubBitmap(wx.Rect(51,51,16,16))
        self.iconsLib['rmsdNone'] = icons16.GetSubBitmap(wx.Rect(68,51,16,16))
        self.iconsLib['origamiLogoDark16'] = icons16.GetSubBitmap(wx.Rect(85,51,16,16))
        self.iconsLib['panel_legend_16'] = icons16.GetSubBitmap(wx.Rect(102,51,16,16))
        self.iconsLib['panel_colorbar_16'] = icons16.GetSubBitmap(wx.Rect(119,51,16,16))
        self.iconsLib['panel_plot1D_16'] = icons16.GetSubBitmap(wx.Rect(136,51,16,16))
        self.iconsLib['panel_plot2D_16'] = icons16.GetSubBitmap(wx.Rect(153,51,16,16))       
        self.iconsLib['panel_plot3D_16'] = icons16.GetSubBitmap(wx.Rect(170,51,16,16))
        self.iconsLib['panel_waterfall_16'] = icons16.GetSubBitmap(wx.Rect(187,51,16,16))
        self.iconsLib['panel_rmsd_16'] = icons16.GetSubBitmap(wx.Rect(204,51,16,16))
        self.iconsLib['bokehLogo_16'] = icons16.GetSubBitmap(wx.Rect(221,51,16,16))
        self.iconsLib['open_origamiMany_16'] = icons16.GetSubBitmap(wx.Rect(238,51,16,16))
        self.iconsLib['open_masslynxMany_16'] = icons16.GetSubBitmap(wx.Rect(255,51,16,16))
        self.iconsLib['open_projectMany_16'] = icons16.GetSubBitmap(wx.Rect(272,51,16,16))
        self.iconsLib['open_textMany_16'] = icons16.GetSubBitmap(wx.Rect(289,51,16,16))
        self.iconsLib['open_agilentMany_16'] = icons16.GetSubBitmap(wx.Rect(306,51,16,16))
        
        self.iconsLib['min_threshold_16'] = icons16.GetSubBitmap(wx.Rect(323,51,16,16))
        self.iconsLib['max_threshold_16'] = icons16.GetSubBitmap(wx.Rect(340,51,16,16))
        self.iconsLib['ccs_table_16'] = icons16.GetSubBitmap(wx.Rect(357,51,16,16))
        self.iconsLib['assign_charge_16'] = icons16.GetSubBitmap(wx.Rect(374,51,16,16))
        self.iconsLib['transparency_16'] = icons16.GetSubBitmap(wx.Rect(390,51,16,16))
        self.iconsLib['overlay_2D_16'] = icons16.GetSubBitmap(wx.Rect(408,51,16,16))
        self.iconsLib['chromatogram_16'] = icons16.GetSubBitmap(wx.Rect(425,51,16,16))
        self.iconsLib['compare_mass_spectra_16'] = icons16.GetSubBitmap(wx.Rect(442,51,16,16))
        self.iconsLib['change_xlabels_16'] = icons16.GetSubBitmap(wx.Rect(459,51,16,16))
        self.iconsLib['change_ylabels_16'] = icons16.GetSubBitmap(wx.Rect(476,51,16,16))

        # LINE 5
        self.iconsLib['request_16'] = icons16.GetSubBitmap(wx.Rect(0,68,16,16))
        self.iconsLib['file_pdf'] = icons16.GetSubBitmap(wx.Rect(17,68,16,16))
        self.iconsLib['folder_picture'] = icons16.GetSubBitmap(wx.Rect(34,68,16,16))
        self.iconsLib['folder_camera'] = icons16.GetSubBitmap(wx.Rect(51,68,16,16))
        self.iconsLib['folder_planet'] = icons16.GetSubBitmap(wx.Rect(68,68,16,16))
        self.iconsLib['folder_trace'] = icons16.GetSubBitmap(wx.Rect(85,68,16,16))
        self.iconsLib['file_zip_16'] = icons16.GetSubBitmap(wx.Rect(102,68,16,16))
        self.iconsLib['file_pdf_16'] = icons16.GetSubBitmap(wx.Rect(119,68,16,16))
        self.iconsLib['file_txt_16'] = icons16.GetSubBitmap(wx.Rect(136,68,16,16))
        self.iconsLib['file_png_16'] = icons16.GetSubBitmap(wx.Rect(153,68,16,16))       
        self.iconsLib['file_csv_16'] = icons16.GetSubBitmap(wx.Rect(170,68,16,16))

        self.iconsLib['aa3to1_16'] = icons16.GetSubBitmap(wx.Rect(204,68,16,16))
        self.iconsLib['aa1to3_16'] = icons16.GetSubBitmap(wx.Rect(221,68,16,16))
        self.iconsLib['pickle_16'] = icons16.GetSubBitmap(wx.Rect(238,68,16,16))
        self.iconsLib['google_logo_16'] = icons16.GetSubBitmap(wx.Rect(255,68,16,16))
        self.iconsLib['bug_16'] = icons16.GetSubBitmap(wx.Rect(272,68,16,16))
        self.iconsLib['cite_16'] = icons16.GetSubBitmap(wx.Rect(289,68,16,16))
        self.iconsLib['fullscreen_16'] = icons16.GetSubBitmap(wx.Rect(306,68,16,16))
        
        self.iconsLib['panel_legend2_16'] = icons16.GetSubBitmap(wx.Rect(323,68,16,16))
        self.iconsLib['scatter2_16'] = icons16.GetSubBitmap(wx.Rect(340,68,16,16))
        self.iconsLib['panel_classifier_16'] = icons16.GetSubBitmap(wx.Rect(357,68,16,16))
        self.iconsLib['panel_crossValidation_16'] = icons16.GetSubBitmap(wx.Rect(374,68,16,16))
        self.iconsLib['panel_unsupervised_16'] = icons16.GetSubBitmap(wx.Rect(391,68,16,16))
        self.iconsLib['panel_supervised_16'] = icons16.GetSubBitmap(wx.Rect(408,68,16,16))
        self.iconsLib['panel_learner_16'] = icons16.GetSubBitmap(wx.Rect(425,68,16,16))
        
        self.iconsLib['process_unidec_16'] = icons16.GetSubBitmap(wx.Rect(442,68,16,16))
        self.iconsLib['panel_log_16'] = icons16.GetSubBitmap(wx.Rect(459,68,16,16))
        self.iconsLib['panel_violin_16'] = icons16.GetSubBitmap(wx.Rect(476,68,16,16))
        self.iconsLib['randomize_16'] = icons16.GetSubBitmap(wx.Rect(493,68,16,16))
        
        # LINE 6
        self.iconsLib['guide_16'] = icons16.GetSubBitmap(wx.Rect(0,85,16,16))
        self.iconsLib['exit_16'] = icons16.GetSubBitmap(wx.Rect(17,85,16,16))
        self.iconsLib['check_online_16'] = icons16.GetSubBitmap(wx.Rect(34,85,16,16))
        self.iconsLib['duplicate_16'] = icons16.GetSubBitmap(wx.Rect(51,85,16,16))
        self.iconsLib['parameters_16'] = icons16.GetSubBitmap(wx.Rect(68,85,16,16))
        self.iconsLib['open_source_16'] = icons16.GetSubBitmap(wx.Rect(85,85,16,16))
        self.iconsLib['sort_16'] = icons16.GetSubBitmap(wx.Rect(102,85,16,16))
        self.iconsLib['open_file_16'] = icons16.GetSubBitmap(wx.Rect(119,85,16,16))
        self.iconsLib['connection_16'] = icons16.GetSubBitmap(wx.Rect(136,85,16,16))
        self.iconsLib['search_16'] = icons16.GetSubBitmap(wx.Rect(153,85,16,16))       
        self.iconsLib['brain_16'] = icons16.GetSubBitmap(wx.Rect(170,85,16,16))
        self.iconsLib['brain_16'] = icons16.GetSubBitmap(wx.Rect(170,85,16,16))
        self.iconsLib['data_reduce_16'] = icons16.GetSubBitmap(wx.Rect(187,85,16,16))
        self.iconsLib['machine_learning_16'] = icons16.GetSubBitmap(wx.Rect(204,85,16,16))
        
        # these were accidentally removed...
        self.iconsLib['plot_waterfall_16'] = icons16.GetSubBitmap(wx.Rect(0,212,16,16))
        self.iconsLib['plot_bar_16'] = icons16.GetSubBitmap(wx.Rect(0,212,16,16))
        self.iconsLib['panel_plot_general_16'] = icons16.GetSubBitmap(wx.Rect(68,85,16,16))
        
#         # LINE 1 (24x24)
#         self.iconsLib['folderOrigami'] = icons16.GetSubBitmap(wx.Rect(0,102,24,24))
#         self.iconsLib['folderMassLynx'] = icons16.GetSubBitmap(wx.Rect(25,102,24,24))
#         self.iconsLib['folderText'] = icons16.GetSubBitmap(wx.Rect(50,102,24,24))
#         self.iconsLib['folderProject'] = icons16.GetSubBitmap(wx.Rect(75,102,24,24))
#         self.iconsLib['folderTextMany'] = icons16.GetSubBitmap(wx.Rect(100,102,24,24))
#         self.iconsLib['folderMassLynxMany'] = icons16.GetSubBitmap(wx.Rect(125,102,24,24))
#         self.iconsLib['panel_legend'] = icons16.GetSubBitmap(wx.Rect(200,102,24,24))
#         self.iconsLib['panel_colorbar'] = icons16.GetSubBitmap(wx.Rect(225,102,24,24))
#         self.iconsLib['panel_plot1D'] = icons16.GetSubBitmap(wx.Rect(249,102,24,24))
#         self.iconsLib['panel_plot2D'] = icons16.GetSubBitmap(wx.Rect(275,102,24,24))
#         self.iconsLib['panel_plot3D'] = icons16.GetSubBitmap(wx.Rect(300,102,24,24))
#         
#         # LINE 2 (24x24)
#         self.iconsLib['saveDoc'] = icons16.GetSubBitmap(wx.Rect(100,127,24,24))
#         self.iconsLib['bokehLogo'] = icons16.GetSubBitmap(wx.Rect(175,127,24,24))
#         self.iconsLib['panel_waterfall'] = icons16.GetSubBitmap(wx.Rect(225,127,24,24))
#         self.iconsLib['panel_rmsd'] = icons16.GetSubBitmap(wx.Rect(250,127,24,24))
#         
#         # LINE 3 (24x24)
#         self.iconsLib['panelCCS'] = icons16.GetSubBitmap(wx.Rect(25,152,24,24))
#         self.iconsLib['panelDT'] = icons16.GetSubBitmap(wx.Rect(50,152,24,24))
#         self.iconsLib['panelIon'] = icons16.GetSubBitmap(wx.Rect(75,152,24,24))
#         self.iconsLib['panelML'] = icons16.GetSubBitmap(wx.Rect(100,152,24,24))
#         self.iconsLib['panelParameters'] = icons16.GetSubBitmap(wx.Rect(125,152,24,24))
#         self.iconsLib['panelText'] = icons16.GetSubBitmap(wx.Rect(150,152,24,24))
#         self.iconsLib['panelDoc'] = icons16.GetSubBitmap(wx.Rect(175,152,24,24))
        
        # listed colormaps
        self.iconsLib['cmap_hls'] = icons16.GetSubBitmap(wx.Rect(408,102,64,16))
        self.iconsLib['cmap_husl'] = icons16.GetSubBitmap(wx.Rect(408,119,64,16))
        self.iconsLib['cmap_cubehelix'] = icons16.GetSubBitmap(wx.Rect(408,136,64,16))
        self.iconsLib['cmap_spectral'] = icons16.GetSubBitmap(wx.Rect(408,153,64,16))
        self.iconsLib['cmap_viridis'] = icons16.GetSubBitmap(wx.Rect(408,170,64,16))
        self.iconsLib['cmap_rainbow'] = icons16.GetSubBitmap(wx.Rect(408,187,64,16))
        self.iconsLib['cmap_inferno'] = icons16.GetSubBitmap(wx.Rect(408,204,64,16))
        self.iconsLib['cmap_cividis'] = icons16.GetSubBitmap(wx.Rect(408,221,64,16))
        
        self.iconsLib['cmap_cool'] = icons16.GetSubBitmap(wx.Rect(473,102,64,16))
        self.iconsLib['cmap_gray'] = icons16.GetSubBitmap(wx.Rect(473,119,64,16))
        self.iconsLib['cmap_rdpu'] = icons16.GetSubBitmap(wx.Rect(473,136,64,16))
        self.iconsLib['cmap_tab20b'] = icons16.GetSubBitmap(wx.Rect(473,153,64,16))
        self.iconsLib['cmap_tab20c'] = icons16.GetSubBitmap(wx.Rect(473,170,64,16))
        self.iconsLib['cmap_modern1'] = icons16.GetSubBitmap(wx.Rect(473,187,64,16))
        self.iconsLib['cmap_modern2'] = icons16.GetSubBitmap(wx.Rect(473,204,64,16))
        self.iconsLib['cmap_winter'] = icons16.GetSubBitmap(wx.Rect(473,221,64,16))
        
        # TOOLBAR
        self.iconsLib['bgrToolbar'] = self.getBgrToolbarBitmap()
        
        
        