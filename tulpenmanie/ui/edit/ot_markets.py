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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PyQt4 import QtCore, QtGui
import otapi

import tulpenmanie.ot.contract
import tulpenmanie.model.ot.servers
import tulpenmanie.model.ot.assets
from tulpenmanie.model.commodities import commodities_model
from tulpenmanie.ui.edit.commodity import NewCommodityDialog


# TODO fetch unknown assets from the server with
# OT_API_getContract, make it optional so local storage doesn't get cluttered

# TODO actually there isn't much point to this dialog, we don't need the markets
# to make an offer

class EditWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        super(EditWidget, self).__init__(parent)
        self.servers_model = tulpenmanie.model.ot.servers.OTServersTreeModel()
        self.assets_model = tulpenmanie.model.ot.assets.OTAssetsSettingsModel()

        self.markets_view = QtGui.QTreeView()
        self.markets_view.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.markets_view.setModel(self.servers_model)
        #TODO make a loop to resize past column 0
        self.markets_view.resizeColumnToContents(1)
        self.markets_view.resizeColumnToContents(2)
        self.markets_view.resizeColumnToContents(3)

        refresh_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('EditWidget',
                                              "Refresh"))
        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(refresh_button, button_box.ActionRole)

        add_to_quick_markets_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('EditWidget',
                                              "add to quick markets"),
            self, triggered=self.addToQuickMarkets)

        map_to_commodities_action = QtGui.QAction(
            QtCore.QCoreApplication.translate('EditWidget', "map to..."),
            self, triggered=self.map_to_commodity)

        self.markets_view.addAction(add_to_quick_markets_action)
        self.markets_view.addAction(map_to_commodities_action)
        self.markets_view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.markets_view)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def addToQuickMarkets(self):
        item = self.markets_view.currentIndex().internalPointer()
        base_id = item.data(item.BASE, QtCore.Qt.UserRole)
        counter_id = item.data(item.COUNTER, QtCore.Qt.UserRole)
        for asset_id in base_id, counter_id:
            search = self.assets_model.findItems(asset_id)
            print search
            if not search:
                dialog = AssetMappingDialog(asset_id, self)
                if not dialog.exec_(): return

        # Now add the market to the exchanges/markets model


    def map_to_commodity(self):
        index = self.markets_view.currentIndex()
        asset_id = self.servers_model.data(index, QtCore.Qt.UserRole)
        dialog = AssetMappingDialog(asset_id, self)
        dialog.exec_()


class AssetMappingDialog(QtGui.QDialog):

    # Maybe throw some random numbers into the preview string
    preview_string = QtCore.QCoreApplication.translate(
        'AssetMappingDialog', "A %1 is %2 %3", "local, amount, remote")

    def __init__(self, assetId, parent=None):
        super(AssetMappingDialog, self).__init__(parent)

        self.asset_id = assetId
        self.contract = tulpenmanie.ot.contract.CurrencyContract(self.asset_id)
        self.asset_name = self.contract.getName()

        # UI
        self.commodity_combo = QtGui.QComboBox()
        self.commodity_combo.setModel(commodities_model)
        self.commodity_combo.setModelColumn(commodities_model.NAME)
        self.commodity_combo.setToolTip(
            QtCore.QCoreApplication.translate('AssetMappingDialog',
                """Map this Open Transactions Asset to a locally defined  """
                """fungible instrument."""))

        self.factor_spin = QtGui.QSpinBox()
        self.factor_spin.setMaximum(1000000000)
        self.factor_spin.setMinimum(1)
        self.factor_spin.setToolTip(
            # TODO probably strip this tip
            QtCore.QCoreApplication.translate('AssetMappingDialog',
                """Open Transactions only uses integer math, therefore """
                """assets backed by instruments that may be divided into """
                """increments less than one (1.0) will most commonly be """
                """ expressed """
                """using that instrument's smallest unit, such as a cent. """
                """To display these assets in the most practical manner """
                """a factor may be used to convert these units into larger, """
                """more common units. """))

        new_local_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('AssetMappingDialog',
                                              "new local"))
        self.preview_label = QtGui.QLabel()

        self.contract_view = QtGui.QPlainTextEdit(
            otapi.OT_API_GetAssetType_Contract(self.asset_id))
        self.contract_view.setReadOnly(True)
        self.contract_view.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)

        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(new_local_button, QtGui.QDialogButtonBox.ActionRole)
        button_box.addButton(QtGui.QDialogButtonBox.Ok)
        button_box.addButton(QtGui.QDialogButtonBox.Cancel)

        # layout
        form_layout = QtGui.QFormLayout()
        form_layout.addRow(
            QtCore.QCoreApplication.translate('AssetMappingDialog',
                                              "map to"),
            self.commodity_combo)
        form_layout.addRow(
            QtCore.QCoreApplication.translate('AssetMappingDialog',
                                              "at a factor of"),
            self.factor_spin)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.preview_label)
        layout.addWidget(self.contract_view)
        layout.addWidget(button_box)
        self.setLayout(layout)

        # connections
        self.commodity_combo.currentIndexChanged[str].connect(
            self.commodityChanged)
        self.factor_spin.valueChanged[str].connect(
            self.factorChanged)
        new_local_button.clicked.connect(self.new_local)
        button_box.accepted.connect(self.submit)
        button_box.rejected.connect(self.reject)

        # select
        self.model = tulpenmanie.model.ot.assets.OTAssetsSettingsModel()
        search = self.model.findItems(self.asset_id)
        if not search:
            self.row = None
            self.factor_spin.setValue(self.contract.getFactor())
            return

        self.row = search[0].row()
        commodity_id = self.model.item(self.row, self.model.LOCAL_ID).text()

        search = commodities_model.findItems(commodity_id)
        if not search: return

        commodity_row = search[0].row()
        self.commodity_combo.setCurrentIndex(commodity_row)
        factor = self.model.item(self.row, self.model.FACTOR).text()
        if factor:
            self.factor_spin.setValue(int(factor))
        else:
            self.factor_spin.setValue(self.contract.getFactor())

        self.preview_label.setText(
            QtCore.QCoreApplication.translate('AssetMappingDialog',
                                              "previous mapping found"))

    def commodityChanged(self, commodity):
        factor = self.factor_spin.value()
        self.setPreview(commodity, factor)

    def factorChanged(self, factor):
        commodity = self.commodity_combo.currentText()
        self.setPreview(commodity, factor)

    def setPreview(self, commodity, factor):
        self.preview_label.setText(
            self.preview_string.arg(commodity
                                    ).arg(factor
                                          ).arg(self.asset_name))
    def new_local(self):
        dialog = NewCommodityDialog(self,
                                    name=self.asset_name,
                                    prefix=self.contract.getSymbol(),
                                    suffix=self.contract.getTLA(),
                                    precision=self.contract.getDecimalPower())
        if dialog.exec_():
            self.commodity_combo.setCurrentIndex(dialog.row)

    def submit(self):
        # this needs to reject() the dialog if everything isn't right
        commodity_id = commodities_model.item(
            self.commodity_combo.currentIndex(), commodities_model.UUID).text()
        print commodity_id

        if self.row is None:
            self.row = self.model.rowCount()

        item = QtGui.QStandardItem(self.asset_id)
        self.model.setItem(self.row, self.model.ASSET_ID, item)

        item = QtGui.QStandardItem(commodity_id)
        self.model.setItem(self.row, self.model.LOCAL_ID, item)

        item = QtGui.QStandardItem(self.factor_spin.cleanText())
        self.model.setItem(self.row, self.model.FACTOR, item)

        self.model.submit()
        self.accept()
