# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils.data import flt


class VLCCRMIn(Document):
    def before_save(self):
        if self.rm_transfer_vlcc_to_cc:
            doc = frappe.get_doc("RM Transfer VLCC To CC", self.rm_transfer_vlcc_to_cc)
            doc.transport_status = "Delivered"
            doc.save(ignore_permissions=True)

    def validate(self):
        self.validate_qty()
        self.validate_target_wh()

    def validate_qty(self):
        for row in self.rm_item_details:
            if row.sent_qty != row.qty:
                frappe.throw(
                    title="Quantity Not Equal",
                    msg=f"Sent Qty and Received Qty not Equal in row {frappe.bold(row.idx)}.",
                )

    def validate_target_wh(self):
        if not self.target_warehouse or self.target_warehouse == "":
            frappe.throw("Enter Target Warehouse!")

    def on_submit(self):
        st_en = frappe.db.get_value(
            "Stock Entry",
            {"rm_transfer_vlcc_to_cc": self.rm_transfer_vlcc_to_cc},
            ["name"],
        )
        self.make_stock_in_entry(st_en)

    @frappe.whitelist()
    def make_stock_in_entry(self, source_name, target_doc=None):
        def set_missing_values(source, target):
            target.set_stock_entry_type()
            target.set_missing_values()

        def update_item(source_doc, target_doc, source_parent):
            target_doc.t_warehouse = ""

            if source_doc.material_request_item and source_doc.material_request:
                add_to_transit = frappe.db.get_value(
                    "Stock Entry", source_name, "add_to_transit"
                )
                if add_to_transit:
                    warehouse = frappe.get_value(
                        "Material Request Item",
                        source_doc.material_request_item,
                        "warehouse",
                    )
                    target_doc.t_warehouse = warehouse

            target_doc.s_warehouse = source_doc.t_warehouse
            target_doc.qty = source_doc.qty - source_doc.transferred_qty

        doclist = get_mapped_doc(
            "Stock Entry",
            source_name,
            {
                "Stock Entry": {
                    "doctype": "Stock Entry",
                    "field_map": {"name": "outgoing_stock_entry"},
                    "validation": {"docstatus": ["=", 1]},
                },
                "Stock Entry Detail": {
                    "doctype": "Stock Entry Detail",
                    "field_map": {
                        "name": "ste_detail",
                        "parent": "against_stock_entry",
                        "serial_no": "serial_no",
                        "batch_no": "batch_no",
                    },
                    "postprocess": update_item,
                    "condition": lambda doc: flt(doc.qty) - flt(doc.transferred_qty)
                    > 0.01,
                },
            },
            target_doc,
            set_missing_values,
        )

        doclist.update(
            {
                "to_warehouse": self.target_warehouse,
                "from_warehouse": self.source_warehouse,
                "vlcc_rm_in": self.name,
            }
        )

        doclist.save(ignore_permissions=True)
        doclist.submit()
        # return doclist
