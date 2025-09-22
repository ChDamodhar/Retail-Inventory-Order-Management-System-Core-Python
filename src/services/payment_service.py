from datetime import datetime
from src.dao.payment_dao import PaymentDAO
from src.dao.order_dao import OrderDAO


class PaymentService:
    def __init__(self):
        self.payment_dao = PaymentDAO()
        self.order_dao = OrderDAO()

    def _convert_datetime(self, obj):
        """Recursively convert datetime objects in dicts/lists to ISO strings."""
        from datetime import datetime
        if isinstance(obj, dict):
            return {k: self._convert_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_datetime(v) for v in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    def create_payment(self, order_id: int, amount: float):
        """Insert pending payment when order is created."""
        payment = self.payment_dao.create_payment(order_id, amount)
        return self._convert_datetime(payment)

    def process_payment(self, order_id: int, method: str):
        """Mark payment as PAID and update order to COMPLETED."""
        payment = self.payment_dao.update_payment(order_id, "PAID", method, datetime.utcnow())
        self.order_dao.update_order_status(order_id, "COMPLETED")
        return self._convert_datetime(payment)

    def refund_payment(self, order_id: int):
        """Mark payment as REFUNDED if order cancelled."""
        payment = self.payment_dao.update_payment(order_id, "REFUNDED")
        return self._convert_datetime(payment)