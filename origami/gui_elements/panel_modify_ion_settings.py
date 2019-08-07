# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import wx
from icons.icons import IconContainer
from styles import makeCheckbox
from styles import MiniFrame
from styles import validator
from utils.converters import num2str
from utils.converters import str2int
from utils.converters import str2num

# TODO: Add possibility to visualise heatmap as false-color image


class PanelModifyIonSettings(MiniFrame):
    """
    Small panel to modify settings in the Ion peaklist panel
    """

    def __init__(self, parent, presenter, config, **kwargs):
        MiniFrame.__init__(self, parent, title="Modify settings...", style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER)

        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = IconContainer()
        self.importEvent = False

        self.SetTitle("Ion: {}".format(kwargs["ionName"]))
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

        if self.itemInfo["charge"] in ["", None, "None"]:
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
        self.parent.onUpdateDocument(itemInfo=self.itemInfo, evt=None)
        self.Destroy()

    def make_panel(self):

        panel = wx.Panel(self, -1, size=(-1, -1))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        select_label = wx.StaticText(panel, wx.ID_ANY, "Select:")
        self.origami_select_value = makeCheckbox(panel, "")
        self.origami_select_value.Bind(wx.EVT_CHECKBOX, self.on_apply)

        filename_label = wx.StaticText(panel, wx.ID_ANY, "Filename:")
        self.origami_filename_value = wx.TextCtrl(panel, wx.ID_ANY, "", style=wx.TE_READONLY)

        ion_label = wx.StaticText(panel, wx.ID_ANY, "Ion:")
        self.origami_ion_value = wx.TextCtrl(panel, wx.ID_ANY, "", style=wx.TE_READONLY)

        label_label = wx.StaticText(panel, wx.ID_ANY, "Label:", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_LEFT)
        self.origami_label_value = wx.TextCtrl(panel, -1, "", size=(90, -1))
        self.origami_label_value.SetValue(self.__check_label(self.itemInfo["label"]))
        self.origami_label_value.Bind(wx.EVT_TEXT, self.on_apply)

        charge_label = wx.StaticText(panel, wx.ID_ANY, "Charge:")
        self.origami_charge_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("intPos"))
        self.origami_charge_value.Bind(wx.EVT_TEXT, self.on_apply)

        min_threshold_label = wx.StaticText(panel, wx.ID_ANY, "Min threshold:")
        self.origami_min_threshold_value = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, value="1", min=0.0, max=1.0, initial=1.0, inc=0.05, size=(60, -1)
        )
        self.origami_min_threshold_value.SetValue(self.itemInfo["min_threshold"])
        self.origami_min_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        max_threshold_label = wx.StaticText(panel, wx.ID_ANY, "Max threshold:")
        self.origami_max_threshold_value = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, value="1", min=0.0, max=1.0, initial=1.0, inc=0.05, size=(60, -1)
        )
        self.origami_max_threshold_value.SetValue(self.itemInfo["max_threshold"])
        self.origami_max_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        colormap_label = wx.StaticText(panel, -1, "Colormap:")
        self.origami_colormap_value = wx.Choice(panel, -1, choices=self.config.cmaps2, size=(-1, -1))
        self.origami_colormap_value.Bind(wx.EVT_CHOICE, self.on_apply)

        self.origami_restrictColormap_value = makeCheckbox(panel, "")
        self.origami_restrictColormap_value.Bind(wx.EVT_CHECKBOX, self.on_restrict_colormaps)

        color_label = wx.StaticText(panel, -1, "Color:")
        self.origami_color_value = wx.Button(panel, wx.ID_ANY, "", wx.DefaultPosition, wx.Size(26, 26), 0)
        self.origami_color_value.SetBackgroundColour(self.itemInfo["color"])
        self.origami_color_value.Bind(wx.EVT_BUTTON, self.on_assign_color)

        mask_label = wx.StaticText(panel, wx.ID_ANY, "Mask:")
        self.origami_mask_value = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, value="1", min=0.0, max=1.0, initial=1.0, inc=0.05, size=(60, -1)
        )
        self.origami_mask_value.SetValue(self.itemInfo["mask"])
        self.origami_mask_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        transparency_label = wx.StaticText(panel, wx.ID_ANY, "Transparency:")
        self.origami_transparency_value = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, value="1", min=0.0, max=1.0, initial=1.0, inc=0.05, size=(60, -1)
        )
        self.origami_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.applyBtn = wx.Button(panel, wx.ID_OK, "Apply", size=(-1, 22))
        self.previousBtn = wx.Button(panel, wx.ID_OK, "Previous", size=(-1, 22))
        self.nextBtn = wx.Button(panel, wx.ID_OK, "Next", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Close", size=(-1, 22))

        self.applyBtn.Bind(wx.EVT_BUTTON, self.on_select)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)
        self.nextBtn.Bind(wx.EVT_BUTTON, self.on_get_next)
        self.previousBtn.Bind(wx.EVT_BUTTON, self.on_get_previous)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.applyBtn, (n, 0), wx.GBSpan(1, 1))
        btn_grid.Add(self.previousBtn, (n, 1), wx.GBSpan(1, 1))
        btn_grid.Add(self.nextBtn, (n, 2), wx.GBSpan(1, 1))
        btn_grid.Add(self.cancelBtn, (n, 3), wx.GBSpan(1, 1))

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(select_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_select_value, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(filename_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_filename_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(ion_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_ion_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(label_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_label_value, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(charge_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_charge_value, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(min_threshold_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_min_threshold_value, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(max_threshold_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_max_threshold_value, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(colormap_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_colormap_value, (n, 1), flag=wx.EXPAND)
        grid.Add(self.origami_restrictColormap_value, (n, 2), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_color_value, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(mask_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_mask_value, (n, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(transparency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_transparency_value, (n, 1), flag=wx.EXPAND)
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

    def on_apply(self, evt):
        self.on_check_id()
        if self.importEvent:
            return
        self.parent.peaklist.CheckItem(self.itemInfo["id"], self.origami_select_value.GetValue())
        self.parent.peaklist.SetStringItem(
            self.itemInfo["id"], self.config.peaklistColNames["charge"], self.origami_charge_value.GetValue()
        )
        self.parent.peaklist.SetStringItem(
            self.itemInfo["id"],
            self.config.peaklistColNames["colormap"],
            self.origami_colormap_value.GetStringSelection(),
        )
        self.parent.peaklist.SetStringItem(
            self.itemInfo["id"], self.config.peaklistColNames["mask"], num2str(self.origami_mask_value.GetValue())
        )
        self.parent.peaklist.SetStringItem(
            self.itemInfo["id"],
            self.config.peaklistColNames["alpha"],
            num2str(self.origami_transparency_value.GetValue()),
        )
        self.parent.peaklist.SetStringItem(
            self.itemInfo["id"], self.config.peaklistColNames["label"], self.origami_label_value.GetValue()
        )

        # update ion information
        self.itemInfo["charge"] = self.origami_charge_value.GetValue()
        self.itemInfo["colormap"] = self.origami_colormap_value.GetStringSelection()
        self.itemInfo["mask"] = self.origami_mask_value.GetValue()
        self.itemInfo["alpha"] = self.origami_transparency_value.GetValue()
        self.itemInfo["label"] = self.origami_label_value.GetValue()
        self.itemInfo["min_threshold"] = self.origami_min_threshold_value.GetValue()
        self.itemInfo["max_threshold"] = self.origami_max_threshold_value.GetValue()

        # update ion value
        try:
            charge = str2int(self.itemInfo["charge"])
            ion_centre = (str2num(self.itemInfo["start"]) + str2num(self.itemInfo["end"])) / 2
            mw = (ion_centre - self.config.elementalMass["Hydrogen"] * charge) * charge
            ion_value = "{:} ~{:.2f} Da".format(self.itemInfo["ionName"], mw)
            self.origami_ion_value.SetValue(ion_value)
        except Exception:
            self.origami_ion_value.SetValue(self.itemInfo["ionName"])

        self.on_assign_color(evt=None)
        self.parent.onUpdateDocument(itemInfo=self.itemInfo, evt=None)

        if evt is not None:
            evt.Skip()

    def on_setup_gui(self, evt):
        self.importEvent = True
        self.origami_select_value.SetValue(self.itemInfo["select"])
        self.origami_filename_value.SetValue(self.itemInfo["document"])

        try:
            charge = str2int(self.itemInfo["charge"])
            ion_centre = (str2num(self.itemInfo["start"]) + str2num(self.itemInfo["end"])) / 2
            mw = (ion_centre - self.config.elementalMass["Hydrogen"] * charge) * charge
            ion_value = ("%s  ~%.2f Da") % (self.itemInfo["ionName"], mw)
            self.origami_ion_value.SetValue(ion_value)
        except Exception:
            self.origami_ion_value.SetValue(self.__check_label(self.itemInfo["ionName"]))

        self.origami_charge_value.SetValue(str(self.itemInfo["charge"]))
        self.origami_label_value.SetValue(self.__check_label(self.itemInfo["label"]))
        self.origami_colormap_value.SetStringSelection(self.itemInfo["colormap"])
        self.origami_mask_value.SetValue(self.itemInfo["mask"])
        self.origami_transparency_value.SetValue(self.itemInfo["alpha"])
        self.origami_color_value.SetBackgroundColour(self.itemInfo["color"])
        self.origami_min_threshold_value.SetValue(self.itemInfo["min_threshold"])
        self.origami_max_threshold_value.SetValue(self.itemInfo["max_threshold"])

        self.on_toggle_controls(evt=None)
        self.importEvent = False

    def on_update_gui(self, itemInfo):
        """
        @param itemInfo (dict): updating GUI with new item information
        """
        self.itemInfo = itemInfo
        self.SetTitle(self.itemInfo["ionName"])

        # check values
        if self.itemInfo["mask"] in ["", None, "None"]:
            self.itemInfo["mask"] = 1

        if self.itemInfo["alpha"] in ["", None, "None"]:
            self.itemInfo["alpha"] = 1

        if self.itemInfo["colormap"] in ["", None, "None"]:
            self.itemInfo["colormap"] = self.config.currentCmap

        if self.itemInfo["color"][0] == -1:
            self.itemInfo["color"] = (1, 1, 1, 255)

        if self.itemInfo["charge"] in ["", None, "None"]:
            self.itemInfo["charge"] = ""

        # setup values
        self.on_setup_gui(evt=None)

        self.SetFocus()

    def on_toggle_controls(self, evt):

        if evt is not None:
            evt.Skip()

    def on_assign_color(self, evt):
        self.on_check_id()
        if evt:
            color = self.parent.on_assign_color(evt=None, itemID=self.itemInfo["id"], give_value=True)
            self.origami_color_value.SetBackgroundColour(color)
        else:
            color = self.origami_color_value.GetBackgroundColour()
            self.parent.peaklist.SetItemBackgroundColour(self.itemInfo["id"], color)

    def on_restrict_colormaps(self, evt):
        """
        The cmap list will be restricted to more limited selection
        """
        currentCmap = self.origami_colormap_value.GetStringSelection()
        if self.origami_restrictColormap_value.GetValue():
            cmap_list = self.config.narrowCmapList
            cmap_list.append(currentCmap)
        else:
            cmap_list = self.config.cmaps2

        # remove duplicates
        cmap_list = sorted(list(set(cmap_list)))

        self.origami_colormap_value.Clear()
        self.origami_colormap_value.SetItems(cmap_list)
        self.origami_colormap_value.SetStringSelection(currentCmap)

    def on_get_next(self, evt):
        self.on_check_id()
        count = self.parent.peaklist.GetItemCount() - 1
        if self.itemInfo["id"] == count:
            new_id = 0
        else:
            new_id = self.itemInfo["id"] + 1

        # get new information
        self.itemInfo = self.parent.OnGetItemInformation(new_id)
        # update table
        self.on_setup_gui(None)
        # update title
        self.SetTitle(self.itemInfo["document"])

    def on_get_previous(self, evt):
        self.on_check_id()
        count = self.parent.peaklist.GetItemCount() - 1
        if self.itemInfo["id"] == 0:
            new_id = count
        else:
            new_id = self.itemInfo["id"] - 1

        # get new information
        self.itemInfo = self.parent.OnGetItemInformation(new_id)
        # update table
        self.on_setup_gui(None)
        # update title
        self.SetTitle(self.itemInfo["document"])

    def on_check_id(self):

        # check whether ID is still correct
        information = self.parent.OnGetItemInformation(self.itemInfo["id"])

        if information["ion_name"] == self.itemInfo["ion_name"]:
            return
        else:
            count = self.parent.peaklist.GetItemCount()
            for row in range(count):
                information = self.parent.OnGetItemInformation(row)
                if information["ion_name"] == self.itemInfo["ion_name"]:
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
