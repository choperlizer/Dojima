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

import heapq
import Queue
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
        self.queue = Queue.PriorityQueue()
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
        self.setRawHeader("User-Agent", "tulpenmanie/0.5.0")
