// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('ME SFG Dispatch Request', {
	refresh: function(frm) {
		if (frm.doc.docstatus == 1){
			frm.add_custom_button(__('Material Transfer'), function(){
				frappe.model.open_mapped_doc({
					method: "s4s.s4s_me.doctype.me_sfg_dispatch_request.me_sfg_dispatch_request.make_transfer",
					frm:cur_frm
				})
				}).addClass("btn btn-primary btn-sm");

		}

		
	},
	setup: function(frm) {
		frm.set_query("me_code", function() {
			return {
				"filters": {
					"supplier_group": "ME",
					
				}
			};
		});

		frm.set_query('batch_no', 'me_dispatch_item', function(doc, cdt, cdn) {
			var item = locals[cdt][cdn];
			if(!item.item_name) {
				frappe.throw(__("Please enter Item Code to get Batch Number"));
			} else {
				if (in_list(["Material Transfer for Manufacture", "Manufacture", "Repack", "Send to Subcontractor"], doc.purpose)) {
					var filters = {
						'item_code': item.item_name,
						'posting_date': frm.doc.posting_date || frappe.datetime.nowdate()
					}
				} else {
					var filters = {
						'item_code': item.item_name
					}
				}

				// User could want to select a manually created empty batch (no warehouse)
				// or a pre-existing batch
				if (frm.doc.purpose != "Material Receipt") {
					filters["warehouse"] = item.warehouse || frm.doc.me_warehouse;
				}

				return {
					query : "erpnext.controllers.queries.get_batch_no",
					filters: filters
				}
			}
		});

	},
	me_code: function(frm){
		frappe.call({
			method:'get_me_warehouse',
			doc:frm.doc,
			callback: function(r){
				console.log("rrrrrrrrrr",r.message)
				frm.set_value("me_warehouse",r.message)
			}
		})
	}
});

frappe.ui.form.on('DCM Dispatch Item',{
	item_name: function(frm,cdt,cdn){
		let child = locals[cdt][cdn]
		frappe.call({
			method:'get_uom',
			doc:cur_frm.doc,
			callback: function(r){
				frm.refresh_field('me_dispatch_item')
			}
		});
	},

	form_render: function(frm,cdt,cdn){
		let child = locals[cdt][cdn]
		child.warehouse = frm.doc.me_warehouse
		frm.refresh_field('me_dispatch_item')
	},

	batch_no: function(frm,cdt,cdn){
		let child = locals[cdt][cdn]
		frappe.call({
			method:'get_batch_qty',
			doc:cur_frm.doc,
			callback: function(r){
				frm.refresh_field('me_dispatch_item')
			}
		})
	},
	
})
