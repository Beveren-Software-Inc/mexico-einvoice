import frappe

@frappe.whitelist()
def filter_payment_form(doctype, txt, searchfield, page_len, start, filters):
    return frappe.db.sql("""select name, description from `tabPayment Form` where enable=1""")

@frappe.whitelist()
def filter_contract_type(doctype, txt, searchfield, page_len, start, filters):
    return frappe.db.sql("""select name, description from `tabContract Type` where enable=1""")

@frappe.whitelist()
def filter_regime_type(doctype, txt, searchfield, page_len, start, filters):
    return frappe.db.sql("""select name, description from `tabRegime Type` where enable=1""")

@frappe.whitelist()
def filter_payment_priodicity(doctype, txt, searchfield, page_len, start, filters):
    return frappe.db.sql("""select name, description from `tabPayment Periodicity` where enable=1""")