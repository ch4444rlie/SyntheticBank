import os
import re
import base64
import json
from faker import Faker
from datetime import datetime, timedelta
import random
import pandas as pd
from pydantic import BaseModel, Field
from typing import List, Dict
from jinja2 import Environment, FileSystemLoader
import pdfkit

# Initialize Faker
fake = Faker()

# Directory setup
SAMPLE_LOGOS_DIR = "sample_logos"
SYNTHETIC_STAT_DIR = "synthetic_statements"
TEMPLATES_DIR = "templates"

# Create directories if they don’t exist
for directory in [SAMPLE_LOGOS_DIR, SYNTHETIC_STAT_DIR, TEMPLATES_DIR]:
    os.makedirs(directory, exist_ok=True)

# Bank configuration
BANK_CONFIG = {
    "chase": {
        "logo": "chase_bank_logo.png",
        "templates": ["chase_classic_style.html", "chase_variation_1.html", "chase_variation_2.html"]
    },
    "citibank": {
        "logo": "citibank_logo.png",
        "templates": ["citibank_classic_template.html", "citibank_variation_1.html", "citibank_variation_2.html"]
    },
    "wellsfargo": {
        "logo": "wellsfargo_logo.png",
        "templates": ["wells_fargo_classic.html", "wells_variation_1.html", "wells_variation_2.html"]
    },
    "pnc": {
        "logo": "pnc_logo.png",
        "templates": ["pnc_classic.html"]
    }
}

# Pydantic models
class FieldDefinition(BaseModel):
    name: str = Field(..., description="Field name")
    is_mutable: bool = Field(..., description="Whether the field is mutable")
    description: str = Field(..., description="Description of the field")

class StatementFields(BaseModel):
    fields: List[FieldDefinition] = Field(..., description="List of mutable and immutable fields")

class Transaction(BaseModel):
    description: str = Field(..., max_length=35, description="Transaction description")
    category: str
    amount: float
    account_type: str

# Predefined transaction categories and descriptions
BUSINESS_CATEGORIES = {
    "loss": [
        ("Vendor Payment", ["Vendor Invoice Payment", "Supplier Payment", "Service Fee", "Contractor Payment"]),
        ("Payroll Expense", ["Employee Salary", "Payroll Distribution", "Staff Wages", "Bonus Payment"]),
        ("Office Supplies", ["Office Supply Purchase", "Stationery Order", "Equipment Rental", "Supply Restock"]),
        ("Equipment Purchase", ["Machinery Purchase", "Hardware Acquisition", "Tool Purchase", "Equipment Upgrade"]),
        ("Marketing Cost", ["Advertising Expense", "Marketing Campaign", "Promo Materials", "Digital Ad Spend"])
    ],
    "gain": [
        ("Client Invoice", ["Client Payment Received", "Invoice Settlement", "Customer Payment", "Service Revenue"]),
        ("Refund Received", ["Vendor Refund", "Overpayment Refund", "Return Credit", "Reimbursement"]),
        ("Investment Income", ["Dividend Payment", "Interest Income", "Investment Return", "Profit Share"]),
        ("Grant Received", ["Business Grant", "Funding Received", "Grant Disbursement", "Award Payment"]),
        ("Sales Revenue", ["Product Sales", "Service Sales", "Retail Revenue", "Online Sales"])
    ]
}

