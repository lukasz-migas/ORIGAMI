# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import wx
from icons.icons import IconContainer
from styles import makeCheckbox
from styles import MiniFrame
from styles import validator
from utils.converters import num2str
from utils.converters import str2int
from utils.labels import get_ion_name_from_label


# TODO: Add possibility to visualise heatmap as false-color image
class PanelModifyIonSettings(MiniFrame):
    """Universal widget to modify common settings in a number of places"""

    def __init__(self, parent, presenter, config, **kwargs):
        MiniFrame.__init__(self, parent, title="Modify parameters...", style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER)

        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = IconContainer()
        self.importEvent = False

        # gui presets
        self.show_mw = True
        self.show_charge = True
        self.apply_thresholds = False
        self.add_show_button = True

        # based on the kwargs, decide which source it is
        # peaklist
        if "ionName" in kwargs:
            self.SetTitle(f"Ion: {kwargs['ionName']}")
            self.item_name = "ion_name"
            self.column_dict = self.config.peaklistColNames
        # overlay
        elif "dataset_name" in kwargs:
            self.SetTitle(f"Item: {kwargs['dataset_name']} | {kwargs['dataset_type']} | {kwargs['document']}")
            self.show_mw = False
            self.show_charge = False
            self.apply_thresholds = True
            self.add_show_button = False
            self.item_name = "item_name"
            self.column_dict = self.config.overlay_list_col_names
        # textlist
        else:
            self.SetTitle(f"File: {kwargs.get('document', 'filename')}")
            self.show_mw = False
            self.item_name = "document"
            self.column_dict = self.config.textlistColNames

        self.itemInfo = kwargs

        # check values
        if self.itemInfo["mask"] in ["", None, "None"]:
            self.itemInfo["mask"] = self.config.overlay_defaultMask

        if self.itemInfo["alpha"] in ["", None, "None"]:
            self.itemInfo["alpha"] = self.config.overlay_defaultAlpha

        if self.itemInfo["colormap"] in ["", None, "None"]:
            self.itemInfo["colormap"] = self.config.currentCmap

        if self.itemInfo["color"][0] == -1:
            self.itemInfo["color"] = (1, 1, 1, 255)

        if self.itemInfo.get("charge", None) in ["", None, "None"]:
            self.itemInfo["charge"] = 1

        # make gui items
        self.make_gui()

        self.Centre()
        self.Layout()
        self.SetFocus()

        # fire-up events
        self.on_setup_gui(evt=None)

    def on_select(self, evt):
        self.on_assign_color(evt=None)
        self.parent.on_update_document(itemInfo=self.itemInfo, evt=None)
        self.Destroy()

    def make_panel(self):

        panel = wx.Panel(self, -1, size=(-1, -1))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        select_label = wx.StaticText(panel, wx.ID_ANY, "Select:")
        self.select_value = makeCheckbox(panel, "")
        self.select_value.Bind(wx.EVT_CHECKBOX, self.on_apply)

        filename_label = wx.StaticText(panel, wx.ID_ANY, "Filename:")
        self.filename_value = wx.TextCtrl(panel, wx.ID_ANY, "", style=wx.TE_READONLY)

        ion_label = wx.StaticText(panel, wx.ID_ANY, "Ion:")
        self.ion_value = wx.TextCtrl(panel, wx.ID_ANY, "", style=wx.TE_READONLY)

        label_label = wx.StaticText(panel, wx.ID_ANY, "Label:", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_LEFT)
        self.label_value = wx.TextCtrl(panel, -1, "", size=(90, -1))
        self.label_value.SetValue(self.__check_label(self.itemInfo["label"]))
        self.label_value.Bind(wx.EVT_TEXT, self.on_apply)

        if not self.show_charge:
            charge_label = wx.StaticText(panel, wx.ID_ANY, "Charge:")
            self.charge_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("intPos"))
            self.charge_value.Bind(wx.EVT_TEXT, self.on_apply)

        mask_label = wx.StaticText(panel, wx.ID_ANY, "Mask:")
        self.mask_value = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, value="1", min=0.0, max=1.0, initial=1.0, inc=0.1, size=(60, -1)
        )
        self.mask_value.SetValue(self.itemInfo["mask"])
        self.mask_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        transparency_label = wx.StaticText(panel, wx.ID_ANY, "Transparency:")
        self.transparency_value = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, value="1", min=0.0, max=1.0, initial=1.0, inc=0.1, size=(60, -1)
        )
        self.transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        min_threshold_label = wx.StaticText(panel, wx.ID_ANY, "Min threshold:")
        self.min_threshold_value = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, value="1", min=0.0, max=1.0, initial=1.0, inc=0.1, size=(60, -1)
        )
        self.min_threshold_value.SetValue(self.itemInfo["min_threshold"])
        self.min_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        max_threshold_label = wx.StaticText(panel, wx.ID_ANY, "Max threshold:")
        self.max_threshold_value = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, value="1", min=0.0, max=1.0, initial=1.0, inc=0.1, size=(60, -1)
        )
        self.max_threshold_value.SetValue(self.itemInfo["max_threshold"])
        self.max_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        colormap_label = wx.StaticText(panel, -1, "Colormap:")
        self.colormap_value = wx.Choice(panel, -1, choices=self.config.cmaps2, size=(-1, -1))
        self.colormap_value.Bind(wx.EVT_CHOICE, self.on_apply)

        self.restrictColormap_value = makeCheckbox(panel, "")
        self.restrictColormap_value.Bind(wx.EVT_CHECKBOX, self.on_restrict_colormaps)

        color_label = wx.StaticText(panel, -1, "Color:")
        self.color_value = wx.Button(panel, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0)
        self.color_value.SetBackgroundColour(self.itemInfo["color"])
        self.color_value.Bind(wx.EVT_BUTTON, self.on_assign_color)

        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        if self.add_show_button:
            self.showBtn = wx.Button(panel, wx.ID_OK, "Show", size=(-1, 22))
            self.showBtn.Bind(wx.EVT_BUTTON, self.on_show)

        self.applyBtn = wx.Button(panel, wx.ID_OK, "Apply", size=(-1, 22))
        self.applyBtn.Bind(wx.EVT_BUTTON, self.on_select)

        self.previousBtn = wx.Button(panel, wx.ID_OK, "Previous", size=(-1, 22))
        self.previousBtn.Bind(wx.EVT_BUTTON, self.on_get_previous)

        self.nextBtn = wx.Button(panel, wx.ID_OK, "Next", size=(-1, 22))
        self.nextBtn.Bind(wx.EVT_BUTTON, self.on_get_next)

        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Close", size=(-1, 22))
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        x = 0
        if self.add_show_button:
            btn_grid.Add(self.showBtn, (n, x), wx.GBSpan(1, 1))
            x += 1
        btn_grid.Add(self.applyBtn, (n, x), wx.GBSpan(1, 1))
        x += 1
        btn_grid.Add(self.previousBtn, (n, x), wx.GBSpan(1, 1))
        x += 1
        btn_grid.Add(self.nextBtn, (n, x), wx.GBSpan(1, 1))
        x += 1
        btn_grid.Add(self.cancelBtn, (n, x), wx.GBSpan(1, 1))

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(select_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.select_value, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(filename_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.filename_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(ion_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ion_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(label_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        if not self.show_charge:
            n = n + 1
            grid.Add(charge_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
            grid.Add(self.charge_value, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(mask_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mask_value, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.transparency_value, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(min_threshold_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.min_threshold_value, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(max_threshold_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.max_threshold_value, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(colormap_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colormap_value, (n, 1), flag=wx.EXPAND)
        grid.Add(self.restrictColormap_value, (n, 2), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.color_value, (n, 1), flag=wx.EXPAND)

        n = n + 1
        grid.Add(horizontal_line, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n = n + 1
        grid.Add(btn_grid, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        main_sizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        self.on_toggle_controls(evt=None)

        return panel

    def on_show(self, evt):
        self.parent.on_plot(evt=None, itemID=self.itemInfo["id"])

    def on_apply(self, evt):
        self.on_check_id()
        if self.importEvent:
            return

        self.parent.peaklist.CheckItem(self.itemInfo["id"], self.select_value.GetValue())

        if self.show_charge:
            self.itemInfo["charge"] = self.charge_value.GetValue()
            self.parent.peaklist.SetStringItem(self.itemInfo["id"], self.column_dict["charge"], self.itemInfo["charge"])

        self.itemInfo["colormap"] = self.colormap_value.GetStringSelection()
        self.parent.peaklist.SetStringItem(self.itemInfo["id"], self.column_dict["colormap"], self.itemInfo["colormap"])

        self.itemInfo["mask"] = self.mask_value.GetValue()
        self.parent.peaklist.SetStringItem(
            self.itemInfo["id"], self.column_dict["mask"], num2str(self.itemInfo["mask"])
        )

        self.itemInfo["alpha"] = self.transparency_value.GetValue()
        self.parent.peaklist.SetStringItem(
            self.itemInfo["id"], self.column_dict["alpha"], num2str(self.itemInfo["alpha"])
        )

        self.itemInfo["label"] = self.label_value.GetValue()
        self.parent.peaklist.SetStringItem(self.itemInfo["id"], self.column_dict["label"], self.itemInfo["label"])

        self.itemInfo["min_threshold"] = self.min_threshold_value.GetValue()
        self.itemInfo["max_threshold"] = self.max_threshold_value.GetValue()

        if self.apply_thresholds:
            self.parent.peaklist.SetStringItem(
                self.itemInfo["id"], self.column_dict["min_threshold"], num2str(self.itemInfo["min_threshold"])
            )
            self.parent.peaklist.SetStringItem(
                self.itemInfo["id"], self.column_dict["max_threshold"], num2str(self.itemInfo["max_threshold"])
            )

        # update ion value
        self.on_update_mw()

        self.on_assign_color(evt=None)

        # update item info
        self.parent.on_update_document(itemInfo=self.itemInfo, evt=None)

        if evt is not None:
            evt.Skip()

    def on_update_mw(self):
        """Update molecular weight based on input"""
        if self.show_mw:
            try:
                mz_start, mz_end = get_ion_name_from_label(self.itemInfo["ionName"], as_num=True)
                charge = str2int(self.itemInfo["charge"])
                ion_centre = (mz_start + mz_end) / 2
                mw = (ion_centre - self.config.elementalMass["Hydrogen"] * charge) * charge
                ion_value = "{:} ~{:.2f} Da".format(self.itemInfo["ionName"], mw)
                self.ion_value.SetValue(ion_value)
            except Exception as err:
                self.ion_value.SetValue(self.itemInfo["ionName"])
                print(err)

    def on_setup_gui(self, evt):
        """Setup GUI based on kwargs / self.itemInfo"""
        self.importEvent = True
        self.select_value.SetValue(self.itemInfo["select"])
        self.filename_value.SetValue(self.itemInfo["document"])

        # update ion value
        self.on_update_mw()

        if self.show_charge:
            self.charge_value.SetValue(str(self.itemInfo["charge"]))
        self.label_value.SetValue(self.__check_label(self.itemInfo["label"]))
        self.colormap_value.SetStringSelection(self.itemInfo["colormap"])
        self.mask_value.SetValue(self.itemInfo["mask"])
        self.transparency_value.SetValue(self.itemInfo["alpha"])
        self.color_value.SetBackgroundColour(self.itemInfo["color"])
        self.min_threshold_value.SetValue(self.itemInfo["min_threshold"])
        self.max_threshold_value.SetValue(self.itemInfo["max_threshold"])

        self.on_toggle_controls(evt=None)

        self.on_update_title(self.itemInfo)

        self.importEvent = False

    def on_update_title(self, itemInfo):
        if "ionName" in itemInfo:
            self.SetTitle(f"Ion: {itemInfo['ionName']}")
        elif "dataset_name" in itemInfo:
            self.SetTitle(f"Item: {itemInfo['dataset_name']} | {itemInfo['dataset_type']} | {itemInfo['document']}")
        else:
            self.SetTitle(f"File: {itemInfo.get('document', 'filename')}")

    def on_update_gui(self, itemInfo):
        """Update GUI

        Parameters
        ----------
        itemInfo : dict
            dictionary with item values
        """
        self.itemInfo = itemInfo

        # check values
        if self.itemInfo["mask"] in ["", None, "None"]:
            self.itemInfo["mask"] = 1

        if self.itemInfo["alpha"] in ["", None, "None"]:
            self.itemInfo["alpha"] = 1

        if self.itemInfo["colormap"] in ["", None, "None"]:
            self.itemInfo["colormap"] = self.config.currentCmap

        if self.itemInfo["color"][0] == -1:
            self.itemInfo["color"] = (1, 1, 1, 255)

        if self.show_charge and self.itemInfo["charge"] in ["", None, "None"]:
            self.itemInfo["charge"] = ""

        # setup values
        self.on_setup_gui(evt=None)

        # setup title
        self.on_update_title(itemInfo)

        self.SetFocus()

    def on_toggle_controls(self, evt):

        if evt is not None:
            evt.Skip()

    def on_assign_color(self, evt):
        self.on_check_id()
        if evt:
            color = self.parent.on_assign_color(evt=None, itemID=self.itemInfo["id"], give_value=True)
            self.color_value.SetBackgroundColour(color)
        else:
            color = self.color_value.GetBackgroundColour()
            self.parent.peaklist.SetItemBackgroundColour(self.itemInfo["id"], color)

    def on_restrict_colormaps(self, evt):
        """Reduce number of items in the colormap to pre-selected list of colormaps"""
        currentCmap = self.colormap_value.GetStringSelection()
        if self.restrictColormap_value.GetValue():
            cmap_list = self.config.narrowCmapList
            cmap_list.append(currentCmap)
        else:
            cmap_list = self.config.cmaps2

        # remove duplicates
        cmap_list = sorted(list(set(cmap_list)))

        self.colormap_value.Clear()
        self.colormap_value.SetItems(cmap_list)
        self.colormap_value.SetStringSelection(currentCmap)

    def on_get_next(self, evt):
        """Get next item in the list"""
        self.on_check_id()
        count = self.parent.peaklist.GetItemCount() - 1
        if self.itemInfo["id"] == count:
            new_id = 0
        else:
            new_id = self.itemInfo["id"] + 1

        # get new information
        self.itemInfo = self.parent.on_get_item_information(new_id)
        # update table
        self.on_setup_gui(None)

    def on_get_previous(self, evt):
        """Get previous item in the list"""
        self.on_check_id()
        count = self.parent.peaklist.GetItemCount() - 1
        if self.itemInfo["id"] == 0:
            new_id = count
        else:
            new_id = self.itemInfo["id"] - 1

        # get new information
        self.itemInfo = self.parent.on_get_item_information(new_id)
        # update table
        self.on_setup_gui(None)

    def on_check_id(self):
        """Ensure order of items has not changed in the list"""

        # check whether ID is still correct
        information = self.parent.on_get_item_information(self.itemInfo["id"])

        if information[self.item_name] == self.itemInfo[self.item_name]:
            return
        else:
            count = self.parent.peaklist.GetItemCount()
            for row in range(count):
                information = self.parent.on_get_item_information(row)
                if information[self.item_name] == self.itemInfo[self.item_name]:
                    if information["id"] == self.itemInfo["id"]:
                        return
                    else:
                        self.itemInfo["id"] = information["id"]
                        return

    @staticmethod
    def __check_label(input_value):
        if input_value is None:
            return ""
        else:
            return str(input_value)
