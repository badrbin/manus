import frappe
from frappe.utils import flt

@frappe.whitelist()
def get_customer_gl_summary(customer=None):
    if not customer: customer = frappe.form_dict.get('customer')
    if not customer: return {}
    gl_aggregates = frappe.db.sql("""
        SELECT 
            SUM(CASE WHEN voucher_type = 'Sales Invoice' THEN debit - credit ELSE 0 END) as total_invoices,
            SUM(CASE WHEN voucher_type != 'Sales Invoice' THEN credit - debit ELSE 0 END) as total_payments,
            SUM(debit - credit) as balance
        FROM `tabGL Entry`
        WHERE party_type = 'Customer' AND party = %s AND is_cancelled = 0
    """, (customer), as_dict=True)
    gl_entries = frappe.db.sql("""
        SELECT posting_date, voucher_type, voucher_no, debit, credit, remarks
        FROM `tabGL Entry`
        WHERE party_type = 'Customer' AND party = %s AND is_cancelled = 0
        ORDER BY posting_date DESC, creation DESC
    """, (customer), as_dict=True)
    total_invoices = flt(gl_aggregates[0].total_invoices) if gl_aggregates and gl_aggregates[0] else 0.0
    total_payments = flt(gl_aggregates[0].total_payments) if gl_aggregates and gl_aggregates[0] else 0.0
    current_balance = flt(gl_aggregates[0].balance) if gl_aggregates and gl_aggregates[0] else 0.0
    return {"total_invoices": total_invoices, "total_payments": total_payments, "current_balance": current_balance, "gl_entries": gl_entries}

@frappe.whitelist()
def get_material_request_available_qty(material_request=None, current_doc=None):
    if not material_request: material_request = frappe.form_dict.get('material_request')
    if not current_doc: current_doc = frappe.form_dict.get('current_doc')
    if not material_request: return {}
    mr_items = frappe.get_all("Material Request Item", filters={"parent": material_request, "parenttype": "Material Request"}, fields=["item_code", "qty"], ignore_permissions=True)
    qty_map = {}
    for item in mr_items: qty_map[item.item_code] = qty_map.get(item.item_code, 0) + item.qty
    other_installations = frappe.get_all("Installation Note", filters={"custom_material_request": material_request, "docstatus": 1, "name": ["!=", current_doc]}, pluck="name")
    if other_installations:
        used_items = frappe.get_all("Installation Note Item", filters={"parent": ["in", other_installations]}, fields=["item_code", "qty"])
        for item in used_items:
            if item.item_code in qty_map: qty_map[item.item_code] = qty_map[item.item_code] - item.qty
    return qty_map

