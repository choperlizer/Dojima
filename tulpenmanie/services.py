from decimal import Decimal

from PyQt4 import QtCore, QtNetwork

exchanges = []
exchange_accounts = []
account_models = []


def register_exchange(exchange_class):
	exchanges.append(exchange_class)

def register_exchange_account(account_class):
    exchange_accounts.append(account_class)

def register_account_model(model_class):
    account_models.append(model_class)


class BaseExchangeMarket(QtCore.QObject):

    def __init__(self, parent):
        super(BaseExchangeMarket, self).__init__(parent)

    def refresh(self):
        #TODO log request
        request = QtNetwork.QNetworkRequest(self._refresh_url)
        request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader,
                          "application/x-www-form-urlencoded")
        self._request_queue.enqueue(request, self._refresh_url.encodedQuery())
