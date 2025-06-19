import os
import json
import re
import base64
from faker import Faker
from datetime import datetime, timedelta
import random
import pandas as pd
from pydantic import BaseModel, Field
from typing import List, Dict
from jinja2 import Environment, FileSystemLoader
import pdfkit

fake = Faker()

SAMPLE_STATEMENT_DIR = "sample_statements"
SAMPLE_LOGOS_DIR = "sample_logos"
SYNTHETIC_STAT_DIR = "synthetic_statements"
TEMPLATES_DIR = "templates"

for directory in [SAMPLE_STATEMENT_DIR, SAMPLE_LOGOS_DIR, SYNTHETIC_STAT_DIR, TEMPLATES_DIR]:
    os.makedirs(directory, exist_ok=True)

BANK_CONFIG = {
    "chase": {"logo": "chase_bank_logo.png", "templates": ["chase_mail_style.html", "chase_website_style.html", "chase_app_style.html"]},
    "citibank": {"logo": "citibank_logo.png", "templates": ["citibank_classic_template.html", "citibank_website_style.html", "citibank_app_style.html"]},
    "wellsfargo": {"logo": "wellsfargo_logo.png", "templates": ["wells_fargo_complete_advantage_checking.html", "wells_fargo_app_style.html", "wells_fargo_web_style.html"]},
    "pnc": {"logo": "pnc_logo.png", "templates": ["pnc_main.html"]}
}

class FieldDefinition(BaseModel):
    name: str
    is_mutable: bool
    description: str

class StatementFields(BaseModel):
    fields: List[FieldDefinition]

class Transaction(BaseModel):
    description: str
    category: str
    amount: float

def generate_category_lists() -> tuple[List[str], List[str]]:
    loss_categories = ["Utility Payment", "Subscription Fee", "Online Purchase", "Rent Payment", "Grocery Shopping"]
    gain_categories = ["Salary Deposit", "Tax Refund", "Gift Received", "Client Payment", "Cash Deposit"]
    return loss_categories, gain_categories

def generate_transaction_description(amount: float, category: str) -> dict:
    description = f"{category} Transaction"[:25]
    description = ' '.join(word.capitalize() for word in description.split())[:25]
    words = description.split()
    if len(words) < 3 or len(words) > 5:
        description = f"{category} Transaction"[:45]
    transaction = Transaction(description=description, category=category, amount=amount)
    return transaction.dict()

def generate_bank_statement(num_transactions: int, account_holder: str) -> pd.DataFrame:
    loss_categories, gain_categories = generate_category_lists()
    start_date = datetime.now() - timedelta(days=30)
    dates = [start_date + timedelta(days=random.randint(0, 30)) for _ in range(num_transactions)]
    transactions = []
    for _ in range(num_transactions):
        is_gain = random.choice([True, False])
        category = random.choice(gain_categories if is_gain else loss_categories)
        amount = round(random.uniform(50, 1000), 2) if is_gain else round(random.uniform(-500, -10), 2)
        transaction = generate_transaction_description(amount, category)
        transactions.append(transaction)
    data = {
        "Date": [d.strftime("%m/%d") for d in dates],
        "Description": [t["description"] for t in transactions],
        "Category": [t["category"] for t in transactions],
        "Amount": [t["amount"] for t in transactions],
        "Balance": [0.0] * num_transactions,
        "Account Holder": [account_holder] * num_transactions,
        "Transaction ID": [(fake.bban()[:10] + str(i).zfill(4)) for i in range(num_transactions)]
    }
    df = pd.DataFrame(data)
    df = df.sort_values("Date")
    initial_balance = round(random.uniform(1000, 20000), 2)
    df["Balance"] = initial_balance + df["Amount"].cumsum()
    return df

def identify_template_fields(template_path: str) -> StatementFields:
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template file not found: {template_path}")
    
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    placeholders = re.findall(r'\{\{([^{}]+)\}\}', template_content)
    placeholders = [p.strip() for p in placeholders]
    
    default_fields = [
        FieldDefinition(name="account_holder", is_mutable=True, description="Name of the account holder"),
        FieldDefinition(name="account_holder_address", is_mutable=True, description="Address of the account holder"),
        FieldDefinition(name="account_number", is_mutable=True, description="Account number"),
        FieldDefinition(name="statement_period", is_mutable=True, description="Statement date range"),
        FieldDefinition(name="summary", is_mutable=True, description="Summary data (e.g., balances, counts, totals)"),
        FieldDefinition(name="transactions", is_mutable=True, description="List of transactions"),
        FieldDefinition(name="daily_balances", is_mutable=True, description="Daily ending balances"),
        FieldDefinition(name="logo_path", is_mutable=True, description="Path to the bank logo"),
        FieldDefinition(name="total_pages", is_mutable=True, description="Total number of pages"),
        FieldDefinition(name="current_page", is_mutable=True, description="Current page number"),
        FieldDefinition(name="bank_name", is_mutable=False, description="Name of the bank"),
        FieldDefinition(name="bank_address", is_mutable=False, description="Bank address"),
        FieldDefinition(name="customer_service", is_mutable=False, description="Customer service contact information"),
        FieldDefinition(name="footnotes", is_mutable=False, description="Footnotes and disclosures")
    ]
    statement_fields = StatementFields(fields=[f for f in default_fields if f.name in placeholders or f.name in template_content])
    
    log_path = os.path.join(SYNTHETIC_STAT_DIR, "template_fields.json")
    with open(log_path, 'w') as f:
        json.dump(statement_fields.model_dump(), f, indent=2)
    
    return statement_fields

