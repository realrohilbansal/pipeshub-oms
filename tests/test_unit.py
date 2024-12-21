import unittest

import os
import sys
import tempfile
from pathlib import Path

cwd = os.getcwd()
if cwd.endswith("tests"):
    os.chdir("..")
sys.path.append(os.getcwd())

from datetime import datetime, time
from unittest.mock import patch
from scripts.order import OrderRequest, OrderResponse, RequestType, ResponseType
from scripts.order_queue import OrderQueue
from scripts.order_processor import OrderProcessor
from scripts.response_handler import ResponseHandler
from scripts.order_management import OrderManagement
from unittest.mock import Mock

class TestOrderSystem(unittest.TestCase):
    def setUp(self):
        self.order_queue = OrderQueue()
        self.start_time = time(10, 0)
        self.end_time = time(18, 0)
        self.order_management = OrderManagement(self.start_time, self.end_time, 5)
        # Create a temporary file for response storage
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "test_responses.json"

    def tearDown(self):
        # Clean up temporary files
        if self.storage_path.exists():
            self.storage_path.unlink()
        os.rmdir(self.temp_dir)

    def create_sample_order(self):
        return OrderRequest(
            m_symbolId=1,
            m_price=100.5,
            m_qty=10,
            m_side='B',
            m_orderId=123
        )

    # OrderQueue Tests
    def test_order_queue_initialization(self):
        self.assertEqual(len(self.order_queue.orders), 0)
        self.assertEqual(len(self.order_queue.queue), 0)

    def test_order_queue_add_order(self):
        order = self.create_sample_order()
        self.order_queue.add_order(order)
        self.assertEqual(len(self.order_queue.orders), 1)
        self.assertEqual(len(self.order_queue.queue), 1)
        self.assertEqual(self.order_queue.orders[123], order)

    def test_order_queue_modify_order(self):
        order = self.create_sample_order()
        self.order_queue.add_order(order)
        
        modify_request = OrderRequest(
            m_symbolId=1,
            m_price=105.0,
            m_qty=15,
            m_side='B',
            m_orderId=123,
            request_type=RequestType.Modify
        )
        self.order_queue.modify_order(modify_request)
        
        modified_order = self.order_queue.orders[123]
        self.assertEqual(modified_order.m_price, 105.0)
        self.assertEqual(modified_order.m_qty, 15)

    def test_order_queue_cancel_order(self):
        order = self.create_sample_order()
        self.order_queue.add_order(order)
        
        cancel_request = OrderRequest(
            m_symbolId=1,
            m_price=100.5,
            m_qty=10,
            m_side='B',
            m_orderId=123,
            request_type=RequestType.Cancel
        )
        self.order_queue.cancel_order(cancel_request)
        
        self.assertEqual(len(self.order_queue.orders), 0)
        self.assertEqual(len(self.order_queue.queue), 0)

    # OrderProcessor Tests
    def test_order_processor_initialization(self):
        processor = OrderProcessor(5, self.order_queue)
        self.assertEqual(processor.order_rate_limit, 5)
        self.assertEqual(processor.tokens, 5)  # Should start with full bucket
        self.assertEqual(processor.max_tokens, 5)

    @patch('time.time')
    def test_order_processor_rate_limiting(self, mock_time):
        # Set initial time
        mock_time.return_value = 1000.0
        processor = OrderProcessor(2, self.order_queue)
        
        # Add three orders
        for i in range(3):
            order = OrderRequest(1, 100.5, 10, 'B', i)
            self.order_queue.add_order(order)
        
        # Process orders
        processor.send = Mock()  # Mock the send method
        
        with processor.lock:
            processor.refill_tokens()  # Should have full tokens
            
            # Should process first two orders
            while processor.tokens >= 1 and self.order_queue.queue:
                order = self.order_queue.queue.popleft()
                processor.send(order)
                processor.tokens -= 1
        
        self.assertEqual(len(self.order_queue.queue), 1)  # One order should remain
        self.assertEqual(processor.tokens, 0)  # Should have used all tokens
        self.assertEqual(processor.send.call_count, 2)  # Send should have been called twice

    @patch('time.time')
    def test_token_refill(self, mock_time):
        mock_time.return_value = 1000.0
        processor = OrderProcessor(2, self.order_queue)  # 2 tokens per second
        
        # Use all tokens
        processor.tokens = 0
        
        # Advance time by 0.5 seconds
        mock_time.return_value = 1000.5
        processor.refill_tokens()
        
        self.assertEqual(processor.tokens, 1)  # Should have gained 1 token (2 tokens/sec * 0.5 sec)

    # ResponseHandler Tests
    def test_response_handler(self):
        handler = ResponseHandler(self.order_queue, storage_path=self.storage_path)
        order = self.create_sample_order()
        self.order_queue.add_order(order)
        
        response = OrderResponse(123, ResponseType.Accept)
        handler.handle_response(response)
        
        # Test in-memory responses
        self.assertEqual(len(handler.responses), 1)
        self.assertEqual(handler.responses[0]['order_id'], 123)
        self.assertEqual(handler.responses[0]['response_type'], ResponseType.Accept)
        self.assertIn('timestamp', handler.responses[0])
        self.assertIn('latency', handler.responses[0])

        # Test persistent storage
        self.assertTrue(self.storage_path.exists())
        
        # Create new handler to test loading from file
        new_handler = ResponseHandler(self.order_queue, storage_path=self.storage_path)
        self.assertEqual(len(new_handler.responses), 1)
        self.assertEqual(new_handler.responses[0]['order_id'], 123)


if __name__ == "__main__":
    unittest.main()
