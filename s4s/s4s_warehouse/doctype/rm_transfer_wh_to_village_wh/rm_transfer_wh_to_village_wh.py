# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import collections
import frappe
from frappe.model.document import Document

class RMTransferWHToVillageWH(Document):
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
		if not frappe.db.get_value("Stock Entry",{"rm_transfer_wh_to_village_wh":self.name,'docstatus':['!=',2]},["name"]):
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
			doc.rm_transfer_wh_to_village_wh = self.name
			doc.save(ignore_permissions=True)
			doc.submit()


	@frappe.whitelist()
	def rm_in_condition(self):
		role_perm = None
		if frappe.session.user == 'Administrator':
			role_perm = "Success"
		else:
			user = frappe.get_doc("User",{"email":frappe.session.user})
			lst = []
			for i in user.roles:
				lst.append(i.role)
			if "ME Field Executive" in lst:
				role_perm = "Success"
			if "System Manager" in lst:
				role_perm = "Success"

		if frappe.db.get_value("Stock Entry",{'rm_transfer_wh_to_village_wh':self.name,'docstatus':1},['name']) and not frappe.db.get_value("ME RM In",{'material_transfer_wh_to_wh':self.name},['name']) and role_perm:
			return "Success"
		
	@frappe.whitelist()
	def set_source_wh(self):
		rm_wh = None
		if frappe.db.get_value("SFG Warehouse User Details",{'name':frappe.session.user},['name']) and frappe.session.user != "Administrator":
			doc = frappe.get_doc("SFG Warehouse User Details",frappe.session.user)
			for i in doc.warehouse_details:
				if i.rm_warehouse:
					rm_wh = i.rm_warehouse
		
		if rm_wh:
			return rm_wh




@frappe.whitelist()
def create_rm_in(source_name,target_doc=None):
	source = frappe.get_doc("RM Transfer WH To Village WH", source_name)
	target = frappe.new_doc("ME RM In")
	target.stock_entry_type = source.stock_entry_type
	target.material_transfer_wh_to_wh = source.name
	target.sent_by = source.sent_by
	target.rm_warehouse = source.wip_warehouse
	# target.wip_warehouse = source.rm_warehouse
	target.material_type = source.material_type
	for row in source.rm_item_details:
		target.append('rm_item_details',{
			'item_code':row.item_code,
			'item_name':row.item_name,
			'sent_qty':row.qty,
			'batch':row.batch,
			'no_of_bags':row.no_of_bags,
			'uom':row.uom,
			'remark':row.remarks

		})
	target.vehicle_no = source.vehicle_no
	target.vehicle_model = source.vehicle_model
	target.driver_name = source.driver_name
	target.driver_mobile_number = source.driver_mobile_number
	target.e_way_bill_no = source.e_way_bill_no

	return target