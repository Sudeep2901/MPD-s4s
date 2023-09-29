frappe.ui.form.on("Work Order",{
    setup: function(frm){
        frm.remove_custom_button("Start")

    },

	refresh: function(frm){
        frm.remove_custom_button("Start")

    },

	onload: function(frm){
        frm.remove_custom_button("Start")

    },

	before_load: function(frm){
        frm.remove_custom_button("Start")

    }
   
})