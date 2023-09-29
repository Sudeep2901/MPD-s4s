# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import collections
import frappe
from frappe.model.document import Document

class MESFGDispatchNote(Document):
	def before_save(self):
		self.batch_duplicate_validation()
		
	def batch_duplicate_validation(self):
		batches = []
		all = []
		for j in self.me_dispatch_item:
			all.append(j.batch_no)
		dup = [item for item, count in collections.Counter(all).items() if count > 1]

		for i in self.me_dispatch_item:
			batches.append(i.batch_no)
		if len(batches) != len(set(batches)):
			if len(dup) == 1:
				frappe.throw(f"Batch {dup[0]} Duplicated")
			if len(dup) > 1:
				frappe.throw(title="Following Batches are duplicated:",msg=dup,as_list=True)

	def on_submit(self):
		self.make_stock_entry()

	def make_stock_entry(self):
		if not frappe.db.get_value("Stock Entry",{'me_sfg_dispatch_note':self.name},['name']):
			doc = frappe.new_doc("Stock Entry")
			doc.company = self.company
			doc.stock_entry_type = self.stock_entry_type
			doc.s4ssupplier = self.me_code
			doc.me_name = self.me_name
			doc.from_warehouse = self.me_warehouse
			doc.to_warehouse = self.cc_warehouse
			doc.add_to_transit = self.add_to_transit
			for i in self.me_dispatch_item:
				doc.append("items",{
					"item_code":i.item_name,
					"qty":i.qty,
					"uom":i.uom,
					"batch_no":i.batch_no,
					"conversion_factor":1
				})
			doc.vehicle_number = self.vehicle_no
			doc.vehicle_model = self.vehicle_model
			doc.drivers_name = self.driver_name
			doc.driver_mobile_number = self.driver_mobile_number
			doc.e_way_bill_no = self.e_way_bill_no
			doc.me_sfg_dispatch_note = self.name
			doc.save(ignore_permissions=True)
			doc.submit()


	@frappe.whitelist()
	def set_warehouses(self):
		wh_lst = []
		if self.me_code:
			if frappe.db.get_value("ME Onboarding",{'supplier':self.me_code},['name']):
				doc = frappe.get_doc("ME Onboarding",{'supplier':self.me_code})
				for row in doc.me_warehouse_details:
					if row.stock_entry == "Material Transfer" and row.add_to_transit == 1:
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
		

	@frappe.whitelist()
	def sfg_material_btn_condition(self):
		if frappe.db.get_value("Stock Entry",{'me_sfg_dispatch_note':self.name,'docstatus':["!=",2]},['name']) and not frappe.db.get_value("SFG Material In",{"me_sfg_dispatch_note":self.name,'docstatus':["!=",2]},['name']):
			return "Success"

@frappe.whitelist()
def create_sfg_material_in(source_name,target_doc=None):
	dn = frappe.get_doc("ME SFG Dispatch Note",source_name)
	doc = frappe.new_doc("SFG Material In")
	doc.stock_entry_type = dn.stock_entry_type
	doc.me_code = dn.me_code
	doc.me_name = dn.me_name
	doc.me_unique_code = dn.me_unique_code
	doc.company = dn.company
	doc.me_sfg_dispatch_note = dn.name
	doc.rm_warehouse = dn.cc_warehouse
	for row in dn.me_dispatch_item:
		doc.append("rm_item_details",{
			"item_code":row.item_name,
			"item_name":row.item_name1,
			"sent_qty":row.qty,
			"no_of_bags":row.no_of_bags,
			"uom":row.uom,
			"batch":row.batch_no,
			"bag_condition":row.bag_condition,
			"moisture":row.moisture,
			"colour":row.colour,
			"taste":row.taste
		})

	doc.vehicle_no = dn.vehicle_no
	doc.vehicle_model = dn.vehicle_model
	doc.driver_name = dn.driver_name
	doc.driver_mobile_number = dn.driver_mobile_number
		
	return doc

		
	
