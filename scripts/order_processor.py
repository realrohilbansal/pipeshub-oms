import time
from threading import Lock

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

    def process_queue(self):
        """
        Processes the order queue
        """
        while True:
            with self.lock:
                current_time = int(time.time())
                if current_time != self.current_second:
                    self.orders_sent_this_second = 0
                    self.current_second = current_time

                while self.orders_sent_this_second < self.order_rate_limit and self.order_queue.queue:
                    order = self.order_queue.queue.popleft()
                    self.send(order)
                    self.orders_sent_this_second += 1

            time.sleep(0.01)

    def send(self, order):
        """
        sends an order to the exchange
        """
        print(f"Order {order.m_orderId} sent to exchange.")
