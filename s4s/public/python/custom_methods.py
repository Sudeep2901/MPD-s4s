import json
from collections import OrderedDict, defaultdict
from itertools import groupby
from typing import Dict, List, Set
from frappe.desk.reportview import get_match_cond

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc, map_child_doc
from frappe.model.naming import set_naming_from_document_naming_rule
from frappe.utils import cint, floor, flt, today
from frappe.utils.nestedset import get_descendants_of

from erpnext.selling.doctype.sales_order.sales_order import (
    make_delivery_note as create_delivery_note_from_sales_order,
)
from erpnext.stock.get_item_details import get_conversion_factor


from frappe.utils import flt, nowdate
from functools import reduce
from erpnext.accounts.doctype.bank_account.bank_account import get_party_bank_account
from frappe import scrub

# TODO: Prioritize SO or WO group warehouse


class PickList(Document):
    def validate(self):
        self.validate_for_qty()

    def before_save(self):
        if not self.get_inventory_clicked:
            self.set_item_locations()

        # set percentage picked in SO
        for location in self.get("locations"):
            if (
                location.sales_order
                and frappe.db.get_value(
                    "Sales Order", location.sales_order, "per_picked"
                )
                == 100
            ):
                frappe.throw("Row " + str(location.idx) + " has been picked already!")

        if self.sales_order:
            for row in self.locations:
                if not row.sales_order:
                    row.sales_order = self.sales_order

    def before_submit(self):
        update_sales_orders = set()
        for item in self.locations:
            # if the user has not entered any picked qty, set it to stock_qty, before submit
            if item.picked_qty == 0:
                item.picked_qty = item.stock_qty

            if item.sales_order_item:
                # update the picked_qty in SO Item
                self.update_sales_order_item(item, item.picked_qty, item.item_code)
                update_sales_orders.add(item.sales_order)

            if not frappe.get_cached_value("Item", item.item_code, "has_serial_no"):
                continue
            if not item.serial_no:
                frappe.throw(
                    _(
                        "Row #{0}: {1} does not have any available serial numbers in {2}"
                    ).format(
                        frappe.bold(item.idx),
                        frappe.bold(item.item_code),
                        frappe.bold(item.warehouse),
                    ),
                    title=_("Serial Nos Required"),
                )
            if len(item.serial_no.split("\n")) == item.picked_qty:
                continue
            frappe.throw(
                _(
                    "For item {0} at row {1}, count of serial numbers does not match with the picked quantity"
                ).format(frappe.bold(item.item_code), frappe.bold(item.idx)),
                title=_("Quantity Mismatch"),
            )

        self.update_bundle_picked_qty()
        self.update_sales_order_picking_status(update_sales_orders)

    def before_cancel(self):
        """Deduct picked qty on cancelling pick list"""
        updated_sales_orders = set()

        for item in self.get("locations"):
            if item.sales_order_item:
                self.update_sales_order_item(item, -1 * item.picked_qty, item.item_code)
                updated_sales_orders.add(item.sales_order)

        self.update_bundle_picked_qty()
        self.update_sales_order_picking_status(updated_sales_orders)

    def update_sales_order_item(self, item, picked_qty, item_code):
        item_table = (
            "Sales Order Item" if not item.product_bundle_item else "Packed Item"
        )
        stock_qty_field = "stock_qty" if not item.product_bundle_item else "qty"

        already_picked, actual_qty = frappe.db.get_value(
            item_table,
            item.sales_order_item,
            ["picked_qty", stock_qty_field],
        )

        if self.docstatus == 1:
            if (((already_picked + picked_qty) / actual_qty) * 100) > (
                100
                + flt(
                    frappe.db.get_single_value(
                        "Stock Settings", "over_delivery_receipt_allowance"
                    )
                )
            ):
                frappe.throw(
                    _(
                        "You are picking more than required quantity for {}. Check if there is any other pick list created for {}"
                    ).format(item_code, item.sales_order)
                )

        frappe.db.set_value(
            item_table, item.sales_order_item, "picked_qty", already_picked + picked_qty
        )

    @staticmethod
    def update_sales_order_picking_status(sales_orders: Set[str]) -> None:
        for sales_order in sales_orders:
            if sales_order:
                frappe.get_doc("Sales Order", sales_order).update_picking_status()

    @frappe.whitelist()
    def set_item_locations(self, save=False):
        self.validate_for_qty()
        items = self.aggregate_item_qty()
        self.item_location_map = frappe._dict()

        from_warehouses = None
        if self.parent_warehouse:
            from_warehouses = get_descendants_of("Warehouse", self.parent_warehouse)

        # Create replica before resetting, to handle empty table on update after submit.
        locations_replica = self.get("locations")

        # reset
        self.delete_key("locations")
        for item_doc in items:
            item_code = item_doc.item_code

            self.item_location_map.setdefault(
                item_code,
                get_available_item_locations(
                    item_code,
                    from_warehouses,
                    self.item_count_map.get(item_code),
                    self.company,
                    wo=self.work_order,
                    purpose=self.purpose,
                    parent_wh=self.parent_warehouse,
                ),
            )

            locations = get_items_with_location_and_quantity(
                item_doc, self.item_location_map, self.docstatus
            )

            item_doc.idx = None
            item_doc.name = None

            for row in locations:
                location = item_doc.as_dict()
                location.update(row)
                self.append("locations", location)

        # If table is empty on update after submit, set stock_qty, picked_qty to 0 so that indicator is red
        # and give feedback to the user. This is to avoid empty Pick Lists.
        if not self.get("locations") and self.docstatus == 1:
            for location in locations_replica:
                location.stock_qty = 0
                location.picked_qty = 0
                self.append("locations", location)
            frappe.msgprint(
                _(
                    "Please Restock Items and Update the Pick List to continue. To discontinue, cancel the Pick List."
                ),
                title=_("Out of Stock"),
                indicator="red",
            )

        if save:
            self.save()

    def aggregate_item_qty(self):
        locations = self.get("locations")
        self.item_count_map = {}
        # aggregate qty for same item
        item_map = OrderedDict()
        for item in locations:
            if not item.item_code:
                frappe.throw("Row #{0}: Item Code is Mandatory".format(item.idx))
            item_code = item.item_code
            reference = item.sales_order_item or item.material_request_item
            key = (item_code, item.uom, item.warehouse, item.batch_no, reference)

            item.idx = None
            item.name = None

            if item_map.get(key):
                item_map[key].qty += item.qty
                item_map[key].stock_qty += flt(
                    item.stock_qty, item.precision("stock_qty")
                )
            else:
                item_map[key] = item

            # maintain count of each item (useful to limit get query)
            self.item_count_map.setdefault(item_code, 0)
            self.item_count_map[item_code] += flt(
                item.stock_qty, item.precision("stock_qty")
            )

        return item_map.values()

    def validate_for_qty(self):
        if self.purpose == "Material Transfer for Manufacture" and (
            self.for_qty is None or self.for_qty == 0
        ):
            frappe.throw(_("Qty of Finished Goods Item should be greater than 0."))

    def before_print(self, settings=None):
        self.group_similar_items()

    def group_similar_items(self):
        group_item_qty = defaultdict(float)
        group_picked_qty = defaultdict(float)

        for item in self.locations:
            group_item_qty[(item.item_code, item.warehouse)] += item.qty
            group_picked_qty[(item.item_code, item.warehouse)] += item.picked_qty

        duplicate_list = []
        for item in self.locations:
            if (item.item_code, item.warehouse) in group_item_qty:
                item.qty = group_item_qty[(item.item_code, item.warehouse)]
                item.picked_qty = group_picked_qty[(item.item_code, item.warehouse)]
                item.stock_qty = group_item_qty[(item.item_code, item.warehouse)]
                del group_item_qty[(item.item_code, item.warehouse)]
            else:
                duplicate_list.append(item)

        for item in duplicate_list:
            self.remove(item)

        for idx, item in enumerate(self.locations, start=1):
            item.idx = idx

    def update_bundle_picked_qty(self):
        product_bundles = self._get_product_bundles()
        product_bundle_qty_map = self._get_product_bundle_qty_map(
            product_bundles.values()
        )

        for so_row, item_code in product_bundles.items():
            picked_qty = self._compute_picked_qty_for_bundle(
                so_row, product_bundle_qty_map[item_code]
            )
            item_table = "Sales Order Item"
            already_picked = frappe.db.get_value(item_table, so_row, "picked_qty")
            frappe.db.set_value(
                item_table,
                so_row,
                "picked_qty",
                already_picked + (picked_qty * (1 if self.docstatus == 1 else -1)),
            )

    def _get_product_bundles(self) -> Dict[str, str]:
        # Dict[so_item_row: item_code]
        product_bundles = {}
        for item in self.locations:
            if not item.product_bundle_item:
                continue
            product_bundles[item.product_bundle_item] = frappe.db.get_value(
                "Sales Order Item",
                item.product_bundle_item,
                "item_code",
            )
        return product_bundles

    def _get_product_bundle_qty_map(
        self, bundles: List[str]
    ) -> Dict[str, Dict[str, float]]:
        # bundle_item_code: Dict[component, qty]
        product_bundle_qty_map = {}
        for bundle_item_code in bundles:
            bundle = frappe.get_last_doc(
                "Product Bundle", {"new_item_code": bundle_item_code}
            )
            product_bundle_qty_map[bundle_item_code] = {
                item.item_code: item.qty for item in bundle.items
            }
        return product_bundle_qty_map

    def _compute_picked_qty_for_bundle(self, bundle_row, bundle_items) -> int:
        """Compute how many full bundles can be created from picked items."""
        precision = frappe.get_precision("Stock Ledger Entry", "qty_after_transaction")

        possible_bundles = []
        for item in self.locations:
            if item.product_bundle_item != bundle_row:
                continue

            qty_in_bundle = bundle_items.get(item.item_code)
            if qty_in_bundle:
                possible_bundles.append(item.picked_qty / qty_in_bundle)
            else:
                possible_bundles.append(0)
        return int(flt(min(possible_bundles), precision or 6))


