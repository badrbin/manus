# Manus Customizations

Custom integrations and validations for ERPNext 15.

## Installation

```bash
bench get-app https://github.com/badrbin/manus.git
bench --site [your-site-name] install-app manus
```

## Features
- Material Request validation against Sales Order billed quantity.
- Payment Entry restriction for Suppliers.
- Sales Invoice quantity validation against Sales Order.
- Custom API endpoints for GL summaries.
