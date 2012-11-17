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
from PyQt4.QtCore import pyqtProperty

from tulpenmanie.model.commodities import commodities_model


# The problem the numbers need to be prefixed with 0. and some 0s
# Maybe they should all display decimals


class _AssetLabel(QtGui.QLineEdit):

    def setPrefix(self, prefix):
        self.prefix = prefix

    def setSuffix(self, suffix):
        self.suffix = suffix


class _AssetIntLabel(_AssetLabel):

    def __init__(self, factor=None, precision=None, parent=None):
        super(_AssetLabel, self).__init__(parent,
                                          readOnly=True)
        self.setAlignment(QtCore.Qt.AlignLeft)
        self.prefix = None
        self.suffix = None

    def textFromValue(self, value):
        text = QtCore.QString().setNum(value)
        if self.prefix:
            text.prepend(self.prefix)
        if self.suffix:
            text.append(self.suffix)

        return text

class _AssetDecimalLabel(_AssetLabel):

    def __init__(self, factor, precision, parent=None):
        super(_AssetLabel, self).__init__(parent)
        self.setAlignment(QtCore.Qt.AlignLeft)
        self.factor = float(factor)
        self.precision = precision
        self.prefix = None
        self.suffix = None

    def textFromValue(self, value):
        if self.factor > 1:
            value /= self.factor
            value = round(value, self.precision)

        text = QtCore.QString().setNum(value)

        if self.prefix:
            text.prepend(self.prefix)
        if self.suffix:
            text.append(self.suffix)
        return text


class _AssetAmountLabel():

    def setValue(self, value):
        self.setText(self.textFromValue(value))

class AssetIntAmountLabel(_AssetIntLabel, _AssetAmountLabel):
    pass
class AssetDecimalAmountLabel(_AssetDecimalLabel, _AssetAmountLabel):
    pass


class _BalanceLabel():

    steady_style = 'color : black'
    increase_style = 'color : green'
    decrease_style = 'color : red'

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

        text = self.textFromValue(value)
        self.setText(text)
        self.setToolTip(QtCore.QCoreApplication.translate(
            "balance display widget", "liquid balance"))
        self.estimated = False

    def change_value(self, change):
        value = self.value + change

        self.setStyleSheet(self.steady_style)
        self.setText(self.textFromValue(value))
        self.setToolTip(QtCore.QCoreApplication.translate(
            "balance display widget", "estimated liquid balance"))
        self.estimated = True


class BalanceIntLabel(_AssetIntLabel, _BalanceLabel):

    def __init__(self, factor=None, precision=None, parent=None):
        super(BalanceIntLabel, self).__init__(parent)
        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.value = None
        self.estimated = True


class BalanceDecimalLabel(_AssetDecimalLabel, _BalanceLabel):

    def __init__(self, factor, precision, parent=None):
        super(BalanceDecimalLabel, self).__init__(factor, precision, parent)
        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.value = None
        self.estimated = True


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
        else:
            self.setPalette(self.steady_palette)

        self.value = value
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


class AssetDecimalSpinBox(QtGui.QDoubleSpinBox):

    decimal_point = QtCore.QLocale().decimalPoint()
    # This valueChanged may not get used since it takes an int
    valueChanged = QtCore.pyqtSignal(int)

    def __init__(self, factor, precision, parent=None):
        super(AssetDecimalSpinBox, self).__init__(parent)
        self.factor = float(factor)
        self.setDecimals(precision)
        self.precision = precision
        self.setRange(0, (factor * 10000) -1 )

    def setValue(self, value):
        value /= self.factor
        value = round(value, self.precision)
        super(AssetDecimalSpinBox, self).setValue(value)

    def value(self):
        text = self.cleanText().remove(self.decimal_point)
        value, ok = text.toInt()
        assert ok
        return value


class AssetIntSpinBox(QtGui.QSpinBox):

    def __init__(self, factor=1, precision=None, parent=None):
        super(AssetIntSpinBox, self).__init__(parent)
        self.setRange(0, (factor * 10000) -1 )


class AssetSpinBox(QtGui.QDoubleSpinBox):

    # TODO avoid precision for now

    decimal_point = QtCore.QLocale().decimalPoint()
    valueChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(AssetSpinBox, self).__init__(parent)
        self.factor = 1
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
