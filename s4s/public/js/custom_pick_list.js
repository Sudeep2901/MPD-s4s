frappe.ui.form.on("Pick List",{
    setup: function(frm){
        frm.set_query('parent_warehouse', () => {
			return {
				filters: {
					'company': frm.doc.company,
					'is_group':0
				}
			};
		});
		frm.set_query('sales_order', () => {
			if(frm.doc.parent_warehouse){
				filters = {
					'company': frm.doc.company,
					'set_warehouse':frm.doc.parent_warehouse
				}

			}
			else{
				filters = {
					'company': frm.doc.company,
				}
			}
			return {
				filters
			};
		});

		frappe.call({
			method:'s4s.public.python.custom_methods.make_cc_mandatory',
			args:{},
			callback: function(r){
				if(r.message){
					if(r.message == "Success"){
						frm.set_df_property("cc_name","reqd",1)
						frm.refresh_field("cc_name")
					}
				}

			}
		})
    },

	parent_warehouse: function(frm){
		if(frm.doc.parent_warehouse){
			frm.set_query('sales_order', () => {
				return {
					filters: {
						'company': frm.doc.company,
						'set_warehouse':frm.doc.parent_warehouse
					}
				};
			});
		}


	},


	get_inventory_batches:function(frm){
		if(!frm.doc.parent_warehouse){
			frappe.msgprint("Please Enter Parent Warehouse.")

		}
		else{
			frappe.call({
				method:'s4s.public.python.custom_methods.get_batch_no',
				args:{filters:{'warehouse':frm.doc.parent_warehouse},searchfield:'name',start:0,page_len:20,doctype:'Batch',txt:''},
				callback:function(r){
					console.log('response',r.message)


					if(r.message.length != 0){
						frm.set_value("get_inventory_clicked",1)
						frm.doc.locations = []
						let data = r.message
						const sortedData = data.slice().sort((a, b) => a.item_code.localeCompare(b.item_code));
						sortedData.forEach(element => {
						var item_locations = cur_frm.add_child('locations')
						item_locations.item_code = element.item_code
						item_locations.batch_no = element.batch_no
						item_locations.qty = element.qty
						item_locations.stock_qty = element.qty
						item_locations.warehouse = frm.doc.parent_warehouse
						item_locations.rate = element.rate
						frm.refresh_field('locations')
					});

					}
					else{
						frm.clear_table('locations')
						frm.refresh_field('locations')
						frappe.msgprint(`No batches found for ${frm.doc.parent_warehouse.bold()}.` )
					}
					
				}
			})

		}
			
			
	}
	
   
})
