# src/services/reporting_service.py
from datetime import datetime, timedelta
from src.config import get_supabase
from typing import List, Dict

class ReportingService:
    """Service to generate reports for sales and customers."""

    def __init__(self):
        self._sb = get_supabase()

    def top_selling_products(self, limit: int = 5) -> List[Dict]:
        """Return top selling products by total quantity sold."""
        resp = self._sb.table("order_items").select("prod_id, quantity").execute()
        if not resp.data:
            return []

        totals = {}
        for item in resp.data:
            pid = item["prod_id"]
            totals[pid] = totals.get(pid, 0) + item["quantity"]

        sorted_pids = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:limit]
        if not sorted_pids:
            return []

        product_ids = [pid for pid, _ in sorted_pids]
        prod_resp = self._sb.table("products").select("prod_id, name").in_("prod_id", product_ids).execute()
        product_names = {p["prod_id"]: p["name"] for p in prod_resp.data}

        return [
            {"prod_id": pid, "name": product_names.get(pid, f"Unknown Product {pid}"), "total_sold": qty}
            for pid, qty in sorted_pids
        ]

    def total_revenue_last_month(self) -> Dict:
        """Return total revenue from completed orders in the last calendar month."""
        today = datetime.utcnow().date()
        first_day_current_month = today.replace(day=1)
        last_day_last_month = first_day_current_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)

        resp = (
            self._sb.table("orders")
            .select("total_amount")
            .eq("status", "COMPLETED")
            .gte("order_date", first_day_last_month.isoformat())
            .lte("order_date", (last_day_last_month + timedelta(days=1)).isoformat()) # lte is inclusive
            .execute()
        )
        
        total = sum(float(o["total_amount"]) for o in resp.data) if resp.data else 0.0
        return {
            "start_date": first_day_last_month.isoformat(),
            "end_date": last_day_last_month.isoformat(),
            "total_revenue": total
        }

    def orders_per_customer(self) -> List[Dict]:
        """Return total orders per customer."""
        resp = self._sb.table("orders").select("cust_id").execute()
        if not resp.data:
            return []

        counts = {}
        for order in resp.data:
            cid = order["cust_id"]
            if cid is not None:
                counts[cid] = counts.get(cid, 0) + 1
        
        if not counts:
            return []

        cust_resp = self._sb.table("customers").select("cust_id, name").in_("cust_id", list(counts.keys())).execute()
        customer_names = {c["cust_id"]: c["name"] for c in cust_resp.data}

        return [
            {"cust_id": cid, "name": customer_names.get(cid, f"Unknown Customer {cid}"), "total_orders": count}
            for cid, count in counts.items()
        ]

    def frequent_customers(self, min_orders: int = 2) -> List[Dict]:
        """Return customers who placed at least a minimum number of orders."""
        all_customers_orders = self.orders_per_customer()
        return [c for c in all_customers_orders if c["total_orders"] >= min_orders]