# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging
import os
import threading

import numpy as np
import wx
logger = logging.getLogger('origami')


class data_visualisation():

    def __init__(self, presenter, view, config):
        self.presenter = presenter
        self.view = view
        self.config = config

        # processing links
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling

        # panel links
        self.documentTree = self.view.panelDocuments.documents

        self.plotsPanel = self.view.panelPlots

        self.ionPanel = self.view.panelMultipleIons
        self.ionList = self.ionPanel.peaklist

        self.textPanel = self.view.panelMultipleText
        self.textList = self.textPanel.peaklist

        self.filesPanel = self.view.panelMML
        self.filesList = self.filesPanel.peaklist

        # add application defaults
        self.plot_page = None

    def on_threading(self, action, args):
        """
        Execute action using new thread
        args: list/dict
            function arguments
        action: str
            decides which action should be taken
        """
        th = None

        # Start thread
        try:
            th.start()
        except Exception as e:
            logger.warning('Failed to execute the operation in threaded mode. Consider switching it off?')
            logger.error(e)
