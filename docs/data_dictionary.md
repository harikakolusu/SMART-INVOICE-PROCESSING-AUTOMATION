# Invoice Automation System – Data Dictionary

## 1. Overview

This document defines the data fields, data types, constraints, relationships and validation rules used in the Invoice Automation System.

Database: SQLite  
Primary technology: Python  
Data format: Synthetic data  
Random seed: 20261022

## 2. Vendor

| Field | Data Type | Required | Validation |
|---|---|---|---|
| vendor_id | TEXT | Yes | Unique primary key; format VND-00001 |
| vendor_name | TEXT | Yes | Must not be empty |
| email | TEXT | No | Valid email format |
| phone | TEXT | No | 10-digit phone number |
| status | TEXT | Yes | ACTIVE or CLOSED |
| created_at | TEXT | No | Valid timestamp |

## 3. PurchaseOrder

| Field | Data Type | Required | Validation |
|---|---|---|---|
| po_id | TEXT | Yes | Unique primary key |
| vendor_id | TEXT | Yes | Must reference an existing Vendor |
| po_date | TEXT | Yes | Valid date |
| status | TEXT | No | OPEN, CLOSED or APPROVED |

Relationship: One Vendor can have multiple Purchase Orders (1:N).

## 4. PurchaseOrderLine

| Field | Data Type | Required | Validation |
|---|---|---|---|
| po_line_id | TEXT | Yes | Unique primary key |
| po_id | TEXT | Yes | Must reference PurchaseOrder |
| sku | TEXT | Yes | Must not be empty |
| quantity | REAL | Yes | Greater than zero |
| unit_price | REAL | Yes | Zero or greater |
| tax_code | TEXT | Yes | GST_5, GST_12 or GST_18 |

Relationship: One Purchase Order can contain 1–8 purchase order lines (1:N).

## 5. GoodsReceipt

| Field | Data Type | Required | Validation |
|---|---|---|---|
| receipt_id | TEXT | Yes | Unique primary key |
| po_id | TEXT | Yes | Must reference PurchaseOrder |
| receipt_date | TEXT | Yes | Must be a valid date |
| status | TEXT | No | RECEIVED or other documented lifecycle state |

Relationship: One Purchase Order can have multiple Goods Receipts (1:N).

## 6. GoodsReceiptLine

| Field | Data Type | Required | Validation |
|---|---|---|---|
| receipt_line_id | TEXT | Yes | Unique primary key |
| receipt_id | TEXT | Yes | Must reference GoodsReceipt |
| po_line_id | TEXT | Yes | Must reference PurchaseOrderLine |
| received_quantity | REAL | Yes | Zero or greater |

Relationship: GoodsReceiptLine connects receipts to purchase order lines.

## 7. Invoice

| Field | Data Type | Required | Validation |
|---|---|---|---|
| invoice_id | TEXT | Yes | Unique primary key |
| vendor_id | TEXT | Yes | Must reference Vendor |
| po_id | TEXT | No | Must reference PurchaseOrder when provided |
| invoice_number | TEXT | Yes | Check duplicate invoices per vendor |
| invoice_date | TEXT | Yes | Valid date; normally not before PO date |
| subtotal | REAL | Yes | Sum of invoice line totals |
| tax_amount | REAL | Yes | Sum of invoice line taxes |
| grand_total | REAL | Yes | Subtotal + tax amount |
| match_status | TEXT | No | PENDING, MATCHED or EXCEPTION |
| lifecycle_status | TEXT | No | Documented invoice lifecycle state |

Relationship: One Vendor can submit multiple Invoices (1:N). A Purchase Order can be associated with multiple invoices.

## 8. InvoiceLine

| Field | Data Type | Required | Validation |
|---|---|---|---|
| invoice_line_id | TEXT | Yes | Unique primary key |
| invoice_id | TEXT | Yes | Must reference Invoice |
| po_line_id | TEXT | No | Must reference PurchaseOrderLine when provided |
| sku | TEXT | Yes | Must not be empty |
| quantity | REAL | Yes | Greater than zero |
| unit_price | REAL | Yes | Zero or greater |
| tax_code | TEXT | Yes | GST_5, GST_12 or GST_18 |
| line_total | REAL | Yes | Quantity × unit price |
| tax_amount | REAL | Yes | Line total × applicable tax rate |