PERSONAL_CATEGORIES = {
    "loss": [
        ("Utility Payment", ["Electric Bill Payment", "Water Bill Payment", "Internet Bill", "Phone Bill"]),
        ("Subscription Fee", ["Streaming Service", "Gym Membership", "Magazine Subscription", "Software License"]),
        ("Online Purchase", ["Ecommerce Purchase", "Online Retail", "Shopping Delivery", "Web Order"]),
        ("Rent Payment", ["Monthly Rent", "Apartment Lease", "Housing Payment", "Landlord Payment"]),
        ("Grocery Shopping", ["Grocery Store Purchase", "Supermarket Bill", "Food Shopping", "Market Purchase"])
    ],
    "gain": [
        ("Salary Deposit", ["Paycheck Deposit", "Wage Deposit", "Salary Credit", "Job Payment"]),
        ("Tax Refund", ["Tax Return Credit", "Refund Deposit", "IRS Refund", "State Tax Refund"]),
        ("Gift Received", ["Gift Money", "Cash Gift", "Family Support", "Personal Gift"]),
        ("Client Payment", ["Freelance Payment", "Consulting Fee", "Service Payment", "Project Payment"]),
        ("Cash Deposit", ["Cash Deposit", "ATM Deposit", "Bank Deposit", "Personal Savings"])
    ]
}

# Generate category lists
def generate_category_lists(account_type: str) -> tuple[List[str], List[str]]:
    categories = BUSINESS_CATEGORIES if account_type == "business" else PERSONAL_CATEGORIES
    loss_categories = [cat[0] for cat in categories["loss"]]
    gain_categories = [cat[0] for cat in categories["gain"]]
    return loss_categories, gain_categories

# Generate transaction description
def generate_transaction_description(amount: float, category: str, account_type: str) -> dict:
    categories = BUSINESS_CATEGORIES if account_type == "business" else PERSONAL_CATEGORIES
    description_list = next((cat[1] for cat in (categories["loss"] + categories["gain"]) if cat[0] == category), [f"{category} Transaction"])
    description = random.choice(description_list)[:35]
    description = ' '.join(word.capitalize() for word in description.split())
    transaction = Transaction(description=description, category=category, amount=amount, account_type=account_type)
    return transaction.model_dump()

# Generate synthetic bank statement
def generate_bank_statement(num_transactions: int, account_holder: str, account_type: str) -> pd.DataFrame:
    if account_type not in ["business", "personal"]:
        raise ValueError("Account type must be 'business' or 'personal'")
    loss_categories, gain_categories = generate_category_lists(account_type)
    start_date = datetime.now() - timedelta(days=30)
    dates = [start_date + timedelta(days=random.randint(0, 30)) for _ in range(num_transactions)]
    transactions = []
    for _ in range(num_transactions):
        is_gain = random.choice([True, False])
        category = random.choice(gain_categories if is_gain else loss_categories)
        amount = round(random.uniform(50, 1000), 2) if is_gain else round(random.uniform(-500, -10), 2)
        transaction = generate_transaction_description(amount, category, account_type)
        transactions.append(transaction)
    data = {
        "Date": [d.strftime("%m/%d") for d in dates],
        "Description": [t["description"] for t in transactions],
        "Category": [t["category"] for t in transactions],
        "Amount": [t["amount"] for t in transactions],
        "Balance": [0.0] * num_transactions,
        "Account Holder": [account_holder] * num_transactions,
        "Account Type": [account_type.capitalize()] * num_transactions,
        "Transaction ID": [(fake.bban()[:10] + str(i).zfill(4)) for i in range(num_transactions)]
    }
    df = pd.DataFrame(data)
    df = df.sort_values("Date")
    initial_balance = round(random.uniform(1000, 20000), 2)
    df["Balance"] = initial_balance + df["Amount"].cumsum()
    return df

