# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class S4SSFGPriceList(Document):
	def validate(self):
		print("hello"*100)
		cluster = frappe.db.get_list('S4S Cluster', pluck='name')
		for clust in cluster:
			count = 0
			for row in self.item_price_list:
				if clust == row.cluster:
					count=count+1
			if count>1:
				frappe.throw(clust+" cluster entry is duplicated...")

		
		if self.active == 1:
			error_count = 0
			clusters = []
			for row in self.item_price_list:
				table_doc = frappe.db.get_list("SFG Processing Price",filters={'cluster':row.cluster,'parent':['!=',self.name]},fields=['parent'])
				if table_doc:
					for i in table_doc:
						doc = frappe.get_doc("S4S SFG Price List",i.get('parent'))
						if doc.active == 1:
							error_count += 1
							clusters.append(row.cluster)
			
			if error_count > 0:
				if len(clusters) == 1:
					frappe.throw(f"Already Active S4S SFG Price List for Cluster {frappe.bold(clusters[0])}")

				else:
					frappe.throw(title="Already Active S4S SFG Price List for Clusters:",as_list=1,msg=[clusters])
						


		
