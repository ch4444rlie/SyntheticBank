import streamlit as st
import pandas as pd
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

    # Generate descriptions with Faker
    descriptions = [fake.company() + f" {random.choice(transaction_types)}" for _ in range(num_transactions)]
    categories = [random.choice(transaction_types) for _ in range(num_transactions)]
    amounts = [round(random.uniform(-1000, 1000), 2) for _ in range(num_transactions)]

    # Create DataFrame
    data = {
        "Date": [d.strftime("%Y-%m-%d") for d in dates],
        "Description": descriptions,
        "Category": categories,
        "Amount": amounts,
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
    # Simple parsing of user input (basic, without Mistral)
    params = {"account_holder": "John Doe", "num_transactions": 10, "categories": ["Purchase", "Deposit", "Withdrawal"]}
    if "for" in user_input:
        account_holder = user_input.split("for")[1].split(",")[0].strip()
        params["account_holder"] = account_holder
    if "transactions" in user_input:
        num = int(user_input.split("transactions")[0].strip())
        params["num_transactions"] = num
    if "mostly" in user_input:
        categories = user_input.split("mostly")[1].strip().split(" and ")
        params["categories"] = categories

    # Generate statement
    statement = generate_bank_statement(
        params["num_transactions"],
        params["account_holder"],
        params["categories"]
    )
    
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