# Identify mutable and immutable fields
def identify_template_fields(bank: str, templates_dir: str = TEMPLATES_DIR) -> StatementFields:
    if bank not in BANK_CONFIG:
        raise ValueError(f"Unsupported bank: {bank}. Supported banks: {list(BANK_CONFIG.keys())}")
    
    template_path = os.path.join(templates_dir, BANK_CONFIG[bank]["templates"][0])
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    placeholders = re.findall(r'\{\{([^{}]+)\}\}', template_content)
    placeholders = [p.strip() for p in placeholders]
    
    default_fields = [
        FieldDefinition(name="account_holder", is_mutable=True, description="Name of the account holder"),
        FieldDefinition(name="account_holder_address", is_mutable=True, description="Address of the account holder"),
        FieldDefinition(name="account_number", is_mutable=True, description="Account number"),
        FieldDefinition(name="statement_period", is_mutable=True, description="Statement date range"),
        FieldDefinition(name="statement_date", is_mutable=True, description="Date the statement was created"),
        FieldDefinition(name="transactions", is_mutable=True, description="List of transaction details"),
        FieldDefinition(name="opening_balance", is_mutable=True, description="Opening balance"),
        FieldDefinition(name="total_debit", is_mutable=True, description="Total debit amount"),
        FieldDefinition(name="total_credit", is_mutable=True, description="Total credit amount"),
        FieldDefinition(name="total", is_mutable=True, description="Total balance"),
        FieldDefinition(name="logo_path", is_mutable=True, description="Path to the bank logo"),
        FieldDefinition(name="important_info", is_mutable=True, description="Important account information"),
        FieldDefinition(name="summary", is_mutable=True, description="Summary of account details (e.g., balances, transactions)"),
        FieldDefinition(name="daily_balances", is_mutable=True, description="Daily balance details"),
        FieldDefinition(name="deposits", is_mutable=True, description="Deposit transactions"),
        FieldDefinition(name="withdrawals", is_mutable=True, description="Withdrawal transactions"),
        FieldDefinition(name="bank_name", is_mutable=False, description=f"Name of the bank ({bank.capitalize()})"),
        FieldDefinition(name="bank_address", is_mutable=False, description="Bank address"),
        FieldDefinition(name="customer_service", is_mutable=False, description="Customer service contact information"),
        FieldDefinition(name="footnotes", is_mutable=False, description="Footnotes and disclosures")
    ]
    statement_fields = StatementFields(fields=[f for f in default_fields if f.name in placeholders or f.name in template_content])
    
    log_path = os.path.join(SYNTHETIC_STAT_DIR, f"template_fields_{bank}.json")
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(statement_fields.model_dump(), f, indent=2)
    
    return statement_fields

