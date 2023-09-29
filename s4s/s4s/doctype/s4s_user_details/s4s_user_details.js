// Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('S4S User details', {
	setup: function(frm) {

		if (frm.doc.company) {
			frm.set_query("inward_warehouse", function() {
				return {
					filters: {
						'company': frm.doc.company,
					}
				}
			});
			frm.set_query("transit_warehouse", function() {
				return {
					filters: {
						'company': frm.doc.company,
					}
				}
			});
		}

	},
	company: function(frm){
		if (frm.doc.company) {
			frm.set_query("inward_warehouse", function() {
				return {
					filters: {
						'company': frm.doc.company,
					}
				}
			});
			frm.set_query("transit_warehouse", function() {
				return {
					filters: {
						'company': frm.doc.company,
					}
				}
			});
		}


	}
});
