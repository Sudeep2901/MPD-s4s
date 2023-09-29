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


def get_conditions(filters):
	conditions=""
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and s4s_p.transaction_date between %(from_date)s and %(to_date)s"
	if filters.get("company"):
		conditions += " and s4s_p.company = %(company)s"
	if filters.get("cc_name"):
		conditions += " and s4s_p.cc_name = %(cc_name)s"
	if filters.get("vlcc_name"):
		conditions += " and s4s_p.vlcc_name = %(vlcc_name)s"
	if filters.get("inward_warehouse"):
		conditions += " and s4s_p.set_warehouse = %(inward_warehouse)s"
	if filters.get("status"):
		# conditions += " and s4s_p.docstatus = %(status)s"
		conditions += " and s4s_p.docstatus = 1" if filters.get("status") == "Submitted" else " and s4s_p.docstatus = 0"
	return conditions


def get_data(conditions,filters):
	data = frappe.db.sql("""
		SELECT
			s4s_p.timestamp,
			s4s_p.transaction_date,
			s4s_p.name ,
			s4s_p.supplier_name ,
			s4s_p.cc_name ,
			s4s_p.vlcc_name ,
			s4s_p.set_warehouse,
			variant.item_name ,
			variant.variety ,
			variant.moisture ,
			s4s_p.total_weight,
			s4s_p.kadta,
			s4s_p.weight_after_kadta ,
			variant.rate,
			s4s_p.total_amount ,
			s4s_p.total_deduction_amount,
			s4s_p.grand_total, 
			s.account_holder_name ,
			s.bank_name ,
			s.account_number ,
			s.ifsc_code,
			s.mobile_no_1,
			s4s_p.grand_total ,
			s4s_p.name,
			pr.name,
			pi.name,
			s4s_p.company ,
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
		INNER JOIN
			`tabSupplier` as s
		ON	
			s.name = s4s_p.supplier
		LEFT JOIN
			`tabPurchase Receipt` AS pr
		ON
			s4s_p.name = pr.s4s_purchase
		LEFT JOIN
			`tabPurchase Invoice` AS pi
		ON
			s4s_p.name = pi.s4s_purchase
		WHERE 
			s4s_p.docstatus != 2 and 
			s4s_p.name != ""
			{0}
	""".format(
		conditions
	    ),filters
		)
	
	return data

def get_columns(filters):
	columns = [
		{
			'fieldname': 'timestamp',
			'label': "Timestamp",
			'fieldtype': 'Datetime'
		},
		{
			'fieldname':'s4s_receipt',
			'label':'Receipt Date',
			'fieldtype':'Date'
		},
		{
			'fieldname':'receipt_no',
			'label':'Receipt Number',
			"fieldtype":'Link',
			'options':'S4S Purchase'
		},
		{
			'fieldname': 'farmer_name',
			'label': "Farmer Name",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'cc_name',
			'label': "CC Name",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'vlcc_name',
			'label': "VLCC Name",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'inward_warehouse',
			'label': "Inward Warehouse",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'crop_name',
			'label': "Crop Name",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'quality',
			'label': "Quality",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'moisture',
			'label': "Moisture %",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'total_weight',
			'label': "Total Weight",
			'fieldtype': 'Float',
			'precision':2
		},
		{
			'fieldname': 'kadta',
			'label': "Kadta %",
			'fieldtype': 'Select',
			'options':"\n1\n2\n3\n4\n5"
		},
		{
			'fieldname': 'weight_after_kadta',
			'label': "Weight After Kadta",
			'fieldtype': 'Float',
			'precision':2
		},
		{
			'fieldname': 'rate_kg',
			'label': "Rate/KG",
			'fieldtype': 'Currency'
		},
		{
			'fieldname': 'total_amount',
			'label': "Total Amount",
			'fieldtype': 'Currency'
		},
		{
			'fieldname': 'total_deduction_amount',
			'label': "Total Deduction Amount",
			'fieldtype': 'Currency'
		},
		{
			'fieldname': 'grand_total',
			'label': "Net Total Amount",
			'fieldtype': 'Currency'
		},
		{
			'fieldname': 'bnf_name',
			'label': "BNF Name",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'bank_name',
			'label': "Bank Name",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'bank_acc_no',
			'label': "Bank Account Number",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'bank_ifsc',
			'label': "Bank IFSC",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'bank_mobile',
			'label': "Bank Mobile Number",
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'amount',
			'label': "Amount",
			'fieldtype': 'Currency'
		},
		{
			'fieldname': 'grn_number',
			'label': "GRN Number",
			'fieldtype': 'Link',
			'options':'S4S Purchase'
		},
		{
			'fieldname': 'system_purchase_receipt',
			'label': "System Purchase Receipt",
			'fieldtype': 'Link',
			'options':'Purchase Receipt'
		},
		{
			'fieldname': 'system_purchase_invoice',
			'label': "System Purchase Invoice",
			'fieldtype': 'Link',
			'options':'Purchase Invoice'
		},
		{
			'fieldname': 'company',
			'label': "Company",
			'fieldtype': 'Link',
			'options':"Company"
		},
		{
			"fieldname":'status',
			"label":'Status',
			'fieldtype':'Select',
			'options':'\nSubmitted\nDraft'
		}
	]
	return columns