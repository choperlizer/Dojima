from PyQt4 import QtCore, QtGui

class OrdersModel(QtGui.QStandardItemModel):

    # TODO set prefixes and suffixes
    # TODO data should be read-only
    
    COLUMNS = 3
    ORDER_ID, PRICE, AMOUNT = range(COLUMNS)

    def __init__(self, parent=None):
        super(OrdersModel, self).__init__(parent)

    def append_order(self, order_id, price, amount):
        self.appendRow( (QtGui.QStandardItem(str(order_id)),
                         QtGui.QStandardItem(str(price)),
                         QtGui.QStandardItem(str(amount)) ) )

    def clear_orders(self):
        self.removeRows(0, self.rowCount())
