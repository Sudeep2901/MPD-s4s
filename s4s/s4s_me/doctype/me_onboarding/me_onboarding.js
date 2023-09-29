// Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('ME Onboarding', {
	// refresh: function(frm) {

	// }
	before_save:function(frm){
		if(!frm.doc.supplier){
			// console.log("hello")
			frappe.call({
				method:"create_supplier",
				doc:frm.doc,
				callback:function(r){
					frm.refresh_field("supplier");
				}
			})
		}else{
			console.log("hello")
			frappe.call({
				method:"update_supplier",
				doc:frm.doc,
				callback:function(r){
					
				}
			})
		}
	},
	setup: function(frm){
		frm.fields_dict["me_warehouse_details"].grid.get_field(
			"source_warehouse"
		).get_query = function (doc) {
			return {
				filters: {
					'is_group': 0,
					'company':frm.doc.company
				},
			};
		};
		
		frm.fields_dict["me_warehouse_details"].grid.get_field(
			"target_warehouse"
		).get_query = function (doc) {
			return {
				filters: {
					'is_group': 0,
					'company':frm.doc.company
				},
			};
		};
		
	},
	company: function(frm){
		frm.fields_dict["me_warehouse_details"].grid.get_field(
			"source_warehouse"
		).get_query = function (doc) {
			return {
				filters: {
					'is_group': 0,
					'company':frm.doc.company
				},
			};
		};
		frm.fields_dict["me_warehouse_details"].grid.get_field(
			"target_warehouse"
		).get_query = function (doc) {
			return {
				filters: {
					'is_group': 0,
					'company':frm.doc.company
				},
			};
		};
		
	}
});
