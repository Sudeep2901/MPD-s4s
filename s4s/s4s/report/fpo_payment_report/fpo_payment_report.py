# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns(filters)
	conditions = get_conditions(filters)
	data = get_data(conditions,filters)
	if not data:
		return [], [], None, []
	return columns, data 

def get_columns(filters):
	columns = [
		{
			'fieldname': 'date',
			'label': "Date",
			'fieldtype': 'Date'
		},
		{
			'fieldname': 'cc_name',
			'label': "CC Name",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'farmer_id',
			'label': "Farmer ID",
			'fieldtype': 'Link',
			'options':"Supplier"
		},
		{
			'fieldname': 'farmer_name',
			'label': "Farmer Name",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'transaction_no',
			'label': "Transaction No",
			'fieldtype': 'Link',
			'options':'Purchase Receipt'
		},
		{
			'fieldname': 'crop_name',
			'label': "Crop Name",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'qty',
			'label': "Qty",
			'fieldtype': 'Int'
		},
		{
			'fieldname': 'purchase_receipt',
			'label': "Purchase Receipt",
			'fieldtype': 'Link',
			'options':"Purchase Receipt"
		},
		{
			'fieldname': 'amount',
			'label': "Amount",
			'fieldtype': 'Currency'
		},
		{
			'fieldname': 'batch_no',
			'label': "Batch Number",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'delivery_no',
			'label': "Delivery Number",
			'fieldtype': 'Link',
			'options':"Delivery Note"
		},
		{
			'fieldname': 'delivery_date',
			'label': "Delivery Date",
			'fieldtype': 'Date'
		},

		{
			'fieldname': 'fpo_pi_no',
			'label': "FPO PI Number",
			'fieldtype': 'Link',
			'options':'Proforma Invoice'
		},
		{
			'fieldname': 'fpo_pi_date',
			'label': "FPO PI Date",
			'fieldtype': 'Date'
		},
		{
			'fieldname': 's4s_grn_no',
			'label': "S4S GRN Number",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 's4s_grn_date',
			'label': "S4S GRN Date",
			'fieldtype': 'Date'
		},
		{
			'fieldname': 'fpo_purchase_order',
			'label': "FPO Purchase Order",
			'fieldtype': 'Link',
			'options':'FPO Purchase Order'
		},
		{
			'fieldname': 'fpo_purchase_date',
			'label': "FPO Purchase Date",
			'fieldtype': 'Date'
		},
		{
			'fieldname': 'sales_order_no',
			'label': "Sales Order Number",
			'fieldtype': 'Link',
			'options':'Sales Order'
		},
		{
			'fieldname': 'sales_order_date',
			'label': "Sales Order Date",
			'fieldtype': 'Date'
		},
		{
			'fieldname':'status',
			'label':"Status",
			'fieldtype':'Data'
		}
		
		
	]
	return columns

def get_conditions(filters):
	conditions=""
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and s4s_p.transaction_date between %(from_date)s and %(to_date)s"
	if filters.get("company"):
		conditions += " and s4s_p.company = %(company)s"
	if filters.get("cc_name"):
		conditions += " and s4s_p.cc_name = %(cc_name)s"
	# if filters.get("vlcc_name"):
	# 	conditions += " and s4s_p.vlcc_name = %(vlcc_name)s"
	# if filters.get("inward_warehouse"):
	# 	conditions += " and s4s_p.set_warehouse = %(inward_warehouse)s"
	if filters.get("status"):
		conditions += " and s4s_p.docstatus = 1" if filters.get("status") == "Submitted" else " and s4s_p.docstatus = 0"
	return conditions

def get_data(conditions,filters):
	data = frappe.db.sql(
		"""
		SELECT
			s4s_p.transaction_date,
			s4s_p.cc_name,
			s4s_p.supplier,
			s4s_p.supplier_name,
			s4s_p.name,
			variant.item_name,
			s4s_p.total_weight,
			pr.name,
			s4s_p.total_amount,
			vr.batch_no,
			dn.name as dn_name,
			dn.posting_date,
			pi.name,
			pi.posting_date,
			" ",
			" ",
			dn.po_no,
			dn.po_date,
			so.name,
			so.transaction_date,
				CASE 
                WHEN s4s_p.docstatus = 1 THEN 'Submitted'
                ELSE 'Draft'
            END
			

		FROM
			`tabS4S Purchase` as s4s_p
		INNER JOIN 
			`tabS4S Purchase receipt` AS variant 
		ON 
			variant.parent = s4s_p.name

		LEFT JOIN
			`tabPurchase Receipt` AS pr
		ON
			s4s_p.name = pr.s4s_purchase
	
		LEFT JOIN 
			`tabPurchase Receipt Item` AS vr 
		ON 
			vr.parent = pr.name

		LEFT JOIN
			`tabDelivery Note Item` AS dni
		ON
			dni.batch_no = vr.batch_no
			
		LEFT JOIN
			`tabDelivery Note` as dn
		ON
			dni.parent = dn.name

		LEFT JOIN
			`tabProforma Invoice` as pi
		ON 
			dn.proforma_invoice = pi.name
		

		LEFT JOIN
			`tabSales Order` as so
		ON
			dn.sales_order = so.name

		WHERE 
			s4s_p.docstatus != 2 and 
			s4s_p.name != ""
			{0}		
		ORDER BY 
			s4s_p.transaction_date DESC

		""".format(
		conditions
	    ),filters
	)
	
	return data