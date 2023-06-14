import frappe

@frappe.whitelist()
def filter_payment_form(doctype, txt, searchfield, page_len, start, filters):
    return frappe.db.sql("""select name, description from `tabPayment Form` where enable=1""")

