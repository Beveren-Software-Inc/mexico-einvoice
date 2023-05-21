import json
import frappe
import requests
from frappe import _
import re


@frappe.whitelist()
def get_token():
    e_invoice_setting = frappe.get_doc("E Invoice Setting", 'E Invoice Setting')
    token = e_invoice_setting.get_password(fieldname="secret_key", raise_exception=False)
    return token

def generate_einvoice(doc, method):
    e_invoice_setting = frappe.get_doc("E Invoice Setting", 'E Invoice Setting')
    if e_invoice_setting.generate_e_invoice:
        token = get_token()
        url = "https://www.facturapi.io/v2/invoices"
        header = {
            "Authorization": "Bearer {}".format(token),
            "Content-Type": "application/json"
        }
        customer = get_customer_details(doc)
        items = get_items(doc)
        
        data = {
            "customer": customer,
            "items": items,
            "use": "G01",
            "payment_form": "28" 
        }

        data = json.dumps(data)
        response = requests.post(url, headers=header, data=data)
        if response.status_code == 200:
            response = response.json()
            doc.e_invoice_id = response.get('id'),
            doc.uuid = response.get('uuid'),
            doc.sat_signature = response.get('sat_signature'),
            doc.signature = response.get('stamp').get('signature'),
            doc.invoice_status = response.get('status'),
            doc.sat_cert_number = response.get('stamp').get('sat_cert_number'),
            doc.cfdi_version = response.get('cfdi_version'),
            doc.verification_url = response.get('verification_url')
        else:
            response = response.json()
            frappe.log_error("generate_einvoice", response.get('message'))
            frappe.throw(_(response.get('message')))

def get_customer_details(doc):
    customer_name, tax_id, tax_system = frappe.db.get_value('Customer', doc.customer, ['customer_name', 'tax_id', 'tax_system'])

    query = f""" select email_id, pincode from `tabAddress` where name = "{doc.customer_address}" """
    address = frappe.db.sql(query, as_dict=1)

    customer = {
        "legal_name": customer_name,
        "email": address[0]['email_id'],
        "tax_id": tax_id, 
        "tax_system": tax_system, 
        "address": { 
            "zip": address[0]['pincode']
        }
    }
    return customer

def get_items(doc):
    items = []

    for item in doc.items:
        #applying taxes
        taxes = []
        if item.item_tax_template:
            frappe.log_error("tax", item.item_code)
            item_tax_doc = frappe.get_doc("Item Tax Template", item.item_tax_template)
            for tax in item_tax_doc.taxes:
                taxes.append({
                    "type": tax.maxico_tax_type,
                    "rate": tax.tax_rate/100
                })
        elif doc.taxes_and_charges:
            frappe.log_error("tax", item.item_code)
            item_tax_doc = frappe.get_doc("Sales Taxes and Charges Template", doc.taxes_and_charges)
            for tax in item_tax_doc.taxes:
                taxes.append({
                    "type": tax.mexico_tax_type,
                    "rate": tax.rate/100
                })

        items.append({
            'quantity': item.qty,
            'product': {
                "description": re.sub('<[^<]+?>', '', _("{}".format(item.description))),
                "product_key": item.product_key,
                "price": item.rate,
                "tax_included": False,
                "taxes":taxes
            }
        })
    return items

@frappe.whitelist()
def cancel_einvoice(invoice_name, e_invoice_id, motive):
    e_invoice_setting = frappe.get_doc("E Invoice Setting", 'E Invoice Setting')
    if e_invoice_setting.cancel_e_invoice:
        token = get_token()
        url = "https://www.facturapi.io/v2/invoices/"+e_invoice_id+"?motive="+motive
        header = {
            "Authorization": "Bearer {}".format(token),
            "Content-Type": "application/json"
        }
        response = requests.delete(url, headers=header)
        if response.status_code == 200:
            doc = frappe.get_doc("Sales Invoice", invoice_name)
            doc.cancel()
            response = response.json()
            
            #set reason
            if motive == "01":
                reason = "01 - Receipt issued with errors related to."
            elif motive == "02":
                reason = "02 - Receipt issued with unrelated errors."
            elif motive == "03":
                reason = "03 - The operation was not carried out."
            elif motive == "04":
                reason = "04 - Nominative operation related to the global invoice."

            frappe.db.set_value('Sales Invoice', invoice_name, {
                'invoice_status': response.get('status'),
                'motive': reason
            })
            frappe.db.commit()
            return "success"
        else:
            response = response.json()
            frappe.log_error("cancel_einvoice.", response.get('message'))
            return "fail"

