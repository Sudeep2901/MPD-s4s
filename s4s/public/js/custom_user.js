frappe.ui.form.on("User",{
    after_save:function(frm){
        console.log("running")
        frappe.call({
            method:"s4s.public.python.custom_user.fetch_data",
            callback:function(r){
                // frm.save()
                // frm.save()
            }
        })
    }
})