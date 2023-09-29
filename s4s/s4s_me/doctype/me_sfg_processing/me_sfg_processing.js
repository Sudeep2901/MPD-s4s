// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('ME SFG Processing', {
	setup: function(frm){
        frm.fields_dict["items"].grid.get_field(
            "wip_warehouse"
        ).get_query = function (doc) {
            return {
                filters: {
                    'is_group': 0,
                    'company':frm.doc.company
                },
            };
        };

		frm.fields_dict["fg_items_table"].grid.get_field(
            "fg_warehouse"
        ).get_query = function (doc) {
            return {
                filters: {
                    'is_group': 0,
                    'company':frm.doc.company
                },
            };
        };

		frm.set_query('batch', 'items', function(doc, cdt, cdn) {
			var item = locals[cdt][cdn];
			if(!item.item_name) {
				frappe.throw(__("Please enter Item Code to get Batch Number"));
			} else {

				var filters = {
						'item_code': item.item_code
					}

				if (item.wip_warehouse) {
					filters["warehouse"] = item.wip_warehouse;
				}

				return {
					query : "erpnext.controllers.queries.get_batch_no",
					filters: filters
				}
			}
		});


    },
	me_code: function(frm){
		if (frm.doc.me_code){
			frappe.call({
				method:"set_wip_wh",
				args:{me_code:frm.doc.me_code},
				doc:frm.doc,
				callback: function(r){
					if (r.message){
						let data = r.message
						frm.doc.items.forEach(element => {
							element.wip_warehouse = data.wip_wh
						});
						frm.doc.fg_items_table.forEach(element => {
							element.fg_warehouse = data.fg_wh
						});

						frm.refresh_field('items')
						frm.refresh_field('fg_items_table')
					}
				
				}
			})
		}
	},
	
	
});

frappe.ui.form.on("RM Item Details",{
	items_add(frm, cdt, cdn) { 
		let child = locals[cdt][cdn]
		if (frm.doc.me_code){
			frappe.call({
				method:"set_wip_wh",
				args:{me_code:frm.doc.me_code},
				doc:frm.doc,
				callback: function(r){
					if (r.message){
						let data = r.message
						child.wip_warehouse = data.wip_wh
						frm.refresh_field('items')
					}
					
				}
			})
		}

    },
	batch: function(frm,cdt,cdn){
		let child = locals[cdt][cdn]
		frappe.call({
			method:'s4s.public.python.custom_methods.execute',
			args:{filters:{'company': 'Science For Society Techno Services Pvt Ltd', 'from_date': frappe.sys_defaults.year_start_date, 'to_date': frappe.datetime.get_today(), 'item_code': child.item_name, 'warehouse': child.wip_warehouse, 'batch_no': child.batch}},
			callback: function(r){
				child.qty = r.message
				frm.refresh_field('items')
			}
		})
	},

})

frappe.ui.form.on("FG Items Table",{
	fg_items_table_add(frm, cdt, cdn) { 
		let child = locals[cdt][cdn]
		if (frm.doc.me_code){
			frappe.call({
				method:"set_wip_wh",
				args:{me_code:frm.doc.me_code},
				doc:frm.doc,
				callback: function(r){
					if (r.message){
						let data = r.message
						child.fg_warehouse = data.fg_wh
						frm.refresh_field('fg_items_table')
					}
				}
			})
		}

    }

})
