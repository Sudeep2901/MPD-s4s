# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from frappe.utils.data import flt
from erpnext.stock.doctype.serial_no.serial_no import get_delivery_note_serial_no


from s4s.public.python.proforma_taxes import calculate_taxes_and_totals as taxes

import frappe.utils
from frappe import _
from frappe.contacts.doctype.address.address import get_company_address
from frappe.model.mapper import get_mapped_doc
from frappe.model.utils import get_fetch_values
from frappe.utils import (
    add_days,
    cint,
    cstr,
    flt,
    get_link_to_form,
    getdate,
    nowdate,
    strip_html,
)
from six import string_types


from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.stock.doctype.item.item import get_item_defaults

from frappe.model.mapper import get_mapped_doc
from frappe.model.utils import get_fetch_values
from frappe.utils import (
    cint,
    flt,
    formatdate,
)
from six import iteritems
import erpnext
from erpnext.accounts.doctype.tax_withholding_category.tax_withholding_category import (
    get_party_tax_withholding_details,
)
from erpnext.accounts.party import get_due_date, get_party_account


class ProformaInvoice(SalesInvoice):
    def on_submit(self):
        if self.sales_order:
            so = frappe.get_doc("Sales Order", self.sales_order)
            so.proforma_invoice = self.name
            so.save(ignore_permissions=True)
        if self.delivery_note_ms:
            for i in self.delivery_note_ms:
                dn = frappe.get_doc("Delivery Note", i.delivery_note)
                dn.proforma_invoice = self.name
                for j in dn.items:
                    j.against_proforma_invoice = self.name

                dn.save(ignore_permissions=True)

    def validate(self):
        self.flags.ignore_validate = True

    @frappe.whitelist()
    def fetch_address(self, company):
        if frappe.db.get_value(
            "Address", {"company": company, "is_your_company_address": 1}, ["name"]
        ):
            return frappe.db.get_value(
                "Address", {"company": company, "is_your_company_address": 1}, ["name"]
            )

    def before_save(self):
        if self.delivery_note:
            dn = frappe.get_doc("Delivery Note", self.delivery_note)
            if dn.cc_name:
                if self.cc_name != dn.cc_name:
                    frappe.throw("CC Name doesn't match in Delivery Note.")

    @frappe.whitelist()
    def get_dn_list(self, items):
        dn_list = []
        for i in items:
            if "delivery_note" in i:
                dn_list.append(i.get("delivery_note"))

        ms_list = []
        if dn_list:
            dn_list = list(set(dn_list))
            for dn in dn_list:
                d = {
                    "docstatus": 0,
                    "doctype": "Delivery Note In Proforma",
                    "__islocal": 1,
                    "__unsaved": 1,
                    "owner": frappe.session.user,
                    "parent": self.name,
                    "parentfield": "delivery_note_ms",
                    "parenttype": "Proforma Invoice",
                    "idx": 1,
                    "delivery_note": dn,
                }
                ms_list.append(d)

        if ms_list:
            return ms_list
        else:
            return []


