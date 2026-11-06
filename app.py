
import sqlite3
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px

# Database location
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "invoice_automation_v2.db"

st.set_page_config(
    page_title="Invoice Automation System",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Invoice Automation Dashboard")
st.write("Monitor invoices, matching results and exceptions.")

# Database connection
@st.cache_data(ttl=30)

def load_data():
    connection = sqlite3.connect(DB_PATH)

    try:
        vendors = pd.read_sql_query(
            "SELECT * FROM Vendor", connection
        )

        purchase_orders = pd.read_sql_query(
            "SELECT * FROM PurchaseOrder", connection
        )

        invoices = pd.read_sql_query(
            "SELECT * FROM Invoice", connection
        )

        matches = pd.read_sql_query(
            "SELECT * FROM InvoiceMatch", connection
        )

        approvals = pd.read_sql_query(
            "SELECT * FROM Approval", connection
        )
        payments = pd.read_sql_query(
            "SELECT * FROM Payment", connection
        )
        events = pd.read_sql_query(
            "SELECT * FROM InvoiceEvent", connection
        )

        return vendors, purchase_orders, invoices, matches, approvals, payments, events

    finally:
        connection.close()


if not DB_PATH.exists():
    st.error("Database file not found: " + str(DB_PATH))
    st.stop()

try:
    vendors, purchase_orders, invoices, matches, approvals, payments, events = load_data()

except Exception as error:
    st.error("Unable to load database: " + str(error))
    st.stop()

# PaymentSummary calculations
total_vendors = len(vendors)
total_pos = len(purchase_orders)
total_invoices = len(invoices)

matched = len(invoices[
    invoices["match_status"] == "MATCHED"
])

exceptions = len(invoices[
    invoices["match_status"] == "EXCEPTION"
])

pending = len(approvals[
    approvals["decision"] == "PENDING"
])
# Payment summary calulations
total_payments = len(payments)

pending_payments = len(payments[
    payments["payment_status"] == "PENDING"
])

completed_payments = len(payments[
    payments["payment_status"] == "COMPLETED"
])

failed_payments = len(payments[
    payments["payment_status"] == "FAILED"
])

total_payment_amount = (
    payments["payment_amount"].sum()
    if not payments.empty else 0
)

success_rate = (
    matched / total_invoices * 100
    if total_invoices > 0 else 0
)

# Dashboard metrics
st.subheader("Business Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Vendors", total_vendors)
col2.metric("Purchase Orders", total_pos)
col3.metric("Total Invoices", total_invoices)
col4.metric("Pending Approvals", pending)

st.divider()

st.subheader("Payment Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Payments", total_payments)
col2.metric("Pending Payments", pending_payments)
col3.metric("Completed Payments", completed_payments)
col4.metric("Failed Payments", failed_payments)

st.metric(
    "Total Payment Amount",
    f"₹{total_payment_amount:,.2f}"
)

st.divider()

# Invoice status chart
st.subheader("Invoice Status Distribution")

status_data = invoices["match_status"].value_counts().reset_index()
status_data.columns = ["Status", "Count"]

if not status_data.empty:
    fig = px.pie(
        status_data,
        names="Status",
        values="Count",
        title="Matched vs Exception Invoices",
        hole=0.4
    )
    st.plotly_chart(fig, use_container_width=True)

# Exception category chart
st.subheader("Exception Categories")

if not matches.empty:

    failed = matches[matches["result"] == "FAIL"]

    if not failed.empty:

        exception_data = (
            failed["check_type"]
            .value_counts()
            .reset_index()
        )

        exception_data.columns = ["Exception Type", "Count"]

        fig2 = px.bar(
            exception_data,
            x="Exception Type",
            y="Count",
            title="Failed Matching Checks",
            text="Count"
        )

        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.success("No failed matching checks.")

# Approval status
st.subheader("Approval Status")

if not approvals.empty:

    approval_data = (
        approvals["decision"]
        .value_counts()
        .reset_index()
    )

    approval_data.columns = ["Decision", "Count"]

    fig3 = px.bar(
        approval_data,
        x="Decision",
        y="Count",
        title="Invoice Approval Status"
    )

    st.plotly_chart(fig3, width="stretch")

# Invoice records
st.subheader("Invoice Records")

st.dataframe(
    invoices,
    width="stretch"
)

# Exception records
st.subheader("Exception Records")

if not matches.empty:

    failed_records = matches[
        matches["result"] == "FAIL"
    ]

    st.dataframe(
        failed_records,
        width="stretch"
    )
# Payment Records
st.subheader("Payment Records")

if not payments.empty:

    st.dataframe(
        payments,
        width="stretch"
    )
# Approval Records
st.subheader("Approval Records")
total_approvals = len(approvals)
pending_approvals = len(approvals[approvals["decision"] == "PENDING"])
approved_approvals = len(approvals[approvals["decision"] == "APPROVED"])
rejected_approvals = len(approvals[approvals["decision"] == "REJECTED"])

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Approvals", total_approvals)
col2.metric("Pending Approvals", pending_approvals)
col3.metric("Approved Approvals", approved_approvals)
col4.metric("Rejected Approvals", rejected_approvals)

if not approvals.empty:

    approval_filter = st.selectbox(
        "Filter Approval Status",
        ["ALL", "PENDING", "APPROVED", "REJECTED"]
    )

    if approval_filter != "ALL":
        filtered_approvals = approvals[
            approvals["decision"] == approval_filter
        ]
    else:
        filtered_approvals = approvals

    st.dataframe(filtered_approvals, width="stretch")
    st.write("Approved records found:", len(filtered_approvals))

else:
    st.info("No approval records found.")
# Audit History
st.divider()
st.subheader("📜 Invoice Audit History")

if not events.empty:
    st.dataframe(events, width="stretch")
else:
    st.info("No audit history records found.")    
st.success("Dashboard loaded successfully!")
