# Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MELead(Document):
	@frappe.whitelist()
	def set_options(self,s_user):
		user_doc = frappe.get_doc("User",{"name":s_user})
		lst = []
		for i in user_doc.roles:
			if i.role == "S4S Lead User":
				lst.extend(["Send to Approval","Rejected by Lead User"])
			if i.role == "S4S Lead Qualifier":
				lst.extend(["Approved by Qualifier", "Rejected by Qualifier"])
			if i.role == "S4S CRM Ganesh":
				lst.extend(["Qualify","Reject","Rework"])
		final_lst = []
		if "Send to Approval" in lst:
			final_lst.append("Send to Approval")
		if "Rejected by Lead User" in lst:
			final_lst.append("Rejected by Lead User")
		if "Approved by Qualifier" in lst:
			final_lst.append("Approved by Qualifier")
		if "Rejected by Qualifier" in lst:
			final_lst.append("Rejected by Qualifier")
		if "Qualify" in lst:
			final_lst.append("Qualify")
		if "Reject" in lst:
			final_lst.append("Reject")
		if "Rework" in lst:
			final_lst.append("Rework")
				
		return final_lst