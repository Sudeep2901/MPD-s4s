
let user_l = [];
let adm_l = []
frappe.call({
    method: "s4s.public.python.listview_all.user_filter",
    args: { doctype: 'Supplier' },
}).then(function(r){
    let data = r.message[0];
    user_l.push(data);
    adm_l.push(r.message[1])
})
frappe.listview_settings['Supplier'] = {
    filters:[],
    onload: function(listview) {
        // if (adm_l[0].includes(frappe.session.user)) {
        //     document.getElementsByClassName("filter-selector")[0].hidden = true;
        // } else {
        //     document.getElementsByClassName("filter-selector")[0].hidden = false;
        // }
        if (user_l[0] != "No") {
            frappe.route_options = user_l[0]
        }
        else{
            frappe.route_options = []
            listview.refresh()
            cur_list.filter_area.remove()
            cur_list.filter_area.clear()
        }
        listview.refresh()
    }
};

setTimeout(() => {
    if (adm_l[0].includes(frappe.session.user)) {
        document.getElementsByClassName("filter-selector")[0].hidden = true;
    } else {
        document.getElementsByClassName("filter-selector")[0].hidden = false;
    }
}, 300);