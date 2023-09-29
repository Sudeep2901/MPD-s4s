// Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('S4S Vehicle Plan', {
	refresh:function(frm){
		$('.btn-pt').on('click', function () {
			if(frm.doc.date){
				frappe.call({
					method:"get_purchase_transactions",
					doc:frm.doc,
					callback:function(r){
						frm.refresh_field("vehicle_assignment");
					}
				})
			}
		})
		$('.btn-fp').on('click', function (){
			if(frm.doc.date){
				frappe.call({
					method:"get_farm_pickups",
					doc:frm.doc,
					callback:function(r){
						frm.refresh_field("farm_pickups");
					}
				})
			}
		})
	},
	date:function(frm){
		$('.btn-pt').on('click', function () {
			console.log("hello")
			if(frm.doc.date){
				frappe.call({
					method:"get_purchase_transactions",
					doc:frm.doc,
					callback:function(r){
						frm.refresh_field("vehicle_assignment");
					}
				})
			}
		})
		$('.btn-fp').on('click', function (){
			if(frm.doc.date){
				frappe.call({
					method:"get_farm_pickups",
					doc:frm.doc,
					callback:function(r){
						frm.refresh_field("farm_pickups");
					}
				})
			}
		})
	},
	setup: function(frm){
		if (frm.doc.company) {
			frm.set_query("cc_name", () => ({
				filters: { 
					company: frm.doc.company, 
				 },
			}));
		}
		if (frm.doc.cc_name) {
			frm.set_query("vlcc_name", () => ({
				filters: { 
					cc_name: frm.doc.cc_name, 
				 },
			}));
		}
	},
	company: function(frm){
		if (frm.doc.company) {
			frm.set_query("cc_name", () => ({
				filters: { 
					company: frm.doc.company, 
				 },
			}));
		}
	},
	cc_name: function(frm){
		if (frm.doc.cc_name) {
			frm.set_query("vlcc_name", () => ({
				filters: { 
					cc_name: frm.doc.cc_name, 
				 },
			}));
		}
	}

});
frappe.ui.form.on("S4S Vehicle Assignment",{
	vehicle_no:function(frm,cdt,cdn){
		var d = locals[cdt][cdn]
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				"doctype": "S4S Vehicle",
				"filters": {"name": d.vehicle_no},
				"fieldname": "driver_name"
			}, 
			callback: function(r) {
				if(r.message){
					d.driver_name = r.message.driver_name
					frm.refresh_field("driver_name")
				}
			}
		});
	}
})
frappe.ui.form.on("S4S Vehicle Assignment for Farmer Query",{
	vehicle_no:function(frm,cdt,cdn){
		var d = locals[cdt][cdn]
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				"doctype": "S4S Vehicle",
				"filters": {"name": d.vehicle_no},
				"fieldname": "driver_name"
			}, 
			callback: function(r) {
				if(r.message){
					d.driver_name = r.message.driver_name
					frm.refresh_field("driver_name")
				}
			}
		});
	}
})