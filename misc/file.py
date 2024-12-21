"""
My first attempt at the order management system. Contains everything in a single file. Works, but not very modular.
"""

import threading
import time
from collections import deque, defaultdict
from datetime import datetime
import random

class RequestType:
    Unknown = 0
    New = 1
    Modify = 2
    Cancel = 3

class ResponseType:
    Unknown = 0
    Accept = 1
    Reject = 2

class OrderRequest:
    def __init__(self, m_symbolId, m_price, m_qty, m_side, m_orderId, request_type=RequestType.New):
        self.m_symbolId = m_symbolId
        self.m_price = m_price
        self.m_qty = m_qty
        self.m_side = m_side 
        self.m_orderId = m_orderId
        self.request_type = request_type
        self.timestamp = time.time()

class OrderResponse:
    def __init__(self, m_orderId, response_type):
        self.m_orderId = m_orderId
        self.m_responseType = response_type

class OrderManagement:
    def __init__(self, start_time, end_time, order_rate_limit):
        # Add authentication-related attributes
        self.username = None
        self.is_authenticated = False
        
        # Configurable time period and rate limits
        self.start_time = start_time
        self.end_time = end_time
        self.order_rate_limit = order_rate_limit

        # Internal state
        self.order_queue = deque()
        self.pending_orders = defaultdict(dict)
        self.responses = []
        self.lock = threading.Lock()
        self.active = False

        # For rate-limiting
        self.orders_sent_this_second = 0
        self.current_second = int(time.time())

    def is_within_time_window(self):
        """
        Checks if the current time is within the configured time window.
        This ensures that orders are only processed during valid hours.
        
        returns:
            bool: True if the current time is within the configured time window, else False.
        """
        current_time = datetime.now().time()
        return self.start_time <= current_time <= self.end_time

    def logon(self, username, password):
        """
        Authenticates user and sends a logon message to the exchange when entering the trading window.
        
        Args:
            username (str): The user's username
            password (str): The user's password
            
        Returns:
            bool: True if authentication and logon successful, False otherwise
        """
        if not self.is_within_time_window():
            print("Cannot logon outside trading hours")
            return False
            
        if not self._authenticate(username, password):
            print("Authentication failed")
            return False
            
        if not self.active:
            self.active = True
            self.username = username
            self.sendLogon()
            return True
        return False

    def logout(self):
        """
        Sends a logout message to the exchange and clears authentication.
        """
        if self.active:
            self.active = False
            self.sendLogout()
            self.username = None
            self.is_authenticated = False

    def _authenticate(self, username, password):
        """
        Placeholder for actual authentication logic.
        
        Args:
            username (str): The user's username
            password (str): The user's password
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        # Replace this with actual authentication logic (e.g., database check)
        valid_credentials = {
            "trader1": "password123",
            "trader2": "password456"
        }
        
        is_valid = valid_credentials.get(username) == password
        self.is_authenticated = is_valid
        return is_valid

    def process_queue(self):
        """
        Continuously processes the order queue, sending orders within rate limits.
        """
        while True:
            # lock for thread safety
            with self.lock:
                current_time = int(time.time())

                # Reset the rate lim counter at the start of each second
                if current_time != self.current_second:
                    self.orders_sent_this_second = 0
                    self.current_second = current_time

                # Send orders from the queue while respecting the rate limit
                while self.orders_sent_this_second < self.order_rate_limit and self.order_queue:
                    order = self.order_queue.popleft()
                    self.send(order)
                    self.orders_sent_this_second += 1

            time.sleep(0.01)  # prevent busy waiting

    def handle_order_request(self, request):
        """
        Handles incoming order requests. Processes Modify and Cancel requests.
        """
        if not self.is_authenticated:
            print(f"Order {request.m_orderId} rejected: User not authenticated")
            return
            
        if not self.is_within_time_window():
            print(f"Order {request.m_orderId} rejected: Outside time window")
            return

        with self.lock:
            if request.m_orderId in self.pending_orders:
                if request.request_type == RequestType.Modify:
                    # Modify logic: Update the price and quantity of the existing order in the queue by reference
                    # modifying the properties directly in the dict, leaving the queue order intact
                    self.pending_orders[request.m_orderId]["price"] = request.m_price
                    self.pending_orders[request.m_orderId]["qty"] = request.m_qty
                    print(f"Order {request.m_orderId} modified in queue.")

                elif request.request_type == RequestType.Cancel:
                    # Cancel logic: Remove the order from the queue entirely
                    # using the reference stored in pending_orders to locate and delete the order
                    self.order_queue.remove(self.pending_orders[request.m_orderId]["order"])
                    del self.pending_orders[request.m_orderId]
                    print(f"Order {request.m_orderId} canceled in queue.")

            else:
                # For new orders add them to the queue and dict
                self.order_queue.append(request)
                self.pending_orders[request.m_orderId] = {
                    "order": request,
                    "price": request.m_price,
                    "qty": request.m_qty,
                    "timestamp": time.time()
                }
                print(f"Order {request.m_orderId} added to queue.")

    def handle_order_response(self, response):
        """
        Handles responses from the exchange and measures latency.
        """
        with self.lock:
            if response.m_orderId in self.pending_orders:
                latency = time.time() - self.pending_orders[response.m_orderId]["timestamp"]
                self.responses.append(
                    {
                        "order_id": response.m_orderId,
                        "response_type": response.m_responseType,
                        "latency": latency,
                    }
                )
                del self.pending_orders[response.m_orderId]

                print(f"Processed response for Order {response.m_orderId}. Latency: {latency:.2f}s")

    def sendLogon(self):
        """
        Placeholder for sending a logon message to the exchange
        """
        print("Logon message sent to exchange")

    def sendLogout(self):
        """
        Placeholder for sending a logout message to the exchange
        """
        print("Logout message sent to exchange")

    def send(self, request):
        """
        Placeholder for sending an order request to the exchange
        """
        print(f"Order {request.m_orderId} sent to exchange")

if __name__ == "__main__":
    # Initialize the order management system
    order_system = OrderManagement(
        start_time=datetime.strptime("10:00:00", "%H:%M:%S").time(),
        end_time=datetime.strptime("19:00:00", "%H:%M:%S").time(),
        order_rate_limit=5,
    )

    # Start processing thread
    processing_thread = threading.Thread(target=order_system.process_queue, daemon=True)
    processing_thread.start()

    # Attempt login with invalid credentials
    print("\n--- Testing invalid login ---")
    if not order_system.logon("trader1", "wrongpassword"):
        print("Invalid login rejected as expected")

    # Login with valid credentials
    print("\n--- Testing valid login ---")
    if order_system.logon("trader1", "password123"):
        print("Successfully logged in")
        
        # Send some test orders
        print("\n--- Sending test orders ---")
        for i in range(10):
            order = OrderRequest(
                m_symbolId=random.randint(1, 100),
                m_price=random.uniform(100, 200),
                m_qty=random.randint(1, 10),
                m_side='B',
                m_orderId=i,
            )
            order_system.handle_order_request(order)
            time.sleep(0.1)

        # Send some test responses
        print("\n--- Processing test responses ---")
        for i in range(10):
            response = OrderResponse(
                m_orderId=i,
                response_type=random.choice([ResponseType.Accept, ResponseType.Reject]),
            )
            order_system.handle_order_response(response)
            time.sleep(0.2)

        # Test order modification
        print("\n--- Testing order modification ---")
        modify_order = OrderRequest(
            m_symbolId=1,
            m_price=150.0,
            m_qty=5,
            m_side='B',
            m_orderId=0,
            request_type=RequestType.Modify
        )
        order_system.handle_order_request(modify_order)

        # Test order cancellation
        print("\n--- Testing order cancellation ---")
        cancel_order = OrderRequest(
            m_symbolId=1,
            m_price=0,
            m_qty=0,
            m_side='B',
            m_orderId=1,
            request_type=RequestType.Cancel
        )
        order_system.handle_order_request(cancel_order)

        # Logout
        print("\n--- Logging out ---")
        order_system.logout()
        
        # Try to send order after logout (should be rejected)
        print("\n--- Testing order after logout ---")
        unauthorized_order = OrderRequest(
            m_symbolId=1,
            m_price=100.0,
            m_qty=1,
            m_side='B',
            m_orderId=99
        )
        order_system.handle_order_request(unauthorized_order)

    # Allow some time for the processing thread to complete
    time.sleep(1)
