# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import collections
import frappe
from frappe.model.document import Document

class MERMIn(Document):
	def validate(self):
		for row in self.rm_item_details:
			if row.sent_qty != row.qty + row.rejected_qty:
				frappe.throw(f"Sent Qty not equal to Received Qty and Rejected Qty in row {frappe.bold(row.idx)}.")

	def on_submit(self):
		self.make_stock_entry()

	def before_save(self):
		self.item_duplicate_validation()

	def item_duplicate_validation(self):
		batches = []
		all = []
		for j in self.rm_item_details:
			all.append(j.batch)
		dup = [item for item, count in collections.Counter(all).items() if count > 1]

		for i in self.rm_item_details:
			batches.append(i.batch)
		if len(batches) != len(set(batches)):
			if len(dup) == 1:
				frappe.throw(f"Batch {dup[0]} Duplicated")
			if len(dup) > 1:
				frappe.throw(title="Following Batches are duplicated:",msg=dup,as_list=True)

	def make_stock_entry(self):
		ref_stock_entry = frappe.db.get_value("Stock Entry",{'rm_transfer_wh_to_village_wh':self.material_transfer_wh_to_wh,'docstatus':1},['name'])
		if not frappe.db.get_value("Stock Entry",{'outgoing_stock_entry':ref_stock_entry,'docstatus':1},['name']):
			doc = frappe.new_doc("Stock Entry")
			doc.company = self.company
			doc.stock_entry_type = self.stock_entry_type
			doc.outgoing_stock_entry = ref_stock_entry
			doc.me_rm_in = self.name
			# doc.material_transfer_wh_to_wh = self.material_transfer_wh_to_wh
			doc.from_warehouse = self.rm_warehouse
			doc.to_warehouse = self.wip_warehouse
			for row in self.rm_item_details:
				doc.append('items',{
					's_warehouse':self.rm_warehouse,
					't_warehouse':self.wip_warehouse,
					'item_code':row.item_code,
					'batch_no':row.batch,
					'uom':row.uom,
					'qty':row.qty,
					'basic_rate':frappe.db.get_value("Stock Entry Detail",{'parent':ref_stock_entry,'item_code':row.item_code,'batch_no':row.batch},["basic_rate"])
				})
			doc.save(ignore_permissions=True)
			doc.submit()

		rej_items = []
		rej_entry = frappe.new_doc("Stock Entry")
		rej_entry.company = self.company
		rej_entry.stock_entry_type = "Material Issue"
		rej_entry.me_rm_in = self.name
		rej_entry.from_warehouse = self.rm_warehouse
		for line in self.rm_item_details:
			if line.rejected_qty > 0:
				rej_items.append(line.item_code)
				rej_entry.append('items',{
					's_warehouse':self.rm_warehouse,
					'item_code':line.item_code,
					'batch_no':line.batch,
					'uom':line.uom,
					'qty':line.rejected_qty,
					'basic_rate':frappe.db.get_value("Stock Entry Detail",{'parent':ref_stock_entry,'item_code':line.item_code,'batch_no':line.batch},["basic_rate"])
				})
		if len(rej_items) != 0:
			rej_entry.save(ignore_permissions=True)
			rej_entry.submit()
		else:
			pass










