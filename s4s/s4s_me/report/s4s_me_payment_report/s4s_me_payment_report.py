# Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate


def execute(filters=None):
	columns = get_columns(filters)
	conditions = get_conditions(filters)
	data = get_data(conditions, filters)
	if not data:
		return [], [], None, []


	return columns, data

def get_conditions(filters):
	conditions = ""
	if filters.get("me_name"):
		conditions += " and se.s4ssupplier = %(me_name)s"

	if filters.get("from_date") and filters.get("to_date"):
		if filters.get("from_date") > filters.get("to_date"):
			frappe.throw("From Date Cannot Be Greater Than To Date.")
		conditions += " and se.posting_date between %(from_date)s and %(to_date)s"
	
	if filters.get("company"):
		conditions += " and rdp.company = %(company)s"
	
	if filters.get("cluster"):
		conditions += " and sup.cluster = %(cluster)s"

	return conditions


def get_data(conditions, filters):
	if filters.get("summary") != 1:
		data = frappe.db.sql(
			"""
			SELECT
				rdp.name as rdp_name,
				sid.item_code,
				rdp.date as posting_date,
				se.name as stock_entry,
				sup.me_code as sup_me_code,
				se.s4ssupplier as app_me,
				se.me_name as se_me_name,
				sup.cluster as cluster,
				sup.village as village_name,
				sup.mobile_no_1 as mo_no,
				sup.bank_name as bank_name,
				sup.account_number as account_no,
				sup.ifsc_code as ifsc_code,
				sup.branch as branch,
				spp.sfg_processing_batch_rate as batch_rate,
				spp.sfg_processing_electricity_rate as electricity_rate,
				sed.qty as loaded_batch,
				sed.qty/50 as no_batches,
				(sed.qty/50)*(spp.sfg_processing_batch_rate + spp.sfg_processing_electricity_rate) as total_amount

			FROM
				`tabS4S Item Details` sid
			LEFT JOIN
				`tabME RM Daily Processing` rdp ON sid.parent = rdp.name
			LEFT JOIN 
				`tabStock Entry` se ON se.me_rm_daily_processing = rdp.name and se.stock_entry_type = "Material Transfer For Manufacture"
			LEFT JOIN 
				`tabStock Entry Detail` sed on sed.parent = se.name
			LEFT JOIN 
				`tabSupplier` sup ON sup.name = se.s4ssupplier
			LEFT JOIN
				`tabSFG Processing Price` spp ON sup.cluster = spp.cluster AND spp.docstatus = 1 

			WHERE
				sid.docstatus = 1 and rdp.stock_entry_type = "Material Transfer For Manufacture"
				{0}
		""".format(
				conditions
			),
			filters,
			as_dict=1,
		)

		error_count = 0
		clusters = []
		for row in data:															
			doc = frappe.db.get_value("SFG Processing Price",{'cluster':row.cluster,'docstatus':1},['parent','name'])		
			if doc:
				spl = frappe.get_doc("S4S SFG Price List",doc[0])	
				if spl.active == 1:
					batch_rate = frappe.db.get_value("SFG Processing Price",{'name':doc[1]},['sfg_processing_batch_rate'])
					el_rate = frappe.db.get_value("SFG Processing Price",{'name':doc[1]},['sfg_processing_electricity_rate'])

					row.update({
						'batch_rate':batch_rate,
						'electricity_rate':el_rate,
						'total_amount':row.no_batches*(batch_rate + el_rate)
					})
				else:
					error_count += 1
					clusters.append(row.cluster)
			else:
				error_count += 1
				clusters.append(row.cluster)
		
		if error_count > 0:
			if len(list(dict.fromkeys(clusters))) == 1:
				frappe.throw(f"S4S SFG Price List Not Found or Not Active for Cluster {frappe.bold(clusters[0])}")
			else:
				frappe.msgprint(title="S4S SFG Price List Not Found or Not Active for Clusters:",msg=list(dict.fromkeys(clusters)),as_list=True,indicator='red')
		else:
			return data
	else:
    	
		data = frappe.db.sql(
			"""
			SELECT
				sup.supplier_name as supplier_name,
				sup.cluster as cluster,
				sup.me_code as me_code,
				sup.village as village_name,
				se.s4ssupplier as me_name,
				sup.mobile_no_1 as mo_no,
				sup.bank_name as bank_name,
				sup.account_number as account_no,
				sup.ifsc_code as ifsc_code,
				sup.branch as branch,
				spp.sfg_processing_batch_rate as batch_rate,
				spp.sfg_processing_electricity_rate as electricity_rate,
				SUM(sed.qty) as loaded_batch,
				SUM(sed.qty)/50 as no_batches,
				(SUM(sed.qty)/50)*(spp.sfg_processing_batch_rate+spp.sfg_processing_electricity_rate) as total_amount
				
			FROM
				`tabS4S Item Details` sid
			LEFT JOIN
				`tabME RM Daily Processing` rdp ON sid.parent = rdp.name
			LEFT JOIN 
				`tabStock Entry` se ON se.me_rm_daily_processing = rdp.name and se.stock_entry_type = "Material Transfer For Manufacture"
			LEFT JOIN 
				`tabStock Entry Detail` sed on sed.parent = se.name
			LEFT JOIN 
				`tabSupplier` sup ON sup.name = se.s4ssupplier
			LEFT JOIN
				`tabSFG Processing Price` spp ON sup.cluster = spp.cluster AND spp.docstatus = 1 
	
			WHERE
				sid.docstatus = 1 and se.stock_entry_type = "Material Transfer For Manufacture"
				{0}
			GROUP BY 
				se.s4ssupplier

		""".format(
				conditions
			),
			filters,
			as_dict=1,
		)
		error_count = 0
		clusters = []
		for row in data:															
			doc = frappe.db.get_value("SFG Processing Price",{'cluster':row.cluster,'docstatus':1},['parent','name'])		
			if doc:
				spl = frappe.get_doc("S4S SFG Price List",doc[0])	
				if spl.active == 1:
					batch_rate = frappe.db.get_value("SFG Processing Price",{'name':doc[1]},['sfg_processing_batch_rate'])
					el_rate = frappe.db.get_value("SFG Processing Price",{'name':doc[1]},['sfg_processing_electricity_rate'])

					row.update({
						'batch_rate':batch_rate,
						'electricity_rate':el_rate,
						'total_amount':row.no_batches*(batch_rate + el_rate)
					})
				else:
					error_count += 1
					clusters.append(row.cluster)
			else:
				error_count += 1
				clusters.append(row.cluster)

	
		if error_count > 0:
			if len(list(dict.fromkeys(clusters))) == 1:
				frappe.throw(f"S4S SFG Price List Not Found or Not Active for Cluster {frappe.bold(clusters[0])}")
			else:
				frappe.msgprint(title="S4S SFG Price List Not Found or Not Active for Clusters:",msg=list(dict.fromkeys(clusters)),as_list=True,indicator='red')
		else:
			return data
	
