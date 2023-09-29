# Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import (
    make_purchase_invoice,
)
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_stock_entry


class S4SPurchase(Document):
    def validate(self):
        buying_price_list = frappe.db.get_single_value(
            "Buying Settings", "buying_price_list"
        )
        if buying_price_list:
            for row in self.purchase_receipt_details:
                price_list_rate = frappe.db.get_value(
                    "Item Price",
                    {"item_code": row.item_code, "price_list": buying_price_list},
                    "price_list_rate",
                )
                if price_list_rate:
                    if row.rate > price_list_rate:
                        frappe.throw(
                            "Rate offered price for {0} must be less than {1}".format(
                                row.item_code, price_list_rate
                            )
                        )

    def before_save(self):
        if not self.total_amount:
            total_weight = 0.00
            for i in self.receipt_details:
                total_weight += i.weight_in_kg
            self.total_weight = total_weight
            if self.kadta:
                self.kadta_weight = (total_weight * int(self.kadta)) / 100
                self.weight_after_kadta = total_weight - (
                    (total_weight * int(self.kadta)) / 100
                )
                self.total_amount = (
                    total_weight - ((total_weight * int(self.kadta)) / 100)
                ) * self.purchase_receipt_details[0].rate
        total = 0.00
        if len(self.taxes) != 0:
            for i in self.taxes:
                total += i.tax_amount
            self.total_deduction_amount = total
        if not self.grand_total:
            self.grand_total = self.total_amount - total

        if self.s4s_farmer_query and frappe.db.exists(
            "S4S Farmer Query", self.s4s_farmer_query
        ):
            fq_doc = frappe.get_doc("S4S Farmer Query", self.s4s_farmer_query)
            print(fq_doc)
            if fq_doc.status != "Pending":
                fq_doc = "Pending"
                if isinstance(
                    fq_doc, frappe.model.document.Document
                ):  # Check if fq_doc is a Document object
                    fq_doc.save()
                # fq_doc.save()

    def on_update_after_submit(self):
        s4s_utr = None
        fpo_utr = None
        s4s_pay = None
        fpo_pay = None

        if self.s4s_utr_no and (self.s4s_utr_no.isspace() == False):
            s4s_utr = True
        if self.fpo_utr_no and (self.fpo_utr_no.isspace() == False):
            fpo_utr = True
        if self.s4s_payment_no and (self.s4s_payment_no.isspace() == False):
            s4s_pay = True
        if self.fpo_payment_no and (self.fpo_payment_no.isspace() == False):
            fpo_pay = True

        if s4s_utr and fpo_utr and s4s_pay and fpo_pay:
            frappe.db.set_value("S4S Purchase", self.name, "payment_status", "Paid")
            self.payment_status = "Paid"

    def on_submit(self):
        if self.s4s_farmer_query and frappe.db.exists(
            "S4S Farmer Query", self.s4s_farmer_query
        ):
            fq_doc = frappe.get_doc("S4S Farmer Query", self.s4s_farmer_query)
            if fq_doc.status != "Completed":
                fq_doc = "Completed"
                if isinstance(fq_doc, frappe.model.document.Document):
                    fq_doc.save()

    @frappe.whitelist()
    def value_fetch(self, user):
        if frappe.db.exists("S4S User details", user):
            user = frappe.get_doc("S4S User details", user)
            self.set_warehouse = user.inward_warehouse

    # @frappe.whitelist()
    # def copy_data1(self):
    # 	purchase_temp = frappe.get_doc("Purchase Taxes and Charges Template","Supplier Deduction - SFSTS")
    # 	self.supplier_deductions = "Supplier Deduction - SFSTS"
    # 	self.taxes = purchase_temp.taxes

    @frappe.whitelist()
    def copy_data2(self, s_deduct):
        purchase_temp = frappe.get_doc("Purchase Taxes and Charges Template", s_deduct)
        self.taxes = purchase_temp.taxes

    @frappe.whitelist()
    def make_docs(self, user):
        make_purchase_receipt(self, user)

    @frappe.whitelist()
    def get_s4s_user_details(self):
        if frappe.session.user != "Administrator":
            if frappe.db.get_value(
                "S4S User details", {"user_id": frappe.session.user}, ["name"]
            ):
                usr_details = frappe.get_doc(
                    "S4S User details", {"user_id": frappe.session.user}
                )
                taluka = ""
                district = ""
                state = ""
                warehouse = ""

                if usr_details.taluka:
                    taluka = usr_details.taluka
                if usr_details.district:
                    district = usr_details.district
                if usr_details.state:
                    state = usr_details.state
                if usr_details.inward_warehouse:
                    warehouse = usr_details.inward_warehouse

                return {
                    "taluka": taluka,
                    "district": district,
                    "state": state,
                    "wh": warehouse,
                }

            else:
                return "No"

        else:
            return "No"

    @frappe.whitelist()
    def get_supplier_deductions(self, company):
        supplier_deductions = frappe.db.get_value(
            "Purchase Taxes and Charges Template",
            {"title": ["like", "%Supplier Deduction%"], "company": company},
            ["name"],
        )
        return supplier_deductions

    @frappe.whitelist()
    def set_options(self):
        usr = frappe.get_doc("User", frappe.session.user)
        usr_list = []
        for i in usr.roles:
            usr_list.append(i.role)

        if "System Manager" in usr_list:
            options = [
                "Pending for Approval",
                "Approved by CC Manager",
                "Rejected by CC Manager",
                "Approved by Area Manager",
                "Rejected by Area Manager",
            ]
            set_ro = False

        else:
            options = []
            set_ro = True

            if "CC User" not in usr_list and "Area Manager" not in usr_list:
                set_ro = True

            if "CC User" in usr_list and self.approved_status == "Pending for Approval":
                options.extend(
                    [
                        "Pending for Approval",
                        "Approved by CC Manager",
                        "Rejected by CC Manager",
                    ]
                )
                set_ro = False
            else:
                set_ro = True

            if "Area Manager" in usr_list and self.approved_status in [
                "Approved by CC Manager",
                "Rejected by CC Manager",
            ]:
                options.extend(
                    [
                        self.approved_status,
                        "Approved by Area Manager",
                        "Rejected by Area Manager",
                    ]
                )
                set_ro = False

            if "Area Manager" in usr_list and self.approved_status in [
                "Approved by Area Manager",
                "Rejected by Area Manager",
            ]:
                set_ro = True

        return {"options": options, "ro": set_ro}


