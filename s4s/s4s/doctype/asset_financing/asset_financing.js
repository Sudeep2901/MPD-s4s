// Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Asset Financing', {
	// refresh: function(frm) {

	// }
	me_lead : function(frm) {
		frappe.call({
			"method": "frappe.client.get",
			args: {
				doctype: "ME Lead",
				name: frm.doc.me_lead
			},
			callback: function (data) {
				frm.set_value("me_lead_name", data.message.lead_name);
				frm.refresh_field("me_lead_name");
			}
		})
	}
});
