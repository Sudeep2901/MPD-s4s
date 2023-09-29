# Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate


def execute(filters=None):
	# if not filters:
	# 	return [], []

	columns = get_columns(filters)
	conditions = get_conditions(filters)
	data = get_data(conditions, filters)
	if not data:
		return [], [], None, []

	# data, chart_data,report_summary = prepare_data(data, filters)

	return columns, data #, None, chart_data,report_summary


def get_conditions(filters):
	conditions = ""
	if filters.get("me_name"):
		conditions += " and se.s4ssupplier = %(me_name)s"

	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and se.posting_date between %(from_date)s and %(to_date)s"

	return conditions


def get_data(conditions, filters):
	if filters.get("summary")!=1:
		data = frappe.db.sql(
			"""
			SELECT
				sed.item_code as item_code,
				se.posting_date as posting_date,
				se.name as document_no,
				s.supplier_name as supplier_name,
				s.cluster as cluster,
				s.me_code as me_code,
				s.village as village_name,
				se.s4ssupplier as me_name,
				s.mobile_no_1 as mo_no,
				s.bank_name as bank_name,
				s.account_number as account_no,
				s.ifsc_code as ifsc_code,
				s.branch as branch,
				spp.sfg_processing_batch_rate as batch_rate,
				spp.sfg_processing_electricity_rate as electricity_rate,
				sed.qty as loaded_batch,
				sed.qty/50 as no_batches,
				(sed.qty/50)*(spp.sfg_processing_batch_rate+spp.sfg_processing_electricity_rate) as total_amount
				
			FROM
				`tabStock Entry Detail` sed
			JOIN
				`tabStock Entry` se ON sed.parent = se.name
				
			LEFT JOIN 
				`tabSupplier` s ON s.name = se.s4ssupplier
				
			LEFT JOIN
				`tabSFG Processing Price` spp ON s.cluster = spp.cluster
			LEFT JOIN `tabS4S SFG Price List` sspl ON spp.parent = sspl.name AND sspl.docstatus = 1 AND sspl.active = 1
	
			WHERE
				se.docstatus = 1 and se.purpose = "Manufacture" AND sed.s_warehouse IS NOT NULL AND se.s4ssupplier IS NOT NULL
				{0}
		""".format(
				conditions
			),
			filters,
			as_dict=1,
		)
	else:
    	
		data = frappe.db.sql(
			"""
			SELECT
				s.supplier_name as supplier_name,
				s.cluster as cluster,
				s.me_code as me_code,
				s.village as village_name,
				se.s4ssupplier as me_name,
				s.mobile_no_1 as mo_no,
				s.bank_name as bank_name,
				s.account_number as account_no,
				s.ifsc_code as ifsc_code,
				s.branch as branch,
				spp.sfg_processing_batch_rate as batch_rate,
				spp.sfg_processing_electricity_rate as electricity_rate,
				SUM(sed.qty) as loaded_batch,
				SUM(sed.qty)/50 as no_batches,
				(SUM(sed.qty)/50)*(spp.sfg_processing_batch_rate+spp.sfg_processing_electricity_rate) as total_amount
				
			FROM
				`tabStock Entry Detail` sed
			JOIN
				`tabStock Entry` se ON sed.parent = se.name
				
			LEFT JOIN 
				`tabSupplier` s ON s.name = se.s4ssupplier
				
			LEFT JOIN
				`tabSFG Processing Price` spp ON s.cluster = spp.cluster
			LEFT JOIN `tabS4S SFG Price List` sspl ON spp.parent = sspl.name AND sspl.docstatus = 1 AND sspl.active = 1
	
			WHERE
				se.docstatus = 1 and se.purpose = "Manufacture" AND sed.s_warehouse IS NOT NULL AND se.s4ssupplier IS NOT NULL
				{0}
			GROUP BY 
				se.s4ssupplier
		""".format(
				conditions
			),
			filters,
			as_dict=1,
		)
	return data
	
