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
import time

import matplotlib.dates
import numpy as np
from PyQt4 import QtCore, QtGui

import dojima.exchange


logger = logging.getLogger(__name__)


class TickerProxy(QtCore.QObject):

    ask_signal = QtCore.pyqtSignal(int)
    last_signal = QtCore.pyqtSignal(int)
    bid_signal = QtCore.pyqtSignal(int)


class _StatsProxy(QtCore.QObject):

    refreshed = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, exchangeObj, marketId, parent=None):
        super(_StatsProxy, self).__init__(parent)
        self.exchange_obj = exchangeObj
        self.market_id = marketId


class DepthProxy(_StatsProxy):

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


"""
class QuotesProxy(QtCore.QObject):

    refreshed_signal = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, exchange_obj, marketId, granularity=1200, parent=None):
        super(QuotesProxy, self).__init__(parent)
        self.exchange_obj = exchangeObj
        self.market_id = marketId
        self.granularity = granularity

    def refresh(self):
        self.exchange_obj.refreshTrades(self.market_id)

    def processTrades(self, epochs, prices, amounts):
        dates = matplotlib.dates.epoch2num(epochs)
        trades

        epochs = np.array(trade_data[0], dtype=np.int32)
        prices = np.array(trade_data[1], dtype=np.float)
        amounts = np.array(trade_data[2], dtype=np.float)

        #epochs.dump('/tmp/epochs')
        #prices.dump('/tmp/prices')
        #amounts.dump('/tmp/amounts')

        dates = list()
        opens = list()
        closes = list()
        highs = list()
        lows = list()
        volumes = list()

        period_start = epochs[0]
        period_end = period_start + self.granularity
        stop = epochs[-1]
        while period_start < stop:
            remaining_index = epochs >= period_start
            epochs = epochs[remaining_index]
            prices = prices[remaining_index]
            amounts = amounts[remaining_index]

            trim_index = epochs < period_end
            if trim_index.any():
                price_selection = prices[trim_index]
                amount_selection = amounts[trim_index]
                dates.append(matplotlib.dates.epoch2num(period_start))
                opens.append(price_selection[0])
                closes.append(price_selection[-1])
                highs.append(price_selection.max())
                lows.append(price_selection.min())
                volumes.append(amount_selection.sum())
            else:
                dates.append(matplotlib.dates.epoch2num(period_start))
                last_price = closes[-1]
                opens.append(last_price)
                closes.append(last_price)
                highs.append(last_price)
                lows.append(last_price)
                volumes.append(0)

            period_start = period_end
            period_end += self.granularity

        # Matplotlib likes this array the other way around,
        # so it gets transposed()
        self.quotes = np.array((dates,
                                opens, closes,
                                highs, lows,
                                volumes), dtype=np.float).transpose()
        self.save()
        self.refreshed_signal.emit(self.quotes)

    def save(self):
        directory = os.path.dirname(self.array_filename)
        if not os.path.exists(directory):
            os.makedir(directory)
        self.quotes.dump(self.array_filename)


        class QuotesProxy(QtCore.QObject):

    refreshed_signal = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, market_uuid, exchange_name,
                 granularity=1200, parent=None):
        super(QuotesProxy, self).__init__(parent)
        storage_directory = str(QtGui.QDesktopServices.storageLocation(
            QtGui.QDesktopServices.DataLocation))

        self.filename = os.path.join(
            storage_directory, '{}_{}_quotes.pickle'.format(market_uuid,
                                                                 exchange_name))
        if os.path.exists(self.array_filename):
            self.quotes = np.load(self.array_filename)
        else:
            self.quotes = None

        self.granularity = granularity
        self.exchange = dojima.exchange.get_exchange_object(exchange_name,
                                                                 market_uuid)
        self.exchange.trades_signal.connect(self._process_trades)

    def refresh(self):
        #if self.quotes is not None and self.quotes.any():
            #self.refreshed_signal.emit(self.quotes)
            #else:

        self.exchange.refresh_trade_data()

    def _process_trades(self, trade_data):
        "Trade data should be (dates, prices, amounts)"
        epochs = np.array(trade_data[0], dtype=np.int32)
        prices = np.array(trade_data[1], dtype=np.float)
        amounts = np.array(trade_data[2], dtype=np.float)

        #epochs.dump('/tmp/epochs')
        #prices.dump('/tmp/prices')
        #amounts.dump('/tmp/amounts')

        dates = list()
        opens = list()
        closes = list()
        highs = list()
        lows = list()
        volumes = list()

        period_start = epochs[0]
        period_end = period_start + self.granularity
        stop = epochs[-1]
        while period_start < stop:
            remaining_index = epochs >= period_start
            epochs = epochs[remaining_index]
            prices = prices[remaining_index]
            amounts = amounts[remaining_index]

            trim_index = epochs < period_end
            if trim_index.any():
                price_selection = prices[trim_index]
                amount_selection = amounts[trim_index]
                dates.append(matplotlib.dates.epoch2num(period_start))
                opens.append(price_selection[0])
                closes.append(price_selection[-1])
                highs.append(price_selection.max())
                lows.append(price_selection.min())
                volumes.append(amount_selection.sum())
            else:
                dates.append(matplotlib.dates.epoch2num(period_start))
                last_price = closes[-1]
                opens.append(last_price)
                closes.append(last_price)
                highs.append(last_price)
                lows.append(last_price)
                volumes.append(0)

            period_start = period_end
            period_end += self.granularity

        # Matplotlib likes this array the other way around,
        # so it gets transposed()
        self.quotes = np.array((dates,
                                opens, closes,
                                highs, lows,
                                volumes), dtype=np.float).transpose()
        self.save()
        self.refreshed_signal.emit(self.quotes)

    def save(self):
        directory = os.path.dirname(self.array_filename)
        if not os.path.exists(directory):
            os.makedir(directory)
        self.quotes.dump(self.array_filename)
"""

class TradesProxy(_StatsProxy):

    refreshed = QtCore.pyqtSignal(np.ndarray)

    def reload(self):
        # TODO this is a temporary method, remove it when fetching market data works
        self.exchange_obj.readTrades()

    def refresh(self):
        self.exchange_obj.refreshTrades(self.market_id)

    def processTrades(self, epochs, prices, amounts):
        dates = matplotlib.dates.epoch2num(epochs)
        # this needs to be float because unless time is rounded to the day, dates is a float
        trades = np.array((dates, prices), dtype=np.float32).transpose()
        return trades
