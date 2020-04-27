# Third-party imports
# Local imports
import wx
from wx.lib.embeddedimage import PyEmbeddedImage

# Local imports
from origami.icons.embed import icons as icons_16


class IconContainer:
    def __init__(self):

        self.load_logos()
        self.load_bullets()
        self.load_icons()

    def load_logos(self):

        origamiLogo = PyEmbeddedImage(
            "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"
            "8eNtssFVb95mvoM+e2ri1PinyeULT7WnRnAes9W0sUW6unokFo3qY5QmAp4UgQ60q+bOkLLy"
            "0oSP2coE5xFdwcg7EisqsXNzgze2TT4ov1Jm1exl52SX5k2N4ulP/xQQLfbI7Noqeyr7uFm+"
            "trbXpb9/lj2VHvgxlS2wn2VKpuVxswyNm9eL9KX/GDFQFJ4mVXW72FO5o+BFCRqamqSmyr2D"
            "MRXqjbBrTZRLdk6ycQJJl2yejAkhE2dSiJIQQgjJFwV7jZIQQggpBChKQgghJAkUJSGEEJIE"
            "ipIQQghJAkVJCCGEJIGiJIQQQpJAURJCCCFJoCgJIYSQJFCUhBBCSBIoSkIIISQJFCUhhBCS"
            "BIqSEEIISQJFSQghhCSBoiSEEEKSQFESQgghSaAoCSGEkCRQlIQQQkgSKEpCCCEkCRQlIYQQ"
            "kgSKkhBCCEkCRUkIIYQkgaIkhBBCkkBREkIIIUmgKAkhhJAkUJSEEEJIEihKQgghJAkUJSGE"
            "EJIEipIQQghJAkVJCCGEJIGiJIQQQpJAURJCCCFJoCgJIYSQJFCUhBBCSBIoSkIIISQJFCUh"
            "hBCSBIqSEEIISQJFSQghhCSBoiSEEEKSQFESQgghSaAoCSGEkCRQlIQQQkgSKEpCCCEkCRQl"
            "IYQQkgSKkhBCCEkCRUkIIYQkgaIkhBBCkkBREkIIIUmgKAkhhJAkUJSEEEJIEihKQgghJAkU"
            "JSGEEDImIv8fYJkezyZa7LkAAAAASUVORK5CYII="
        )
        self.getLogo = origamiLogo.GetBitmap()

        # ----------------------------------------------------------------------
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
            "rkJggg=="
        )
        self.getBulletsOnData = bullets.GetData
        self.getBulletsOnImage = bullets.GetImage
        self.getBulletsOnBitmap = bullets.GetBitmap

        self.getIcons16Data = icons_16.GetData
        self.getIcons16Image = icons_16.GetImage
        self.getIcons16Bitmap = icons_16.GetBitmap

        # ----------------------------------------------------------------------
        BgrToolbar = PyEmbeddedImage(
            "iVBORw0KGgoAAAANSUhEUgAAACMAAAAkCAYAAAAD3IPhAAAAGXRFWHRTb2Z0d2FyZQBBZG9i"
            "ZSBJbWFnZVJlYWR5ccllPAAAAD1JREFUeNrs0LEJACAUQ0E/OLibRytnSHGB1x+ZJKtlAwMD"
            "AwMDAwMDAwMDAwMDAwMD8zGv04LZTc9cAQYAXRFpP7LCOH4AAAAASUVORK5CYII="
        )
        self.getBgrToolbarData = BgrToolbar.GetData
        self.getBgrToolbarImage = BgrToolbar.GetImage
        self.getBgrToolbarBitmap = BgrToolbar.GetBitmap

    def load_bullets(self):
        self.bulletsLib = {}
        bulletsOn = self.getBulletsOnBitmap()
        self.bulletsLib["bulletsDoc"] = bulletsOn.GetSubBitmap(wx.Rect(0, 0, 13, 12))  # 0
        self.bulletsLib["bulletsMS"] = bulletsOn.GetSubBitmap(wx.Rect(13, 0, 13, 12))  # 1
        self.bulletsLib["bulletsDT"] = bulletsOn.GetSubBitmap(wx.Rect(26, 0, 13, 12))  # 2
        self.bulletsLib["bulletsRT"] = bulletsOn.GetSubBitmap(wx.Rect(39, 0, 13, 12))  # 3
        self.bulletsLib["bulletsDot"] = bulletsOn.GetSubBitmap(wx.Rect(52, 0, 13, 12))  # 4
        self.bulletsLib["bulletsAnnot"] = bulletsOn.GetSubBitmap(wx.Rect(66, 0, 13, 12))  # 5
        self.bulletsLib["bullets2DT"] = bulletsOn.GetSubBitmap(wx.Rect(79, 0, 13, 12))  # 6
        self.bulletsLib["bulletsCalibration"] = bulletsOn.GetSubBitmap(wx.Rect(92, 0, 13, 12))  # 7
        self.bulletsLib["bulletsOverlay"] = bulletsOn.GetSubBitmap(wx.Rect(105, 0, 13, 12))  # 8

        self.bulletsLib["bulletsDocOn"] = bulletsOn.GetSubBitmap(wx.Rect(0, 11, 13, 12))  # 9
        self.bulletsLib["bulletsMSIon"] = bulletsOn.GetSubBitmap(wx.Rect(13, 11, 13, 12))  # 10
        self.bulletsLib["bulletsDTIon"] = bulletsOn.GetSubBitmap(wx.Rect(26, 11, 13, 12))  # 11
        self.bulletsLib["bulletsRTIon"] = bulletsOn.GetSubBitmap(wx.Rect(39, 11, 13, 12))  # 12
        self.bulletsLib["bulletsDotOn"] = bulletsOn.GetSubBitmap(wx.Rect(52, 11, 13, 12))  # 13
        self.bulletsLib["bulletsAnnotIon"] = bulletsOn.GetSubBitmap(wx.Rect(66, 11, 13, 12))  # 14
        self.bulletsLib["bullets2DTIon"] = bulletsOn.GetSubBitmap(wx.Rect(79, 11, 13, 12))  # 15
        self.bulletsLib["bulletsCalibrationIon"] = bulletsOn.GetSubBitmap(wx.Rect(92, 11, 13, 12))  # 16
        self.bulletsLib["bulletsOverlayIon"] = bulletsOn.GetSubBitmap(wx.Rect(105, 11, 13, 12))  # 17

    def load_icons(self):
        self.iconsLib = {}
        icons16 = self.getIcons16Bitmap()

        self.iconsLib["blank_16"] = icons16.GetSubBitmap(wx.Rect(0, 212, 16, 16))

        # LINE 1
        y = 0
        self.iconsLib["open16"] = icons16.GetSubBitmap(wx.Rect(0, y, 16, 16))
        self.iconsLib["extract16"] = icons16.GetSubBitmap(wx.Rect(17, y, 16, 16))
        self.iconsLib["add16"] = icons16.GetSubBitmap(wx.Rect(34, y, 16, 16))
        self.iconsLib["remove16"] = icons16.GetSubBitmap(wx.Rect(51, y, 16, 16))
        self.iconsLib["bin16"] = icons16.GetSubBitmap(wx.Rect(68, y, 16, 16))
        self.iconsLib["overlay16"] = icons16.GetSubBitmap(wx.Rect(85, y, 16, 16))
        self.iconsLib["save16"] = icons16.GetSubBitmap(wx.Rect(102, y, 16, 16))
        self.iconsLib["scatter16"] = icons16.GetSubBitmap(wx.Rect(119, y, 16, 16))
        self.iconsLib["process16"] = icons16.GetSubBitmap(wx.Rect(136, y, 16, 16))
        self.iconsLib["filter16"] = icons16.GetSubBitmap(wx.Rect(153, y, 16, 16))
        self.iconsLib["print16"] = icons16.GetSubBitmap(wx.Rect(170, y, 16, 16))
        self.iconsLib["combine16"] = icons16.GetSubBitmap(wx.Rect(187, y, 16, 16))
        self.iconsLib["examine16"] = icons16.GetSubBitmap(wx.Rect(204, y, 16, 16))
        self.iconsLib["refresh16"] = icons16.GetSubBitmap(wx.Rect(221, y, 16, 16))
        self.iconsLib["process_extract_16"] = icons16.GetSubBitmap(wx.Rect(238, y, 16, 16))
        self.iconsLib["process_ms_16"] = icons16.GetSubBitmap(wx.Rect(255, y, 16, 16))
        self.iconsLib["process_2d_16"] = icons16.GetSubBitmap(wx.Rect(272, y, 16, 16))
        self.iconsLib["process_origami_16"] = icons16.GetSubBitmap(wx.Rect(289, y, 16, 16))
        self.iconsLib["process_fit_16"] = icons16.GetSubBitmap(wx.Rect(306, y, 16, 16))
        self.iconsLib["process_extract2_16"] = icons16.GetSubBitmap(wx.Rect(323, y, 16, 16))
        self.iconsLib["save_as_16"] = icons16.GetSubBitmap(wx.Rect(340, y, 16, 16))
        self.iconsLib["save_multiple_16"] = icons16.GetSubBitmap(wx.Rect(357, y, 16, 16))
        self.iconsLib["save_png_16"] = icons16.GetSubBitmap(wx.Rect(374, y, 16, 16))
        self.iconsLib["mask_16"] = icons16.GetSubBitmap(wx.Rect(391, y, 16, 16))
        self.iconsLib["new_document_16"] = icons16.GetSubBitmap(wx.Rect(408, y, 16, 16))
        self.iconsLib["highlight_16"] = icons16.GetSubBitmap(wx.Rect(425, y, 16, 16))
        self.iconsLib["web_access_16"] = icons16.GetSubBitmap(wx.Rect(442, y, 16, 16))
        self.iconsLib["export_config_16"] = icons16.GetSubBitmap(wx.Rect(459, y, 16, 16))
        self.iconsLib["import_config_16"] = icons16.GetSubBitmap(wx.Rect(476, y, 16, 16))
        self.iconsLib["heatmap_grid_16"] = icons16.GetSubBitmap(wx.Rect(493, y, 16, 16))

        # LINE 2
        y += 17
        self.iconsLib["calibration16"] = icons16.GetSubBitmap(wx.Rect(0, y, 16, 16))
        self.iconsLib["ms16"] = icons16.GetSubBitmap(wx.Rect(17, y, 16, 16))
        self.iconsLib["rt16"] = icons16.GetSubBitmap(wx.Rect(34, y, 16, 16))
        self.iconsLib["annotate16"] = icons16.GetSubBitmap(wx.Rect(51, y, 16, 16))
        self.iconsLib["document16"] = icons16.GetSubBitmap(wx.Rect(68, y, 16, 16))
        self.iconsLib["info16"] = icons16.GetSubBitmap(wx.Rect(85, y, 16, 16))
        self.iconsLib["tick16"] = icons16.GetSubBitmap(wx.Rect(102, y, 16, 16))
        self.iconsLib["cross16"] = icons16.GetSubBitmap(wx.Rect(119, y, 16, 16))
        self.iconsLib["folder16"] = icons16.GetSubBitmap(wx.Rect(136, y, 16, 16))
        self.iconsLib["idea16"] = icons16.GetSubBitmap(wx.Rect(153, y, 16, 16))
        self.iconsLib["setting16"] = icons16.GetSubBitmap(wx.Rect(170, y, 16, 16))
        self.iconsLib["bars16"] = icons16.GetSubBitmap(wx.Rect(187, y, 16, 16))
        self.iconsLib["chromeBW16"] = icons16.GetSubBitmap(wx.Rect(204, y, 16, 16))
        self.iconsLib["ieBW16"] = icons16.GetSubBitmap(wx.Rect(221, y, 16, 16))
        self.iconsLib["panel_ccs_16"] = icons16.GetSubBitmap(wx.Rect(238, y, 16, 16))
        self.iconsLib["panel_dt_16"] = icons16.GetSubBitmap(wx.Rect(255, y, 16, 16))
        self.iconsLib["panel_ion_16"] = icons16.GetSubBitmap(wx.Rect(272, y, 16, 16))
        self.iconsLib["panel_mll__16"] = icons16.GetSubBitmap(wx.Rect(289, y, 16, 16))
        self.iconsLib["panel_text_16"] = icons16.GetSubBitmap(wx.Rect(306, y, 16, 16))
        self.iconsLib["panel_params_16"] = icons16.GetSubBitmap(wx.Rect(323, y, 16, 16))
        self.iconsLib["panel_doc_16"] = icons16.GetSubBitmap(wx.Rect(340, y, 16, 16))
        self.iconsLib["show_table_16"] = icons16.GetSubBitmap(wx.Rect(357, y, 16, 16))
        self.iconsLib["hide_table_16"] = icons16.GetSubBitmap(wx.Rect(374, y, 16, 16))
        self.iconsLib["color_panel_16"] = icons16.GetSubBitmap(wx.Rect(391, y, 16, 16))
        self.iconsLib["zoom_16"] = icons16.GetSubBitmap(wx.Rect(408, y, 16, 16))
        self.iconsLib["filelist_16"] = icons16.GetSubBitmap(wx.Rect(425, y, 16, 16))
        self.iconsLib["color_palette_16"] = icons16.GetSubBitmap(wx.Rect(442, y, 16, 16))
        self.iconsLib["driftscope_16"] = icons16.GetSubBitmap(wx.Rect(459, y, 16, 16))
        self.iconsLib["masslynx_16"] = icons16.GetSubBitmap(wx.Rect(476, y, 16, 16))
        self.iconsLib["panel_general2_16"] = icons16.GetSubBitmap(wx.Rect(493, y, 16, 16))

        # LINE 3
        y += 17
        self.iconsLib["check16"] = icons16.GetSubBitmap(wx.Rect(0, y, 16, 16))
        self.iconsLib["origamiLogo16"] = icons16.GetSubBitmap(wx.Rect(17, y, 16, 16))
        self.iconsLib["plotIMS16"] = icons16.GetSubBitmap(wx.Rect(34, y, 16, 16))
        self.iconsLib["plotIMSoverlay16"] = icons16.GetSubBitmap(wx.Rect(51, y, 16, 16))
        self.iconsLib["plotCalibration16"] = icons16.GetSubBitmap(wx.Rect(68, y, 16, 16))
        self.iconsLib["documentTwo16"] = icons16.GetSubBitmap(wx.Rect(102, y, 16, 16))
        self.iconsLib["settings16_2"] = icons16.GetSubBitmap(wx.Rect(119, y, 16, 16))
        self.iconsLib["reload16"] = icons16.GetSubBitmap(wx.Rect(136, y, 16, 16))
        self.iconsLib["load16"] = icons16.GetSubBitmap(wx.Rect(153, y, 16, 16))
        self.iconsLib["github16"] = icons16.GetSubBitmap(wx.Rect(170, y, 16, 16))
        self.iconsLib["youtube16"] = icons16.GetSubBitmap(wx.Rect(187, y, 16, 16))
        self.iconsLib["chromeC16"] = icons16.GetSubBitmap(wx.Rect(204, y, 16, 16))
        self.iconsLib["ieC16"] = icons16.GetSubBitmap(wx.Rect(221, y, 16, 16))
        self.iconsLib["open_origami_16"] = icons16.GetSubBitmap(wx.Rect(238, y, 16, 16))
        self.iconsLib["open_masslynx_16"] = icons16.GetSubBitmap(wx.Rect(255, y, 16, 16))
        self.iconsLib["open_project_16"] = icons16.GetSubBitmap(wx.Rect(272, y, 16, 16))
        self.iconsLib["open_text_16"] = icons16.GetSubBitmap(wx.Rect(289, y, 16, 16))
        self.iconsLib["open_agilent_16"] = icons16.GetSubBitmap(wx.Rect(306, y, 16, 16))
        self.iconsLib["maximize_16"] = icons16.GetSubBitmap(wx.Rect(323, y, 16, 16))
        self.iconsLib["minimize_16"] = icons16.GetSubBitmap(wx.Rect(340, y, 16, 16))
        self.iconsLib["clear_16"] = icons16.GetSubBitmap(wx.Rect(357, y, 16, 16))
        self.iconsLib["mobilogram_16"] = icons16.GetSubBitmap(wx.Rect(408, y, 16, 16))
        self.iconsLib["mass_spectrum_16"] = icons16.GetSubBitmap(wx.Rect(425, y, 16, 16))
        self.iconsLib["heatmap_16"] = icons16.GetSubBitmap(wx.Rect(442, y, 16, 16))
        self.iconsLib["export2_config_16"] = icons16.GetSubBitmap(wx.Rect(459, y, 16, 16))
        self.iconsLib["import2_config_16"] = icons16.GetSubBitmap(wx.Rect(476, y, 16, 16))
        self.iconsLib["folder_path_16"] = icons16.GetSubBitmap(wx.Rect(493, y, 16, 16))

        # LINE 4
        y += 17
        self.iconsLib["rmsdBottomLeft"] = icons16.GetSubBitmap(wx.Rect(0, y, 16, 16))
        self.iconsLib["rmsdTopLeft"] = icons16.GetSubBitmap(wx.Rect(17, y, 16, 16))
        self.iconsLib["rmsdTopRight"] = icons16.GetSubBitmap(wx.Rect(34, y, 16, 16))
        self.iconsLib["rmsdBottomRight"] = icons16.GetSubBitmap(wx.Rect(51, y, 16, 16))
        self.iconsLib["rmsdNone"] = icons16.GetSubBitmap(wx.Rect(68, y, 16, 16))
        self.iconsLib["origamiLogoDark16"] = icons16.GetSubBitmap(wx.Rect(85, y, 16, 16))
        self.iconsLib["panel_legend_16"] = icons16.GetSubBitmap(wx.Rect(102, y, 16, 16))
        self.iconsLib["panel_colorbar_16"] = icons16.GetSubBitmap(wx.Rect(119, y, 16, 16))
        self.iconsLib["panel_plot1D_16"] = icons16.GetSubBitmap(wx.Rect(136, y, 16, 16))
        self.iconsLib["panel_plot2D_16"] = icons16.GetSubBitmap(wx.Rect(153, y, 16, 16))
        self.iconsLib["panel_plot3D_16"] = icons16.GetSubBitmap(wx.Rect(170, y, 16, 16))
        self.iconsLib["panel_waterfall_16"] = icons16.GetSubBitmap(wx.Rect(187, y, 16, 16))
        self.iconsLib["panel_rmsd_16"] = icons16.GetSubBitmap(wx.Rect(204, y, 16, 16))
        self.iconsLib["bokehLogo_16"] = icons16.GetSubBitmap(wx.Rect(221, y, 16, 16))
        self.iconsLib["open_origamiMany_16"] = icons16.GetSubBitmap(wx.Rect(238, y, 16, 16))
        self.iconsLib["open_masslynxMany_16"] = icons16.GetSubBitmap(wx.Rect(255, y, 16, 16))
        self.iconsLib["open_projectMany_16"] = icons16.GetSubBitmap(wx.Rect(272, y, 16, 16))
        self.iconsLib["open_textMany_16"] = icons16.GetSubBitmap(wx.Rect(289, y, 16, 16))
        self.iconsLib["open_agilentMany_16"] = icons16.GetSubBitmap(wx.Rect(306, y, 16, 16))
        self.iconsLib["min_threshold_16"] = icons16.GetSubBitmap(wx.Rect(323, y, 16, 16))
        self.iconsLib["max_threshold_16"] = icons16.GetSubBitmap(wx.Rect(340, y, 16, 16))
        self.iconsLib["ccs_table_16"] = icons16.GetSubBitmap(wx.Rect(357, y, 16, 16))
        self.iconsLib["assign_charge_16"] = icons16.GetSubBitmap(wx.Rect(374, y, 16, 16))
        self.iconsLib["transparency_16"] = icons16.GetSubBitmap(wx.Rect(390, y, 16, 16))
        self.iconsLib["overlay_2D_16"] = icons16.GetSubBitmap(wx.Rect(408, y, 16, 16))
        self.iconsLib["chromatogram_16"] = icons16.GetSubBitmap(wx.Rect(425, y, 16, 16))
        self.iconsLib["compare_mass_spectra_16"] = icons16.GetSubBitmap(wx.Rect(442, y, 16, 16))
        self.iconsLib["change_xlabels_16"] = icons16.GetSubBitmap(wx.Rect(459, y, 16, 16))
        self.iconsLib["change_ylabels_16"] = icons16.GetSubBitmap(wx.Rect(476, y, 16, 16))
        self.iconsLib["folder_path_16"] = icons16.GetSubBitmap(wx.Rect(493, y, 16, 16))

        # LINE 5
        y += 17
        self.iconsLib["request_16"] = icons16.GetSubBitmap(wx.Rect(0, y, 16, 16))
        self.iconsLib["file_pdf"] = icons16.GetSubBitmap(wx.Rect(17, y, 16, 16))
        self.iconsLib["folder_picture"] = icons16.GetSubBitmap(wx.Rect(34, y, 16, 16))
        self.iconsLib["folder_camera"] = icons16.GetSubBitmap(wx.Rect(51, y, 16, 16))
        self.iconsLib["folder_planet"] = icons16.GetSubBitmap(wx.Rect(68, y, 16, 16))
        self.iconsLib["folder_trace"] = icons16.GetSubBitmap(wx.Rect(85, y, 16, 16))
        self.iconsLib["file_zip_16"] = icons16.GetSubBitmap(wx.Rect(102, y, 16, 16))
        self.iconsLib["file_pdf_16"] = icons16.GetSubBitmap(wx.Rect(119, y, 16, 16))
        self.iconsLib["file_txt_16"] = icons16.GetSubBitmap(wx.Rect(136, y, 16, 16))
        self.iconsLib["file_png_16"] = icons16.GetSubBitmap(wx.Rect(153, y, 16, 16))
        self.iconsLib["file_csv_16"] = icons16.GetSubBitmap(wx.Rect(170, y, 16, 16))
        self.iconsLib["file_csv_alt_16"] = icons16.GetSubBitmap(wx.Rect(187, y, 16, 16))
        self.iconsLib["aa3to1_16"] = icons16.GetSubBitmap(wx.Rect(204, y, 16, 16))
        self.iconsLib["aa1to3_16"] = icons16.GetSubBitmap(wx.Rect(221, y, 16, 16))
        self.iconsLib["pickle_16"] = icons16.GetSubBitmap(wx.Rect(238, y, 16, 16))
        self.iconsLib["google_logo_16"] = icons16.GetSubBitmap(wx.Rect(255, y, 16, 16))
        self.iconsLib["bug_16"] = icons16.GetSubBitmap(wx.Rect(272, y, 16, 16))
        self.iconsLib["cite_16"] = icons16.GetSubBitmap(wx.Rect(289, y, 16, 16))
        self.iconsLib["fullscreen_16"] = icons16.GetSubBitmap(wx.Rect(306, y, 16, 16))
        self.iconsLib["panel_legend2_16"] = icons16.GetSubBitmap(wx.Rect(323, y, 16, 16))
        self.iconsLib["scatter2_16"] = icons16.GetSubBitmap(wx.Rect(340, y, 16, 16))
        self.iconsLib["panel_classifier_16"] = icons16.GetSubBitmap(wx.Rect(357, y, 16, 16))
        self.iconsLib["panel_crossValidation_16"] = icons16.GetSubBitmap(wx.Rect(374, y, 16, 16))
        self.iconsLib["panel_unsupervised_16"] = icons16.GetSubBitmap(wx.Rect(391, y, 16, 16))
        self.iconsLib["panel_supervised_16"] = icons16.GetSubBitmap(wx.Rect(408, y, 16, 16))
        self.iconsLib["panel_learner_16"] = icons16.GetSubBitmap(wx.Rect(425, y, 16, 16))
        self.iconsLib["process_unidec_16"] = icons16.GetSubBitmap(wx.Rect(442, y, 16, 16))
        self.iconsLib["panel_log_16"] = icons16.GetSubBitmap(wx.Rect(459, y, 16, 16))
        self.iconsLib["panel_violin_16"] = icons16.GetSubBitmap(wx.Rect(476, y, 16, 16))
        self.iconsLib["randomize_16"] = icons16.GetSubBitmap(wx.Rect(493, y, 16, 16))

        # LINE 6
        y += 17
        self.iconsLib["guide_16"] = icons16.GetSubBitmap(wx.Rect(0, y, 16, 16))
        self.iconsLib["exit_16"] = icons16.GetSubBitmap(wx.Rect(17, y, 16, 16))
        self.iconsLib["check_online_16"] = icons16.GetSubBitmap(wx.Rect(34, y, 16, 16))
        self.iconsLib["duplicate_16"] = icons16.GetSubBitmap(wx.Rect(51, y, 16, 16))
        self.iconsLib["parameters_16"] = icons16.GetSubBitmap(wx.Rect(68, y, 16, 16))
        self.iconsLib["open_source_16"] = icons16.GetSubBitmap(wx.Rect(85, y, 16, 16))
        self.iconsLib["sort_16"] = icons16.GetSubBitmap(wx.Rect(102, y, 16, 16))
        self.iconsLib["open_file_16"] = icons16.GetSubBitmap(wx.Rect(119, y, 16, 16))
        self.iconsLib["connection_16"] = icons16.GetSubBitmap(wx.Rect(136, y, 16, 16))
        self.iconsLib["search_16"] = icons16.GetSubBitmap(wx.Rect(153, y, 16, 16))
        self.iconsLib["brain_16"] = icons16.GetSubBitmap(wx.Rect(170, y, 16, 16))
        self.iconsLib["data_reduce_16"] = icons16.GetSubBitmap(wx.Rect(187, y, 16, 16))
        self.iconsLib["machine_learning_16"] = icons16.GetSubBitmap(wx.Rect(204, y, 16, 16))

        self.iconsLib["school_16"] = icons16.GetSubBitmap(wx.Rect(221, y, 16, 16))
        self.iconsLib["owl_16"] = icons16.GetSubBitmap(wx.Rect(238, y, 16, 16))
        self.iconsLib["builder_16"] = icons16.GetSubBitmap(wx.Rect(255, y, 16, 16))
        self.iconsLib["board_16"] = icons16.GetSubBitmap(wx.Rect(272, y, 16, 16))
        self.iconsLib["chart_16"] = icons16.GetSubBitmap(wx.Rect(289, y, 16, 16))
        self.iconsLib["barchart_16"] = icons16.GetSubBitmap(wx.Rect(306, y, 16, 16))
        self.iconsLib["rocket_16"] = icons16.GetSubBitmap(wx.Rect(323, y, 16, 16))
        self.iconsLib["measure_16"] = icons16.GetSubBitmap(wx.Rect(340, y, 16, 16))
        self.iconsLib["sort_1to9_16"] = icons16.GetSubBitmap(wx.Rect(357, y, 16, 16))
        self.iconsLib["sort_AtoZ_16"] = icons16.GetSubBitmap(wx.Rect(374, y, 16, 16))
        self.iconsLib["mark_peak_16"] = icons16.GetSubBitmap(wx.Rect(391, y, 16, 16))
        self.iconsLib["run_run_16"] = icons16.GetSubBitmap(wx.Rect(408, y, 16, 16))
        self.iconsLib["climb_16"] = icons16.GetSubBitmap(wx.Rect(425, y, 16, 16))
        self.iconsLib["duplicate_item_16"] = icons16.GetSubBitmap(wx.Rect(442, y, 16, 16))
        self.iconsLib["rename_16"] = icons16.GetSubBitmap(wx.Rect(459, y, 16, 16))

        # these were accidentally removed...
        self.iconsLib["plot_waterfall_16"] = icons16.GetSubBitmap(wx.Rect(0, 212, 16, 16))
        self.iconsLib["plot_bar_16"] = icons16.GetSubBitmap(wx.Rect(0, 212, 16, 16))
        self.iconsLib["panel_plot_general_16"] = icons16.GetSubBitmap(wx.Rect(68, y, 16, 16))

        # listed colormaps
        self.iconsLib["cmap_hls"] = icons16.GetSubBitmap(wx.Rect(408, 102, 64, 16))
        self.iconsLib["cmap_husl"] = icons16.GetSubBitmap(wx.Rect(408, 119, 64, 16))
        self.iconsLib["cmap_cubehelix"] = icons16.GetSubBitmap(wx.Rect(408, 136, 64, 16))
        self.iconsLib["cmap_spectral"] = icons16.GetSubBitmap(wx.Rect(408, 153, 64, 16))
        self.iconsLib["cmap_viridis"] = icons16.GetSubBitmap(wx.Rect(408, 170, 64, 16))
        self.iconsLib["cmap_rainbow"] = icons16.GetSubBitmap(wx.Rect(408, 187, 64, 16))
        self.iconsLib["cmap_inferno"] = icons16.GetSubBitmap(wx.Rect(408, 204, 64, 16))
        self.iconsLib["cmap_cividis"] = icons16.GetSubBitmap(wx.Rect(408, 221, 64, 16))

        self.iconsLib["cmap_cool"] = icons16.GetSubBitmap(wx.Rect(473, 102, 64, 16))
        self.iconsLib["cmap_gray"] = icons16.GetSubBitmap(wx.Rect(473, 119, 64, 16))
        self.iconsLib["cmap_rdpu"] = icons16.GetSubBitmap(wx.Rect(473, 136, 64, 16))
        self.iconsLib["cmap_tab20b"] = icons16.GetSubBitmap(wx.Rect(473, 153, 64, 16))
        self.iconsLib["cmap_tab20c"] = icons16.GetSubBitmap(wx.Rect(473, 170, 64, 16))
        self.iconsLib["cmap_modern1"] = icons16.GetSubBitmap(wx.Rect(473, 187, 64, 16))
        self.iconsLib["cmap_modern2"] = icons16.GetSubBitmap(wx.Rect(473, 204, 64, 16))
        self.iconsLib["cmap_winter"] = icons16.GetSubBitmap(wx.Rect(473, 221, 64, 16))

        # TOOLBAR
        self.iconsLib["bgrToolbar"] = self.getBgrToolbarBitmap()
