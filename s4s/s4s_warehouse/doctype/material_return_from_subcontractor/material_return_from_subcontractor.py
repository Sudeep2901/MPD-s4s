# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import collections

class MaterialReturnFromSubcontractor(Document):
	def on_submit(self):
		self.create_stock_entry()

	def validate(self):
		self.wip_item_duplicate_validation()

	def before_save(self):
		self.set_fg_item()

	def set_fg_item(self):
		if self.fg_items_table:
			for i in self.fg_items_table:
				if i.idx == 1 and not i.is_finished_item:
					i.is_finished_item = 1

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
				frappe.throw(title="Following Batches are duplicated:",msg=dup,as_list=True)

	def create_stock_entry(self):
		if not frappe.db.get_value("Stock Entry",{'material_return_from_subcontractor':self.name},['name']):
			stock_entry = frappe.new_doc("Stock Entry")
			stock_entry.company = self.company
			stock_entry.stock_entry_type = self.stock_entry_type
			stock_entry.set_posting_time = 1
			stock_entry.posting_date = self.date
			stock_entry.from_warehouse = self.wip_warehouse
			stock_entry.to_warehouse = self.fg_warehouse
			for row in self.items:
				stock_entry.append("items",{
					"s_warehouse":self.wip_warehouse,
					"item_code":row.item_code,
					"qty":row.qty,
					"uom":row.uom,
					"batch_no":row.batch,
				})
			for item in self.fg_items_table:
				stock_entry.append("items",{
					"t_warehouse":item.fg_warehouse,
					"item_code":item.item_code,
					"qty":item.qty,
					"uom":item.uom,
					"is_finished_item":item.is_finished_item,
					"is_process_loss":item.is_process_loss,
					"is_scrap_item":item.is_scrap_item
				})
			stock_entry.material_return_from_subcontractor = self.name
			stock_entry.save(ignore_permissions=True)
			stock_entry.submit()
