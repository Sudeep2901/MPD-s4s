// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('ME SFG QC Check List', {
	setup: function(frm){
		frm.set_query("me_code", () => ({
			filters: { "supplier_group": "ME"},
		}));
	}
});
