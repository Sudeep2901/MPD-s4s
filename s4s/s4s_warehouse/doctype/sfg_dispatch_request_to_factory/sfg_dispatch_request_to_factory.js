// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('SFG Dispatch Request To Factory', {
	refresh: function(frm){
		if (frm.doc.docstatus == 1) {
			frappe.call({
				method:'btn_condition',
				doc:frm.doc,
				callback:function(r){
					if (r.message){
						if (r.message == "Success"){
							frm.add_custom_button(__('SFG Transfer'), function () {
								frappe.model.open_mapped_doc({
									method: "s4s.s4s_warehouse.doctype.sfg_dispatch_request_to_factory.sfg_dispatch_request_to_factory.make_sfg_transfer",
									frm: cur_frm
								})
								
							}).addClass('btn-primary');;

						}
					}
				}
			})
			
		}
	},
	setup: function(frm){
		if(frm.is_new()){
			frappe.call({
				method:'set_factory_warehouse',
				doc:frm.doc,
				callback: function(r){
					if(r.message){
						frm.set_value('factory_warehouse',r.message)
					}
				}
			})
		}
		frm.set_query('sfg_warehouse', function(doc) {
				   return {
					   filters: {
						   "is_group": 0,
						   "company": doc.company
					   }
				   };
			   });
	   frm.set_query('factory_warehouse', function(doc) {
		   return {
			   filters: {
				   "is_group": 0,
				   "company": doc.company,
				   "warehouse_type":"Transit"
			   }
		   };
	   });
	   
	  
	   frm.set_query('batch', 'sfg_material_details', function(doc, cdt, cdn) {
		   var item = locals[cdt][cdn];
		   if(!item.item_code) {
			   frappe.throw(__("Please enter Item Code to get Batch Number"));
		   } else {

			   var filters = {
					   'item_code': item.item_code
				   }

			   if (frm.doc.sfg_warehouse) {
				   filters["warehouse"] = frm.doc.sfg_warehouse;
			   }

			   return {
				   query : "erpnext.controllers.queries.get_batch_no",
				   filters: filters
			   }
		   }
	   });


   },

   comapny: function(frm){
	   if(frm.doc.company){
		   frm.set_query('sfg_warehouse', function(doc) {
			   return {
				   filters: {
					   "is_group": 0,
					   "company": doc.company
				   }
			   };
		   });
		   frm.set_query('factory_warehouse', function(doc) {
			   return {
				   filters: {
					   "is_group": 0,
					   "company": doc.company
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
			args:{filters:{'company': frm.doc.company, 'from_date': frappe.sys_defaults.year_start_date, 'to_date': frappe.datetime.get_today(), 'item_code': child.item_name, 'warehouse': frm.doc.sfg_warehouse, 'batch_no': child.batch}},
			callback: function(r){
				child.qty = r.message
				frm.refresh_field('sfg_material_details')
			}
		})
	},
})
