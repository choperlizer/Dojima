# Dojima, a markets client.
# Copyright (C) 2012-2013 Emery Hemingway
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

# Actually most of this file came from http://btcchina.org/api-trade-documentation-en

import base64
import hashlib
import hmac
import http.client
import json
import logging
import re
import time

from decimal import Decimal

import numpy as np
from PyQt4 import QtCore, QtGui, QtNetwork

import dojima.exchange
import dojima.exchanges
import dojima.data.market
import dojima.data.offers
import dojima.network
import dojima.ui.wizard


PRETTY_NAME = "BTC China"
PLAIN_NAME = "btcchina"
MARKET_ID = 'BTCCNY'
HOSTNAME = 'btchina.com'

logger = logging.getLogger(PLAIN_NAME)

def saveAccountSettings(access_key, secret_key):
    settings = QtCore.QSettings()
    settings.beginGroup(PLAIN_NAME)
    settings.setValue('access_key', access_key)
    settings.setValue('secret_key', secret_key)

def loadAccountSettings():
    settings = QtCore.QSettings()
    settings.beginGroup(PLAIN_NAME)
    access_key = settings.value('access_key')
    secret_key = settings.value('secret_key')
    return access_key, secret_key

class BtcchinaExchangeProxy(dojima.exchange.ExchangeProxySingleMarket):

    id = PLAIN_NAME
    name = PRETTY_NAME
    local_market_map  = None
    remote_market_map = None
    base_id    = 'btcchina-BTC'
    counter_id = 'btcchina-CNY'

    def getExchangeObject(self):
        if self.exchange_object is None:
            self.exchange_object = BtcchinaExchange()
        return self.exchange_object

    def getPrettyMarketName(self, market_id):
        return 'BTCCNY'

    def getWizardPage(self, wizard):
        return BtcchinaWizardPage(wizard)

    
class BtcchinaWizardPage(dojima.ui.wizard.ExchangeWizardPage):
    name = PRETTY_NAME

    def initializePage(self):
        self.username_edit = QtGui.QLineEdit()
        self.password_edit = QtGui.QLineEdit(echoMode=QtGui.QLineEdit.Password)
        self.base_combo = QtGui.QComboBox()
        self.counter_combo = QtGui.QComboBox()

        new_local_button = QtGui.QPushButton(
            QtCore.QCoreApplication.translate(PLAIN_NAME, "New Commodity",
                                              "The label on the new "
                                              "commodity button in the "
                                              "new market wizard."))

        button_box = QtGui.QDialogButtonBox()
        button_box.addButton(new_local_button, button_box.ActionRole)

        layout = QtGui.QFormLayout()
        layout.addRow(QtCore.QCoreApplication.translate(PLAIN_NAME, "Access Key"), self.username_edit)
        layout.addRow(QtCore.QCoreApplication.translate(PLAIN_NAME, "Secret Key"), self.password_edit)
        layout.addRow(QtCore.QCoreApplication.translate(PLAIN_NAME, "Local Bitcoin Commodity"), self.base_combo)
        layout.addRow(QtCore.QCoreApplication.translate(PLAIN_NAME, "Local Renminbi Commodity"), self.counter_combo)
        layout.addRow(button_box)
        self.setLayout(layout)

        self.base_combo.setModel(dojima.model.commodities.local_model)
        self.counter_combo.setModel(dojima.model.commodities.local_model)

        self.username_edit.editingFinished.connect(self.checkCompleteState)
        self.password_edit.editingFinished.connect(self.checkCompleteState)

        new_local_button.clicked.connect(self.showNewCommodityDialog)
        self.username_edit.textChanged.connect(self.checkCompleteState)
        self.password_edit.textChanged.connect(self.checkCompleteState)
        self.base_combo.currentIndexChanged.connect(self.checkCompleteState)
        self.counter_combo.currentIndexChanged.connect(self.checkCompleteState)

        username, password = loadAccountSettings()
        if username:
            self.username_edit.setText(username)
        if password:
            self.password_edit.setText(password)

        self.checkCompleteState()

    def validatePage(self):
        saveAccountSettings(self.username_edit.text(), self.password_edit.text())

        local_base_id    = self.base_combo.itemData(self.base_combo.currentIndex(), QtCore.Qt.UserRole)
        local_counter_id = self.counter_combo.itemData(self.counter_combo.currentIndex(), QtCore.Qt.UserRole)

        dojima.model.commodities.remote_model.map('btcchina-BTC', local_base_id)
        dojima.model.commodities.remote_model.map('btcchina-CNY', local_counter_id)
        return dojima.model.commodities.remote_model.submit()

    
