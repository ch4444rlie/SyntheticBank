import streamlit as st
import pandas as pd
import os
import base64
from statement_generator import (
    generate_bank_statement,
    identify_template_fields,
    generate_populated_html_and_pdf,
    TEMPLATES_DIR,
    SYNTHETIC_STAT_DIR,
    BANK_CONFIG
)
from faker import Faker

fake = Faker()

st.set_page_config(page_title="Synthetic Bank Statement Generator", page_icon="🏦", layout="wide")

st.markdown("""
<style>
.stButton > button {
    width: 100%;
    height: 40px;
    font-size: 16px;
    margin-bottom: 8px; /* Consistent spacing between buttons */
    transition: all 0.2s ease; /* Smooth transition for hover and active states */
}

/* Highlight selected buttons */
.stButton > button.selected {
    background-color: #007bff !important; /* Blue background for selected state */
    color: white !important; /* White text for selected state */
    border: 1px solid #0056b3 !important; /* Slightly darker border for contrast */
}

/* Hover effect for non-selected buttons */
.stButton > button:hover:not(.selected) {
    background-color: #e6f0ff !important; /* Light blue hover effect */
    border: 1px solid #007bff !important;
}

/* Adjusted buttons for Select Template Style section */
div[data-testid="stVerticalBlock"] > div:nth-child(3) .stButton > button {
    height: 40px; /* Reduced height */
    font-size: 14px; /* Smaller font size for condensed text */
    padding: 2px 6px; /* Reduced padding for tighter spacing */
    line-height: 1.2; /* Reduced line spacing */
    margin-bottom: 4px; /* Reduced spacing between buttons */
}
</style>
""", unsafe_allow_html=True)

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

