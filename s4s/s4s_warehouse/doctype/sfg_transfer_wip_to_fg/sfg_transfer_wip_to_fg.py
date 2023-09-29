# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import collections
import frappe
from frappe.model.document import Document

class SFGTransferWIPtoFG(Document):
	def on_submit(self):
		self.create_stock_entry()

	def create_stock_entry(self):
		if not frappe.db.get_value("Stock Entry",{'sfg_transfer_wip_to_fg':self.name},['name']):
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
			stock_entry.sfg_transfer_wip_to_fg = self.name
			stock_entry.save(ignore_permissions=True)
			stock_entry.submit()

	def validate(self):
		self.wip_item_duplicate_validation()

	def before_save(self):
		self.set_fg_for_one_line()
		
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

