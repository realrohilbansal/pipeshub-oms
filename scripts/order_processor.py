import time
from threading import Lock, Thread

class OrderProcessor:
    """
    Processes orders and sends them to the exchange (rate limited)
    """
    def __init__(self, order_rate_limit, order_queue):
        self.order_rate_limit = order_rate_limit  # tokens per second
        self.order_queue = order_queue
        self.lock = Lock()
        
        # Token bucket parameters
        self.tokens = order_rate_limit  # Start with full bucket
        self.max_tokens = order_rate_limit
        self.last_update = time.time()
        
        # Start processing thread
        self.running = True
        self.processing_thread = Thread(target=self.process_queue, daemon=True)
        self.processing_thread.start()

    def refill_tokens(self):
        """Refills tokens based on elapsed time"""
        now = time.time()
        time_passed = now - self.last_update
        new_tokens = time_passed * self.order_rate_limit
        self.tokens = min(self.tokens + new_tokens, self.max_tokens)
        self.last_update = now

    def process_queue(self):
        """Processes the order queue using token bucket algorithm"""
        while self.running:
            if self.order_queue.queue:
                with self.lock:
                    self.refill_tokens()
                    
                    if self.tokens >= 1:
                        order = self.order_queue.queue.popleft()
                        self.send(order)
                        self.tokens -= 1
                    
            time.sleep(0.01)  # Small sleep to prevent CPU spinning

    def send(self, order):
        """
        Sends an order to the exchange in a thread-safe manner
        """
        with self.lock:
            print(f"Order {order.m_orderId} sent to exchange.")

    def stop(self):
        """
        Stops the processing thread
        """
        self.running = False
        if self.processing_thread.is_alive():
            self.processing_thread.join()
