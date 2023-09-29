# Copyright (c) 2023, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate
import pandas as pd
import datetime


def execute(filters=None):
	columns = get_columns(filters)
	conditions = get_conditions(filters)

	data = get_data(conditions, filters)
	if not data:
		return [], [], None, []

	return columns, data 


def get_conditions(filters):
	conditions = ""
	if filters.get("item_code"):
		conditions += " and ip.item_code = %(item_code)s"
	if filters.get("price_list"):
		conditions += " and ip.price_list = %(price_list)s"
	if filters.get("type"):
		conditions += " and ip.buying = 1" if filters.get("type") == "Buying" else " and ip.selling = 1"
      
	return conditions

def get_data(conditions, filters):
		
	data = frappe.db.sql(
		"""
		SELECT
			ip.item_code as item_code,
			ip.item_name as item_name,
			ip.price_list as price_list,
			ip.price_list_rate as rate

		FROM
			`tabItem Price` ip

		WHERE
			ip.name !=""
			{0}
			
	""".format(
			conditions
		),
		filters,
		as_dict=1,
	)
	return data

def get_columns(filters):
	columns = [
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 160,
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": "Price List",
			"fieldname": "price_list",
			"fieldtype": "Link",
			"options": "Price List",
			"width": 160
		},
  		{
			"label": _("Rate"),
			"fieldname": "rate",
			"fieldtype": "Currency",
			"width": 160
		}
	]

	

	return columns
	