@frappe.whitelist()
def make_sales_invoice_from_so(source_name, target_doc=None, ignore_permissions=False):
    def postprocess(source, target):
        set_missing_values(source, target)
        # Get the advance paid Journal Entries in Sales Invoice Advance
        if target.get("allocate_advances_automatically"):
            target.set_advances()

    def set_missing_values(source, target):
        t = taxes(target)
        target.flags.ignore_permissions = True
        target.run_method("set_missing_values")
        target.run_method("set_po_nos")
        # target.run_method("calculate_taxes_and_totals")
        if target.get("taxes"):
            target.grand_total = flt(target.get("taxes")[-1].total) + flt(
                target.rounding_adjustment
            )
        else:
            target.grand_total = flt(target.net_total)

        if target.apply_discount_on == "Grand Total" and target.get(
            "is_cash_or_non_trade_discount"
        ):
            target.grand_total -= target.discount_amount

        if target.get("taxes"):
            target.total_taxes_and_charges = flt(
                target.grand_total - target.net_total - flt(target.rounding_adjustment),
                target.precision("total_taxes_and_charges"),
            )
        else:
            target.total_taxes_and_charges = 0.0

        t._set_in_company_currency(
            doc=target, fields=["total_taxes_and_charges", "rounding_adjustment"]
        )

        target.base_grand_total = (
            flt(
                target.grand_total * target.conversion_rate,
                target.precision("base_grand_total"),
            )
            if target.total_taxes_and_charges
            else target.base_net_total
        )
        target.round_floats_in(target, ["grand_total", "base_grand_total"])

        t.set_rounded_total()

        if source.company_address:
            target.update({"company_address": source.company_address})
        else:
            # set company address
            target.update(get_company_address(target.company))

        if target.company_address:
            target.update(
                get_fetch_values(
                    "Sales Invoice", "company_address", target.company_address
                )
            )

        # set the redeem loyalty points if provided via shopping cart
        if source.loyalty_points and source.order_type == "Shopping Cart":
            target.redeem_loyalty_points = 1

    def update_item(source, target, source_parent):
        target.amount = flt(source.amount) - flt(source.billed_amt)
        target.base_amount = target.amount * flt(source_parent.conversion_rate)
        target.qty = (
            target.amount / flt(source.rate)
            if (source.rate and source.billed_amt)
            else source.qty - source.returned_qty
        )

        if source_parent.project:
            target.cost_center = frappe.db.get_value(
                "Project", source_parent.project, "cost_center"
            )
        if target.item_code:
            item = get_item_defaults(target.item_code, source_parent.company)
            item_group = get_item_group_defaults(
                target.item_code, source_parent.company
            )
            cost_center = item.get("selling_cost_center") or item_group.get(
                "selling_cost_center"
            )

            if cost_center:
                target.cost_center = cost_center

    doclist = get_mapped_doc(
        "Sales Order",
        source_name,
        {
            "Sales Order": {
                "doctype": "Proforma Invoice",
                "field_map": {
                    "party_account_currency": "party_account_currency",
                    "payment_terms_template": "payment_terms_template",
                },
                "field_no_map": ["payment_terms_template"],
                "validation": {"docstatus": ["=", 1]},
            },
            "Sales Order Item": {
                "doctype": "Proforma Invoice Item",
                "field_map": {
                    "name": "so_detail",
                    "parent": "sales_order",
                },
                "postprocess": update_item,
                "condition": lambda doc: doc.qty
                and (doc.base_amount == 0 or abs(doc.billed_amt) < abs(doc.amount)),
            },
            "Sales Taxes and Charges": {
                "doctype": "Sales Taxes and Charges",
                "add_if_empty": True,
            },
            "Sales Team": {"doctype": "Sales Team", "add_if_empty": True},
        },
        target_doc,
        postprocess,
        ignore_permissions=ignore_permissions,
    )

    automatically_fetch_payment_terms = cint(
        frappe.db.get_single_value(
            "Accounts Settings", "automatically_fetch_payment_terms"
        )
    )
    if automatically_fetch_payment_terms:
        doclist.set_payment_schedule()

    doclist.set_onload("ignore_price_list", True)

    return doclist


