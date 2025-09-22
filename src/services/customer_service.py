from typing import List, Dict, Optional
from src.dao.customer_dao import CustomerDAO


class CustomerError(Exception):
    pass

class CustomerService:

    def __init__(self):
        self.customer_dao = CustomerDAO()

    def create_customer(self, name: str, email: str, phone: str, city: Optional[str] = None) -> Dict:
        try:
            return self.customer_dao.create_customer(name, email, phone, city)
        except ValueError as e:
            raise CustomerError(str(e))

    def update_customer(self, cust_id: int, phone: Optional[str] = None, city: Optional[str] = None) -> Dict:
        fields = {}
        if phone:
            fields["phone"] = phone
        if city:
            fields["city"] = city
        if not fields:
            raise CustomerError("No fields to update")
        return self.customer_dao.update_customer(cust_id, fields)

    def delete_customer(self, cust_id: int) -> Dict:
        try:
            return self.customer_dao.delete_customer(cust_id)
        except ValueError as e:
            raise CustomerError(str(e))

    def list_customers(self) -> List[Dict]:
        return self.customer_dao.list_customers()

    def search_customers(self, email: Optional[str] = None, city: Optional[str] = None) -> List[Dict]:
        return self.customer_dao.search_customers(email=email, city=city)