def get_columns(filters):
	if filters.get("summary")!=1:
		columns = [
			
			{
				"label":_("RM Item Name"),
				"fieldname":"item_code",
				"fieldtype":"Link",
				"options":"Item",
				"width":160
			},
			{
				"label": _("Posting Date"),
				"fieldname": "posting_date",
				"fieldtype": "Date",
				"width": 160,
			},
			{
				"label":_("Document Number"),
				"fieldname":"document_no",
				"fieldtype":"Link",
				"options":"Stock Entry",
				"width":160
			},
			{
				"label": _("ME CODE"),
				"fieldname": "me_code",
				"fieldtype": "Data",
				"width": 160,
			},
			{
				"label": _("ME NAME"),
				"fieldname": "supplier_name",
				"fieldtype": "Data",
				"width": 160,
			},
			{
				"label": _("APPROVED ME"),
				"fieldname": "me_name",
				"fieldtype": "Link",
				"options":"Supplier",
				"width": 160,
			},
			{
				"label": _("CLUSTER"),
				"fieldname": "cluster",
				"fieldtype": "Link",
				"options":"S4S Cluster",
				"width": 160,
			},
			{
				"label": _("VILLAGE NAME"),
				"fieldname": "village_name",
				"fieldtype": "Link",
				"options":"S4S Village List",
				"width": 160,
			},
			{
				"label": _("MO. NO"),
				"fieldname": "mo_no",
				"fieldtype": "Data",
				"width": 160,
			},
			{
				"label": _("BANK NAME"),
				"fieldname": "bank_name",
				"fieldtype": "Link",
				"options":"S4S Bank List",
				"width": 160,
			},	
			{
				"label": _("ACCOUNT NO"),
				"fieldname": "account_no",
				"fieldtype": "Data",
				"width": 160,
			},	
			{
				"label": _("IFSC CODE"),
				"fieldname": "ifsc_code",
				"fieldtype": "Data",
				"width": 160,
			},		
			{
				"label": _("BRANCH"),
				"fieldname": "branch",
				"fieldtype": "Data",
				"width": 160,
			},		
			{
				"label": _("BACTH RATE (PER KG)"),
				"fieldname": "batch_rate",
				"fieldtype": "Currency",
				"width": 160,
			},		
			{
				"label": _("ELECTRICITY RATE (PER BATCH)"),
				"fieldname": "electricity_rate",
				"fieldtype": "Currency",
				"width": 160,
			},		
			{
				"label": _("LOADED BATCH ( IN KG)"),
				"fieldname": "loaded_batch",
				"fieldtype": "Float",
				"width": 160,
				"precision":2
			},		
			{
				"label": _("NO. BATCHES"),
				"fieldname": "no_batches",
				"fieldtype": "Float",
				"width": 160,
				"precision":3
			},		
			{
				"label": _("TOTAL AMOUNT"),
				"fieldname": "total_amount",
				"fieldtype": "Currency",
				"width": 160,
			},
		]
	else:
		columns = [
			{
				"label": _("ME CODE"),
				"fieldname": "me_code",
				"fieldtype": "Data",
				"width": 160,
			},
			{
				"label": _("ME NAME"),
				"fieldname": "supplier_name",
				"fieldtype": "Data",
				"width": 160,
			},
			{
				"label": _("APPROVED ME"),
				"fieldname": "me_name",
				"fieldtype": "Link",
				"options":"Supplier",
				"width": 160,
			},
			{
				"label": _("CLUSTER"),
				"fieldname": "cluster",
				"fieldtype": "Link",
				"options":"S4S Cluster",
				"width": 160,
			},
			{
				"label": _("VILLAGE NAME"),
				"fieldname": "village_name",
				"fieldtype": "Link",
				"options":"S4S Village List",
				"width": 160,
			},
			{
				"label": _("MO. NO"),
				"fieldname": "mo_no",
				"fieldtype": "Data",
				"width": 160,
			},
			{
				"label": _("BANK NAME"),
				"fieldname": "bank_name",
				"fieldtype": "Link",
				"options":"S4S Bank List",
				"width": 160,
			},	
			{
				"label": _("ACCOUNT NO"),
				"fieldname": "account_no",
				"fieldtype": "Data",
				"width": 160,
			},	
			{
				"label": _("IFSC CODE"),
				"fieldname": "ifsc_code",
				"fieldtype": "Data",
				"width": 160,
			},		
			{
				"label": _("BRANCH"),
				"fieldname": "branch",
				"fieldtype": "Data",
				"width": 160,
			},		
			{
				"label": _("BACTH RATE (PER KG)"),
				"fieldname": "batch_rate",
				"fieldtype": "Currency",
				"width": 160,
			},		
			{
				"label": _("ELECTRICITY RATE (PER BATCH)"),
				"fieldname": "electricity_rate",
				"fieldtype": "Currency",
				"width": 160,
			},		
			{
				"label": _("LOADED BATCH ( IN KG)"),
				"fieldname": "loaded_batch",
				"fieldtype": "Float",
				"width": 160,
				"precision":2
			},		
			{
				"label": _("NO. BATCHES"),
				"fieldname": "no_batches",
				"fieldtype": "Float",
				"width": 160,
				"precision":3
			},		
			{
				"label": _("TOTAL AMOUNT"),
				"fieldname": "total_amount",
				"fieldtype": "Currency",
				"width": 160,
			},
		]
	return columns
	