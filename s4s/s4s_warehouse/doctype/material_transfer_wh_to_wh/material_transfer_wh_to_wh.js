// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Material Transfer WH To WH', {
	refresh:function(frm){
		if (frm.doc.docstatus == 1){
			frappe.call({
				method:"material_in_condition",
				doc:frm.doc,
				callback:function(r){
					if(r.message){
						if(r.message == "Success"){
							frm.add_custom_button(__('Material In'), function(){
								frappe.model.open_mapped_doc({
									method: "s4s.s4s_warehouse.doctype.material_transfer_wh_to_wh.material_transfer_wh_to_wh.create_material_in",
									frm:cur_frm
								})
								}).addClass("btn btn-primary btn-sm");

						}
					}
				}
			})
		}
		
		
	},
	onload:function(frm){
		if (frm.is_new()){
			frappe.call({
				method:"fetch_user_details",
				doc:frm.doc,
				callback:function(r){
					if (!frm.doc.sfg_dispatch_request_to_factory && !frm.doc.material_transfer_request_wh_to_wh){
						if(r.message){
							let data = r.message
							frm.set_value("rm_warehouse",data.rm_wh)
						}

					}
					
				}
			})

		}
		
	},
	setup: function(frm) {
		frm.set_query('batch', 'rm_item_details', function(doc, cdt, cdn) {
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
					filters["warehouse"] = frm.doc.rm_warehouse;
				}

				return {
					query : "erpnext.controllers.queries.get_batch_no",
					filters: filters
				}
			}
		});
		
		frm.set_query('wip_warehouse', function(doc) {
			return {
				filters: {
					"is_group": 0,
					"company": frm.doc.company,
					"warehouse_type": "Transit"
				}
			};
		});
		frm.set_query('rm_warehouse', function(doc) {
			return {
				filters: {
					"is_group": 0,
					"company": frm.doc.company
				}
			};
		});


	},
	company: function(frm){
		if(frm.doc.company){
			frm.set_query('wip_warehouse', function(doc) {
				return {
					filters: {
						"is_group": 0,
						"company": frm.doc.company,
						"warehouse_type": "Transit"
					}
				};
			});
			frm.set_query('rm_warehouse', function(doc) {
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

frappe.ui.form.on("S4S Item Details", {
	batch: function(frm,cdt,cdn){
		let child = locals[cdt][cdn]
		frappe.call({
			method:'s4s.public.python.custom_methods.execute',
			args:{filters:{'company': frm.doc.company, 'from_date': frappe.sys_defaults.year_start_date, 'to_date': frappe.datetime.get_today(), 'item_code': child.item_name, 'warehouse': frm.doc.rm_warehouse, 'batch_no': child.batch}},
			callback: function(r){
				child.qty = r.message
				frm.refresh_field('rm_item_details')
			}
		})
	},
})
