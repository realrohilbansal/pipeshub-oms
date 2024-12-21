import time
from threading import Lock, Thread

class OrderProcessor:
    """
    Processes orders and sends them to the exchange (rate limited)
    """
    def __init__(self, order_rate_limit, order_queue):
        self.order_rate_limit = order_rate_limit
        self.order_queue = order_queue
        self.lock = Lock()
        self.orders_sent_this_second = 0
        self.current_second = int(time.time())
        
        # Start processing thread
        self.running = True
        self.processing_thread = Thread(target=self.process_queue, daemon=True)
        self.processing_thread.start()

    def process_queue(self):
        """
        Processes the order queue in a separate thread
        """
        while self.running:
            with self.lock:
                current_time = int(time.time())
                if current_time != self.current_second:
                    self.orders_sent_this_second = 0
                    self.current_second = current_time

                while (self.orders_sent_this_second < self.order_rate_limit and 
                       self.order_queue.queue):
                    order = self.order_queue.queue.popleft()
                    self.send(order)
                    self.orders_sent_this_second += 1

            time.sleep(0.01)

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
