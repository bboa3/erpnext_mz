frappe.provide('erpnext_mz.onboarding');

(function () {
  // console.log('🚀 MZ Onboarding script loaded'); // Commented for production
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
            options: ['Normal (16%)', 'Reduzida (5%)', 'Isento'],
            default: 'Normal (16%)',
            reqd: 1,
            description: __('Regime de IVA padrão da Empresa'),
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
        title: __('Contactos da Empresa e Pagamentos'),
        fields: [
          { fieldname: 'cb_contacts', fieldtype: 'Column Break', label: __('Contactos da Empresa') },
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
          { fieldname: 'cb_payment_methods', fieldtype: 'Column Break', label: __('Métodos de pagamento padrão da empresa') },
          { fieldname: 'payment_method_cash', fieldtype: 'Check', label: __('Dinheiro (Cash)'), default: 0, description: __('Pagamentos em numerário registados na conta "Caixa"') },
          { fieldname: 'payment_method_bci', fieldtype: 'Check', label: __('Banco BCI'), default: 0, description: __('Conta no Banco BCI') },
          { fieldname: 'payment_method_millenium', fieldtype: 'Check', label: __('Banco Millenium BIM'), default: 0, description: __('Conta no Banco MIM') },
          { fieldname: 'payment_method_standard_bank', fieldtype: 'Check', label: __('Banco Standard Bank'), default: 0, description: __('Conta no Standard Bank') },
          { fieldname: 'payment_method_absa', fieldtype: 'Check', label: __('Banco ABSA'), default: 0, description: __('Conta no ABSA') },
          { fieldname: 'payment_method_emola', fieldtype: 'Check', label: __('E-Mola'), default: 0, description: __('Carteira móvel E-Mola') },
          { fieldname: 'payment_method_mpesa', fieldtype: 'Check', label: __('M-Pesa'), default: 0, description: __('Carteira móvel M-Pesa') },
          { fieldname: 'payment_method_fnb', fieldtype: 'Check', label: __('Banco FNB'), default: 0, description: __('Conta no Banco FNB') },
          { fieldname: 'payment_method_moza', fieldtype: 'Check', label: __('Moza Banco'), default: 0, description: __('Conta no Moza Banco') },
          { fieldname: 'payment_method_letshego', fieldtype: 'Check', label: __('Banco Letshego'), default: 0, description: __('Conta no Banco Letshego') },
          { fieldname: 'payment_method_first_capital', fieldtype: 'Check', label: __('First Capital Bank'), default: 0, description: __('Conta no First Capital Bank') },
          { fieldname: 'payment_method_nedbank', fieldtype: 'Check', label: __('Nedbank'), default: 0, description: __('Conta no Nedbank') },
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
            closing = true;
            d.hide();
            setTimeout(() => { closing = false; resolve(); }, 0);
          });
        },
        secondary_action_label: __('Ignorar'),
        secondary_action() {
          post('erpnext_mz.setup.onboarding.skip_step', { step: 3 }).then(() => {
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

  // Test function for manual triggering (can be called from browser console)
  erpnext_mz.onboarding.test = function () {
    console.log('🧪 Testing MZ onboarding manually...');
    checkAndTriggerOnboarding();
  };

  // Performance optimization: prevent multiple simultaneous calls
  let isCheckingOnboarding = false;
  let onboardingChecked = false;

  // Function to check and trigger onboarding
  function checkAndTriggerOnboarding() {
    try {
      // Performance optimization: prevent multiple calls
      if (isCheckingOnboarding || onboardingChecked) {
        return;
      }

      // Check if we're in the desk (not login page)
      if (!window.location.pathname.includes('/app/')) {
        return;
      }

      // Check if setup wizard is completed
      if (!frappe.boot.setup_complete) {
        return;
      }

      // Set flag to prevent multiple simultaneous calls
      isCheckingOnboarding = true;

      // Check if onboarding should be triggered
      frappe.call({
        method: 'erpnext_mz.setup.onboarding.should_trigger_onboarding',
        callback: function (r) {
          isCheckingOnboarding = false; // Reset flag

          if (r.message && r.message.should_trigger) {
            onboardingChecked = true; // Mark as checked to prevent future calls
            erpnext_mz.onboarding.start(r.message.status);
          } else {
            // If trigger flag not set, mark as checked to prevent future calls
            if (r.message && r.message.reason === 'Trigger flag not set') {
              onboardingChecked = true;
            }
          }
        },
        error: function () {
          isCheckingOnboarding = false; // Reset flag on error
        }
      });
    } catch (e) {
      console.error('Onboarding error:', e);
      isCheckingOnboarding = false; // Reset flag on error
    }
  }

  // Optimized event listeners with debouncing
  let onboardingTimeout = null;

  function debouncedCheckAndTrigger() {
    if (onboardingTimeout) {
      clearTimeout(onboardingTimeout);
    }
    onboardingTimeout = setTimeout(checkAndTriggerOnboarding, 100);
  }

  // Try multiple approaches to trigger onboarding
  $(document).on('app_ready', function () {
    debouncedCheckAndTrigger();
  });

  // Also try the startup event which might be more reliable
  $(document).on('startup', function () {
    debouncedCheckAndTrigger();
  });

  // Also check when the page is fully loaded
  $(window).on('load', function () {
    debouncedCheckAndTrigger();
  });

  // Direct check when script loads (for immediate execution)
  if (frappe && frappe.boot && frappe.boot.setup_complete) {
    setTimeout(checkAndTriggerOnboarding, 500);
  }
})();


