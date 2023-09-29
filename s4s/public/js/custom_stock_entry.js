frappe.ui.form.on("Stock Entry",{
    refresh:function(frm){
        if (frm.doc.docstatus === 1) {
			if (frm.doc.add_to_transit && frm.doc.purpose=='Material Transfer' && frm.doc.per_transferred < 100) {
			    cur_frm.remove_custom_button('End Transit');
				frm.add_custom_button('Material In', function() {
					frappe.model.open_mapped_doc({
						method: "s4s.s4s.custom.custom_stock_entry.make_stock_in_entry",
						frm: frm
					})
				});
			}


            setTimeout(() => {
                frappe.call({
                    method:'s4s.public.python.custom_methods.hide_material_in',
                    args:{name:frm.doc.name},
                    callback:function(r){
                        if (r.message){
                            if(r.message == "Success"){
                                frm.remove_custom_button("Material In")
                            }
                        }
    
                    }
    
                })
            }, 100);
        }
        if(frm.doc.is_s4s_purchase){
            frappe.call({
                method:"s4s.public.python.custom_methods.check_roles",
                args:{},
                callback:function(r){
                    if(r.message == "Yes"){
                        frm.set_df_property("dcm_name",'hidden',1)
                        frm.set_df_property("dcm_location",'hidden',1)
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
        if(frm.doc.stock_entry_type && frm.doc.s4ssupplier){
            frappe.call({
                method:"s4s.s4s.custom.custom_stock_entry.fetch_warehouse",
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
    add_to_transit:function(frm){
        if(frm.doc.stock_entry_type && frm.doc.s4ssupplier){
            frappe.call({
                method:"s4s.s4s.custom.custom_stock_entry.fetch_warehouse",
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
    s4ssupplier:function(frm){
        if (!frm.doc.s4ssupplier){
            frm.set_query('bom_no', () => {
                return {
                    filters: {
                       "docstatus":1,
                       "is_active":1
                    }
                }
            })

        }
        else{
            frm.set_query('bom_no', () => {
                return {
                    filters: {
                       "is_me_bom":1
                    }
                }
            })

        }
        if(frm.doc.s4ssupplier){
            frappe.call({
                method:"frappe.client.get",
                args:{
                    doctype:"Supplier",
                    name:frm.doc.s4ssupplier
                },
                callback:function(r){
                    frm.set_value("me_name",r.message.supplier_name);
                }
            })
        }
        if(frm.doc.stock_entry_type && frm.doc.s4ssupplier){
            frappe.call({
                method:"s4s.s4s.custom.custom_stock_entry.fetch_warehouse",
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
    onload:function(frm){
       setTimeout(() => {
         if (frm.doc.docstatus == 1){
             frappe.call({
                 method:'s4s.public.python.custom_methods.hide_material_in',
                 args:{name:frm.doc.name},
                 callback:function(r){
                     if (r.message){
                         if(r.message == "Success"){
                             frm.remove_custom_button("Material In")
                         }
                     }
 
                 }
 
             })
         }
       }, 100);
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
                        frm.set_query('stock_entry_type', () => {
                            return {
                                filters: {
                                    name: ['in', ["Manufacture"]]
                                }
                            }
                        })
                    }
                });
            }
        })

        if(frm.doc.is_s4s_purchase){
            frappe.call({
                method:"s4s.public.python.custom_methods.check_roles",
                args:{},
                callback:function(r){
                    if(r.message == "Yes"){
                        frm.set_df_property("dcm_name",'hidden',1)
                        frm.set_df_property("dcm_location",'hidden',1)
                    }

                }
            })
            
        }
    },
    onload_post_render:function(frm){
        frm.refresh_field("rejected_quantity");
    },
    before_save:function(frm){
        if(frm.doc.stock_entry_type == "Material Transfer" && frappe.db.exists("S4S User details",frappe.session.user)){
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "S4S User details",
                    name: frappe.session.user,
                },
                callback(r) {
                    if(r.message) {
                        var doc = r.message;
                        if(doc.transit_warehouse!=frm.doc.to_warehouse && frm.doc.outgoing_stock_entry){
                            frm.set_value("add_to_transit",0);
                            frm.refresh_field("add_to_transit");
                        }
                    }
                }
            });
        }
        if(frm.doc.me_weight_details){
            var total_weight = 0;
            frm.doc.me_weight_details.forEach(row => {
                total_weight+=row.weight_in_kg;
            });
            frm.doc.total_bags = frm.doc.me_weight_details.length;
            frm.refresh_field("total_bags");
            frm.doc.total_goni_weight = total_weight;
            frm.refresh_field("total_goni_weight");
        }
        if(frm.doc.rejected_quantity){
            var total_weight = 0;
            frm.doc.rejected_quantity.forEach(row => {
                total_weight+=row.weight_in_kg;
            });
            frm.doc.rejected_total_bags = frm.doc.rejected_quantity.length;
            frm.refresh_field("rejected_total_bags");
            frm.doc.rejected_total_goni_weight = total_weight;
            frm.refresh_field("rejected_total_goni_weight");
        }
        
    }
})
frappe.ui.form.on("ME Goni Weight",{
    weight_in_kg:function(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        if(frm.doc.me_weight_details && d.weight_in_kg!=0){
            var total_weight = 0;
            frm.doc.me_weight_details.forEach(row => {
                total_weight+=row.weight_in_kg;
            });
            frm.doc.total_bags = frm.doc.me_weight_details.length;
            frm.refresh_field("total_bags");
            frm.doc.total_goni_weight = total_weight;
            frm.refresh_field("total_goni_weight");
        }
    }
})
frappe.ui.form.on("S4S Goni Weight",{
    weight_in_kg:function(frm,cdt,cdn){
        var d = locals[cdt][cdn]
        if(frm.doc.rejected_quantity && d.weight_in_kg!=0){
            var total_weight = 0;
            frm.doc.rejected_quantity.forEach(row => {
                total_weight+=row.weight_in_kg;
            });
            frm.doc.rejected_total_bags = frm.doc.rejected_quantity.length;
            frm.refresh_field("rejected_total_bags");
            frm.doc.rejected_total_goni_weight = total_weight;
            frm.refresh_field("rejected_total_goni_weight");
        }
    }
})