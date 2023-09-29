# Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.mapper import get_mapped_doc
import frappe
from frappe.model.document import Document

class S4SFarmerQuery(Document):
	def validate(self):
		buying_price_list = frappe.db.get_single_value("Buying Settings","buying_price_list")
		if buying_price_list:
			price_list_rate = frappe.db.get_value("Item Price",{"item_code": self.item_name,"price_list":buying_price_list},"price_list_rate")
			if price_list_rate:
				if self.rate > price_list_rate:
					frappe.throw('Rate offered price for {0} must be less than {1}'.format(self.item_name,price_list_rate))
	
	def before_save(self):
		if not self.docstatus and self.status!="Inactive":
			self.status="Active"
		if self.s4s_purchase and frappe.db.exists("S4S Purchase",self.s4s_purchase):
				sp=frappe.get_doc("S4S Purchase",self.s4s_purchase)
				if sp.docstatus==0:
					self.status="Pending"
				if sp.docstatus==1:
					self.status="Completed"
					
@frappe.whitelist()
def make_s4s_purchase(source_name, target_doc=None):
	inward_wh = None
	if frappe.db.get_value("S4S User details",{'name':frappe.session.user},['name']):
		user_det = frappe.get_doc("S4S User details",frappe.session.user)
		inward_wh = user_det.inward_warehouse
	farmer_query = frappe.get_doc("S4S Farmer Query",source_name)
	if farmer_query:
		s4s_supplier = frappe.get_doc("S4S Supplier",farmer_query.supplier)
		if s4s_supplier.supplier:
			get_supplier_doc = frappe.get_doc("Supplier",s4s_supplier.supplier)
			doc = frappe.new_doc("S4S Purchase")
			doc.supplier = get_supplier_doc.name
			doc.supplier_name = get_supplier_doc.supplier_name
			doc.company = farmer_query.company
			doc.s4s_farmer_query = farmer_query.name
			doc.delivery_location = farmer_query.delivery_location
			doc.vlcc_name = farmer_query.vlcc_name
			doc.cc_name = farmer_query.cc_name
			doc.village = farmer_query.village
			doc.taluka = farmer_query.taluka
			doc.district = farmer_query.district
			doc.state = farmer_query.state
			if inward_wh:
				doc.set_warehouse = inward_wh
			doc.append("purchase_receipt_details",{
				"item_code":farmer_query.item_code,
				"item_name":farmer_query.item_name,
				"variety":farmer_query.variety,
				"moisture":farmer_query.moisture,
				"rate":farmer_query.rate
			})
			# doc.supplier_deductions = "Supplier Deduction - SFSTS"
			# doc.supplier_deductions = frappe.db.get_value("Purchase Taxes and Charges Template",{'title':['like',"%Supplier Deduction%"],'company':farmer_query.company},['name'])
			values = [{"category": "Total",
					  "add_deduct_tax": "Deduct",
					  "charge_type": "Actual",
					  "included_in_print_rate": 0,
					  "included_in_paid_amount": 0,
					  "account_head": "Hamali Charges - SFSTS",
					  "description": "Hamali Charges",
					  "cost_center": "Main - SFSTS",
					  "account_currency": "INR",
					 },
					 {"category": "Total",
					  "add_deduct_tax": "Deduct",
					  "charge_type": "Actual",
					  "included_in_print_rate": 0,
					  "included_in_paid_amount": 0,
					  "account_head": "Tolai Charges - SFSTS",
					  "description": "Tolai Charges",
					  "cost_center": "Main - SFSTS",
					  "account_currency": "INR",
					 },
					 {"category": "Total",
					  "add_deduct_tax": "Deduct",
					  "charge_type": "Actual",
					  "included_in_print_rate": 0,
					  "included_in_paid_amount": 0,
					  "account_head": "Upner Charges - SFSTS",
					  "description": "Upner Charges",
					  "cost_center": "Main - SFSTS",
					  "account_currency": "INR",
					  },
					 {
					  "category": "Total",
					  "add_deduct_tax": "Deduct",
					  "charge_type": "Actual",
					  "included_in_print_rate": 0,
					  "included_in_paid_amount": 0,
					  "account_head": "Transport Charges - SFSTS",
					  "description": "Transport Charges",
					  "cost_center": "Main - SFSTS",
					  "account_currency": "INR"
					  },
					 {"category": "Total",
					  "add_deduct_tax": "Deduct",
					  "charge_type": "Actual",
					  "included_in_print_rate": 0,
					  "included_in_paid_amount": 0,
					  "account_head": "Other Charges - SFSTS",
					  "description": "Other Charges",
					  "cost_center": "Main - SFSTS",
					  "account_currency": "INR",
					 }]
			for row in values:
				doc.append("taxes",{
    	            "category": row['category'],
					"add_deduct_tax": row['add_deduct_tax'],
					"charge_type": row['charge_type'],
					"included_in_print_rate": row['included_in_print_rate'],
					"included_in_paid_amount": row['included_in_paid_amount'],
					"account_head": row['account_head'],
					"description": row['description'],
					"cost_center": row['cost_center'],
					"account_currency": row['account_currency']
    	        })
			
			return doc
		else:
			frappe.throw(source_name+" this farmer is not Approved Supplier.")