def validate_item_locations(pick_list):
    if not pick_list.locations:
        frappe.throw(_("Add items in the Item Locations table"))


def get_items_with_location_and_quantity(item_doc, item_location_map, docstatus):
    available_locations = item_location_map.get(item_doc.item_code)
    locations = []

    # if stock qty is zero on submitted entry, show positive remaining qty to recalculate in case of restock.
    remaining_stock_qty = (
        item_doc.qty
        if (docstatus == 1 and item_doc.stock_qty == 0)
        else item_doc.stock_qty
    )

    while remaining_stock_qty > 0 and available_locations:
        item_location = available_locations.pop(0)
        item_location = frappe._dict(item_location)

        stock_qty = (
            remaining_stock_qty
            if item_location.qty >= remaining_stock_qty
            else item_location.qty
        )
        qty = stock_qty / (item_doc.conversion_factor or 1)

        uom_must_be_whole_number = frappe.db.get_value(
            "UOM", item_doc.uom, "must_be_whole_number"
        )
        if uom_must_be_whole_number:
            qty = floor(qty)
            stock_qty = qty * item_doc.conversion_factor
            if not stock_qty:
                break

        serial_nos = None
        if item_location.serial_no:
            serial_nos = "\n".join(item_location.serial_no[0 : cint(stock_qty)])

        locations.append(
            frappe._dict(
                {
                    "qty": qty,
                    "stock_qty": stock_qty,
                    "warehouse": item_location.warehouse,
                    "serial_no": serial_nos,
                    "batch_no": item_location.batch_no,
                }
            )
        )

        remaining_stock_qty -= stock_qty

        qty_diff = item_location.qty - stock_qty
        # if extra quantity is available push current warehouse to available locations
        if qty_diff > 0:
            item_location.qty = qty_diff
            if item_location.serial_no:
                # set remaining serial numbers
                item_location.serial_no = item_location.serial_no[-int(qty_diff) :]
            available_locations = [item_location] + available_locations

    # update available locations for the item
    item_location_map[item_doc.item_code] = available_locations
    return locations


def get_available_item_locations(
    item_code,
    from_warehouses,
    required_qty,
    company,
    wo,
    purpose,
    parent_wh,
    ignore_validation=False,
):
    print(
        "+++++++++++++++++++++CUSTOM CLASS METHOD+++++++++++++++++++++++++++++++++", wo
    )

    # customisation when creating direct pick list
    if purpose == "Delivery":
        if parent_wh:
            from_warehouses = [parent_wh]

    # customisation when creating pick list from work order
    if wo:
        wrk_ord = frappe.get_doc("Work Order", wo)
        from_warehouses = [wrk_ord.source_warehouse]

    locations = []
    has_serial_no = frappe.get_cached_value("Item", item_code, "has_serial_no")
    has_batch_no = frappe.get_cached_value("Item", item_code, "has_batch_no")

    if has_batch_no and has_serial_no:
        locations = get_available_item_locations_for_serial_and_batched_item(
            item_code, from_warehouses, required_qty, company
        )
    elif has_serial_no:
        locations = get_available_item_locations_for_serialized_item(
            item_code, from_warehouses, required_qty, company
        )
    elif has_batch_no:
        locations = get_available_item_locations_for_batched_item(
            item_code, from_warehouses, required_qty, company
        )
    else:
        locations = get_available_item_locations_for_other_item(
            item_code, from_warehouses, required_qty, company
        )

    total_qty_available = sum(location.get("qty") for location in locations)

    remaining_qty = required_qty - total_qty_available

    if remaining_qty > 0 and not ignore_validation:
        frappe.msgprint(
            _("{0} units of Item {1} is not available.").format(
                remaining_qty, frappe.get_desk_link("Item", item_code)
            ),
            title=_("Insufficient Stock"),
        )

    return locations


def get_available_item_locations_for_serialized_item(
    item_code, from_warehouses, required_qty, company
):
    filters = frappe._dict(
        {"item_code": item_code, "company": company, "warehouse": ["!=", ""]}
    )

    if from_warehouses:
        filters.warehouse = ["in", from_warehouses]

    serial_nos = frappe.get_all(
        "Serial No",
        fields=["name", "warehouse"],
        filters=filters,
        limit=required_qty,
        order_by="purchase_date",
        as_list=1,
    )

    warehouse_serial_nos_map = frappe._dict()
    for serial_no, warehouse in serial_nos:
        warehouse_serial_nos_map.setdefault(warehouse, []).append(serial_no)

    locations = []
    for warehouse, serial_nos in warehouse_serial_nos_map.items():
        locations.append(
            {"qty": len(serial_nos), "warehouse": warehouse, "serial_no": serial_nos}
        )

    return locations


