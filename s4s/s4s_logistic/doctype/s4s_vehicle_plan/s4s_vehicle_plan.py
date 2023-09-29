# Copyright (c) 2022, Mannlowe Information Service Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _, msgprint


class S4SVehiclePlan(Document):
    @frappe.whitelist()
    def get_farm_pickups(self):
        conditions = ""
        if self.cc_name:
            conditions += f" AND fq.cc_name = '{self.cc_name}' "
        if self.vlcc_name:
            conditions += f" AND fq.vlcc_name = '{self.vlcc_name}' "

        data = frappe.db.sql(
            """
				SELECT
					fq.name as transaction_id,
					fq.delivery_location as pickup_location,
					fq.item_code as item_code,
					fq.tentative_qty as qty,
					fq.cc_name as cc_name,
					fq.vlcc_name as vlcc_name
				FROM
					`tabS4S Farmer Query` fq
				WHERE
					fq.delivery_location = "Farm Pick up" AND
					fq.pickup_request = "Arrange Vehicle" AND
					fq.date = '{0}' AND
					fq.company = '{1}'
					{2}
				ORDER BY
					fq.vlcc_name
			""".format(
                self.date, self.company, conditions
            ),
            as_dict=1,
        )
        if data:
            for i in data:
                if not frappe.db.exists(
                    {
                        "doctype": "S4S Vehicle Assignment for Farmer Query",
                        "transaction_id": i["transaction_id"],
                        "docstatus": 1,
                    }
                ):
                    if len(self.get("farm_pickups")):
                        if any(
                            d.transaction_id == i["transaction_id"]
                            for d in self.farm_pickups
                        ):
                            pass
                        else:
                            self.append(
                                "farm_pickups",
                                {
                                    "transaction_id": i["transaction_id"],
                                    "pickup_location": i["pickup_location"],
                                    "item_code": i["item_code"],
                                    "qty": i["qty"],
                                    "cc_name": i["cc_name"],
                                    "vlcc_name": i["vlcc_name"],
                                },
                            )
                    else:
                        self.append(
                            "farm_pickups",
                            {
                                "transaction_id": i["transaction_id"],
                                "pickup_location": i["pickup_location"],
                                "item_code": i["item_code"],
                                "qty": i["qty"],
                                "cc_name": i["cc_name"],
                                "vlcc_name": i["vlcc_name"],
                            },
                        )
                else:
                    pass
        else:
            frappe.msgprint(_("No any Farm Pick Ups on {0}").format(self.date))

    @frappe.whitelist()
    def get_purchase_transactions(self):
        if not self.company:
            frappe.throw("Please Enter Company!")

        conditions = ""
        if self.cc_name:
            conditions += f" AND p.cc_name = '{self.cc_name}' "
        if self.vlcc_name:
            conditions += f" AND p.vlcc_name = '{self.vlcc_name}' "

        data = frappe.db.sql(
            """
				SELECT
					p.name as transaction_id,
					p.delivery_location as pickup_location,
					pr.item_code as item_code,
					p.weight_after_kadta as qty,
					p.cc_name  as cc_name,
					p.vlcc_name as vlcc_name
				FROM
					`tabS4S Purchase receipt` pr
				JOIN 
					`tabS4S Purchase` p ON pr.parent = p.name
				WHERE
					p.docstatus = 1 AND
					p.delivery_location = "At VLCC" AND
					p.transaction_date = '{0}' AND
					p.company = '{1}'
					{2}
				ORDER BY
					p.vlcc_name
			""".format(
                self.date, self.company, conditions
            ),
            as_dict=1,
        )
        if data:
            for i in data:
                if not frappe.db.exists(
                    {
                        "doctype": "S4S Vehicle Assignment",
                        "transaction_id": i["transaction_id"],
                        "docstatus": 1,
                    }
                ):
                    if len(self.get("vehicle_assignment")) != 0:
                        if any(
                            d.transaction_id == i["transaction_id"]
                            for d in self.vehicle_assignment
                        ):
                            pass
                        else:
                            self.append(
                                "vehicle_assignment",
                                {
                                    "transaction_id": i["transaction_id"],
                                    "pickup_location": i["pickup_location"],
                                    "item_code": i["item_code"],
                                    "qty": i["qty"],
                                    "cc_name": i["cc_name"],
                                    "vlcc_name": i["vlcc_name"],
                                },
                            )
                    else:
                        self.append(
                            "vehicle_assignment",
                            {
                                "transaction_id": i["transaction_id"],
                                "pickup_location": i["pickup_location"],
                                "item_code": i["item_code"],
                                "qty": i["qty"],
                                "cc_name": i["cc_name"],
                                "vlcc_name": i["vlcc_name"],
                            },
                        )
                else:
                    pass
        else:
            self.vehicle_assignment = []
            frappe.msgprint(_("No any VLCC Transactions on {0}").format(self.date))

    @frappe.whitelist()
    def before_save(self):
        if len(self.get("vehicle_assignment")) != 0:
            for row in self.get("vehicle_assignment"):
                if row.transaction_id and row.assigned == "Yes":
                    s4s_purchase = frappe.get_doc("S4S Purchase", row.transaction_id)
                    s4s_purchase.vehicle_no = row.vehicle_no if row.vehicle_no else ""
                    s4s_purchase.vehicle_model = (
                        row.vehicle_model if row.vehicle_model else ""
                    )
                    s4s_purchase.driver_name = (
                        row.driver_name if row.driver_name else ""
                    )
                    s4s_purchase.driver_mobile_number = (
                        row.driver_mobile_number if row.driver_mobile_number else ""
                    )
                    s4s_purchase.assigned_vehicle = (
                        row.assigned if row.assigned else "No"
                    )
                    s4s_purchase.save()
                if row.transaction_id and row.assigned == "No" or not row.assigned:
                    s4s_purchase = frappe.get_doc("S4S Purchase", row.transaction_id)
                    s4s_purchase.vehicle_no = ""
                    s4s_purchase.vehicle_model = ""
                    s4s_purchase.driver_name = ""
                    s4s_purchase.driver_mobile_number = ""
                    s4s_purchase.assigned_vehicle = "No"
                    s4s_purchase.save()

        if len(self.get("farm_pickups")) != 0:
            for row in self.get("farm_pickups"):
                if row.transaction_id and row.assigned == "Yes":
                    s4s_purchase = frappe.get_doc(
                        "S4S Farmer Query", row.transaction_id
                    )
                    s4s_purchase.vehicle_no = row.vehicle_no if row.vehicle_no else ""
                    s4s_purchase.vehicle_model = (
                        row.vehicle_model if row.vehicle_model else ""
                    )
                    s4s_purchase.driver_name = (
                        row.driver_name if row.driver_name else ""
                    )
                    s4s_purchase.driver_mobile_number = (
                        row.driver_mobile_number if row.driver_mobile_number else ""
                    )
                    s4s_purchase.assigned_vehicle = (
                        row.assigned if row.assigned else "No"
                    )
                    s4s_purchase.save()
                if row.transaction_id and row.assigned == "No" or not row.assigned:
                    s4s_purchase = frappe.get_doc(
                        "S4S Farmer Query", row.transaction_id
                    )
                    s4s_purchase.vehicle_no = ""
                    s4s_purchase.vehicle_model = ""
                    s4s_purchase.driver_name = ""
                    s4s_purchase.driver_mobile_number = ""
                    s4s_purchase.assigned_vehicle = "No"
                    s4s_purchase.save()

    def validate(self):
        self.validate_vehicle()

    def validate_vehicle(self):
        for row in self.vehicle_assignment:
            if row.assigned == "Yes" and not row.vehicle_no:
                frappe.throw(
                    f"Please select vehicle for assignment in Vehicle Assignment row {frappe.bold(row.idx)}."
                )

        for row in self.farm_pickups:
            if row.assigned == "Yes" and not row.vehicle_no:
                frappe.throw(
                    f"Please select vehicle for assignment in Farm Pickups in row {frappe.bold(row.idx)}."
                )