def get_columns(filters):
	if filters.get("summary")!=1:
		columns = [
			{
				"label":_(frappe.bold("Document Name")),
				"fieldname":"rdp_name",
				"fieldtype":"Link",
				"options":"ME RM Daily Processing",
				"width":160
			},
			
			{
				"label":_(frappe.bold("RM Item Name")),
				"fieldname":"item_code",
				"fieldtype":"Link",
				"options":"Item",
				"width":160
			},
			{
				"label": _(frappe.bold("Posting Date")),
				"fieldname": "posting_date",
				"fieldtype": "Date",
				"width": 160,
			},
			{
				"label":_(frappe.bold("System Stock Entry Number")),
				"fieldname":"stock_entry",
				"fieldtype":"Link",
				"options":"Stock Entry",
				"width":160
			},
			{
				"label": _(frappe.bold("ME CODE")),
				"fieldname": "sup_me_code",
				"fieldtype": "Data",
				"width": 160
			},
			{
				"label": _(frappe.bold("ME NAME")),
				"fieldname": "se_me_name",
				"fieldtype": "Data",
				"width": 160,
			},
			{
				"label": _(frappe.bold("APPROVED ME")),
				"fieldname": "app_me",
				"fieldtype": "Link",
				"options":"Supplier",
				"width": 160,
			},
			{
				"label": _(frappe.bold("CLUSTER")),
				"fieldname": "cluster",
				"fieldtype": "Link",
				"options":"S4S Cluster",
				"width": 160,
			},
			{
				"label": _(frappe.bold("VILLAGE NAME")),
				"fieldname": "village_name",
				"fieldtype": "Link",
				"options":"S4S Village List",
				"width": 160,
			},
			{
				"label": _(frappe.bold("MOBILE NUMBER")),
				"fieldname": "mo_no",
				"fieldtype": "Data",
				"width": 160,
			},
			{
				"label": _(frappe.bold("BANK NAME")),
				"fieldname": "bank_name",
				"fieldtype": "Link",
				"options":"S4S Bank List",
				"width": 160,
			},	
			{
				"label": _(frappe.bold("ACCOUNT NO")),
				"fieldname": "account_no",
				"fieldtype": "Data",
				"width": 160,
			},	
			{
				"label": _(frappe.bold("IFSC CODE")),
				"fieldname": "ifsc_code",
				"fieldtype": "Data",
				"width": 160,
			},		
			{
				"label": _(frappe.bold("BRANCH")),
				"fieldname": "branch",
				"fieldtype": "Data",
				"width": 160,
			},		
			{
				"label": _(frappe.bold("BATCH RATE (PER KG)")),
				"fieldname": "batch_rate",
				"fieldtype": "Currency",
				"width": 160,
			},		
			{
				"label": _(frappe.bold("ELECTRICITY RATE (PER BATCH)")),
				"fieldname": "electricity_rate",
				"fieldtype": "Currency",
				"width": 160,
			},		
			{
				"label": _(frappe.bold("LOADED BATCH ( IN KG)")),
				"fieldname": "loaded_batch",
				"fieldtype": "Float",
				"width": 160,
				"precision":2
			},		
			{
				"label": _(frappe.bold("NO. BATCHES")),
				"fieldname": "no_batches",
				"fieldtype": "Float",
				"width": 160,
				"precision":2
			},		
			{
				"label": _(frappe.bold("TOTAL AMOUNT")),
				"fieldname": "total_amount",
				"fieldtype": "Currency",
				"width": 160,
			},
		]
	else:
		columns = [
			{
				"label": _(frappe.bold("ME CODE")),
				"fieldname": "me_code",
				"fieldtype": "Data",
				"width": 160,
			},
			{
				"label": _(frappe.bold("ME NAME")),
				"fieldname": "supplier_name",
				"fieldtype": "Data",
				"width": 160,
			},
			{
				"label": _(frappe.bold("APPROVED ME")),
				"fieldname": "me_name",
				"fieldtype": "Link",
				"options":"Supplier",
				"width": 160,
			},
			{
				"label": _(frappe.bold("CLUSTER")),
				"fieldname": "cluster",
				"fieldtype": "Link",
				"options":"S4S Cluster",
				"width": 160,
			},
			{
				"label": _(frappe.bold("VILLAGE NAME")),
				"fieldname": "village_name",
				"fieldtype": "Link",
				"options":"S4S Village List",
				"width": 160,
			},
			{
				"label": _(frappe.bold("MOBILE NUMBER")),
				"fieldname": "mo_no",
				"fieldtype": "Data",
				"width": 160,
			},
			{
				"label": _(frappe.bold("BANK NAME")),
				"fieldname": "bank_name",
				"fieldtype": "Link",
				"options":"S4S Bank List",
				"width": 160,
			},	
			{
				"label": _(frappe.bold("ACCOUNT NO")),
				"fieldname": "account_no",
				"fieldtype": "Data",
				"width": 160,
			},	
			{
				"label": _(frappe.bold("IFSC CODE")),
				"fieldname": "ifsc_code",
				"fieldtype": "Data",
				"width": 160,
			},		
			{
				"label": _(frappe.bold("BRANCH")),
				"fieldname": "branch",
				"fieldtype": "Data",
				"width": 160,
			},		
			{
				"label": _(frappe.bold("BATCH RATE (PER KG)")),
				"fieldname": "batch_rate",
				"fieldtype": "Currency",
				"width": 160,
			},		
			{
				"label": _(frappe.bold("ELECTRICITY RATE (PER BATCH)")),
				"fieldname": "electricity_rate",
				"fieldtype": "Currency",
				"width": 160,
			},		
			{
				"label": _(frappe.bold("LOADED BATCH ( IN KG)")),
				"fieldname": "loaded_batch",
				"fieldtype": "Float",
				"width": 160,
				"precision":2
			},		
			{
				"label": _(frappe.bold("NO. BATCHES")),
				"fieldname": "no_batches",
				"fieldtype": "Float",
				"width": 160,
				"precision":2
			},		
			{
				"label": _(frappe.bold("TOTAL AMOUNT")),
				"fieldname": "total_amount",
				"fieldtype": "Currency",
				"width": 160,
			},
		]
	return columns
	