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
            if st.button(BANK_DISPLAY_NAMES[bank_key], key=f"bank_button_{bank_key}"):
                st.session_state["selected_bank_key"] = bank_key
                st.session_state["generated"] = False
    
    selected_bank_key = st.session_state["selected_bank_key"]
    selected_bank = BANK_DISPLAY_NAMES.get(selected_bank_key, "No Bank Selected")

    num_transactions = st.slider("Number of Transactions", min_value=3, max_value=12, value=5, step=1)
    if selected_bank_key:
        template_files = [f for f in BANK_CONFIG[selected_bank_key]["templates"] if f.endswith('.html')]
        if not template_files:
            st.error(f"No templates found for {selected_bank}. Contact the administrator.")
            st.stop()
        selected_template = st.selectbox("Select Template Style", template_files, format_func=lambda x: TEMPLATE_DISPLAY_NAMES.get(x, x))
    else:
        selected_template = None
        st.markdown("Select a bank to choose a template style.")
    
    # Sidebar buttons (always visible)
    if st.button("Generate Statement (Sidebar)", key="sidebar_generate_button"):
        if not (selected_bank_key and selected_template):
            st.error("Please select a bank and template style first.")
        else:
            st.session_state["trigger_generate"] = True
    # Sidebar download button (disabled until generated)
    if st.session_state.get("generated", False) and st.session_state.get("pdf_file"):
        with open(st.session_state["pdf_file"], "rb") as f:
            pdf_content = f.read()
            st.download_button(
                label=f"Download {selected_bank} PDF (Sidebar)",
                data=pdf_content,
                file_name=os.path.basename(st.session_state["pdf_file"]),
                mime="application/pdf",
                key=f"sidebar_pdf_download_{selected_bank_key}"
            )
    else:
        st.button(
            label=f"Download {selected_bank} PDF (Sidebar)",
            key=f"sidebar_pdf_download_disabled_{selected_bank_key}",
            disabled=True
        )

st.title("Synthetic Bank Statement Generator")
st.markdown("""
Create realistic synthetic bank statements for development purposes.  
- Customize your synthetic bank statement using the sidebar options.  
- For a highly realistic bank statement, select the 'Classic' template style.  
- For a statement with added noise to challenge processing, choose a 'Custom' template style.  
- Download the generated PDF after configuration.  
- All data is synthetic and for learning purposes only.
""")

st.subheader(f"Preview: {selected_bank} Statement")
preview_placeholder = st.empty()

if "generated" not in st.session_state:
    st.session_state["generated"] = False
if "trigger_generate" not in st.session_state:
    st.session_state["trigger_generate"] = False

if st.button("Generate Statement", key="generate_button", disabled=not (selected_bank_key and selected_template)) or st.session_state["trigger_generate"]:
    if not (selected_bank_key and selected_template):
        st.error("Please select a bank and template style first.")
        st.session_state["trigger_generate"] = False
    else:
        with st.spinner(f"Generating {selected_bank} statement..."):
            try:
                account_holder = fake.company().upper()
                df = generate_bank_statement(num_transactions, account_holder)
                csv_filename = os.path.join(SYNTHETIC_STAT_DIR, f"bank_statement_{account_holder.replace(' ', '_')}_{selected_bank_key}.csv")
                df.to_csv(csv_filename, index=False)
                template_path = os.path.join(TEMPLATES_DIR, selected_template)
                statement_fields = identify_template_fields(template_path)
                results = generate_populated_html_and_pdf(df, account_holder, selected_bank_key, TEMPLATES_DIR, SYNTHETIC_STAT_DIR, selected_template)
                for _, pdf_file in results:
                    st.session_state["generated"] = True
                    st.session_state["pdf_file"] = pdf_file
                    st.session_state["trigger_generate"] = False
                    with open(pdf_file, "rb") as f:
                        pdf_content = f.read()
                        st.download_button(
                            label=f"Download {selected_bank} PDF",
                            data=pdf_content,
                            file_name=os.path.basename(pdf_file),
                            mime="application/pdf",
                            key=f"pdf_download_{selected_bank_key}"
                        )
                    pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                    pdf_preview = f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" height="600px" style="border: none;"></iframe>'
                    preview_placeholder.markdown("""
                    **Note**: If the PDF preview doesn't display (e.g., due to Chrome security settings), use the download button above or in the sidebar to view the statement.
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
                preview_placeholder.markdown("No statement generated. Resolve the error and try again.")
                st.session_state["generated"] = False
                st.session_state["trigger_generate"] = False

if not st.session_state["generated"]:
    preview_placeholder.markdown("Select a bank and options in the sidebar, then click 'Generate Statement' to preview your synthetic bank statement.")