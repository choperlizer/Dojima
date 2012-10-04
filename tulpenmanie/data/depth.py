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

import logging
import os
import os.path
import time

import numpy as np
from PyQt4 import QtCore, QtGui

import tulpenmanie.exchange


logger = logging.getLogger(__name__)


class DepthProxy(QtCore.QObject):

    refreshed_signal = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, market_uuid, exchange_name,
                 precision=2, parent=None):
        super(DepthProxy, self).__init__(parent)
        self.storage_directory = str(QtGui.QDesktopServices.storageLocation(
            QtGui.QDesktopServices.DataLocation))

        self.precision = precision
        self.exchange = tulpenmanie.exchange.get_exchange_object(exchange_name,
                                                                 market_uuid)
        self.exchange.depth_signal.connect(self._process_depth)

    def get_array_filename(self):
        array_filename = os.path.join(
            self.storage_directory, '{}_{}_{}_depth.pickle'.format(market_uuid,
                                                                   exchange_name,
                                                                   int(time.time())))

        return array_filename

    def refresh(self):
        #if self.depth is not None and self.depth.any():
        #    self.refreshed_signal.emit(self.depth)
        #else:
        self.exchange.refresh_depth_data()

    def _process_depth(self, depth_data):
        "depth data should be (asks(prices, amounts), bids(prices, amounts))"
        times = list()
        price_steps = list()
        volume_sums = list()
        step_size = 1.0 / pow(10, self.precision)
        now = time.time()
        now = matplotlib.dates.epoch2num(now)

        #bids
        bids = np.array(depth_data[1], dtype=np.float).transpose()
        bid_prices = bids[0]
        bid_volumes = bids[1]
        floor = bid_prices.max().round(self.precision)
        bottom = bid_prices.min()

        while floor > bottom:
            floor -= step_size
            index = bid_prices > floor

            times.append(now)
            price_steps.append(floor)
            volume_sums.append(bid_volumes[index].sum())

        price_steps.reverse()
        volume_sums.reverse()

        # asks
        asks = np.array(depth_data[0], dtype=np.float).transpose()
        ask_prices = asks[0]
        ask_volumes = bids[1]
        ceiling = ask_prices.min().round(self.precision)
        top = ask_prices.max()

        while ceiling < top:
            ceiling += step_size
            index = ask_prices < ceiling

            times.append(now)
            price_steps.append(ceiling)
            volume_sums.append(ask_volumes[index].sum())

        self.depth = np.array((times, price_steps, volume_sums)).transpose()
        self.save()
        self.refreshed_signal.emit(self.depth)

    def save(self):
        array_filename = self.get_array_filename()
        directory = os.path.dirname(array_filename)
        if not os.path.exists(directory):
            os.makedir(directory)
        self.depth.dump(self.get_array_filename)
        logger.debug("saved depth data to %s", array_filename)
