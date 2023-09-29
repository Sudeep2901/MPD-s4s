frappe.ui.form.on("Purchase Order",{
    // validate : function(frm){
    //     frappe.db.get_single_value('Buying Settings', 'buying_price_list').then(buying_price_list => {
    //         // console.log(buying_price_list)
    //         if(buying_price_list){
    //             $.each(frm.doc.items, function(index, row) {
    //                 frappe.call({
    //                     method: "frappe.client.get_value",
    //                     args: {
    //                         "doctype": "Item Price",
    //                         "filters": {
    //                             "item_code": row.item_code,
    //                             "price_list":buying_price_list,
    //                         },
    //                         "fieldname":"price_list_rate"
    //                     }, 
    //                     callback: function(r) {
    //                         if(row.rate > r.message["price_list_rate"]){
    //                             frappe.validated = false;
    //                             // frappe.msgprint("Item Price for row",index," must be less than ",r.message["price_list_rate"]);
    //                             // frappe.msgprint(__('Print Failure Insufficient Stock for Item:<a href="/desk#Form/Item/{0}">{0}</a> ', [frm.doc.sal_flagged_item]));
    //                             frappe.msgprint(__('Item Price for row {0} must be less than {1}', [index+1,r.message["price_list_rate"]]));
    //                         }
    //                     }
    //                 });
    //             })
    //         }
    //     })
    // },
    // setup:function(frm){
    //     console.log(frappe.db.get_single_value('Buying Settings', 'buying_price_list'));
    // }
})