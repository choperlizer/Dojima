import logging
from Queue import Queue, PriorityQueue
from PyQt4 import QtCore, QtNetwork

logger = logging.getLogger(__name__)


class HostRequestQueue(QtCore.QObject):

    """This class was intended to only be instantiated by a network manager."""
    pending_requests_signal = QtCore.pyqtSignal(int)

    #TODO optionally make two queues, rather than turn proritization off
    def __init__(self, wait, prioritize, parent):
        super(HostRequestQueue, self).__init__(parent)
        if prioritize is True:
            self.queue = PriorityQueue()
        else:
            self.queue = Queue()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.pop_and_request)
        self.timer.start(wait)
        self.network_manager = parent

    def set_wait(self, wait):
        self.timer.setInterval(wait)

    def enqueue(self, request, data, priority=1):
        self.queue.put( (priority, request, data) )
        self.pending_requests_signal.emit(self.queue.qsize())

    def pop_and_request(self):
        if self.queue.empty():
            return
        items =self.queue.get(False)
        request = items[1]
        data = items[2]

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("requesting %s", request.url().toString())
        self.network_manager.post(request, data)
        self.pending_requests_signal.emit(self.queue.qsize())

class NetworkAccessManager(QtNetwork.QNetworkAccessManager):

    def __init__(self, parent=None):
        super(NetworkAccessManager, self).__init__(parent)
        self._reply_endpoints = dict()
        self._host_queues = dict()
        self.finished.connect(self.process)

    def host_queue(self, hostname, wait, prioritize=True):
        """Returns a queue object to append requests and data to."""
        if hostname in self._host_queues:
            queue = self._host_queues[hostname]
            logger.debug("%s request queue created", hostname)
            queue.set_wait(wait)
        else:
            queue = HostRequestQueue(wait, prioritize, self)
            self._host_queues[hostname] = queue
        return queue

    def register_reply_handler(self, url, handler):
        url = str(url.toString())
        if url in self._reply_endpoints:
            self._reply_endpoints[url].append(handler)
        else:
            self._reply_endpoints[url] = [ handler ]

    def process(self, reply):
        url = str(reply.url().toString())
        for handler in self._reply_endpoints[url]:
            if handler is not None:
                handler(reply)
