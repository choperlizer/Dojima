# -*- coding: utf-8 -*-
# Tulpenmanie, a markets client.
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
        self.contract = otapi.OT_API_GetAssetType_Contract(self.id)

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

    def getDecimalPower(self):
        if self.decimal_power is None:
            self.parseContractXml()
        return self.decimal_power

    def parseContractXml(self):
        contract = QtCore.QString(self.contract)
        start = contract.indexOf('<')
        end = contract.lastIndexOf('>')
        reader = QtCore.QXmlStreamReader(contract[start:end])

        while not reader.atEnd():
            if reader.isStartElement():
                if reader.name() == 'currency':
                    # TODO do a setattr on these things, and then let whatever
                    # looks at this thing do hasattrs or something else
                    a = reader.attributes()
                    self.name =  a.value('name').toString()
                    self.tla =  a.value('tla').toString()
                    self.symbol = a.value('symbol').toString()
                    self.type = a.value('decimal').toString()
                    self.factor = int(a.value('factor').toString())
                    self.decimal_power = int(a.value('decimal_power').toString())
                    self.faction = a.value('fraction').toString()
                    return

            reader.readNext()
