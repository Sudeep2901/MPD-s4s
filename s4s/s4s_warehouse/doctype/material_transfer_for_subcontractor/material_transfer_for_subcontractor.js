// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Material Transfer for Subcontractor', {
	onload:function(frm){
		setTimeout(() => {
			if (frm.is_new()){
				frappe.call({
					method:"fetch_user_details",
					doc:frm.doc,
					callback:function(r){
						if(r.message){
							let data = r.message
							frm.set_value("rm_warehouse",data.rm_wh)
						}
					}
				})
	
			}
		}, 100);

		
	},
	setup: function(frm) {
		frm.trigger('onload')
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
						'item_code': item.item_name,
						"warehouse":frm.doc.rm_warehouse
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

	},
	refresh:function(frm){
		
		frappe.call({
			method:'btn_cond_check',
			doc:frm.doc,
			callback:function(r){
				if(frm.doc.docstatus == 1 && r.message == "Yes"){
					frm.add_custom_button(__('Return From Subcontractor'), function(){
						frappe.model.open_mapped_doc({
							method: "s4s.s4s_warehouse.doctype.material_transfer_for_subcontractor.material_transfer_for_subcontractor.create_return_subcon_entry",
							frm:cur_frm
						})
						}).addClass("btn btn-primary btn-sm");
				}
			}
		})
	}
	
});

frappe.ui.form.on("S4S Item Details", {
	batch: function(frm,cdt,cdn){
		let child = locals[cdt][cdn]
		frappe.call({
			method:'s4s.public.python.custom_methods.execute',
			args:{filters:{'company': 'Science For Society Techno Services Pvt Ltd', 'from_date': frappe.sys_defaults.year_start_date, 'to_date': frappe.datetime.get_today(), 'item_code': child.item_name, 'warehouse': frm.doc.rm_warehouse, 'batch_no': child.batch}},
			callback: function(r){
				child.qty = r.message
				frm.refresh_field('rm_item_details')
			}
		})
	},
})