def _get_tonce(self):
    return int(time.time()*1000000)

def _get_params_hash(self,pdict):
    pstring=""
    # The order of params is critical for calculating a correct hash
    fields=['tonce','accesskey','requestmethod','id','method','params']
    for f in fields:
        if pdict[f]:
            if f == 'params':
                # Convert list to string, then strip brackets and spaces
                # probably a cleaner way to do this
                param_string=re.sub("[\[\] ]","",str(pdict[f]))
                param_string=re.sub("'",'',param_string)
                pstring+=f+'='+param_string+'&'
            else:
                pstring+=f+'='+str(pdict[f])+'&'
        else:
            pstring+=f+'=&'
    pstring=pstring.strip('&')
 
    # now with correctly ordered param string, calculate hash
    phash = hmac.new(self.secret_key, pstring, hashlib.sha1).hexdigest()
    return phash


class BtcchinaExchange(QtCore.QObject, dojima.exchange.ExchangeSingleMarket):
    valueType = Decimal

    accountChanged = QtCore.pyqtSignal(str)
    bitcoinDepositAddress = QtCore.pyqtSignal(str)
    bitcoinDepositAddressExpiry = QtCore.pyqtSignal(str)
    bitcoinWithdrawalReply = QtCore.pyqtSignal(str)
    exchange_error_signal = QtCore.pyqtSignal(str)
    
    def __init__(self, network_manager=None, parent=None):
        if network_manager is None:
            network_manager = dojima.network.get_network_manager()
        super(BtcchinaExchange, self).__init__(parent)

        self.network_manager = network_manager
        self.host_queue = self.network_manager.get_host_request_queue(HOSTNAME, 500)
        self.requests = list()
        self.replies = set()
        self._access_key = None
        self._secret_key = None
        self._bitcoin_deposit_address = None

        self._ticker_refresh_rate = 16

        self.account_validity_proxies = dict()
        self.balance_proxies = dict()
        self.ticker_proxy = dojima.data.market.TickerProxyDecimal(self)
        self.depth_proxy = dojima.data.market.DepthProxy('BTCCNY', self)
        self.ticker_clients = 0
        self.ticker_timer = QtCore.QTimer(self)
        self.ticker_timer.timeout.connect(self.refreshTicker)

        self.account_validity_proxy = dojima.data.account.AccountValidityProxy(self)

        self.base_balance_proxy = dojima.data.balance.BalanceProxyDecimal(self)
        self.counter_balance_proxy = dojima.data.balance.BalanceProxyDecimal(self)

        self.offers_model = dojima.data.offers.Model()
        self.offer_proxy_asks = dojima.data.offers.FilterAsksModel(self.offers_model)
        self.offer_proxy_bids = dojima.data.offers.FilterBidsModel(self.offers_model)
                
        self.loadAccountCredentials()

    def hasAccount(self, market=None):
        return bool(self._access_key and self._secret_key)

    def loadAccountCredentials(self, market=None):
        access_key, secret_key = loadAccountSettings()
        if self._access_key != access_key or self._secret_key != secret_key:
            self._access_key = access_key
            self._secret_key = secret_key
            self.accountChanged.emit(MARKET_ID)

    def refreshTicker(self, market=None):
        BtcchinaTickerRequest(self)

    def refreshDepth(self, market=None):
        BtcchinaDepthRequest(self)

    def cancelOffer(self, order_id, market=None):
        BtcchinaCancelOrderRequest(params, self)
                
    def get_account_info(self,post_data={}):
        post_data['method']='getAccountInfo'
        post_data['params']=[]
        return self._private_request(post_data)
 
    def get_market_depth(self,post_data={}):
        post_data['method']='getMarketDepth'
        post_data['params']=[]
        return self._private_request(post_data)
 
    def buy(self,price,amount,post_data={}):
        post_data['method']='buyOrder'
        post_data['params']=[price,amount]
        return self._private_request(post_data)
 
    def sell(self,price,amount,post_data={}):
        post_data['method']='sellOrder'
        post_data['params']=[price,amount]
        return self._private_request(post_data)
 
    def cancel(self,order_id,post_data={}):
        post_data['method']='cancelOrder'
        post_data['params']=[order_id]
        return self._private_request(post_data)
 
    def request_withdrawal(self,currency,amount,post_data={}):
        post_data['method']='requestWithdrawal'
        post_data['params']=[currency,amount]
        return self._private_request(post_data)
 
    def get_deposits(self,currency='BTC',pending=True,post_data={}):
        post_data['method']='getDeposits'
        if pending:
            post_data['params']=[currency]
        else:
            post_data['params']=[currency,'false']
        return self._private_request(post_data)
 
    def get_orders(self,id=None,open_only=True,post_data={}):
        # this combines getOrder and getOrders
        if id is None:
            post_data['method']='getOrders'
            if open_only:
                post_data['params']=[]
            else:
                post_data['params']=['false']
        else:
            post_data['method']='getOrder'
            post_data['params']=[id]
        return self._private_request(post_data)
 
    def get_withdrawals(self,id='BTC',pending=True,post_data={}):
        # this combines getWithdrawal and getWithdrawls
        try:
            id = int(id)
            post_data['method']='getWithdrawal'
            post_data['params']=[id]
        except:
            post_data['method']='getWithdrawals'
            if pending:
                post_data['params']=[id]
            else:
                post_data['params']=[id,'false']
        return self._private_request(post_data)

    
