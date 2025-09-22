from typing import Optional, List, Dict
from src.config import get_supabase


class CustomerDAO:
    """Data Access Object for customers table."""

    def __init__(self):
        self._sb = get_supabase()

    def create_customer(self, name: str, email: str, phone: str, city: Optional[str] = None) -> Optional[Dict]:
        # Check for unique email
        if self.get_customer_by_email(email):
            raise ValueError(f"Email already exists: {email}")

        payload = {"name": name, "email": email, "phone": phone}
        if city:
            payload["city"] = city

        self._sb.table("customers").insert(payload).execute()
        resp = self._sb.table("customers").select("*").eq("email", email).limit(1).execute()
        return resp.data[0] if resp.data else None

    def get_customer_by_id(self, cust_id: int) -> Optional[Dict]:
        resp = self._sb.table("customers").select("*").eq("cust_id", cust_id).limit(1).execute()
        return resp.data[0] if resp.data else None

    def get_customer_by_email(self, email: str) -> Optional[Dict]:
        resp = self._sb.table("customers").select("*").eq("email", email).limit(1).execute()
        return resp.data[0] if resp.data else None

    def update_customer(self, cust_id: int, fields: Dict) -> Optional[Dict]:
        self._sb.table("customers").update(fields).eq("cust_id", cust_id).execute()
        resp = self._sb.table("customers").select("*").eq("cust_id", cust_id).limit(1).execute()
        return resp.data[0] if resp.data else None

    def delete_customer(self, cust_id: int) -> Optional[Dict]:
        # Check if customer has orders
        resp_orders = self._sb.table("orders").select("*").eq("cust_id", cust_id).limit(1).execute()
        if resp_orders.data:
            raise ValueError("Cannot delete customer: orders exist")

        resp_before = self._sb.table("customers").select("*").eq("cust_id", cust_id).limit(1).execute()
        row = resp_before.data[0] if resp_before.data else None
        self._sb.table("customers").delete().eq("cust_id", cust_id).execute()
        return row

    def list_customers(self, limit: int = 100) -> List[Dict]:
        resp = self._sb.table("customers").select("*").order("cust_id", desc=False).limit(limit).execute()
        return resp.data or []

    def search_customers(self, email: Optional[str] = None, city: Optional[str] = None) -> List[Dict]:
        q = self._sb.table("customers").select("*")
        if email:
            q = q.ilike("email", f"%{email}%")
        if city:
            q = q.ilike("city", f"%{city}%")
        resp = q.execute()
        return resp.data or []