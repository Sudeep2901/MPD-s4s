frappe.ui.form.on("Purchase Receipt",{
    refresh:function(frm){
        $('button[data-fieldname="move_data_to_farmers"]').css("color","white");
        $('button[data-fieldname="move_data_to_farmers"]').css("background-color", "#2490ef");
    },
    move_data_to_farmers:function(frm){
        cur_frm.clear_table("farmer_purchase_receipt");
        var total_qty = 0.0;
        var total_amount = 0.0;
        $.each(frm.doc.items, function(index, row) {
            var d = frm.add_child("farmer_purchase_receipt");
            d.item_code = row.item_code;
            d.item_name = row.item_name;
            d.variety = row.variety;
            d.moisture_content = row.moisture_content;
            d.received_qty = row.received_qty;
            d.qty = row.qty;
            d.katta = row.rejected_qty;
            d.rate = row.rate;
            d.amount = row.amount;
            total_qty += d.qty;
            total_amount += d.amount;
            cur_frm.refresh_field("farmer_purchase_receipt");
        });
        frm.doc.total_farmers_quantity = total_qty;
        frm.doc.farmers_total = total_amount;
        frm.refresh_field("total_farmers_quantity");
        frm.refresh_field("farmers_total");
    },
    before_save:function(frm){
        $.each(frm.doc.items, function(index, row) {
            $.each(frm.doc.farmer_purchase_receipt, function(index1, row1){
                if(row.item_code === row1.item_code){
                    row.rate = row1.amount/row.qty;
                }
            })
        })
        frm.refresh_field("items");
    }
})

var set_css = function (frm) {
    let el = document.querySelectorAll("[data-fieldname='move_data_to_farmers']")[0].style.backgroundColor ="#4287f5";
    let fl = document.querySelectorAll("[data-fieldname='move_data_to_farmers']")[0].style.color ="white";
}

frappe.ui.form.on("S4S Farmer Receipt",{
    qty : function(frm,cdt,cdn){
        var d = locals[cdt][cdn];
        d.amount = d.qty * d.rate;
        d.received_qty = d.katta + d.qty;
        cur_frm.refresh_field("farmer_purchase_receipt");

        var total_qty = 0.0;
        var total_amount = 0.0;
        $.each(frm.doc.farmer_purchase_receipt, function(index, row) {
            total_qty += row.qty;
            total_amount += row.amount;
        });
        cur_frm.doc.total_farmers_quantity = total_qty;
        cur_frm.doc.farmers_total = total_amount;
        // console.log(cur_frm.doc.total_farmers_quantity,cur_frm.doc.farmers_total);
        cur_frm.refresh_field("total_farmers_quantity");
        cur_frm.refresh_field("farmers_total");
    },
    rate : function(frm,cdt,cdn){
        var d = locals[cdt][cdn];
        d.amount = d.qty * d.rate;
        cur_frm.refresh_field("farmer_purchase_receipt");

        var total_qty = 0.0;
        var total_amount = 0.0;
        $.each(frm.doc.farmer_purchase_receipt, function(index, row) {
            total_qty += row.qty;
            total_amount += row.amount;
        });
        cur_frm.doc.total_farmers_quantity = total_qty;
        cur_frm.doc.farmers_total = total_amount;
        // console.log(total_qty,total_amount,cur_frm.doc.total_farmers_quantity,cur_frm.doc.farmers_total);
        cur_frm.refresh_field("total_farmers_quantity");
        cur_frm.refresh_field("farmers_total");
    },
    katta : function(frm,cdt,cdn){
        var d = locals[cdt][cdn];
        d.received_qty = d.katta + d.qty;
        cur_frm.refresh_field("farmer_purchase_receipt");
    }
})