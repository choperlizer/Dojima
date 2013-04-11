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

import multiprocessing

#import otapi
from PyQt4 import QtCore


def process_requests(queue):
    objEasy = otapi.OTMadeEasy()
    
    while True:
        request_tulpe = queue.get()
        if request_tuple is None: break
        method = getattr(objEasy, request_tuple[0])


class OTServerRequestManager(QtCore.QObject):

    request_queue = multiprocessing.Queue()
    pool = multiprocessing.Pool(processes=1)
        
    def __init__(self, parent=None):
        super(OTServerRequestManager, self).__init__(parent)
        ot_process = multiprocessing.Process(target=process_requests, args=(self.request_queue,))
        ot_process.start()

    def send(self, requestObject):
        self.request_queue.put(requestObject)
