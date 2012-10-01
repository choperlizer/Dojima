# Tulpenmanie, a graphical speculation platform.
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

import matplotlib.figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

import tulpenmanie.data

class Dialog(QtGui.QDialog):

    def __init__(self, market_uuid, parent):
        super(Dialog, self).__init__(parent)
        self.market_uuid = market_uuid
        self.exchanges = dict()

        self.menu_bar = QtGui.QMenuBar(self)
        self.plot_menu = QtGui.QMenu("plot", self.menu_bar)
        self.menu_bar.addMenu(self.plot_menu)

        # HARDCODING
        chart_canvas = ChartCanvas(self, width=5, height=4, dpi=100)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.menu_bar)
        layout.addWidget(chart_canvas)

        self.setLayout(layout)

class ChartCanvas(FigureCanvas):

    # HARDCODING
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        figure = matplotlib.figure.Figure(figsize=(width, height), dpi=dpi)
        # HARDCODING
        self.axes = figure.add_subplot(111)
        # this is so axes are cleared every time plot() is called
        self.axes.hold(False)

        FigureCanvas.__init__(self, figure)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.axes.xaxis_date()
        self.plot_order_price()

    def plot_order_price(self, exchange_name='MtGox'):
        array = tulpenmanie.data.get_trades(self.parent().market_uuid,
                                            exchange_name)
        self.axes.plot_date(array[0], array[1])
