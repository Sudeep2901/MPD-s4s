// Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('S4S Purchase', {
	setup:function(frm){
		// console.log(frappe.get_doc("S4S Supplier",frappe.session.user))
		frappe.call({
			method:"value_fetch",
			doc:frm.doc,
			args:{
				"user":frappe.session.user
			},
			callback:function(r){
				frm.refresh_field("set_warehouse");
			}
		})
		if (frm.doc.company) {
			frm.set_query("set_warehouse", function() {
				return {
					filters: {
						'is_group': 0,
                        'warehouse_type':["!=","Transit"],
						'company': frm.doc.company
					}
				}
			})
		};
		
	},
	refresh: function(frm){
		let pay_read_only = false

		if(frm.doc.payment_status == "Paid"){
			pay_read_only = true
		}

		if (/^\s*$/.test(frm.doc.s4s_utr_no) && !frm.doc.s4s_utr_no ) {
			pay_read_only = false
		}
		if (/^\s*$/.test(frm.doc.fpo_utr_no) && !frm.doc.fpo_utr_no ) {
			pay_read_only = false
		}
		if (/^\s*$/.test(frm.doc.s4s_payment_no) && !frm.doc.s4s_payment_no ) {
			pay_read_only = false
		}
		if (/^\s*$/.test(frm.doc.fpo_payment_no) && !frm.doc.fpo_payment_no ) {
			pay_read_only = false
		}

		if (pay_read_only == true){
			frm.set_df_property("payment_status","read_only",1)
		}
		else{
			frm.set_df_property("payment_status","read_only",0)
		}

		frappe.call({
			method:"set_options",
			doc:frm.doc,
			callback:function(r){
				if(r.message){
					let data = r.message
					if (data.ro === true){
						frm.set_df_property("approved_status","read_only",1)
						frm.refresh_field("approved_status")
					}
					else{
						frm.set_df_property("approved_status","read_only",0)
						frm.set_df_property("approved_status","options",data.options)
						frm.refresh_field("approved_status")
					}

				}
			}
		})
	},
	s4s_utr_no: function(frm){
		if(frm.doc.s4s_utr_no == ""){
			frm.set_df_property("payment_status","read_only",0)
			
		}
	},
	fpo_utr_no: function(frm){
		if(frm.doc.fpo_utr_no == ""){
			frm.set_df_property("payment_status","read_only",0)
			
		}
	},
	s4s_payment_no: function(frm){
		if(frm.doc.s4s_payment_no == ""){
			frm.set_df_property("payment_status","read_only",0)
			
		}
	},
	fpo_payment_no: function(frm){
		if(frm.doc.fpo_payment_no == ""){
			frm.set_df_property("payment_status","read_only",0)
		}
	},
	on_submit:function(frm){
		console.log("running")
		frappe.call({
			"method":"make_docs",
			"doc":frm.doc,
			"args":{
				"user":frappe.session.user
			}
		})
	},
	supplier_deductions:function(frm){
		// cur_frm.clear_table("taxes")
		// cur_frm.refresh_field("taxes");
		frappe.call({
			method:"copy_data2",
			doc:frm.doc,
			args:{
				"s_deduct":frm.doc.supplier_deductions
			},
			callback:function(r){
				frm.refresh_field("taxes");
			}
		})
	},
	// onload:function(frm){
	// 	if(frm.doc.__islocal){
	// 		frappe.call({
	// 			method:"copy_data1",
	// 			doc:frm.doc,
	// 			callback:function(r){
	// 				cur_frm.refresh_field("supplier_deductions");
	// 				cur_frm.refresh_field("taxes");
	// 			}
	// 		})
	// 	}		
	// },
	after_save:function(frm){
		if(frm.doc.s4s_farmer_query){
			frappe.db.set_value('S4S Farmer Query', frm.doc.s4s_farmer_query, 's4s_purchase', frm.doc.name);
		}
		
	},
	before_save:function(frm){
		if(frm.doc.kadta){
			// if(frm.doc.receipt_details.length == 1){
			// 	if(frm.doc.receipt_details.length!=0){
					var total_weight = 0.00;
					$.each(frm.doc.receipt_details, function(index, row) {
						total_weight += row.weight_in_kg
					});
					cur_frm.doc.total_weight = total_weight;
					cur_frm.refresh_field("total_weight");
					if(frm.doc.kadta){
						cur_frm.doc.kadta_weight = (total_weight * parseInt(frm.doc.kadta))/100;
						cur_frm.refresh_field("kadta_weight");
						cur_frm.doc.weight_after_kadta = total_weight-((total_weight * parseInt(frm.doc.kadta))/100);
						cur_frm.refresh_field("weight_after_kadta");
						cur_frm.doc.total_amount = (total_weight-((total_weight * parseInt(frm.doc.kadta))/100)) * cur_frm.doc.purchase_receipt_details[0].rate;
						cur_frm.refresh_field("total_amount")
					}
			// 	}
			// }
		}
		if(frm.doc.taxes.length!=0){
			var total = 0.00;
			$.each(frm.doc.taxes, function(index, row) {
				total += row.tax_amount
			});
			cur_frm.doc.total_deduction_amount = total;
			cur_frm.refresh_field("total_deduction_amount")
			cur_frm.doc.grand_total = cur_frm.doc.total_amount - total || 0;
			cur_frm.refresh_field("grand_total");
		}
		if(!frm.doc.set_warehouse){
			frappe.call({
				method:"value_fetch",
				doc:frm.doc,
				args:{
					"user":frappe.session.user
				},
				callback:function(r){
					frm.refresh_field("set_warehouse");
				}
			})
		}
	},
	supplier:function(frm){
		if (frm.doc.supplier){
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Supplier",
					name: frm.doc.supplier,
				},
				callback(r) {
					if(r.message) {
						var doc = r.message;
						frm.set_value("supplier_name",doc.supplier_name);
						frm.set_value("vlcc_name",doc.vlcc_name)
						frm.set_value("cc_name",doc.cc_name)
						frm.set_value("village",doc.village)
						frm.set_value("taluka",doc.taluka)
						frm.set_value("district",doc.district)
						frm.set_value("state",doc.state_)
						frm.refresh_field("supplier_name");
					}
				}
			});

		}
		
	},
	kadta:function(frm){
		if(frm.doc.kadta){
			// if(frm.doc.receipt_details.length == 1){
			// 	if(frm.doc.receipt_details.length!=0){
					var total_weight = 0.00;
					$.each(frm.doc.receipt_details, function(index, row) {
						total_weight += row.weight_in_kg
					});
					cur_frm.doc.total_weight = total_weight;
					cur_frm.refresh_field("total_weight");
					if(frm.doc.kadta){
						cur_frm.doc.kadta_weight = (total_weight * parseInt(frm.doc.kadta))/100;
						cur_frm.refresh_field("kadta_weight");
						cur_frm.doc.weight_after_kadta = total_weight-((total_weight * parseInt(frm.doc.kadta))/100);
						cur_frm.refresh_field("weight_after_kadta");
						cur_frm.doc.total_amount = (total_weight-((total_weight * parseInt(frm.doc.kadta))/100)) * cur_frm.doc.purchase_receipt_details[0].rate;
						cur_frm.refresh_field("total_amount")
					}
			// 	}
			// }
		}
	},
	onload:function(frm){
		if (!frm.doc.s4s_farmer_query){
			frappe.call({
				method:"get_s4s_user_details",
				doc:frm.doc,
				callback:function(r){
					if (r.message != "No"){
						frm.set_value("set_warehouse",r.message.wh)
						frm.set_value("taluka",r.message.taluka)
						frm.set_value("state",r.message.state)
						frm.set_value("district",r.message.district)
					}
				}
			})
		}

		frappe.call({
			method:"set_options",
			doc:frm.doc,
			callback:function(r){
				if(r.message){
					let data = r.message
					if (data.ro === true){
						frm.set_df_property("approved_status","read_only",1)
						frm.refresh_field("approved_status")
					}
					else{
						frm.set_df_property("approved_status","read_only",0)
						frm.set_df_property("approved_status","options",data.options)
						frm.refresh_field("approved_status")
					}

				}
			}
		})
		
	},
	onload_post_render:function(frm){
		if (frm.is_new() && frm.doc.company){
			frappe.call({
				method:"get_supplier_deductions",
				doc:frm.doc,
				args:{company:frm.doc.company},
				callback:function(r){
					if (r.message){
						frm.set_value("supplier_deductions",r.message)
		
					}
				}
			})
		}
		
	},
	company: function(frm){
		if (frm.doc.company && !frm.doc.cc_name && !frm.doc.vlcc_name) {
			frm.set_query("set_warehouse", function() {
				return {
					filters: {
						'company': frm.doc.company,
						'is_group': 0,
                        'warehouse_type':["!=","Transit"],
					}
				}
			})
		}
		else if (frm.doc.company && !frm.doc.cc_name && frm.doc.vlcc_name){
			frm.set_query("set_warehouse", function() {
				return {
					filters: {
						'company': frm.doc.company,
						'is_group': 0,
                        'warehouse_type':["!=","Transit"],
						'cc_link1': frm.doc.cc_name,
					}
				}
			})

		}
		else if (frm.doc.company && !frm.doc.cc_name && frm.doc.vlcc_name){
			frm.set_query("set_warehouse", function() {
				return {
					filters: {
						'company': frm.doc.company,
						'is_group': 0,
                        'warehouse_type':["!=","Transit"],
						'vlcc_link': frm.doc.vlcc_name
					}
				}
			})

		}
		else if (frm.doc.company && frm.doc.cc_name && frm.doc.vlcc_name){
			frm.set_query("set_warehouse", function() {
				return {
					filters: {
						'company': frm.doc.company,
						'is_group': 0,
                        'warehouse_type':["!=","Transit"],
						'vlcc_link': frm.doc.vlcc_name,
						'cc_link1': frm.doc.cc_name,
					}
				}
			})

		}
	},
	cc_name: function(frm){
		if (frm.doc.cc_name && !frm.doc.vlcc_name) {
			frm.set_query("set_warehouse", function() {
				return {
					filters: {
						'company': frm.doc.company,
						'is_group': 0,
                        'warehouse_type':["!=","Transit"],
						'cc_link1': frm.doc.cc_name
					}
				}
			})
		}
		else if (frm.doc.cc_name && frm.doc.vlcc_name) {
			frm.set_query("set_warehouse", function() {
				return {
					filters: {
						'company': frm.doc.company,
						'is_group': 0,
                        'warehouse_type':["!=","Transit"],
						'cc_link1': frm.doc.cc_name,
						'vlcc_link': frm.doc.vlcc_name
					}
				}
			})
		}
		else if (!frm.doc.cc_name && !frm.doc.vlcc_name) {
			frm.set_query("set_warehouse", function() {
				return {
					filters: {
						'company': frm.doc.company,
						'is_group': 0,
                        'warehouse_type':["!=","Transit"],
						
					}
				}
			})
		}
		
	},
	vlcc_name: function(frm){
		if (frm.doc.vlcc_name && !frm.doc.cc_name) {
			frm.set_query("set_warehouse", function() {
				return {
					filters: {
						'company': frm.doc.company,
						'is_group': 0,
                        'warehouse_type':["!=","Transit"],
						'vlcc_link': frm.doc.vlcc_name	
					}
				}
			})
		}
		else if (frm.doc.vlcc_name && frm.doc.cc_name) {
			frm.set_query("set_warehouse", function() {
				return {
					filters: {
						'company': frm.doc.company,
						'is_group': 0,
                        'warehouse_type':["!=","Transit"],
						'cc_link1': frm.doc.cc_name,
						'vlcc_link': frm.doc.vlcc_name
					}
				}
			})
		}
		else if (!frm.doc.cc_name && !frm.doc.vlcc_name) {
			frm.set_query("set_warehouse", function() {
				return {
					filters: {
						'company': frm.doc.company,
						'is_group': 0,
                        'warehouse_type':["!=","Transit"],
						
					}
				}
			})
		}
		
	},

});
frappe.ui.form.on("S4S Purchase receipt",{
	item_code : function(frm,cdt,cdn){
		var d = locals[cdt][cdn]
		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Item",
				name: d.item_code,
			},
			callback(r) {
				if(r.message) {
					var doc = r.message;
					d.item_name = doc.item_name;
					frm.refresh_field("purchase_receipt_details");
				}
			}
		});
		frappe.db.get_single_value('Buying Settings', 'buying_price_list').then(buying_price_list => {
			if(buying_price_list){
				frappe.call({
					method: "frappe.client.get_value",
					args: {
						"doctype": "Item Price",
						"filters": {
							"item_code": d.item_code,
							"price_list":buying_price_list,
						},
						"fieldname":"price_list_rate"
					}, 
					callback: function(r) {
						d.rate = r.message["price_list_rate"]
						frm.refresh_field("purchase_receipt_details");
					}
				});
			}
		});
	}
})
frappe.ui.form.on("S4S Goni Weight",{
	weight_in_kg:function(frm,cdt,cdn){
		var total_weight = 0.00;
		$.each(frm.doc.receipt_details, function(index, row) {
			total_weight += row.weight_in_kg
		});
		cur_frm.doc.total_weight = total_weight;
		cur_frm.refresh_field("total_weight");
		if(frm.doc.kadta){
			cur_frm.doc.kadta_weight = (total_weight * parseInt(frm.doc.kadta))/100;
			cur_frm.refresh_field("kadta_weight");
			cur_frm.doc.weight_after_kadta = total_weight-((total_weight * parseInt(frm.doc.kadta))/100);
			cur_frm.refresh_field("weight_after_kadta");
			cur_frm.doc.total_amount = (total_weight-((total_weight * parseInt(frm.doc.kadta))/100)) * cur_frm.doc.purchase_receipt_details[0].rate;
			cur_frm.refresh_field("total_amount")
		}
	}
})
frappe.ui.form.on("Purchase Taxes and Charges",{
	tax_amount:function(frm,cdt,cdn){
		if(frm.doc.taxes.length!=0){
			var total = 0.00;
			$.each(frm.doc.taxes, function(index, row) {
				total += row.tax_amount
			});
			cur_frm.doc.total_deduction_amount = total;
			cur_frm.refresh_field("total_deduction_amount")
			cur_frm.doc.grand_total = cur_frm.doc.total_amount - total || 0;
			cur_frm.refresh_field("grand_total");
		}
	}
})