def get_available_item_locations_for_batched_item(
    item_code, from_warehouses, required_qty, company
):
    warehouse_condition = "and warehouse in %(warehouses)s" if from_warehouses else ""
    batch_locations = frappe.db.sql(
        """
		SELECT
			sle.`warehouse`,
			sle.`batch_no`,
			SUM(sle.`actual_qty`) AS `qty`
		FROM
			`tabStock Ledger Entry` sle, `tabBatch` batch
		WHERE
			sle.batch_no = batch.name
			and sle.`item_code`=%(item_code)s
			and sle.`company` = %(company)s
			and batch.disabled = 0
			and sle.is_cancelled=0
			and IFNULL(batch.`expiry_date`, '2200-01-01') > %(today)s
			{warehouse_condition}
		GROUP BY
			sle.`warehouse`,
			sle.`batch_no`,
			sle.`item_code`
		HAVING `qty` > 0
		ORDER BY IFNULL(batch.`expiry_date`, '2200-01-01'), batch.`creation`
	""".format(
            warehouse_condition=warehouse_condition
        ),
        {  # nosec
            "item_code": item_code,
            "company": company,
            "today": today(),
            "warehouses": from_warehouses,
        },
        as_dict=1,
    )

    return batch_locations


def get_available_item_locations_for_serial_and_batched_item(
    item_code, from_warehouses, required_qty, company
):
    # Get batch nos by FIFO
    locations = get_available_item_locations_for_batched_item(
        item_code, from_warehouses, required_qty, company
    )

    filters = frappe._dict(
        {
            "item_code": item_code,
            "company": company,
            "warehouse": ["!=", ""],
            "batch_no": "",
        }
    )

    # Get Serial Nos by FIFO for Batch No
    for location in locations:
        filters.batch_no = location.batch_no
        filters.warehouse = location.warehouse
        location.qty = (
            required_qty if location.qty > required_qty else location.qty
        )  # if extra qty in batch

        serial_nos = frappe.get_list(
            "Serial No",
            fields=["name"],
            filters=filters,
            limit=location.qty,
            order_by="purchase_date",
        )

        serial_nos = [sn.name for sn in serial_nos]
        location.serial_no = serial_nos

    return locations


def get_available_item_locations_for_other_item(
    item_code, from_warehouses, required_qty, company
):
    # gets all items available in different warehouses
    warehouses = [
        x.get("name")
        for x in frappe.get_list("Warehouse", {"company": company}, "name")
    ]

    filters = frappe._dict(
        {
            "item_code": item_code,
            "warehouse": ["in", warehouses],
            "actual_qty": [">", 0],
        }
    )

    if from_warehouses:
        filters.warehouse = ["in", from_warehouses]

    item_locations = frappe.get_all(
        "Bin",
        fields=["warehouse", "actual_qty as qty"],
        filters=filters,
        limit=required_qty,
        order_by="creation",
    )

    return item_locations


@frappe.whitelist()
def create_delivery_note(source_name, target_doc=None):
    print("IIIIIIIIIIIIII Custom Running")
    pick_list = frappe.get_doc("Pick List", source_name)
    validate_item_locations(pick_list)
    sales_dict = dict()
    sales_orders = []
    delivery_note = None
    for location in pick_list.locations:
        if location.sales_order:
            sales_orders.append(
                frappe.db.get_value(
                    "Sales Order",
                    location.sales_order,
                    ["customer", "name as sales_order"],
                    as_dict=True,
                )
            )

    for customer, rows in groupby(sales_orders, key=lambda so: so["customer"]):
        sales_dict[customer] = {row.sales_order for row in rows}

    if sales_dict:
        delivery_note = create_dn_with_so(sales_dict, pick_list)

    if not all(item.sales_order for item in pick_list.locations):
        delivery_note = create_dn_wo_so(pick_list)

    frappe.msgprint(_("Delivery Note(s) created for the Pick List"))
    return delivery_note


def create_dn_wo_so(pick_list):
    delivery_note = frappe.new_doc("Delivery Note")

    item_table_mapper_without_so = {
        "doctype": "Delivery Note Item",
        "field_map": {
            "rate": "rate",
            "name": "name",
            "parent": "",
        },
    }
    map_pl_locations(pick_list, item_table_mapper_without_so, delivery_note)
    print("delivery note assgj", delivery_note.as_dict())
    delivery_note.insert(ignore_mandatory=True)

    return delivery_note


def create_dn_with_so(sales_dict, pick_list):
    delivery_note = None

    item_table_mapper = {
        "doctype": "Delivery Note Item",
        "field_map": {
            "rate": "rate",
            "name": "so_detail",
            "parent": "against_sales_order",
        },
        "condition": lambda doc: abs(doc.delivered_qty) < abs(doc.qty)
        and doc.delivered_by_supplier != 1,
    }

    for customer in sales_dict:
        for so in sales_dict[customer]:
            delivery_note = None
            delivery_note = create_delivery_note_from_sales_order(
                so, delivery_note, skip_item_mapping=True
            )
            break
        if delivery_note:
            # map all items of all sales orders of that customer
            for so in sales_dict[customer]:
                map_pl_locations(pick_list, item_table_mapper, delivery_note, so)
            delivery_note.flags.ignore_mandatory = True
            if pick_list.get_inventory_clicked == 1:
                for i in delivery_note.items:
                    i.against_sales_order = pick_list.sales_order
                    i.so_detail = frappe.db.get_value(
                        "Sales Order Item", {"parent": pick_list.sales_order}, ["name"]
                    )
                delivery_note.title = delivery_note.customer
                delivery_note.cc_name = pick_list.cc_name
                delivery_note.po_no = frappe.db.get_value(
                    "Sales Order", {"name": pick_list.sales_order}, ["po_no"]
                )
                delivery_note.po_date = frappe.db.get_value(
                    "Sales Order", {"name": pick_list.sales_order}, ["po_date"]
                )

                delivery_note.flags.ignore_validate = True

            delivery_note.insert()
            update_packed_item_details(pick_list, delivery_note)
            delivery_note.save()

    return delivery_note


def map_pl_locations(pick_list, item_mapper, delivery_note, sales_order=None):
    for location in pick_list.locations:
        if location.sales_order != sales_order or location.product_bundle_item:
            continue

        if location.sales_order_item:
            sales_order_item = frappe.get_doc(
                "Sales Order Item", location.sales_order_item
            )
        else:
            sales_order_item = None

        source_doc = sales_order_item or location

        dn_item = map_child_doc(source_doc, delivery_note, item_mapper)

        if dn_item:
            dn_item.pick_list_item = location.name
            dn_item.warehouse = location.warehouse
            dn_item.qty = flt(location.picked_qty) / (
                flt(location.conversion_factor) or 1
            )
            dn_item.batch_no = location.batch_no
            dn_item.serial_no = location.serial_no

            update_delivery_note_item(source_doc, dn_item, delivery_note)

    add_product_bundles_to_delivery_note(pick_list, delivery_note, item_mapper)
    set_delivery_note_missing_values(delivery_note)

    delivery_note.pick_list = pick_list.name
    delivery_note.company = pick_list.company
    delivery_note.customer = frappe.get_value("Sales Order", sales_order, "customer")


def add_product_bundles_to_delivery_note(
    pick_list: "PickList", delivery_note, item_mapper
) -> None:
    """Add product bundles found in pick list to delivery note.

    When mapping pick list items, the bundle item itself isn't part of the
    locations. Dynamically fetch and add parent bundle item into DN."""
    product_bundles = pick_list._get_product_bundles()
    product_bundle_qty_map = pick_list._get_product_bundle_qty_map(
        product_bundles.values()
    )

    for so_row, item_code in product_bundles.items():
        sales_order_item = frappe.get_doc("Sales Order Item", so_row)
        dn_bundle_item = map_child_doc(sales_order_item, delivery_note, item_mapper)
        dn_bundle_item.qty = pick_list._compute_picked_qty_for_bundle(
            so_row, product_bundle_qty_map[item_code]
        )
        update_delivery_note_item(sales_order_item, dn_bundle_item, delivery_note)