with st.sidebar:
    st.header("Statement Options")
    st.markdown("Configure your synthetic bank statement.")
    st.subheader("Select Bank")
    banks = list(BANK_CONFIG.keys())
    if "selected_bank_key" not in st.session_state:
        st.session_state["selected_bank_key"] = None
    
    cols = st.columns(2)
    for idx, bank_key in enumerate(banks):
        with cols[idx % 2]:
            # Add 'selected' class if this bank is selected
            button_class = "selected" if st.session_state["selected_bank_key"] == bank_key else ""
            if st.button(BANK_DISPLAY_NAMES[bank_key], key=f"bank_button_{bank_key}", help="Select bank"):
                st.session_state["selected_bank_key"] = bank_key
                st.session_state["generated"] = False
                st.session_state["selected_account_type"] = None
                st.session_state["selected_template"] = None
                # Force rerun to update button styles
                st.rerun()
    
    selected_bank_key = st.session_state["selected_bank_key"]
    selected_bank = BANK_DISPLAY_NAMES.get(selected_bank_key, "No Bank Selected")

    st.subheader("Select Account Type")
    account_types = ["Business", "Personal"]
    if "selected_account_type" not in st.session_state:
        st.session_state["selected_account_type"] = None
    
    cols_account = st.columns(2)
    for idx, account_type in enumerate(account_types):
        with cols_account[idx % 2]:
            # Add 'selected' class if this account type is selected
            button_class = "selected" if st.session_state["selected_account_type"] == account_type else ""
            if st.button(account_type, key=f"account_type_button_{account_type}", help="Select account type"):
                st.session_state["selected_account_type"] = account_type
                st.session_state["generated"] = False
                st.rerun()
    
    selected_account_type = st.session_state["selected_account_type"]

    num_transactions = st.slider("Number of Transactions", min_value=3, max_value=12, value=5, step=1)
    if selected_bank_key and selected_account_type:
        template_files = [f for f in BANK_CONFIG[selected_bank_key]["templates"] if f.endswith('.html')]
        if not template_files:
            st.error(f"No templates found for {selected_bank}. Contact the administrator.")
            st.stop()
        st.subheader("Select Template Style")
        if "selected_template" not in st.session_state:
            st.session_state["selected_template"] = None
        
        cols_template = st.columns(len(template_files) // 2 + len(template_files) % 2)
        for idx, template in enumerate(template_files):
            with cols_template[idx % len(cols_template)]:
                display_name = TEMPLATE_DISPLAY_NAMES.get(template, template)
                # Add 'selected' class if this template is selected
                button_class = "selected" if st.session_state["selected_template"] == template else ""
                if st.button(display_name, key=f"template_button_{template}", help="Select template style"):
                    st.session_state["selected_template"] = template
                    st.session_state["generated"] = False
                    st.rerun()
        
        selected_template = st.session_state["selected_template"]
    else:
        selected_template = None
        st.markdown("Select a bank and account type to choose a template style.")
    
    if st.button("Generate Statement (Sidebar)", key="sidebar_generate_button"):
        if not (selected_bank_key and selected_account_type and selected_template):
            st.error("Please select a bank, account type, and template style first.")
        else:
            st.session_state["trigger_generate"] = True
            st.rerun()

st.title("Lightweight Synthetic Bank Statement Generator")
st.markdown("""  
- Create your synthetic bank statement with the sidebar options.  
- For a highly realistic bank statement, such as one you would receive in the mail, select the 'Classic' template style.  
- For a less realistic variation on the bank statement, choose a 'Custom' template style.  
- Download the generated PDF after configuration.  
""")

if "generated" not in st.session_state:
    st.session_state["generated"] = False
if "trigger_generate" not in st.session_state:
    st.session_state["trigger_generate"] = False
if "pdf_content" not in st.session_state:
    st.session_state["pdf_content"] = None
if "pdf_filename" not in st.session_state:
    st.session_state["pdf_filename"] = None

if st.button("Generate Statement", key="generate_button", disabled=not (selected_bank_key and selected_account_type and selected_template)) or st.session_state["trigger_generate"]:
    if not (selected_bank_key and selected_account_type and selected_template):
        st.error("Please select a bank, account type, and template style first.")
        st.session_state["trigger_generate"] = False
    else:
        with st.spinner(f"Generating {selected_bank} statement..."):
            try:
                account_holder = fake.company().upper() if selected_account_type == "Business" else fake.name()
                df = generate_bank_statement(num_transactions, account_holder)
                csv_filename = os.path.join(SYNTHETIC_STAT_DIR, f"bank_statement_{account_holder.replace(' ', '_')}_{selected_bank_key}.csv")
                df.to_csv(csv_filename, index=False)
                template_path = os.path.join(TEMPLATES_DIR, selected_template)
                statement_fields = identify_template_fields(template_path)
                results = generate_populated_html_and_pdf(df, account_holder, selected_bank_key, TEMPLATES_DIR, SYNTHETIC_STAT_DIR, selected_template)
                for _, pdf_file in results:
                    st.session_state["generated"] = True
                    st.session_state["pdf_filename"] = os.path.basename(pdf_file)
                    with open(pdf_file, "rb") as f:
                        st.session_state["pdf_content"] = f.read()
                    st.session_state["trigger_generate"] = False
                    st.download_button(
                        label=f"Download {selected_bank} PDF",
                        data=st.session_state["pdf_content"],
                        file_name=st.session_state["pdf_filename"],
                        mime="application/pdf",
                        key=f"pdf_download_{selected_bank_key}"
                    )
                    st.subheader(f"Preview: {selected_bank} Statement")
                    preview_placeholder = st.empty()
                    pdf_base64 = base64.b64encode(st.session_state["pdf_content"]).decode('utf-8')
                    pdf_preview = f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" height="600px" style="border: none;"></iframe>'
                    preview_placeholder.markdown("""
                    **Note**: If the PDF preview doesn't display (e.g., due to Chrome security settings), use the download button above to view the statement.
                    """)
                    preview_placeholder.markdown(pdf_preview, unsafe_allow_html=True)
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
                - Verify the template is valid.
                - If the PDF preview or download fails, try Firefox/Edge or disable Chrome’s ad blockers.
                - Refresh or contact the administrator.
                """)
                preview_placeholder = st.empty()
                preview_placeholder.markdown("No statement generated. Resolve the error and try again.")
                st.session_state["generated"] = False
                st.session_state["trigger_generate"] = False
                st.session_state["pdf_content"] = None
                st.session_state["pdf_filename"] = None

if not st.session_state["generated"]:
    st.subheader(f"Preview: {selected_bank} Statement")
    preview_placeholder = st.empty()
    preview_placeholder.markdown("Select a bank and options in the sidebar, then click 'Generate Statement' to preview your synthetic bank statement.")