# Generate populated HTML and PDF
def generate_populated_html_and_pdf(df: pd.DataFrame, account_holder: str, bank: str, template_dir: str, output_dir: str, account_type: str, template_name: str) -> list:
    if bank not in BANK_CONFIG:
        raise ValueError(f"Unsupported bank: {bank}. Supported banks: {list(BANK_CONFIG.keys())}")
    if template_name not in BANK_CONFIG[bank]["templates"]:
        raise ValueError(f"Template {template_name} not supported for {bank}")
    
    env = Environment(loader=FileSystemLoader(template_dir))
    
    initial_balance = round(random.uniform(1000, 20000), 2)
    deposits_total = sum(x for x in df['Amount'] if x > 0)
    withdrawals_total = abs(sum(x for x in df['Amount'] if x < 0))
    ending_balance = initial_balance + deposits_total - withdrawals_total
    service_fee = 25 if ending_balance < 5000 else 0
    if service_fee:
        withdrawals_total += service_fee
        ending_balance -= service_fee
    
    # Calculate statement period
    min_date = datetime.strptime(min(df['Date']), "%m/%d").replace(year=2025)
    max_date = datetime.strptime(max(df['Date']), "%m/%d").replace(year=2025)
    statement_date = datetime.now().strftime("%B %d, %Y at %I:%M %p %Z")
    
    address = fake.address().replace('\n', '<br>')[:100]
    account_holder = account_holder[:50]
    account_number = fake.bban()[:15]
    
    logo_path = os.path.join(SAMPLE_LOGOS_DIR, BANK_CONFIG[bank]["logo"])
    logo_data = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            logo_data = f"data:image/png;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
    
    # Important account information
    important_info = """
    <h3>Important Account Information</h3>
    <p>Thank you for banking with us. Please review your statement carefully. If you have any questions or notice any discrepancies, contact our customer service at 1-800-555-1234. For your security, do not share your account details. Visit our website for tips on protecting your account.</p>
    """
    if account_type == "business":
        if bank == "chase":
            important_info = f"""
            <h3>Important Account Information</h3>
            <p>Effective July 1, 2025, the monthly service fee for {account_type.capitalize()} {bank.capitalize()} Complete Checking accounts will increase to $20 unless you maintain a minimum daily balance of $2,000, have $2,000 in net purchases on a {bank.capitalize()} Business Debit Card, or maintain linked {bank.capitalize()} business accounts with a combined balance of $10,000.</p>
            <p>Starting June 30, 2025, {bank.capitalize()} will offer enhanced cash flow tools for {account_type.capitalize()} Complete Checking accounts via {bank.capitalize()} Online, including automated invoice tracking and payment scheduling.</p>
            <p>Effective July 15, 2025, {bank.capitalize()} will reduce wire transfer fees to $25 for domestic transfers for {account_type.capitalize()} Complete Checking accounts, down from $30.</p>
            <p>For questions, visit your local {bank.capitalize()} Branch or call the {bank.capitalize()} Customer Care Center at <b>1-800-242-7338</b>, available 24/7.</ superfamily</p>
            """
        # ... (rest of the important_info for other banks unchanged)
    else:  # Personal
        if bank == "chase":
            important_info = f"""
            <h3>Important Account Information</h3>
            <p>Effective July 1, 2025, the monthly service fee for {account_type.capitalize()} {bank.capitalize()} Total Checking accounts will increase to $15 unless you maintain a minimum daily balance of $1,500, have $500 in qualifying direct deposits, or maintain a linked {bank.capitalize()} savings account with a balance of $5,000 or more.</p>
            <p>Starting June 30, 2025, {bank.capitalize()} will introduce real-time transaction alerts for {account_type.capitalize()} Total Checking accounts via the {bank.capitalize()} Mobile app to enhance account monitoring. Enable alerts at chase.com/alerts.</p>
            <p>Effective July 15, 2025, {bank.capitalize()} will waive overdraft fees for transactions of $5 or less and cap daily overdraft fees at two per day for {account_type.capitalize()} Total Checking accounts.</p>
            <p>For questions, visit your local {bank.capitalize()} Branch or call the {bank.capitalize()} Customer Care Center at <b>1-800-242-7338</b>, available 24/7.</p>
            """
        # ... (rest of the important_info for other banks unchanged)

    if bank == "citibank":
        transactions = []
        total_debit = abs(sum(x for x in df['Amount'] if x < 0))
        total_credit = sum(x for x in df['Amount'] if x > 0)
        running_balance = initial_balance
        for _, row in df.iterrows():
            amount = row['Amount']
            debit = f"£{abs(amount):,.2f}" if amount < 0 else ""
            credit = f"£{amount:,.2f}" if amount > 0 else ""
            running_balance += amount
            transactions.append({
                "date": row["Date"],
                "description": row["Description"],
                "debit": debit,
                "credit": credit,
                "balance": f"£{running_balance:,.2f}"
            })
        template_data = {
            "account_holder": account_holder,
            "client_number": fake.uuid4()[:8],
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80).strftime("%m/%d/%Y"),
            "customer_account_number": account_number,
            "customer_iban": f"GB{fake.random_number(digits=2)}CITI{fake.random_number(digits=14)}",
            "customer_bank_name": "Citibank",
            "statement_period": f"{min_date.strftime('%B %d')} through {max_date.strftime('%B %d')}",
            "statement_date": statement_date,
            "opening_balance": f"£{initial_balance:,.2f}",
            "transactions": transactions,
            "total_debit": f"£{total_debit:,.2f}",
            "total_credit": f"£{total_credit:,.2f}",
            "total": f"£{ending_balance:,.2f}",
            "logo_path": logo_data,
            "important_info": important_info,
            "account_type": account_type.capitalize()
        }
    elif bank in ["wellsfargo", "pnc"]:
        transactions = []
        running_balance = initial_balance
        for _, row in df.iterrows():
            amount = row['Amount']
            transaction_type = "deposit" if amount > 0 else "electronic" if random.choice([True, False]) else "other"
            deposits_credits = f"${amount:,.2f}" if amount > 0 else ""
            withdrawals_debits = f"${abs(amount):,.2f}" if amount < 0 else ""
            running_balance += amount
            transactions.append({
                "date": row["Date"],
                "description": row["Description"],
                "deposits_credits": deposits_credits,
                "withdrawals_debits": withdrawals_debits,
                "ending_balance": f"${running_balance:,.2f}",
                "type": transaction_type
            })
        daily_balances = [
            {"date": row["Date"], "amount": f"${row['Balance']:,.2f}"}
            for _, row in df.drop_duplicates(subset="Date").iterrows()
        ]
        summary = {
            "beginning_balance": f"${initial_balance:,.2f}",
            "deposits_total": f"${deposits_total:,.2f}",
            "withdrawals_total": f"${withdrawals_total:,.2f}",
            "ending_balance": f"${ending_balance:,.2f}",
            "deposits_count": sum(1 for x in df['Amount'] if x > 0),
            "withdrawals_count": sum(1 for x in df['Amount'] if x < 0) + (1 if service_fee else 0),
            "transactions_count": len(df),
            "average_balance": f"${round((initial_balance + ending_balance) / 2, 2):,.2f}",
            "fees": f"${service_fee:,.2f}",
            "checks_written": random.randint(0, 5),
            "pos_transactions": random.randint(0, 10),
            "pos_pin_transactions": random.randint(0, 5),
            "total_atm_transactions": random.randint(0, 8),
            "pnc_atm_transactions": random.randint(0, 5) if bank == "pnc" else 0,
            "other_atm_transactions": random.randint(0, 3),
            "apy_earned": f"{random.uniform(0.01, 0.5):.2f}%" if bank in ["wellsfargo", "pnc"] else "0.00%",
            "days_in_period": random.randint(28, 31),
            "average_collected_balance": f"${round(random.uniform(initial_balance, ending_balance), 2):,.2f}",
            "interest_paid_period": f"${random.uniform(0.1, 10):,.2f}" if bank in ["wellsfargo", "pnc"] else "$0.00",
            "interest_paid_ytd": f"${random.uniform(1, 50):,.2f}" if bank in ["wellsfargo", "pnc"] else "$0.00",
            "overdraft_protection1": f"{bank.capitalize()} Savings Account XXXX1234" if random.choice([True, False]) else "",
            "overdraft_protection2": f"{bank.capitalize()} Credit Line XXXX5678" if random.choice([True, False]) else "",
            "overdraft_status": "Opted-In" if random.choice([True, False]) else "Opted-Out"
        }
        template_data = {
            "account_holder": account_holder,
            "account_holder_address": address,
            "account_number": account_number,
            "statement_period": f"{min_date.strftime('%B %d')}, 2025 – {max_date.strftime('%B %d')}, 2025",
            "statement_date": statement_date,
            "logo_path": logo_data,
            "important_info": important_info,
            "summary": summary,
            "transactions": transactions,
            "daily_balances": daily_balances,
            "account_type": account_type.capitalize()
        }
    else:  # Chase
        deposits = [
            {"date": row["Date"], "description": row["Description"], "amount": f"${row['Amount']:,.2f}"}
            for _, row in df.iterrows() if row['Amount'] > 0
        ]
        withdrawals = [
            {"date": row["Date"], "description": row["Description"], "amount": f"${abs(row['Amount']):,.2f}"}
            for _, row in df.iterrows() if row['Amount'] < 0
        ]
        # Generate daily balances for every day in the statement period
        statement_start = min_date
        statement_end = max_date
        day_delta = timedelta(days=1)
        balance_map = {}
        running_balance = initial_balance
        current_date = statement_start
        df = df.sort_values("Date")  # Ensure DataFrame is sorted
        transaction_index = 0
        while current_date <= statement_end:
            iso_date = current_date.isoformat()
            # Check if there are transactions on this date
            daily_transactions = df[df["Date"] == current_date.strftime("%m/%d")]
            if not daily_transactions.empty:
                # Sum all transactions for this date
                daily_amount = daily_transactions["Amount"].sum()
                running_balance += daily_amount
            balance_map[iso_date] = f"${running_balance:,.2f}"
            current_date += day_delta
        
        daily_balances = [
            {"date": row["Date"], "amount": f"${row['Balance']:,.2f}"}
            for _, row in df.drop_duplicates(subset="Date").iterrows()
        ]
        summary = {
            "beginning_balance": f"${initial_balance:,.2f}",
            "deposits_count": len(deposits),
            "deposits_total": f"${deposits_total:,.2f}",
            "withdrawals_count": len(withdrawals) + (1 if service_fee else 0),
            "withdrawals_total": f"${withdrawals_total:,.2f}",
            "ending_balance": f"${ending_balance:,.2f}",
            "average_balance": f"${round((initial_balance + ending_balance) / 2, 2):,.2f}",
            "fees": f"${service_fee:,.2f}",
            "checks_written": random.randint(0, 5),
            "pos_transactions": random.randint(0, 10),
            "pos_pin_transactions": random.randint(0, 5),
            "total_atm_transactions": random.randint(0, 8),
            "pnc_atm_transactions": 0,
            "other_atm_transactions": random.randint(0, 3),
            "apy_earned": "0.00%",
            "days_in_period": random.randint(28, 31),
            "average_collected_balance": f"${round(random.uniform(initial_balance, ending_balance), 2):,.2f}",
            "interest_paid_period": "$0.00",
            "interest_paid_ytd": "$0.00",
            "overdraft_protection1": "Chase Savings Account XXXX1234" if random.choice([True, False]) else "",
            "overdraft_protection2": "Chase Credit Line XXXX5678" if random.choice([True, False]) else "",
            "overdraft_status": "Opted-In" if random.choice([True, False]) else "Opted-Out"
        }
        template_data = {
            "account_holder": account_holder,
            "account_holder_address": address,
            "account_number": account_number,
            "statement_period": f"{min_date.strftime('%B %d')} through {max_date.strftime('%B %d')}",
            "statement_date": statement_date,
            "logo_path": logo_data,
            "important_info": important_info,
            "summary": summary,
            "deposits": deposits,
            "withdrawals": withdrawals,
            "daily_balances": daily_balances,
            "show_fee_waiver": service_fee == 0,
            "account_type": account_type.capitalize(),
            "statement_start": statement_start,
            "statement_end": statement_end,
            "day_delta": day_delta,
            "balance_map": balance_map
        }
    
    template = env.get_template(template_name)
    template_name_base = os.path.splitext(template_name)[0]
    html_filename = os.path.join(output_dir, f"bank_statement_{account_type.upper()}_{account_holder.replace(' ', '_')}_{bank}_{template_name_base}.html")
    pdf_filename = os.path.join(output_dir, f"bank_statement_{account_type.upper()}_{account_holder.replace(' ', '_')}_{bank}_{template_name_base}.pdf")
    
    rendered_html = template.render(**template_data)
    
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(rendered_html)
    
    wkhtmltopdf_path = os.environ.get("WKHTMLTOPDF_PATH", "/usr/bin/wkhtmltopdf")
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
    options = {
        "enable-local-file-access": "",
        "page-size": "Letter",
        "margin-top": "0.8in",
        "margin-right": "0.9in",
        "margin-bottom": "0.8in",
        "margin-left": "0.9in",
        "encoding": "UTF-8",
        "disable-javascript": "",
        "image-dpi": "300",
        "enable-forms": "",
        "no-outline": "",
        "print-media-type": "",
        "minimum-font-size": "10"
    }
    try:
        pdfkit.from_string(rendered_html, pdf_filename, configuration=config, options=options)
        return [(html_filename, pdf_filename)]
    except OSError as e:
        raise Exception(f"PDF generation failed for {bank} template {template_name}: {e}")