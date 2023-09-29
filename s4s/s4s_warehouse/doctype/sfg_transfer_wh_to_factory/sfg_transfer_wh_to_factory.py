# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import collections
import frappe
from frappe.model.document import Document

class SFGTransferWHToFactory(Document):
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
		if not frappe.db.get_value("Stock Entry",{"_sfg_transfer_wh_to_factory":self.name},["name"]):
			doc = frappe.new_doc("Stock Entry")
			doc.company = self.company
			doc.stock_entry_type = self.stock_entry_type
			doc.add_to_transit = 1
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
			doc.vehicle_number = self.vehicle_no
			doc.vehicle_model = self.vehicle_model
			doc.drivers_name = self.driver_name
			doc.driver_mobile_number = self.driver_mobile_number
			doc.e_way_bill_no = self.e_way_bill_no
			doc._sfg_transfer_wh_to_factory = self.name
			doc.save(ignore_permissions=True)
			doc.submit()


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
