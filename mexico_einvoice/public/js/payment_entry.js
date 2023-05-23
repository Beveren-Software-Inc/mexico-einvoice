frappe.ui.form.on('Payment Entry', {
	onload: function(frm) {
		frm.set_query('payment_form', function(doc) {
			return {
				query: "mexico_einvoice.filters.filter_payment_form",
			}
		});
	},
})