# -*- coding: utf-8 -*-
# Dojima, a markets client.
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
# GNU General Public Licnense for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

import otapi
from PyQt4 import QtCore


logger = logging.getLogger(__name__)


class CurrencyContract(object):

    def __init__(self, assetTypeId):
        self.id = assetTypeId

        # TODO find a signing nym and verify the contract
        #self.xml = otapi.OTAPI_Basic_VerifyAndRetrieveXMLContents(
        #    assetTypeId, dojima.ot.getSigningNym())

        self.contract = otapi.OTAPI_Basic_GetAssetType_Contract(assetTypeId)

        self.name = None
        self.tla = None
        self.symbol = None
        self.type = None
        self.factor = None
        self.decimal_power = None
        self.fraction = None

    def getName(self):
        if self.name is None:
            self.parseContractXml()
        return self.name

    def getTLA(self):
        if self.tla is None:
            self.parseContractXml()
        return self.tla

    def getSymbol(self):
        if self.symbol is None:
            self.parseContractXml()
        return self.symbol

    def getFactor(self):
        if self.factor is None:
            self.parseContractXml()
        return self.factor

    def getPower(self):
        # TODO reconcile what is power and decimal_power
        if self.decimal_power is None:
            self.parseContractXml()
        return self.decimal_power

    def parseContractXml(self):
        start = self.contract.index('<')
        end = self.contract.rindex('>')
        reader = QtCore.QXmlStreamReader(self.contract[start:end])

        while not reader.atEnd():
            if reader.isStartElement():
                if reader.name() == 'currency':
                    # TODO do a setattr on these things, and then let whatever
                    # looks at this thing do hasattrs or something else
                    a = reader.attributes()
                    self.name =  a.value('name')
                    self.tla =  a.value('tla')
                    self.symbol = a.value('symbol')
                    self.type = a.value('decimal')
                    self.factor = int(a.value('factor'))
                    self.decimal_power = int(a.value('decimal_power'))
                    self.faction = a.value('fraction')
                    return

            reader.readNext()
