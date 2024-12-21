import time
import json
from pathlib import Path

class ResponseHandler:
    def __init__(self, order_queue, storage_path="responses.json"):
        self.order_queue = order_queue
        self.responses = []
        self.storage_path = Path(storage_path)
        self._load_responses()  # Load existing responses on initialization

    def _load_responses(self):
        """Load existing responses from storage file"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    self.responses = json.load(f)
            except json.JSONDecodeError:
                # If file is empty or corrupted, start with empty list
                self.responses = []
        else:
            # Create the file with an empty list
            self._save_responses()

    def _save_responses(self):
        """Save responses to persistent storage"""
        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w') as f:
            # Convert responses to JSON-serializable format
            serializable_responses = []
            for response in self.responses:
                serializable_response = response.copy()
                # Convert ResponseType enum to string
                if 'response_type' in serializable_response:
                    serializable_response['response_type'] = str(serializable_response['response_type'])
                serializable_responses.append(serializable_response)
            json.dump(serializable_responses, f, indent=4)

    def handle_response(self, response):
        """
        Handles a response from the exchange and stores it persistently
        """
        if response.m_orderId in self.order_queue.orders:
            latency = time.time() - self.order_queue.orders[response.m_orderId].timestamp
            response_data = {
                "order_id": response.m_orderId,
                "response_type": response.m_responseType,
                "latency": latency,
                "timestamp": time.time()
            }
            self.responses.append(response_data)
            self._save_responses()  # Save to persistent storage
            del self.order_queue.orders[response.m_orderId]
            print(f"Processed response for Order {response.m_orderId}. Latency: {latency:.2f}s")
