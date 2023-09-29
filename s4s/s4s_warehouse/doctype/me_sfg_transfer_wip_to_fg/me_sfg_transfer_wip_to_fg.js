// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('ME SFG Transfer WIP to FG', {
	setup: function(frm) {
		frm.set_query('batch', 'items', function(doc, cdt, cdn) {
			var item = locals[cdt][cdn];
			if(!item.item_name) {
				frappe.throw(__("Please enter Item Code to get Batch Number"));
			} else {
				if (in_list(["Material Transfer for Manufacture", "Manufacture", "Repack", "Send to Subcontractor"], doc.purpose)) {
					var filters = {
						'item_code': item.item_code,
						'posting_date': frm.doc.date || frappe.datetime.nowdate()
					}
				} else {
					var filters = {
						'item_code': item.item_code
					}
				}

				if (frm.doc.purpose != "Material Receipt") {
					filters["warehouse"] = item.wip_warehouse;
				}

				return {
					query : "erpnext.controllers.queries.get_batch_no",
					filters: filters
				}
			}
		});
	},
});


frappe.ui.form.on('RM Item Details',{
	batch: function(frm,cdt,cdn){
		let child = locals[cdt][cdn]
		frappe.call({
			method:'s4s.public.python.custom_methods.execute',
			args:{filters:{'company': 'Science For Society Techno Services Pvt Ltd', 'from_date': frappe.sys_defaults.year_start_date, 'to_date': frappe.datetime.get_today(), 'item_code': child.item_name, 'warehouse': child.wip_warehouse, 'batch_no': child.batch}},
			callback: function(r){
				child.qty = r.message
				frm.refresh_field('items')
			}
		})
	},
})
