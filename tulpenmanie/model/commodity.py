# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui

from model.base import FlatSettingsModel


class CommoditiesModel(FlatSettingsModel):

    COLUMNS = 5
    UUID, NAME, PREFIX, SUFFIX, PRECISION = range(COLUMNS)
    SETTINGS_MAP = (('name', NAME), ('prefix', PREFIX),
                    ('suffix', SUFFIX), ('precision', PRECISION))

    def __init__(self, parent=None):
        super(CommoditiesModel, self).__init__('commodities', parent)

    def new_commodity(self):
        uuid = QtCore.QUuid.createUuid().toString()[1:-1]
        item = QtGui.QStandardItem(uuid)

        self.appendRow( (item,
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem(),
                         QtGui.QStandardItem()) )
        return item.row()
