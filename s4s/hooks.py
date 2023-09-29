from . import __version__ as app_version

app_name = "s4s"
app_title = "S4S"
app_publisher = "Mannlowe Information Service Pvt. Ltd."
app_description = "Food Processing"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "shrikant.pawar@mannlowe.com"
app_license = "MIT"


# fixtures = [
# {"dt":"Custom Field", "filters": [["fieldname", "in", ("release_fence", "search_mode", "priority", "size_minimum", "size_maximum", "customer_pricing_rule_id", "planning_parameters", "column_break_16", "alternate_selection", "column_break_25", "type", "post_op_time", "postop_time", "size_minimum", "size_multiple", "size_maximum", "planning_parameters", "release_fence", "duration", "duration_per_unit", "column_break_66", "search_mode", "priority", "alternate_selection", "type", "c", "location", "available", "type", "column_break_5", "minimum_calendar", "min_interval", "location", "column_break_7", "priority", "fence", "effective_start", "effective_end", "size_minimum", "size_multiple", "size_maximum", "section_break_2", "resource", "resource_quantity", "lead_time", "type", "release_plan", "release_plan_wo", "frepple_po_ref", "column_break_2", "calendar", "release_plan_wo", "frepple_mo_ref", "section_break_15", "warehouse", "type", "constrained", "column_break_21", "efficiency", "maximum_calendar", "available", "maximum", "max_early", "efficiency_calendar")]]},
# {"dt":"Custom Field", "filters": [["fieldname", "in", ("taluka")]]},
# 	{"dt": "Custom Field", "filters": [
#      	[
#         	"name", "like", "Supplier-%"
#      	]
# 	]}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/s4s/css/s4s.css"
# app_include_js = "/assets/s4s/js/s4s.js"

# include js, css files in header of web template
# web_include_css = "/assets/s4s/css/s4s.css"
# web_include_js = "/assets/s4s/js/s4s.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "s4s/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
    "Purchase Receipt": "public/js/custom_purchase_receipt.js",
    "Purchase Order": "public/js/custom_purchase_order.js",
    "Stock Entry": "public/js/custom_stock_entry.js",
    "Pick List": "public/js/custom_pick_list.js",
    "Work Order": "public/js/custom_work_order.js",
    "User": "public/js/custom_user.js",
    "Payment Entry": "public/js/custom_payment_entry.js",
    "Sales Order": "public/js/custom_sales_order.js",
    "Delivery Note": "public/js/custom_delivery_note.js",
}

doctype_list_js = {
    "Purchase Invoice": "public/js/purchase_invoice_listview.js",
    "Supplier": "public/js/supplier_listview.js",
    "S4S Supplier": "public/js/s4s_supplier_listview.js",
    "DCM Material Request": "public/js/doc_material_request_listview.js",
    "S4S Farmer Query": "public/js/s4s_farmer_query_listview.js",
    "S4S Purchase": "public/js/s4s_purchase_listview.js",
    "Purchase Receipt": "public/js/purchase_receipt_listview.js",
    "Payment Entry": "public/js/payment_entry_listview.js",
    "Sales Order": "public/js/sale_order_listview.js",
    "Pick List": "public/js/pick_list_listview.js",
    "Sales Invoice": "public/js/sales invoice_listview.js",
    "Customer": "public/js/customer_listview.js",
    "Delivery Note": "public/js/delivery_note_listview.js",
    "Proforma Invoice": "public/js/performa_invoice_listview.js",
    "S4S Transaction Approval": "public/js/s4s_transaction_approva_listview.js",
}


# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "s4s.install.before_install"
# after_install = "s4s.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "s4s.uninstall.before_uninstall"
# after_uninstall = "s4s.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "s4s.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    # "ToDo": "custom_app.overrides.CustomToDo"
    "Pick List": "s4s.public.python.custom_methods.PickList"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Work Order": {"before_naming": "s4s.public.python.custom_methods.before_naming"},
    "Delivery Note": {
        "before_save": "s4s.public.python.custom_methods.map_fields_in_dn",
        "on_submit": "s4s.public.python.custom_methods.share_doc",
    },
    "DocShare": {
        "after_insert": "s4s.public.python.custom_methods.create_share_doc",
        "after_delete": "s4s.public.python.custom_methods.delete_share_doc",
    },
    # "Purchase Invoice": {
    #     "on_submit": "s4s.public.python.custom_methods.get_payment_entry"
    # },
    "Stock Entry": {
        "before_save": "s4s.public.python.custom_methods.set_basic_rate_in_stock_entry",
        "before_submit": "s4s.public.python.custom_methods.set_basic_rate_in_stock_entry",
    },
    "Sales Order": {
        "before_save": "s4s.public.python.custom_methods.make_cc_mandatory_in_so"
    }
    # "User":{"before_save":"s4s.public.python.custom_user.fetch_data"}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"s4s.tasks.all"
