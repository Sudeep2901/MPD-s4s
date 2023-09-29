# Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MEMaterialRequest(Document):
	@frappe.whitelist()
	def make_material_request(self):
		material_req = frappe.new_doc("Material Request")
		material_req.update({
			'material_request_type' : self.purpose,
			'schedule_date' : self.delivery_date,
			'set_from_warehouse' : self.rm_warehouse,
			'set_warehouse' : self.require_warehouse,
		})
		for i in self.items:
			material_req.append("items",{
				'item_code' : i.item_code,
				'item_name' : i.item_name,
				'qty' : i.qty,
				'uom' : i.uom
			})
		material_req.insert()
		# material_req.submit()
		self.material_request = material_req.name
		
