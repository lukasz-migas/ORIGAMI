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
        "AACBtS4tQxr8zJcqTgAAAABJRU5ErkJggg==")
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
        self.iconsLib['process_unidec_16'] = icons16.GetSubBitmap(wx.Rect(442,68,16,16))
        self.iconsLib['panel_log_16'] = icons16.GetSubBitmap(wx.Rect(459,68,16,16))
        self.iconsLib['panel_violin_16'] = icons16.GetSubBitmap(wx.Rect(476,68,16,16))
        self.iconsLib['randomize_16'] = icons16.GetSubBitmap(wx.Rect(493,68,16,16))
        
        # LINE 6
        self.iconsLib['blank_16'] = icons16.GetSubBitmap(wx.Rect(0,85,16,16))
        self.iconsLib['plot_waterfall_16'] = icons16.GetSubBitmap(wx.Rect(17,85,16,16))
        self.iconsLib['plot_bar_16'] = icons16.GetSubBitmap(wx.Rect(34,85,16,16))
        self.iconsLib['panel_plot_general_16'] = icons16.GetSubBitmap(wx.Rect(51,85,16,16))
        self.iconsLib['guide_16'] = icons16.GetSubBitmap(wx.Rect(68,85,16,16))
        self.iconsLib['exit_16'] = icons16.GetSubBitmap(wx.Rect(85,85,16,16))
        self.iconsLib['check_online_16'] = icons16.GetSubBitmap(wx.Rect(102,85,16,16))
        self.iconsLib['duplicate_16'] = icons16.GetSubBitmap(wx.Rect(119,85,16,16))
        self.iconsLib['parameters_16'] = icons16.GetSubBitmap(wx.Rect(136,85,16,16))
        
        # LINE 1 (24x24)
        self.iconsLib['folderOrigami'] = icons16.GetSubBitmap(wx.Rect(0,102,24,24))
        self.iconsLib['folderMassLynx'] = icons16.GetSubBitmap(wx.Rect(25,102,24,24))
        self.iconsLib['folderText'] = icons16.GetSubBitmap(wx.Rect(50,102,24,24))
        self.iconsLib['folderProject'] = icons16.GetSubBitmap(wx.Rect(75,102,24,24))
        self.iconsLib['folderTextMany'] = icons16.GetSubBitmap(wx.Rect(100,102,24,24))
        self.iconsLib['folderMassLynxMany'] = icons16.GetSubBitmap(wx.Rect(125,102,24,24))
        self.iconsLib['panel_legend'] = icons16.GetSubBitmap(wx.Rect(200,102,24,24))
        self.iconsLib['panel_colorbar'] = icons16.GetSubBitmap(wx.Rect(225,102,24,24))
        self.iconsLib['panel_plot1D'] = icons16.GetSubBitmap(wx.Rect(249,102,24,24))
        self.iconsLib['panel_plot2D'] = icons16.GetSubBitmap(wx.Rect(275,102,24,24))
        self.iconsLib['panel_plot3D'] = icons16.GetSubBitmap(wx.Rect(300,102,24,24))
        
        # LINE 2 (24x24)
        self.iconsLib['saveDoc'] = icons16.GetSubBitmap(wx.Rect(100,127,24,24))
        self.iconsLib['bokehLogo'] = icons16.GetSubBitmap(wx.Rect(175,127,24,24))
        self.iconsLib['panel_waterfall'] = icons16.GetSubBitmap(wx.Rect(225,127,24,24))
        self.iconsLib['panel_rmsd'] = icons16.GetSubBitmap(wx.Rect(250,127,24,24))
        
        # LINE 3 (24x24)
        self.iconsLib['panelCCS'] = icons16.GetSubBitmap(wx.Rect(25,152,24,24))
        self.iconsLib['panelDT'] = icons16.GetSubBitmap(wx.Rect(50,152,24,24))
        self.iconsLib['panelIon'] = icons16.GetSubBitmap(wx.Rect(75,152,24,24))
        self.iconsLib['panelML'] = icons16.GetSubBitmap(wx.Rect(100,152,24,24))
        self.iconsLib['panelParameters'] = icons16.GetSubBitmap(wx.Rect(125,152,24,24))
        self.iconsLib['panelText'] = icons16.GetSubBitmap(wx.Rect(150,152,24,24))
        self.iconsLib['panelDoc'] = icons16.GetSubBitmap(wx.Rect(175,152,24,24))
        
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
        
        
        