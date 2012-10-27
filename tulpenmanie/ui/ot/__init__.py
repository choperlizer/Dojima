# -*- coding: utf-8 -*-
# Tulpenmanie, a markets client.
# Copyright (C) 2012  Emery Hemingway
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public Licnense for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os.path

import otapi
from PyQt4 import QtCore, QtGui

import tulpenmanie.ui.ot.asset
import tulpenmanie.ui.ot.nym 

class CreateNymAction(QtGui.QAction):

    def __init__(self, parent):
        super(CreateNymAction, self).__init__(
            QtCore.QCoreApplication.translate('CreateNymDialog', "create &nym"),
            parent)
        self.triggered.connect(self.show_dialog)

    def show_dialog(self):
        dialog = tulpenmanie.ui.ot.nym.CreateNymDialog(self.parent())
        dialog.show()


class AssetContractImportAction(QtGui.QAction):

    def __init__(self, parent):
        super(AssetContractImportAction, self).__init__(
            QtCore.QCoreApplication.translate('AssetContractImportDialog',
                                              "import &asset contract"),
            parent)
        self.triggered.connect(self.show_dialog)

    def show_dialog(self):
        dialog = tulpenmanie.ui.ot.asset.AssetContractImportDialog(self.parent())
        dialog.show()


actions = (CreateNymAction, AssetContractImportAction,)

