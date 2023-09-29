// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('S4S Transaction Approval', {
	setup: function(frm){
		if (frm.doc.company) {
			frm.set_query("cc_name", () => ({
				filters: { company: frm.doc.company},
			}));
		}
	},
	company: function(frm){
		frm.set_query("cc_name", () => ({
			filters: { company: frm.doc.company},
		}));
	},

	get_entries: function(frm) {
		frappe.call({
			method:"get_data",
			doc:frm.doc,
			callback:function(r){
				if (r.message != "No Records"){
					frm.doc.approval_details = []
					let data = r.message
					data.forEach(element => {
						let c = frm.add_child('approval_details')
						c.date = element.transaction_date
						c.cc_name = element.cc_name
						c.farmer_name = element.farmer_name
						c.transaction_no = element.s4s_p_name
						c.crop_name = element.item_code
						c.qty = element.qty
						c.purchase_receipt = element.pur_rect
						c.amount = element.amount
						c.fpo_dc_no = element.del_note
						c.fpo_dc_date = element.del_date
						c.s4s_grn_no = element.grn_name
						c.s4s_grn_date = element.grn_date
						c.fpo_pi_no = element.pi_name
						c.fpo_pi_date = element.pi_date
						c.fpo_sale_order_no = element.so_name
						c.fpo_sale_order_date = element.so_date
						c.s4s_fpo_purchase_order = element.po_no
						c.s4s_fpo_purchase_order_date = element.po_date,
						c.total_deduction_amount = element.deduction
						c.net_total = element.net_total

					});
					frm.refresh_field("approval_details")
				}
				else{
					frm.doc.approval_details = []
					frm.clear_table("approval_details")
					frm.refresh_field("approval_details")
					frappe.msgprint("No Records Found For Given Period.")
				}

			}
		})

	}
});
