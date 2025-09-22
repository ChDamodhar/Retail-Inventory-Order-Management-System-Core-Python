# src/services/order_service.py
from typing import List, Dict
from src.dao.order_dao import OrderDAO
from src.dao.product_dao import ProductDAO
from src.dao.customer_dao import CustomerDAO
from src.services.payment_service import PaymentService, PaymentError

class OrderError(Exception):
    pass

class OrderService:
    def __init__(self):
        self.order_dao = OrderDAO()
        self.product_dao = ProductDAO()
        self.customer_dao = CustomerDAO()
        self.payment_service = PaymentService()

    def create_order(self, cust_id: int, items_to_order: List[Dict]) -> Dict:
        if not self.customer_dao.get_customer_by_id(cust_id):
            raise OrderError(f"Customer with ID {cust_id} not found.")
        if not items_to_order:
            raise OrderError("Cannot create an order with no items.")

        total_amount = 0.0
        items_with_price = []
        products_to_update = []

        for item in items_to_order:
            prod_id, quantity = item["prod_id"], item["quantity"]
            product = self.product_dao.get_product_by_id(prod_id)
            if not product:
                raise OrderError(f"Product with ID {prod_id} not found.")
            if product["stock"] < quantity:
                raise OrderError(f"Not enough stock for '{product['name']}'. Available: {product['stock']}, Requested: {quantity}")
            
            total_amount += float(product["price"]) * quantity
            items_with_price.append({**item, "price": product["price"]})
            products_to_update.append({"id": prod_id, "new_stock": product["stock"] - quantity})

        order = self.order_dao.create_order(cust_id, items_with_price, total_amount)
        if not order:
            raise OrderError("Failed to create the order in the database.")

        for p_update in products_to_update:
            self.product_dao.update_product(p_update["id"], {"stock": p_update["new_stock"]})
            
        self.payment_service.create_payment(order['order_id'], total_amount)

        return self.get_order_details(order["order_id"])

    def get_order_details(self, order_id: int) -> Dict:
        order = self.order_dao.get_order_details(order_id)
        if not order:
            raise OrderError(f"Order with ID {order_id} not found.")
        return order

    def cancel_order(self, order_id: int) -> Dict:
        order = self.get_order_details(order_id)
        if order["status"] in ["CANCELLED", "COMPLETED"]:
            raise OrderError(f"Cannot cancel order {order_id}. Status is '{order['status']}'.")

        for item in order["items"]:
            product = item["product"]
            if product:
                new_stock = product["stock"] + item["quantity"]
                self.product_dao.update_product(product["prod_id"], {"stock": new_stock})
        
        try:
            self.payment_service.refund_payment(order_id)
        except PaymentError as e:
            # Ignore if payment wasn't processed yet, but log it
            print(f"Notice: Could not refund payment for order {order_id}. Reason: {e}")

        return self.order_dao.update_order_status(order_id, "CANCELLED")

    def complete_order(self, order_id: int) -> Dict:
        order = self.get_order_details(order_id)
        if order["status"] != "PLACED":
             raise OrderError(f"Only 'PLACED' orders can be completed. Current status: '{order['status']}'.")
        
        payment = self.payment_service.payment_dao.get_payment(order_id)
        if not payment or payment['status'] != 'PAID':
            raise OrderError(f"Order cannot be completed until payment is processed. Payment status: '{payment['status'] if payment else 'N/A'}'.")

        return self.order_dao.update_order_status(order_id, "COMPLETED")