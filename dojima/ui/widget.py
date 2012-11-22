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

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtProperty

from dojima.model.commodities import commodities_model

class _AssetLCDWidget(QtGui.QLCDNumber):

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

    def __init__(self, parent=None):
        super(_AssetLCDWidget, self).__init__(parent)
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
        self.display(value)


class AssetIntLCDWidget(_AssetLCDWidget):

    def __init__(self, factor=None, precision=None, parent=None):
        super(AssetIntLCDWidget, self).__init__(parent)


class AssetDecimalLCDWidget(_AssetLCDWidget):

    def __init__(self, factor=1, precision=0, parent=None):
        super(AssetDecimalLCDWidget, self).__init__(parent)
        self.precision= precision
        self.factor = float(factor)

    def display(self, value):
        value /= self.factor
        value = round(value, self.precision)
        super(AssetDecimalLCDWidget, self).display(value)


class BitcoinSpin(QtGui.QDoubleSpinBox):

    def __init__(self, parent=None):
        super(BitcoinSpin, self).__init__(parent)
        self.setMaximum(21000000)
        self.setDecimals(8)


class AssetAmountView(QtGui.QLineEdit):

    def __init__(self, factor=1, parent=None):
        super(AssetAmountView, self).__init__(parent, readOnly=True)
        self.factor = factor
        self.prefix = None
        self.suffix = None
        self._value = None

    def setFactor(self, factor):
        self.factor = float(factor)

    def setPrefix(self, prefix):
        self.prefix = prefix

    def setSuffix(self, suffix):
        self.suffix = suffix

    def setValue(self, value):
        self._value = value
        self.setText(self.textFromValue(value))

    def textFromValue(self, value):
        if self.factor > 1:
            value /= self.factor
            #value = round(value, self.precision)

        text = QtCore.QString().setNum(value)
        if self.prefix:
            text.prepend(self.prefix)
        if self.suffix:
            text.append(self.suffix)

        return text

    def value(self):
        return self._value


class AssetSpinBox(QtGui.QDoubleSpinBox):

    # TODO avoid precision for now

    decimal_point = QtCore.QLocale().decimalPoint()
    #valueChanged = QtCore.pyqtSignal(int)

    def __init__(self, factor=1, parent=None):
        super(AssetSpinBox, self).__init__(parent)
        self.factor = factor
        self.precision = None
        self.scale = None

    def setFactor(self, factor):
        self.factor = factor
        self.setSingleStep(10.0 * factor)
        # TODO check this
        if self.scale:
            maximum = (factor * scale) - factor
            self.setMaximum(maximum)

    def setPrecision(self, precision):
        self.precision = precision

    def setScale(self, scale):
        step = pow(10, scale)
        self.setSingleStep(step)
        self.setMaximum( step * 99 )

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

        text = QtCore.QString().setNum(value)

        #if self.prefix():
        #    text.prepend(self.prefix())
        #if self.suffix():
        #    text.append(self.suffix())

        return text

    def value(self):
        text = self.cleanText().remove(self.decimal_point)
        value, ok = text.toInt()
        assert ok
        return value

    def valueFromText(self, text):
        text.remove(self.decimal_point)

        if self.prefix():
            text.remove(self.prefix())
        if self.suffix():
            text.remove(self.suffix())

        value, ok = text.toInt()
        assert ok
        if self.factor > 1:
            value *= self.factor

        #self.valueChanged.emit(value)
        return value


class ScaleSpin(QtGui.QSpinBox):

    def __init__(self, parent=None):
        super(ScaleSpin, self).__init__(parent)
        self.scale = 1
        self.setValue(1)
        self.setMaximum(100)

    def stepBy(self, steps):
        self.scale += steps
        self.setMinimum(self.value())
        print self.scale
        value = pow(10, self.scale)
        self.setValue(value)
        self.setMaximum(value * 10)
