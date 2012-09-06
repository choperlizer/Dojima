# Tuplenmanie, a commodities market client.
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

import heapq
import Queue
import logging
from PyQt4 import QtCore, QtNetwork


logger = logging.getLogger(__name__)


class HostRequestQueue(QtCore.QObject):
    """Queues requests for a host."""

    #pending_requests_signal = QtCore.pyqtSignal(int)

    def __init__(self, wait, parent=None):
        super(HostRequestQueue, self).__init__(parent)
        #self.queue = Queue.PriorityQueue()
        self.queue = Queue.Queue()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.pop)
        self.timer.start(wait)

    def set_wait(self, wait):
        self.timer.setInterval(wait)

    def enqueue(self, requester):
        self.queue.put(requester)

    def pop(self):
        if self.queue.empty():
            return
        requester = self.queue.get(False)
        requester.pop_request()


class NetworkAccessManager(QtNetwork.QNetworkAccessManager):

    def __init__(self, parent=None):
        super(NetworkAccessManager, self).__init__(parent)
        self._host_request_queues = dict()
        #self.finished.connect(self.check_reply)

    def check_reply(self, reply):
        if reply.error():
            logger.error("%s - %s", reply.url().toString(), reply.errorString())
            reply.deleteLater()

    def get_host_request_queue(self, hostname, wait):
        if hostname in self._host_request_queues:
            host_queue = self._host_request_queues[hostname]
            #TODO manager this wait time better
            host_queue.set_wait(wait)
        else:
            host_queue = HostRequestQueue(wait, self)
            self._host_request_queues[hostname] = host_queue
        return host_queue
