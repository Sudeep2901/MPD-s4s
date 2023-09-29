frappe.listview_settings['Shared Documents'] = {

    filters : [],

    onload(listview) {
        if (frappe.session.user == 'Administrator') {
            document.getElementsByClassName("filter-selector")[0].hidden = false;
        } else {
            document.getElementsByClassName("filter-selector")[0].hidden = true;
            this.filters =  ['user', '=', frappe.session.user]
            frappe.route_options = [{'user':['=',frappe.session.user]}]
        }

      
    },

}