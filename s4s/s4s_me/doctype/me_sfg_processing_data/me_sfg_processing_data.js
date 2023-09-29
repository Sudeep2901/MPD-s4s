// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('ME SFG Processing Data', {
	setup: function(frm) {
		frm.set_query("me_code", function() {
			return {
				"filters": {
					"supplier_group": "ME",
					
				}
			};
		});

	},

	me_code:function(frm){
        if(frm.doc.me_code){
            frappe.call({
                method:"frappe.client.get",
                args:{
                    doctype:"Supplier",
                    name:frm.doc.me_code
                },
                callback:function(r){
                    frm.set_value("me_name",r.message.supplier_name);
                }
            })
        }
        if(frm.doc.stock_entry_type && frm.doc.me_code){
            frappe.call({
                method:"s4s.public.python.custom_me_sfg.fetch_warehouse",
                args:{
                    stock_entry:frm.doc,
                    user:frappe.session.user,
                    field:"stock_entry_type"
                },
                callback:function(r){
                    if(r.message){
                        if(r.message.from_warehouse!=""){
                            frm.set_value("from_warehouse",r.message.from_warehouse);
                        }
                        if(r.message.to_warehouse!=""){
                            frm.set_value("to_warehouse",r.message.to_warehouse);
                        }
                    }
                }
            })
        }
    },
	stock_entry_type:function(frm){
        if(frm.doc.stock_entry_type && frm.doc.stock_entry_type==="Manufacture"){
            frappe.call({
                method:"frappe.client.get",
                args:{
                    doctype:"User",
                    name:frappe.session.user
                },
                callback:function(r){
                    var user_doc = r.message;
                    user_doc.roles.forEach(element => {
                        if(element.role === "ME Field Executive"){
                            frm.set_value("from_bom",1);
                            
                        }
                    });
                }
            })
        }
        if(frm.doc.stock_entry_type && frm.doc.me_code){
            frappe.call({
                method:"s4s.public.python.custom_me_sfg.fetch_warehouse",
                args:{
                    stock_entry:frm.doc,
                    user:frappe.session.user,
                    field:"stock_entry_type"
                },
                callback:function(r){
                    if(r.message){
                        if(r.message.from_warehouse!=""){
                            frm.set_value("from_warehouse",r.message.from_warehouse);
                        }
                        if(r.message.to_warehouse!=""){
                            frm.set_value("to_warehouse",r.message.to_warehouse);
                        }
                    }
                }
            })
        }
    },
});

frappe.ui.form.on('Stock Entry Detail', {
	
	form_render:function(frm,cdt,cdn){
		var child = locals[cdt][cdn]
		console.log(">>>>>>>>>>...",frm.doc)
		if (frm.doc.doctype == "ME SFG Processing Data"){
			frappe.model.set_df_property("is_finished_item", "reqd", 1);
		}
	}

})


erpnext.stock.StockEntry = erpnext.stock.StockController.extend({

	fg_completed_qty: function() {
		this.get_items();
	},

	get_items: function() {
		var me = this;
		if(!this.frm.doc.fg_completed_qty || !this.frm.doc.bom_no)
			frappe.throw(__("BOM and Manufacturing Quantity are required"));

		if(this.frm.doc.work_order || this.frm.doc.bom_no) {
			// if work order / bom is mentioned, get items
			return this.frm.call({
				doc: me.frm.doc,
				freeze: true,
				method: "get_items",
				callback: function(r) {
					if(!r.exc) refresh_field("items");
					if(me.frm.doc.bom_no) attach_bom_items(me.frm.doc.bom_no)
				}
			});
		}
	},

})
$.extend(cur_frm.cscript, new erpnext.stock.StockEntry({frm: cur_frm}));


