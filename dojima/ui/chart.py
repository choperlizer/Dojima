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

import matplotlib.ticker
import matplotlib.figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.finance


class _ChartDialog(QtGui.QDialog):

    def __init__(self, proxy, parent=None):
        super(_ChartDialog, self).__init__(parent)
        self.proxy = proxy

        self.chart_canvas = ChartCanvas(self)

        self.refresh_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate('ChartDialog',
                                              "Refresh"))

        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(self.refresh_button, button_box.ActionRole)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.chart_canvas)
        layout.addWidget(button_box)
        self.setLayout(layout)

        self.refresh_button.clicked.connect(self.requestRefresh)
        self.proxy.refreshed.connect(self.plot)
        self.requestRefresh()

    def requestRefresh(self):
        self.refresh_button.setDisabled(True)
        self.proxy.refresh()


class DepthDialog(_ChartDialog):
        
    def plot(self, data):
        self.refresh_button.setEnabled(True)
        if data is None:
            QtGui.QMessageBox.warning(self,
                QtCore.QCoreApplication.translate("DepthChartDialog",
                                                  "Depth Chart"),
                QtCore.QCoreApplication.translate("DepthChartDialog",
                                                  "Not enough offer data to chart."))
            return
        self.chart_canvas.axes.plot(data[0], data[1])
        self.chart_canvas.draw()


class TradesDialog(_ChartDialog):

    def plot(self, data):
        self.refresh_button.setEnabled(True)
        if data is None:
            QtGui.QMessageBox.warning(self,
                QtCore.QCoreApplication.translate("TradesChartDialog",
                                                  "Trades Chart"),
                QtCore.QCoreApplication.translate("TradesChartDialog",
                                                  "Not enough trade data to chart."))
            return
        self.chart_canvas.axes.plot(data)
        self.chart_canvas.draw()


class ChartCanvas(FigureCanvas):

    def __init__(self, parent):
        figure = matplotlib.figure.Figure()
        self.axes = figure.add_subplot(111)

        FigureCanvas.__init__(self, figure)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        """
        # Set Y tick format
        model =  tulpenmanie.market.model
        search = model.findItems(parent.market_uuid,
                                 QtCore.Qt.MatchExactly,
                                 model.UUID)
        row = search[0].row()
        commodity_uuid = model.item(row, model.COUNTER).text()
n
        model =  tulpenmanie.commodity.model
        search = model.findItems(commodity_uuid,
                                 QtCore.Qt.MatchExactly,
                                 model.UUID)
        row = search[0].row()
        prefix = model.item(row, model.PREFIX).text()
        suffix = model.item(row, model.SUFFIX).text()
        precision = model.item(row, model.PRECISION).text()

        format_string = QtCore.QString()
        if prefix:
            format_string.append(prefix)
        format_string.append('%1')
        if precision:
            format_string.append("." + precision + 'f')
        if suffix:
            format_string.append(suffix)

        formatter = matplotlib.ticker.FormatStrFormatter(format_string)
        self.axes.yaxis.set_major_formatter(formatter)
        """
        #self.axes.xaxis_date()

        self.cid = self.mpl_connect('button_press_event', self.onclick)

    def onclick(self, event):
        print(self.parent())



