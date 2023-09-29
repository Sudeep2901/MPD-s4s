// Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('SFG Data Processing', {
	finish_batch:function(frm){
		frappe.call({
			method:"finish_batch",
			doc:frm.doc,
			callback:function(r){
				frm.refresh_field("finish_batch_entry");
				frm.save();
			}
		})
	},
	refresh:function(frm){
		console.log(frm.fields_dict["wip_to_sfg_item"])
		frm.get_field("custom_save").$input.addClass("btn-primary");
		frm.get_field("custom_submit").$input.addClass("btn-primary");
		frm.get_field("finish_batch").$input.addClass("btn-primary");
		cur_frm.get_field("finish_batch_entry").grid.cannot_add_rows = true;
		cur_frm.refresh_field("finish_batch_entry")
	},
	custom_save:function(frm){
		frappe.call({
			method:"on_save_btn",
			doc:frm.doc,
			args:{
				"rm_to_wip_item":frm.doc.rm_to_wip_item
			},
			callback:function(r){
				frm.refresh_field("rm_to_wip_stock_entry");
				frm.save();
			}
		})
	},
	custom_submit:function(frm){
		frappe.call({
			method:"on_submit_btn",
			doc:frm.doc,
			args:{
				"rm_to_wip_item":frm.doc.rm_to_wip_item
			},
			callback:function(r){
				cur_frm.refresh_fields("se_submitted");
				cur_frm.refresh_fields("rm_to_wip_item");
				cur_frm.refresh_field("batch_no");
				cur_frm.refresh_field("batch_qty");
				cur_frm.refresh_field("batch_qty_uom");
				cur_frm.refresh_field("wip_to_sfg_item");
				window.location.reload();
			}
		})
	},
	dcm_name:function(frm){
		if(frm.doc.dcm_name){
			frappe.call({
				method:"frappe.client.get",
				args:{
					"doctype":"DCM List",
					"name":frm.doc.dcm_name
				},
				callback:function(r){
					frm.set_value("source_rm_location",r.message.rm_location);
					frm.set_value("target_wip_location",r.message.wip_location);
					frm.set_value("source_wip_location",r.message.wip_location);
					frm.set_value("target_sfg_location",r.message.sfg_location);
				}
			})
		}
	},
	item_code:function(frm){
		if(frm.doc.item_code){
			frappe.call({
				method:"fetch_rm_items",
				doc:frm.doc,
				callback:function(r){
					frm.refresh_field("rm_to_wip_item");
					frm.refresh_field("wip_item");
					frm.refresh_field("bom");
				}
			})
		}		
	},
	setup:function(frm){
		frm.set_query('batch_no', 'rm_to_wip_item', function(doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			if(!d.item_code){
				frappe.throw(__("Please enter Item Code to get Batch Number"));
			}else{
				return {
					query : "erpnext.controllers.queries.get_batch_no",
					filters: {
						'item_code': d.item_code,
						'warehouse':d.source_location
					}
				}
			}
		})
		frm.set_query('batch_no', 'wip_to_sfg_item', function(doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			if(!d.sfg_product){
				frappe.throw(__("Please enter Item Code to get Batch Number"));
			}else{
				return {
					query : "erpnext.controllers.queries.get_batch_no",
					filters: {
						'item_code': d.sfg_product,
						'warehouse':frm.source_wip_location
					}
				}
			}
		})
	}
});
frappe.ui.form.on("RM To WIP Item",{
	rm_to_wip_item_add:function(frm,cdt,cdn){
		var d = locals[cdt][cdn]
		frappe.call({
			method:"frappe.client.get",
			args:{
				"doctype":"Item",
				"name":frm.doc.item_code
			},
			callback:function(r){
				d.source_location = frm.doc.source_rm_location;
				d.item_code = frm.doc.item_code;
				d.uom = r.message.stock_uom;
				frm.refresh_field("rm_to_wip_item");
			}
		})
	}
})
frappe.ui.form.on("WIP To SFG Item",{
	wip_to_sfg_item_add:function(frm,cdt,cdn){
		let d = locals[cdt][cdn]
		if(frm.doc.bom){
			frappe.call({
				method:"frappe.client.get",
				args:{
					"doctype":"Item",
					"name":frm.doc.item_code
				},
				callback:function(r){
					d.date = frappe.datetime.nowdate();
					d.sfg_product = r.message.dcm_item_mapping[0].sfg_item;
					d.uom = r.message.stock_uom;
					frm.refresh_field("wip_to_sfg_item");
				}
			})
		}
	},
	custom_save:function(frm,cdt,cdn){
		var d = locals[cdt][cdn]
		if(!d.stock_entry){
			frappe.call({
				method:"on_child_save",
				doc:frm.doc,
				args:{
					"d":d
				},
				callback:function(r){
					frappe.model.set_value(d.doctype, d.name, 'stock_entry', r.message);
					frm.save();
				}
			})
		}
	},
	custom_submit:function(frm,cdt,cdn){
		var d = locals[cdt][cdn]
		if(d.stock_entry){
			frappe.call({
				method:"on_child_submit",
				doc:frm.doc,
				args:{
					"d":d
				},
				callback:function(r){
					frappe.model.set_value(d.doctype, d.name, 'se_submitted', r.message.se_submitted);
					frappe.model.set_value(d.doctype, d.name, 'batch_no', r.message.batch_no);
					frm.set_value("batch_qty",r.message.batch_qty);
					frm.save();
				}
			})
		}
	}
})