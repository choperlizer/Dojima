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

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtProperty

import tulpenmanie.commodity

class CommodityWidgetBase(object):

    def get_prefix(self):
        return tulpenmanie.commodity.model.item(
            self.commodity_row, tulpenmanie.commodity.model.PREFIX).text()
    prefix = property(get_prefix)

    def get_suffix(self):
        return tulpenmanie.commodity.model.item(
            self.commodity_row, tulpenmanie.commodity.model.SUFFIX).text()
    suffix = property(get_suffix)

    def get_precision(self):
        precision = tulpenmanie.commodity.model.item(
            self.commodity_row, tulpenmanie.commodity.model.PRECISION).text()
        if not precision:
            precision = None
        else:
            precision = int(precision)
        return precision
    precision = property(get_precision)


class CommodityLcdWidget(QtGui.QLCDNumber, CommodityWidgetBase):

    white_palette = QtGui.QPalette(QtGui.QApplication.palette())
    white_palette.setColor(QtGui.QPalette.WindowText,
                           QtCore.Qt.white)

    green_palette = QtGui.QPalette(QtGui.QApplication.palette())
    green_palette.setColor(QtGui.QPalette.WindowText,
                           QtGui.QColor.fromHsv(120, 255, 255))
    light_green_palette = QtGui.QPalette(QtGui.QApplication.palette())
    light_green_palette.setColor(QtGui.QPalette.WindowText,
                                QtGui.QColor.fromHsv(120, 128, 255))

    red_palette = QtGui.QPalette(QtGui.QApplication.palette())
    red_palette.setColor(QtGui.QPalette.WindowText,
                         QtGui.QColor.fromHsv( 0, 255, 255))
    light_red_palette = QtGui.QPalette(QtGui.QApplication.palette())
    light_red_palette.setColor(QtGui.QPalette.WindowText,
                               QtGui.QColor.fromHsv(0, 128, 255))


    def __init__(self, commodity_row, parent=None):
        super(CommodityLcdWidget, self).__init__(parent)
        self.commodity_row = commodity_row

        self.setStyleSheet('background : black')
        self.setSegmentStyle(self.Flat)
        self.steady_palette = self.white_palette
        self.value = None

    def setValue(self, value):
        if value == self.value:
            if self.palette is not self.steady_palette:
                self.setPalette(self.steady_palette)
                return
        elif self.value and value > self.value:
            self.setPalette(self.green_palette)
            self.steady_palette = self.light_green_palette
        elif self.value and value < self.value:
            self.setPalette(self.red_palette)
            self.steady_palette = self.light_red_palette

        self.value = value
        if self.precision:
            value_string = str(round(value, self.precision))
            left, right = value_string.split('.')
            value_string = left + '.' + right.ljust(self.precision, '0')
        else:
            value_string = str(value)

        length = len(value_string)
        if self.digitCount() < length:
            self.setDigitCount(length)
        self.display(value_string)


class CommoditySpinBox(QtGui.QDoubleSpinBox, CommodityWidgetBase):

    def __init__(self, commodity_row, parent=None):
        super(CommoditySpinBox, self).__init__(parent)
        self.commodity_row = commodity_row

        self.setPrefix(self.get_prefix())
        self.setSuffix(self.get_suffix())
        if self.precision:
            self.setDecimals(self.precision)


class BalanceLabel(QtGui.QLabel, CommodityWidgetBase):
    steady_style = 'color : black'
    increase_style = 'color : green'
    decrease_style = 'color : red'

    def __init__(self, commodity_row, parent=None):
        super(BalanceLabel, self).__init__(parent)
        self.commodity_row = commodity_row
        self.value = None
        self.estimated = True

    def setValue(self, value):
        if value == self.value:
            self.setStyleSheet(self.steady_style)
            if not self.estimated:
                return

        elif self.value and value > self.value:
            self.setStyleSheet(self.increase_style)
        elif self.value and value < self.value:
            self.setStyleSheet(self.decrease_style)

        self.value = value

        if self.precision:
            value = round(value, self.precision)
        self.setText(self.prefix + str(value) + self.suffix)
        self.setToolTip(QtCore.QCoreApplication.translate(
            "balance display widget", "liquid balance"))
        self.estimated = False

    def change_value(self, change):
        value = self.value + change
        self.setStyleSheet(self.steady_style)

        if self.precision:
            value = round(value, self.precision)
        self.setText("(" + self.prefix + str(value) + self.suffix + ")")
        self.setToolTip(QtCore.QCoreApplication.translate(
            "balance display widget", "estimated liquid balance"))
        self.estimated = True


class UuidComboBox(QtGui.QComboBox):

    #TODO set the default tulpenmanie.commodity.model column to 1

    def _get_current_uuid(self):
        return self.model().item(self.currentIndex(), 0).text()

    def _set_current_uuid(self, uuid):
        results = self.model().findItems(uuid)
        if results:
            self.setCurrentIndex(results[0].row())
        else:
            self.setCurrentIndex(-1)

    currentUuid = pyqtProperty(str, _get_current_uuid, _set_current_uuid)
