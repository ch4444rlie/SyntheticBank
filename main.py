# app/main.py
import streamlit as st
import pandas as pd
import os
from statement_generator import generate_bank_statement, identify_template_fields, generate_populated_html, TEMPLATES_DIR, SYNTHETIC_STAT_DIR
from faker import Faker

fake = Faker()

st.set_page_config(page_title="Bank Statement Generator", page_icon="🏦")
st.title("Synthetic Bank Statement Generator")
st.write("Create a synthetic Chase bank statement as HTML. Use your browser's 'Print > Save as PDF' to generate a PDF.")

num_transactions = st.number_input("Number of Transactions (3-12)", min_value=3, max_value=12, value=5, step=1)
template_files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith('.html')]
template_name = st.selectbox("Select Template Style", template_files)
account_holder = st.text_input("Account Holder Name", value=fake.company().upper())

if st.button("Generate Statement"):
    with st.spinner("Generating bank statement..."):
        try:
            df = generate_bank_statement(num_transactions, account_holder)
            csv_filename = os.path.join(SYNTHETIC_STAT_DIR, f"bank_statement_{account_holder.replace(' ', '_')}_chase.csv")
            df.to_csv(csv_filename, index=False)
            
            template_path = os.path.join(TEMPLATES_DIR, template_name)
            statement_fields = identify_template_fields(template_path)
            
            html_filename = generate_populated_html(
                df, account_holder, TEMPLATES_DIR, SYNTHETIC_STAT_DIR, template_name
            )
            
            st.success("Statement generated successfully!")
            st.write(f"CSV saved as: {csv_filename}")
            st.write(f"HTML saved as: {html_filename}")
            with open(html_filename, "r") as f:
                html_content = f.read()
                st.download_button(
                    label="Download HTML",
                    data=html_content,
                    file_name=os.path.basename(html_filename),
                    mime="text/html"
                )
                st.markdown(html_content, unsafe_allow_html=True)
            
            st.write("Template Fields:")
            for field in statement_fields.fields:
                st.write(f"- {field.name}: {'Mutable' if field.is_mutable else 'Immutable'}, {field.description}")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")