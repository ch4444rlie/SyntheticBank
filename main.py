# app/main.py
import streamlit as st
import pandas as pd
import os
from statement_generator import generate_bank_statement, identify_template_fields, generate_populated_html_and_pdf, TEMPLATES_DIR, SYNTHETIC_STAT_DIR
from faker import Faker

fake = Faker()

st.set_page_config(page_title="Bank Statement Generator", page_icon="🏦")
st.title("Synthetic Bank Statement Generator")
st.markdown("""
Create a synthetic Chase bank statement as a PDF. 
- Enter the number of transactions (3–12) and select a template.
- Download the generated PDF directly.
- No software installation required—just use your browser!
""")

num_transactions = st.number_input("Number of Transactions (3-12)", min_value=3, max_value=12, value=5, step=1)
template_files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith('.html')]
if not template_files:
    st.error("No HTML templates found in the templates directory. Please contact the app administrator.")
    st.stop()
template_name = st.selectbox("Select Template Style", template_files)
account_holder = st.text_input("Account Holder Name", value=fake.company().lower())

if st.button("Generate Statement"):
    with st.spinner("Generating bank statement..."):
        try:
            df = generate_bank_statement(num_transactions, account_holder)
            csv_filename = os.path.join(SYNTHETIC_STAT_DIR, f"bank_statement_{account_holder.replace(' ', '_')}_chase.csv")
            df.to_csv(csv_filename, index=False)
            
            template_path = os.path.join(TEMPLATES_DIR, template_name)
            statement_fields = identify_template_fields(template_path)
            
            html_filename, pdf_filename = generate_populated_html_and_pdf(
                df, account_holder, TEMPLATES_DIR, SYNTHETIC_STAT_DIR, template_name
            )
            
            st.success("Statement generated successfully!")
            st.write(f"CSV saved as: {csv_filename}")
            st.write(f"PDF saved as: {pdf_filename}")
            
            # Download PDF
            with open(pdf_filename, "rb") as f:
                pdf_content = f.read()
                st.download_button(
                    label="Download PDF",
                    data=pdf_content,
                    file_name=os.path.basename(pdf_filename),
                    mime="application/pdf",
                    key="pdf_download"
                )
            
            st.write("Template Fields:")
            for field in statement_fields.fields:
                st.write(f"- {field.name}: {'Mutable' if field.is_mutable else 'Immutable'}, {field.description}")
        
        except Exception as e:
            st.error(f"Error generating statement: {str(e)}")
            st.markdown("""
            **Troubleshooting**:
            - Ensure the number of transactions is between 3 and 12.
            - Verify a valid template is selected.
            - If the issue persists, try refreshing the page or contact the app administrator.
            """)