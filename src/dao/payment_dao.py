from src.config import get_supabase
from datetime import datetime
from typing import Optional, Dict, Any, Union, List


class PaymentDAO:
    def __init__(self):
        self._sb = get_supabase()

    def _convert_datetime(self, obj: Any) -> Any:
        """Recursively convert datetime objects to ISO strings."""
        if isinstance(obj, dict):
            return {k: self._convert_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_datetime(v) for v in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    def create_payment(self, order_id: int, amount: float) -> Optional[Dict]:
        payload = {
            "order_id": order_id,
            "amount": amount,
            "status": "PENDING"
        }
        self._sb.table("payments").insert(payload).execute()
        resp = (
            self._sb.table("payments")
            .select("*")
            .eq("order_id", order_id)
            .limit(1)
            .execute()
        )
        return self._convert_datetime(resp.data[0]) if resp.data else None

    def update_payment(
        self,
        order_id: int,
        status: str,
        method: Optional[str] = None,
        paid_at: Optional[Union[datetime, str]] = None,
    ) -> Optional[Dict]:
        payload = {"status": status}
        if method:
            payload["method"] = method
        if paid_at:
            # Store ISO string if datetime passed
            if isinstance(paid_at, datetime):
                payload["paid_at"] = paid_at.isoformat()
            else:
                payload["paid_at"] = paid_at

        self._sb.table("payments").update(payload).eq("order_id", order_id).execute()
        resp = (
            self._sb.table("payments")
            .select("*")
            .eq("order_id", order_id)
            .limit(1)
            .execute()
        )
        return self._convert_datetime(resp.data[0]) if resp.data else None

    def get_payment(self, order_id: int) -> Optional[Dict]:
        resp = (
            self._sb.table("payments")
            .select("*")
            .eq("order_id", order_id)
            .limit(1)
            .execute()
        )
        return self._convert_datetime(resp.data[0]) if resp.data else None