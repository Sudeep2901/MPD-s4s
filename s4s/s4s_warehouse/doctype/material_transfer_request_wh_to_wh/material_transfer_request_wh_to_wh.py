# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import collections
import frappe
from frappe.model.document import Document

class MaterialTransferRequestWHToWH(Document):
	def before_save(self):
		self.batch_duplicate_validation()

	def batch_duplicate_validation(self):
		batches = []
		all = []
		for j in self.sfg_material_details:
			all.append(j.batch)
		dup = [item for item, count in collections.Counter(all).items() if count > 1]

		for i in self.sfg_material_details:
			batches.append(i.batch)
		if len(batches) != len(set(batches)):
			if len(dup) == 1:
				frappe.throw(f"Batch {dup[0]} Duplicated")
			if len(dup) > 1:
				frappe.throw(title="Following Batches are duplicated:",msg=dup,as_list=True)

	
	@frappe.whitelist()
	def material_tfr_condition(self):
		if not frappe.db.get_value("Material Transfer WH To WH",{"material_transfer_request_wh_to_wh":self.name},['name']):
			return "Success"
		else:
			return ""


@frappe.whitelist()
def create_material_tfr(source_name,target_doc=None):
	doc = frappe.get_doc("Material Transfer Request WH To WH",source_name)
	target = frappe.new_doc("Material Transfer WH To WH")
	target.material_transfer_request_wh_to_wh = doc.name
	target.company = doc.company
	target.rm_warehouse = doc.source_warehouse
	target.wip_warehouse = doc.target_warehouse

	for row in doc.sfg_material_details:
		target.append("rm_item_details",{
			"item_code":row.item_code,
			"item_name":row.item_name,
			"qty":row.qty,
			"uom":row.uom,
			"batch":row.batch
		})

	return target