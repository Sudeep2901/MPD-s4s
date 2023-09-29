// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Price List Report"] = {
	"filters": [
		{
			"fieldname": "item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"options":"Item",
			"width": "80"
		},
		{
			"fieldname": "price_list",
			"label": __("Price List"),
			"fieldtype": "Link",
			"options":"Price List",
			"width": "80"
		},
		{
			"fieldname": "type",
			"label": __("Price List Type"),
			"fieldtype": "Select",
			"options":["Buying","Selling"],
			"width": "80"
		},
	]
};
