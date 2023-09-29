# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RMTransferVLCCToCC(Document):
    def on_submit(self):
        self.transport_status = "In Transit"
        self.sumbit_stock_entry()

    def sumbit_stock_entry(self):
        if frappe.db.get_value(
            "Stock Entry", {"rm_transfer_vlcc_to_cc": self.name}, ["name"]
        ):
            se = frappe.get_doc("Stock Entry", {"rm_transfer_vlcc_to_cc": self.name})
            se.submit()

    @frappe.whitelist()
    def check_roles(self):
        role, doc_created = None, None

        roles_lst = []
        user = frappe.get_doc("User", frappe.session.user)
        for i in user.roles:
            roles_lst.append(i.role)

        if ("System Manager" in roles_lst) or ("CC User" in roles_lst):
            role = True

        if not frappe.db.get_value(
            "VLCC RM In",
            {"rm_transfer_vlcc_to_cc": self.name, "docstatus": ["!=", 2]},
            ["name"],
        ):
            doc_created = True

        if role and doc_created:
            return "Success"


@frappe.whitelist()
def make_vlcc_rm_in(source_name, target_doc=None):
    doc = frappe.get_doc("RM Transfer VLCC To CC", source_name)
    vri = frappe.new_doc("VLCC RM In")
    vri.supplier = doc.supplier
    vri.supplier_name = doc.supplier_name
    vri.vlcc_name = doc.vlcc_name
    vri.cc_name = doc.cc_name
    vri.village = doc.village
    vri.taluka = doc.taluka
    vri.district = doc.district
    vri.state = doc.state
    vri.company = doc.company
    vri.vehicle_no = doc.vehicle_no
    vri.driver_name = doc.driver_name
    vri.rm_transfer_vlcc_to_cc = doc.name
    vri.source_warehouse = doc.cc_warehouse
    if frappe.db.get_value(
        "S4S User details", {"name": frappe.session.user}, ["inward_warehouse"]
    ):
        vri.target_warehouse = frappe.db.get_value(
            "S4S User details", {"name": frappe.session.user}, ["inward_warehouse"]
        )

    for i in doc.rm_item_details:
        vri.append(
            "rm_item_details",
            {
                "item_code": i.item_code,
                "item_name": i.item_name,
                "sent_qty": i.qty,
                "qty": i.qty,
                "uom": i.uom,
                "batch": i.batch,
                "remark": i.remarks,
                "no_of_bags": i.no_of_bags,
            },
        )

    vri.vehicle_no = doc.vehicle_no
    vri.vehicle_model = doc.vehicle_model
    vri.driver_name = doc.driver_name
    vri.driver_mobile_number = doc.driver_mobile_number
    vri.e_way_bill_no = doc.e_way_bill_no

    return vri
