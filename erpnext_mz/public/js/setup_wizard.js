frappe.provide("erpnext_mz.setup");

// Register our slide only if our app hasn't already completed setup
frappe.setup.on("before_load", function () {
  if (
    frappe.boot.setup_wizard_completed_apps?.length &&
    frappe.boot.setup_wizard_completed_apps.includes("erpnext_mz")
  ) {
    return;
  }

  frappe.setup.add_slide({
    name: "mz_intro",
    title: __("ERPNext Moçambique Setup"),
    icon: "fa fa-flag",
    fields: [
      {
        fieldname: "enable_mz_defaults",
        label: __("Apply Mozambique Defaults"),
        fieldtype: "Check",
        default: 1,
        description: __(
          "Sets language to Português (Moçambique), currency to MZN, timezone Africa/Maputo, and number/date formats."
        ),
      },
      { fieldtype: "Section Break" },
      {
        fieldname: "create_demo",
        label: __("Create Demo Data (optional)"),
        fieldtype: "Check",
        default: 0,
      },
    ],

    validate: function () {
      // Always allow; values are optional
      return true;
    },
  });
});


