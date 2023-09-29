# Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DCMMaterialRequest(Document):
	@frappe.whitelist()
	def set_options(self,s_user):
		user_doc = frappe.get_doc("User",{"name":s_user})
		lst = []
		for i in user_doc.roles:
			if i.role == "DCM Supervisor" and self.dcm_supervisor!=1:
				lst.extend(["Approve by DCM Supervisor","Reject by DCM Supervisor"])
			if (i.role == "S4S CC User" or i.role == "DCM SFG Warehouse User") and self.cc_user!=1:
				lst.extend(["Accept by CC Supervisor", "Reject by CC Supervisor"])
			if i.role == "Logistic Supervisor" and self.logistic_supervisor!=1:
				lst.extend(["Accept by Logistic Supervisor"])
			if i.role == "S4S Logistic Manager" and self.s4s_logistic_manager!=1:
				lst.extend(["Accept by Logistic Supervisor"])
				
		final_lst = []
		if "Approve by DCM Supervisor" in lst:
			final_lst.append("Approve by DCM Supervisor")
		if "Reject by DCM Supervisor" in lst:
			final_lst.append("Reject by DCM Supervisor")
		if "Accept by CC Supervisor" in lst:
			final_lst.append("Accept by CC Supervisor")
		if "Reject by CC Supervisor" in lst:
			final_lst.append("Reject by CC Supervisor")
		if "Accept by Logistic Supervisor" in lst:
			final_lst.append("Accept by Logistic Supervisor")
		if self.approval_status and self.approval_status not in final_lst:
			final_lst.append(self.approval_status)
		return final_lst
	
	@frappe.whitelist()
	def permission_check_for_user(self,user):
		response = 0
		doc = frappe.get_doc("User",{"name":user})
		for i in doc.roles:
			if i.role == "S4S CC User" or i.role == "DCM SFG Warehouse User":
				response=1
				
		if self.name and self.docstatus == 1 and frappe.db.exists("Stock Entry",{"dcm_material_request":self.name}):
			response = 0
			
		return response
		
	# @frappe.whitelist()
	# def make_material_request(self):
	# 	material_req = frappe.new_doc("Material Request")
	# 	material_req.update({
	# 		'material_request_type' : self.purpose,
	# 		'schedule_date' : self.delivery_date,
	# 		'set_from_warehouse' : self.rm_warehouse,
	# 		'set_warehouse' : self.dcm_warehouse,
	# 	})
	# 	for i in self.items:
	# 		material_req.append("items",{
	# 			'item_code' : i.item_code,
	# 			'item_name' : i.item_name,
	# 			'qty' : i.qty,
	# 			'uom' : i.uom
	# 		})
	# 	material_req.insert()
	# 	# material_req.submit()
	# 	self.material_request = material_req.name
	
	
@frappe.whitelist()
def make_material_transfer(source_name, target_doc=None):
	mr = frappe.get_doc("DCM Material Request",source_name)
	doc = frappe.new_doc("Stock Entry")
	doc.company = mr.company
	doc.stock_entry_type = "Material Transfer"
	doc.dcm_material_request = mr.name
	doc.posting_date = mr.request_date
	doc.add_to_transit = 1
	doc.dcm_name = mr.dcm_name
	doc.dcm_location = mr.dcm_location
	doc.from_warehouse = mr.rm_warehouse
	doc.to_warehouse = mr.dcm_warehouse
	doc.vehicle_number = mr.vehicle_no
	doc.vehicle_model = mr.vehicle_model
	doc.drivers_name = mr.driver_name
	doc.driver_mobile_number = mr.driver_mobile_number
	if mr.items:
		for i in mr.items:
			doc.append("items",{
				"s_warehouse":mr.rm_warehouse,
				"t_warehouse":mr.dcm_warehouse,
				"item_code":i.item_code,
				"item_name":i.item_name,
				"qty":i.cc_approved_qty,
				"uom":i.uom,
				"stock_uom":frappe.get_value("Item",{"name":i.item_code},"stock_uom")
			})
	return doc