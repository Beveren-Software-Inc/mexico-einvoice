frappe.ui.form.on('Payroll Entry', {
    refresh: function (frm) {
        if (frm.doc.docstatus == 1 && frm.doc.status == "Submitted" && !frm.doc.payroll_id) {
            frm.events.add_e_payroll_buttons(frm);
        }
    },
    add_e_payroll_buttons: function (frm) {
        frm.add_custom_button(__("Make E-Pyroll"), function () {
            frappe.call({
                method: 'mexico_einvoice.payroll.submit_e_payroll',
                args: {
                    'name': frm.doc.name,
                },
                callback: function (r) {
                    if(r.message == "success"){
                        frappe.show_alert('E Payroll generated successfully', 5);
                    }
                }
            });
        }).addClass("btn-primary");
    }
})