def update_packed_item_details(pick_list: "PickList", delivery_note) -> None:
    """Update stock details on packed items table of delivery note."""

    def _find_so_row(packed_item):
        for item in delivery_note.items:
            if packed_item.parent_detail_docname == item.name:
                return item.so_detail

    def _find_pick_list_location(bundle_row, packed_item):
        if not bundle_row:
            return
        for loc in pick_list.locations:
            if (
                loc.product_bundle_item == bundle_row
                and loc.item_code == packed_item.item_code
            ):
                return loc

    for packed_item in delivery_note.packed_items:
        so_row = _find_so_row(packed_item)
        location = _find_pick_list_location(so_row, packed_item)
        if not location:
            continue
        packed_item.warehouse = location.warehouse
        packed_item.batch_no = location.batch_no
        packed_item.serial_no = location.serial_no


@frappe.whitelist()
def create_stock_entry(pick_list):
    pick_list = frappe.get_doc(json.loads(pick_list))
    validate_item_locations(pick_list)

    if stock_entry_exists(pick_list.get("name")):
        return frappe.msgprint(
            _("Stock Entry has been already created against this Pick List")
        )

    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.pick_list = pick_list.get("name")
    stock_entry.purpose = pick_list.get("purpose")
    stock_entry.set_stock_entry_type()

    if pick_list.get("work_order"):
        stock_entry = update_stock_entry_based_on_work_order(pick_list, stock_entry)
    elif pick_list.get("material_request"):
        stock_entry = update_stock_entry_based_on_material_request(
            pick_list, stock_entry
        )
    else:
        stock_entry = update_stock_entry_items_with_no_reference(pick_list, stock_entry)

    stock_entry.set_missing_values()

    return stock_entry.as_dict()


@frappe.whitelist()
def get_pending_work_orders(
    doctype, txt, searchfield, start, page_length, filters, as_dict
):
    return frappe.db.sql(
        """
		SELECT
			`name`, `company`, `planned_start_date`
		FROM
			`tabWork Order`
		WHERE
			`status` not in ('Completed', 'Stopped')
			AND `qty` > `material_transferred_for_manufacturing`
			AND `docstatus` = 1
			AND `company` = %(company)s
			AND `name` like %(txt)s
		ORDER BY
			if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999), name
		LIMIT
			%(start)s, %(page_length)s""",
        {
            "txt": "%%%s%%" % txt,
            "_txt": txt.replace("%", ""),
            "start": start,
            "page_length": frappe.utils.cint(page_length),
            "company": filters.get("company"),
        },
        as_dict=as_dict,
    )


@frappe.whitelist()
def target_document_exists(pick_list_name, purpose):
    if purpose == "Delivery":
        return frappe.db.exists("Delivery Note", {"pick_list": pick_list_name})

    return stock_entry_exists(pick_list_name)


@frappe.whitelist()
def get_item_details(item_code, uom=None):
    details = frappe.db.get_value("Item", item_code, ["stock_uom", "name"], as_dict=1)
    details.uom = uom or details.stock_uom
    if uom:
        details.update(get_conversion_factor(item_code, uom))

    return details


def update_delivery_note_item(source, target, delivery_note):
    cost_center = frappe.db.get_value("Project", delivery_note.project, "cost_center")
    if not cost_center:
        cost_center = get_cost_center(source.item_code, "Item", delivery_note.company)

    if not cost_center:
        cost_center = get_cost_center(
            source.item_group, "Item Group", delivery_note.company
        )

    target.cost_center = cost_center


def get_cost_center(for_item, from_doctype, company):
    """Returns Cost Center for Item or Item Group"""
    return frappe.db.get_value(
        "Item Default",
        fieldname=["buying_cost_center"],
        filters={"parent": for_item, "parenttype": from_doctype, "company": company},
    )


def set_delivery_note_missing_values(target):
    target.run_method("set_missing_values")
    target.run_method("set_po_nos")
    target.run_method("calculate_taxes_and_totals")


def stock_entry_exists(pick_list_name):
    return frappe.db.exists("Stock Entry", {"pick_list": pick_list_name})


def update_stock_entry_based_on_work_order(pick_list, stock_entry):
    work_order = frappe.get_doc("Work Order", pick_list.get("work_order"))

    stock_entry.work_order = work_order.name
    stock_entry.company = work_order.company
    stock_entry.from_bom = 1
    stock_entry.bom_no = work_order.bom_no
    stock_entry.use_multi_level_bom = work_order.use_multi_level_bom
    stock_entry.fg_completed_qty = pick_list.for_qty
    if work_order.bom_no:
        stock_entry.inspection_required = frappe.db.get_value(
            "BOM", work_order.bom_no, "inspection_required"
        )

    is_wip_warehouse_group = frappe.db.get_value(
        "Warehouse", work_order.wip_warehouse, "is_group"
    )
    if not (is_wip_warehouse_group and work_order.skip_transfer):
        wip_warehouse = work_order.wip_warehouse
    else:
        wip_warehouse = None
    stock_entry.to_warehouse = wip_warehouse

    stock_entry.project = work_order.project

    for location in pick_list.locations:
        item = frappe._dict()
        update_common_item_properties(item, location)
        item.t_warehouse = wip_warehouse

        stock_entry.append("items", item)

    return stock_entry


def update_stock_entry_based_on_material_request(pick_list, stock_entry):
    for location in pick_list.locations:
        target_warehouse = None
        if location.material_request_item:
            target_warehouse = frappe.get_value(
                "Material Request Item", location.material_request_item, "warehouse"
            )
        item = frappe._dict()
        update_common_item_properties(item, location)
        item.t_warehouse = target_warehouse
        stock_entry.append("items", item)

    return stock_entry


def update_stock_entry_items_with_no_reference(pick_list, stock_entry):
    for location in pick_list.locations:
        item = frappe._dict()
        update_common_item_properties(item, location)

        stock_entry.append("items", item)

    return stock_entry


def update_common_item_properties(item, location):
    item.item_code = location.item_code
    item.s_warehouse = location.warehouse
    item.qty = location.picked_qty * location.conversion_factor
    item.transfer_qty = location.picked_qty
    item.uom = location.uom
    item.conversion_factor = location.conversion_factor
    item.stock_uom = location.stock_uom
    item.material_request = location.material_request
    item.serial_no = location.serial_no
    item.batch_no = location.batch_no
    item.material_request_item = location.material_request_item


# method overriding work order standard method adding validation
@frappe.whitelist()
def before_naming(self, method):
    if self.production_plan:
        if frappe.db.get_value(
            "Work Order", {"production_plan": self.production_plan}, ["name"]
        ):
            frappe.throw(
                msg="Work Order already exists. Delete existing one to create new.",
                title="Already Exists",
            )


