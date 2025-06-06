import streamlit as st
import pandas as pd
import json
import ollama
from faker import Faker
from datetime import datetime, timedelta
import random

fake = Faker()

def generate_bank_statement(num_transactions, account_holder, transaction_types=None):
    account_holder = account_holder or fake.name()
    transaction_types = transaction_types or ["Purchase", "Deposit", "Withdrawal"]

    # Generate dates
    start_date = datetime.now() - timedelta(days=90)
    dates = [start_date + timedelta(days=random.randint(0, 90)) for _ in range(num_transactions)]

    # Generate descriptions with Mistral (batched)
    prompt = f"""
    Generate {num_transactions} realistic bank transaction descriptions in JSON format.
    Each should have 'description', 'category', and 'amount'.
    Bias toward categories: {', '.join(transaction_types)}.
    Example: [
        {{"description": "Grocery purchase at Whole Foods", "category": "Groceries", "amount": -45.67}},
        {{"description": "Salary from Acme Corp", "category": "Deposit", "amount": 2000.00}}
    ]
    """
    response = ollama.generate(model="mistral:7b-instruct-v0.3-q4_0", prompt=prompt)
    transactions = json.loads(response['response'])

    # Create DataFrame
    data = {
        "Date": [d.strftime("%Y-%m-%d") for d in dates],
        "Description": [t["description"] for t in transactions[:num_transactions]],
        "Category": [t["category"] for t in transactions[:num_transactions]],
        "Amount": [t["amount"] for t in transactions[:num_transactions]],
        "Balance": [0] * num_transactions,
        "Account Holder": [account_holder] * num_transactions,
        "Account Number": [fake.bban() for _ in range(num_transactions)]
    }
    df = pd.DataFrame(data)
    
    # Sort and calculate balance
    df = df.sort_values("Date")
    initial_balance = random.uniform(1000, 5000)
    df["Balance"] = initial_balance + df["Amount"].cumsum()
    
    return df

# Streamlit app
st.title("Synthetic Bank Statement Generator")

# User input
user_input = st.text_area("Describe the bank statement (e.g., '20 transactions for Alice, mostly groceries and bills')", 
                         value="20 transactions for Alice, mostly groceries and bills")
generate_button = st.button("Generate Statement")

if generate_button and user_input:
    # Parse user input with Mistral
    prompt = f"""
    Parse this request into JSON with 'account_holder', 'num_transactions', and 'categories'.
    Example: {{"account_holder": "Alice", "num_transactions": 20, "categories": ["Groceries", "Bills"]}}
    Request: "{user_input}"
    """
    response = ollama.generate(model="mistral:7b-instruct-v0.3-q4_0", prompt=prompt)
    params = json.loads(response['response'])

    # Extract parameters
    account_holder = params.get("account_holder", "John Doe")
    num_transactions = params.get("num_transactions", 10)
    categories = params.get("categories", ["Purchase", "Deposit", "Withdrawal"])

    # Generate statement
    statement = generate_bank_statement(num_transactions, account_holder, categories)
    
    # Display preview
    st.write("### Bank Statement Preview")
    st.dataframe(statement)
    
    # Download option
    csv = statement.to_csv(index=False)
    st.download_button(
        label="Download Statement as CSV",
        data=csv,
        file_name="bank_statement.csv",
        mime="text/csv"
    )