from typing import List, Dict, Optional
from src.config import get_supabase

class OrderDAO:
    """Data Access Object for orders and order_items."""

    def __init__(self):
        self._sb = get_supabase()

    def create_order(self, cust_id: int, items: List[Dict], total_amount: float) -> Optional[Dict]:
        """Insert order and order_items."""

        # 1️⃣ Insert order
        order_payload = {
            "cust_id": cust_id,
            "total_amount": total_amount,
            "status": "PLACED"
        }
        self._sb.table("orders").insert(order_payload).execute()

        # 2️⃣ Fetch the latest order for this customer
        order_resp = (
            self._sb.table("orders")
            .select("*")
            .eq("cust_id", cust_id)
            .order("order_date", desc=True)  # Use actual column
            .limit(1)
            .execute()
        )
        if not order_resp.data:
            return None

        order_id = order_resp.data[0]["order_id"]

        # 3️⃣ Insert order items
        for item in items:
            prod_resp = (
                self._sb.table("products")
                .select("*")
                .eq("prod_id", item["prod_id"])  # Use correct column name
                .limit(1)
                .execute()
            )
            if not prod_resp.data:
                continue

            product = prod_resp.data[0]

            item_payload = {
                "order_id": order_id,
                "product_id": product["prod_id"],  # FK column in order_items
                "quantity": item["quantity"],
                "price": product["price"]           # store current price
            }
            self._sb.table("order_items").insert(item_payload).execute()

        return self.get_order_details(order_id)

    def get_order_details(self, order_id: int) -> Optional[Dict]:
        """Return order info with customer and items."""
        order_resp = self._sb.table("orders").select("*").eq("order_id", order_id).limit(1).execute()
        if not order_resp.data:
            return None
        order = order_resp.data[0]

        # Fetch customer info
        cust_resp = self._sb.table("customers").select("*").eq("cust_id", order["cust_id"]).limit(1).execute()
        order["customer"] = cust_resp.data[0] if cust_resp.data else None

        # Fetch order items
        items_resp = self._sb.table("order_items").select("*").eq("order_id", order_id).execute()
        order["items"] = items_resp.data or []

        return order

    def list_orders_by_customer(self, cust_id: int) -> List[Dict]:
        resp = self._sb.table("orders").select("*").eq("cust_id", cust_id).execute()
        return resp.data or []

    def update_order_status(self, order_id: int, status: str) -> Optional[Dict]:
        self._sb.table("orders").update({"status": status}).eq("order_id", order_id).execute()
        return self.get_order_details(order_id)