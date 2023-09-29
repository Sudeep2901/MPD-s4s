// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('S4S Inter Company Warehouse Settings', {
	setup: function(frm) {
		frm.set_query('warehouse', 's4s_inter_company_warehouse', function(doc, cdt, cdn) {
			var item = locals[cdt][cdn];
			if(!item.company) {
				frappe.throw(__("Please enter FPO Company to get Warehouse!"));
			} else {
				
				let filters = {
					"is_group":0,
					"company":item.company
				}

				return {
					filters: filters
				}
			}
		});
		frm.set_query('warehouse_1', 's4s_inter_company_warehouse', function(doc, cdt, cdn) {
			var item = locals[cdt][cdn];
			if(!item.company_1) {
				frappe.throw(__("Please enter S4S Company to get Warehouse!"));
			} else {
				
				let filters = {
					"is_group":0,
					"company":item.company_1
				}

				return {
					filters: filters
				}
			}
		});

	}
});