def make_purchase_receipt(self, user):
    doc = frappe.new_doc("Purchase Receipt")
    doc.supplier = self.supplier
    doc.company = self.company
    doc.vlcc_name = self.vlcc_name
    doc.cc_name = self.cc_name
    doc.village = self.village
    doc.taluka = self.taluka
    doc.district = self.district
    doc.set_warehouse = self.set_warehouse
    doc.s4s_purchase = self.name
    doc.append(
        "items",
        {
            "item_code": self.purchase_receipt_details[0].item_code,
            "qty": self.total_weight,
            "variety": self.purchase_receipt_details[0].variety,
            "moisture_content": self.purchase_receipt_details[0].moisture,
            "rate": self.total_amount / self.total_weight,
            "cost_center": "",
        },
    )
    doc.taxes_and_charges = self.supplier_deductions
    # doc.taxes = []
    doc.taxes = self.taxes
    doc.save(ignore_permissions=True)
    print("purchase receipt")
    # for pr in doc.taxes:
    # 	print(pr.tax_amount)
    # 	for sp in self.taxes:
    # 		if pr.account_head == sp.account_head:
    # 			pr.tax_amount = sp.tax_amount
    # doc.save()
    doc.submit()
    # CODE COMMENTED FOR PURCHASE INVOICE CREATION
    # pi = make_purchase_invoice(doc.name)
    # pi.save(ignore_permissions=True)
    # pi.submit()
    # print("done purchase invoice")

    rm_tfr_doc = None

    if frappe.db.exists("S4S User details", user) and not frappe.db.get_value(
        "RM Transfer VLCC To CC", {"s4s_purchase": self.name}, ["name"]
    ):
        usr_det = frappe.get_doc("S4S User details", frappe.session.user)

        if usr_det.transit_warehouse:
            rm_doc = frappe.new_doc("RM Transfer VLCC To CC")
            rm_doc.supplier = self.supplier
            rm_doc.supplier_name = self.supplier_name
            rm_doc.vlcc_name = self.vlcc_name
            rm_doc.cc_name = self.cc_name
            rm_doc.village = self.village
            rm_doc.taluka = self.taluka
            rm_doc.district = self.district
            rm_doc.state = self.state
            rm_doc.company = self.company
            rm_doc.vehicle_no = self.vehicle_no
            rm_doc.vehicle_model = self.vehicle_model
            rm_doc.driver_mobile_number = self.driver_mobile_number
            rm_doc.driver_name = self.driver_name
            rm_doc.vlcc_warehouse = frappe.db.get_value(
                "Purchase Receipt", {"name": doc.name}, ["set_warehouse"]
            )
            rm_doc.cc_warehouse = usr_det.transit_warehouse
            rm_doc.s4s_purchase = self.name
            # rm_doc.vehicle_model =
            # rm_doc.driver_mobile_number =
            # rm_doc.e_way_bill_no =
            pr = frappe.get_doc("Purchase Receipt", doc.name)
            for i in pr.items:
                rm_doc.append(
                    "rm_item_details",
                    {
                        "item_code": i.item_code,
                        "item_name": i.item_name,
                        "qty": i.qty,
                        "batch": i.batch_no,
                        "uom": i.uom,
                    },
                )
            rm_doc.save(ignore_permissions=True)
            rm_tfr_doc = rm_doc.name

    if frappe.db.exists("S4S User details", user):
        get_user = frappe.get_doc("S4S User details", user)
        if get_user.transit_warehouse:
            se = make_stock_entry(doc.name)
            se.vlcc_name = self.vlcc_name
            se.cc_name = self.cc_name
            se.village = self.village
            se.taluka = self.taluka
            se.district = self.district
            se.from_warehouse = doc.set_warehouse
            se.to_warehouse = get_user.transit_warehouse
            se.add_to_transit = 1
            se.s4ssupplier = doc.supplier
            se.purchase_rate = self.total_amount / self.total_weight
            if rm_tfr_doc:
                se.rm_transfer_vlcc_to_cc = rm_tfr_doc
            se.save(ignore_permissions=True)
            se_up = frappe.get_doc("Stock Entry", se.name)
            se_up.rm_transfer_vlcc_to_cc = rm_tfr_doc
            # se.submit()

        if frappe.db.get_value(
            "Stock Entry Detail", {"reference_purchase_receipt": doc.name}, ["parent"]
        ):
            se_name = frappe.db.get_value(
                "Stock Entry Detail",
                {"reference_purchase_receipt": doc.name},
                ["parent"],
            )
            frappe.db.sql(
                f"""
				update `tabStock Entry` set custom_supplier = '{self.supplier}', custom_supplier_name = '{self.supplier_name}', s4ssupplier = '', me_name = '', is_s4s_purchase = 1
				where name = '{se_name}'
			"""
            )
