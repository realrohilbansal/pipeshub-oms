from collections import deque
import os, sys

cwd = os.getcwd()
if cwd.endswith("scripts"):
    os.chdir("..")
sys.path.append(os.getcwd())

from scripts.order import RequestType

class OrderQueue:
    """
    Represents the order queue
    """
    def __init__(self):
        self.orders = {}
        self.queue = deque()

    def __len__(self):
        """
        Returns the number of orders in the queue.
        """
        return len(self.queue)

    def handle_request(self, order_request):
        """
        Handles an order request
        """
        if order_request.m_orderId in self.orders:
            if order_request.request_type == RequestType.Modify:
                self.modify_order(order_request)
            elif order_request.request_type == RequestType.Cancel:
                self.cancel_order(order_request)
        else:
            self.add_order(order_request)

    def add_order(self, order_request):
        """
        for new requests, add them to the queue and dict
        
        params:
            order_request: the order request to add
        """
        self.queue.append(order_request)
        self.orders[order_request.m_orderId] = order_request
        print(f"Order {order_request.m_orderId} added to queue.")

    def modify_order(self, modify_request):
        """
        modify an order in the queue through the dict
        
        params:
            modify_request: the modify request to process
        """
        order = self.orders[modify_request.m_orderId]
        order.m_price = modify_request.m_price
        order.m_qty = modify_request.m_qty
        print(f"Order {modify_request.m_orderId} modified.")

    def cancel_order(self, cancel_request):
        """
        cancel an order in the queue and the dict
        
        params:
            cancel_request: the cancel request to process
        """
        if cancel_request.m_orderId in self.orders:
            self.queue.remove(self.orders[cancel_request.m_orderId])
            del self.orders[cancel_request.m_orderId]
            print(f"Order {cancel_request.m_orderId} canceled.")