# method override for create pick list from sales order
@frappe.whitelist()
def create_pick_list(source_name, target_doc=None):
    from erpnext.stock.doctype.packed_item.packed_item import is_product_bundle

    def update_item_quantity(source, target, source_parent) -> None:
        picked_qty = flt(source.picked_qty) / (flt(source.conversion_factor) or 1)
        qty_to_be_picked = flt(source.qty) - max(picked_qty, flt(source.delivered_qty))

        target.qty = qty_to_be_picked
        target.stock_qty = qty_to_be_picked * flt(source.conversion_factor)

    def update_packed_item_qty(source, target, source_parent) -> None:
        qty = flt(source.qty)
        for item in source_parent.items:
            if source.parent_detail_docname == item.name:
                picked_qty = flt(item.picked_qty) / (flt(item.conversion_factor) or 1)
                pending_percent = (
                    item.qty - max(picked_qty, item.delivered_qty)
                ) / item.qty
                target.qty = target.stock_qty = qty * pending_percent
                return

    def should_pick_order_item(item) -> bool:
        return (
            abs(item.delivered_qty) < abs(item.qty)
            and item.delivered_by_supplier != 1
            and not is_product_bundle(item.item_code)
        )

    doc = get_mapped_doc(
        "Sales Order",
        source_name,
        {
            "Sales Order": {
                "doctype": "Pick List",
                "validation": {"docstatus": ["=", 1]},
            },
            "Sales Order Item": {
                "doctype": "Pick List Item",
                "field_map": {"parent": "sales_order", "name": "sales_order_item"},
                "postprocess": update_item_quantity,
                "condition": should_pick_order_item,
            },
            "Packed Item": {
                "doctype": "Pick List Item",
                "field_map": {
                    "parent": "sales_order",
                    "name": "sales_order_item",
                    "parent_detail_docname": "product_bundle_item",
                },
                "field_no_map": ["picked_qty"],
                "postprocess": update_packed_item_qty,
            },
        },
        target_doc,
    )

    so = frappe.get_doc("Sales Order", source_name)
    if so.set_warehouse:
        doc.parent_warehouse = so.set_warehouse
    doc.purpose = "Delivery"
    doc.set_item_locations()
    print(">>>>>>>>>>>>>>>>METHOD OVERRIDDEN SUCCESSFULLY<<<<<<<<<<<<<<<<<<<<<<<<<")
    return doc


########### batch qty updation in sfg dispatch request #################
import frappe
from frappe import _
from frappe.utils import cint, flt, getdate


@frappe.whitelist()
def execute(filters):
    filters = json.loads(filters)
    print("KKKKKKKKKKKK", filters)
    if not filters:
        filters = {}

    # if filters.from_date > filters.to_date:
    # 	frappe.throw(_("From Date must be before To Date"))

    float_precision = cint(frappe.db.get_default("float_precision")) or 3

    columns = get_columns(filters)
    item_map = get_item_details(filters)
    iwb_map = get_item_warehouse_batch_map(filters, float_precision)

    data = []
    for item in sorted(iwb_map):
        if not filters.get("item") or filters.get("item") == item:
            for wh in sorted(iwb_map[item]):
                for batch in sorted(iwb_map[item][wh]):
                    qty_dict = iwb_map[item][wh][batch]
                    if (
                        qty_dict.opening_qty
                        or qty_dict.in_qty
                        or qty_dict.out_qty
                        or qty_dict.bal_qty
                    ):
                        data.append(
                            [
                                item,
                                item_map[item]["item_name"],
                                item_map[item]["description"],
                                wh,
                                batch,
                                flt(qty_dict.opening_qty, float_precision),
                                flt(qty_dict.in_qty, float_precision),
                                flt(qty_dict.out_qty, float_precision),
                                flt(qty_dict.bal_qty, float_precision),
                                item_map[item]["stock_uom"],
                            ]
                        )
    if len(data) != 0:
        return data[0][8]


def get_columns(filters):
    """return columns based on filters"""

    columns = (
        [_("Item") + ":Link/Item:100"]
        + [_("Item Name") + "::150"]
        + [_("Description") + "::150"]
        + [_("Warehouse") + ":Link/Warehouse:100"]
        + [_("Batch") + ":Link/Batch:100"]
        + [_("Opening Qty") + ":Float:90"]
        + [_("In Qty") + ":Float:80"]
        + [_("Out Qty") + ":Float:80"]
        + [_("Balance Qty") + ":Float:90"]
        + [_("UOM") + "::90"]
    )

    return columns


def get_conditions(filters):
    conditions = ""
    if not filters.get("from_date"):
        frappe.throw(_("'From Date' is required"))

    if filters.get("to_date"):
        conditions += " and posting_date <= '%s'" % filters["to_date"]
    else:
        frappe.throw(_("'To Date' is required"))

    for field in ["item_code", "batch_no", "company"]:
        if filters.get(field):
            conditions += " and {0} = {1}".format(
                field, frappe.db.escape(filters.get(field))
            )

    if filters.get("warehouse"):
        warehouse_details = frappe.db.get_value(
            "Warehouse", filters.get("warehouse"), ["lft", "rgt"], as_dict=1
        )
        if warehouse_details:
            conditions += (
                " and exists (select name from `tabWarehouse` wh \
				where wh.lft >= %s and wh.rgt <= %s and sle.warehouse = wh.name)"
                % (warehouse_details.lft, warehouse_details.rgt)
            )

    return conditions


# get all details
def get_stock_ledger_entries(filters):
    conditions = get_conditions(filters)
    return frappe.db.sql(
        """
		select item_code, batch_no, warehouse, posting_date, sum(actual_qty) as actual_qty
		from `tabStock Ledger Entry` as sle
		where is_cancelled = 0 and docstatus < 2 and ifnull(batch_no, '') != '' %s
		group by voucher_no, batch_no, item_code, warehouse
		order by item_code, warehouse"""
        % conditions,
        as_dict=1,
    )


def get_item_warehouse_batch_map(filters, float_precision):
    sle = get_stock_ledger_entries(filters)
    iwb_map = {}

    from_date = getdate(filters["from_date"])
    to_date = getdate(filters["to_date"])

    for d in sle:
        iwb_map.setdefault(d.item_code, {}).setdefault(d.warehouse, {}).setdefault(
            d.batch_no,
            frappe._dict(
                {"opening_qty": 0.0, "in_qty": 0.0, "out_qty": 0.0, "bal_qty": 0.0}
            ),
        )
        qty_dict = iwb_map[d.item_code][d.warehouse][d.batch_no]
        if d.posting_date < from_date:
            qty_dict.opening_qty = flt(qty_dict.opening_qty, float_precision) + flt(
                d.actual_qty, float_precision
            )
        elif d.posting_date >= from_date and d.posting_date <= to_date:
            if flt(d.actual_qty) > 0:
                qty_dict.in_qty = flt(qty_dict.in_qty, float_precision) + flt(
                    d.actual_qty, float_precision
                )
            else:
                qty_dict.out_qty = flt(qty_dict.out_qty, float_precision) + abs(
                    flt(d.actual_qty, float_precision)
                )

        qty_dict.bal_qty = flt(qty_dict.bal_qty, float_precision) + flt(
            d.actual_qty, float_precision
        )

    return iwb_map


def get_item_details(filters):
    item_map = {}
    for d in frappe.db.sql(
        "select name, item_name, description, stock_uom from tabItem", as_dict=1
    ):
        item_map.setdefault(d.name, d)

    return item_map


#############################################################################################################


# Hide me code and me name in stock entry
@frappe.whitelist()
def check_roles():
    if frappe.session.user != "Administrator":
        usr = frappe.get_doc("User", {"email": frappe.session.user})
        lst = []
        perm_roles = ["CC User", "VLCC User", "System Manager"]
        for i in usr.roles:
            if i.role in perm_roles:
                lst.append(i.role)

        if len(lst) != 0:
            return "Yes"
        else:
            return "No"


