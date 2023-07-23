var dialog_cancel;

frappe.ui.form.on('Sales Invoice', {
	refresh: function(frm) {
        dialog_cancel = new frappe.ui.Dialog(getDialogCancel(frm));
        
		if (frm.doc.docstatus == 1 && frm.doc.e_invoice_id) {
            frm.add_custom_button(__('Download E-Invoice'), function() {
                download_e_invoice(frm.doc.e_invoice_id)
            })
            // remove action buttons from child table
            $('.grid-buttons').remove()
        }
        //show download button in grid row
        show_download_buttons(frm)

        //download payment invoice
        frm.fields_dict['e_invoice_payments'].$wrapper.on('click', '.download-button', function() {
            var invoice_id = $(this).data('invoice-id');
            download_e_invoice(invoice_id);
        });
    },
    before_cancel: function(frm){
        dialog_cancel.show();
        frappe.validated = false; 
    },
    onload_post_render: function(frm) {
        if(frm.is_dirty()){
            frm.set_value({
                'e_invoice_id': '',
                'invoice_status': '',
                'motive': '', 
                'uuid': '',
                'cfdi_version': '',
                'verification_url': '',
                'sat_cert_number': '',
                'signature': ''
            })
            
            //clear e invoice payments
            frm.set_value('e_invoice_payments', []);

        }
	}
});

function download_e_invoice(e_invoice_id){
    frappe.call({
        method: "mexico_einvoice.utils.get_token",
        args: {
            e_invoice_id: e_invoice_id,
        },
        callback: function(r) {
            if(r.message) {
                const bearerToken = "Bearer "+r.message;
                fetch("https://www.facturapi.io/v2/invoices/"+e_invoice_id+"/zip", {
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
                a.download = e_invoice_id+".zip";
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
            { value: '04', label: '04 - Nominative operation related to the global invoice.'}
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

function show_download_buttons(frm){
    frm.fields_dict['e_invoice_payments'].$wrapper.find('.grid-body .rows').find(".grid-row").each(function (i, item) {
        let invoice_id = frm.doc.e_invoice_payments[i].id
        $(item).find('[data-fieldname="action_button"]').replaceWith(`
            <div class="col grid-static-col col-xs-2 " data-fieldname="action_button" data-fieldtype="Button">
                <div class="field-area" style="margin:-3px">
                    <div class="form-group frappe-control input-max-width" title="Download Payment Invoice">
                        <button class="btn btn-xs btn-primary input-sm download-button" data-invoice-id="${invoice_id}">Download</button>
                    </div>
                </div>
            </div>
        `);
    });
}

frappe.ui.form.on('E Invoice Payments', {
    form_render(frm, cdt, cdn){
        frm.fields_dict.e_invoice_payments.grid.wrapper.find('.grid-delete-row').hide();
        frm.fields_dict.e_invoice_payments.grid.wrapper.find('.grid-duplicate-row').hide();
        frm.fields_dict.e_invoice_payments.grid.wrapper.find('.grid-move-row').hide();
        frm.fields_dict.e_invoice_payments.grid.wrapper.find('.grid-append-row').hide();
        frm.fields_dict.e_invoice_payments.grid.wrapper.find('.grid-insert-row-below').hide();
        frm.fields_dict.e_invoice_payments.grid.wrapper.find('.grid-insert-row').hide();
    }
})