# src/services/payment_service.py
from datetime import datetime
from src.dao.payment_dao import PaymentDAO
from src.dao.order_dao import OrderDAO

class PaymentError(Exception):
    pass

class PaymentService:
    def __init__(self):
        self.payment_dao = PaymentDAO()
        self.order_dao = OrderDAO()

    def create_payment(self, order_id: int, amount: float):
        """Insert a pending payment record when an order is created."""
        return self.payment_dao.create_payment(order_id, amount)

    def process_payment(self, order_id: int, method: str):
        """Mark payment as PAID and update order status."""
        order = self.order_dao.get_order_details(order_id)
        if not order:
            raise PaymentError(f"Order with ID {order_id} not found.")
        
        if order['status'] != 'PLACED':
             raise PaymentError(f"Cannot process payment for an order with status '{order['status']}'.")

        payment = self.payment_dao.update_payment(order_id, "PAID", method, datetime.utcnow())
        self.order_dao.update_order_status(order_id, "COMPLETED")
        return payment

    def refund_payment(self, order_id: int):
        """Mark payment as REFUNDED."""
        payment = self.payment_dao.get_payment(order_id)
        if not payment:
            raise PaymentError(f"No payment record found for order ID {order_id}.")
        
        if payment['status'] != 'PAID':
            raise PaymentError(f"Cannot refund a payment that is not 'PAID'. Current status: '{payment['status']}'")

        return self.payment_dao.update_payment(order_id, "REFUNDED")