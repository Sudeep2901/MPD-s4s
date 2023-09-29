# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import collections
import frappe
from frappe.model.document import Document


class SFGDispatchRequestToFactory(Document):
    @frappe.whitelist()
    def set_factory_warehouse(self):
        factory_wh = ""
        if (
            frappe.db.get_value(
                "SFG Warehouse User Details", {"name": frappe.session.user}, ["name"]
            )
            and frappe.session.user != "Administrator"
        ):
            doc = frappe.get_doc("SFG Warehouse User Details", frappe.session.user)
            if doc.warehouse_details:
                for i in doc.warehouse_details:
                    if i.factory_transit_warehouse:
                        factory_wh = i.factory_transit_warehouse
        return factory_wh

    @frappe.whitelist()
    def btn_condition(self):
        usr_roles = []
        doc = frappe.get_doc("User", frappe.session.user)
        for i in doc.roles:
            usr_roles.append(i.role)

        if (
            not frappe.db.get_value(
                "Material Transfer WH To WH",
                {"sfg_dispatch_request_to_factory": self.name, "docstatus": ["!=", 2]},
                ["name"],
            )
            and "SFG Warehouse User" in usr_roles
        ):
            return "Success"
        else:
            return "Already Created"

    def before_save(self):
        self.batch_duplicate_validation()

    def batch_duplicate_validation(self):
        batches = []
        all = []
        for j in self.sfg_material_details:
            all.append(j.batch)
        dup = [item for item, count in collections.Counter(all).items() if count > 1]

        for i in self.sfg_material_details:
            batches.append(i.batch)
        if len(batches) != len(set(batches)):
            if len(dup) == 1:
                frappe.throw(f"Batch {dup[0]} Duplicated")
            if len(dup) > 1:
                frappe.throw(
                    title="Following Batches are duplicated:", msg=dup, as_list=True
                )


@frappe.whitelist()
def make_sfg_transfer(source_name, target_doc=None):
    source = frappe.get_doc("SFG Dispatch Request To Factory", source_name)
    target = frappe.new_doc("Material Transfer WH To WH")
    target.sfg_dispatch_request_to_factory = source.name
    target.rm_warehouse = source.sfg_warehouse
    target.wip_warehouse = source.factory_warehouse
    target.company = source.company
    for row in source.sfg_material_details:
        target.append(
            "rm_item_details",
            {
                "item_code": row.item_code,
                "item_name": row.item_name,
                "qty": row.qty,
                "uom": row.uom,
                "batch": row.batch,
            },
        )

    return target