# Map purchase invoice fields to payment entry
@frappe.whitelist()
def map_fields(dn):
    doc = frappe.get_doc("Purchase Invoice", dn)
    vlcc_name = ""
    cc_name = ""
    village = ""
    taluka = ""
    district = ""
    s4s_purchase = ""

    if doc.vlcc_name:
        vlcc_name = doc.vlcc_name
    if doc.cc_name:
        cc_name = doc.cc_name
    if doc.village:
        village = doc.village
    if doc.taluka:
        taluka = doc.taluka
    if doc.district:
        district = doc.district
    if doc.s4s_purchase:
        s4s_purchase = doc.s4s_purchase

    return {
        "vlcc_name": vlcc_name,
        "cc_name": cc_name,
        "village": village,
        "taluka": taluka,
        "district": district,
        "s4s_purchase": s4s_purchase,
    }


@frappe.whitelist()
def create_proforma_invoice(source_name, target_doc=None):
    so = frappe.get_doc("Sales Order", source_name)
    so_dict = so.as_dict()
    del so_dict["name"]
    del so_dict["creation"]
    del so_dict["modified"]
    del so_dict["modified_by"]
    del so_dict["naming_series"]
    del so_dict["owner"]
    so_dict.update(
        {"doctype": "Proforma Invoice", "docstatus": 0, "sales_order": so.name}
    )
    proforma_invoice = frappe.new_doc("Proforma Invoice")
    proforma_invoice.update(so_dict)
    return proforma_invoice


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_batch_no(doctype, txt, searchfield, start, page_len, filters):
    filters = json.loads(filters)
    doctype = "Batch"
    cond = ""
    if filters.get("posting_date"):
        cond = (
            "and (batch.expiry_date is null or batch.expiry_date >= %(posting_date)s)"
        )

    batch_nos = None
    args = {
        # "item_code": filters.get("item_code"),
        "warehouse": filters.get("warehouse"),
        "posting_date": filters.get("posting_date"),
        "txt": "%{0}%".format(txt),
        "start": start,
        "page_len": page_len,
    }

    having_clause = "having sum(sle.actual_qty) > 0"
    if filters.get("is_return"):
        having_clause = ""

    meta = frappe.get_meta(doctype, cached=True)
    searchfields = meta.get_search_fields()

    search_columns = ""
    search_cond = ""

    if searchfields:
        search_columns = ", " + ", ".join(searchfields)
        search_cond = " or " + " or ".join(
            [field + " like %(txt)s" for field in searchfields]
        )

    if args.get("warehouse"):
        searchfields = ["batch." + field for field in searchfields]
        if searchfields:
            search_columns = ", " + ", ".join(searchfields)
            search_cond = " or " + " or ".join(
                [field + " like %(txt)s" for field in searchfields]
            )

        batch_nos = frappe.db.sql(
            """select sle.batch_no, round(sum(sle.actual_qty),2) as qty, sle.stock_uom,
				concat('MFG-',batch.manufacturing_date), concat('EXP-',batch.expiry_date), sle.item_code
				{search_columns}
			from `tabStock Ledger Entry` sle
				INNER JOIN `tabBatch` batch on sle.batch_no = batch.name
			where
				batch.disabled = 0
				and sle.is_cancelled = 0
				and sle.warehouse = %(warehouse)s
				and (sle.batch_no like %(txt)s
				or batch.expiry_date like %(txt)s
				or batch.manufacturing_date like %(txt)s
				{search_cond})
				and batch.docstatus < 2
				{cond}
				{match_conditions}
			group by batch_no {having_clause}
			order by batch.expiry_date, sle.batch_no desc
			limit %(start)s, %(page_len)s""".format(
                search_columns=search_columns,
                cond=cond,
                match_conditions=get_match_cond(doctype),
                having_clause=having_clause,
                search_cond=search_cond,
            ),
            args,
            as_dict=1,
        )

        for i in batch_nos:
            batch = frappe.get_doc("Batch", i.get("batch_no"))
            if batch.reference_doctype == "Purchase Receipt":
                i.update(
                    {
                        "rate": frappe.db.get_value(
                            "Purchase Receipt Item",
                            {
                                "parent": batch.reference_name,
                                "item_code": i.get("item_code"),
                                "batch_no": i.get("batch_no"),
                            },
                            ["rate"],
                        )
                    }
                )
            if batch.reference_doctype == "Stock Reconciliation":
                i.update(
                    {
                        "rate": frappe.db.get_value(
                            "Stock Reconciliation Item",
                            {
                                "parent": batch.reference_name,
                                "item_code": i.get("item_code"),
                                "batch_no": i.get("batch_no"),
                            },
                            ["valuation_rate"],
                        )
                    }
                )

        return batch_nos
    else:
        return frappe.db.sql(
            """select name, concat('MFG-', manufacturing_date), concat('EXP-',expiry_date)
			{search_columns}
			from `tabBatch` batch
			where batch.disabled = 0
			and item = %(item_code)s
			and (name like %(txt)s
			or expiry_date like %(txt)s
			or manufacturing_date like %(txt)s
			{search_cond})
			and docstatus < 2
			{0}
			{match_conditions}

			order by expiry_date, name desc
			limit %(start)s, %(page_len)s""".format(
                cond,
                search_columns=search_columns,
                search_cond=search_cond,
                match_conditions=get_match_cond(doctype),
            ),
            args,
        )

@frappe.whitelist()
def hide_material_in(name):
    if frappe.db.get_value(
        "Stock Entry", {"outgoing_stock_entry": name, "docstatus": 1}, ["name"]
    ):
        return "Success"


def map_fields_in_dn(self, method):
    if self.pick_list:
        pl = frappe.get_doc("Pick List", self.pick_list)
        self.customer = pl.customer
        self.set_warehouse = pl.parent_warehouse
        self.title = pl.customer
        self.cc_name = pl.cc_name
        if pl.sales_order:
            so = frappe.get_doc("Sales Order", pl.sales_order)
            self.sales_order = so.name
            if so.po_no:
                self.po_no = so.po_no
            if so.po_date:
                self.po_date = so.po_date

    set_naming_from_document_naming_rule(self)


@frappe.whitelist()
def create_purchase_rect(source_name, target=None):
    frappe.clear_cache()
    setting = frappe.get_doc("S4S Inter Company Settings")
    dn = frappe.get_doc("Delivery Note", source_name)
    pr = frappe.new_doc("Purchase Receipt")

    dn_customer = frappe.db.get_value(
        "Customer", {"name": dn.customer}, ["customer_name"]
    )
    setting_suppliers = []
    pr_company = ""

    for row in setting.inter_company_details:
        if dn_customer == row.company:
            pr_company = row.company
            if row.supplier:
                setting_suppliers.append(row.supplier)
            if row.supplier2:
                setting_suppliers.append(row.supplier2)

    pr_supplier = ""

    if setting_suppliers:
        for i in setting_suppliers:
            if (
                frappe.db.get_value("Supplier", {"name": i}, ["supplier_name"])
                == dn.company
            ):
                pr_supplier = i

    pr.supplier = pr_supplier
    pr.company = pr_company
    pr.supplier_delivery_note = dn.name
    pr.supplier_dn_date = dn.posting_date

    if pr_supplier != "":
        sup_doc = frappe.get_doc("Supplier", pr_supplier)
        pr.supplier_type = sup_doc.supplier_group
    if pr_company != "":
        comp_doc = frappe.get_doc("Company", pr_company)
        pr.abbr = comp_doc.abbr

    dn_dict = dn.as_dict()
    fpo_po_no = dn_dict["po_no"]

    del dn_dict["naming_series"]
    del dn_dict["name"]
    del dn_dict["owner"]
    del dn_dict["creation"]
    del dn_dict["modified"]
    del dn_dict["modified_by"]
    del dn_dict["customer"]
    del dn_dict["company"]
    del dn_dict["docstatus"]
    del dn_dict["posting_date"]
    del dn_dict["posting_time"]
    del dn_dict["abbr"]
    del dn_dict["set_warehouse"]
    del dn_dict["taxes_and_charges"]
    del dn_dict["sales_team"]
    del dn_dict["taxes"]
    del dn_dict["other_charges_calculation"]
    del dn_dict["po_no"]
    del dn_dict["po_date"]

    items = [
        x.update(
            {
                "docstatus": 0,
                "batch_no": "",
                "expense_account": "",
                "warehouse": "",
                "cost_center": "",
            }
        )
        for x in dn_dict["items"]
    ]
    dn_dict.update({"items": items})

    if frappe.db.get_value(
        "FPO Purchase Order", {"name": fpo_po_no, "docstatus": ["!=", 2]}
    ):
        dn_dict.update({"fpo_purchase_order": fpo_po_no})

    pr.update(dn_dict)

    # map inter company warehouse
    pr_wh = None

    inter_com_wh_settings = frappe.get_doc("S4S Inter Company Warehouse Settings")
    for row in inter_com_wh_settings.s4s_inter_company_warehouse:
        if (
            row.company == dn.company
            and row.warehouse == dn.set_warehouse
            and row.company_1 == dn.customer_name
        ):
            pr_wh = row.warehouse_1

    if pr_wh:
        items_wh = [x.update({"warehouse": pr_wh}) for x in pr.as_dict()["items"]]

        pr.update({"set_warehouse": pr_wh, "items": items_wh})

    return pr


