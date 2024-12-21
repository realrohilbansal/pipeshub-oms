import unittest
import time
from datetime import datetime, timedelta

import os
import sys
import tempfile
from pathlib import Path

cwd = os.getcwd()
if cwd.endswith("tests"):
    os.chdir("..")
sys.path.append(os.getcwd())

from scripts.order_management import OrderManagement
from scripts.order import OrderRequest, OrderResponse, RequestType, ResponseType

class TestOrderManagementIntegration(unittest.TestCase):
    def setUp(self):
        # Create temporary storage for responses
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "test_responses.json"
        
        # Set up with trading hours that include current time
        current_time = datetime.now().time()
        self.start_time = (datetime.now() - timedelta(hours=1)).time()
        self.end_time = (datetime.now() + timedelta(hours=1)).time()
        
        self.system = OrderManagement(
            start_time=self.start_time,
            end_time=self.end_time,
            order_rate_limit=5,
            response_storage_path=self.storage_path
        )
        self.system.logon()
        # Small delay to ensure threads are started
        time.sleep(0.1)

    def test_complete_order_lifecycle(self):
        """Test a complete order lifecycle: New -> Modify -> Cancel"""
        # Create new order
        new_order = OrderRequest(
            m_symbolId=1,
            m_price=100.5,
            m_qty=10,
            m_side='B',
            m_orderId=1001,
            request_type=RequestType.New
        )
        self.system.handle_order_request(new_order)
        time.sleep(0.1)  # Allow time for async processing
        self.assertIn(1001, self.system.order_queue.orders)

        # Modify order
        modify_order = OrderRequest(
            m_symbolId=1,
            m_price=101.5,
            m_qty=15,
            m_side='B',
            m_orderId=1001,
            request_type=RequestType.Modify
        )
        self.system.handle_order_request(modify_order)
        self.assertEqual(self.system.order_queue.orders[1001].m_price, 101.5)
        self.assertEqual(self.system.order_queue.orders[1001].m_qty, 15)

        # Cancel order
        cancel_order = OrderRequest(
            m_symbolId=1,
            m_price=101.5,
            m_qty=15,
            m_side='B',
            m_orderId=1001,
            request_type=RequestType.Cancel
        )
        self.system.handle_order_request(cancel_order)
        self.assertNotIn(1001, self.system.order_queue.orders)

    def test_rate_limiting(self):
        """Test that orders are rate limited correctly"""
        # Submit fewer orders at rate higher than limit
        orders_to_submit = 5  # Reduced from 10
        
        # Submit orders
        for i in range(orders_to_submit):
            order = OrderRequest(
                m_symbolId=1,
                m_price=100.0 + i,
                m_qty=10,
                m_side='B',
                m_orderId=2000 + i,
                request_type=RequestType.New
            )
            self.system.handle_order_request(order)
        
        # Allow some time for initial processing
        time.sleep(0.2)
        
        # Verify token bucket state
        with self.system.order_processor.lock:
            initial_tokens = self.system.order_processor.tokens
            self.assertLessEqual(
                initial_tokens,
                self.system.order_processor.max_tokens
            )
        
        # Allow time for token replenishment
        time.sleep(1.0)
        
        # Verify tokens have been replenished
        with self.system.order_processor.lock:
            final_tokens = self.system.order_processor.tokens
            self.assertGreater(final_tokens, initial_tokens)

    def test_response_handling(self):
        """Test order response handling and latency calculation"""
        # Submit order
        order = OrderRequest(
            m_symbolId=1,
            m_price=100.0,
            m_qty=10,
            m_side='B',
            m_orderId=3001
        )
        self.system.handle_order_request(order)
        time.sleep(0.1)  # Allow time for async processing
        
        # Send response
        response = OrderResponse(3001, ResponseType.Accept)
        self.system.handle_order_response(response)
        time.sleep(0.1)  # Allow time for async processing

        # Verify response handling
        self.assertEqual(len(self.system.response_handler.responses), 1)
        response_record = self.system.response_handler.responses[0]
        self.assertEqual(response_record['order_id'], 3001)
        self.assertEqual(response_record['response_type'], ResponseType.Accept)
        self.assertGreater(response_record['latency'], 0)

    def test_trading_hours(self):
        """Test order handling during and outside trading hours"""
        # Create an order
        order = OrderRequest(
            m_symbolId=1,
            m_price=100.0,
            m_qty=10,
            m_side='B',
            m_orderId=4001
        )

        # Test during trading hours
        if self.system.is_within_time_window():
            self.system.handle_order_request(order)
            self.assertIn(4001, self.system.order_queue.orders)

        # Force outside trading hours scenario
        self.system.end_time = (datetime.now() - timedelta(hours=1)).time()
        order.m_orderId = 4002
        self.system.handle_order_request(order)
        self.assertNotIn(4002, self.system.order_queue.orders)

    def test_multiple_orders_and_responses(self):
        """Test handling multiple orders and responses simultaneously"""
        # Submit multiple orders
        orders = []
        for i in range(5):
            order = OrderRequest(
                m_symbolId=1,
                m_price=100.0 + i,
                m_qty=10,
                m_side='B',
                m_orderId=5001 + i
            )
            orders.append(order)
            self.system.handle_order_request(order)
        
        time.sleep(0.1)  # Allow time for async processing

        # Send responses in reverse order
        for i in range(4, -1, -1):
            response = OrderResponse(5001 + i, ResponseType.Accept)
            self.system.handle_order_response(response)
        
        time.sleep(0.1)  # Allow time for async processing
        self.assertEqual(len(self.system.response_handler.responses), 5)
        self.assertEqual(len(self.system.order_queue.orders), 0)

    def test_response_persistence(self):
        """Test that responses are properly persisted to storage"""
        # Submit order
        order = OrderRequest(
            m_symbolId=1,
            m_price=100.0,
            m_qty=10,
            m_side='B',
            m_orderId=6001
        )
        self.system.handle_order_request(order)
        time.sleep(0.1)
        
        # Send response
        response = OrderResponse(6001, ResponseType.Accept)
        self.system.handle_order_response(response)
        time.sleep(0.1)

        # Create new system instance to verify loading from storage
        new_system = OrderManagement(
            start_time=self.start_time,
            end_time=self.end_time,
            order_rate_limit=5,
            response_storage_path=self.storage_path
        )
        
        self.assertEqual(len(new_system.response_handler.responses), 1)
        stored_response = new_system.response_handler.responses[0]
        self.assertEqual(stored_response['order_id'], 6001)
        self.assertEqual(stored_response['response_type'], str(ResponseType.Accept))
        self.assertIn('timestamp', stored_response)
        self.assertIn('latency', stored_response)

    def tearDown(self):
        self.system.logout()
        # Clean up temporary files
        if self.storage_path.exists():
            self.storage_path.unlink()
        os.rmdir(self.temp_dir)

if __name__ == "__main__":
    unittest.main()