def generate_populated_html_and_pdf(df: pd.DataFrame, account_holder: str, bank: str, template_dir: str, output_dir: str) -> list:
    if bank not in BANK_CONFIG:
        raise ValueError(f"Unsupported bank: {bank}. Supported banks: {list(BANK_CONFIG.keys())}")
    
    env = Environment(loader=FileSystemLoader(template_dir))
    
    initial_balance = round(random.uniform(1000, 20000), 2)
    deposits_total = sum(x for x in df['Amount'] if x > 0)
    withdrawals_total = abs(sum(x for x in df['Amount'] if x < 0))
    ending_balance = initial_balance + deposits_total - withdrawals_total
    service_fee = 25 if ending_balance < 5000 else 0
    if service_fee:
        withdrawals_total += service_fee
        ending_balance -= service_fee
    
    transactions_count = len(df)
    
    min_date = datetime.strptime(min(df['Date']), "%m/%d").replace(year=2025).strftime("%B %d")
    max_date = datetime.strptime(max(df['Date']), "%m/%d").replace(year=2025).strftime("%B %d")
    statement_date = datetime.now().strftime("%B %d, %Y at %I:%M %p %Z")  # e.g., June 19, 2025 at 03:09 PM CDT
    
    address = fake.address().replace('\n', '<br>')[:100]
    account_holder = account_holder[:50]
    account_number = fake.bban()[:15]
    
    logo_path = os.path.join(SAMPLE_LOGOS_DIR, BANK_CONFIG[bank]["logo"])
    logo_data = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            logo_data = f"data:image/png;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
    
    if bank == "citibank":
        transactions = []
        total_debit = abs(sum(x for x in df['Amount'] if x < 0))
        total_credit = sum(x for x in df['Amount'] if x > 0)
        running_balance = initial_balance
        for _, row in df.iterrows():
            amount = row['Amount']
            debit = f"${abs(amount):,.2f}" if amount < 0 else ""
            credit = f"${amount:,.2f}" if amount > 0 else ""
            running_balance += amount
            transactions.append({
                "date": row["Date"],
                "description": row["Description"],
                "debit": debit,
                "credit": credit,
                "balance": f"${running_balance:,.2f}"
            })
        template_data = {
            "account_holder": account_holder,
            "client_number": fake.uuid4()[:8],
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80).strftime("%m/%d/%Y"),
            "customer_account_number": account_number,
            "customer_iban": f"GB{fake.random_number(digits=2)}CITI{fake.random_number(digits=14)}",
            "customer_bank_name": "Citibank",
            "statement_period": f"{min_date} through {max_date}",
            "statement_date": statement_date,
            "opening_balance_debit": "",
            "opening_balance_credit": "",
            "opening_balance": f"${initial_balance:,.2f}",
            "transactions": transactions,
            "total_debit": f"${total_debit:,.2f}",
            "total_credit": f"${total_credit:,.2f}",
            "total": f"${ending_balance:,.2f}",
            "logo_path": logo_data,
            "total_pages": 1,
            "current_page": 1
        }
    elif bank in ["wellsfargo", "pnc"]:
        transactions = []
        running_balance = initial_balance
        for index, row in df.iterrows():
            amount = row['Amount']
            transaction_type = "deposit" if amount > 0 else "electronic" if random.choice([True, False]) else "other"
            deposits_credits = f"${amount:,.2f}" if amount > 0 else ""
            withdrawals_debits = f"${abs(amount):,.2f}" if amount < 0 else ""
            running_balance += amount
            transactions.append({
                "date": row["Date"],
                "description": row["Description"],
                "amount": f"${abs(amount):,.2f}" if amount < 0 else f"${amount:,.2f}",
                "deposits_credits": deposits_credits,
                "withdrawals_debits": withdrawals_debits,
                "ending_balance": f"${running_balance:,.2f}",
                "type": transaction_type
            })
        
        daily_balances = [
            {"date1": df.iloc[i]["Date"], "bal1": f"${df.iloc[i]['Balance']:.2f}", "date2": "", "bal2": "", "date3": "", "bal3": ""}
            for i in range(0, len(df), 3)
        ] + [
            {"date1": df.iloc[i]["Date"], "bal1": f"${df.iloc[i]['Balance']:.2f}", "date2": df.iloc[i+1]["Date"] if i+1 < len(df) else "", "bal2": f"${df.iloc[i+1]['Balance']:.2f}" if i+1 < len(df) else "", "date3": "", "bal3": ""}
            for i in range(len(df)//3 * 3, len(df)-1, 2)
            if len(df) > len(df)//3 * 3
        ]
        
        template_data = {
            "account_holder": account_holder,
            "account_holder_address": address,
            "account_number": account_number,
            "statement_period": f"{min_date}, 2025 – {max_date}, 2025",
            "statement_date": statement_date,
            "logo_path": logo_data,
            "summary": {
                "beginning_balance": f"${initial_balance:,.2f}",
                "deposits_total": f"${deposits_total:,.2f}",
                "withdrawals_total": f"${withdrawals_total:,.2f}",
                "ending_balance": f"${ending_balance:,.2f}",
                "average_balance": f"${round((initial_balance + ending_balance) / 2, 2):,.2f}",
                "fees": f"${service_fee:,.2f}",
                "checks_written": random.randint(0, 5),
                "pos_transactions": random.randint(0, 10),
                "pos_pin_transactions": random.randint(0, 5),
                "total_atm_transactions": random.randint(0, 8),
                "pnc_atm_transactions": random.randint(0, 5),
                "other_atm_transactions": random.randint(0, 3),
                "apy_earned": f"{random.uniform(0.01, 0.5):.2f}%",
                "days_in_period": random.randint(28, 31),
                "average_collected_balance": f"${random.uniform(1000, 20000):,.2f}",
                "interest_paid_period": f"${random.uniform(0.1, 10):,.2f}",
                "interest_paid_ytd": f"${random.uniform(1, 50):,.2f}",
                "overdraft_protection1": "PNC Savings Account XXXX1234" if random.choice([True, False]) else "",
                "overdraft_protection2": "PNC Credit Line XXXX5678" if random.choice([True, False]) else "",
                "overdraft_status": "Opted-Out" if random.choice([True, False]) else "Opted-In"
            },
            "transactions": transactions,
            "daily_balances": daily_balances,
            "total_pages": 1,
            "current_page": 1
        }
        if bank == "wellsfargo":
            template_data["statement_period"] = f"{min_date}, 2025 – {max_date}, 2025"
    else:  # Chase
        deposits = [
            {"date": row["Date"], "description": row["Description"], "amount": f"${row['Amount']:,.2f}"}
            for _, row in df.iterrows() if row['Amount'] > 0
        ]
        withdrawals = [
            {"date": row["Date"], "description": row["Description"], "amount": f"${abs(row['Amount']):,.2f}"}
            for _, row in df.iterrows() if row['Amount'] < 0
        ]
        daily_balances = []
        balance_dict = {}
        for _, row in df.iterrows():
            date = row["Date"]
            balance_dict[date] = row["Balance"]
        for date in sorted(balance_dict.keys()):
            daily_balances.append({"date": date, "amount": balance_dict[date]})
        
        template_data = {
            "account_holder": account_holder,
            "account_holder_address": address,
            "account_number": account_number,
            "statement_period": f"{min_date} through {max_date}",
            "summary": {
                "beginning_balance": f"${initial_balance:,.2f}",
                "deposits_count": len(deposits),
                "deposits_total": f"${deposits_total:,.2f}",
                "withdrawals_count": len(withdrawals) + (1 if service_fee else 0),
                "withdrawals_total": f"${withdrawals_total:,.2f}",
                "ending_balance": f"${ending_balance:,.2f}",
                "transactions_count": transactions_count
            },
            "deposits": deposits,
            "withdrawals": withdrawals,
            "daily_balances": daily_balances,
            "logo_path": logo_data,
            "show_fee_waiver": service_fee == 0,
            "total_pages": 1,
            "current_page": 1
        }
    
    results = []
    for template_file in BANK_CONFIG[bank]["templates"]:
        if not os.path.exists(os.path.join(template_dir, template_file)):
            raise FileNotFoundError(f"Template {template_file} not found in {template_dir}")
        
        template = env.get_template(template_file)
        template_name = os.path.splitext(template_file)[0]
        html_filename = os.path.join(output_dir, f"bank_statement_{account_holder.replace(' ', '_')}_{bank}_{template_name}.html")
        pdf_filename = os.path.join(output_dir, f"bank_statement_{account_holder.replace(' ', '_')}_{bank}_{template_name}.pdf")
        
        rendered_html = template.render(**template_data)
        
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(rendered_html)
        
        wkhtmltopdf_path = os.environ.get("WKHTMLTOPDF_PATH", "C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
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
            "print-media-type": ""
        }
        try:
            pdfkit.from_string(rendered_html, pdf_filename, configuration=config, options=options)
            results.append((html_filename, pdf_filename))
        except OSError as e:
            raise Exception(f"PDF generation failed for {bank} template {template_file}: {e}. Ensure wkhtmltopdf is installed and accessible.")
    
    return results