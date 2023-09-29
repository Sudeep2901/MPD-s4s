// Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('S4S Price List', {
	refresh: function(frm) {
		frm.doc.price_list_name = frm.doc.date
		frm.refresh_field("price_list_name");
	}
});
frappe.ui.form.on('S4S Item Price',{
	item_code:function(frm,cdt,cdn){
		var d = locals[cdt][cdn]
		if(d.item_code){
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Item",
					name: d.item_code,
				},
				callback(r) {
					if(r.message) {
						var doc = r.message;
						d.item_name = doc.item_name
						d.uom = doc.stock_uom
						frm.refresh_field("item_price_list");
					}
				}
			});
		}
	}
})