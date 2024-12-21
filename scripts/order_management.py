from datetime import datetime
import threading

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

        # Add thread for order processing
        self.processing_thread = threading.Thread(
            target=self.order_processor.process_queue,
            daemon=True
        )
        self.processing_thread.start()

    def is_within_time_window(self):
        """
        Checks if the current time is within the trading window
        """
        current_time = datetime.now().time()
        return self.start_time <= current_time <= self.end_time

    def logon(self):
        if not self.active and self.is_within_time_window():
            self.active = True
            # Thread-safe logon
            threading.Thread(
                target=lambda: print("Logon message sent to exchange"),
                daemon=True
            ).start()

    def logout(self):
        if self.active and not self.is_within_time_window():
            self.active = False
            # Thread-safe logout
            threading.Thread(
                target=lambda: print("Logout message sent to exchange"),
                daemon=True
            ).start()

    def handle_order_request(self, order_request):
        """
        Handles an order request in a separate thread
        """
        def process_request():
            if not self.is_within_time_window():
                print(f"Order {order_request.m_orderId} rejected: Outside time window")
                return
            else:
                self.order_queue.handle_request(order_request)

        threading.Thread(target=process_request, daemon=True).start()

    def handle_order_response(self, response):
        """
        Handles an order response in a separate thread
        """
        threading.Thread(
            target=lambda: self.response_handler.handle_response(response),
            daemon=True
        ).start()

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