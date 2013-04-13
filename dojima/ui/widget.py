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

from decimal import Decimal

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtProperty

import dojima.data.offers

class _LCDWidget(QtGui.QLCDNumber):

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


class LCDDecimalWidget(_LCDWidget):

    def __init__(self, parent=None):
        super(LCDDecimalWidget, self).__init__(parent, digitCount=8, smallDecimalPoint=True)
        self.setStyleSheet('background : black')
        self.setSegmentStyle(self.Flat)
        self.steady_palette = self.white_palette
        self._value = None

    def setValue(self, value):
        if value == self._value:
            if self.palette is not self.steady_palette:
                self.setPalette(self.steady_palette)
                return

        elif self._value and value > self._value:
            self.setPalette(self.green_palette)
            self.steady_palette = self.light_green_palette
        elif self._value and value < self._value:
            self.setPalette(self.red_palette)
            self.steady_palette = self.light_red_palette
        else:
            self.setPalette(self.steady_palette)

        self._value = value
        # Decimal's get converted to int's here, so make it float #
        self.display(float(value))

        
class LCDIntWidget(_LCDWidget):
    
    def __init__(self, factor, power, parent=None):
        super(LCDIntWidget, self).__init__(parent, digitCount=8, smallDecimalPoint=True)
        self.factor = float(factor)
        self.power = power
        self.setStyleSheet('background : black')
        self.setSegmentStyle(self.Flat)
        self.steady_palette = self.white_palette
        self._value = None

    def setFactor(self, factor):
        self.factor = float(factor)

    def setValue(self, value):
        if value == self._value:
            if self.palette is not self.steady_palette:
                self.setPalette(self.steady_palette)
                return

        elif self._value and value > self._value:
            self.setPalette(self.green_palette)
            self.steady_palette = self.light_green_palette
        elif self._value and value < self._value:
            self.setPalette(self.red_palette)
            self.steady_palette = self.light_red_palette
        else:
            self.setPalette(self.steady_palette)

        self._value = value
        if self.factor > 1:
            value /= self.factor

        self.display(value)
                

class BitcoinSpin(QtGui.QDoubleSpinBox):

    def __init__(self, parent=None):
        super(BitcoinSpin, self).__init__(parent)
        self.setMaximum(21000000)
        self.setDecimals(8)


class _AssetAmountView(QtGui.QLineEdit):

    def changeValue(self, change):
        self._value = self._value + change
        self.setText(self.textFromValue(self._value))
    
    def setPrefix(self, prefix):
        self.prefix = prefix

    def setSuffix(self, suffix):
        self.suffix = suffix

    def setValue(self, value):
        self._value = value
        self.setText(self.textFromValue(value))

    def value(self):
        return self._value    


class AssetAmountDecimalView(_AssetAmountView):

    def __init__(self, parent=None):
        super(AssetAmountDecimalView, self).__init__(parent, readOnly=True)
        self.prefix = None
        self.suffix = None
        self._value = None

    def textFromValue(self, value):
        text = str(value)
        if self.prefix:
            text = self.prefix + text
        if self.suffix:
            text = text + self.suffix
        return text


class AssetAmountIntView(_AssetAmountView):

    def __init__(self, factor=1, parent=None):
        super(AssetAmountIntView, self).__init__(parent, readOnly=True)
        self.factor = float(factor)
        self.prefix = None
        self.suffix = None
        self._value = None

    def setFactor(self, factor):
        self.factor = float(factor)

    def textFromValue(self, value):
        if self.factor > 1:
            value /= self.factor
            #value = round(value, self.precision)

        text = str(value)
        if self.prefix:
            text = self.prefix + text
        if self.suffix:
            text = text + self.suffix

        return text

        
class _AssetSpinBox(QtGui.QDoubleSpinBox):
    #TODO make get value string method

    # factor and scale will determine step size and maximum
    # power will determine the decimals
    # type will determine the base

    # precision can be avoided for now


    #valueChanged = QtCore.pyqtSignal(int)

    def setPrecision(self, precision):
        self.precision = precision
        raise NotImplementedError


class AssetDecimalSpinBox(_AssetSpinBox):

    def __init__(self, precision=None, scale=1, base="decimal", parent=None):
        if base != "decimal":
            raise NotImplementedError("{} base not supported".format(base))
        self.precision = precision
        self.scale = scale

        # need something to round with if scale is set
        if scale > 1:
            # This wont work with non-decimal numbers
            self.scale_round_digits = -len(str(scale)) + 1

        # The super contructor calls textFromValue and maybe others so set
        # attributes first
        super(AssetDecimalSpinBox, self).__init__(parent)
        if (scale is not None and scale > 1):
            step = factor * scale

            self.setSingleStep(step)
            self.setMaximum(step * 99)
        else:
            self.setMaximum(999999999)

    def setScale(self, scale):
        """1, 10, 100, etc"""
        step = scale

        self.setSingleStep(step)
        self.setMaximum(step * 99 )

    def setValue(self, value):
        self._value = value
        if self.precision is not None:
            value = round(value, self.precision)
        super(AssetSpinBox, self).setValue(value)

    def textFromValue(self, value):
        if self.precision:
            value = round(value, self.precision)

        return str(value)

    def value(self):
        text = self.cleanText()
        if not len(text):
            return 0
        else:
            return Decimal(text)

        
