// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('ME SFG Transfer to WIP', {
	onload: function(frm) {
		if (frm.is_new()){
			frappe.call({
				method:"fetch_user_details",
				doc:frm.doc,
				callback:function(r){
					if(r.message){
						let data = r.message
						frm.set_value("rm_warehouse",data.rm_wh)
						frm.set_value("wip_warehouse",data.wip_wh)
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
						'item_code': item.item_code,
						'posting_date': frm.doc.date || frappe.datetime.nowdate()
					}
				} else {
					var filters = {
						'item_code': item.item_code
					}
				}

				if (frm.doc.purpose != "Material Receipt") {
					filters["warehouse"] = item.warehouse || frm.doc.rm_warehouse;
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
					frm.add_custom_button(__('Create FG Entry'), function(){
						frappe.model.open_mapped_doc({
							method: "s4s.s4s_warehouse.doctype.me_sfg_transfer_to_wip.me_sfg_transfer_to_wip.create_fg_entry",
							frm:cur_frm
						})
						}).addClass("btn btn-primary btn-sm");
				}
			}
		})
	}
	
});
