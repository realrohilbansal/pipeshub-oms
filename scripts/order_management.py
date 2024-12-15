from datetime import datetime

import os, sys

cwd = os.getcwd()
if cwd.endswith("scripts"):
    os.chdir("..")
sys.path.append(os.getcwd())

from scripts.order_queue import OrderQueue
from scripts.order_processor import OrderProcessor
from scripts.response_handler import ResponseHandler
from scripts.order import OrderRequest, RequestType, OrderResponse, ResponseType

class OrderManagement:
    """
    Manages the order queue and processes orders
    """
    def __init__(self, start_time, end_time, order_rate_limit):
        self.start_time = start_time
        self.end_time = end_time
        self.order_queue = OrderQueue()
        self.order_processor = OrderProcessor(order_rate_limit, self.order_queue)
        self.response_handler = ResponseHandler(self.order_queue)
        self.active = False

    def is_within_time_window(self):
        """
        Checks if the current time is within the trading window
        """
        current_time = datetime.now().time()
        return self.start_time <= current_time <= self.end_time

    def logon(self):
        if not self.active and self.is_within_time_window():
            self.active = True
            print("Logon message sent to exchange")

    def logout(self):
        if self.active and not self.is_within_time_window():
            self.active = False
            print("Logout message sent to exchange")

    def handle_order_request(self, order_request):
        """
        Handles an order request

        params:
            order_request: the order request to handle
        """
        if not self.is_within_time_window():
            print(f"Order {order_request.m_orderId} rejected: Outside time window")
            return
        else:
            self.order_queue.handle_request(order_request)

    def handle_order_response(self, response):
        """
        Handles an order response

        params:
            response: the order response to handle
        """
        self.response_handler.handle_response(response)

if __name__ == "__main__":
    order_management = OrderManagement(
        start_time=datetime.strptime("10:00:00", "%H:%M:%S").time(),
        end_time=datetime.strptime("18:00:00", "%H:%M:%S").time(),
        order_rate_limit=5,
    )

    order_management.logon()
    order_management.handle_order_request(OrderRequest(1, RequestType.New, "AAPL", "BUY", 100, 100))
    order_management.handle_order_response(OrderResponse(1, ResponseType.Accept))
    order_management.logout()