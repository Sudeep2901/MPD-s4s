// Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('SFG Dispatch Request', {
	trip_end:function(frm){
		frm.set_value("approval_status","Close Request");
	},
	approval_status:function(frm){
		if(frm.doc.__islocal || frm.doc.docstatus===0){
			frappe.call({
				method:"frappe.client.get",
				args:{
					doctype:"User",
					name:frappe.session.user
				},
				callback:function(r){
					var result = r.message;
					if(result.roles){
						result.roles.forEach(row => {
							if(row.role === "DCM Field Supervisor"){
								frm.set_value("approval_status","");
							}
						});
					}
				}
			})
		}
		if(frm.doc.approval_status){
			frappe.call({
				method:"frappe.client.get",
				args:{
					doctype:"User",
					name:frappe.session.user
				},
				callback:function(r){
					var result = r.message;
					if(result.roles){
						result.roles.forEach(row => {
							if(row.role === "DCM Supervisor"){
								if(frm.doc.approval_status.includes("Approve by DCM Supervisor","Reject by DCM Supervisor")){
									frm.set_value("dcm_supervisor",1);
								}
							}
						})
					}
				}
			})
		}
		if(frm.doc.approval_status && frm.doc.docstatus===1){
			frappe.call({
				method:"frappe.client.get",
				args:{
					doctype:"User",
					name:frappe.session.user
				},
				callback:function(r){
					var result = r.message;
					if(result.roles){
						result.roles.forEach(row => {
							if(row.role === "DCM Supervisor"){
								if(frm.doc.approval_status.includes("Approve by DCM Supervisor","Reject by DCM Supervisor")){
									frm.set_value("dcm_supervisor",1);
								}
							}
							if(row.role === "CC User" || row.role === "VLCC User"){
								if(frm.doc.approval_status.includes("Approve by CC Supervisor")){
									frm.set_value("cc_user",1);
								}
							}
							if(row.role === "Factory RM Store Manager"){
								if(frm.doc.approval_status==="Approve by Factory Supervisor"){
									frm.set_value("factory_rm_store_manager",1);
								}
							}
							if(row.role === "Logistic Supervisor"){
								if(frm.doc.approval_status==="Accept by Logistic Supervisor"){
									frm.set_value("logistic_supervisor",1);
								}
							}
						});
					}
				}
			})
		}
	},
	onload:function(frm){
		frappe.call({
			method:"set_options",
			doc:frm.doc,
			args:{
				"s_user" : frappe.session.user
			},
			callback:function(r){
				const result = r.message;
				if(typeof(result) === "object"){
					frm.set_df_property("approval_status", "options", result);
				}
			}
		})
	},
	refresh: function(frm){
		frappe.call({
			method:"frappe.client.get",
			args:{
				doctype:"User",
				name:frappe.session.user
			},
			callback:function(r){
				var result = r.message;
				if(result.roles){
					result.roles.forEach(row => {
						if(row.role === "DCM Supervisor"){
							if(frm.doc.dcm_supervisor==1){
								cur_frm.set_df_property("approval_status","options",[frm.doc.approval_status]);
							}
						}
						if(row.role === "CC User" || row.role === "VLCC User"){
							if(frm.doc.cc_user===1){
								frm.set_df_property("approval_status","options",[frm.doc.approval_status]);
							}
						}
						if(row.role === "Logistic Supervisor"){
							if(frm.doc.logistic_supervisor===1){
								frm.set_df_property("approval_status","options",[frm.doc.approval_status]);
							}
						}
						if(row.role === "Factory RM Store Manager"){
							if(frm.doc.factory_rm_store_manager===1){
								frm.set_df_property("approval_status","options",[frm.doc.approval_status]);
							}
						}
					});
				}
			}
		})
	
		// let s = []
		// frappe.db.get_value("Stock Entry",{'sfg_dispatch_request':frm.doc.name,"docstatus":['!=',2]},['name','docstatus']).then(function(r){
		// 	s.push(r.message.name)
		// 	s.push(r.message.docstatus)
		// })
		if (frm.doc.docstatus==1){
			frappe.call({
				method:'check_role',
				doc:frm.doc,
				callback: function(r){
					if (r.message){
						if ((r.message.includes("DCM Supervisor") || r.message.includes("DCM Field Supervisor")) && r.message.includes("Success")){
							// if (s[0] === undefined){
								frm.add_custom_button(__('Material Transfer'), function(){
									frappe.model.open_mapped_doc({
										method: "s4s.s4s_dcm.doctype.sfg_dispatch_request.sfg_dispatch_request.make_transfer",
										frm:cur_frm
									})
									}).addClass("btn btn-primary btn-sm");
							// }
						}
					}
				}
			})
			frappe.call({
				method:'role_check',
				doc:frm.doc,
				callback: function(r){
					if (r.message){
						if (r.message == "Success"){
							frm.add_custom_button(__('SFG Material In'), function(){
								frappe.model.open_mapped_doc({
									method: "s4s.s4s_dcm.doctype.sfg_dispatch_request.sfg_dispatch_request.make_sfg_material_in",
									frm:cur_frm
								})
								}).addClass("btn btn-primary btn-sm");
						}
						
					}
				}
			})
		};
	},
	
	dcm_name: function(frm){
		frappe.call({
			method:'get_dcm_warehouse',
			doc:cur_frm.doc,
			callback: function(r){
				frm.refresh_field('dcm_warehouse')
			}
		})
	},
	setup:function(frm){
		frm.set_query('batch_no', 'dcm_dispatch_item', function(doc, cdt, cdn) {
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
					filters["warehouse"] = frm.doc.dcm_warehouse;
				}

				return {
					query : "erpnext.controllers.queries.get_batch_no",
					filters: filters
				}
			}
		});
		frm.set_query('dcm_warehouse', function(doc) {
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
					"company": frm.doc.company,
					"warehouse_type":"Transit"

				}
			};
		});
		
	},
	vehicle_no: function(frm){
		frappe.call({
			method:'get_logi_details',
			doc:frm.doc,
			callback: function(r){
				frm.refresh_field('driver_name')
				frm.refresh_field('driver_mobile_number')
				frm.refresh_field('vehicle_model')
			}

		})
	},
	company: function(frm){
		if(frm.doc.company){
			frm.set_query('dcm_warehouse', function(doc) {
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
						"company": frm.doc.company,
						"warehouse_type":"Transit"
					}
				};
			});
	

		}
	}
});


frappe.ui.form.on('DCM Dispatch Item',{
	item_name: function(frm,cdt,cdn){
		let child = locals[cdt][cdn]
		frappe.call({
			method:'get_uom',
			doc:cur_frm.doc,
			callback: function(r){
				frm.refresh_field('dcm_dispatch_item')
			}
		});
	},

	form_render: function(frm,cdt,cdn){
		let child = locals[cdt][cdn]
		child.warehouse = frm.doc.dcm_warehouse
		frm.refresh_field('dcm_dispatch_item')
	},

	batch_no: function(frm,cdt,cdn){
		let child = locals[cdt][cdn]
		frappe.call({
			method:'s4s.public.python.custom_methods.execute',
			args:{filters:{'company': 'Science For Society Techno Services Pvt Ltd', 'from_date': frappe.sys_defaults.year_start_date, 'to_date': frappe.datetime.get_today(), 'item_code': child.item_name, 'warehouse': frm.doc.dcm_warehouse, 'batch_no': child.batch_no}},
			callback: function(r){
				child.qty = r.message
				frm.refresh_field('dcm_dispatch_item')
			}
		})
	},
	
})
