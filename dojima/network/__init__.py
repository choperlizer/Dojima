# Dojima, a markets client.
# Copyright (C) 2012-2013  Emery Hemingway
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

import heapq
import queue
import logging
import random
from PyQt4 import QtCore, QtNetwork


logger = logging.getLogger(__name__)

network_manager = None

def get_network_manager(parent=None):
    if not network_manager:
        global network_manager
        network_manager = NetworkAccessManager(parent)
    return network_manager


class HostRequestQueue(QtCore.QObject):
    """Queues requests for a host."""

    #pending_requests_signal = QtCore.pyqtSignal(int)

    def __init__(self, wait, parent=None):
        super(HostRequestQueue, self).__init__(parent)
        self.queue = queue.PriorityQueue()
        self.wait = wait
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.pop)
        self.timer.start(wait)

    def set_wait(self, wait):
        """Change the minimum interval between requests"""
        self.timer.setInterval(wait)
        self.wait = wait

    def enqueue(self, requester, priority=None):
        """Enqueue an object that wishes to request"""
        if not self.timer.isActive():
            self.timer.start(self.wait)
            requester.pop_request()
        else:
            if priority is None:
                priority = random.randint(4,16)
            self.queue.put((priority, requester))

    def pop(self):
        # TODO !!! if queue is empty and wait has elasped since the last
        # pop, pop immediatly
        """Pop an object that has a request queued and call pop_request()"""
        if self.queue.empty():
            self.timer.stop()
        else:
            requester = self.queue.get(False)[1]
            requester.pop_request()


class NetworkAccessManager(QtNetwork.QNetworkAccessManager):

    def __init__(self, parent=None):
        super(NetworkAccessManager, self).__init__(parent)
        self._host_request_queues = dict()

    def get_host_request_queue(self, hostname, wait):
        """return a queue that object can queue themselves into"""
        if hostname in self._host_request_queues:
            host_queue = self._host_request_queues[hostname]
            #TODO manager this wait time better
            host_queue.set_wait(wait)
        else:
            host_queue = HostRequestQueue(wait, self)
            self._host_request_queues[hostname] = host_queue
        return host_queue


class NetworkRequest(QtNetwork.QNetworkRequest):

    def __init__(self, url):
        super(NetworkRequest, self).__init__(url)
        # BAD hardcoding
        # TODO get this from QApplication
        self.setRawHeader("User-Agent", "dojima/0.7.0")


class ExchangeRequest(object):
    priority = 3
    host_priority = None

    def __init__(self, parent):
        self.parent = parent
        self.reply = None
        parent.requests.append( (self.priority, self,) )
        parent.host_queue.enqueue(self.parent, self.host_priority)

    def __del__(self):
        if self.reply:
            self.reply.deleteLater()

    def _prepare_request(self):
        self.request = NetworkRequest(self.url)
        self.request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                               "application/x-www-form-urlencoded")
        query = QtCore.QUrl()
        if self.params:
            for key, value in list(self.params['query'].items()):
                query.addQueryItem(key, value)
        self.query = query.encodedQuery()

    def _extract_reply(self):
        self.parent.replies.remove(self)
        if self.reply.error():
            logger.error(self.reply.errorString())
        else:
            if logger.isEnabledFor(logging.INFO):
                logger.info("received reply to %s", self.url.toString())
            raw_reply = bytearray(self.reply.readAll()).decode()
            self._handle_reply(raw_reply)

    def _handle_error(self, error):
        logger.error(error)
        #self.parent.exchange_error_signal.emit(msg)
        #logger.warning(msg)


class ExchangeGETRequest(ExchangeRequest):

    def send(self):
        self.request = NetworkRequest(self.url)
        if logger.isEnabledFor(logging.INFO):
            logger.info("GET to %s", self.url.toString())
        self.reply = self.parent.network_manager.get(self.request)
        self.reply.finished.connect(self._extract_reply)
        self.parent.replies.add(self)


class ExchangePOSTRequest(ExchangeRequest):

    def __init__(self, params, parent):
        self.parent = parent
        self.params = params
        self.reply = None
        parent.requests.append( (self.priority, self,) )
        parent.host_queue.enqueue(self.parent, self.host_priority)
    

    def send(self):
        self._prepare_request()
        if logger.isEnabledFor(logging.INFO):
            logger.info("POST to %s", self.url.toString())
        self.reply = self.parent.network_manager.post(self.request,
                                                      self.query)
        self.reply.finished.connect(self._extract_reply)
        self.parent.replies.add(self)
