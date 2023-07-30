frappe.ui.form.on('Employee', {
	onload: function(frm) {
		//filter Type of Contract
		frm.set_query('type_of_contract', function(doc) {
			return {
				query: "mexico_einvoice.filters.filter_contract_type",
			}
		});

		//filter Regime Type
		frm.set_query('regime_type', function(doc) {
			return {
				query: "mexico_einvoice.filters.filter_regime_type",
			}
		});

		//filter Payment Periodicity
		frm.set_query('payment_periodicity', function(doc) {
			return {
				query: "mexico_einvoice.filters.filter_payment_priodicity",
			}
		});

		//set default field value
		if(frm.doc.__islocal){
			//set type_of_contract
			frappe.db.get_list('Contract Type', {
				fields: ['name'],
				filters: {
					enable: 1,
					default: 1
				}
			}).then(records => {
				if(records.length){
					frm.set_value("type_of_contract", records[0].name)
				}
			})
			
			//set regime_type
			frappe.db.get_list('Regime Type', {
				fields: ['name'],
				filters: {
					enable: 1,
					default: 1
				}
			}).then(records => {
				if(records.length){
					frm.set_value("regime_type", records[0].name)
				}
			})
			
			//set payment_periodicity
			frappe.db.get_list('Payment Periodicity', {
				fields: ['name'],
				filters: {
					enable: 1,
					default: 1
				}
			}).then(records => {
				if(records.length){
					frm.set_value("payment_periodicity", records[0].name)
				}
			})
		}
	}
})