// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('ME SFG Dispatch Note', {
	refresh: function(frm){
		if (frm.doc.docstatus == 1){
			frappe.call({
				method:"sfg_material_btn_condition",
				doc:frm.doc,
				callback: function(r){
					if (r.message){
						if(r.message == "Success"){
							console.log("",r.message.bold())
							frm.add_custom_button(__('SFG Material In'), function(){
								frappe.model.open_mapped_doc({
									method: "s4s.s4s_me.doctype.me_sfg_dispatch_note.me_sfg_dispatch_note.create_sfg_material_in",
									frm:cur_frm
								})
								}).addClass("btn btn-primary btn-sm");

						}
					}

				}
			})
			
		}
	},
	setup: function(frm) {
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
					filters["warehouse"] = frm.doc.me_warehouse;
				}

				return {
					query : "erpnext.controllers.queries.get_batch_no",
					filters: filters
				}
			}
		});
		frm.set_query('me_warehouse', function(doc) {
			return {
				filters: {
					"is_group": 0,
					"company": frm.doc.company
				}
			};
		});
		frm.set_query('cc_warehouse', function(doc) {
			return {
				filters: {
					"is_group": 0,
					"company": frm.doc.company
				}
			};
		});


	},
	me_code:function(frm){
		frappe.call({
			method:"set_warehouses",
			doc:frm.doc,
			callback:function(r){
				if (r.message != "No"){
					frm.set_value("me_warehouse",r.message[0])
					frm.set_value("cc_warehouse",r.message[1])
				}
			}
		})
	},
	company: function(frm){
		if(frm.doc.company){
			frm.set_query('me_warehouse', function(doc) {
				return {
					filters: {
						"is_group": 0,
						"company": frm.doc.company
					}
				};
			});
			frm.set_query('cc_warehouse', function(doc) {
				return {
					filters: {
						"is_group": 0,
						"company": frm.doc.company
					}
				};
			});
	

		}
	}

});

frappe.ui.form.on("DCM Dispatch Item", {
	batch_no: function(frm,cdt,cdn){
		let child = locals[cdt][cdn]
		frappe.call({
			method:'s4s.public.python.custom_methods.execute',
			args:{filters:{'company': 'Science For Society Techno Services Pvt Ltd', 'from_date': frappe.sys_defaults.year_start_date, 'to_date': frappe.datetime.get_today(), 'item_code': child.item_name, 'warehouse': frm.doc.me_warehouse, 'batch_no': child.batch_no}},
			callback: function(r){
				child.qty = r.message
				frm.refresh_field('me_dispatch_item')
			}
		})
	},
})
