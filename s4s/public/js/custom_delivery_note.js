{% include 'erpnext/stock/doctype/delivery_note/delivery_note.js' %};

frappe.provide("s4s.stock");


frappe.ui.form.on('Delivery Note',{})


s4s.stock.CustomDeliveryNoteController = erpnext.stock.DeliveryNoteController.extend({
    setup: function(doc) {
		this._super(doc);
	},
    refresh: function(doc, dt, dn) {
        var me = this;
        this._super(doc);
        
        if (doc.docstatus == 1){
            this.frm.remove_custom_button("Shipment","Create")
            this.frm.remove_custom_button("Installation Note","Create")
            this.frm.remove_custom_button("Delivery Trip","Create")
            this.frm.remove_custom_button("Subscription","Create")

            frappe.call({
                method:"s4s.public.python.custom_methods.pur_rect_btn",
                args:{dn_name:doc.name},
                callback:function(r){

                   if (r.message) {
                    let data = r.message
                     if (data.msg == "Success" && data.role == "Success"){
                         me.frm.add_custom_button(__("Create S4S GRN"), () => {
                             frappe.model.open_mapped_doc({
                                     method: "s4s.public.python.custom_methods.create_purchase_rect",
                                     frm: cur_frm
                                 })
                             },"Create");
 
                     }
                   }
                }
            })

        }

    },

    

    

})

$.extend(cur_frm.cscript, new s4s.stock.CustomDeliveryNoteController({frm: cur_frm}));



