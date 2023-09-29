# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SearchListSetting(Document):
	
	@frappe.whitelist()
	def field_list(self,doctype):
		doc_list=[" "]
		meta = frappe.get_meta(doctype)
		fields = [field.fieldname for field in meta.fields]
		for k in fields:
			doc_list.append(k)
			
		return doc_list

	doc_list = [""]