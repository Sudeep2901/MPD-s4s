frappe.ui.form.on('Payment Entry',{
    before_save:function(frm){
        if (frm.doc.references){
            if (frm.doc.references.length != 0) {
                if(frm.doc.references[0].reference_doctype == "Purchase Invoice"){
                    if (frm.doc.references[0].reference_name){
                        frappe.call({
                            method:"s4s.public.python.custom_methods.map_fields",
                            args:{dn:frm.doc.references[0].reference_name},
                            callback:function(r){
                                if (r.message){
                                    frm.set_value("vlcc_name",r.message.vlcc_name)
                                    frm.set_value("cc_name",r.message.cc_name)
                                    frm.set_value("village",r.message.village)
                                    frm.set_value("taluka",r.message.taluka)
                                    frm.set_value("district",r.message.district)
                                    frm.set_value("s4s_purchase",r.message.s4s_purchase)
    
                                }
                            }
                        })
                    }
                }
            }
        }
    }
})