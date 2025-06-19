import streamlit as st
import pandas as pd
import os
from statement_generator import generate_bank_statement, identify_template_fields, generate_populated_html_and_pdf, TEMPLATES_DIR, SYNTHETIC_STAT_DIR, BANK_CONFIG
from faker import Faker

fake = Faker()

st.set_page_config(page_title="Bank Statement Generator", page_icon="🏦")
st.title("Synthetic Bank Statement Generator")
st.markdown("""
Create a synthetic bank statement as a PDF. 
- Select a bank and number of transactions (3–12).
- Choose a template style for the selected bank.
- Download the generated PDF directly.
- No software installation required—just use your browser!
""")

banks = list(BANK_CONFIG.keys())
selected_bank = st.selectbox("Select Bank", banks, index=0)
num_transactions = st.number_input("Number of Transactions (3-12)", min_value=3, max_value=12, value=5, step=1)
template_files = [f for f in BANK_CONFIG[selected_bank]["templates"] if f.endswith('.html')]
if not template_files:
 st.error(f"No HTML templates found for {selected_bank} in the templates directory. Please contact the app administrator.")
 st.stop()
template_name = st.selectbox("Select Template Style", template_files)
account_holder = st.text_input("Account Holder Name", value=fake .company().upper())

if st.button("Generate Statement"):
 with st.spinner(f"Generating {selected_bank.capitalize()} statement..."):
 try:
 df = generate_bank_statement(num_transactions, account_holder)
 csv_filename = os.path.join(SYNTHETIC_STAT_DIR, f"bank_statement_{account_holder.replace(' ', '_')}_{selected_bank}.csv")
 df.to_csv(csv_filename, index=False)
 
 template_path = os.path.join(TEMPLATES_DIR, template_name)
 statement_fields = identify_template_fields(template_path)
 
 results = generate_populated_html_and_pdf(df, account_holder, selected_bank, TEMPLATES_DIR, SYNTHETIC_STAT_DIR)
 for html_file, pdf_file in results:
 st.success(f"Statement generated successfully for {selected_bank.capitalize()}!")
 st.write(f"CSV saved as: {csv_filename}")
 st.write(f"PDF saved as: {pdf_file}")
 
 # Download PDF
 with open(pdf_file, "rb") as f:
 pdf_content = f.read()
 st.download_button(
 label=f"Download {selected_bank.capitalize()} PDF",
 data=pdf_content,
 file_name=os.path.basename(pdf_file),
 mime="application/pdf",
 key=f"pdf_download_{selected_bank}"
 )
 
 st.write("Template Fields:")
 for field in statement_fields.fields:
 st.write(f"- {field.name}: {'Mutable' if field.is_mutable else 'Immutable'}, {field.description}")
 
 except Exception as e:
 st.error(f"Error generating statement: {str(e)}")
 st.markdown("""
 **Troubleshooting**:
 - Ensure the number of transactions is between 3 and 12.
 - Verify a valid template is selected for the chosen bank.
 - If the issue persists, try refreshing the page or contact the app administrator.
 """)