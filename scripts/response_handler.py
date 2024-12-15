import time

class ResponseHandler:
    def __init__(self, order_queue):
        self.order_queue = order_queue
        self.responses = []

    def handle_response(self, response):
        """
        Handles a response from the exchange
        """
        if response.m_orderId in self.order_queue.orders:
            latency = time.time() - self.order_queue.orders[response.m_orderId].timestamp
            self.responses.append({
                "order_id": response.m_orderId,
                "response_type": response.m_responseType,
                "latency": latency,
            })
            del self.order_queue.orders[response.m_orderId]
            print(f"Processed response for Order {response.m_orderId}. Latency: {latency:.2f}s")
