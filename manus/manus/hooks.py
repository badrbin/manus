app_name = "manus"
app_title = "Manus Customizations"
app_publisher = "Manus"
app_description = "Custom integrations and validations for ERPNext 15"
app_email = "info@manus.im"
app_license = "mit"

# Document Events
doc_events = {
    "Material Request": {
        "validate": "manus.api.validations.validate_material_request_against_billed"
    },
    "Payment Entry": {
        "validate": "manus.api.validations.validate_payment_entry_supplier"
    },
    "Sales Invoice": {
        "validate": "manus.api.validations.validate_sales_invoice_qty_against_so"
    }
}
