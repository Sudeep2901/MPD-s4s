# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import collections

class SFGTransferToWIP(Document):
	def on_submit(self):
		self.create_stock_entry()
	
	def before_save(self):
		self.batch_duplicate_validation()
		
	def batch_duplicate_validation(self):
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


	def create_stock_entry(self):
		if not frappe.db.get_value("Stock Entry",{'dcm_sfg_transfer_to_wip':self.name},['name']):
			stock_entry = frappe.new_doc("Stock Entry")
			stock_entry.company = self.company
			stock_entry.stock_entry_type = self.stock_entry_type
			stock_entry.set_posting_time = 1
			stock_entry.posting_date = self.date
			stock_entry.from_warehouse = self.rm_warehouse
			stock_entry.to_warehouse = self.wip_warehouse
			for row in self.rm_item_details:
				stock_entry.append("items",{
					"s_warehouse":self.rm_warehouse,
					"t_warehouse":self.wip_warehouse,
					"item_code":row.item_code,
					"qty":row.qty,
					"uom":row.uom,
					"batch_no":row.batch
				})
			stock_entry.dcm_sfg_transfer_to_wip = self.name
			stock_entry.save(ignore_permissions=True)
			stock_entry.submit()

	@frappe.whitelist()
	def fetch_user_details(self):
		if frappe.session.user != "Administrator":
			if frappe.db.get_value("SFG Warehouse User Details",{'user_email':frappe.session.user},['name']):
				doc = frappe.get_doc("SFG Warehouse User Details",{'user_email':frappe.session.user})
				rm_warehouse = ""
				wip_warehouse = ""
				for row in doc.warehouse_details:
					rm_warehouse = row.rm_warehouse
					wip_warehouse = row.wip_warehouse

				
				return {"rm_wh":rm_warehouse,"wip_wh":wip_warehouse}

	# Hide create fg entry btn if created already
	@frappe.whitelist()
	def btn_cond_check(self):
		lst = frappe.db.get_list("SFG Transfer WIP to FG",{'dcm_sfg_transfer_to_wip':self.name,'docstatus':['!=',2]})
		if len(lst) == 0:
			return "Yes"
		else:
			return "No"
		
@frappe.whitelist()
def create_fg_entry(source_name,target_doc=None):
	source = frappe.get_doc("SFG Transfer To WIP",source_name)
	target = frappe.new_doc("SFG Transfer WIP to FG")
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

	if frappe.db.get_value("SFG Warehouse User Details",{'user_email':frappe.session.user},['name']):
		user_details = frappe.get_doc("SFG Warehouse User Details",{'user_email':frappe.session.user})

		for row in user_details.warehouse_details:
			if row.fg_warehouse:
				target.append("fg_items_table",{
					"fg_warehouse":row.fg_warehouse,
					"is_finished_item":1
				})
			
			if row.by_product_warehouse:
				target.append("fg_items_table",{
					"fg_warehouse":row.by_product_warehouse,
					"is_scrap_item":1
				})

			if row.rejected_warehouse:
				target.append("fg_items_table",{
					"fg_warehouse":row.rejected_warehouse,
					"is_scrap_item":1,
				})

			if row.process_loss_warehouse:
				target.append("fg_items_table",{
					"fg_warehouse":row.process_loss_warehouse,
					"is_scrap_item":1,
				})


	target.dcm_sfg_transfer_to_wip = source.name

	return target