@frappe.whitelist()
def get_sales_order_summary(sales_order=None):
    if not sales_order: sales_order = frappe.form_dict.get('sales_order')
    if not sales_order: return []
    summary_data = {}
    so_items = frappe.db.sql("""
        SELECT so_item.name as so_detail, so_item.item_code, so_item.item_name, so_item.qty, so_item.delivered_qty,
            IFNULL((SELECT SUM(sii.qty) FROM `tabSales Invoice Item` sii WHERE sii.so_detail = so_item.name AND sii.docstatus = 1), 0) as billed_actual_qty
        FROM `tabSales Order Item` so_item WHERE so_item.parent = %s
    """, (sales_order), as_dict=1)
    for item in so_items:
        if item.item_code in summary_data:
            summary_data[item.item_code]['so_qty'] += item.qty
            summary_data[item.item_code]['delivered_qty'] += item.delivered_qty
            summary_data[item.item_code]['billed_qty'] += item.billed_actual_qty
            summary_data[item.item_code]['balance'] += item.qty
        else:
            summary_data[item.item_code] = {"item_code": item.item_code, "item_name": item.item_name, "so_qty": item.qty, "delivered_qty": item.delivered_qty, "billed_qty": item.billed_actual_qty, "mr_qty": 0.0, "installed_qty": 0.0, "balance": item.qty, "is_extra": False}
    related_mrs = frappe.get_all("Material Request", filters={"sales_order": sales_order, "docstatus": 1}, pluck="name", ignore_permissions=True)
    if related_mrs:
        mr_items = frappe.get_all("Material Request Item", filters={"parent": ["in", related_mrs]}, fields=["item_code", "item_name", "qty"], ignore_permissions=True)
        for row in mr_items:
            if row.item_code in summary_data:
                summary_data[row.item_code]['mr_qty'] += row.qty
                summary_data[row.item_code]['balance'] = summary_data[row.item_code]['so_qty'] - summary_data[row.item_code]['mr_qty']
            else:
                summary_data[row.item_code] = {"item_code": row.item_code, "item_name": row.item_name, "so_qty": 0.0, "delivered_qty": 0.0, "billed_qty": 0.0, "mr_qty": row.qty, "installed_qty": 0.0, "balance": 0.0 - row.qty, "is_extra": True}
    inst_items = frappe.db.sql("""
        SELECT child.item_code, child.qty FROM `tabInstallation Note Item` child INNER JOIN `tabInstallation Note` parent ON child.parent = parent.name WHERE parent.docstatus = 1 AND parent.custom_sales_order = %s
    """, (sales_order), as_dict=1)
    for row in inst_items:
        if row.item_code in summary_data: summary_data[row.item_code]['installed_qty'] += row.qty
        else: summary_data[row.item_code] = {"item_code": row.item_code, "item_name": row.item_code, "so_qty": 0.0, "delivered_qty": 0.0, "billed_qty": 0.0, "mr_qty": 0.0, "installed_qty": row.qty, "balance": 0.0, "is_extra": True}
    return list(summary_data.values())

@frappe.whitelist()
def get_sales_order_item_codes(sales_order=None):
    if not sales_order: sales_order = frappe.form_dict.get('sales_order')
    if not sales_order: return []
    return frappe.get_all("Sales Order Item", filters={"parent": sales_order}, pluck="item_code", ignore_permissions=True)

@frappe.whitelist()
def get_stock_entries_by_mr(mr_name=None):
    if not mr_name: mr_name = frappe.form_dict.get("mr_name")
    if not mr_name: return {"entries": [], "items": []}
    entries = frappe.get_all("Stock Entry", filters={"custom_material_request": mr_name, "docstatus": ["<", 2]}, fields=["name", "stock_entry_type", "posting_date", "docstatus"], order_by="creation desc")
    if not entries: return {"entries": [], "items": []}
    se_names = [d.name for d in entries]
    items = frappe.get_all("Stock Entry Detail", filters={"parent": ["in", se_names]}, fields=["parent", "item_code", "qty", "uom", "s_warehouse", "t_warehouse"])
    return {"entries": entries, "items": items}

@frappe.whitelist()
def get_supplier_gl_summary(supplier=None):
    if not supplier: supplier = frappe.form_dict.get('supplier')
    if not supplier: return {}
    gl_aggregates = frappe.db.sql("""
        SELECT SUM(credit) as total_invoices, SUM(debit) as total_payments, SUM(credit - debit) as balance
        FROM `tabGL Entry`
        WHERE party_type = 'Supplier' AND party = %s AND is_cancelled = 0
    """, (supplier), as_dict=True)
    gl_entries = frappe.db.sql("""
        SELECT posting_date, voucher_type, voucher_no, debit, credit, remarks
        FROM `tabGL Entry`
        WHERE party_type = 'Supplier' AND party = %s AND is_cancelled = 0
        ORDER BY posting_date DESC, creation DESC
    """, (supplier), as_dict=True)
    total_invoices = flt(gl_aggregates[0].total_invoices) if gl_aggregates else 0.0
    total_payments = flt(gl_aggregates[0].total_payments) if gl_aggregates else 0.0
    current_balance = flt(gl_aggregates[0].balance) if gl_aggregates else 0.0
    return {"total_invoices": total_invoices, "total_payments": total_payments, "current_balance": current_balance, "gl_entries": gl_entries}