# 	],
# 	"daily": [
# 		"s4s.tasks.daily"
# 	],
# 	"hourly": [
# 		"s4s.tasks.hourly"
# 	],
# 	"weekly": [
# 		"s4s.tasks.weekly"
# 	]
# 	"monthly": [
# 		"s4s.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "s4s.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    # "frappe.desk.doctype.event.event.get_events": "s4s.event.get_events"
    "erpnext.selling.doctype.sales_order.sales_order.create_pick_list": "s4s.public.python.custom_methods.create_pick_list",
    "erpnext.stock.doctype.pick_list.pick_list.create_delivery_note": "s4s.public.python.custom_methods.create_delivery_note",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
override_doctype_dashboards = {
    "Delivery Note": "s4s.public.python.delivery_note_dashboard.get_data"
}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
    {
        "doctype": "{doctype_1}",
        "filter_by": "{filter_by}",
        "redact_fields": ["{field_1}", "{field_2}"],
        "partial": 1,
    },
    {
        "doctype": "{doctype_2}",
        "filter_by": "{filter_by}",
        "partial": 1,
    },
    {
        "doctype": "{doctype_3}",
        "strict": False,
    },
    {"doctype": "{doctype_4}"},
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"s4s.auth.validate"
# ]

# Translation
# --------------------------------

# Make link fields search translated document names for these DocTypes
# Recommended only for DocTypes which have limited documents with untranslated names
# For example: Role, Gender, etc.,
# translated_search_doctypes = []
# import frappe
# lst = []
# a = frappe.get_all("Field Name")

# for i in a:
#     lst.append(i.get("name"))

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                (
                    "Stock Entry-sfg_dispatch_request",
                    "Stock Entry-me_sfg_dispatch_request",
                    "Stock Entry-me_sfg_processing_data",
                    "Stock Entry-factory_rm_transfer_to_mfg",
                    "Stock Entry-material_transfer_wip_to_fg",
                    "Stock Entry-_sfg_transfer_wh_to_factory",
                    "Stock Entry-rm_transfer_wh_to_me",
                    "Stock Entry-me_rm_daily_processing",
                    "Stock Entry-me_sfg_dispatch_note",
                    "BOM-is_me_bom",
                    "Stock Entry-e_way_bill_no",
                    "Stock Entry-to_date",
                    "Stock Entry-from_date",
                    "Stock Entry-is_s4s_purchase",
                    "Stock Entry-custom_supplier_name",
                    "Stock Entry-custom_supplier",
                    "Supplier-state_",
                    "Stock Entry-dcm_sfg_transfer_to_wip",
                    "Stock Entry-sfg_transfer_wip_to_fg",
                    "Stock Entry-me_sfg_transfer_wip_to_fg",
                    "Stock Entry-me_sfg_transfer_to_wip",
                    "Stock Entry-material_transfer_wh_to_wh",
                    "Stock Entry-material_return_from_subcontractor",
                    "Stock Entry-material_transfer_for_subcontractor",
                    "Stock Entry-subcontracting_supplier_name",
                    "Stock Entry-subcontracting_supplier",
                    "Stock Entry-material_in",
                    "Purchase Receipt-fpo_purchase_order",
                    "Warehouse-warehouse_subtype",
                    "Warehouse-dcm_link",
                    "Stock Entry-sfg_dispatch_request1",
                    "Stock Entry-sfg_material_in",
                    "Warehouse-vlcc_link",
                    "Warehouse-cc_link1",
                    "Stock Entry-rm_transfer_wh_to_village_wh",
                    "Stock Entry-me_rm_in",
                    "Stock Entry-me_sfg_processing",
                    "Stock Entry-rm_return_me_wh_to_village_wh",
                    "Delivery Note-cc_name",
                    "Delivery Note Item-against_proforma_invoice",
                    "Stock Entry-rm_transfer_vlcc_to_cc",
                    "Stock Entry-vlcc_rm_in",
                    "Sales Order-cc_name",
                    "Purchase Receipt-s4s_purchase"
                ),
            ]
        ],
    },
    {
        "dt": "Property Setter",
        "filters": [["name", "in", ("Purchase Receipt Item-base_rate-precision")]],
    },
    # {"dt":"Field Name","filters":[["name", "in", tuple(lst)]]}
]
