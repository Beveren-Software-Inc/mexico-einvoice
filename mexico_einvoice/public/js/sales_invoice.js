frappe.ui.form.on('Sales Invoice', {
	refresh: function(frm) {
		if (frm.doc.docstatus == 1 && frm.doc.e_invoice_id) {
            frm.add_custom_button(__('Download E-Invoice'), function() {
                download_e_invoice(frm)
            })
        }
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