# Dojima, a markets client.
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import otapi
from PyQt4 import QtCore, QtGui

import dojima.ui.ot.views


class CreateNymDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(CreateNymDialog, self).__init__(parent)

        self.key_size_combo = QtGui.QComboBox()
        self.key_size_combo.addItems( ("1024", "2048", "4096", "8192") )
        self.key_size_combo.setCurrentIndex(1)
        self.key_size_combo.setToolTip(
            QtCore.QCoreApplication.translate(
                'CreateNymDialog', "The amount of entropy in bits\n"
                                   "used to create this nym keypair.",
                "This one is pretty technical, this option basically sets the "
                "relative difficulty of compromising the encyption involed with "
                "this nym. Suffice to say it is much harder to crack at any "
                "level than goverment propaganda would make it appear."))

        self.name_edit = QtGui.QLineEdit()

        form_layout = QtGui.QFormLayout()
        form_layout.addRow(
            QtCore.QCoreApplication.translate('CreateNymDialog', "key size",
                                              "or key difficulty"),
            self.key_size_combo)
        form_layout.addRow(
            QtCore.QCoreApplication.translate('CreateNymDialog', "label"),
            self.name_edit)

        create_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('CreateNymDialog', "Create"))
        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(create_button, button_box.ActionRole)
        button_box.addButton(QtGui.QDialogButtonBox.Cancel)

        create_button.clicked.connect(self.createNym)
        button_box.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def createNym(self):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        error_title = QtCore.QCoreApplication.translate('CreateNymDialog',
                                                        "Error")

        nym_id = otapi.OTAPI_Basic_CreateNym(
            int(self.key_size_combo.currentText()))

        if not nym_id:
            QtGui.QApplication.restoreOverrideCursor()
            QtGui.QMessageBox.warning(self, error_title,
                                      otapi.OT_API_PeekMemlogFront())
            return

        # TODO make a selectable default signing nym
        # to use for this sort of thing
        otapi.OTAPI_Basic_SetNym_Name(nym_id, nym_id, str(self.name_edit.text()))

        QtGui.QApplication.restoreOverrideCursor()
        self.accept()


class SelectNymDialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(SelectNymDialog, self).__init__(parent)

        self.nym_combo = dojima.ui.ot.views.ComboBox()
        self.nym_combo.setModel(dojima.model.ot.nyms.model)
        button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                            QtGui.QDialogButtonBox.Cancel)

        layout = QtGui.QFormLayout()
        layout.addRow(
            QtCore.QCoreApplication.translate('SelectNymDialog',
                                              "Nym:"),
            self.nym_combo)
        self.setLayout(layout)

        layout.addRow(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    @property
    def nym_id(self):
        return self.nym_combo.getOTID()
