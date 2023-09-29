// Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('S4S Farmer Query', {
	supplier: function(frm) {
		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "S4S Supplier",
				name: frm.doc.supplier,
			},
			callback(r) {
				if(r.message) {
					var s4s_sup = r.message;
					frm.set_value("supplier_name",s4s_sup.supplier_name);
					frm.refresh_field("supplier_name");
					frm.set_value("mobile_no",s4s_sup.mobile_no);
					frm.refresh_field("mobile_no");
					frm.set_value("vlcc_name",s4s_sup.vlcc_name);
					frm.refresh_field("vlcc_name");
					frm.set_value("cc_name",s4s_sup.cc_name);
					frm.refresh_field("cc_name");
					frm.set_value("village",s4s_sup.village);
					frm.refresh_field("village");
					frm.set_value("taluka",s4s_sup.taluka);
					frm.refresh_field("taluka");
					frm.set_value("district",s4s_sup.district);
					frm.refresh_field("district");
					frm.set_value("state",s4s_sup.state);
					frm.refresh_field("state");
				}
			}
		});		
	},
	item_name:function(frm){
		frappe.db.get_single_value('Buying Settings', 'buying_price_list').then(buying_price_list => {
			if(buying_price_list){
				frappe.call({
					method: "frappe.client.get_value",
					args: {
						"doctype": "Item Price",
						"filters": {
							"item_code": frm.doc.item_name,
							"price_list":buying_price_list,
						},
						"fieldname":"price_list_rate"
					}, 
					callback: function(r) {
						frm.set_value("rate",r.message["price_list_rate"])
						frm.refresh_field("rate")
					}
				});
			}
		});
	},
	refresh:function(frm){
		$("#add_transaction").on("click",() =>{
			frappe.model.open_mapped_doc({
				method: "s4s.s4s_vlcc.doctype.s4s_farmer_query.s4s_farmer_query.make_s4s_purchase",
				frm:cur_frm
			})
		})
	},
	item_code:function(frm){
		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Item",
				name: frm.doc.item_code,
			},
			callback(r) {
				if(r.message) {
					var doc = r.message;
					frm.set_value("item_name",doc.item_name);
					frm.refresh_field("item_name");
				}
			}
		});
	}
});
