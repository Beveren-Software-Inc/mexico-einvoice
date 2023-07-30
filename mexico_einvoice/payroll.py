import json
from frappe import _
import requests
from mexico_einvoice.utils import get_token
import frappe
from frappe.utils import getdate, nowdate

def update_payroll_entry(doc, method):
    if doc.docstatus == 1 and doc.payroll_entry:
        frappe.db.set_value('Payroll Employee Detail', {'parent': doc.payroll_entry, 'employee': doc.employee}, {
            'salary_slip': doc.name,
            'payment_days': doc.payment_days
        })

        p_doc = frappe.get_doc("Payroll Entry", doc.payroll_entry)
        p_doc.save()

@frappe.whitelist()
def submit_e_payroll(name: str):
    token = get_token()
    url = "https://www.facturapi.io/v2/invoices"
    header = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json"
    }

    doc = frappe.get_doc("Payroll Entry", name)
    company_details= get_company_details(doc)
    employees_details = get_employees_details(doc)
    
    data = {
        "type": "N",
        "customer": company_details,
        "complements": employees_details,
        "date": str(getdate(nowdate()))
    }

    data = json.dumps(data)
    response = requests.post(url, headers=header, data=data)
    if response.status_code == 200:
        response = response.json()
        doc.payroll_id = response.get('id'),
        doc.payroll_status = response.get('status'),
        doc.verification_url = response.get('verification_url')
        doc.save()
        return "success"
    else:
        response = response.json()
        frappe.log_error("submit_e_payroll", response.get('message'))
        frappe.throw(_(response.get('message')))

def get_company_details(doc):
    company = frappe.get_doc("Company", doc.company)

    #validate mandatory fields for epayroll
    if not company.tax_id:
        frappe.throw(_("Tax Id is mandatory field in Company"), exc=frappe.MandatoryError)
    elif not company.tax_system:
        frappe.throw(_("Tax System is mandatory field in Company"), exc=frappe.MandatoryError)
    elif not company.zip:
        frappe.throw(_("Zip is mandatory field in Company"), exc=frappe.MandatoryError)

    email = company.email or ""
    phone = company.phone_no or ""
    company_details = {
        "legal_name": company.name,
        "tax_id": company.tax_id,
        "tax_system": company.tax_system,
        "email": str(email),
        "phone": str(phone),
        "address": {
            "zip": str(company.zip)
        }
    }
    return company_details

def get_employees_details(doc):
    employees_details = []
    for emp in doc.employees:
        employees_details.append({
            "type": "nomina",
            "data": {
                "fecha_inicial_pago": str(doc.start_date),
                "fecha_final_pago": str(doc.end_date),
                "num_dias_pagados": str(emp.payment_days),
                "receptor": {
                    "curp": emp.curp,
                    "tipo_contrato": emp.type_of_contract,
                    "tipo_regimen": emp.regime_type,
                    "num_empleado": emp.employee_no,
                    "periodicidad_pago": emp.payment_periodicity,
                    "clave_ent_fed": emp.state_code
                }
            }
        })

    return employees_details