# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import collections
import frappe
from frappe.model.document import Document


class MESFGProcessing(Document):
    def on_submit(self):
        self.create_stock_entry()

    def validate(self):
        self.wip_item_duplicate_validation()
        self.validate_warehouse()
        self.validate_qty()

    def before_save(self):
        self.set_fg_for_one_line()

    @frappe.whitelist()
    def set_wip_wh(self, me_code):
        wip_warehouse = ""
        fg_warehouse = ""
        if frappe.db.get_value("ME Onboarding", {"supplier": me_code}, ["name"]):
            doc = frappe.get_doc("ME Onboarding", {"supplier": me_code})
            if doc.me_warehouse_details:
                for row in doc.me_warehouse_details:
                    if row.stock_entry == "Manufacture":
                        wip_warehouse = row.source_warehouse
                        fg_warehouse = row.target_warehouse

        return {"wip_wh": wip_warehouse, "fg_wh": fg_warehouse}

    def create_stock_entry(self):
        if not frappe.db.get_value(
            "Stock Entry",
            {"me_sfg_processing": self.name, "docstatus": ["!=", 2]},
            ["name"],
        ):
            stock_entry = frappe.new_doc("Stock Entry")
            stock_entry.company = self.company
            stock_entry.stock_entry_type = self.stock_entry_type
            stock_entry.set_posting_time = 1
            stock_entry.posting_date = str(self.date).split(" ")[0]
            stock_entry.posting_time = str(self.date).split(" ")[1]
            stock_entry.s4ssupplier = self.me_code
            stock_entry.me_name = self.me_name
            # stock_entry.from_warehouse = self.wip_warehouse
            # stock_entry.to_warehouse = self.fg_warehouse
            for row in self.items:
                stock_entry.append(
                    "items",
                    {
                        "s_warehouse": row.wip_warehouse,
                        "item_code": row.item_code,
                        "qty": row.qty,
                        "uom": row.uom,
                        "batch_no": row.batch,
                    },
                )
            for item in self.fg_items_table:
                stock_entry.append(
                    "items",
                    {
                        "t_warehouse": item.fg_warehouse,
                        "item_code": item.item_code,
                        "qty": item.qty,
                        "uom": item.uom,
                        "is_finished_item": item.is_finished_item,
                        "is_process_loss": item.is_process_loss,
                        "is_scrap_item": item.is_scrap_item,
                    },
                )
            stock_entry.me_sfg_processing = self.name
            stock_entry.save(ignore_permissions=True)
            stock_entry.submit()

    def wip_item_duplicate_validation(self):
        items = []
        all = []
        for j in self.items:
            all.append(j.batch)
        dup = [item for item, count in collections.Counter(all).items() if count > 1]

        for i in self.items:
            items.append(i.batch)
        if len(items) != len(set(items)):
            if len(dup) == 1:
                frappe.throw(f"Batch {dup[0]} Duplicated")
            if len(dup) > 1:
                frappe.throw(
                    title="Following Batches are duplicated:", msg=dup, as_list=True
                )

    def validate_warehouse(self):
        for row in self.items:
            if row.wip_warehouse or row.wip_warehouse != "":
                if frappe.db.get_value(
                    "ME Onboarding", {"supplier": self.me_code}, ["name"]
                ):
                    doc = frappe.get_doc("ME Onboarding", {"supplier": self.me_code})
                    if doc.me_warehouse_details:
                        for i in doc.me_warehouse_details:
                            if i.stock_entry == "Manufacture":
                                if row.wip_warehouse != i.source_warehouse:
                                    frappe.throw(
                                        f"WIP Warehouse different from that of in ME Onboarding in row {frappe.bold(row.idx)}."
                                    )

        for row in self.fg_items_table:
            if row.fg_warehouse or row.fg_warehouse != "":
                if frappe.db.get_value(
                    "ME Onboarding", {"supplier": self.me_code}, ["name"]
                ):
                    doc = frappe.get_doc("ME Onboarding", {"supplier": self.me_code})
                    if doc.me_warehouse_details:
                        for i in doc.me_warehouse_details:
                            if i.stock_entry == "Manufacture":
                                if row.fg_warehouse != i.target_warehouse:
                                    frappe.throw(
                                        f"FG Warehouse different from that of in ME Onboarding in row {frappe.bold(row.idx)}."
                                    )

    def set_fg_for_one_line(self):
        fg_item_lines = []
        for i in self.fg_items_table:
            fg_item_lines.append(i.as_dict())

        if len(fg_item_lines) != 0:
            if len(fg_item_lines) == 1:
                for row in self.fg_items_table:
                    row.is_finished_item = 1
                    row.is_scrap_item = 0
                    row.is_process_loss = 0
            else:
                for row in self.fg_items_table:
                    if row.idx == 1:
                        row.is_finished_item = 1
                        row.is_scrap_item = 0
                        row.is_process_loss = 0

    def validate_qty(self):
        wip_qty, fg_qty = 0, 0
        if self.items:
            for row in self.items:
                wip_qty += int(row.qty)

        if self.fg_items_table:
            for i in self.fg_items_table:
                fg_qty += int(i.qty)

        if fg_qty != 0:
            if fg_qty > wip_qty:
                frappe.throw("Total FG Qty Greater Than Total WIP Qty.")
