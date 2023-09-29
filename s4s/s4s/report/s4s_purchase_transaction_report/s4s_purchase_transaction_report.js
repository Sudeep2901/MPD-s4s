// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */



frappe.query_reports["S4S Purchase Transaction Report"] = {
    "filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options":"Company"
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_days(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "cc_name",
			"label": __("CC Name"),
			"fieldtype": "Link",
			"options":"S4S CC List"
		},
		{
			"fieldname": "vlcc_name",
			"label": __("VLCC Name"),
			"fieldtype": "Link",
			"options":"S4S VLCC List"
		},
		{
			"fieldname": "inward_warehouse",
			"label": __("Inward Warehouse"),
			"fieldtype": "Link",
			"options":"Warehouse"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options":"\nDraft\nSubmitted"
		},
	]
};