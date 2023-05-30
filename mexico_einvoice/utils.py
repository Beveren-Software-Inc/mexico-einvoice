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
            "payment_form": "99" ,
            "payment_method": "PPD"
        }

        #validate advance payment
        validate_advance_payments(data, doc)

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

def validate_advance_payments(data, doc):
    if doc.outstanding_amount == 0:
        data.update({
            "payment_form": "30" ,
            "payment_method": "PUE"
        })

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
            item_tax_doc = frappe.get_doc("Item Tax Template", item.item_tax_template)
            for tax in item_tax_doc.taxes:
                taxes.append({
                    "type": tax.maxico_tax_type,
                    "rate": tax.tax_rate/100
                })
        elif doc.taxes_and_charges:
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

def get_customer_from_payment(doc):
    customer_name, tax_id, tax_system = frappe.db.get_value('Customer', doc.party, ['customer_name', 'tax_id', 'tax_system'])


    query = f""" select email_id, pincode from `tabAddress` where name in (select customer_primary_address from `tabCustomer` 
        where name = "{doc.party}") """
    
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

def update_payment(doc, method):

    if not doc.references:
        return
    
    customer = get_customer_from_payment(doc)

    #update related documents
    related_documents = []
    for rel_doc in doc.references:
        if rel_doc.reference_doctype == "Sales Invoice":
            uuid = frappe.get_value("Sales Invoice", rel_doc.reference_name, 'uuid')
            installments = linked_sales_invoice(rel_doc.reference_name)

            invoice_details = {
                "uuid": uuid,
                "amount": rel_doc.allocated_amount,
                "last_balance": rel_doc.outstanding_amount,
                "installment": installments+1,
                "taxes": [
                    {
                        "base": rel_doc.allocated_amount / (1+ 0.16),
                        "type": "IVA",
                        "rate": 0.16
                    }
                ]
            }
            related_documents.append(invoice_details)

    complements = [
        {
            "type": "pago",
            "data": [
                {
                    "payment_form": doc.payment_form,
                    "related_documents": related_documents
                }
            ]
        }
    ]

    data = {  
        "type": "P",
        "customer": customer,
        "complements": complements
    }

    token = get_token()
    url = "https://www.facturapi.io/v2/invoices"
    header = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json"
    }

    data = json.dumps(data)
    frappe.log_error("data", data)
    response = requests.post(url, headers=header, data=data)
    if response.status_code == 200:
        response = response.json()
        frappe.log_error("update_payment", response.get('message'))
    else:
        response = response.json()
        frappe.log_error("update_payment", response.get('message'))
        frappe.throw(_(response.get('message')))

def linked_sales_invoice(sales_invoice):
    query = f""" select COUNT(name) as installment from `tabPayment Entry Reference` where parenttype="Payment Entry" 
        and reference_doctype="Sales Invoice" and reference_name="{sales_invoice}" """
    count = frappe.db.sql(query, pluck='installment')
    return count[0]