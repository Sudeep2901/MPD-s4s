# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.contacts.doctype.address.address import get_address_display


class FPOPurchaseOrder(Document):
    @frappe.whitelist()
    def set_company_address(self, company):
        query = frappe.db.sql(
            f"""
			select address.name, link.link_name from `tabAddress` as address join `tabDynamic Link` as link on link.parent = address.name and address.is_your_company_address = 1
			where link.link_doctype = 'Company' and link.link_name = '{company}'
		""",
            as_dict=1,
        )

        if len(query) > 0:
            for row in query:
                return row

    def before_submit(self):
        self.create_sales_order()

    @frappe.whitelist()
    def create_sales_order(self):
        if not frappe.db.get_value("Sales Order", {"po_no": self.name}, ["name"]):
            settings = frappe.get_doc("S4S Inter Company Settings")
            so_company, so_customer, setting_suppliers = "", "", []
            selling_setting = frappe.get_doc("Selling Settings")

            for row in settings.inter_company_details:
                if self.supplier_name == row.company:
                    so_company = row.company
                    if row.customer:
                        if (
                            frappe.db.get_value(
                                "Customer", {"name": row.customer}, ["customer_name"]
                            )
                            == self.company
                        ):
                            so_customer = row.customer
                    break

            customer_address = frappe.db.get_value(
                "Dynamic Link",
                {
                    "parenttype": "Address",
                    "link_name": so_customer,
                    "link_doctype": "Customer",
                },
                ["parent"],
            )

            cust_addr_doc = frappe.get_doc("Address", customer_address)
            cust_address_display = get_address_display(cust_addr_doc.as_dict())

            comp_addr_doc = frappe.get_doc(
                "Address", {"company": so_company, "is_your_company_address": 1}
            )
            comp_address_display = get_address_display(comp_addr_doc.as_dict())

            fpo_dict = self.as_dict()
            del fpo_dict["address_display"]
            del fpo_dict["name"]
            del fpo_dict["naming_series"]
            del fpo_dict["shipping_address"]
            del fpo_dict["docstatus"]
            del fpo_dict["doctype"]
            del fpo_dict["owner"]
            del fpo_dict["creation"]

            so = frappe.new_doc("Sales Order")
            so.update(fpo_dict)
            so.update(
                {
                    "company": so_company,
                    "customer": so_customer,
                    "delivery_date": self.to_date1,
                    "po_no": self.name,
                    "transaction_date": self.transaction_date,
                    "po_date": self.transaction_date,
                    "company_address": comp_addr_doc.name,
                    "company_address_display": comp_address_display,
                    "customer_address": customer_address,
                    "address_display": cust_address_display,
                }
            )

            items_updated = [
                x.update({"delivery_date": self.to_date1})
                for x in so.as_dict()["items"]
            ]

            so.update({"items": items_updated})

            so.flags.ignore_validate = True

            so.save(ignore_permissions=True)
