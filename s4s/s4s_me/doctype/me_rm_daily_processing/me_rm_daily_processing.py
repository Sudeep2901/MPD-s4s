# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import collections
import frappe
from frappe.model.document import Document

class MERMDailyProcessing(Document):
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

	def on_submit(self):
		self.make_stock_entry()

	def make_stock_entry(self):
		if not frappe.db.get_value("Stock Entry",{'me_rm_daily_processing':self.name},["name"]):
			doc = frappe.new_doc("Stock Entry")
			doc.company = self.company
			doc.stock_entry_type = self.stock_entry_type
			doc.s4ssupplier = self.me_code
			doc.me_name = self.me_name
			doc.from_warehouse = self.rm_warehouse
			doc.to_warehouse = self.wip_warehouse
			for row in self.rm_item_details:
				doc.append("items",{
					"item_code":row.item_code,
					"item_name":row.item_name,
					"qty":row.qty,
					"uom":row.uom,
					"batch_no":row.batch,
					"conversion_factor":1
				})
			doc.me_rm_daily_processing = self.name
			doc.save(ignore_permissions=True)
			doc.submit()


	@frappe.whitelist()
	def set_warehouses(self):
		wh_lst = []
		if self.me_code:
			if frappe.db.get_value("ME Onboarding",{'supplier':self.me_code},['name']):
				doc = frappe.get_doc("ME Onboarding",{'supplier':self.me_code})
				for row in doc.me_warehouse_details:
					if row.stock_entry == "Material Transfer for Manufacture":
						wh_lst.append(row.source_warehouse)
						wh_lst.append(row.target_warehouse)
						
				
				if len(wh_lst) != 0:
					return wh_lst
				
				else:
					return "No"
			else:
				return "No"
			
		else:
			return "No"

