import time
import threading
from queue import Empty

class OrderProcessor:
    """
    Processes orders from the queue at a rate-limited pace
    """
    def __init__(self, order_rate_limit, order_queue):
        self.order_rate_limit = order_rate_limit
        self.order_queue = order_queue
        self.tokens = order_rate_limit  # Start with full bucket
        self.max_tokens = order_rate_limit
        self.last_token_time = time.time()
        self.lock = threading.Lock()
        self.running = True

    def refill_tokens(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        time_passed = now - self.last_token_time
        new_tokens = time_passed * self.order_rate_limit
        self.tokens = min(self.tokens + new_tokens, self.max_tokens)
        self.last_token_time = now

    def process_queue(self):
        """Process orders from the queue at the rate limit"""
        while self.running:
            try:
                # Check if we have tokens available
                with self.lock:
                    self.refill_tokens()
                    if self.tokens >= 1 and len(self.order_queue.queue) > 0:
                        order = self.order_queue.queue.popleft()
                        self.tokens -= 1
                        self.send(order)
                    
                # Sleep briefly to prevent busy-waiting
                time.sleep(0.1)
                    
            except Empty:
                # No orders in queue, wait briefly
                time.sleep(0.1)
            except Exception as e:
                print(f"Error processing order: {e}")
                time.sleep(0.1)

    def send(self, order):
        """Simulate sending order to exchange"""
        print(f"Sending order {order.m_orderId} to exchange")
        # Simulate network delay
        time.sleep(0.05)

    def stop(self):
        """Stop the processor"""
        self.running = False
