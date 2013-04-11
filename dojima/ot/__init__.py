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

import otapi
from PyQt4 import QtCore


class _OTRequestThread(QtCore.QThread):

    objEasy = otapi.OTMadeEasy()

    def __init__(self, parent=None):
        super(_OTRequestThread, self).__init__(parent)

        self.mutex = QtCore.QMutex()
        self.requestAdded = QtCore.QWaitCondition()
        self.requests = list()

        self.start()

    def __del__(self):
        self.mutex.lock()
        while self.requests:
            request = self.requests.pop(0)
            del request
        self.requests.append(None)
        self.requestAdded.wakeOne()

        self.wait()
        otapi.OTAPI_Basic_AppShutdown()

    def addRequest(self, requestObject):
        locker = QtCore.QMutexLocker(self.mutex)
        self.requests.append( (requestObject.priority, requestObject,) )
        self.requestAdded.wakeOne()

    def run(self):
        otapi.OTAPI_Basic_AppStartup()
        otapi.OTAPI_Basic_Init()
        otapi.OTAPI_Basic_LoadWallet()

        while True:
            self.mutex.lock()
            if len(self.requests) == 0:
                self.requestAdded.wait(self.mutex)

            request = heapq.heappop(self.requests)[1]
            self.mutex.unlock()

            request.exec_(self.objEasy)
            request.deleteLater()


class OpenTxsAccessManager(QtCore.QObject):

    thread = _OTRequestThread()

    def __init__(self, parent=None):
        super(OpenTxsAccessManager, self).__init__(parent)

    def request(self, requestObject):
        #print "queuing", requestObject.priority, requestObject
        #self.queueRequest.emit( (requestObject.priority, requestObject,) )
        #return requestObject.getReply()

        self.thread.addRequest(requestObject)
