# Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class MEOnboarding(Document):
	@frappe.whitelist()
	def create_supplier(self):
		sup_doc = frappe.new_doc("Supplier")
		sup_doc.update(
			{
				'company':self.company,
				'supplier_name' :  self.me_name,
				'supplier_group' :  self.type_of_me,
				"cluster":self.cluster,
				'me_code' : self.me_code,
				'mobile_no_1' :  self.mobile_no,
				'aadhar_card_no' :  self.aadhar_card_no,
				'pan' :  self.pan_no,
				'village' :  self.village,
				'taluka' :  self.taluka,
				'district' :  self.district,
				'state_':self.state,
				'account_holder_name' :  self.account_holder_name,
				'account_number' :  self.account_number,
				'bank_name' :  self.bank_name,
				'ifsc_code' :  self.ifsc_code,
				'branch' :  self.branch,
				'pan_card_photo' :  self.pan_card_photo,
				'aadhar_card_photo' :  self.aadhar_card_photo,
				'bank_passbook_photo' :  self.bank_passbook_photo
			}
		)
		sup_doc.insert()
		self.supplier = sup_doc.name
		addr_doc = frappe.new_doc("Address")
		addr_doc.update(
			{
				"address_title" : sup_doc.name,
				"address_type" : "Billing",
				"address_line1" : self.village,
				"city" : self.taluka,
				"county" : self.district,
				"state" : self.state,
				"pincode" : self.pin_code,
				"company":self.company
			}
		)
		addr_doc.append("links",{
			'link_doctype': 'Supplier',
			'link_name': sup_doc.name
		})
		addr_doc.insert()
		con_doc = frappe.new_doc("Contact")
		con_doc.update(
			{
				"doctype":"Contact",
				"first_name" : sup_doc.name,
				"company":self.company
			}
		)
		con_doc.append("phone_nos",{
			"phone":self.mobile_no,
			"is_primary_phone":1,
			"is_primary_mobile_no":1
		})
		con_doc.append("links",{
			'link_doctype': 'Supplier',
			'link_name': sup_doc.name
		})
		con_doc.insert()
		
	@frappe.whitelist()
	def update_supplier(self):
		sup_doc = frappe.get_doc("Supplier",self.supplier,as_dict=1)
		sup_doc.update(
			{
				'company':self.company,
				'supplier_name' :  self.me_name,
				'supplier_group' :  self.type_of_me,
				"cluster":self.cluster,
				'me_code' : self.me_code,
				'mobile_no_1' :  self.mobile_no,
				'aadhar_card_no' :  self.aadhar_card_no,
				'pan' :  self.pan_no,
				'village' :  self.village,
				'taluka' :  self.taluka,
				'district' :  self.district,
				'state_':self.state,
				'account_holder_name' :  self.account_holder_name,
				'account_number' :  self.account_number,
				'bank_name' :  self.bank_name,
				'ifsc_code' :  self.ifsc_code,
				'branch' :  self.branch,
				'pan_card_photo' :  self.pan_card_photo,
				'aadhar_card_photo' :  self.aadhar_card_photo,
				'bank_passbook_photo' :  self.bank_passbook_photo
			}
		)
		sup_doc.save()
		addr_doc = frappe.get_doc("Address",frappe.db.get_value("Dynamic Link",{'link_doctype': 'Supplier','parenttype':'Address','link_name': sup_doc.name},"parent"))
		addr_doc.update(
			{
				"address_line1" : self.village,
				"city" : self.taluka,
				"county" : self.district,
				"state" : self.state,
				"pincode" : self.pin_code,
				"company":self.company
			}
		)
		addr_doc.save()
		con_doc = frappe.get_doc("Contact",frappe.db.get_value("Dynamic Link",{'link_doctype': 'Supplier','parenttype':'Contact','link_name': sup_doc.name},"parent"))
		con_doc.update({
			"company":self.company
		})
		if self.mobile_no not in [x.phone for x in con_doc.phone_nos]:
			for i in con_doc.phone_nos:
				i.update({
					"is_primary_phone":0,
					"is_primary_mobile_no":0
				})
			con_doc.append("phone_nos",{
				"phone":self.mobile_no,
				"is_primary_phone":1,
				"is_primary_mobile_no":1
			})
		con_doc.save()
