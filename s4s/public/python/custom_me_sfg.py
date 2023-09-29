import json
from collections import defaultdict

import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint, comma_or, cstr, flt, format_time, formatdate, getdate, nowdate
# from erpnext.stock.doctype.stock_entry import set_stock_entry_type

@frappe.whitelist()
def fetch_warehouse(stock_entry,user,field):
	stock_entry = json.loads(stock_entry)
	user_doc = frappe.get_doc("User",{"name":user})
	result = {"from_warehouse":"","to_warehouse":""}
	for i in user_doc.roles:
		if i.role == "ME Field Executive" and stock_entry["stock_entry_type"]=="Manufacture" and stock_entry["me_code"] and frappe.db.exists("ME Onboarding",{"supplier":stock_entry["me_code"]}):
			me_onboarding = frappe.get_doc("ME Onboarding",{"supplier":stock_entry["me_code"]})
			for row in me_onboarding.me_warehouse_details:
				if row.stock_entry == "Manufacture":
					result["from_warehouse"] = row.source_warehouse
					result["to_warehouse"] = row.target_warehouse
					print("running1")
					
		elif i.role == "ME Field Executive" and stock_entry["stock_entry_type"]=="Material Transfer" and not stock_entry["add_to_transit"] and stock_entry["me_code"] and frappe.db.exists("ME Onboarding",{"supplier":stock_entry["me_code"]}):
			me_onboarding = frappe.get_doc("ME Onboarding",{"supplier":stock_entry["me_code"]})
			for row in me_onboarding.me_warehouse_details:
				if row.stock_entry == "Material Transfer" and row.add_to_transit!=1:
					result["from_warehouse"] = row.source_warehouse
					result["to_warehouse"] = row.target_warehouse
					print("running2")
					
		elif i.role == "ME Field Executive" and stock_entry["stock_entry_type"]=="Material Transfer" and stock_entry["add_to_transit"] and stock_entry["me_code"] and frappe.db.exists("ME Onboarding",{"supplier":stock_entry["me_code"]}):
			me_onboarding = frappe.get_doc("ME Onboarding",{"supplier":stock_entry["me_code"]})
			for row in me_onboarding.me_warehouse_details:
				if row.stock_entry == "Material Transfer" and row.add_to_transit==1:
					result["from_warehouse"] = row.source_warehouse
					result["to_warehouse"] = row.target_warehouse
					print("running3")
	print(result)   
	return result
	

@frappe.whitelist()
def make_stock_in_entry(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.set_stock_entry_type()
		target.set_missing_values()

	def update_item(source_doc, target_doc, source_parent):
		target_doc.t_warehouse = ""

		if source_doc.material_request_item and source_doc.material_request:
			add_to_transit = frappe.db.get_value("Stock Entry", source_name, "add_to_transit")
			if add_to_transit:
				warehouse = frappe.get_value(
					"Material Request Item", source_doc.material_request_item, "warehouse"
				)
				target_doc.t_warehouse = warehouse

		target_doc.s_warehouse = source_doc.t_warehouse
		target_doc.qty = source_doc.qty - source_doc.transferred_qty

	
	doclist = get_mapped_doc(
		"Stock Entry",
		source_name,
		{
			"Stock Entry": {
				"doctype": "Stock Entry",
				"field_map": {"name": "outgoing_stock_entry"},
				"validation": {"docstatus": ["=", 1]},
			},
			"Stock Entry Detail": {
				"doctype": "Stock Entry Detail",
				"field_map": {
					"name": "ste_detail",
					"parent": "against_stock_entry",
					"serial_no": "serial_no",
					"batch_no": "batch_no",
				},
				"postprocess": update_item,
				"condition": lambda doc: flt(doc.qty) - flt(doc.transferred_qty) > 0.01,
			},
		},
		target_doc,
		set_missing_values,
	)
	if not doclist.from_warehouse:
		doclist.from_warehouse = frappe.get_value("Stock Entry",source_name,"to_warehouse")
	if not doclist.to_warehouse and doclist.dcm_name:
		doclist.to_warehouse = frappe.get_value("DCM List",doclist.dcm_name,"rm_location")
	return doclist