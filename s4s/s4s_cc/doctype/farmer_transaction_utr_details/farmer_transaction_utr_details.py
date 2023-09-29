# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FarmerTransactionUTRDetails(Document):
    def on_submit(self):
        self.update_s4s_utr_details()

    def before_save(self):
        self.update_s4s_utr_details()

    def update_s4s_utr_details(self):
        for row in self.approval_details:
            if row.transaction_no:
                sp = frappe.get_doc("S4S Purchase", row.transaction_no)
                if sp.docstatus == 1:
                    if row.s4s_utr_no:
                        sp.s4s_utr_no = row.s4s_utr_no
                    if row.s4s_payment_no:
                        sp.s4s_payment_no = row.s4s_payment_no
                    if row.fpo_utr_no:
                        sp.fpo_utr_no = row.fpo_utr_no
                    if row.fpo_payment_no:
                        sp.fpo_payment_no = row.fpo_payment_no

                    sp.save(ignore_permissions=True)

    @frappe.whitelist()
    def get_data(self):
        if not self.from_date:
            frappe.throw("Please Enter From Date.")
        if not self.to_date:
            frappe.throw("Please Enter To Date.")

        if self.from_date > self.to_date:
            frappe.throw("From Date Cannot be Greater than To Date.")

        if not self.company:
            frappe.throw("Please Enter Company.")

        if self.cc_name:
            query = frappe.db.sql(
                f"""
				SELECT
					s4s_p.creation,
					s4s_p.docstatus,
					s4s_p.transaction_date,
					s4s_p.cc_name,
					s4s_p.supplier AS farmer,
					s4s_p.supplier_name AS farmer_name,
					s4s_p.name AS s4s_p_name,
					variant.item_code,
					s4s_p.total_weight AS qty,
					purchase_rect.name AS pur_rect,
					purchase_rect.posting_date AS pr_date,
					s4s_p.total_amount as amount,
					s4s_p.total_deduction_amount as deduction,
					s4s_p.grand_total as net_total,
					pri.batch_no,
					dni.parent as del_note,
					DATE(dni.creation) as del_date,
					pi.name as pi_name,
					pi.posting_date as pi_date,
					so.name as so_name,
					so.transaction_date as so_date,
					dn.po_no as po_no,
					dn.po_date as po_date,
					pur_inv.name as purchase_inv,
					grn.name as grn_name,
					grn.posting_date as grn_date,
					pe.name as pe_name

				FROM
					`tabS4S Purchase` AS s4s_p
				LEFT JOIN
					`tabS4S Purchase receipt` AS variant
				ON
					variant.parent = s4s_p.name
				LEFT JOIN
					`tabPurchase Receipt` as purchase_rect
				ON 
					s4s_p.name = purchase_rect.s4s_purchase
				LEFT JOIN
					`tabPurchase Receipt Item` as pri
				ON
					purchase_rect.name = pri.parent
				LEFT JOIN
					`tabDelivery Note Item` as dni
				ON
					pri.batch_no = dni.batch_no
				LEFT JOIN
					`tabDelivery Note` as dn
				ON 
					dn.name = dni.parent 

				LEFT JOIN
					`tabProforma Invoice` as pi
				ON
					dn.proforma_invoice = pi.name
				LEFT JOIN 
					`tabSales Order` as so
				ON 
					dn.sales_order = so.name
				LEFT JOIN 
					`tabPurchase Invoice` as pur_inv
				ON 
					s4s_p.name = pur_inv.s4s_purchase
				LEFT JOIN 
					`tabPurchase Receipt` as grn
				ON
					grn.supplier_delivery_note = dn.name
				LEFT JOIN
					`tabPayment Entry` as pe
				ON
					s4s_p.name = pe.s4s_purchase AND pe.docstatus = 0
				WHERE 
					s4s_p.company = '{self.company}' AND
					s4s_p.cc_name = '{self.cc_name}' AND
					s4s_p.docstatus = 1 AND
					s4s_p.creation BETWEEN '{self.from_date}' AND '{self.to_date}'
				ORDER BY
					s4s_p.transaction_date DESC
			""",
                as_dict=1,
            )
        else:
            query = frappe.db.sql(
                f"""
				SELECT
					s4s_p.creation,
					s4s_p.docstatus,
					s4s_p.transaction_date,
					s4s_p.cc_name,
					s4s_p.supplier AS farmer,
					s4s_p.supplier_name AS farmer_name,
					s4s_p.name AS s4s_p_name,
					variant.item_code,
					s4s_p.total_weight AS qty,
					purchase_rect.name AS pur_rect,
					purchase_rect.posting_date AS pr_date,
					s4s_p.total_amount as amount,
					s4s_p.total_deduction_amount as deduction,
					s4s_p.grand_total as net_total,
					pri.batch_no,
					dni.parent as del_note,
					DATE(dni.creation) as del_date,
					pi.name as pi_name,
					pi.posting_date as pi_date,
					so.name as so_name,
					so.transaction_date as so_date,
					dn.po_no as po_no,
					dn.po_date as po_date,
					pur_inv.name as purchase_inv,
					grn.name as grn_name,
					grn.posting_date as grn_date,
					pe.name as pe_name

				FROM
					`tabS4S Purchase` AS s4s_p
				LEFT JOIN
					`tabS4S Purchase receipt` AS variant
				ON
					variant.parent = s4s_p.name
				LEFT JOIN
					`tabPurchase Receipt` as purchase_rect
				ON 
					s4s_p.name = purchase_rect.s4s_purchase
				LEFT JOIN
					`tabPurchase Receipt Item` as pri
				ON
					purchase_rect.name = pri.parent
				LEFT JOIN
					`tabDelivery Note Item` as dni
				ON
					pri.batch_no = dni.batch_no
				LEFT JOIN
					`tabDelivery Note` as dn
				ON 
					dn.name = dni.parent 

				LEFT JOIN
					`tabProforma Invoice` as pi
				ON
					dn.proforma_invoice = pi.name
				LEFT JOIN 
					`tabSales Order` as so
				ON 
					dn.sales_order = so.name
				LEFT JOIN 
					`tabPurchase Invoice` as pur_inv
				ON 
					s4s_p.name = pur_inv.s4s_purchase
				LEFT JOIN 
					`tabPurchase Receipt` as grn
				ON
					grn.supplier_delivery_note = dn.name

				LEFT JOIN
					`tabPayment Entry` as pe
				ON
					s4s_p.name = pe.s4s_purchase AND pe.docstatus = 0

				WHERE 
					s4s_p.company = '{self.company}' AND
					s4s_p.docstatus = 1 AND
					s4s_p.creation BETWEEN '{self.from_date}' AND '{self.to_date}'
				ORDER BY
					s4s_p.transaction_date DESC
			""",
                as_dict=1,
            )

        new_query = []

        for dataset in query:
            if not frappe.db.get_value(
                "Farmer Transaction UTR Item",
                {
                    "transaction_no": dataset.get("s4s_p_name"),
                    "docstatus": ["in", [0, 1]],
                    "parent": ["!=", self.name],
                },
                ["parent"],
            ):
                new_query.append(dataset)

        if len(new_query) != 0:
            return new_query
        else:
            return "No Records"
