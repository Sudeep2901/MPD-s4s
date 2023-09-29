// Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('ME Material Request', {
	before_submit: function(frm) {
		frappe.call({
			method:"make_material_request",
			doc:frm.doc,
			callback:function(r){
				frm.refresh_field("material_request");
			}
		})
	}
});
