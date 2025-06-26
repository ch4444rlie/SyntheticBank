import streamlit as st
import pandas as pd
import os
import base64
from new_generator import (
    generate_bank_statement,
    identify_template_fields,
    generate_populated_html_and_pdf,
    TEMPLATES_DIR,
    SYNTHETIC_STAT_DIR,
    BANK_CONFIG
)
from faker import Faker

fake = Faker()

# Streamlit page configuration
st.set_page_config(page_title="Synthetic Bank Statement Generator", page_icon="🏦", layout="wide")

# Custom CSS for buttons
st.markdown("""
<style>
.stButton > button {
    width: 100%;
    height: 40px;
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

# Bank and template display names for user-friendly interface
BANK_DISPLAY_NAMES = {
    "chase": "Chase",
    "citibank": "Citibank",
    "wellsfargo": "Wells Fargo",
    "pnc": "PNC"
}

TEMPLATE_DISPLAY_NAMES = {
    "chase_classic_style.html": "Classic Chase Statement",
    "chase_variation_1.html": "Custom Chase Statement 1",
    "chase_variation_2.html": "Custom Chase Statement 2",
    "citibank_classic_template.html": "Classic Citibank Statement",
    "citibank_variation_1.html": "Custom Citibank Statement 1",
    "citibank_variation_2.html": "Custom Citibank Statement 2",
    "wells_fargo_classic.html": "Classic Wells Fargo Statement",
    "wells_variation_1.html": "Custom Wells Fargo Statement 1",
    "wells_variation_2.html": "Custom Wells Fargo Statement 2",
    "pnc_classic.html": "Classic PNC Statement"
}

# Sidebar for user inputs
with st.sidebar:
    st.header("Statement Options")
    st.markdown("Configure your synthetic bank statement.")
    
    # Bank selection
    st.subheader("Select Bank")
    banks = list(BANK_CONFIG.keys())
    if "selected_bank_key" not in st.session_state:
        st.session_state["selected_bank_key"] = None
    
    cols = st.columns(2)
    for idx, bank_key in enumerate(banks):
        with cols[idx % 2]:
            if st.button(BANK_DISPLAY_NAMES[bank_key], key=f"bank_button_{bank_key}"):
                st.session_state["selected_bank_key"] = bank_key
                st.session_state["generated"] = False
    
    selected_bank_key = st.session_state["selected_bank_key"]
    selected_bank = BANK_DISPLAY_NAMES.get(selected_bank_key, "No Bank Selected")

    # Account type selection
    st.subheader("Select Account Type")
    account_type = st.radio("Account Type", ["Personal", "Business"], index=0)
    account_type = account_type.lower()

    # Number of transactions
    num_transactions = st.slider("Number of Transactions", min_value=3, max_value=12, value=5, step=1)

    # Template selection
    if selected_bank_key:
        template_files = [f for f in BANK_CONFIG[selected_bank_key]["templates"] if f.endswith('.html')]
        if not template_files:
            st.error(f"No templates found for {selected_bank}. Contact the administrator.")
            st.stop()
        selected_template = st.selectbox("Select Template Style", template_files, format_func=lambda x: TEMPLATE_DISPLAY_NAMES.get(x, x))
    else:
        selected_template = None
        st.markdown("Select a bank to choose a template style.")
    
    # Generate button
    if st.button("Generate Statement", key="sidebar_generate_button"):
        if not (selected_bank_key and selected_template):
            st.error("Please select a bank and template style first.")
        else:
            st.session_state["trigger_generate"] = True

# Main interface
st.title("Lightweight Synthetic Bank Statement Generator")
st.markdown("""  
- Create your synthetic bank statement with the sidebar options.  
- Select **Personal** or **Business** account type to customize transaction categories.  
- Choose a **Classic** template for a realistic statement or a **Custom** template for variations.  
- Download the generated PDF, which includes important account information.  
""")

# Initialize session state
if "generated" not in st.session_state:
    st.session_state["generated"] = False
if "trigger_generate" not in st.session_state:
    st.session_state["trigger_generate"] = False
if "pdf_content" not in st.session_state:
    st.session_state["pdf_content"] = None
if "pdf_filename" not in st.session_state:
    st.session_state["pdf_filename"] = None

# Handle generation
if st.session_state["trigger_generate"]:
    if not (selected_bank_key and selected_template):
        st.error("Please select a bank and template style first.")
        st.session_state["trigger_generate"] = False
    else:
        with st.spinner(f"Generating {selected_bank} {account_type} statement..."):
            try:
                # Generate account holder based on account type
                account_holder = fake.company().upper() if account_type == "business" else fake.name().upper()
                df = generate_bank_statement(num_transactions, account_holder, account_type)
                csv_filename = os.path.join(SYNTHETIC_STAT_DIR, f"bank_statement_{account_type.upper()}_{account_holder.replace(' ', '_')}_{selected_bank_key}.csv")
                df.to_csv(csv_filename, index=False, encoding='utf-8')
                
                statement_fields = identify_template_fields(selected_bank_key, TEMPLATES_DIR)
                results = generate_populated_html_and_pdf(df, account_holder, selected_bank_key, TEMPLATES_DIR, SYNTHETIC_STAT_DIR, account_type)
                
                # Use the first result (single template)
                html_file, pdf_file = results[0]
                st.session_state["generated"] = True
                st.session_state["pdf_filename"] = os.path.basename(pdf_file)
                with open(pdf_file, "rb") as f:
                    st.session_state["pdf_content"] = f.read()
                st.session_state["trigger_generate"] = False
                
                # Display download button
                st.download_button(
                    label=f"Download {selected_bank} {account_type.capitalize()} PDF",
                    data=st.session_state["pdf_content"],
                    file_name=st.session_state["pdf_filename"],
                    mime="application/pdf",
                    key=f"pdf_download_{selected_bank_key}_{account_type}"
                )
                
                # Preview section
                st.subheader(f"Preview: {selected_bank} {account_type.capitalize()} Statement")
                preview_placeholder = st.empty()
                pdf_base64 = base64.b64encode(st.session_state["pdf_content"]).decode('utf-8')
                pdf_preview = f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" height="600px" style="border: none;"></iframe>'
                preview_placeholder.markdown("""
                **Note**: If the PDF preview doesn't display (e.g., due to Chrome security settings), use the download button above to view the statement.
                """)
                preview_placeholder.markdown(pdf_preview, unsafe_allow_html=True)
                
                # Details expander
                with st.expander("View Details"):
                    st.write(f"CSV saved: {csv_filename}")
                    st.write(f"PDF saved: {pdf_file}")
                    st.write("Template Fields:")
                    for field in statement_fields.fields:
                        st.write(f"- {field.name}: {'Mutable' if field.is_mutable else 'Immutable'}, {field.description}")
            
            except Exception as e:
                st.error(f"Error generating statement: {str(e)}")
                st.markdown("""
                **Troubleshooting**:
                - Ensure transactions are between 3 and 12.
                - Verify the template and logo files exist.
                - Check that wkhtmltopdf is installed.
                - If the PDF preview or download fails, try Firefox/Edge or disable Chrome’s ad blockers.
                - Refresh or contact the administrator.
                """)
                preview_placeholder = st.empty()
                preview_placeholder.markdown("No statement generated. Resolve the error and try again.")
                st.session_state["generated"] = False
                st.session_state["trigger_generate"] = False
                st.session_state["pdf_content"] = None
                st.session_state["pdf_filename"] = None

# Default preview message
if not st.session_state["generated"]:
    st.subheader(f"Preview: {selected_bank} {account_type.capitalize()} Statement")
    preview_placeholder = st.empty()
    preview_placeholder.markdown("Select a bank, account type, and options in the sidebar, then click 'Generate Statement' to preview your synthetic bank statement.")