# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MESFGDispatchRequest(Document):
	@frappe.whitelist()
	def get_me_warehouse(self):
		target = None
		me_on = frappe.get_doc("ME Onboarding",{'supplier':self.me_code})
		for entry in me_on.me_warehouse_details:
			if entry.stock_entry == "Manufacture":
				target = entry.target_warehouse
    
		print("----------------------------------------",target)
		return target

	@frappe.whitelist()
	def get_uom(self):
		for i in self.me_dispatch_item:
			item = frappe.get_doc("Item",{'name':i.item_name})
			if item.name == i.item_name:
				i.uom = item.stock_uom

	@frappe.whitelist()
	def get_batch_qty(self):
		for i in self.me_dispatch_item:
			batch = frappe.get_doc("Batch",{'name':i.batch_no})
			if i.batch_no == batch.name:
				i.qty = batch.batch_qty

@frappe.whitelist()
def make_transfer(source_name,target_doc=None):
	me_req = frappe.get_doc("ME SFG Dispatch Request",source_name)
	doc = frappe.new_doc("Stock Entry")
	doc.stock_entry_type = 'Material Transfer'
	doc.add_to_transit =1
	doc.s4ssupplier = me_req.me_code
	doc.me_name = me_req.me_name
	doc.from_warehouse = me_req.me_warehouse
	doc.set_posting_time = 1
	doc.posting_date = me_req.date
	doc.vehicle_number = me_req.vehicle_no
	doc.vehicle_model = me_req.vehicle_model
	doc.drivers_name = me_req.driver_name
	doc.driver_mobile_number = me_req.driver_mobile_number
	doc.me_sfg_dispatch_request = me_req.name
	doc.to_warehouse = me_req.cc_warehouse
	for item in me_req.me_dispatch_item:
		doc.append('items',{
			's_warehouse' : me_req.me_warehouse,
			't_warehouse' : me_req.cc_warehouse,
			'item_code' : item.item_name,
			'qty' : item.qty,
			'batch_no' : item.batch_no,
			'stock_uom' : item.uom

		})
	return doc

