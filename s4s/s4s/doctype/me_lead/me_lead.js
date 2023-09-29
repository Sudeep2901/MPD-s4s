// Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('ME Lead', {
	onload:function(frm){
		frappe.call({
			method:"set_options",
			doc:frm.doc,
			args:{
				"s_user" : frappe.session.user
			},
			callback:function(r){
				const result = r.message;
				if(typeof(result) === "object"){
					frm.set_df_property("lead_approval_status", "options", result);
				}
			}
		})
		if(frm.doc.docstatus === 1){
			frappe.call({
				method:"s4s.api.hide_fields",
				args:{
					"s_user" : frappe.session.user
				},
				callback:function(r){
					if(r.message != 1){
	
						if(frm.doc.docstatus===1){
							const arr = [ "gender", "status", "address_type", "village", "taluka", "district", "state", "country", "pincode", "mobile_no", "whats_app_no", "dist", "taluka_name", "village_name", "s4s_cc", "latitude", "longitude", "source_of_lead", "source_name", "group_lead_name", "group_size", "group_name", "aadhar_card", "pan_card", "address_proof", "bank_passbook", "ration_card", "voters_id", "light_bill", "space_for_processing", "photo_of_space", "photo_of_space_2", "photo_of_space_3", "light_availability", "water_availability", "ease_of_transportation", "ok_to_take_loan", "taken_a_loan", "defaulted_on_the_loan", "me_is_interested", "follow_up_me", "recommend_the_me", "followup_by", "next_contact_by", "next_contact_date", "notes", "audio_feedback"]
							arr.forEach(function(entry){
								cur_frm.set_df_property(entry, "allow_on_submit", "0");
							});
							// cur_frm.set_df_property("group_lead_name", "allow_on_submit", "1");
							// cur_frm.set_df_property("group_name", "allow_on_submit", "1");
							// cur_frm.set_df_property("group_size", "allow_on_submit", "1");    
						}
						
						frm.refresh_fields();
					}
				}
			})
		}
	},
	setup: function(frm){
		frm.set_value("lead_owner",frm.doc.owner);
		frm.refresh_field("lead_owner");
	},
	refresh: function(frm) {
		frm.add_custom_button(__('Lead Qualification Form'), () => {
			let lqf =  frappe.model.get_new_doc("Lead Qualification Form");
			lqf.lead_type = frm.doc.lead_type;
			lqf.naming_series = "LEAD QF.-";
			lqf.lead_name = frm.doc.lead_name;
			lqf.gender = frm.doc.gender;
			lqf.lead_owner = frm.doc.lead_owner;
			lqf.lead_date = frm.doc.lead_date;
			lqf.status = frm.doc.status;
			lqf.address_type = frm.doc.address_type;
			lqf.village = frm.doc.village;
			lqf.taluka = frm.doc.taluka;
			lqf.district = frm.doc.district;
			lqf.state = frm.doc.state;
			lqf.country = frm.doc.country;
			lqf.pincode = frm.doc.pincode;
			lqf.mobile_no = frm.doc.mobile_no;
			lqf.whats_app_no = frm.doc.whats_app_no;
			lqf.dist = frm.doc.dist;
			lqf.taluka_name = frm.doc.taluka_name;
			lqf.village_name = frm.doc.village_name;
			lqf.s4s_cc = frm.doc.s4s_cc;
			lqf.latitude = frm.doc.latitude;
			lqf.longitude = frm.doc.longitude;
			lqf.source_of_lead = frm.doc.source_of_lead;
			lqf.source_name = frm.doc.source_name;
			lqf.group_lead_name = frm.doc.group_lead_name;
			lqf.group_size = frm.doc.group_size;
			lqf.group_name = frm.doc.group_name;
			// lqf.aadhar_card = frm.doc.aadhar_card;
			// lqf.pan_card = frm.doc.pan_card;
			// lqf.address_proof = frm.doc.address_proof;
			// lqf.bank_passbook = frm.doc.bank_passbook;
			// lqf.ration_card = frm.doc.ration_card;
			// lqf.voters_id = frm.doc.voters_id;
			// lqf.light_bill = frm.doc.light_bill;
			lqf.space_for_processing = frm.doc.space_for_processing;
			lqf.photo_of_space = frm.doc.photo_of_space;
			lqf.photo_of_space_2 = frm.doc.photo_of_space_2;
			lqf.photo_of_space_3 = frm.doc.photo_of_space_3;
			lqf.light_availability = frm.doc.light_availability;
			lqf.water_availability = frm.doc.water_availability;
			lqf.ease_of_transportation = frm.doc.ease_of_transportation;
			lqf.ok_to_take_loan = frm.doc.ok_to_take_loan;
			lqf.taken_a_loan = frm.doc.taken_a_loan;
			lqf.defaulted_on_the_loan = frm.doc.defaulted_on_the_loan;
			lqf.me_is_interested = frm.doc.me_is_interested;
			lqf.follow_up_me = frm.doc.follow_up_me;
			lqf.recommend_the_me = frm.doc.recommend_the_me;
			lqf.followup_by = frm.doc.followup_by;
			lqf.next_contact_by = frm.doc.next_contact_by;
			lqf.next_contact_date = frm.doc.next_contact_date;
			lqf.notes = frm.doc.notes;
			lqf.audio_feedback = frm.doc.audio_feedback;
			lqf.me_lead = frm.doc.name;
			frappe.set_route("Form", "Lead Qualification Form", lqf.name);
		}, __('Create'));
	}
});
