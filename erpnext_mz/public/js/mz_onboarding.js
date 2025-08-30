frappe.provide('erpnext_mz.onboarding');

(function () {
  function post(path, args) {
    return frappe.call({ method: path, args });
  }

  async function show_step_1(status) {
    return new Promise((resolve) => {
      let closing = false;
      const d = new frappe.ui.Dialog({
        title: __('Dados fiscais da Empresa'),
        fields: [
          {
            fieldname: 'cb1',
            fieldtype: 'Column Break',
            label: __('Dados fiscais')
          },
          {
            fieldname: 'tax_id',
            label: __('NUIT da Empresa'),
            fieldtype: 'Data',
            reqd: 1,
            description: __('Número de Identificação Tributária'),
          },
          {
            fieldname: 'tax_regime',
            label: __('Regime de IVA'),
            fieldtype: 'Select',
            options: ['Normal', 'Isento', 'Exportador'],
            reqd: 1,
            description: __('Regime de IVA da Empresa'),
          },
          {
            fieldname: 'cb2',
            fieldtype: 'Column Break',
            label: __('Endereço Legal da Empresa')
          },
          {
            fieldname: 'address_line1',
            fieldtype: 'Data',
            label: __('Endereço'),
            description: __('Casa, Rua, Avenida, etc.'),
          },
          {
            fieldname: 'neighborhood_or_district',
            fieldtype: 'Data',
            reqd: 1,
            label: __('Bairro ou distrito'),
            description: __('Bairro ou distrito onde a empresa está localizada'),
          },
          {
            fieldname: 'city',
            fieldtype: 'Data',
            reqd: 1,
            label: __('Cidade'),
            description: __('Cidade onde a empresa está localizada'),
          },
          {
            fieldname: 'province',
            fieldtype: 'Data',
            reqd: 1,
            label: __('Província'),
            description: __('Província onde a empresa está localizada'),
          },
        ],
        primary_action_label: __('Salvar e Continuar'),
        primary_action(values) {
          post('erpnext_mz.setup.onboarding.save_step', { step: 1, values }).then(() => {
            closing = true;
            d.hide();
            setTimeout(() => { closing = false; resolve(); }, 0);
          });
        }
      });

      // Make dialog non-dismissable
      d.$wrapper.on('hide.bs.modal', function (e) {
        if (!closing) {
          e.preventDefault();
          e.stopImmediatePropagation();
          d.show();
        }
      });
      d.$wrapper.find('.modal-header .btn-close').hide();

      d.set_values(status || {});
      d.show();
    });
  }

  async function show_step_2(status) {
    return new Promise((resolve) => {
      let closing = false;
      const d = new frappe.ui.Dialog({
        title: __('Contactos da Empresa'),
        fields: [
          {
            fieldname: 'phone',
            label: __('Nº de Telefone'),
            fieldtype: 'Data',
            reqd: 1,
            description: __('Nº de Telefone da Empresa'),
          },
          {
            fieldname: 'email',
            label: __('Email'),
            fieldtype: 'Data',
            reqd: 1,
            description: __('Email da Empresa'),
          },
          {
            fieldname: 'website',
            label: __('Website'),
            fieldtype: 'Data',
            description: __('Website da Empresa'),
          },
        ],
        primary_action_label: __('Salvar e Continuar'),
        primary_action(values) {
          post('erpnext_mz.setup.onboarding.save_step', { step: 2, values }).then(() => {
            closing = true;
            d.hide();
            setTimeout(() => { closing = false; resolve(); }, 0);
          });
        }
      });
      d.$wrapper.on('hide.bs.modal', function (e) { if (!closing) { e.preventDefault(); e.stopImmediatePropagation(); d.show(); } });
      d.$wrapper.find('.modal-header .btn-close').hide();
      d.set_values(status || {});
      d.show();
    });
  }

  async function show_step_3_optional(status) {
    return new Promise((resolve) => {
      let closing = false;
      const d = new frappe.ui.Dialog({
        title: __('Configuração da Empresa (opcional)'),
        fields: [
          {
            fieldname: 'logo',
            label: __('Logótipo da Empresa'),
            fieldtype: 'Attach Image',
            description: __('Logótipo da Empresa'),
          },
          {
            fieldname: 'terms_and_conditions_of_sale',
            label: __('Termos de venda padrão'),
            fieldtype: 'Small Text',
            description: __('Termos e condições de venda padrão da Empresa'),
          },
        ],
        primary_action_label: __('Salvar e Continuar'),
        primary_action(values) {
          post('erpnext_mz.setup.onboarding.save_step', { step: 3, values }).then(() => {
            post('erpnext_mz.setup.onboarding.apply_all', {}).then(() => {
              closing = true;
              d.hide();
              setTimeout(() => { closing = false; resolve(); }, 0);
            });
          });
        },
        secondary_action_label: __('Ignorar'),
        secondary_action() {
          post('erpnext_mz.setup.onboarding.skip_step', { step: 3 }).then(() => {
            post('erpnext_mz.setup.onboarding.apply_all', {}).then(() => {
              closing = true;
              d.hide();
              setTimeout(() => { closing = false; resolve(); }, 0);
            });
          });
        }
      });
      d.$wrapper.on('hide.bs.modal', function (e) { if (!closing) { e.preventDefault(); e.stopImmediatePropagation(); d.show(); } });
      d.$wrapper.find('.modal-header .btn-close').hide();
      d.set_values(status || {});
      d.show();
    });
  }

  async function run_chain(status) {
    // fetch latest status and prefill values to avoid stale
    const [latest, values] = await Promise.all([
      post('erpnext_mz.setup.onboarding.get_status', {}),
      post('erpnext_mz.setup.onboarding.get_profile_values', {}),
    ]);
    const s = (latest && latest.message) || status || {};
    const prefill = (values && values.message) || {};

    // Step 1 - mandatory
    if (!s.step1_complete) {
      await show_step_1(prefill);
    }

    // Step 2 - mandatory
    if (!s.step2_complete) {
      await show_step_2(prefill);
    }

    // Step 3 - optional
    if (!s.step3_skipped) {
      await show_step_3_optional(prefill);
    }
  }

  erpnext_mz.onboarding.start = run_chain;

  $(document).on('app_ready', function () {
    try {
      const s = (frappe.boot && frappe.boot.erpnext_mz_onboarding) || null;
      // Check if we're in the desk (not login page)
      if (window.location.pathname.includes('/app/') && s && !s.applied) {
        erpnext_mz.onboarding.start(s);
      }
    } catch (e) {
      console.error('Onboarding error:', e);
    }
  });
})();


