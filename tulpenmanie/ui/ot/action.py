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

import tulpenmanie.ui.ot.contract
import tulpenmanie.ui.ot.nym


class _DialogAction(QtGui.QAction):

    def __init__(self, parent):
        super(_DialogAction, self).__init__(self.title, parent)
        self.triggered.connect(self.show_dialog)

    def show_dialog(self):
        dialog = self.Dialog(self.parent())
        dialog.show()


class CreateNymAction(_DialogAction):

    title = QtCore.QCoreApplication.translate('CreateNymDialog', "create &nym")
    Dialog = tulpenmanie.ui.ot.nym.CreateNymDialog


class AssetContractImportAction(_DialogAction):
    title = QtCore.QCoreApplication.translate('ContractImportDialog',
                                              "import &asset contract")
    Dialog = tulpenmanie.ui.ot.contract.AssetContractImportDialog


class ServerContractImportAction(_DialogAction):

    title = QtCore.QCoreApplication.translate('ContractImportDialog',
                                              "import &server contract")
    Dialog = tulpenmanie.ui.ot.contract.ServerContractImportDialog


actions = (CreateNymAction,
           AssetContractImportAction,
           ServerContractImportAction)
