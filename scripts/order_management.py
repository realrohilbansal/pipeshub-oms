from datetime import datetime, timedelta
import threading
import json

import os, sys

cwd = os.getcwd()
if cwd.endswith("scripts"):
    os.chdir("..")
sys.path.append(os.getcwd())

from scripts.order import OrderRequest, RequestType, OrderResponse, ResponseType
from scripts.order_queue import OrderQueue
from scripts.order_processor import OrderProcessor
from scripts.response_handler import ResponseHandler

class OrderManagement:
    """
    Manages the order queue and processes orders
    """
    def __init__(self, start_time, end_time, order_rate_limit, response_storage_path="responses.json"):
        """
        Initialize the order management system
        
        Args:
            start_time (time): Trading start time
            end_time (time): Trading end time
            order_rate_limit (int): Maximum orders per second
            response_storage_path (str): Path to store response data
        """
        self.start_time = start_time
        self.end_time = end_time
        self.order_queue = OrderQueue()
        self.order_processor = OrderProcessor(order_rate_limit, self.order_queue)
        self.response_handler = ResponseHandler(self.order_queue, storage_path=response_storage_path)
        self.is_logged_on = False

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
        if not self.is_logged_on and self.is_within_time_window():
            self.is_logged_on = True
            # Thread-safe logon
            threading.Thread(
                target=lambda: print("Logon message sent to exchange"),
                daemon=True
            ).start()

    def logout(self):
        if self.is_logged_on and not self.is_within_time_window():
            self.is_logged_on = False
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
    import time
    from pathlib import Path

    # Create a test storage path
    storage_path = Path("test_responses.json")
    
    # Initialize system during trading hours
    current_time = datetime.now()
    start_time = (current_time - timedelta(hours=1)).time()
    end_time = (current_time + timedelta(hours=1)).time()
    
    order_management = OrderManagement(
        start_time=start_time,
        end_time=end_time,
        order_rate_limit=5,
        response_storage_path=storage_path
    )

    # Start the system
    order_management.logon()
    time.sleep(0.1)  # Wait for logon
    
    # Create and send a new order
    new_order = OrderRequest(
        m_symbolId=1,
        m_price=100.5,
        m_qty=10,
        m_side='B',
        m_orderId=1001,
        request_type=RequestType.New
    )
    print("\nSending new order...")
    order_management.handle_order_request(new_order)
    time.sleep(0.1)  # Wait for order processing

    # Send an accept response
    print("\nSending accept response...")
    accept_response = OrderResponse(1001, ResponseType.Accept)
    order_management.handle_order_response(accept_response)
    time.sleep(0.1)  # Wait for response processing

    # Verify response storage
    print("\nVerifying stored responses...")
    if storage_path.exists():
        with open(storage_path, 'r') as f:
            stored_data = json.load(f)
            print(f"Stored responses: {json.dumps(stored_data, indent=2)}")
            
        # Create new system instance to verify loading
        print("\nCreating new system instance to verify loading...")
        new_system = OrderManagement(
            start_time=start_time,
            end_time=end_time,
            order_rate_limit=5,
            response_storage_path=storage_path
        )
        print(f"Loaded responses: {len(new_system.response_handler.responses)}")
        if new_system.response_handler.responses:
            response = new_system.response_handler.responses[0]
            print(f"First response details: {response}")