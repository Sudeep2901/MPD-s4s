// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('RM Return ME WH To Village WH', {
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
				}
			};
		});
		frm.set_query('rm_warehouse', function(doc) {
			return {
				filters: {
					"is_group": 0,
					"company": frm.doc.company,

				}
			};
		});
	},
	me_code: function(frm){
		if(frm.doc.me_code){
			frappe.call({
				method:"get_me_details",
				doc:frm.doc,
				args:{me_code:frm.doc.me_code},
				callback:function(r){
					if(r.message){
						let data = r.message
						frm.set_value('rm_warehouse',data.me_rm_wh)
						frm.set_value('wip_warehouse',data.village_rm_wh)
					}

				}
			})
		}
	}
});
