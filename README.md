# Smart Invoice Processing & Automation System

## 1. Project Overview

The Smart Invoice Processing & Automation System is a Python-based application designed to automate invoice processing, validation, matching, exception handling, approval workflows, and payment processing.

The system compares invoice details with Purchase Orders (PO) and Goods Receipts (GR), identifies mismatches, routes exception invoices for approval, manages payment readiness, and maintains invoice lifecycle history.

An interactive Streamlit dashboard provides visibility into invoice processing activities, approvals, payments, exceptions, and audit history.

## 2. Project Objectives

- Automate invoice processing and validation.
- Generate synthetic business data for testing.
- Perform invoice-to-PO and invoice-to-GR matching.
- Identify duplicate invoices and data mismatches.
- Route exceptions to appropriate approval teams.
- Manage approval decisions and invoice lifecycle statuses.
- Validate payment readiness and prevent duplicate payments.
- Maintain invoice audit history.
- Monitor business activities through an interactive dashboard.

## 3. Technologies Used

| Category | Technology |
|---|---|
| Programming Language | Python |
| Database | SQLite |
| Dashboard | Streamlit |
| Data Processing | Pandas |
| Data Visualization | Plotly |
| Synthetic Data Generation | Faker |
| Testing | Pytest |

## 4. Project Structure

```text
Invoice_Automation_System/
│
├── data/
│   └── invoice_automation_v2.db
│
├── database/
│   ├── db.py
│   └── schema.sql
│
├── generator/
│   ├── generate_data.py
│   └── generate_data_v2.py
│
├── services/
│   ├── matching.py
│   ├── exception_routing.py
│   ├── approval_workflow.py
│   └── payment_processing.py
│
├── tests/
│   ├── test_validation.py
│   └── test_payment_processing.py
│
├── output/
│   └── ground_truth.csv
│
├── docs/
│
├── app.py
├── requirements.txt
└── README.md
```

## 5. Main Features

### 5.1 Synthetic Data Generation

Generates realistic sample business data using Python and Faker.

Generated dataset:
- 300 Vendors
- 1,500 Purchase Orders
- 2,000 Invoices
- 2,000 Invoice Lines

The V2 generator also creates Goods Receipts, Purchase Order Lines, and ground-truth validation data.

### 5.2 Invoice Matching Engine

Compares invoice information against purchase orders and goods receipts.

Validation includes:
- Vendor validation
- Purchase Order validation
- Duplicate invoice detection
- Invoice price validation
- Ordered quantity validation
- Received quantity validation
- Goods Receipt validation
- Tax code validation

The matching engine records PASS and FAIL results in the InvoiceMatch table.

### 5.3 Exception Routing

Automatically identifies invoices with failed matching checks.

- Routes exceptions to appropriate review teams.
- Creates approval records.
- Assigns teams based on exception categories.
- Updates invoice lifecycle status.
- Supports repeatable routing of pending automatic approvals.

### 5.4 Approval Workflow

Manages approval decisions for exception invoices.

- Displays pending approvals.
- Supports APPROVED and REJECTED decisions.
- Stores reviewer comments.
- Updates invoice lifecycle status.
- Records lifecycle changes in audit history.

### 5.5 Payment Processing

Manages payment readiness and payment status.

- Checks whether invoices are eligible for payment.
- Blocks rejected invoices.
- Blocks unresolved matching exceptions.
- Checks approval completion.
- Prevents duplicate payment records.
- Creates payment records with PENDING status.
- Supports COMPLETED and FAILED payment statuses.
- Updates invoice lifecycle status to PAID or PAYMENT_FAILED.

### 5.6 Streamlit Dashboard

Provides an interactive dashboard displaying:

- Business overview
- Vendor and purchase order information
- Invoice status distribution
- Invoice matching results
- Exception categories
- Approval status
- Payment overview
- Invoice records
- Exception records
- Payment records
- Approval records
- Invoice audit history

## 6. Invoice Matching Results

Final V2 execution results:

| Metric | Result |
|---|---:|
| Total Invoices | 2,000 |
| Matched Invoices | 1,400 |
| Exception Invoices | 600 |
| Matching Success Rate | 70% |

The exception records are intentionally generated to validate the matching and exception-handling workflows.

## 7. Exception Routing Results

| Metric | Result |
|---|---:|
| Total Exception Invoices | 600 |
| Invoices Routed | 600 |
| Approval Records Created | 778 |

Multiple approval records can be created for an invoice when it has multiple matching exceptions.

## 8. Database Tables

The SQLite database contains the following tables:

1. Vendor
2. PurchaseOrder
3. PurchaseOrderLine
4. GoodsReceipt
5. GoodsReceiptLine
6. Invoice
7. InvoiceLine
8. Approval
9. Payment
10. InvoiceMatch
11. InvoiceEvent

## 9. Installation

Clone or download the project and open the project directory.

Create a virtual environment:

```bash
python -m venv venv
```

Activate the environment in Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 10. Execution Instructions

Run the following commands from the main project directory.

### Generate synthetic data

```powershell
python generator/generate_data_v2.py
```

**Important:** The V2 generator drops and recreates database tables. Back up your database and ground-truth file before running it again.

### Run invoice matching

```powershell
python services/matching.py
```

### Run exception routing

```powershell
python services/exception_routing.py
```

### Run approval workflow

```powershell
python services/approval_workflow.py
```

### Run payment processing

```powershell
python services/payment_processing.py
```

### Launch the Streamlit dashboard

```powershell
streamlit run app.py
```

Open the application in your browser:

```text
http://localhost:8501
```

## 11. Testing

The project uses Pytest for automated testing.

Run all tests:

```powershell
python -m pytest -v
```

Run payment processing tests separately:

```powershell
python -m pytest -v tests/test_payment_processing.py
```

### Final Testing Results

| Test Category | Result |
|---|---:|
| Database and invoice validation | 6 Passed |
| Payment processing | 8 Passed |
| Total Automated Tests | 14 Passed |
| Failed Tests | 0 |

The payment tests cover:
- Payment readiness
- Invalid invoice handling
- Unresolved exception blocking
- Pending approval blocking
- Duplicate payment prevention
- Payment creation
- Successful payment completion
- Failed payment handling
- Invoice lifecycle updates
- Audit event creation

## 12. Conclusion

The Smart Invoice Processing & Automation System demonstrates how Python, SQLite, Streamlit, and automated testing can be combined to build an invoice processing solution.

The application provides automated invoice matching, exception identification, approval workflows, payment processing, and audit history.

It improves visibility into invoice processing activities and demonstrates an end-to-end invoice automation workflow.