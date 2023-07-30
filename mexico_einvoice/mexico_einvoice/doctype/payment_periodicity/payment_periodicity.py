# Copyright (c) 2023, Beveren-Software-Inc and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PaymentPeriodicity(Document):
	def on_update(self):
		if self.default:
			query = f""" update `tabPayment Periodicity` set `default` = 0 where name != "{self.name}" """
			frappe.db.sql(query)
			frappe.db.commit()
			self.reload()
