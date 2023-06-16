frappe.ui.form.on('Payment Entry', {
	onload: function(frm) {
		frm.set_query('payment_form', function(doc) {
			return {
				query: "mexico_einvoice.filters.filter_payment_form",
			}
		});
		
		//set default payment form
		frappe.db.get_list('Payment Form', {
			fields: ['name'],
			filters: {
				enable: 1,
				default: 1
			}
		}).then(records => {
			if(records.length){
				frm.set_value("payment_form", records[0].name)
			}
		})
	}
})