Relationship: One Invoice can contain multiple Invoice Lines (1:N).

## 9. Approval

| Field | Data Type | Required | Validation |
|---|---|---|---|
| approval_id | TEXT | Yes | Unique primary key |
| invoice_id | TEXT | Yes | Must reference Invoice |
| approver_name | TEXT | No | Assigned approver or review team |
| decision | TEXT | Yes | PENDING, APPROVED or REJECTED |
| decision_date | TEXT | No | Valid decision timestamp |
| comments | TEXT | No | Approval or rejection explanation |

Relationship: One Invoice can have multiple Approval records (1:N).

## 10. Payment

| Field | Data Type | Required | Validation |
|---|---|---|---|
| payment_id | TEXT | Yes | Unique primary key |
| invoice_id | TEXT | Yes | Must reference Invoice |
| payment_amount | REAL | Yes | Greater than zero |
| payment_date | TEXT | No | Valid payment date |
| payment_status | TEXT | No | PENDING, COMPLETED or FAILED |

Relationship: One Invoice can have multiple Payment records (1:N). Payments must only be initiated for eligible invoices.

## 11. InvoiceMatch

| Field | Data Type | Required | Validation |
|---|---|---|---|
| match_id | INTEGER | Yes | Auto-increment primary key |
| invoice_id | TEXT | Yes | Must reference Invoice |
| check_type | TEXT | Yes | Type of business validation |
| result | TEXT | Yes | PASS or FAIL |
| expected_value | TEXT | No | Expected business value |
| actual_value | TEXT | No | Actual invoice value |
| message | TEXT | No | Explanation of validation |
| checked_at | TEXT | No | Timestamp of validation |

## 12. InvoiceEvent

| Field | Data Type | Required | Validation |
|---|---|---|---|
| event_id | INTEGER | Yes | Auto-increment primary key |
| invoice_id | TEXT | Yes | Must reference Invoice |
| old_status | TEXT | No | Previous lifecycle status |
| new_status | TEXT | Yes | New lifecycle status |
| event_description | TEXT | No | Reason for state transition |
| event_time | TEXT | No | Event timestamp |

## 13. Business Validation Rules

1. Every primary key must be unique.
2. Foreign keys must reference valid parent records.
3. Invoice totals must reconcile with invoice lines.
4. Tax must be calculated using the applicable tax code.
5. Duplicate invoice numbers must be detected per vendor.
6. Invoice quantity must not exceed ordered or received quantity unless explicitly classified as an exception.
7. Closed vendors must be flagged.
8. Invoice dates must be checked against purchase order dates.
9. Price differences must be checked against the configured tolerance.
10. Blocked invoices must not be marked payment-ready.

## 14. Data Generation Standards

- Generate 300 vendors.
- Generate 1,500 purchase orders.
- Generate 2,200 purchase order lines.
- Generate 1,800 goods receipts.
- Generate 2,000 invoices.
- Use fixed random seed 20261022.
- Use deterministic and immutable IDs.
- Generate ground-truth labels separately.
- Validate generated records before processing.

## 15. Relationship Summary

| Parent Entity | Child Entity | Cardinality |
|---|---|---|
| Vendor | PurchaseOrder | 1:N |
| Vendor | Invoice | 1:N |
| PurchaseOrder | PurchaseOrderLine | 1:N |
| PurchaseOrder | GoodsReceipt | 1:N |
| GoodsReceipt | GoodsReceiptLine | 1:N |
| PurchaseOrderLine | GoodsReceiptLine | 1:N |
| Invoice | InvoiceLine | 1:N |
| PurchaseOrderLine | InvoiceLine | 1:N |
| Invoice | Approval | 1:N |
| Invoice | Payment | 1:N |
| Invoice | InvoiceMatch | 1:N |
| Invoice | InvoiceEvent | 1:N |

Note: InvoiceLine and GoodsReceiptLine provide links to purchase order lines. These relationships support matching across the purchase order, receipt and invoice.

---

**Document:** Invoice Automation System Data Dictionary  
**Purpose:** Database design, validation, synthetic data generation and invoice processing documentation.