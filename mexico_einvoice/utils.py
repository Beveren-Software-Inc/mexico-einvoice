import json
import frappe
import requests
from frappe import _

@frappe.whitelist()
def download_invoice():
    url = "https://www.facturapi.io/v2/invoices/644ec19dd54135c25a27ac99/pdf"
    headers = {
        "Authorization": "Bearer sk_test_eaGqR1xJyLow7NABEyvm24vwXzn26P4KdmWvQrpZ3Y",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    return response.content
 
def e_invoice_setting():
    e_invoice_setting = frappe.get_doc("E Invoice Setting", 'E Invoice Setting')
    return e_invoice_setting

def generate_einvoice(doc, method):
    invoice_setting = e_invoice_setting()
    url = "https://www.facturapi.io/v2/invoices"
    header = {
        "Authorization": "Bearer {}".format(
            invoice_setting.get_password(fieldname="secret_key", raise_exception=False)
        ),
        "Content-Type": "application/json"
    }
    customer = get_customer_details(doc)
    data = {
        "customer": customer,
        "items": [{
            "quantity": 1,
            "product": {
                "description": "Toast", #reqd
                "product_key": "60131324", #reqd
                "price": 420 #reqd
            }
        }],
        "use": "G01",
        "payment_form": "28"  # Tarjeta de crédito
    }
    response = requests.post(url, headers=header, data=json.dumps(data))

    if response.status_code == 200:
        response = response.json()
        frappe.log_error("response", response)
        doc.e_invoice_id = response.get('id'),
        doc.uuid = response.get('uuid'),
        doc.sat_signature = response.get('sat_signature'),
        doc.signature = response.get('stamp').get('signature'),
        doc.invoice_status = response.get('status'),
        doc.sat_cert_number = response.get('stamp').get('sat_cert_number'),
        doc.cfdi_version = response.get('cfdi_version'),
        doc.verification_url = response.get('verification_url')


def get_customer_details(doc):
    customer_name, tax_id, tax_system = frappe.db.get_value('Customer', doc.customer, ['customer_name', 'tax_id', 'tax_system'])

    # query = f""" select email_id, pincode from `tabAddress` where name = "{doc.customer_address}" """
    # address_ = frappe.db.sql(query, as_dict=1)

    customer = {
        "legal_name": customer_name, #reqd
        "email": "test@example.com",
        "tax_id": tax_id, #reqd
        "tax_system": tax_system, #reqd
        "address": { #reqd
            "zip": "85900"
        }
    }
    return customer