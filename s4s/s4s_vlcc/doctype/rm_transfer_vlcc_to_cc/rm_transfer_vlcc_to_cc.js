// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('RM Transfer VLCC To CC', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1){
			frappe.call({
				method:"check_roles",
				doc:frm.doc,
				callback: function(r){
					if(r.message){
						if(r.message == "Success"){
							frm.add_custom_button('VLCC RM In', function() {
								frappe.model.open_mapped_doc({
									method: "s4s.s4s_vlcc.doctype.rm_transfer_vlcc_to_cc.rm_transfer_vlcc_to_cc.make_vlcc_rm_in",
									frm: cur_frm
								})
				
							}).addClass('btn-primary');

						}
					}
				}
			})
			
		}

	}
});
