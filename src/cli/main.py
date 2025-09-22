# src/cli/main.py
import argparse
import json
from src.services.product_service import ProductService, ProductError
from src.dao.product_dao import ProductDAO
from src.services.customer_service import CustomerService, CustomerError
from src.services.order_service import OrderService, OrderError
from src.services.payment_service import PaymentService, PaymentError
from src.services.reporting_service import ReportingService

class RetailCLI:
    """CLI for retail management."""

    def __init__(self):
        self.product_service = ProductService()
        self.product_dao = ProductDAO()
        self.customer_service = CustomerService()
        self.order_service = OrderService()
        self.payment_service = PaymentService()
        self.reporting_service = ReportingService()

    def _print_json(self, data):
        """Helper to print JSON nicely."""
        print(json.dumps(data, indent=2, default=str))

    # ---------------- Product Commands ----------------
    def cmd_product_add(self, args):
        try:
            p = self.product_service.add_product(args.name, args.sku, args.price, args.stock, args.category)
            print("Product created:")
            self._print_json(p)
        except ProductError as e:
            print(f"Error: {e}")

    def cmd_product_list(self, args):
        ps = self.product_dao.list_products(limit=100)
        self._print_json(ps)

    # ---------------- Customer Commands ----------------
    def cmd_customer_add(self, args):
        try:
            c = self.customer_service.create_customer(args.name, args.email, args.phone, args.city)
            print("Customer created:")
            self._print_json(c)
        except CustomerError as e:
            print(f"Error: {e}")

    def cmd_customer_update(self, args):
        try:
            c = self.customer_service.update_customer(args.customer, phone=args.phone, city=args.city)
            print("Customer updated:")
            self._print_json(c)
        except CustomerError as e:
            print(f"Error: {e}")

    def cmd_customer_delete(self, args):
        try:
            c = self.customer_service.delete_customer(args.customer)
            print("Customer deleted:")
            self._print_json(c)
        except CustomerError as e:
            print(f"Error: {e}")

    def cmd_customer_list(self, args):
        cs = self.customer_service.list_customers()
        self._print_json(cs)

    def cmd_customer_search(self, args):
        cs = self.customer_service.search_customers(email=args.email, city=args.city)
        self._print_json(cs)

    # ---------------- Order Commands ----------------
    def cmd_order_create(self, args):
        items = []
        for item_str in args.item:
            try:
                pid, qty = item_str.split(":")
                items.append({"prod_id": int(pid), "quantity": int(qty)})
            except ValueError:
                print(f"Invalid item format: '{item_str}'. Use 'product_id:quantity'.")
                return
        try:
            order = self.order_service.create_order(args.customer, items)
            print("Order created:")
            self._print_json(order)
        except OrderError as e:
            print(f"Error: {e}")

    def cmd_order_show(self, args):
        try:
            order = self.order_service.get_order_details(args.order)
            self._print_json(order)
        except OrderError as e:
            print(f"Error: {e}")

    def cmd_order_cancel(self, args):
        try:
            order = self.order_service.cancel_order(args.order)
            print("Order cancelled:")
            self._print_json(order)
        except OrderError as e:
            print(f"Error: {e}")

    # ---------------- Payment Commands ----------------
    def cmd_payment_process(self, args):
        try:
            payment = self.payment_service.process_payment(args.order, args.method)
            print("Payment processed:")
            self._print_json(payment)
        except (PaymentError, OrderError) as e:
            print(f"Error: {e}")

    # ---------------- Reporting Commands ----------------
    def cmd_report_top_products(self, args):
        report = self.reporting_service.top_selling_products()
        self._print_json(report)

    def cmd_report_revenue_last_month(self, args):
        report = self.reporting_service.total_revenue_last_month()
        self._print_json(report)

    def cmd_report_orders_per_customer(self, args):
        report = self.reporting_service.orders_per_customer()
        self._print_json(report)

    def cmd_report_frequent_customers(self, args):
        report = self.reporting_service.frequent_customers(min_orders=args.min_orders)
        self._print_json(report)

    # ---------------- CLI Parser ----------------
    def build_parser(self):
        parser = argparse.ArgumentParser(prog="retail-cli", description="A CLI to manage a retail system.")
        subparsers = parser.add_subparsers(dest="command", required=True)

        # Product parser
        p_prod = subparsers.add_parser("product", help="Manage products")
        prod_sub = p_prod.add_subparsers(dest="action", required=True)
        add_p = prod_sub.add_parser("add", help="Add a new product")
        add_p.add_argument("--name", required=True)
        add_p.add_argument("--sku", required=True)
        add_p.add_argument("--price", type=float, required=True)
        add_p.add_argument("--stock", type=int, default=0)
        add_p.add_argument("--category")
        add_p.set_defaults(func=self.cmd_product_add)
        list_p = prod_sub.add_parser("list", help="List all products")
        list_p.set_defaults(func=self.cmd_product_list)

        # Customer parser
        p_cust = subparsers.add_parser("customer", help="Manage customers")
        cust_sub = p_cust.add_subparsers(dest="action", required=True)
        add_c = cust_sub.add_parser("add", help="Add a new customer")
        add_c.add_argument("--name", required=True)
        add_c.add_argument("--email", required=True)
        add_c.add_argument("--phone", required=True)
        add_c.add_argument("--city")
        add_c.set_defaults(func=self.cmd_customer_add)
        update_c = cust_sub.add_parser("update", help="Update a customer's details")
        update_c.add_argument("customer", type=int, help="Customer ID")
        update_c.add_argument("--phone")
        update_c.add_argument("--city")
        update_c.set_defaults(func=self.cmd_customer_update)
        del_c = cust_sub.add_parser("delete", help="Delete a customer")
        del_c.add_argument("customer", type=int, help="Customer ID")
        del_c.set_defaults(func=self.cmd_customer_delete)
        list_c = cust_sub.add_parser("list", help="List all customers")
        list_c.set_defaults(func=self.cmd_customer_list)
        search_c = cust_sub.add_parser("search", help="Search for customers")
        search_c.add_argument("--email")
        search_c.add_argument("--city")
        search_c.set_defaults(func=self.cmd_customer_search)

        # Order parser
        p_order = subparsers.add_parser("order", help="Manage orders")
        order_sub = p_order.add_subparsers(dest="action", required=True)
        create_o = order_sub.add_parser("create", help="Create a new order")
        create_o.add_argument("--customer", type=int, required=True, help="Customer ID")
        create_o.add_argument("--item", required=True, nargs="+", help="Item in 'prod_id:qty' format (can be repeated)")
        create_o.set_defaults(func=self.cmd_order_create)
        show_o = order_sub.add_parser("show", help="Show details of a specific order")
        show_o.add_argument("order", type=int, help="Order ID")
        show_o.set_defaults(func=self.cmd_order_show)
        cancel_o = order_sub.add_parser("cancel", help="Cancel an order")
        cancel_o.add_argument("order", type=int, help="Order ID")
        cancel_o.set_defaults(func=self.cmd_order_cancel)

        # Payment parser
        p_pay = subparsers.add_parser("payment", help="Manage payments")
        pay_sub = p_pay.add_subparsers(dest="action", required=True)
        pay_process = pay_sub.add_parser("process", help="Process payment for an order")
        pay_process.add_argument("order", type=int, help="Order ID")
        pay_process.add_argument("--method", type=str, choices=["Cash", "Card", "UPI"], required=True)
        pay_process.set_defaults(func=self.cmd_payment_process)

        # Reporting parser
        p_rep = subparsers.add_parser("report", help="Generate reports")
        rep_sub = p_rep.add_subparsers(dest="action", required=True)
        rep_sub.add_parser("top_products", help="Show top selling products").set_defaults(func=self.cmd_report_top_products)
        rep_sub.add_parser("revenue_last_month", help="Show total revenue from last month").set_defaults(func=self.cmd_report_revenue_last_month)
        rep_sub.add_parser("orders_per_customer", help="Show order counts per customer").set_defaults(func=self.cmd_report_orders_per_customer)
        freq_cust = rep_sub.add_parser("frequent_customers", help="Show frequent customers")
        freq_cust.add_argument("--min_orders", type=int, default=2, help="Minimum number of orders")
        freq_cust.set_defaults(func=self.cmd_report_frequent_customers)

        return parser

    def run(self):
        parser = self.build_parser()
        args = parser.parse_args()
        args.func(args)

def main():
    try:
        cli = RetailCLI()
        cli.run()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()