@frappe.whitelist()
def make_sales_invoice_from_dn(source_name, target_doc=None):
    doc = frappe.get_doc("Delivery Note", source_name)

    to_make_invoice_qty_map = {}
    returned_qty_map = get_returned_qty_map(source_name)
    invoiced_qty_map = get_invoiced_qty_map(source_name)

    def set_missing_values(source, target):
        t = taxes(target)
        target.run_method("set_missing_values")
        target.run_method("set_po_nos")

        if len(target.get("items")) == 0:
            frappe.throw(_("All these items have already been Invoiced/Returned"))

        # target.run_method("calculate_taxes_and_totals")
        if target.get("taxes"):
            target.grand_total = flt(target.get("taxes")[-1].total) + flt(
                target.rounding_adjustment
            )
        else:
            target.grand_total = flt(target.net_total)

        if target.apply_discount_on == "Grand Total" and target.get(
            "is_cash_or_non_trade_discount"
        ):
            target.grand_total -= target.discount_amount

        if target.get("taxes"):
            target.total_taxes_and_charges = flt(
                target.grand_total - target.net_total - flt(target.rounding_adjustment),
                target.precision("total_taxes_and_charges"),
            )
        else:
            target.total_taxes_and_charges = 0.0

        t._set_in_company_currency(
            doc=target, fields=["total_taxes_and_charges", "rounding_adjustment"]
        )

        target.base_grand_total = (
            flt(
                target.grand_total * target.conversion_rate,
                target.precision("base_grand_total"),
            )
            if target.total_taxes_and_charges
            else target.base_net_total
        )
        target.round_floats_in(target, ["grand_total", "base_grand_total"])

        t.set_rounded_total()

        # set company address
        if source.company_address:
            target.update({"company_address": source.company_address})
        else:
            # set company address
            target.update(get_company_address(target.company))

        if target.company_address:
            target.update(
                get_fetch_values(
                    "Sales Invoice", "company_address", target.company_address
                )
            )

    def update_item(source_doc, target_doc, source_parent):
        target_doc.qty = to_make_invoice_qty_map[source_doc.name]

        if (
            source_doc.serial_no
            and source_parent.per_billed > 0
            and not source_parent.is_return
        ):
            target_doc.serial_no = get_delivery_note_serial_no(
                source_doc.item_code, target_doc.qty, source_parent.name
            )

    def get_pending_qty(item_row):
        pending_qty = item_row.qty - invoiced_qty_map.get(item_row.name, 0)

        returned_qty = 0
        if returned_qty_map.get(item_row.name, 0) > 0:
            returned_qty = flt(returned_qty_map.get(item_row.name, 0))
            returned_qty_map[item_row.name] -= pending_qty

        if returned_qty:
            if returned_qty >= pending_qty:
                pending_qty = 0
                returned_qty -= pending_qty
            else:
                pending_qty -= returned_qty
                returned_qty = 0

        to_make_invoice_qty_map[item_row.name] = pending_qty

        return pending_qty

    doc = get_mapped_doc(
        "Delivery Note",
        source_name,
        {
            "Delivery Note": {
                "doctype": "Proforma Invoice",
                "field_map": {"is_return": "is_return"},
                "validation": {"docstatus": ["=", 1]},
            },
            "Delivery Note Item": {
                "doctype": "Proforma Invoice Item",
                "field_map": {
                    "name": "dn_detail",
                    "parent": "delivery_note",
                    "so_detail": "so_detail",
                    "against_sales_order": "sales_order",
                    "serial_no": "serial_no",
                    "cost_center": "cost_center",
                },
                "postprocess": update_item,
                "filter": lambda d: get_pending_qty(d) <= 0
                if not doc.get("is_return")
                else get_pending_qty(d) > 0,
            },
            "Sales Taxes and Charges": {
                "doctype": "Sales Taxes and Charges",
                "add_if_empty": True,
            },
            "Sales Team": {
                "doctype": "Sales Team",
                "field_map": {"incentives": "incentives"},
                "add_if_empty": True,
            },
        },
        target_doc,
        set_missing_values,
    )

    automatically_fetch_payment_terms = cint(
        frappe.db.get_single_value(
            "Accounts Settings", "automatically_fetch_payment_terms"
        )
    )
    if automatically_fetch_payment_terms:
        doc.set_payment_schedule()

    doc.set_onload("ignore_price_list", True)

    is_same_cc = True
    dn_list = []

    for i in doc.items:
        dn_list.append(i.delivery_note)

    if dn_list:
        list_wo_duplicate = list(set(dn_list))
        cc_name_lst = []

        if len(list_wo_duplicate) > 1:
            for e in list_wo_duplicate:
                dn_doc = frappe.get_doc("Delivery Note", e)
                cc_name_lst.append(dn_doc.cc_name)

        if cc_name_lst:
            if len(list(set(cc_name_lst))) != 1:
                is_same_cc = False

    if is_same_cc == False:
        frappe.throw("CC Name Not Same in Selected Delivery Notes!")
        return

    return doc


def get_returned_qty_map(delivery_note):
    """returns a map: {so_detail: returned_qty}"""
    returned_qty_map = frappe._dict(
        frappe.db.sql(
            """select dn_item.dn_detail, abs(dn_item.qty) as qty
		from `tabDelivery Note Item` dn_item, `tabDelivery Note` dn
		where dn.name = dn_item.parent
			and dn.docstatus = 1
			and dn.is_return = 1
			and dn.return_against = %s
	""",
            delivery_note,
        )
    )

    return returned_qty_map


def get_invoiced_qty_map(delivery_note):
    """returns a map: {dn_detail: invoiced_qty}"""
    invoiced_qty_map = {}

    for dn_detail, qty in frappe.db.sql(
        """select dn_detail, qty from `tabSales Invoice Item`
		where delivery_note=%s and docstatus=1""",
        delivery_note,
    ):
        if not invoiced_qty_map.get(dn_detail):
            invoiced_qty_map[dn_detail] = 0
        invoiced_qty_map[dn_detail] += qty

    return invoiced_qty_map
