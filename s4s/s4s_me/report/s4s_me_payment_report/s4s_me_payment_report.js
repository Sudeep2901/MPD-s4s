// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */


$(document).ready(function() {
	setTimeout(() => {
		let elements = document.querySelectorAll(".dt-cell");
		elements.forEach(element => {
			element.style.textAlign = "left";
		});
	}, 500);
});

let company = []
frappe.call({
	method:'s4s.public.python.custom_methods.set_company_filter_in_report',
	callback: function(r){
		if(r.message){
			company.push(r.message)
		}
	}
}).then(function(){
	frappe.query_reports["S4S ME Payment Report"] = {
		"filters": [
			{
				"fieldname": "company",
				"label": __("Company"),
				"fieldtype": "Link",
				"options":"Company",
				"width": "80",
				"default":company[0]
			},
			{
				"fieldname": "cluster",
				"label": __("Cluster"),
				"fieldtype": "Link",
				"options":"S4S Cluster",
				"width": "80"
			},
			
			{
				"fieldname": "from_date",
				"label": __("From Date"),
				"fieldtype": "Date",
				"width": "80"
			},
			{
				"fieldname": "to_date",
				"label": __("To Date"),
				"fieldtype": "Date",
				"width": "80"
			},
			{
				"fieldname": "me_name",
				"label": __("ME Name"),
				"fieldtype": "Link",
				"width": "80",
				"options": "Supplier"
			},
			
			{
				"fieldname": "summary",
				"label": __("Summary"),
				"fieldtype": "Check",
				"width": "80"
			}
		],
		onload: function(report) {
			document.getElementsByClassName("no-breadcrumbs")[0].addEventListener("mouseover",function(e){
				let elements = document.querySelectorAll(".dt-cell");			
				elements.forEach(element => {
					element.style.textAlign = "left";
				})
			
			})
			
		}
	};
	

})
