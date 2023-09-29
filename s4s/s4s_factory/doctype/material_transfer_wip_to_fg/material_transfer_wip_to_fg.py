# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import collections
import frappe
from frappe.model.document import Document

class MaterialtransferWIPtoFG(Document):
	def on_submit(self):
		self.create_fg_entry()
		
	def create_fg_entry(self):
		if not frappe.db.get_value("Stock Entry",{'material_transfer_wip_to_fg':self.name},['name']):
			fg_entry = frappe.new_doc("Stock Entry")
			fg_entry.company = self.company
			fg_entry.stock_entry_type = self.stock_entry_type
			fg_entry.set_posting_time = 1
			fg_entry.posting_date = self.date
			fg_entry.from_warehouse = self.wip_warehouse
			fg_entry.to_warehouse = self.fg_warehouse
			for row in self.items:
				fg_entry.append("items",{
					"s_warehouse":self.wip_warehouse,
					"item_code":row.item_code,
					"qty":row.qty,
					"uom":row.uom,
					"batch_no":row.batch,
				})
			for item in self.fg_items_table:
				fg_entry.append("items",{
					"t_warehouse":item.fg_warehouse,
					"item_code":item.item_code,
					"qty":item.qty,
					"uom":item.uom,
					"is_finished_item":item.is_finished_item,
					"is_process_loss":item.is_process_loss,
					"is_scrap_item":item.is_scrap_item
				})
			fg_entry.material_transfer_wip_to_fg = self.name
			fg_entry.save(ignore_permissions=True)
			fg_entry.submit()
		
	def before_save(self):
		self.set_fg_for_one_line()
		self.wip_item_duplicate_validation()
		# self.fg_item_duplicate_validation()
		
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

	# def fg_item_duplicate_validation(self):
	# 	items = []
	# 	all = []
	# 	for j in self.fg_items_table:
	# 		all.append(j.item_code)
	# 	dup = [item for item, count in collections.Counter(all).items() if count > 1]

	# 	for i in self.fg_items_table:
	# 		items.append(i.item_code)
	# 	if len(items) != len(set(items)):
	# 		if len(dup) == 1:
	# 			frappe.throw(f"Item {dup[0]} Duplicated")
	# 		if len(dup) > 1:
	# 			frappe.throw(title="Following Items are duplicated:",msg=dup,as_list=True)

	def set_fg_for_one_line(self):
		fg_item_lines = []
		for i in self.fg_items_table:
			fg_item_lines.append(i.as_dict())
		if len(fg_item_lines) == 1:
			for row in self.fg_items_table:
				row.is_finished_item = 1
				row.is_scrap_item = 0
				row.is_process_loss = 0

			