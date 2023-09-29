# Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import collections
import frappe
from frappe.model.document import Document


class SFGDispatchRequest(Document):
    @frappe.whitelist()
    def set_options(self, s_user):
        user_doc = frappe.get_doc("User", {"name": s_user})
        lst = []
        for i in user_doc.roles:
            if i.role == "DCM Supervisor" and self.dcm_supervisor != 1:
                lst.extend(["Approve by DCM Supervisor", "Reject by DCM Supervisor"])
            if (
                i.role == "CC User"
                or i.role == "VLCC User"
                or i.role == "DCM SFG Warehouse User"
            ) and self.cc_user != 1:
                lst.extend(["Approve by CC Supervisor"])
            if i.role == "Logistic Supervisor" and self.logistic_supervisor != 1:
                lst.extend(["Accept by Logistic Supervisor"])
            if (
                i.role == "Factory RM Store Manager"
                and self.factory_rm_store_manager != 1
            ):
                lst.extend(["Approve by Factory Supervisor"])

        final_lst = []
        if "Approve by DCM Supervisor" in lst:
            final_lst.append("Approve by DCM Supervisor")
        if "Reject by DCM Supervisor" in lst:
            final_lst.append("Reject by DCM Supervisor")
        if "Approve by CC Supervisor" in lst:
            final_lst.append("Approve by CC Supervisor")
        if "Approve by Factory Supervisor" in lst:
            final_lst.append("Approve by Factory Supervisor")
        if "Accept by Logistic Supervisor" in lst:
            final_lst.append("Accept by Logistic Supervisor")
        if self.approval_status and self.approval_status not in final_lst:
            final_lst.append(self.approval_status)
        return final_lst

    def before_save(self):
        batch = []
        all = []
        for j in self.dcm_dispatch_item:
            all.append(j.batch_no)
        dup = [item for item, count in collections.Counter(all).items() if count > 1]

        for i in self.dcm_dispatch_item:
            batch.append(i.batch_no)
        if len(batch) != len(set(batch)):
            if len(dup) == 1:
                frappe.throw(f"Batch {dup[0]} Duplicated")
            if len(dup) > 1:
                frappe.throw(
                    title="Following batches are duplicated:", msg=dup, as_list=True
                )

    @frappe.whitelist()
    def get_dcm_warehouse(self):
        if self.dcm_name:
            dcm = frappe.get_doc("DCM List", {"name": self.dcm_name})
            self.dcm_warehouse = dcm.sfg_location
        else:
            pass

    @frappe.whitelist()
    def get_uom(self):
        for i in self.dcm_dispatch_item:
            item = frappe.get_doc("Item", {"name": i.item_name})
            if item.name == i.item_name:
                i.uom = item.stock_uom

    @frappe.whitelist()
    def get_batch_qty(self):
        for i in self.dcm_dispatch_item:
            batch = frappe.get_doc("Batch", {"name": i.batch_no})
            if i.batch_no == batch.name:
                i.qty = batch.batch_qty

    @frappe.whitelist()
    def get_logi_details(self):
        if self.vehicle_no:
            veh = frappe.get_doc("S4S Vehicle", self.vehicle_no)
            self.driver_name = veh.driver_name
            self.driver_mobile_number = veh.driver_mobile_number
            self.vehicle_model = veh.vehicle_model

    @frappe.whitelist()
    def check_role(self):
        lst = []
        doc = frappe.get_doc("User", frappe.session.user)
        for row in doc.roles:
            if row.role == "DCM Supervisor":
                lst.append(row.role)
            if row.role == "DCM Field Supervisor":
                lst.append(row.role)

        if not frappe.db.get_value(
            "Stock Entry",
            {
                "sfg_dispatch_request": self.name,
                "add_to_transit": 1,
                "docstatus": ["!=", 2],
            },
            ["name"],
        ):
            lst.append("Success")

        return lst

    @frappe.whitelist()
    def role_check(self):
        lst = []
        doc = frappe.get_doc("User", frappe.session.user)
        for row in doc.roles:
            if row.role == "S4S CC User":
                lst.append(row.role)
            if row.role == "Factory RM Store Manager":
                lst.append(row.role)

        if (
            ("S4S CC User" in lst or "Factory RM Store Manager" in lst)
            and not frappe.db.get_value(
                "SFG Material In",
                {"material_transfer_wh_to_wh": self.name, "docstatus": ["!=", 2]},
                ["name"],
            )
            and frappe.db.get_value(
                "Stock Entry", {"sfg_dispatch_request": self.name}, ["name"]
            )
        ):
            return "Success"


@frappe.whitelist()
def filtered_batch(dcm_warehouse, item):
    lst = []
    query = frappe.db.get_list(
        "Stock Entry Detail",
        {
            "item_code": item,
            "s_warehouse": ["in", ["", None]],
            "t_warehouse": dcm_warehouse,
            "qty": ["!=", 0],
            "docstatus": 1,
        },
        ["parent", "batch_no", "qty"],
    )
    for i in query:
        lst.append(i.get("batch_no"))
    return lst


@frappe.whitelist()
def make_transfer(source_name, target_doc=None):
    dis_req = frappe.get_doc("SFG Dispatch Request", source_name)
    doc = frappe.new_doc("Stock Entry")
    doc.company = dis_req.company
    doc.stock_entry_type = "Material Transfer"
    doc.add_to_transit = 1
    doc.dcm_name = dis_req.dcm_name
    doc.dcm_location = dis_req.dcm_location
    doc.from_warehouse = dis_req.dcm_warehouse
    doc.set_posting_time = 1
    doc.posting_date = dis_req.date
    doc.vehicle_number = dis_req.vehicle_no
    doc.vehicle_model = dis_req.vehicle_model
    doc.drivers_name = dis_req.driver_name
    doc.driver_mobile_number = dis_req.driver_mobile_number
    doc.sfg_dispatch_request = dis_req.name
    doc.to_warehouse = dis_req.cc_warehouse
    for item in dis_req.dcm_dispatch_item:
        doc.append(
            "items",
            {
                "s_warehouse": dis_req.dcm_warehouse,
                "t_warehouse": dis_req.cc_warehouse,
                "item_code": item.item_name,
                "qty": item.qty,
                "batch_no": item.batch_no,
                "stock_uom": item.uom,
            },
        )
    return doc


@frappe.whitelist()
def make_sfg_material_in(source_name, target_doc=None):
    source = frappe.get_doc("SFG Dispatch Request", source_name)
    target = frappe.new_doc("SFG Material In")
    target.material_transfer_wh_to_wh = source.name
    target.dcm_name = source.dcm_name
    target.dcm_location = source.dcm_location
    target.rm_warehouse = source.cc_warehouse
    for row in source.dcm_dispatch_item:
        target.append(
            "rm_item_details",
            {
                "item_code": row.item_name,
                "item_name": row.item_name1,
                "sent_qty": row.qty,
                "batch": row.batch_no,
                "no_of_bags": row.no_of_bags,
                "uom": row.uom,
                "bag_condition": row.bag_condition,
                "moisture": row.moisture,
                "colour": row.colour,
                "taste": row.taste,
            },
        )
    target.vehicle_no = source.vehicle_no
    target.vehicle_model = source.vehicle_model
    target.driver_name = source.driver_name
    target.driver_mobile_number = source.driver_mobile_number

    return target
