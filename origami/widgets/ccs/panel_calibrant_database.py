# Standard library imports
import itertools
from operator import itemgetter

# Third-party imports
import wx
import numpy as np

# Local imports
from origami.styles import ListCtrl
from origami.utils.converters import str2int
from origami.utils.converters import str2num


class PanelCalibrantDatabase(wx.MiniFrame):
    """UI controls to display loaded CCS calibration database"""

    def __init__(self, parent, presenter, config, mode):
        wx.MiniFrame.__init__(
            self,
            parent,
            -1,
            "Select protein...",
            size=(-1, -1),
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
        )

        self.parent = parent
        self.presenter = presenter
        self.config = config

        # modes = calibrants/proteins
        self.currentItem = None
        self.mode = mode
        self.ccsDB = self.config.ccsDB
        self.reverse = False
        self.lastColumn = None
        self.dataOut = None
        # make gui items
        self.make_gui()
        # Populate the table
        self.onPopulateTable()
        wx.EVT_CLOSE(self, self.on_close)

        self.Centre()
        self.Layout()
        self.SetSize((850, 300))
        self.SetMinSize((850, 300))
        self.peaklist.SetFocus()
        self.CentreOnParent()

    def on_close(self, evt):
        """Destroy this frame."""

        if self.dataOut is None:
            self.config.proteinData = None

        self.Destroy()

    # ----

    def make_gui(self):

        # make panel
        panel = self.makeDatabasePanel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 1, wx.EXPAND, 0)

        if self.mode == "calibrants":
            size = (800, 400)
        else:
            size = (400, 400)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)
        self.SetMinSize(size)

    def makeDatabasePanel(self):

        panel = wx.Panel(self, -1, size=(-1, -1))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.peaklist = ListCtrl(panel, style=wx.LC_REPORT)
        self.peaklist.InsertColumn(0, "protein", width=150)
        self.peaklist.InsertColumn(1, "MW (kDa)", width=80)
        self.peaklist.InsertColumn(2, "units", width=60)
        if self.mode == "calibrants":
            # TODO : add m/z
            self.peaklist.InsertColumn(3, "z", width=40)
            self.peaklist.InsertColumn(4, "m/z (kDa)", width=80)
            self.peaklist.InsertColumn(5, "He⁺", width=60)
            self.peaklist.InsertColumn(6, "N2⁺", width=60)
            self.peaklist.InsertColumn(7, "He⁻", width=60)
            self.peaklist.InsertColumn(8, "N2⁻", width=60)
            self.peaklist.InsertColumn(9, "state", width=100)
            self.peaklist.InsertColumn(10, "source", width=60)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)

        self.addBtn = wx.Button(panel, wx.ID_OK, "Add", size=(-1, -1))
        self.addBtn.Hide()
        self.selectBtn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, -1))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, -1))

        self.selectBtn.Bind(wx.EVT_BUTTON, self.onSelect)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)

        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5

        # pack elements
        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
        grid.Add(self.addBtn, (0, 0), wx.GBSpan(1, 1))
        grid.Add(self.selectBtn, (0, 1), wx.GBSpan(1, 1))
        grid.Add(self.cancelBtn, (0, 2), wx.GBSpan(1, 1))

        main_sizer.Add(self.peaklist, 1, wx.EXPAND, 2)
        main_sizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def onItemSelected(self, evt):
        self.currentItem = evt.m_itemIndex
        if self.currentItem is None:
            return

    def onSelect(self, evt):
        if self.currentItem is None:
            return

        if self.mode == "calibrants":

            columns = self.peaklist.GetColumnCount()
            tempRow = []
            for col in range(columns):
                item = self.peaklist.GetItem(itemId=self.currentItem, col=col)
                tempRow.append(item.GetText())

            self.config.proteinData = tempRow
            # If dataOut is empty, self.config.proteinData will be reset (in case of cancel)
            self.dataOut = tempRow

            # Now, annotate item
            if len(tempRow) != 0:
                self.parent.panelCCS.topP.onAnnotateItems(evt=None, addProtein=True)

        elif self.mode == "proteins":
            protein = self.peaklist.GetItem(self.currentItem, self.config.ccsDBColNames["protein"]).GetText()
            mw = self.peaklist.GetItem(self.currentItem, self.config.ccsDBColNames["mw"]).GetText()

            self.config.proteinData = [protein, mw]
            self.dataOut = [protein, mw]

            # Now annotate item
            if len(self.dataOut) != 0:
                self.parent.panelDocuments.documents.panelInfo.onAnnotateProteinInfo(data=self.config.proteinData)

    def onPopulateTable(self):

        if self.mode == "calibrants":
            try:
                if self.ccsDB is not None:
                    pass
            except TypeError:
                ccsDBlist = self.ccsDB.values.tolist()
                for row in ccsDBlist:
                    self.peaklist.Append(row)

        elif self.mode == "proteins":
            try:
                if self.ccsDB is not None:
                    pass
            except TypeError:
                # Convert the DB to dictionary --> list of lists
                ccsDBDict = self.ccsDB.to_dict(orient="index")
                tempData = []
                for key in ccsDBDict:
                    tempData.append([ccsDBDict[key]["Protein"], ccsDBDict[key]["MW"], str(ccsDBDict[key]["Subunits"])])

                tempData.sort()
                tempData = list(item for item, _ in itertools.groupby(tempData))
                for row in tempData:
                    self.peaklist.Append(row)

    def OnGetColumnClick(self, evt):
        self.OnSortByColumn(column=evt.GetColumn())

    def OnSortByColumn(self, column):
        """
        Sort data in peaklist based on pressed column
        """
        # Check if it should be reversed
        if self.lastColumn is None:
            self.lastColumn = column
        elif self.lastColumn == column:
            if self.reverse:
                self.reverse = False
            else:
                self.reverse = True
        else:
            self.reverse = False
            self.lastColumn = column

        columns = self.peaklist.GetColumnCount()
        rows = self.peaklist.GetItemCount()

        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.peaklist.GetItem(itemId=row, col=col)
                #  We want to make sure certain columns are numbers
                if (
                    col == self.config.ccsDBColNames["mw"]
                    or col == self.config.ccsDBColNames["ion"]
                    or col == self.config.ccsDBColNames["hePos"]
                    or col == self.config.ccsDBColNames["n2Pos"]
                    or col == self.config.ccsDBColNames["heNeg"]
                    or col == self.config.ccsDBColNames["n2Neg"]
                ):
                    itemData = str2num(item.GetText())
                    if itemData is None:
                        itemData = 0
                    tempRow.append(itemData)
                # Integers
                elif col == self.config.ccsDBColNames["units"] or col == self.config.ccsDBColNames["charge"]:
                    itemData = str2int(item.GetText())
                    if itemData is None:
                        itemData = 0
                    tempRow.append(itemData)
                # Text
                else:
                    tempRow.append(item.GetText())
            tempData.append(tempRow)

        # Sort data
        tempData.sort(key=itemgetter(column), reverse=self.reverse)
        # Clear table
        self.peaklist.DeleteAllItems()

        # Reinstate data
        rowList = np.arange(len(tempData))
        for row in rowList:
            self.peaklist.Append(tempData[row])
