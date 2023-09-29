// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Material Transfer Request WH To WH', {
	setup: function(frm) {
		frm.set_query('batch', 'sfg_material_details', function(doc, cdt, cdn) {
			var item = locals[cdt][cdn];
			if(!item.item_name) {
				frappe.throw(__("Please enter Item Code to get Batch Number"));
			} else {
			
				var filters = {
					'item_code': item.item_name
				}

				if (frm.doc.source_warehouse) {
					filters["warehouse"] = frm.doc.source_warehouse;
				}

				return {
					query : "erpnext.controllers.queries.get_batch_no",
					filters: filters
				}
			}
		});

		if (frm.doc.company) {
			frm.set_query('source_warehouse', function(doc) {
				return {
					filters: {
						"is_group": 0,
						"company": frm.doc.company,
						"warehouse_type": ["!=","Transit"]
					}
				};
			});
	
			frm.set_query('target_warehouse', function(doc) {
				return {
					filters: {
						"is_group": 0,
						"company": frm.doc.company,
						"warehouse_type": "Transit"
					}
				};
			});
	
		}

	},
	refresh: function(frm){
		if (frm.doc.docstatus == 1){
			frappe.call({
				method:"material_tfr_condition",
				doc:frm.doc,
				callback:function(r){
					if(r.message){
						if(r.message == "Success"){
							frm.add_custom_button(__('Material Transfer'), function(){
								frappe.model.open_mapped_doc({
									method: "s4s.s4s_warehouse.doctype.material_transfer_request_wh_to_wh.material_transfer_request_wh_to_wh.create_material_tfr",
									frm:cur_frm
								})
								}).addClass("btn btn-primary btn-sm");

						}
					}
				}
			})
		}
	},
	company: function(frm){
		if (frm.doc.company) {
			frm.set_query('source_warehouse', function(doc) {
				return {
					filters: {
						"is_group": 0,
						"company": frm.doc.company,
						"warehouse_type": ["!=","Transit"]
					}
				};
			});
	
			frm.set_query('target_warehouse', function(doc) {
				return {
					filters: {
						"is_group": 0,
						"company": frm.doc.company,
						"warehouse_type": "Transit"
					}
				};
			});
	
		}
	}
});

frappe.ui.form.on("S4S Material Request To Factory", {
	batch: function(frm,cdt,cdn){
		let child = locals[cdt][cdn]
		frappe.call({
			method:'s4s.public.python.custom_methods.execute',
			args:{filters:{'company': frm.doc.company, 'from_date': frappe.sys_defaults.year_start_date, 'to_date': frappe.datetime.get_today(), 'item_code': child.item_name, 'warehouse': frm.doc.source_warehouse, 'batch_no': child.batch}},
			callback: function(r){
				child.qty = r.message
				frm.refresh_field('sfg_material_details')
			}
		})
	},
})