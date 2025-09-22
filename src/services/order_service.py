from typing import List, Dict
from src.dao.order_dao import OrderDAO
from src.dao.customer_dao import CustomerDAO
from src.dao.product_dao import ProductDAO
from src.services.payment_service import PaymentService


class OrderError(Exception):
    pass


class OrderService:
    """Service for creating and managing orders."""

    def __init__(self):
        self.order_dao = OrderDAO()
        self.customer_dao = CustomerDAO()
        self.product_dao = ProductDAO()
        self.payment_service = PaymentService()  # Inject PaymentService here

    def create_order(self, cust_id: int, items: List[Dict]) -> Dict:
        # 1️⃣ Check customer exists
        customer = self.customer_dao.get_customer_by_id(cust_id)
        if not customer:
            raise OrderError(f"Customer {cust_id} does not exist")

        # 2️⃣ Check stock & calculate total
        total_amount = 0
        for item in items:
            prod = self.product_dao.get_product_by_id(item["prod_id"])
            if not prod:
                raise OrderError(f"Product {item['prod_id']} does not exist")
            if prod.get("stock", 0) < item["quantity"]:
                raise OrderError(
                    f"Insufficient stock for {prod['name']} (Available: {prod['stock']})"
                )
            total_amount += prod["price"] * item["quantity"]

        # 3️⃣ Deduct stock
        for item in items:
            prod = self.product_dao.get_product_by_id(item["prod_id"])
            new_stock = prod["stock"] - item["quantity"]
            self.product_dao.update_product(item["prod_id"], {"stock": new_stock})

        # 4️⃣ Create order
        order = self.order_dao.create_order(cust_id, items, total_amount)

        # 5️⃣ Create pending payment for this order
        self.payment_service.create_payment(order["order_id"], total_amount)

        return order

    def get_order_details(self, order_id: int) -> Dict:
        order = self.order_dao.get_order_details(order_id)
        if not order:
            raise OrderError(f"Order {order_id} not found")
        return order

    def list_orders_by_customer(self, cust_id: int) -> List[Dict]:
        return self.order_dao.list_orders_by_customer(cust_id)

    def cancel_order(self, order_id: int) -> Dict:
        order = self.get_order_details(order_id)
        if order["status"] != "PLACED":
            raise OrderError("Only PLACED orders can be cancelled")

        # Restore stock
        for item in order["items"]:
            prod = self.product_dao.get_product_by_id(item["product_id"])
            new_stock = prod.get("stock", 0) + item["quantity"]
            self.product_dao.update_product(item["product_id"], {"stock": new_stock})

        # Update order status
        self.order_dao.update_order_status(order_id, "CANCELLED")

        # Refund payment
        self.payment_service.refund_payment(order_id)

        # Return updated order
        return self.get_order_details(order_id)

    def complete_order(self, order_id: int) -> Dict:
        order = self.get_order_details(order_id)
        if order["status"] != "PLACED":
            raise OrderError("Only PLACED orders can be completed")
        updated_order = self.order_dao.update_order_status(order_id, "COMPLETED")
        # Optionally mark payment as PAID if not already
        self.payment_service.process_payment(order_id, method="UPI")  # Default method
        return updated_order