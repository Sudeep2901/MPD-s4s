// Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Lead Qualification Form', {
	// refresh: function(frm) {

	// }
	// before_save:function(frm){
	// 	frappe.db.set_value("ME Lead",frm.doc.me_lead,"lead_approval_status",frm.doc.lead_approval_status);
	// },
	on_submit:function(frm){
		frappe.db.set_value("ME Lead",frm.doc.me_lead,"lead_approval_status",frm.doc.lead_approval_status);
	},
	lead_approval_status:function(frm){
		if(frm.doc.docstatus===1){
			frappe.db.set_value("ME Lead",frm.doc.me_lead,"lead_approval_status",frm.doc.lead_approval_status);
		}
	},
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
							const arr = ["lead_qualification_owner","lead_type", "lead_name", "age", "religion", "marital_status", "education_deatils", "housewife", "own_farm", "farm_labour", "job", "daily_wage_worker", "part_time_work", "work_experience", "work_experience_details", "no_of_family_members", "family_type", "husband", "husbands_occupation", "no_of_children", "age_youngest_child", "age_oldest_child", "me_stay_with_inlaws", "father_inlaw", "mother_inlaw", "husband_1", "children", "inlaws", "me_household", "irrigation_type", "soybean", "wheat", "maize", "ginger", "tomato", "moong", "onion", "tur", "bajra", "cotton", "earning_members", "annual_farm_income", "annual_other_income", "family_income_dependency", "no_of_cattle", "cow", "buffalo", "goat", "cattle_details", "needy_for_work", "hardwork", "communication", "understanding_of_work", "behavior_with_group", "remark", "me_committed_s4s", "space", "site_located_at", "accessibility_me_full_time", "accessibility_me_part_time", "distance_from_site", "space_rating_hygiene", "space_rating_safety", "space_rating_neighbor", "flooring", "electricity_type", "electricity_meter", "electricity_load", "electricity_power_cut", "electricity_remark", "water_source", "water_availability", "storage_availability", "road_connectivity", "unloading_rm", "hamal_availability", "aadhar_card", "aadhar_card_no", "pan_card", "pan_card_no", "address_proof", "bank_passbook", "ration_card", "voters_id", "light_bill", "others", "communicated_me", "dcm_work", "bank_loan", "earning_potential", "company_requirements", "legal", "ethics", "me_willing_work", "family_willing_support", "banking_willingness", "recommend_me", "remark_2", "me_lead"]
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
});