"""
class Dialog(QtGui.QDialog):

    def __init__(self, market_uuid, parent):
        super(Dialog, self).__init__(parent)
        self.market_uuid = market_uuid
        self.exchanges = dict()

        #self.menu_bar = QtGui.QMenuBar(self)
        #self.plot_menu = QtGui.QMenu("plot", self.menu_bar)
        #self.menu_bar.addMenu(self.plot_menu)

        start_group = QtGui.QGroupBox(QtCore.QCoreApplication.translate(
            "Dialog", "start time"))

        date_button = QtGui.QRadioButton(QtCore.QCoreApplication.translate(
            "Dialog", "&date"))
        yesterday = QtCore.QDate.currentDate().addDays(-1)
        date_edit = QtGui.QDateTimeEdit(yesterday, date_button)
        date_edit.setMaximumDate(yesterday)
        date_edit.setDisplayFormat('yyyy-MM-dd')
        date_edit.setCalendarPopup(True)
        date_button.toggled.connect(date_edit.setEnabled)

        offset_button = QtGui.QRadioButton(QtCore.QCoreApplication.translate(
            "Dialog", "&offset"))
        offset_days_edit = QtGui.QSpinBox(offset_button)
        offset_days_edit.setSuffix(QtCore.QCoreApplication.translate(
            "Dialog", " days"))
        offset_days_edit.setValue(1)
        offset_hours_edit = QtGui.QSpinBox(offset_button)
        offset_hours_edit.setMaximum(23)
        offset_hours_edit.setSuffix(QtCore.QCoreApplication.translate(
            "Dialog", " hours"))
        offset_button.toggled.connect(offset_days_edit.setEnabled)
        offset_button.toggled.connect(offset_hours_edit.setEnabled)

        start_layout = QtGui.QHBoxLayout()
        start_layout.addWidget(date_button)
        start_layout.addWidget(date_edit)
        start_layout.addWidget(offset_button)
        start_layout.addWidget(offset_days_edit)
        start_layout.addWidget(offset_hours_edit)
        start_group.setLayout(start_layout)
        date_button.setChecked(True)
        offset_button.toggled.emit(False)

        period_group = QtGui.QGroupBox(QtCore.QCoreApplication.translate(
            "Dialog", "period size:"))
        days_button = QtGui.QRadioButton(QtCore.QCoreApplication.translate(
            "Dialog", "&days"))
        self.period_days_edit = QtGui.QSpinBox()
        self.period_days_edit.setValue(1)
        days_button.toggled.connect(self.period_days_edit.setEnabled)

        subday_button = QtGui.QRadioButton(QtCore.QCoreApplication.translate(
            "Dialog", "&sub-day"))
        self.period_subday_edit = QtGui.QTimeEdit()
        self.period_subday_edit.setDisplayFormat('HH:mm')
        self.period_subday_edit.setToolTip(QtCore.QCoreApplication.translate(
            "Dialog", "hours:minutes"))
        subday_button.toggled.connect(self.period_subday_edit.setEnabled)
        period_layout = QtGui.QHBoxLayout()
        period_layout.addWidget(days_button)
        period_layout.addWidget(self.period_days_edit)
        period_layout.addWidget(subday_button)
        period_layout.addWidget(self.period_subday_edit)
        period_group.setLayout(period_layout)
        days_button.setChecked(True)
        subday_button.toggled.emit(False)

        top_layout = QtGui.QHBoxLayout()
        top_layout.addWidget(start_group)
        top_layout.addWidget(period_group)

        # HARDCODING
        self.chart_canvas = ChartCanvas(self)

        self.plot_combo = QtGui.QComboBox()
        self.exchange_combo = QtGui.QComboBox()
        self.stacked_layout = QtGui.QStackedLayout()

        plot_layout = QtGui.QHBoxLayout()

        plot_layout.addWidget(self.plot_combo)
        plot_layout.addWidget(self.exchange_combo)
        plot_layout.addLayout(self.stacked_layout)
        for Widget in plot_widgets:
            widget = Widget(self)
            self.stacked_layout.addWidget(widget)
            self.plot_combo.addItem(widget.name)
        self.plot_combo.currentIndexChanged.connect(
            self.stacked_layout.setCurrentIndex)

        self.plots_model = QtGui.QStandardItemModel()
        plots_view = QtGui.QTableView()
        plots_view.setModel(self.plots_model)

        layout = QtGui.QVBoxLayout()
        #layout.addWidget(self.menu_bar)
        layout.addLayout(top_layout)
        layout.addWidget(self.chart_canvas)
        layout.addWidget(plots_view)
        layout.addLayout(plot_layout)
        self.setLayout(layout)

        #TODO it'd be nice to build a list of exchanges with market_uuid
        # support when the model is parsed at startup and when editing settings
        for row in range(tulpenmanie.exchange.model.rowCount()):
            exchange_item = tulpenmanie.exchange.model.item(row, 0)
            exchange_name = exchange_item.text()
            exchange_object = tulpenmanie.exchange.get_exchange_object(
                exchange_name, market_uuid)
            if exchange_object:
                self.exchange_combo.addItem(exchange_name)

    def get_axes(self):
        return self.chart_canvas.axes

    def add_lines(self, plot_name, exchange_name, lines):
        plot_item = QtGui.QStandardItem(plot_name)
        exchange_item = QtGui.QStandardItem(exchange_name)
        plot_item.lines = lines
        exchange_item.lines = lines



"""
"""
class _PlotWidget(QtGui.QWidget):

    def __init__(self, parent):
        super(_PlotWidget, self).__init__(parent)
        self.parent = parent
        self.plot_button = QtGui.QPushButton(QtCore.QCoreApplication.translate(
            "Dialog", "plot"))
        self._populate_widget()
        self.plot_button.clicked.connect(self._request_data)

    def _populate_widget(self):
        layout = QtGui.QHBoxLayout()
        layout.addStretch(1)
        layout.addWidget(self.plot_button)
        self.setLayout(layout)


class _QuotePlot(_PlotWidget):
    name = QtCore.QCoreApplication.translate("PeriodHighPlot",
                                             "period high price")

    def _request_data(self):
        exchange_name = self.parent.exchange_combo.currentText()
        self.quotes_proxy = tulpenmanie.data.QuotesProxy(
            self.parent.market_uuid, exchange_name)

        self.quotes_proxy.refreshed_signal.connect(self._plot)
        self.quotes_proxy.refresh()


class PeriodHigh(_QuotePlot):
    name = QtCore.QCoreApplication.translate("PeriodHigh",
                                             "period high price")
    def _plot(self, quotes):
        axes = self.parent.get_axes()
        axes.plot(quotes[:,0], quotes[:,3])
        self.parent.chart_canvas.draw()

plot_widgets.append(PeriodHigh)


class PeriodLow(_QuotePlot):
    name = QtCore.QCoreApplication.translate("PeriodHigh",
                                             "period low price")
    def _plot(self, quotes):
        axes = self.parent.get_axes()
        axes.plot(quotes[:,0], quotes[:,4])
        self.parent.chart_canvas.draw()

plot_widgets.append(PeriodLow)

class CandleStick(_QuotePlot):
    name = QtCore.QCoreApplication.translate("CandleStickPlot",
                                             "Candlestick")
    def _plot(self, quotes):
        axes = self.parent.get_axes()
        matplotlib.finance.candlestick(axes, quotes, width=0.005)
        self.parent.chart_canvas.draw()

plot_widgets.append(CandleStick)


class DaySummary(_QuotePlot):
    name = QtCore.QCoreApplication.translate("DaySummaryPlot",
                                             "Day Summary")
    def _plot(self, quotes):
        axes = self.parent.get_axes()
        matplotlib.finance.plot_day_summary(axes, quotes)
        self.parent.chart_canvas.draw()

plot_widgets.append(DaySummary)

class VolumeOverlay(_QuotePlot):
    name = QtCore.QCoreApplication.translate("VolumeOverlay",
                                             "VolumeOVerlay")
    def _plot(self, quotes):
        axes = self.parent.get_axes()
        matplotlib.finance.volume_overlay3(axes, quotes)
        self.parent.chart_canvas.draw()

plot_widgets.append(VolumeOverlay)


class _DepthPlot(_PlotWidget):
    name = QtCore.QCoreApplication.translate("PeriodHighPlot",
                                             "period high price")

    def _request_data(self):
        exchange_name = self.parent.exchange_combo.currentText()
        self.proxy = tulpenmanie.data.DepthProxy(
            self.parent.market_uuid, exchange_name)

        self.proxy.refreshed_signal.connect(self._plot)
        self.proxy.refresh()


class DepthPlot(_DepthPlot):
    name = QtCore.QCoreApplication.translate("DepthPlot",
                                             "depth plot")
    def _plot(self, depth):
        axes = self.parent.get_axes()
        axes.contour(depth)
        self.parent.chart_canvas.draw()

plot_widgets.append(DepthPlot)


class OrderDialog(QtGui.QDialog):

    def __init__(self, parent=None, price=0.0, amount=0.0):
        super(OrderDialog, self).__init__(parent)

        label = QtGui.QLabel("This could be a cool order dialog")
        price_label = QtGui.QLabel("price %s" % price)
        amount_label = QtGui.QLabel("amount %s" % amount)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(price_label)
        layout.addWidget(amount_label)
        self.setLayout(layout)
"""
