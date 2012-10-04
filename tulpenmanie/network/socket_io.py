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

import json
import logging

from PyQt4 import QtCore, QtNetwork
from ws4py.client.threadedclient import WebSocketClient


# TODO don't let the user try to connect to two different hosts
# over the same socket client


logger = logging.get_logger(__name__)


class SocketIOClient(QtCore.QObject):

    _states = ('connecting', 'connected', 'disconnecting', 'disconnected')

    on_message = QtCore.pyqtSignal(list)
    on_json_message = QtCore.pyqtSignal(list)
    on_event = QtCore.pyqtSignal(list)
    on_error = QtCore.pyqtSignal(list)

    def __init__(self, network_manager=None, parent=None):
        super(SocketIOClient, self).__init__(parent=None)
        if network_manager is None:
            self.network_manager = tulpenmanie.network.get_network_manager()
        else:
            self.network_manager = network_manager
        self._state = 3
        self.namespaces = {'': self}
        self.endpoint_queue = list()
        self.heartbeat_timer = QtCore.QTimer(self)
        self.heartbeat_timer.timeout.connect(self._emit_heartbeat)

    @property
    def state(self):
        return self._states[self._state]

    def connect(self, url):
        self._state = 0
        #TODO decide what to do about SSL
        endpoint = url.path()
        query = str(url.toString()).partition('?')[2]
        if self.namespace._state != 1:
            self.namespace_queue.append((endpoint, query))
            self._send_handshake(url)
            return
        else:
            if endpoint not in self.endpoints:
                namespace = EndpointNameSpace(endpoint, self)
            else:
                namespace = self.endpoints[endpoint]
            if namespace._state > 1:
                self._emit_connect(endpoint, query)

    def _send_handshake(self, url):
        self.host = url.host()
        url.setPath('/socket.io/1')
        # TODO might need to strip query arguments
        # TODO this request should have a User-Agent,
        # there is a overidden request class for that in network/__init__.py
        request = QtNetwork.QNetworkRequest(url)
        self.reply = self.network_manager.get(request)
        self.reply.finished.connect(self._receive_handshake)

    def _receive_handshake(self):
        if self.reply.error():
            logger.error(self.reply.errorString())
            self._state = 3
            self.reply.deleteLater()
            return
        handshake = str(self.reply.readAll()).split(':')
        self.session_id = handshake[0]
        self.heartbeat_interval = int(handshake) * 750
        self.close_timeount = handshake[2]
        transports = handshake[3].split(',')
        if 'websocket' not in transports:
            self.error("Websocket is not a supported transport for %s",
                       self.reply.url.toString())
            return
        self._connect_websocket_transport(self.session_id)
        self.reply.deleteLater()

    def _connect_websocket_transport(self, session_id):
        url = 'wss://{}/socket.io/1/websocket/{}'.format(self.host, session_id)
        self.transport = WebSocketTransport(url)
        self.transport.connected_signal.connect(self._set_transport_state)
        self.transport.message_signal.connect(self._handle_message)
        self.transport.connect()

    def disconnect(self):
        self._state = 2
        #self.transport.close()

    def _set_transport_state(self, state):
        if state:
            self._state = 1
            self.heartbeat_timer.start(self.heartbeat_interval)
            while self.endpoint_queue:
                path, query = endpoint_queue.pop()
                self._emit_connect(path, query)
        else:
            self.heartbeat_timer.stop
            self._state = 3

    def _handle_message(self, message):
        message = message.split(':', 3)
        code = message[0]
        handler = self.message_handlers[code]
        handler(message)

    def _disconnect_(self, message):
        logger.info("received disconnect message from %s", self.host)
        self._state = 2
        self.transport.close()

    def _connect_(self, message):
        logger.debug("recieved connect echo from %s", self.host)

    def _heartbeat_(self, message):
        pass

    def _message_(self, message):
        namespace = self.namespaces[message[2]]
        namespace.on_message.emit(message[3])
        for index, part in enumerate(message):
            logger.info("message part %: %s", index, part)

    def _json_message_(self, message):
        namespace = self.namespaces[message[2]]
        namespace.on_json_message.emit(message[3])
        for index, part in enumerate(message):
            logger.info("json message part %: %s", index, part)

    def _event_(self, message):
        namespace = self.namespaces[message[2]]
        namespace.on_event.emit(message[3])
        for index, part in enumerate(message):
            logger.info("event part %: %s", index, part)

    def _ack_(self, message):
        """Could be used to verify that something was received """
        pass

    def _error_(self, message):
        namespace = self.namespaces[message[2]]
        namespace.on_error.emit(message[3])
        logger.error("[%s][%s] %s", self.host, message[2], message[3])

    def _noop_(self, message):
        pass

    message_handlers = (_disconnect_, _connect_, _heartbeat_, _message_,
                        _json_message_, _event_, _ack_, _error_, _noop_)

    def _emit_connect(self, endpoint, query=None):
        if query:
            endpoint += '?' + query
        payload = (1, '', endpoint)
        self.transport.send(':'.join(payload))

    def _emit_heartbeat(self):
        self.transport.send('2')

    def emit_message(self, message, endpoint=''):
        payload = (3, '', endpoint, message)
        self.transport.send(':'.join(payload))

    def emit_json_message(self, message, endpoint=''):
        payload = (4, '', endpoint, json.dumps(message))
        self.transport.send(':'.join(payload))

    def emit_event(self, message, endpoint=''):
        """
        An event is like a json message,
        but has mandatory name and args fields.
        name is a string and args an array.
        """
        assert name in message
        assert args in message
        payload = (5, '', endpoint, json.dumps(message))
        self.transport.send(':'.join(payload))


class EndpointNameSpace(QtCore.QObject):

    _states = ('connecting', 'connected', 'disconnecting', 'disconnected')

    on_message = QtCore.pyqtSignal(list)
    on_json_message = QtCore.pyqtSignal(list)
    on_event = QtCore.pyqtSignal(list)
    on_error = QtCore.pyqtSignal(list)

    def __init__(self, endpoint, parent=None):
        super(EndpointNameSpace, self).__init__(parent=None)
        self.endpoint = endpoint
        self._state = 3

    @property
    def state(self):
        return self._states[self.state]

    def emit_message(self, message):
        payload = (3, '', self.endpoint, message)
        self.parent.transport.send(':'.join(payload))

    def emit_json_message(self, message):
        payload = (4, '', self.endpoint, json.dumps(message))
        self.parent.transport.send(':'.join(payload))

    def emit_event(self, message):
        """
        An event is like a json message, but has mandatory name
        and args fields. name is a string and args an array.
        """
        assert name in message
        assert args in message
        payload = (5, '', self.endpoint, json.dumps(message))
        self.parent.transport.send(':'.join(payload))


class WebSocketTransport(QtCore.QObject, WebSocketClient):

    logger = logging.getLogger('WebsocketTransport')
    connected_signal = QtCore.pyqtSignal(bool)
    message_signal = QtCore.pyqtSignal(str)

    #TODO Defined Status Codes http://tools.ietf.org/html/rfc6455#section-7.4.1

    def __init__(self, url, protocols=None, extensions=None, parent=None):
        super(WebSocketTransport, self).__init__(parent)
        WebSocketBaseClient.__init__(self, url, protocols, extensions)

    def opened(self):
        self.logger.info("connected to %s", self.url)
        self.connected_signal.emit(True)

    def closed(self, code, reason=None):
        self.logger.info("%s closed %s %s", self.url, code, reason)
        self.connected_signal.emit(False)

    def recieved_message(self, message):
        self.logger.debug(message)
        self.message_signal.emit(message)
