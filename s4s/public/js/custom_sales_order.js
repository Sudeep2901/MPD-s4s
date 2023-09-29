frappe.ui.form.on('Sales Order',{
    refresh:function(frm){
        setTimeout(() => {
            if (frm.doc.docstatus == 1){
                cur_frm.remove_custom_button("Work Order","Create")
                cur_frm.remove_custom_button("Material Request","Create")
                cur_frm.remove_custom_button("Request for Raw Materials","Create")
                cur_frm.remove_custom_button("Purchase Order","Create")
                cur_frm.remove_custom_button("Project","Create")
                cur_frm.remove_custom_button("Subscription","Create")
                cur_frm.remove_custom_button("Payment Request","Create")
                frm.add_custom_button(__("Proforma Invoice"), () => {
                    frappe.model.open_mapped_doc({
                        method: "s4s.public.python.custom_methods.create_proforma_invoice",
                        frm: frm
                    })
                },'Create');
                   

            }
           
        }, 100);
       
    },
    onload:function(frm){
        setTimeout(() => {
            if (frm.doc.docstatus == 1){
                cur_frm.remove_custom_button("Work Order","Create")
                cur_frm.remove_custom_button("Material Request","Create")
                cur_frm.remove_custom_button("Request for Raw Materials","Create")
                cur_frm.remove_custom_button("Purchase Order","Create")
                cur_frm.remove_custom_button("Project","Create")
                cur_frm.remove_custom_button("Subscription","Create")
                cur_frm.remove_custom_button("Payment Request","Create")
                frm.add_custom_button(__("Proforma Invoice"), () => {
                    frappe.model.open_mapped_doc({
                        method: "s4s.public.python.custom_methods.create_proforma_invoice",
                        frm: frm
                    })
                },'Create');
               
            }
            frm.set_query('set_warehouse', () => {
                return {
                    filters: {
                        'is_group': 0,
                        'warehouse_type':["!=","Transit"],
                        'company':frm.doc.company
                    }
                };
            });
           
            
        }, 100);
       
    },
    setup: function(frm){
        frm.set_query('set_warehouse', () => {
            return {
                filters: {
                    'is_group': 0,
                    'warehouse_type':["!=","Transit"]
                }
            };
        });
        if (frm.doc.company) {
            frm.set_query('cc_name', () => {
                return {
                    filters: {
                        'company':frm.doc.company
                    }
                };
            });
        }

    },
    company: function(frm){
        if (frm.doc.company) {
            frm.set_query('cc_name', () => {
                return {
                    filters: {
                        'company':frm.doc.company
                    }
                };
            });
        }
    },
    customer_name: function(frm){
        if(frm.doc.customer_name){
            if (frm.doc.customer_name == "Science For Society Techno Services Pvt Ltd"){
                frm.set_df_property("cc_name","reqd",1)
            }
            else{
                frm.set_df_property("cc_name","reqd",0)
            }

        }
    }

})