class AssetIntSpinBox(_AssetSpinBox):

    decimal_point = QtCore.QLocale().decimalPoint()
    
    def __init__(self, factor=1, power=0, precision=None, scale=1, base="decimal", parent=None):
        if base != "decimal":
            raise NotImplementedError("{} base not supported".format(base))
        self.factor = float(factor)
        self.power = power
        self.precision = precision
        self.scale = scale

        # need something to round with if scale is set
        if scale > 1:
            # This wont work with non-decimal numbers
            self.scale_round_digits = -len(str(scale)) + 1

        # The super contructor calls textFromValue and maybe others so set
        # attributes first
        super(AssetIntSpinBox, self).__init__(parent, decimals=power)
        if (scale is not None and scale > 1):
            step = factor * scale

            self.setSingleStep(step)
            self.setMaximum(step * 99)
        else:
            self.setMaximum(999999999)

    def setFactor(self, factor):
        # TODO 'type="decimal" factor="1000" decimal_power="3"' maybe pow() here?
        self.factor = float(factor)
        step = factor

        if (self.scale > 1):
            step *= self.scale

        self.setSingleStep(step)
        self.setMaximum(step * 99)

    def setScale(self, scale):
        """1, 10, 100, etc"""
        step = scale
        if self.factor > 1:
            step *= self.factor

        self.setSingleStep(step)
        self.setMaximum(step * 99 )

        if scale > 1:
            # This wont work with non-decimal numbers
            self.scale_round_digits = scale * 10

    def setValue(self, value):
        self._value = value
        if self.factor > 1:
            value /= self.factor
        if self.precision is not None:
            value = round(value, self.precision)
        super(AssetSpinBox, self).setValue(value)

    def textFromValue(self, value):
        if self.factor > 1:
            value /= self.factor

            if self.precision:
                value = round(value, self.precision)

        text = str(value)

        return text

        
class OffersView(QtGui.QTableView):

    def hideColumns(self):
        self.hideColumn(0)
        self.hideColumn(3)
        self.hideColumn(4)
        self.hideColumn(5)


class _OfferItemDelegate(QtGui.QItemDelegate):
    # I tried styleitemdelegate but got segfaults
    pass


class OfferItemDecimalDelegate(_OfferItemDelegate):
    def __init__(self, factor=1, prefix=None, suffix=None, parent=None):
        super(OfferItemDecimalDelegate, self).__init__(parent)
        self.prefix = prefix
        self.suffix = suffix

    def paint(self, painter, option, index):
        value = index.model().data(index, QtCore.Qt.UserRole)
        text = str(value)

        if self.prefix:
            text = self.prefix + text
        if self.suffix:
            text = text +  self.suffix

        option.displayAlignment = (QtCore.Qt.AlignRight |
                                   QtCore.Qt.AlignVCenter)
        self.drawDisplay(painter, option, option.rect, text)
        self.drawFocus(painter, option, option.rect)        


class OfferItemIntDelegate(_OfferItemDelegate):
    def __init__(self, factor=1, prefix=None, suffix=None, parent=None):
        super(OfferItemIntDelegate, self).__init__(parent)

        if factor > 1:
            self.factor = float(factor)
        else:
            self.factor = factor

        self.prefix = prefix
        self.suffix = suffix

    def paint(self, painter, option, index):
        value = index.model().data(index, QtCore.Qt.UserRole)

        if self.factor > 1:
            value /= self.factor

        text = str(value)

        if self.prefix:
            text = self.prefix + text
        if self.suffix:
            text = text +  self.suffix

        option.displayAlignment = (QtCore.Qt.AlignRight |
                                   QtCore.Qt.AlignVCenter)
        self.drawDisplay(painter, option, option.rect, text)
        self.drawFocus(painter, option, option.rect)


class OfferStyledItemDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, factor=1, prefix=None, suffix=None, parent=None):
        super(OfferStyledItemDelegate, self).__init__(parent)

        if factor > 1:
            self.factor = float(factor)
        else:
            self.factor = factor

        self.prefix = prefix
        self.suffix = suffix

    def setEditorData(self, editor, index):
        value = index.model().data(index, QtCore.Qt.QUserRole)

        if self.factor > 1:
            value /= self.factor

        text = str(value)

        if self.prefix:
            text = self.prefix + text
        if self.suffix:
            text = text +  self.suffix

            #option.displayAlignment = (QtCore.QtAlignRight |
            #                       QtCore.Qt.AlignVCenter)
        editor.setText(text)


        # I think this can go
class ScaleSpin(QtGui.QSpinBox):

    def __init__(self, parent=None):
        super(ScaleSpin, self).__init__(parent)
        self.scale = 1
        self.setValue(1)
        self.setMaximum(100)

    def stepBy(self, steps):
        self.scale += steps
        self.setMinimum(self.value())
        value = pow(10, self.scale)
        self.setValue(value)
        self.setMaximum(value * 10)
