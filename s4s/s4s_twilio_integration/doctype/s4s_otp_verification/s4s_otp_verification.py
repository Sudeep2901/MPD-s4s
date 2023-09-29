# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class S4SOTPVerification(Document):
	@frappe.whitelist()
	def fetch_data(self):
		doc = frappe.get_all("User",filters={'enabled':1},fields=['name','mobile_no'])
		self.users = []
		for i in doc:
			self.append("users",{
				"user":i.name,
				"mobile_number":i.mobile_no
				# "timestamp":"0",
				# "otp":"0"
			})
		self.save()
