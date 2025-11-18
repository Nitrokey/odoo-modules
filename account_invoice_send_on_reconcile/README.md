# Account Invoice Send on Reconcile

## Overview

This Odoo 15.0 module automatically sends customer invoice emails when bank payments are reconciled with invoices from bank statements.

## Features

- **Automatic Invoice Sending**: When reconciling bank statement lines with customer invoices, the module automatically sends the invoice email to the customer
- **Duplicate Prevention**: Uses the `is_move_sent` flag to prevent sending duplicate emails
- **Smart Filtering**: Only sends for:
  - Posted customer invoices
  - Fully paid invoices
  - Invoices not already marked as sent
- **Error Handling**: Email sending errors are logged but don't break the reconciliation process

## Configuration

No configuration required. The module works automatically once installed.

## Usage

1. Navigate to Accounting > Dashboard > Bank
2. Import or create bank statement lines
3. Reconcile statement lines with customer invoices
4. The module automatically sends invoice emails for reconciled, fully-paid invoices
5. Check the invoice's "Sent" status to confirm