class _BtcchinaRequest(dojima.network.ExchangeGETRequest):
    priority = 3
    host_priority = None
    
    
class BtcchinaTickerRequest(_BtcchinaRequest):
    url = QtCore.QUrl("https://data.btcchina.com/data/ticker")
    
    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)

        data = data['ticker']
        self.parent.ticker_proxy.last_signal.emit(Decimal(data['last']))
        self.parent.ticker_proxy.ask_signal.emit(Decimal(data['sell']))
        self.parent.ticker_proxy.bid_signal.emit(Decimal(data['buy']))

        
class BtcchinaDepthRequest(_BtcchinaRequest):
    url = QtCore.QUrl("https://data.btcchina.com/data/orderbook")

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw)

        bids = data ['bids']
        bids = np.array(bids, dtype=np.float).transpose()
        self.parent.depth_proxy.processBids(bids)

        asks = data ['asks']
        asks = np.array(asks, dtype=np.float).transpose()
        self.parent.depth_proxy.processAsks(asks)
                
    
class _BtcchinaPrivateRequest(dojima.network.ExchangePOSTRequest):
    priority = 1
    host_priority = 0
    url = QtCore.QUrl('https://api.btcchina.com/api_trade_v1.php')

    
    def _prepare_request(self):
        self.request = QtNetwork.QNetworkRequest(self.url)
        self.request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                               "application/x-www-form-urlencoded")

        #fill in common post_data parameters
        tonce=self._get_tonce()
        params = {'tonce': tonce,
                  'accesskey': self.access_key,
                  'requestmethod': 'post',
                  'method': self.method}

        if self.params:
            params.update(self.params)
                  
        # If ID is not passed as a key of post_data, just use tonce
        if not 'id' in params:
            params['id']=tonce

        self.query = urllib.parse.urlencode(params)
 
        pd_hash=_get_params_hash(params)
 
        # must use b64 encode        
        auth_string='Basic '+base64.b64encode(self.access_key+':'+pd_hash)
        self.request.setRawHeader('Authorization', auth_string)
        self.request.setRawHeader('Json-Rpc-Tonce', tonce)

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, parse_float=Decimal, parse_int=Decimal)
        if 'result' in data:
            self.handle_reply(data['result'])
            return

        if 'error' in data:
            logger.error("%s: %s", data['error'], self.query)
            return
                    
        # not great error handling....
        print("status:",response.status)
        print("reason:".response.reason)

        
class BtcchinaCancelOrderRequest(_BtcchinaPrivateRequest):
    method = 'cancelOrder'
    priority = 0

    def _handle_reply(self, raw):
        logger.debug(raw)
        data = json.loads(raw, parse_float=Decimal, parse_int=Decimal)

        order_id =data['order_id']
        seach = self.parent.offers_model.findItems(order_id)
        for item in search:
            self.parent.offers_model.removeRow(item.row())
        
    
def parse_markets():
    if PLAIN_NAME in dojima.exchanges.container: return
    exchange_proxy = BtcchinaExchangeProxy()
    dojima.exchanges.container.addExchange(exchange_proxy)

parse_markets()
