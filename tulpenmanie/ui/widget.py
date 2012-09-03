from decimal import *

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtProperty

class CommodityWidgetBase(object):

    def _set_commodity_attributes(self, commodity_row):
        model = self.manager.commodities_model
        self.prefix = model.item(commodity_row, model.PREFIX).text()
        self.suffix = model.item(commodity_row, model.SUFFIX).text()
        self.precision = int(model.item(commodity_row, model.PRECISION).text())


class BigCommodityWidget(QtGui.QLabel, CommodityWidgetBase):

    def __init__(self, title, commodity_row, parent=None):
        super(BigCommodityWidget, self).__init__(parent)
        self._set_commodity_attributes(commodity_row)
        self.value = None

        title_label = QtGui.QLabel(title)
        title_label.setAlignment(QtCore.Qt.AlignHCenter)
        self.label = QtGui.QLabel()
        self.label.setAlignment(QtCore.Qt.AlignHCenter)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(title_label)
        layout.addWidget(self.label)

        self.setLayout(layout)

    def setValue(self, value):
        ## Change color of background, not text
        if self.value and value > self.value:
            self.setStyleSheet('color : green')
        elif self.value and value < self.value:
            self.setStyleSheet('color : red')
        else:
            self.setStyleSheet('color : black')
        self.value = value

        value = round(value, self.precision)
        self.label.setText(self.prefix + str(value) + self.suffix)


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
