from datetime import datetime
import frappe
from frappe import _

# @frappe.whitelist()
# def user_filter(doctype):
#     filters = {}
#     if frappe.db.get_value("Search List Setting",{"user_id":frappe.session.user},["name"]):
#         doc = frappe.get_doc("Search List Setting",{'name':frappe.session.user})

#         for row in doc.filter:
#             if row.document_type == doctype and row.fieldtype not in ["Date","Datetime","Time"]:
#                 filters[row.fieldname] = ['in',[row.value]]
#             else:
#                 filters[row.fieldname] = ['=',row.value]
    
#     if len(filters) != 0:
#         return filters
#     else:
#         return "No"

@frappe.whitelist()
def user_filter(doctype):
    filters = {}
    user_l = []
    user = frappe.get_all("Search List Setting")
    for i in user:
        user_l.append(i.name)

    if frappe.db.get_value("Search List Setting",{"user_id":frappe.session.user},["name"]):
        doc = frappe.get_doc("Search List Setting",{'name':frappe.session.user})
        for row in doc.filter:
            if row.document_type == doctype :
                if row.fieldtype not in ["Date","Datetime","Time"]:
                    filters[row.fieldname] = ['in',[row.value]]
                else:
                    date_str = row.value
                    date_frmt = "%d-%m-%Y"
                    date_obj = datetime.strptime(date_str, date_frmt)
                    formatted_date = date_obj.strftime("%d-%m-%Y")
                    filters[row.fieldname] = ['==',formatted_date]


    if len(filters) != 0:
        return [filters,user_l]
    else:
        return ["No",user_l]