@frappe.whitelist()
def pur_rect_btn(dn_name):
    if frappe.session.user != "Administrator":
        msg = ""
        usr_role = ""
        if not frappe.db.get_value(
            "Purchase Receipt",
            {"supplier_delivery_note": dn_name, "docstatus": 1},
            ["name"],
        ):
            msg += "Success"

        roles = []
        usr = frappe.get_doc("User", frappe.session.user)
        for i in usr.roles:
            roles.append(i.role)
        if "S4S CC User" in roles:
            usr_role += "Success"

        return {"msg": msg, "role": usr_role}

    else:
        return {"msg": "Success", "role": "Success"}


def share_doc(self, method):
    cc_name = None
    if self.pick_list:
        pl = frappe.get_doc("Pick List", self.pick_list)
        if pl.cc_name:
            cc_name = pl.cc_name

    if cc_name:
        # users = frappe.db.get_list("User Permission", {"allow": "S4S CC List", "for_value": cc_name}, "user")
        users = frappe.db.sql(
            f"""select user from `tabUser Permission` where allow = "S4S CC List" and for_value = "{cc_name}" """,
            as_dict=1,
        )
        user = [
            x
            for x in users
            if frappe.db.get_value(
                "User Permission",
                {
                    "user": x.get("user"),
                    "allow": "Company",
                    "for_value": "Science For Society Techno Services Pvt Ltd",
                },
                ["name"],
            )
        ]

        if user:
            for i in user:
                if frappe.has_permission(
                    self.doctype, "read", user=i.user
                ) and not frappe.db.get_value(
                    "DocShare",
                    {
                        "user": i.user,
                        "share_doctype": self.doctype,
                        "share_name": self.name,
                    },
                ):
                    doct = {
                        "user": i.user,
                        "share_doctype": self.doctype,
                        "share_name": self.name,
                        "read": 1,
                        "write": 1,
                        "share": 1,
                        "submit": 0,
                        "everyone": 0,
                        "notify_by_email": 1,
                        "doctype": "DocShare",
                    }
                    frappe.get_doc(doct).insert(ignore_permissions=True)


@frappe.whitelist()
def create_share_doc(self, method):
    from datetime import datetime

    shared_doc = frappe.get_doc(self.share_doctype, self.share_name)
    if not frappe.db.get_value(
        "Shared Documents",
        {
            "document_type": self.share_doctype,
            "document_id": self.share_name,
            "user": self.user,
        },
    ):
        datetime_str = str(shared_doc.creation)
        datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")
        date_obj = datetime_obj.date()

        doc = frappe.new_doc("Shared Documents")
        doc.document_type = self.share_doctype
        if self.share_doctype == "Delivery Note":
            doc.company = shared_doc.company
            doc.warehouse = shared_doc.set_warehouse
            doc.cc_name = shared_doc.cc_name
        doc.document_id = self.share_name
        doc.user = self.user
        doc.creation_time = shared_doc.creation
        doc.document_creation_date = date_obj
        doc.save(ignore_permissions=True)


@frappe.whitelist()
def delete_share_doc(self, method):
    if frappe.db.get_value(
        "Shared Documents",
        {
            "document_type": self.share_doctype,
            "document_id": self.share_name,
            "user": self.user,
        },
        ["name"],
    ):
        doc = frappe.get_doc(
            "Shared Documents",
            {
                "document_type": self.share_doctype,
                "document_id": self.share_name,
                "user": self.user,
            },
        )
        doc.delete()


@frappe.whitelist()
def set_basic_rate_in_stock_entry(self, method):
    if self.sfg_dispatch_request1:
        if frappe.db.get_value(
            "Stock Entry",
            {
                "sfg_dispatch_request": self.sfg_dispatch_request1,
                "docstatus": 1,
                "add_to_transit": 1,
            },
            ["name"],
        ):
            se = frappe.get_doc(
                "Stock Entry",
                {
                    "sfg_dispatch_request": self.sfg_dispatch_request1,
                    "docstatus": 1,
                    "add_to_transit": 1,
                },
            )
            for row in self.items:
                for line in se.items:
                    if (
                        row.item_code == line.item_code
                        and row.batch_no == line.batch_no
                    ):
                        row.basic_rate = line.basic_rate

    if self.me_sfg_dispatch_note:
        if frappe.db.get_value(
            "Stock Entry",
            {
                "me_sfg_dispatch_note": self.me_sfg_dispatch_note,
                "docstatus": 1,
                "add_to_transit": 1,
            },
            ["name"],
        ):
            se = frappe.get_doc(
                "Stock Entry",
                {
                    "me_sfg_dispatch_note": self.me_sfg_dispatch_note,
                    "docstatus": 1,
                    "add_to_transit": 1,
                },
            )
            for row in self.items:
                for line in se.items:
                    if (
                        row.item_code == line.item_code
                        and row.batch_no == line.batch_no
                    ):
                        row.basic_rate = line.basic_rate

    if self.material_in:
        mat_in = frappe.get_doc("Material In", self.material_in)
        wh_to_wh = frappe.get_doc(
            "Material Transfer WH To WH", mat_in.material_transfer_wh_to_wh
        )
        st_en = frappe.get_doc(
            "Stock Entry",
            {
                "material_transfer_wh_to_wh": wh_to_wh.name,
                "docstatus": 1,
                "add_to_transit": 1,
            },
        )
        for row in self.items:
            for line in st_en.items:
                if row.item_code == line.item_code and row.batch_no == line.batch_no:
                    row.basic_rate = line.basic_rate

    if self.me_rm_in:
        mat_in = frappe.get_doc("ME RM In", self.me_rm_in)
        wh_to_wh = frappe.get_doc(
            "RM Transfer WH To Village WH", mat_in.material_transfer_wh_to_wh
        )
        st_en = frappe.get_doc(
            "Stock Entry",
            {
                "rm_transfer_wh_to_village_wh": wh_to_wh.name,
                "docstatus": 1,
                "add_to_transit": 1,
            },
        )
        for row in self.items:
            for line in st_en.items:
                if row.item_code == line.item_code and row.batch_no == line.batch_no:
                    row.basic_rate = line.basic_rate

    if self.rm_transfer_vlcc_to_cc:
        # doc = frappe.get_doc("RM Transfer VLCC To CC",self.rm_transfer_vlcc_to_cc)
        if self.outgoing_stock_entry:
            ste = frappe.get_doc("Stock Entry", self.outgoing_stock_entry)
            for i in self.items:
                for j in ste.items:
                    if i.item_code == j.item_code and i.batch_no == j.batch_no:
                        i.basic_rate = j.basic_rate


