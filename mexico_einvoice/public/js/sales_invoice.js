var dialog_cancel;

frappe.ui.form.on('Sales Invoice', {
	refresh: function(frm) {
        dialog_cancel = new frappe.ui.Dialog(getDialogCancel(frm));
        
		if (frm.doc.docstatus == 1 && frm.doc.e_invoice_id) {
            frm.add_custom_button(__('Download E-Invoice'), function() {
                download_e_invoice(frm)
            })
        }
    },
    before_cancel: function(frm){
        dialog_cancel.show();
        frappe.validated = false; 
    }
});

function download_e_invoice(frm){
    frappe.call({
        method: "mexico_einvoice.utils.get_token",
        args: {
            e_invoice_id: frm.doc.e_invoice_id,
        },
        callback: function(r) {
            if(r.message) {
                const bearerToken = "Bearer "+r.message;
                fetch("https://www.facturapi.io/v2/invoices/"+frm.doc.e_invoice_id+"/pdf", {
                headers: {
                    "Authorization": bearerToken
                }
                })
                .then(response => response.blob())
                .then(blob => {
                // Create a download link for the PDF file
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = frm.doc.e_invoice_id+".pdf";
                document.body.appendChild(a);
                a.click();
                a.remove();})
            }
        }
    });
}

function getDialogCancel (frm) {
    return {
      primary_action_label: 'Cancel E-Invoice',
      primary_action: function (values) {
        cancel_einvoice(frm, values);
      },
      title: 'Cancel E-Invoice',
      fields: [
        {
          label: 'Reason of Cancellation',
          fieldname: 'motive',
          fieldtype: 'Select',
          options: [
            { value: '01', label: '01 - Receipt issued with errors related to.'},
            { value: '02', label: '02 - Receipt issued with unrelated errors.'},
            { value: '03', label: '03 - The operation was not carried out.'},
            { value: '04', label: '04 - Nominative operation related to the global invoice.'},

          ],
          required: true,
          default:"03",
        },
      ]
    };
}

function cancel_einvoice(frm, values) {
    frappe.call('mexico_einvoice.utils.cancel_einvoice', {
        invoice_name: frm.doc.name,
        e_invoice_id: frm.doc.e_invoice_id,
        motive: values.motive
    })
    .then(response => {
        if(response.message == 'success') {
            dialog_cancel.hide();
            setTimeout(function () {
                frappe.msgprint({
                    message: 'E-Invoice cancelled successfully.',
                    indicator: 'green'
                });
            }, 500);
            frm.reload_doc();
        } 
        else {
            frappe.msgprint({
                message: 'Error: ' + "E-Invoice cancellation fail",
                indicator: 'red'
            });
        }
    })
  }