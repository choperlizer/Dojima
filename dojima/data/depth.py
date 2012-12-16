# Dōjima, a commodities market client.
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

import matplotlib.dates
import numpy as np
from PyQt4 import QtCore, QtGui

import dojima.exchange


#logger = logging.getLogger(__name__)


class DepthProxy(QtCore.QObject):

    refreshed = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, exchangeObj, marketId, parent=None):
        super(DepthProxy, self).__init__(parent)
        self.exchange_obj = exchangeObj
        self.market_id = marketId

    def reload(self):
        # TODO this is a temporary method, remove it when fetching the market offers works
        self.exchange_obj.readDepth()

    def refresh(self):
        self.exchange_obj.refreshDepth(self.market_id)

    def processDepth(self, asks, bids):
        "depth data should be asks(prices, amounts), bids(prices, amounts)"
        times = list()
        price_steps = list()
        volume_sums = list()
        #step_size = 1.0 / pow(10, self.precision)
        now = time.time()
        now = matplotlib.dates.epoch2num(now)

        #bids
        print bids
        bids = np.array(bids, dtype=np.float).transpose()
        if not bids: return None
        bid_prices = bids[0]
        bid_volumes = bids[1]
        floor = bid_prices.max()#.round(self.precision)
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
        asks = np.array(asks, dtype=np.float).transpose()
        if not asks: return None
        ask_prices = asks[0]
        ask_volumes = bids[1]
        ceiling = ask_prices.min()#.round(self.precision)
        top = ask_prices.max()

        while ceiling < top:
            ceiling += step_size
            index = ask_prices < ceiling

            times.append(now)
            price_steps.append(ceiling)
            volume_sums.append(ask_volumes[index].sum())

        self.depth = np.array((times, price_steps, volume_sums)).transpose()
        self.refreshed.emit(self.depth)
