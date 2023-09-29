# Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
class SFGDataProcessing(Document):
	def after_insert(self):
		if self.rm_to_wip_stock_entry:
			# self.save()
			doc = frappe.get_doc("Stock Entry",self.rm_to_wip_stock_entry)
			doc.sfg_data_processing = self.name
			doc.save()
			
	@frappe.whitelist()
	def finish_batch(self):
		if self.item_code and self.bom:
			bom = frappe.get_doc("BOM",self.bom)
			item_doc = frappe.get_doc("Item",self.item_code)
			self.finish_batch_entry = []
			self.append("finish_batch_entry",{
				"date":frappe.utils.nowdate(),
				"sfg_product": item_doc.dcm_item_mapping[0].sfg_item,
				"uom":frappe.get_value("Item",item_doc.dcm_item_mapping[0].sfg_item,"stock_uom"),
				"qty":self.batch_qty/bom.items[0].qty,
				"finish_batch":1,
				"finish_for_qty":self.batch_qty/bom.items[0].qty
			})
	
	@frappe.whitelist()
	def on_save_btn(self,rm_to_wip_item):
		if self.item_code:
			item_doc = frappe.get_doc("Item",self.item_code)
			if item_doc.dcm_item_mapping and item_doc.dcm_item_mapping[0].wastage_item and item_doc.dcm_item_mapping[0].wip_item:
				raw_items = []
				wip_item = {
					"target_location":self.target_wip_location,
					"item_code":item_doc.dcm_item_mapping[0].wip_item,
					"qty":0.00,
					"uom":frappe.db.get_value("Item",item_doc.dcm_item_mapping[0].wip_item,"stock_uom"),
					"is_finished_item":1
				}
				wip_item_qty = 0.00
				wastage_items = []
				for row in rm_to_wip_item:
					if row["item_code"] == self.item_code:
						raw_items.append(row)
						wip_item_qty = wip_item_qty + row["qty"]
					elif row["item_code"] == item_doc.dcm_item_mapping[0].wastage_item:
						wastage_items.append(row)
						wip_item_qty = wip_item_qty - row["qty"]
					else:
						pass
				wip_item["qty"] = wip_item_qty
				
				stock_entry = frappe.new_doc("Stock Entry")
				stock_entry.company = self.company
				stock_entry.stock_entry_type = "Manufacture"
				stock_entry.set_posting_time = 1
				stock_entry.posting_date = self.date
				stock_entry.dcm_name = self.dcm_name
				stock_entry.from_warehouse = self.source_rm_location
				stock_entry.to_warehouse = self.target_wip_location
				
				for row in raw_items:
					stock_entry.append("items",{
						"s_warehouse":row["source_location"] if row["source_location"] else "",
						"item_code":row["item_code"] if row["item_code"] else "",
						"qty":row["qty"] if row["qty"] else 0,
						"uom":row["uom"],
						"batch_no":row["batch_no"] if row["batch_no"] else frappe.throw("Please Select Batch For Raw Items") 
					})
					
				stock_entry.append("items",{
					"item_code":wip_item["item_code"],
					"t_warehouse":wip_item["target_location"],
					"qty":wip_item["qty"],
					"uom":wip_item["uom"],
					"is_finished_item":wip_item["is_finished_item"]
				})
				
				for row in wastage_items:
					stock_entry.append("items",{
						"t_warehouse":row["target_location"] if row["target_location"] else "",
						"item_code":row["item_code"] if row["item_code"] else "",
						"qty":row["qty"] if row["qty"] else 0,
						"uom":row["uom"]
					})
				stock_entry.save()
				self.rm_to_wip_stock_entry = stock_entry.name
				# self.save()
	
	@frappe.whitelist()
	def on_submit_btn(self,rm_to_wip_item):
		if self.item_code and self.rm_to_wip_stock_entry:
			item_doc = frappe.get_doc("Item",self.item_code)
			if item_doc.dcm_item_mapping and item_doc.dcm_item_mapping[0].wastage_item and item_doc.dcm_item_mapping[0].wip_item:
				raw_items = []
				wip_item = {
					"target_location":self.target_wip_location,
					"item_code":item_doc.dcm_item_mapping[0].wip_item,
					"qty":0.00,
					"uom":frappe.db.get_value("Item",item_doc.dcm_item_mapping[0].wip_item,"stock_uom"),
					"is_finished_item":1
				}
				wip_item_qty = 0.00
				wastage_items = []
				for row in rm_to_wip_item:
					if row["item_code"] == self.item_code:
						raw_items.append(row)
						wip_item_qty = wip_item_qty + row["qty"]
					elif row["item_code"] == item_doc.dcm_item_mapping[0].wastage_item:
						wastage_items.append(row)
						wip_item_qty = wip_item_qty - row["qty"]
					else:
						pass
				wip_item["qty"] = wip_item_qty
				
				stock_entry = frappe.get_doc("Stock Entry",self.rm_to_wip_stock_entry)
				if stock_entry.docstatus!=1:
					stock_entry.stock_entry_type = "Manufacture"
					stock_entry.posting_date = self.date
					stock_entry.from_warehouse = self.source_rm_location
					stock_entry.to_warehouse = self.target_wip_location
					stock_entry.items = []
					for row in raw_items:
						stock_entry.append("items",{
							"s_warehouse":row["source_location"] if row["source_location"] else "",
							"item_code":row["item_code"] if row["item_code"] else "",
							"qty":row["qty"] if row["qty"] else 0,
							"uom":row["uom"],
							"batch_no":row["batch_no"] if row["batch_no"] else frappe.throw("Please Select Batch For Raw Items") 
						})
						
					stock_entry.append("items",{
						"item_code":wip_item["item_code"],
						"t_warehouse":wip_item["target_location"],
						"qty":wip_item["qty"],
						"uom":wip_item["uom"],
						"is_finished_item":wip_item["is_finished_item"]
					})
					
					for row in wastage_items:
						stock_entry.append("items",{
							"t_warehouse":row["target_location"] if row["target_location"] else "",
							"item_code":row["item_code"] if row["item_code"] else "",
							"qty":row["qty"] if row["qty"] else 0,
							"uom":row["uom"]
						})
					# stock_entry.insert()
					stock_entry.submit()
					for row in self.rm_to_wip_item:
						row.batch_no = frappe.get_value("Stock Entry Detail",{"parent":stock_entry.name,"item_code":row.item_code},"batch_no")
					self.se_submitted = 1
					for row in stock_entry.items:
						if row.item_code == item_doc.dcm_item_mapping[0].wip_item:
							batch_doc = frappe.get_doc("Batch",row.batch_no)
							self.batch_no = batch_doc.name
							self.batch_qty = batch_doc.batch_qty
							self.batch_qty_uom = batch_doc.stock_uom
							self.append("wip_to_sfg_item",{
								"date":frappe.utils.nowdate(),
								"sfg_product": item_doc.dcm_item_mapping[0].sfg_item,
								"uom":frappe.get_value("Item",item_doc.dcm_item_mapping[0].sfg_item,"stock_uom")
							})
					self.save()
				else:
					frappe.throw(self.rm_to_wip_stock_entry+" this stock entry already submitted")
		else:
			frappe.throw("Make Correct Entries")
			
	@frappe.whitelist()
	def fetch_rm_items(self):
		if self.item_code:
			item = frappe.get_doc("Item",self.item_code)
			if item.dcm_item_mapping[0] and item.dcm_item_mapping[0].wastage_item:
				self.rm_to_wip_item = []
				self.append("rm_to_wip_item",{
					"source_location" : self.source_rm_location,
	 				"item_code" : self.item_code,
	 				"uom" : item.stock_uom
				})
				self.append("rm_to_wip_item",{
	 				"item_code" : item.dcm_item_mapping[0].wastage_item,
	 				"target_location" : self.target_wip_location,
	 				"uom" : frappe.get_value("Item",item.dcm_item_mapping[0].wastage_item,"stock_uom")
				})
				self.wip_item = item.dcm_item_mapping[0].wip_item
				if item.dcm_item_mapping[0].sfg_bom:
					self.bom = item.dcm_item_mapping[0].sfg_bom
	
	@frappe.whitelist()
	def on_child_save(self,d):
		if self.bom:
			stock_entry = frappe.new_doc("Stock Entry")
			stock_entry.update({
				'company':self.company,
				'stock_entry_type': "Manufacture",
				'posting_date': d["date"],
				'sfg_data_processing':self.name,
				'dcm_name': self.dcm_name,
				'from_warehouse': self.source_wip_location,
				'to_warehouse': self.target_sfg_location,
				'from_bom': 1,
				'bom_no': self.bom,
				'fg_completed_qty': d["qty"] if not d["finish_batch"] else d["finish_for_qty"]
			})
			bom = frappe.get_doc("BOM",self.bom)
			stock_entry.items =[]
			for row in bom.items:
				stock_entry.append("items",{
					"s_warehouse":self.source_wip_location if self.source_wip_location else "",
					"item_code":row.item_code if row.item_code else "",
					"qty":d["qty"]*row.qty if not d["finish_batch"] else self.batch_qty,
					"uom":row.stock_uom,
					"batch_no":self.batch_no 
				})
			stock_entry.append("items",{
				"item_code":bom.item,
				"t_warehouse":self.target_sfg_location,
				"qty":d["qty"],
				"uom":d["uom"],
				"is_finished_item":1
			})
			stock_entry.append("me_weight_details",{
				"goni_no": "Goni No-1",
				"weight_in_kg": d["qty"],
				"moisture": d["moisture"] ,
				"colour": d["colour"],
				"flake_size":d["flake_size"],
				"quality":d["quality"],
				"overall":d["overall"]
			})
			stock_entry.save()
			return stock_entry.name
			
			
	@frappe.whitelist()
	def on_child_submit(self,d):
		if self.bom:
			stock_entry = frappe.get_doc("Stock Entry",d["stock_entry"])
			stock_entry.update({
				# 'stock_entry_type': "Manufacture",
				'company':self.company,
				'posting_date': d["date"],
				'sfg_data_processing':self.name,
				'dcm_name': self.dcm_name,
				'from_warehouse': self.source_wip_location,
				'to_warehouse': self.target_sfg_location,
				'from_bom': 1,
				'bom_no': self.bom,
				'fg_completed_qty':  d["qty"] if not d["finish_batch"] else d["finish_for_qty"]
			})
			bom = frappe.get_doc("BOM",self.bom)
			stock_entry.items =[]
			for row in bom.items:
				stock_entry.append("items",{
					"s_warehouse":self.source_wip_location if self.source_wip_location else "",
					"item_code":row.item_code if row.item_code else "",
					"qty":d["qty"]*row.qty if not d["finish_batch"] else self.batch_qty,
					"uom":row.stock_uom,
					"batch_no":self.batch_no 
				})
			stock_entry.append("items",{
				"item_code":bom.item,
				"t_warehouse":self.target_sfg_location,
				"qty":d["qty"],
				"uom":d["uom"],
				"is_finished_item":1
			})
			stock_entry.me_weight_details = []
			stock_entry.append("me_weight_details",{
				"goni_no": "Goni No-1",
				"weight_in_kg": d["qty"],
				"moisture": d["moisture"] ,
				"colour": d["colour"],
				"flake_size":d["flake_size"],
				"quality":d["quality"],
				"overall":d["overall"]
			})
			stock_entry.save()
			stock_entry.submit()
			batch_qty = frappe.get_value("Batch",self.batch_no,"batch_qty")
			result = {
				"se_submitted":1,
				"batch_qty":batch_qty,
				"batch_no":frappe.get_value("Stock Entry Detail",{"parent":stock_entry.name,"item_code":bom.item},"batch_no")
			}
			return result