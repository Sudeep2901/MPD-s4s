// Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Search List Setting', {
	setup: function(frm,cdt,cdn) {
		
		frm.set_query('fields', 'filter', function(doc, cdt, cdn) {
			var item = locals[cdt][cdn];
			var filters = {
				'document_type': item.document_type
			}
			return {
				filters: filters
			}
		});
	},
	// 	// frappe.call({
	// 	// 	method: "field_list",
	// 	// 	doc: frm.doc,
	// 	// 	args:{doctype:child.document_type},
	// 	// 	callback: function(r) {
	// 	// 		console.log("KKKKKKKKKKKKKKKKKK",r.message)
	// 	// 			// frappe.meta.get_docfield(cdt, "field_names", cdn).options = r.message;
	// 	// 			// frappe.model.set_value(cdt, cdn, "field_names", " "); 
	// 	// 			// frm.refresh_field("filter");
	// 	// 			// frm.fields_dict.filter.grid.update_docfield_property("field_names","options",r.message)
	// 	// 			// frm.refresh_field("filter");
	// 	// 	}
	// 	// });
	// }

	// refresh: function(frm) {
    //     // Access child table field
    //     var childTableField = frm.doc.filter;
        
    //     // Loop through child table rows
    //     childTableField.forEach(function(row) {
	// 	//  for(i in row){
	// 		console.log("555555555555555555555",row.document_type,doctype);
	// 		let k = [1,2,3,4,5,6]
	// 		if(row.document_type){
	// 			// frm.set_df_property("field_name", "options", [1,2,3,4,5]);
	// 			console.log("6666666666666666666666")
	// 			frappe.call({
	// 				method:"field_list",
	// 				doc:frm.doc,
	// 				args:{doctype:row.document_type},
	// 				callback:function(r){
	// 					// frm.set_df_property("field_name", "options",r.message );
	// 					frm.fields_dict.filter.grid.update_docfield_property("field_names","options",r.message)
	// 					console.log("*******************",r.message)
	// 				}
	// 			})
	// 		}

			
		//  }
            // Access fields within each row
            // var row.field_names = [1,2,3,5,4]
            
            // Perform actions with the child table fields
           
    //     });
    // }

});
frappe.ui.form.on('Search List Table', {

	document_type: function(frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		frappe.call({
			method: "field_list",
			doc: frm.doc,
			args:{doctype:child.document_type},
			callback: function(r) {
				console.log("KKKKKKKKKKKKKKKKKK",r.message)
					frappe.meta.get_docfield(cdt, "field_names", cdn).options = r.message;
					frappe.model.set_value(cdt, cdn, "field_names", " "); 
					frm.refresh_field("filter");
					// frm.fields_dict.filter.grid.update_docfield_property("field_names","options",r.message)
					// frm.refresh_field("filter");
			}
		});
	},
})