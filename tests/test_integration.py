import unittest
import time
from datetime import datetime, timedelta

import os
import sys

cwd = os.getcwd()
if cwd.endswith("tests"):
    os.chdir("..")
sys.path.append(os.getcwd())

from scripts.order_management import OrderManagement
from scripts.order import OrderRequest, OrderResponse, RequestType, ResponseType

class TestOrderManagementIntegration(unittest.TestCase):
    def setUp(self):
        # Set up with trading hours from 10 AM to 5 PM
        self.system = OrderManagement(
            start_time=datetime.strptime("10:00:00", "%H:%M:%S").time(),
            end_time=datetime.strptime("18:00:00", "%H:%M:%S").time(),
            order_rate_limit=5
        )
        self.system.logon()

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
        # Submit orders at rate higher than limit
        orders_to_submit = 10
        for i in range(orders_to_submit):
            order = OrderRequest(
                m_symbolId=1,
                m_price=100.0 + i,
                m_qty=10,
                m_side='B',
                m_orderId=2000 + i
            )
            self.system.handle_order_request(order)

        # Verify that some orders are queued due to rate limiting
        self.assertTrue(len(self.system.order_queue.queue) > 0)
        self.assertLessEqual(
            self.system.order_processor.orders_sent_this_second,
            self.system.order_processor.order_rate_limit
        )

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
        
        # Simulate some processing time
        time.sleep(0.1)
        
        # Send response
        response = OrderResponse(3001, ResponseType.Accept)
        self.system.handle_order_response(response)

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

        # Send responses in reverse order
        for i in range(4, -1, -1):
            response = OrderResponse(5001 + i, ResponseType.Accept)
            self.system.handle_order_response(response)

        # Verify all responses were handled
        self.assertEqual(len(self.system.response_handler.responses), 5)
        self.assertEqual(len(self.system.order_queue.orders), 0)

    def tearDown(self):
        self.system.logout()

if __name__ == "__main__":
    unittest.main()
