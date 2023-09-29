# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import collections
import frappe
from frappe.model.document import Document

class FactoryRMTransfertoMFG(Document):
	def on_submit(self):
		self.create_mfg_entry()

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
				frappe.throw(title="Following Batches are duplicated:",msg=dup,as_list=True)

	# Make transfer to mfg stock entry
	def create_mfg_entry(self):
		if not frappe.db.get_value("Stock Entry",{'factory_rm_transfer_to_mfg':self.name},['name']):
			mfg_entry = frappe.new_doc("Stock Entry")
			mfg_entry.company = self.company
			mfg_entry.stock_entry_type = self.stock_entry_type
			mfg_entry.set_posting_time = 1
			mfg_entry.posting_date = self.date
			mfg_entry.from_warehouse = self.rm_warehouse
			mfg_entry.to_warehouse = self.wip_warehouse
			for row in self.rm_item_details:
				mfg_entry.append("items",{
					"s_warehouse":self.rm_warehouse,
					"t_warehouse":self.wip_warehouse,
					"item_code":row.item_code,
					"qty":row.qty,
					"uom":row.uom,
					"batch_no":row.batch
				})
			mfg_entry.factory_rm_transfer_to_mfg = self.name
			mfg_entry.save(ignore_permissions=True)
			mfg_entry.submit()

	# Hide create fg entry btn if created already
	@frappe.whitelist()
	def btn_cond(self):
		lst = frappe.db.get_list("Material transfer WIP to FG",{'factory_rm_transfer_to_mfg':self.name,'docstatus':['!=',2]})
		if len(lst) == 0:
			return "Yes"
		else:
			return "No"


@frappe.whitelist()
def create_fg_entry(source_name,target_doc=None):
	source = frappe.get_doc("Factory RM Transfer to MFG",source_name)
	target = frappe.new_doc("Material transfer WIP to FG")
	target.stock_entry_tye = "Manufacture"
	target.date = source.date
	target.wip_warehouse = source.wip_warehouse
	for row in source.rm_item_details:
		target.append("items",{
			"item_code":row.item_code,
			"item_name":row.item_name,
			"qty":row.qty,
			"uom":row.uom,
			"batch":row.batch,
			"wip_warehouse":source.wip_warehouse
		})
	target.append('fg_items_table',{
		"fg_warehouse":"Factory FG - SFSTS",
		"is_finished_item":1,
	})
	target.append('fg_items_table',{
		"fg_warehouse":"Factory By-Product - SFSTS",
		"is_scrap_item":1,
	})
	target.append('fg_items_table',{
		"fg_warehouse":"Factory Process Loss - SFSTS",
		"is_scrap_item":1,
	})
	target.append('fg_items_table',{
		"fg_warehouse":"Factory Rejected RM - SFSTS",
		"is_scrap_item":1,
	})

	target.factory_rm_transfer_to_mfg = source.name

	return target

