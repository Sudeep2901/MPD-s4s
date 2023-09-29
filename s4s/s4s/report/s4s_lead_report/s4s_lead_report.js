// Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["S4S Lead Report"] = {
	"filters": [
		{
			"fieldname": "created_from",
			"label": __("Created From"),
			"fieldtype": "Date",
			"width": "80"
		},
		{
			"fieldname": "created_to",
			"label": __("Created To"),
			"fieldtype": "Date",
			"width": "80"
		},
		{
			"fieldname": "modified_from",
			"label": __("Modified From"),
			"fieldtype": "Date",
			"width": "80"
		},
		{
			"fieldname": "modified_to",
			"label": __("Modified To"),
			"fieldtype": "Date",
			"width": "80"
		}
	]
};