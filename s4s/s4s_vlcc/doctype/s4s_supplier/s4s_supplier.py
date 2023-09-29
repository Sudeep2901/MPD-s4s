# Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from six import integer_types, string_types, text_type

class S4SSupplier(Document):
	def before_save(self):
		if self.pan_no:
			self.pan_no = self.pan_no.upper()

		if self.supplier:
			self.approval_status = "Approved"
		else:
			self.approval_status = "Pending"


	@frappe.whitelist( allow_guest=True )
	def assign_address(self,addr,sup_doc):
		doc = frappe.get_doc('Address', addr)
		doc.links = []
		doc.append('links', {
			'link_doctype': 'Supplier',
			'link_name': sup_doc
		})
		doc.save()
	
	@frappe.whitelist()
	def value_fetch(self,user):
		if frappe.db.exists("S4S User details",user):
			user = frappe.get_doc("S4S User details",user)
			self.vlcc_name = user.vlcc_name
			self.cc_name = user.cc_name
			self.village = user.village
			self.taluka = user.taluka
			self.district = user.district
			self.state = user.state
			
	@frappe.whitelist()
	def create_supplier(self):
		sup = frappe.new_doc("Supplier")
		sup.supplier_name=self.supplier_name
		sup.supplier_group=self.type_of_supplier
		sup.mobile_no_1=self.mobile_no
		sup.aadhar_card_no=self.aadhar_card_no
		sup.pan=self.pan_no
		sup.vlcc_name=self.vlcc_name
		sup.cc_name=self.cc_name
		sup.village=self.village
		sup.taluka=self.taluka
		sup.district=self.district
		sup.state_ = self.state
		sup.account_holder_name=self.account_holder_name
		sup.account_number=self.account_number
		sup.bank_name=self.bank_name
		sup.ifsc_code=self.ifsc_code
		sup.branch=self.branch
		sup.pan_card_photo=self.pan_card_photo
		sup.aadhar_card_photo=self.aadhar_card_photo
		sup.bank_passbook_photo=self.bank_passbook_photo
		sup.save()
		self.supplier = sup.name
		addr = frappe.new_doc("Address")
		addr.address_title = sup.name
		addr.address_type = "Billing"
		addr.address_line1=self.village
		addr.city = self.taluka
		addr.county = self.district
		addr.append("links",{
			'link_doctype': 'Supplier',
			'link_name': sup.name
		})
		addr.save()
		con = frappe.new_doc("Contact")
		con.first_name = self.supplier_name
		con.append("phone_nos",{
			"phone":self.mobile_no,
			"is_primary_phone":1,
			"is_primary_mobile_no":1
		})
		con.append("links",{
			'link_doctype': 'Supplier',
			'link_name': sup.name
		})
		con.save()
		self.save()