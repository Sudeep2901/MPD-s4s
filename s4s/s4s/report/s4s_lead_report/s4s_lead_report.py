# Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate
import pandas as pd
import datetime


def execute(filters=None):
	columns = get_columns(filters)
	conditions = get_conditions(filters)

	data = get_data(conditions, filters)
	if not data:
		return [], [], None, []

	# data, chart_data,report_summary = prepare_data(data, filters)

	return columns, data #, None, chart_data,report_summary


def get_conditions(filters):
	conditions = ""
	if filters.get("created_from") and filters.get("created_to"):
		conditions += " and ml.creation between %(created_from)s and %(created_to)s"
	if filters.get("modified_from") and filters.get("modified_to"):
		conditions += " and ml.modified between %(modified_from)s and %(modified_to)s"
      
	return conditions

def get_data(conditions, filters):
		
	data = frappe.db.sql(
		"""
		SELECT
			ml.name as me_lead,
			CASE ml.docstatus
				WHEN "0" THEN "Draft"
				WHEN "1" THEN "Submitted"
				WHEN "2" THEN "Cancelled"
			END AS doc_status,
			ml.owner as doc_owner,
			ml.creation as created_date,
			ml.modified as modified_date,
			ml.lead_name as lead_name,
			ml.lead_date as lead_generation_date,
			ml.status as lead_status,
			ml.lead_owner as lead_owner,
			ml.lead_type as lead_type,
			ml.address_type as address_type,
			ml.village as village,
			ml.taluka as taluka,
			ml.district as district,
			ml.state as state,

			qif.name as lead_qualification_form,
   			CASE qif.docstatus
				WHEN "0" THEN "Draft"
				WHEN "1" THEN "Submitted"
				WHEN "2" THEN "Cancelled"
			END AS qif_status,
			qif.owner as qif_doc_owner,
			qif.creation as qif_created_date,
			qif.modified as qif_modified_date,
			qif.lead_qualification_owner as lead_qualification_owner

		FROM
			`tabME Lead` ml
		LEFT JOIN `tabLead Qualification Form` qif
			ON  ml.name = qif.me_lead

		WHERE
			ml.name !=""
			{0}
			
	""".format(
			conditions
		),
		filters,
		as_dict=1,
	)
	return data

def get_columns(filters):
	columns = [
		{
			"label": _("ME Lead"),
			"fieldname": "me_lead",
			"fieldtype": "Link",
			"options": "ME Lead",
			"width": 160,
		},
		{
			"label": _("Doc Status"),
			"fieldname": "doc_status",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": "Doc Owner",
			"fieldname": "doc_owner",
			"fieldtype": "Link",
			"options": "User",
			"width": 160
		},
  		{
			"label": _("Created Date"),
			"fieldname": "created_date",
			"fieldtype": "Date",
			"width": 160
		},
		{
			"label": _("Modified Date"),
			"fieldname": "modified_date",
			"fieldtype": "Date",
			"width": 160
		},
		{
			"label": _("Lead Name"),
			"fieldname": "lead_name",
			"fieldtype": "Data",
			"width": 160,
		},
  		{
			"label": _("Lead Generation Date"),
			"fieldname": "lead_generation_date",
			"fieldtype": "Date",
			"width": 160
		},
		{
			"label": _("Lead Status"),
			"fieldname": "lead_name",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Lead Owner"),
			"fieldname": "lead_owner",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Lead Type"),
			"fieldname": "lead_type",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Address Type"),
			"fieldname": "address_type",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": _("Village"),
			"fieldname": "village",
			"fieldtype": "Link",
			"options": "S4S Village List",
			"width": 160,
		},
		{
			"label": _("Taluka"),
			"fieldname": "taluka",
			"fieldtype": "Link",
			"options": "S4S Taluka List",
			"width": 160,
		},
		{
			"label": _("District"),
			"fieldname": "district",
			"fieldtype": "Link",
			"options": "S4S District List",
			"width": 160,
		},
		{
			"label": _("State"),
			"fieldname": "state",
			"fieldtype": "Link",
			"options": "S4S State",
			"width": 160,
		},
  
		{
			"label": _("Lead Qualification Form"),
			"fieldname": "lead_qualification_form",
			"fieldtype": "Link",
			"options": "Lead Qualification Form",
			"width": 160,
		},
		{
			"label": _("QIF Status"),
			"fieldname": "qif_status",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": "QIF Doc Owner",
			"fieldname": "qif_doc_owner",
			"fieldtype": "Link",
			"options": "User",
			"width": 160
		},
  		{
			"label": _("QIF Created Date"),
			"fieldname": "qif_created_date",
			"fieldtype": "Date",
			"width": 160
		},
		{
			"label": _("QIF Modified Date"),
			"fieldname": "qif_modified_date",
			"fieldtype": "Date",
			"width": 160
		},
		{
			"label": "QIF Lead Qualification Owner",
			"fieldname": "lead_qualification_owner",
			"fieldtype": "Link",
			"options": "User",
			"width": 160
		},
	]

	

	return columns
	
