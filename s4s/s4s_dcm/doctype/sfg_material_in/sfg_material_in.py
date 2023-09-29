# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import collections
from frappe.model.document import Document


class SFGMaterialIn(Document):
    def validate(self):
        for row in self.rm_item_details:
            if row.sent_qty != row.qty + row.rejected_qty:
                frappe.throw(
                    f"Sent Qty not equal to Received Qty and Rejected Qty in row {frappe.bold(row.idx)}."
                )

    def on_submit(self):
        self.make_stock_entry()

    def before_save(self):
        self.item_duplicate_validation()

    def item_duplicate_validation(self):
        batches = []
        all = []
        for j in self.rm_item_details:
            all.append(j.batch)
        dup = [item for item, count in collections.Counter(all).items() if count > 1]

        for i in self.rm_item_details:
            batches.append(i.batch)
        if len(batches) != len(set(batches)):
            if len(dup) == 1:
                frappe.throw(f"Batch {dup[0]} Duplicated")
            if len(dup) > 1:
                frappe.throw(
                    title="Following Batches are duplicated:", msg=dup, as_list=True
                )

    def make_stock_entry(self):
        if self.material_transfer_wh_to_wh:
            ref_stock_entry = frappe.db.get_value(
                "Stock Entry",
                {
                    "sfg_dispatch_request": self.material_transfer_wh_to_wh,
                    "docstatus": 1,
                },
                ["name"],
            )
            if not frappe.db.get_value(
                "Stock Entry",
                {"outgoing_stock_entry": ref_stock_entry, "docstatus": 1},
                ["name"],
            ):
                doc = frappe.new_doc("Stock Entry")
                doc.company = self.company
                doc.dcm_name = self.dcm_name
                doc.dcm_location = self.dcm_location
                doc.stock_entry_type = self.stock_entry_type
                doc.outgoing_stock_entry = ref_stock_entry
                doc.sfg_material_in = self.name
                doc.sfg_dispatch_request1 = self.material_transfer_wh_to_wh
                doc.from_warehouse = self.rm_warehouse
                doc.to_warehouse = self.wip_warehouse
                for row in self.rm_item_details:
                    doc.append(
                        "items",
                        {
                            "s_warehouse": self.rm_warehouse,
                            "t_warehouse": self.wip_warehouse,
                            "item_code": row.item_code,
                            "batch_no": row.batch,
                            "uom": row.uom,
                            "qty": row.qty,
                            "basic_rate": frappe.db.get_value(
                                "Stock Entry Detail",
                                {
                                    "parent": ref_stock_entry,
                                    "item_code": row.item_code,
                                    "batch_no": row.batch,
                                },
                                ["basic_rate"],
                            ),
                        },
                    )
                doc.save(ignore_permissions=True)
                doc.submit()

            rej_items = []
            rej_entry = frappe.new_doc("Stock Entry")
            rej_entry.company = self.company
            rej_entry.dcm_name = self.dcm_name
            rej_entry.dcm_location = self.dcm_location
            rej_entry.stock_entry_type = "Material Issue"
            rej_entry.sfg_material_in = self.name
            rej_entry.sfg_dispatch_request1 = self.material_transfer_wh_to_wh
            rej_entry.from_warehouse = self.rm_warehouse
            for line in self.rm_item_details:
                if line.rejected_qty > 0:
                    rej_items.append(line.item_code)
                    rej_entry.append(
                        "items",
                        {
                            "s_warehouse": self.rm_warehouse,
                            "item_code": line.item_code,
                            "batch_no": line.batch,
                            "uom": line.uom,
                            "qty": line.rejected_qty,
                            "basic_rate": frappe.db.get_value(
                                "Stock Entry Detail",
                                {
                                    "parent": ref_stock_entry,
                                    "item_code": line.item_code,
                                    "batch_no": line.batch,
                                },
                                ["basic_rate"],
                            ),
                        },
                    )
            if len(rej_items) != 0:
                rej_entry.save(ignore_permissions=True)
                rej_entry.submit()
            else:
                pass

        if self.me_sfg_dispatch_note:
            ref_stock_entry = frappe.db.get_value(
                "Stock Entry",
                {"me_sfg_dispatch_note": self.me_sfg_dispatch_note, "docstatus": 1},
                ["name"],
            )
            if not frappe.db.get_value(
                "Stock Entry",
                {"outgoing_stock_entry": ref_stock_entry, "docstatus": 1},
                ["name"],
            ):
                doc = frappe.new_doc("Stock Entry")
                doc.company = self.company
                doc.dcm_name = self.dcm_name
                doc.dcm_location = self.dcm_location
                doc.stock_entry_type = self.stock_entry_type
                doc.outgoing_stock_entry = ref_stock_entry
                doc.sfg_material_in = self.name
                doc.me_sfg_dispatch_note = self.me_sfg_dispatch_note
                doc.from_warehouse = self.rm_warehouse
                doc.to_warehouse = self.wip_warehouse
                for row in self.rm_item_details:
                    doc.append(
                        "items",
                        {
                            "s_warehouse": self.rm_warehouse,
                            "t_warehouse": self.wip_warehouse,
                            "item_code": row.item_code,
                            "batch_no": row.batch,
                            "uom": row.uom,
                            "qty": row.qty,
                            "basic_rate": frappe.db.get_value(
                                "Stock Entry Detail",
                                {
                                    "parent": ref_stock_entry,
                                    "item_code": row.item_code,
                                    "batch_no": row.batch,
                                },
                                ["basic_rate"],
                            ),
                        },
                    )
                doc.save(ignore_permissions=True)
                doc.submit()

            rej_items = []
            rej_entry = frappe.new_doc("Stock Entry")
            rej_entry.company = self.company
            rej_entry.dcm_name = self.dcm_name
            rej_entry.dcm_location = self.dcm_location
            rej_entry.stock_entry_type = "Material Issue"
            rej_entry.sfg_material_in = self.name
            rej_entry.me_sfg_dispatch_note = self.me_sfg_dispatch_note
            rej_entry.from_warehouse = self.rm_warehouse
            for line in self.rm_item_details:
                if line.rejected_qty > 0:
                    rej_items.append(line.item_code)
                    rej_entry.append(
                        "items",
                        {
                            "s_warehouse": self.rm_warehouse,
                            "item_code": line.item_code,
                            "batch_no": line.batch,
                            "uom": line.uom,
                            "qty": line.rejected_qty,
                            "basic_rate": frappe.db.get_value(
                                "Stock Entry Detail",
                                {
                                    "parent": ref_stock_entry,
                                    "item_code": line.item_code,
                                    "batch_no": line.batch,
                                },
                                ["basic_rate"],
                            ),
                        },
                    )
            if len(rej_items) != 0:
                rej_entry.save(ignore_permissions=True)
                rej_entry.submit()
            else:
                pass

    @frappe.whitelist()
    def btn_hide_condition(self):
        check_doc = frappe.db.get_value(
            "SFG QC Check List", {"sfg_material_in": self.name}, ["name"]
        )
        msg = ""
        if frappe.session.user == "Administrator" and not check_doc:
            msg = "Success"
        else:
            roles = []
            usr = frappe.get_doc("User", frappe.session.user)
            for i in usr.roles:
                roles.append(i.role)
            if (
                ("S4S SFG Quality User" in roles)
                or ("System Manager" in roles)
                and (not check_doc)
            ):
                msg = "Success"

        return msg


@frappe.whitelist()
def create_qc_checklist(source_name, target_doc=None):
    doc = frappe.get_doc("SFG Material In", source_name)
    qc = frappe.new_doc("SFG QC Check List")
    qc.dcm_name = doc.dcm_name
    qc.dcm_location = doc.dcm_location
    qc.sfg_material_in = doc.name

    return qc
