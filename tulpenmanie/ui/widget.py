# Tulpenmanie, a commodities market client.
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

from decimal import *

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtProperty

import tulpenmanie.commodity

class CommodityWidgetBase(object):

    def _set_commodity_attributes(self, commodity_row):
        model = tulpenmanie.commodity.commodities_model
        self.prefix = model.item(commodity_row, model.PREFIX).text()
        self.suffix = model.item(commodity_row, model.SUFFIX).text()
        self.precision = int(model.item(commodity_row, model.PRECISION).text())


class CommodityLcdWidget(QtGui.QLCDNumber, CommodityWidgetBase):
    # maybe display prefixes/suffixes as well

    def __init__(self, commodity_row, parent=None):
        super(CommodityLcdWidget, self).__init__(parent)

        self.setStyleSheet('background : black')
        self.default_palette = QtGui.QPalette(self.palette())
        self.default_palette.setColor(QtGui.QPalette.WindowText,
                                      QtCore.Qt.white)

        self.increase_palette = QtGui.QPalette(self.palette())
        self.increase_palette.setColor(QtGui.QPalette.WindowText,
                                       QtCore.Qt.green)

        self.decrease_palette = QtGui.QPalette(self.palette())
        self.decrease_palette.setColor(QtGui.QPalette.WindowText,
                                       QtCore.Qt.red)
        self.setSegmentStyle(self.Flat)

        model = tulpenmanie.commodity.commodities_model
        self.precision = int(model.item(commodity_row, model.PRECISION).text())
        self.value = None

    def setValue(self, value):
        if self.value and value > self.value:
            self.setPalette(self.increase_palette)
        elif self.value and value < self.value:
            self.setPalette(self.decrease_palette)
        else:
            self.setPalette(self.default_palette)

        self.value = value
        value_string = str(round(value, self.precision))
        left, right = value_string.split('.')
        value_string = left + '.' + right.ljust(self.precision, '0')

        length = len(value_string)
        if self.digitCount() < length:
            self.setDigitCount(length)
        self.display(value_string)


class CommoditySpinBox(QtGui.QDoubleSpinBox, CommodityWidgetBase):

    def __init__(self, commodity_row, parent=None):
        super(CommoditySpinBox, self).__init__(parent)

        self._set_commodity_attributes(commodity_row)
        self.setPrefix(self.prefix)
        self.setSuffix(self.suffix)
        self.setDecimals(self.precision)


class CommodityWidget(QtGui.QLabel, CommodityWidgetBase):

    alignment = QtCore.Qt.AlignRight

    def __init__(self, commodity_row, parent=None):
        super(CommodityWidget, self).__init__(parent)

        self._set_commodity_attributes(commodity_row)
        self.value = None

    def refresh_settings(self):
        #maybe prefix, suffix, precision best drawn from the model each time
        pass

    def setValue(self, value):
        if self.value and value > self.value:
            self.setStyleSheet('color : green')
        elif self.value and value < self.value:
            self.setStyleSheet('color : red')
        else:
            self.setStyleSheet('color : black')
        self.value = value

        value = round(value, self.precision)
        self.setText(self.prefix + str(value) + self.suffix)


class UuidComboBox(QtGui.QComboBox):

    #TODO set the default model column to 1

    def _get_current_uuid(self):
        return self.model().item(self.currentIndex(), 0).text()

    def _set_current_uuid(self, uuid):
        results = self.model().findItems(uuid)
        if results:
            self.setCurrentIndex(results[0].row())
        else:
            self.setCurrentIndex(-1)

    currentUuid = pyqtProperty(str, _get_current_uuid, _set_current_uuid)
