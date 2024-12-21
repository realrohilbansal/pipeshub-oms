from enum import Enum
import time

class RequestType(Enum):
    Unknown = 0
    New = 1
    Modify = 2
    Cancel = 3

class ResponseType(Enum):
    Unknown = 0
    Accept = 1
    Reject = 2

class OrderRequest:
    """
    Represents an order request to be sent to the exchange
    """
    def __init__(self, m_symbolId, m_price, m_qty, m_side, m_orderId, request_type=RequestType.New):
        self.m_symbolId = m_symbolId
        self.m_price = m_price
        self.m_qty = m_qty
        self.m_side = m_side
        self.m_orderId = m_orderId
        self.request_type = request_type
        self.timestamp = time.time()

class OrderResponse:
    """
    Represents a response from the exchange to an order request
    """
    def __init__(self, m_orderId, m_responseType):
        self.m_orderId = m_orderId
        self.m_responseType = m_responseType
