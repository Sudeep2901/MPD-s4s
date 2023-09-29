# Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class S4SVehicle(Document):
	def before_save(self):
		self.add_details()


	def add_details(self):
		if not frappe.db.get_value("Address",{'address_line1':self.village,'city':self.taluka,'county':self.district},['name']):
			add = frappe.new_doc("Address")
			add.address_title = self.driver_name
			add.address_line1 = self.village
			add.city = self.taluka
			add.county = self.district
			add.state = self.state
			add.pincode = self.pin_code
			add.save(ignore_permissions=True)
			self.driver_address = add.name
		else:
			add = frappe.get_doc("Address",{'name':self.driver_address})
			add.address_title = self.driver_name
			add.address_line1 = self.village
			add.city = self.taluka
			add.county = self.district
			add.state = self.state
			add.pincode = self.pin_code
			add.save(ignore_permissions=True)

		full_name  = self.driver_name.split(' ')
		first_name = full_name[0]
		last_name = full_name[1]
		if not frappe.db.get_value("Contact",{'first_name':first_name,'last_name':last_name},['name']):
			con = frappe.new_doc("Contact")
			con.first_name = first_name
			con.last_name = last_name
			mobile = ""
			if not self.driver_mobile_number:
				mobile = ""
			else:
				mobile = self.driver_mobile_number
			con.append('phone_nos',{
				'phone':mobile,
				'is_primary_mobile_no':1
			})
			con.save(ignore_permissions=True)
			self.contact = con.name

		else:
			con = frappe.get_doc("Contact",self.contact)
			con.first_name = first_name
			con.last_name = last_name
			mobile = ""
			if not self.driver_mobile_number:
				mobile = ""
			else:
				mobile = self.driver_mobile_number
			for i in con.phone_nos:
				i.phone = mobile
			con.save(ignore_permissions=True)



		
