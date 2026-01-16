import frappe
from frappe import _
from frappe.utils import flt

def validate_material_request_against_billed(doc, method=None):
    if doc.docstatus == 1 and doc.sales_order:
        billed_data = frappe.db.sql("""
            SELECT item_code, SUM(qty) as total_billed 
            FROM `tabSales Invoice Item` 
            WHERE sales_order = %s AND docstatus = 1 
            GROUP BY item_code
        """, (doc.sales_order,), as_dict=True)
        billed_map = {d.item_code: flt(d.total_billed) for d in billed_data}

        prev_mr_data = frappe.db.sql("""
            SELECT child.item_code, SUM(child.qty) as total_qty 
            FROM `tabMaterial Request` par 
            INNER JOIN `tabMaterial Request Item` child ON child.parent = par.name 
            WHERE par.sales_order = %s AND par.name != %s AND par.docstatus = 1 
            GROUP BY child.item_code
        """, (doc.sales_order, doc.name or "NEW"), as_dict=True)
        prev_qty_map = {d.item_code: flt(d.total_qty) for d in prev_mr_data}

        current_request_map = {}
        for item in doc.items:
            current_request_map[item.item_code] = current_request_map.get(item.item_code, 0) + flt(item.qty)

        errors = []
        for item_code, qty_now in current_request_map.items():
            total_billed = flt(billed_map.get(item_code, 0))
            total_prev_submitted = flt(prev_qty_map.get(item_code, 0))
            balance = total_billed - (total_prev_submitted + qty_now)

            if balance < -0.001:
                shortage = abs(balance)
                errors.append(
                    f"<li><b>الصنف: {item_code}</b><br>"
                    f"إجمالي المفوتر: {total_billed}, "
                    f"طلب سابق: {total_prev_submitted}, "
                    f"طلب حالي: {qty_now}, "
                    f"<b>العجز: {shortage}</b></li>"
                )

        if errors:
            frappe.throw(
                title=_("يوجد عجز في رصيد المفوتر"),
                msg=_("لا يمكن اعتماد طلب المواد لوجود عجز في رصيد المفوتر:<ul>{0}</ul>").format("".join(errors))
            )

def validate_payment_entry_supplier(doc, method=None):
    if doc.party_type == "Supplier":
        frappe.throw(_("عذراً، لا يُسمح باستخدام الموردين (Suppliers) في شاشة سند الدفع نهائياً، يرجى استخدام قيد اليومية."))

def validate_sales_invoice_qty_against_so(doc, method=None):
    for item in doc.items:
        if item.sales_order and item.so_detail:
            so_qty = frappe.db.get_value("Sales Order Item", item.so_detail, "qty") or 0
            billed_qty_history = frappe.db.sql("""
                SELECT SUM(qty) 
                FROM `tabSales Invoice Item` 
                WHERE so_detail = %s AND docstatus = 1 AND parent != %s
            """, (item.so_detail, doc.name))
            prev_billed_qty = flt(billed_qty_history[0][0]) if billed_qty_history else 0.0
            remaining_qty = so_qty - prev_billed_qty
            if flt(item.qty) > flt(remaining_qty) + 0.001:
                frappe.throw(
                    msg=_("خطأ في الصنف (Row #{0}): الكمية المدخلة ({1}) تتجاوز الكمية المتبقية في أمر البيع ({2}).").format(
                        item.idx, item.qty, remaining_qty
                    ),
                    title=_("تجاوز كمية أمر البيع")
                )
