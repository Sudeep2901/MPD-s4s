// Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('DCM Material Request', {
	setup:function(frm){
		frm.set_query('dcm_warehouse', function(doc) {
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
							if(row.role === "S4S CC User"){
								if(frm.doc.approval_status.includes("Accept by CC Supervisor", "Reject by CC Supervisor")){
									frm.set_value("cc_user",1);
								}
							}
							if(row.role === "Logistic Supervisor"){
								if(frm.doc.approval_status==="Accept by Logistic Supervisor"){
									frm.set_value("logistic_supervisor",1);
								}
							}
							if(row.role === "S4S Logistic Manager"){
								if(frm.doc.approval_status==="Accept by Logistic Supervisor"){
									frm.set_value("s4s_logistic_manager",1);
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
	vehicle_no:function(frm){
		if(frm.doc.vehicle_no){
			frappe.call({
				method:"frappe.client.get",
				args:{
					doctype:"S4S Vehicle",
					name:frm.doc.vehicle_no
				},
				callback:function(r){
					if(r.message){
						var result = r.message;
						frm.set_value("vehicle_model",result.vehicle_model);
						frm.set_value("driver_name",result.driver_name);
						frm.set_value("driver_mobile_number",result.driver_mobile_number);
					}
				}
			})
		}
	},
	dcm_name:function(frm){
		if(frm.doc.dcm_name){
			frappe.call({
				method:"frappe.client.get",
				args:{
					doctype:"DCM List",
					name:frm.doc.dcm_name
				},
				callback:function(r){
					var r=r.message;
					frm.set_value("dcm_warehouse",r.transit_location);
				}
			})
		}
	},
	refresh:function(frm){
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
						if(row.role === "S4S CC User"){
							if(frm.doc.cc_user===1){
								frm.set_df_property("approval_status","options",[frm.doc.approval_status]);
							}
						}
						if(row.role === "Logistic Supervisor"){
							if(frm.doc.logistic_supervisor===1){
								frm.set_df_property("approval_status","options",[frm.doc.approval_status]);
							}
						}
						if(row.role === "S4S Logistic Manager"){
							if(frm.doc.s4s_logistic_manager===1){
								frm.set_df_property("approval_status","options",[frm.doc.approval_status]);
							}
						}
					});
				}
			}
		})
		if(frm.doc.docstatus===1){
			frappe.call({
				method:"permission_check_for_user",
				doc:frm.doc,
				args:{
					"user":frappe.session.user
				},
				callback:function(r){
					var result = r.message;
					if(result===1){
						frm.add_custom_button(__("Material Transfer"), function() {
							frappe.model.open_mapped_doc({
								method: "s4s.s4s_dcm.doctype.dcm_material_request.dcm_material_request.make_material_transfer",
								frm: frm,
							})
						}).addClass("btn-primary").removeClass("btn-default");
					}
				}
			})
		}
	},
	company: function(frm){
		if(frm.doc.company){
			frm.set_query('dcm_warehouse', function(doc) {
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
	

		}
	}

});
frappe.ui.form.on("S4S DCM Material request",{
	item_code:function(frm,cdt,cdn){
		var d = locals[cdt][cdn]
		if(d.item_code){
			frappe.call({
				method:"frappe.client.get",
				args:{
					"doctype":"Item",
					"name":d.item_code
				},
				callback:function(r){
					var r = r.message;
					d.uom=r.stock_uom;
					d.item_name = r.item_name;
					frm.refresh_field("items");
				}
			})
		}
	}
})
