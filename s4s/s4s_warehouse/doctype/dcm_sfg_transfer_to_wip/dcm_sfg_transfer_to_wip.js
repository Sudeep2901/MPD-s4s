// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('DCM SFG Transfer to WIP', {
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
					frm.add_custom_button(__('Create FG Entry'), function(){
						// frappe.model.open_mapped_doc({
						// 	method: "s4s.s4s_warehouse.doctype.dcm_sfg_transfer_to_wip.dcm_sfg_transfer_to_wip.create_fg_entry",
						// 	frm:cur_frm
						// })
						}).addClass("btn btn-primary btn-sm");
				}
			}
		})
	},
	wip_warehouse:function(frm){
			frm.doc.rm_item_details.forEach(function(row){
				row.wip_warehouse = frm.doc.wip_warehouse;
				frm.refresh_field('rm_item_details');
			});

		
		
	}
	
});

frappe.ui.form.on('RM Item Details',{
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
	rm_item_details_add:function(frm, cdt, cdn) { 
        let child = locals[cdt][cdn]
		if(frm.doc.wip_warehouse){
			child.wip_warehouse = frm.doc.wip_warehouse
		}
    }
	
	
})
