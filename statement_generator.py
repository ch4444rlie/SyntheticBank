# app/statement_generator.py
import os
import json
import re
import base64
from faker import Faker
from datetime import datetime, timedelta
import random
import pandas as pd
from pydantic import BaseModel, Field
from typing import List
from jinja2 import Environment, FileSystemLoader

fake = Faker()

SAMPLE_STATEMENT_DIR = "sample_statements"
SAMPLE_LOGOS_DIR = "sample_logos"
SYNTHETIC_STAT_DIR = "synthetic_statements"
TEMPLATES_DIR = "templates"

for directory in [SAMPLE_STATEMENT_DIR, SAMPLE_LOGOS_DIR, SYNTHETIC_STAT_DIR, TEMPLATES_DIR]:
    os.makedirs(directory, exist_ok=True)

BANK_LOGO = "chase_bank_logo.png"
BANK_NAME = "chase"

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
        FieldDefinition(name="summary", is_mutable=True, description="Checking summary data (beginning balance, counts, totals)"),
        FieldDefinition(name="deposits", is_mutable=True, description="List of deposit transactions"),
        FieldDefinition(name="withdrawals", is_mutable=True, description="List of withdrawal transactions"),
        FieldDefinition(name="daily_balances", is_mutable=True, description="Daily ending balances"),
        FieldDefinition(name="logo_path", is_mutable=True, description="Path to the bank logo"),
        FieldDefinition(name="bank_name", is_mutable=False, description="Name of the bank (JPMorgan Chase)"),
        FieldDefinition(name="bank_address", is_mutable=False, description="Bank address"),
        FieldDefinition(name="checking_summary_header", is_mutable=False, description="Header for checking summary"),
        FieldDefinition(name="deposits_header", is_mutable=False, description="Header for deposits section"),
        FieldDefinition(name="withdrawals_header", is_mutable=False, description="Header for withdrawals section"),
        FieldDefinition(name="daily_balance_header", is_mutable=False, description="Header for daily balance section"),
        FieldDefinition(name="customer_service", is_mutable=False, description="Customer service contact information"),
        FieldDefinition(name="footnotes", is_mutable=False, description="Footnotes and disclosures")
    ]
    statement_fields = StatementFields(fields=[f for f in default_fields if f.name in placeholders or f.name in template_content])
    
    log_path = os.path.join(SYNTHETIC_STAT_DIR, "template_fields.json")
    with open(log_path, 'w') as f:
        json.dump(statement_fields.model_dump(), f, indent=2)
    
    return statement_fields

def generate_populated_html(df: pd.DataFrame, account_holder: str, template_dir: str, output_dir: str, template_name: str) -> str:
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
    
    address = fake.address().replace('\n', '<br>')
    
    logo_path = os.path.join(SAMPLE_LOGOS_DIR, BANK_LOGO)
    logo_data = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            logo_data = f"data:image/png;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
    
    min_date = datetime.strptime(min(df['Date']), "%m/%d").replace(year=2025).strftime("%B %d, %Y")
    max_date = datetime.strptime(max(df['Date']), "%m/%d").replace(year=2025).strftime("%B %d, %Y")
    
    template_data = {
        "account_holder": account_holder,
        "account_holder_address": address,
        "account_number": fake.bban()[:15],
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
        "show_fee_waiver": service_fee == 0
    }
    
    if not os.path.exists(os.path.join(template_dir, template_name)):
        raise FileNotFoundError(f"Template {template_name} not found in {template_dir}")
    
    template = env.get_template(template_name)
    html_filename = os.path.join(output_dir, f"bank_statement_{account_holder.replace(' ', '_')}_{os.path.splitext(template_name)[0]}.html")
    
    rendered_html = template.render(**template_data)
    
    with open(html_filename, 'w') as f:
        f.write(rendered_html)
    
    return html_filename