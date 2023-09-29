// Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('S4S Supplier', {
	vlcc_name:function(frm){
		if(frm.doc.vlcc_name){
			var value;
			frappe.call({method:"frappe.client.get",args:{doctype:"S4S VLCC List",name:frm.doc.vlcc_name},aync:false,callback:function(r){if(r.message){value = r.message.cc_name;}}})
			// if(value){
				frm.set_query("cc_name",function(){
					return {
						filters:{
							"name":value
						}
					}
				})
			// }
		}
	},
	cc_name:function(frm){
		if(frm.doc.cc_name){
			var taluka;
			frappe.call({method:"frappe.client.get",args:{doctype:"S4S CC List",name:frm.doc.cc_name},aync:false,callback:function(r){if(r.message){taluka = r.message.taluka;}}})
			// if(taluka){
				frm.set_query("village",function(){
					return {
						filters:[
							["S4S Village List","taluka","=",taluka]
						]
					}
				})
				frm.set_query("taluka",function(){
					return {
						filters:[
							["S4S Taluka List","name","=",taluka]
						]
					}
				})
			// }
		}
		if(frm.doc.cc_name){
			frm.set_query("vlcc_name", function() {
				return {
					filters: {
						"cc_name": frm.doc.cc_name
					}
				}
			});
		}
	},
	taluka:function(frm){
		if(frm.doc.taluka){
			var value;
			frappe.call({method:"frappe.client.get",args:{doctype:"S4S Taluka List",name:frm.doc.taluka},aync:false,callback:function(r){if(r.message){value = r.message.district;}}})
			// if(value){
				frm.set_query("district",function(){
					return {
						filters:{
							"name":value
						}
					}
				})
			// }
		}
		if(frm.doc.taluka){
			frm.set_query("village", function() {
				return {
					filters: {
						"taluka": frm.doc.taluka,
					}
				}
			});
			frm.set_query("cc_name", function() {
				return {
					filters: [
						["S4S CC List","taluka","=", frm.doc.taluka]
					]
				}
			});
		}
	},
	district:function(frm){
		if(frm.doc.district){
			frm.set_query("taluka", function() {
				return {
					filters: {
						"district": frm.doc.district,
					}
				}
			});
		}
	},
	setup:function(frm){
		frappe.call({
			method:"value_fetch",
			doc:frm.doc,
			args:{
				"user":frappe.session.user
			},
			callback:function(r){
				frm.refresh_field("vlcc_name");
				frm.refresh_field("cc_name");
				frm.refresh_field("village");
				frm.refresh_field("taluka");
				frm.refresh_field("district");
			}
		})
	},
	refresh: function(frm) {
		$('#create_supplier').on("click",() =>{
			console.log("Hello")
			if(frappe.get_doc("Supplier",{"farmer_mobile_no":frm.doc.mobile_no}))
			{
				msgprint("Supplier with "+frm.doc.mobile_no+" this mobile number already Exists.");
				validated=false;
				return false;
			}else{
				frappe.call({
					method:'create_supplier',
					doc:frm.doc,
					callback:function(r){
						frm.refresh_field("supplier");
						frm.refresh_field("approval_status")
						frm.save()
					}
				})
				// frappe.call({
				// 	method: 'frappe.client.insert',
				// 	args: {
				// 		doc: {
				// 			"doctype": 'Supplier',
				// 			"supplier_name": frm.doc.supplier_name,
				// 			"supplier_group":frm.doc.type_of_supplier,
				// 			"mobile_no_1":frm.doc.mobile_no,
				// 			"aadhar_card_no":frm.doc.aadhar_card_no,
				// 			"pan":frm.doc.pan_no,
				// 			"vlcc_name":frm.doc.vlcc_name,
				// 			"cc_name":frm.doc.cc_name,
				// 			"village":frm.doc.village,
				// 			"taluka":frm.doc.taluka,
				// 			"district":frm.doc.district,
				// 			"account_holder_name":frm.doc.account_holder_name,
				// 			"account_number":frm.doc.account_number,
				// 			"bank_name":frm.doc.bank_name,
				// 			"ifsc_code":frm.doc.ifsc_code,
				// 			"branch":frm.doc.branch,
				// 			"pan_card_photo":frm.doc.pan_card_photo,
				// 			"aadhar_card_photo":frm.doc.aadhar_card_photo,
				// 			"bank_passbook_photo":frm.doc.bank_passbook_photo,
							
				// 			"mobile_no":frm.doc.mobile_no
							
				// 		}
				// 	},
				// 	callback: function(r) {
				// 		var data = r.message;
				// 		frm.set_value("supplier",data.name);
				// 		frm.refresh_field("supplier");
				// 		frm.save()
				// 		frappe.db.insert({
				// 			"doctype" : "Address",
				// 			"address_title" : data.name,
				// 			"address_type" : "Billing",
				// 			"address_line1":frm.doc.village,
				// 			"city":frm.doc.taluka,
				// 			"county":frm.doc.district
				// 			// "links":{
				// 			// 	"link_doctype":"Supplier",
				// 			// 	"link_name":data.name,
				// 			// 	"link_title":data.supplier_name
				// 			// }
				// 		}).then(function(u) {
				// 			frappe.call({
				// 				"method":"assign_address",
				// 				"doc":frm.doc,
				// 				"args":{"addr":u.name,"sup_doc":data.name},
				// 				callback:function(r){
				// 					// console.log(r.message)
				// 				}
				// 			})
				// 		})
				// 	}
				// });
			}
		})
	}
});


