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
        self.finished.connect(self.check_reply)

    def check_reply(self, reply):
        logger.debug("recieved %s", reply.url().toString())
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