from erpnext.accounts.doctype.payment_entry.payment_entry import *


@frappe.whitelist()
def get_payment_entry(
    self,
    method,
    party_amount=None,
    bank_account=None,
    bank_amount=None,
    reference_date=None,
):
    dt = self.doctype
    dn = self.name
    reference_doc = None
    doc = frappe.get_doc(dt, dn)
    over_billing_allowance = frappe.db.get_single_value(
        "Accounts Settings", "over_billing_allowance"
    )
    if dt in ("Sales Order", "Purchase Order") and flt(doc.per_billed, 2) >= (
        100.0 + over_billing_allowance
    ):
        frappe.throw(_("Can only make payment against unbilled {0}").format(_(dt)))

    party_type = set_party_type(dt)
    party_account = set_party_account(dt, dn, doc, party_type)
    party_account_currency = set_party_account_currency(dt, party_account, doc)
    payment_type = set_payment_type(dt, doc)
    grand_total, outstanding_amount = set_grand_total_and_outstanding_amount(
        party_amount, dt, party_account_currency, doc
    )

    # bank or cash
    bank = get_bank_cash_account(doc, bank_account)

    paid_amount, received_amount = set_paid_amount_and_received_amount(
        dt,
        party_account_currency,
        bank,
        outstanding_amount,
        payment_type,
        bank_amount,
        doc,
    )

    reference_date = getdate(reference_date)
    (
        paid_amount,
        received_amount,
        discount_amount,
        valid_discounts,
    ) = apply_early_payment_discount(
        paid_amount, received_amount, doc, party_account_currency, reference_date
    )

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = payment_type
    pe.company = doc.company
    pe.cost_center = doc.get("cost_center")
    pe.posting_date = nowdate()
    pe.reference_date = reference_date
    pe.mode_of_payment = doc.get("mode_of_payment")
    pe.party_type = party_type
    pe.party = doc.get(scrub(party_type))
    pe.contact_person = doc.get("contact_person")
    pe.contact_email = doc.get("contact_email")
    pe.ensure_supplier_is_not_blocked()

    pe.paid_from = party_account if payment_type == "Receive" else bank.account
    pe.paid_to = party_account if payment_type == "Pay" else bank.account
    pe.paid_from_account_currency = (
        party_account_currency if payment_type == "Receive" else bank.account_currency
    )
    pe.paid_to_account_currency = (
        party_account_currency if payment_type == "Pay" else bank.account_currency
    )
    pe.paid_amount = paid_amount
    pe.received_amount = received_amount
    pe.letter_head = doc.get("letter_head")

    if dt in ["Purchase Order", "Sales Order", "Sales Invoice", "Purchase Invoice"]:
        pe.project = doc.get("project") or reduce(
            lambda prev, cur: prev or cur,
            [x.get("project") for x in doc.get("items")],
            None,
        )  # get first non-empty project from items

    if pe.party_type in ["Customer", "Supplier"]:
        bank_account = get_party_bank_account(pe.party_type, pe.party)
        pe.set("bank_account", bank_account)
        pe.set_bank_account_data()

    # only Purchase Invoice can be blocked individually
    if doc.doctype == "Purchase Invoice" and doc.invoice_is_blocked():
        frappe.msgprint(_("{0} is on hold till {1}").format(doc.name, doc.release_date))
    else:
        if doc.doctype in (
            "Sales Invoice",
            "Purchase Invoice",
            "Purchase Order",
            "Sales Order",
        ) and frappe.get_value(
            "Payment Terms Template",
            {"name": doc.payment_terms_template},
            "allocate_payment_based_on_payment_terms",
        ):
            for reference in get_reference_as_per_payment_terms(
                doc.payment_schedule,
                dt,
                dn,
                doc,
                grand_total,
                outstanding_amount,
                party_account_currency,
            ):
                pe.append("references", reference)
        else:
            if dt == "Dunning":
                pe.append(
                    "references",
                    {
                        "reference_doctype": "Sales Invoice",
                        "reference_name": doc.get("sales_invoice"),
                        "bill_no": doc.get("bill_no"),
                        "due_date": doc.get("due_date"),
                        "total_amount": doc.get("outstanding_amount"),
                        "outstanding_amount": doc.get("outstanding_amount"),
                        "allocated_amount": doc.get("outstanding_amount"),
                    },
                )
                pe.append(
                    "references",
                    {
                        "reference_doctype": dt,
                        "reference_name": dn,
                        "bill_no": doc.get("bill_no"),
                        "due_date": doc.get("due_date"),
                        "total_amount": doc.get("dunning_amount"),
                        "outstanding_amount": doc.get("dunning_amount"),
                        "allocated_amount": doc.get("dunning_amount"),
                    },
                )
            else:
                pe.append(
                    "references",
                    {
                        "reference_doctype": dt,
                        "reference_name": dn,
                        "bill_no": doc.get("bill_no"),
                        "due_date": doc.get("due_date"),
                        "total_amount": grand_total,
                        "outstanding_amount": outstanding_amount,
                        "allocated_amount": outstanding_amount,
                    },
                )

    pe.setup_party_account_field()
    pe.set_missing_values()

    if party_account and bank:
        if dt == "Employee Advance":
            reference_doc = doc
        pe.set_exchange_rate(ref_doc=reference_doc)
        pe.set_amounts()

        if discount_amount:
            base_total_discount_loss = 0
            if frappe.db.get_single_value(
                "Accounts Settings", "book_tax_discount_loss"
            ):
                base_total_discount_loss = split_early_payment_discount_loss(
                    pe, doc, valid_discounts
                )

            set_pending_discount_loss(
                pe,
                doc,
                discount_amount,
                base_total_discount_loss,
                party_account_currency,
            )

        pe.set_difference_amount()

    sp = frappe.get_doc("S4S Purchase", doc.s4s_purchase)

    pe.vlcc_name = sp.vlcc_name
    pe.cc_name = sp.cc_name
    pe.village = sp.village
    pe.taluka = sp.taluka
    pe.district = sp.district

    if doc.s4s_purchase:
        pe.s4s_purchase = doc.s4s_purchase

    pe.flags.ignore_validate = True
    pe.save(ignore_permissions=True)


@frappe.whitelist()
def set_company_filter_in_report():
    if frappe.db.get_value(
        "User Permission",
        {"allow": "Company", "user": frappe.session.user, "is_default": 1},
        ["for_value"],
    ):
        return frappe.db.get_value(
            "User Permission",
            {"allow": "Company", "user": frappe.session.user, "is_default": 1},
            ["for_value"],
        )


@frappe.whitelist()
def make_cc_mandatory():
    roles = []
    if frappe.session.user != "Administrator":
        user = frappe.get_doc("User", frappe.session.user)
        for i in user.roles:
            roles.append(i.role)

        if "FPO CC User" in roles:
            return "Success"

    else:
        return ""


@frappe.whitelist()
def make_cc_mandatory_in_so(self, method):
    if self.customer_name == "Science For Society Techno Services Pvt Ltd":
        self.meta.get_field("cc_name").update({"reqd": 1})
