import streamlit as st
import os
from datetime import datetime
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from pdfkit import from_string
import base64

# Set up Jinja2 environment
template_dir = "templates"
env = Environment(loader=FileSystemLoader(template_dir))

# App title and configuration
st.set_page_config(page_title="Fancy Bank Statement Generator", layout="wide")
st.title("Fancy Bank Statement Generator")

# Sidebar for data input
st.sidebar.header("Statement Data")
account_holder = st.sidebar.text_input("Account Holder Name", "John Doe")
account_number = st.sidebar.text_input("Account Number", "1234567890")
account_type = st.sidebar.selectbox("Account Type", ["Personal", "Business"])
statement_period = st.sidebar.text_input("Statement Period", "June 1, 2025 - June 30, 2025")
statement_date = st.sidebar.text_input("Statement Date", "June 26, 2025 10:23 AM CDT")  # Updated to current date/time
logo_path = st.sidebar.text_input("Logo Path", "logo.png")

# Transaction data input
st.sidebar.subheader("Transaction Data")
transactions_data = st.sidebar.file_uploader("Upload Transactions CSV", type="csv")
if transactions_data:
    transactions_df = pd.read_csv(transactions_data)
else:
    transactions_df = pd.DataFrame({
        "date": ["2025-06-01", "2025-06-15", "2025-06-30"],
        "description": ["Salary Deposit", "Grocery Purchase", "Utility Bill"],
        "deposits_credits": ["1000.00", "", "500.00"],
        "withdrawals_debits": ["", "150.00", "200.00"],
        "ending_balance": ["1000.00", "850.00", "1150.00"]
    })

# Summary data
st.sidebar.subheader("Summary Data")
summary = {
    "beginning_balance": st.sidebar.text_input("Beginning Balance", "0.00"),
    "deposits_total": st.sidebar.text_input("Total Deposits", "1500.00"),
    "withdrawals_total": st.sidebar.text_input("Total Withdrawals", "350.00"),
    "ending_balance": st.sidebar.text_input("Ending Balance", "1150.00"),
    "deposits_count": st.sidebar.number_input("Deposit Instances", min_value=0, value=2),
    "withdrawals_count": st.sidebar.number_input("Withdrawal Instances", min_value=0, value=2),
    "transactions_count": st.sidebar.number_input("Total Transactions", min_value=0, value=4)
}
show_fee_waiver = st.sidebar.checkbox("Show Fee Waiver", value=False)

# Important account information (simulated for now)
important_account_info = """
<p>Between May 1, 2025, and September 30, 2025, Citibank will discontinue mobile check deposits. Use Online Banking or visit a branch.</p>
<p>Effective June 22, 2025, the fee for expedited funds will increase from 1.5% to 2.0% for amounts over $100.</p>
<p>Contact us at 1-800-374-9700 within 60 days for statement errors, per Regulation E.</p>
<p>Funds availability for deposits will increase to $500 on the first day starting June 15, 2025; large deposits may be held up to 7 days.</p>
<p>Enable Citibank Mobile’s new budgeting tools and alerts at citibank.com/mobile.</p>
<p>Monthly service fees for Citibank accounts will rise to $12.95 on July 1, 2025, unless a $1,000 balance is maintained.</p>
<p>Biometric login for mobile banking starts July 1, 2025—set up at citibank.com/security.</p>
<p>For support, call 1-800-374-9700 or visit a branch; Spanish support at 1-800-248-4231.</p>
""" if account_type == "Personal" else """
<p>Effective June 22, 2025, the monthly fee for Citibank Business Checking will increase to $25 unless a $5,000 balance is maintained.</p>
<p>Citibank Business Online now offers payroll integration and cash flow tools—enroll at citibank.com/business.</p>
<p>Wire transfer fees will rise to $35 for domestic and $50 for international starting June 30, 2025.</p>
<p>Transactions over $10,000 may be reported to the IRS; contact 1-800-374-9700 for details.</p>
<p>Business Rewards Program launches August 1, 2025, with 1% cash back on $5,000 monthly card use.</p>
<p>Same-day ACH settlement available from July 15, 2025—contact us to enable.</p>
<p>New expense tracking tool for business accounts launches July 1, 2025, at citibank.com/business-tools.</p>
<p>For support, call 1-800-374-9700 (Mon-Fri 8 AM-6 PM) or visit citibank.com/business.</p>
"""

# Footnotes and disclosures (simulated)
footnotes = "<p><strong>1.</strong> Privacy details at citibank.com/privacy.</p>"
disclosures = "<p><strong>2.</strong> Fees may apply; see citibank.com/fees.</p>"
terms = "<p><strong>3.</strong> Terms subject to change; visit citibank.com/terms.</p>"

# Bank and template selection
st.header("Generate Statement")
banks = ["chase", "citibank", "wells_fargo"]
bank = st.selectbox("Select Bank", banks)

# Dynamically load template variations from the bank subdirectory
template_dir = os.path.join(template_dir, bank)
if os.path.exists(template_dir):
    variations = [f for f in os.listdir(template_dir) if f.endswith(".html")]
    if variations:
        selected_variations = st.multiselect("Select Variations", variations, default=variations[0],
                                           format_func=lambda x: x.replace(".html", "").replace("_", " ").title())
    else:
        st.error(f"No template files found in {template_dir}")
else:
    st.error(f"Template directory {template_dir} does not exist")
    variations = []
    selected_variations = []

# Generate PDF button
if st.button("Generate PDF") and selected_variations:
    for variation in selected_variations:
        template_path = os.path.join(template_dir, variation)
        if os.path.exists(template_path):
            template = env.get_template(template_path)

            # Prepare data for template
            data = {
                "account_holder": account_holder,
                "account_number": account_number,
                "account_type": account_type,
                "statement_period": statement_period,
                "statement_date": statement_date,
                "logo_path": logo_path,
                "transactions": transactions_df.to_dict(orient="records"),
                "summary": summary,
                "show_fee_waiver": show_fee_waiver,
                "important_account_info": important_account_info,
                "footnotes": footnotes,
                "disclosures": disclosures,
                "terms": terms,
                "customer_account_number": account_number,  # For Citibank compatibility
                "customer_iban": "GB29NWBK60161331926819",  # Placeholder
                "customer_bank_name": "Citibank UK Limited",  # Placeholder
                "client_number": "C123456",  # Placeholder
                "date_of_birth": "1990-01-01",  # Placeholder
                "opening_balance": summary["beginning_balance"],
                "opening_balance_debit": "0.00",  # Placeholder
                "opening_balance_credit": summary["beginning_balance"],  # Placeholder
                "total_debit": summary["withdrawals_total"],
                "total_credit": summary["deposits_total"],
                "total": summary["ending_balance"]
            }

            # Render template
            html_content = template.render(data)

            # Generate PDF
            pdf = from_string(html_content, False)
            pdf_filename = f"{bank}_{variation.replace('.html', '')}_{account_number}.pdf"
            with open(pdf_filename, "wb") as f:
                f.write(pdf)

            # Provide download link
            b64 = base64.b64encode(pdf).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="{pdf_filename}">Download {variation.replace(".html", "").replace("_", " ").title()} PDF</a>'
            st.markdown(href, unsafe_allow_html=True)
        else:
            st.error(f"Template file {template_path} not found")

