# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import collections

class MaterialTransferforSubcontractor(Document):
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

	def on_submit(self):
		self.make_stock_entry()

	def make_stock_entry(self):
		if not frappe.db.get_value("Stock Entry",{"material_transfer_for_subcontractor":self.name},["name"]):
			doc = frappe.new_doc("Stock Entry")
			doc.company = self.company
			doc.stock_entry_type = self.stock_entry_type
			doc.from_warehouse = self.rm_warehouse
			doc.to_warehouse = self.wip_warehouse
			doc.subcontracting_supplier = self.subcontractor_supplier
			doc.subcontracting_supplier_name = self.subcontractor_supplier_name
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
			doc.material_transfer_for_subcontractor = self.name
			doc.save(ignore_permissions=True)
			doc.submit()
			
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


	@frappe.whitelist()
	def btn_cond_check(self):
		lst = frappe.db.get_list("Material Return From Subcontractor",{'dcm_sfg_transfer_to_wip':self.name,'docstatus':['!=',2]})
		if len(lst) == 0:
			return "Yes"
		else:
			return "No"


@frappe.whitelist()
def create_return_subcon_entry(source_name,target_doc=None):
	source = frappe.get_doc("Material Transfer for Subcontractor",source_name)
	target = frappe.new_doc("Material Return From Subcontractor")
	target.stock_entry_tye = "Manufacture"
	target.date = source.date
	target.wip_warehouse = source.wip_warehouse
	target.subcontracting_supplier = source.subcontractor_supplier
	target.subcontracting_supplier_name = source.subcontractor_supplier_name
	for row in source.rm_item_details:
		target.append("items",{
			"item_code":row.item_code,
			"item_name":row.item_name,
			"qty":row.qty,
			"uom":row.uom,
			"batch":row.batch,
			"wip_warehouse":source.wip_warehouse
		})

	# if frappe.db.get_value("SFG Warehouse User Details",{'user_email':frappe.session.user},['name']):
	# 	user_details = frappe.get_doc("SFG Warehouse User Details",{'user_email':frappe.session.user})

	# 	for row in user_details.warehouse_details:
	# 		if row.fg_warehouse:
	# 			target.append("fg_items_table",{
	# 				"fg_warehouse":row.fg_warehouse,
	# 				"is_finished_item":1
	# 			})
			
	# 		if row.by_product_warehouse:
	# 			target.append("fg_items_table",{
	# 				"fg_warehouse":row.by_product_warehouse,
	# 				"is_scrap_item":1
	# 			})

	# 		if row.rejected_warehouse:
	# 			target.append("fg_items_table",{
	# 				"fg_warehouse":row.rejected_warehouse,
	# 				"is_scrap_item":1,
	# 			})

	# 		if row.process_loss_warehouse:
	# 			target.append("fg_items_table",{
	# 				"fg_warehouse":row.process_loss_warehouse,
	# 				"is_scrap_item":1,
	# 			})


	target.dcm_sfg_transfer_to_wip = source.name

	return target