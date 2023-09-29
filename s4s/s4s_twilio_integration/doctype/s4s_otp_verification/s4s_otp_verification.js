// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('S4S OTP Verification', {
	fetch_users: function(frm) {
		frappe.call({
			method:"fetch_data",
			doc:frm.doc,
			callback:function(r){
				frm.refresh_field("users");
				// frm.save()
			}
		})
	}
});
