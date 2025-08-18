frappe.ui.form.on(['Customer', 'Supplier', 'Company'], {
	onload(frm) {
		// Nothing required; we only attach validate handler
	},
	validate(frm) {
		try {
			const doctype = frm.doc.doctype;
			let value = frm.doc.nuit;
			if (doctype === 'Company' && (!value || value === '')) {
				// Fallback to tax_id if nuit is not set; we do NOT overwrite, just validate if present
				value = frm.doc.tax_id || '';
			}
			if (!value) {
				return; // allow empty
			}
			const s = String(value).trim();
			const ok = /^\d{9}$/.test(s);
			if (!ok) {
				frappe.throw(__('NUIT inválido: deve conter exatamente 9 dígitos. Valor: {0}', [s]));
			}
		} catch (e) {
			// never block save due to client error; server-side validation remains
		}
	}
});
