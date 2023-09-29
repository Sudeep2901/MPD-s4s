# Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class S4SPriceList(Document):
	def on_submit(self):
		if self.item_price_list:
			pl = frappe.new_doc("Price List")
			pl.price_list_name = self.price_list_name
			pl.currency = self.currency
			pl.buying = self.buying
			pl.save()
			for row in self.item_price_list:
				ip = frappe.new_doc("Item Price")
				ip.item_code = row.item_code
				ip.price_list = pl.name
				ip.buying = pl.buying
				ip.currency = pl.currency
				ip.price_list_rate = row.price_list_rate
				ip.save()