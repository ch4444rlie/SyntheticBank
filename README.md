# Synthetic Bank Statement Generator

This project generates **synthetic bank statements** mimicking real-world financial documents, enabling innovation in financial data processing while preserving privacy. By combining Large Language Models (LLMs), synthetic data generation, and HTML templating, it produces realistic PDF statements for **learning, development, and testing** in controlled environments.

**Important**: The synthetic data generated is strictly for **learning and development purposes** and must not be used for fraudulent activities or real-world financial applications.

![image](https://github.com/user-attachments/assets/21b75450-4d19-4c1e-a3a2-503a25b47d42)


## Why Synthetic Bank Statements?
- **Privacy Protection**: Enables developers to work with realistic financial data without sensitive information.
- **Innovation**: Supports financial tools, machine learning models, and data processing pipelines.
- **Realism**: Produces structurally diverse statements with authentic layouts, transaction patterns, and branding.

## Project Objectives
This project addresses three key challenges:
1. **Realistic and Diverse Data**: Uses LLMs (Mistral via Ollama) and Faker to generate varied transaction descriptions (e.g., "Grocery Store Purchase") and account details (names, addresses, account numbers).
2. **Authentic Formatting**: Renders statements in HTML with Jinja2 templates and converts to PDFs using wkhtmltopdf, replicating real-world bank statement layouts.
3. **Scalable Templates**: Supports 10 unique templates with distinct layouts, enabling adaptation for various bank formats (e.g., Chase, Wells Fargo).

## Approach and Implementation
### Research
- Analyzed real-world bank statements from multiple institutions to understand layouts, fonts, and structural elements like headers, footers, and transaction tables.
- Studied challenges in OCR and table extraction, such as misaligned columns, varied fonts, and noise (e.g., watermarks, disclaimers).
- Explored synthetic data generation techniques to mimic transaction patterns and edge cases like negative balances or missing fields.

### Tools and Libraries
- **Data Generation**: `Faker` for account details (names, addresses, account numbers); `Mistral` (via Ollama) for realistic transaction descriptions and categories.
- **Templating**: `Jinja2` for HTML templates, enabling dynamic data insertion and layout variability.
- **PDF Generation**: `wkhtmltopdf` to convert HTML to PDFs, ensuring compatibility with OCR tools.
- **Data Processing**: `pandas` for transaction table management; `pydantic` for data validation.
- **External Tools**: Base64-encoded logos embedded in templates to replicate branding.

### Variability and Realism
- Created **10 unique HTML templates**, each with distinct layouts:
  - Varied column names (e.g., "Transaction Date" vs. "Date", "Amount" vs. "Value").
  - Different fonts (Arial, Times New Roman, Helvetica) and sizes.
  - Randomized footers, headers, and summaries (e.g., account summary tables, promotional text).
  - Multiple currencies (USD, EUR, GBP) and amount formats (e.g., $1,234.56 vs. 1234.56).
  - Single-page and multi-page statements to test pagination.
- Added **noise** to challenge downstream processing:
  - Misaligned tables, overlapping text, and watermarks.
  - Randomized disclaimers and fine print.
  - Edge cases like negative balances, duplicate transactions, or incomplete fields.
- Ensured realism by modeling transaction patterns after real statements (e.g., recurring deposits, varied merchant names).

### Methods and Final Approach
- Experimented with `reportlab` for PDF generation but chose `wkhtmltopdf` with HTML templating for greater layout flexibility.
- Tested GPT-based LLMs for transaction descriptions but selected Mistral for local deployment and efficiency.
- Adopted Jinja2 templating for its ability to support diverse layouts and scalability for additional bank formats.

### Potential Improvements
- Add scanned document effects (e.g., skew, noise) using `Pillow` to further test OCR robustness.
- Expand template variety to include mobile app-style or legacy formats.
- Implement a configuration file to parameterize layout options (e.g., font, currency) for easier customization.
- Integrate automated testing to validate PDF structure against processing pipeline requirements.

### Scalability and Reusability
- Modular pipeline allows new templates to be added by creating additional HTML files.
- Parameterized data generation (e.g., transaction count, currency) supports customization.
- Code is documented and structured for reuse in other synthetic data projects (see `final_chase_generator.ipynb`).

## Deliverables
1. **10 Synthetic Bank Statement PDFs**:
   - Each with a unique layout, available in the `synthetic_statements/` directory.
   - Examples include varied column structures, fonts, currencies, and noise elements.
2. **Documentation**: This README details the approach, tools, and implementation.
3. **Code and Tooling**: The Jupyter Notebook (`final_chase_generator.ipynb`) and Streamlit app (`app/main.py`) provide a reusable generator script.

## Current Pipeline
1. **Template Creation**:
   - 10 HTML templates with varied layouts, created using Jinja2 and LLM assistance.
   - Placeholders for dynamic fields (e.g., transactions, account details) and static elements (e.g., logos).
2. **Synthetic Data Generation**:
   - `Faker` generates account holder details; `Mistral` creates transaction descriptions.
   - Data stored in `pandas` DataFrames for processing.
3. **Output Formatting**:
   - Jinja2 populates templates with data; wkhtmltopdf converts to PDFs.
   - Base64-encoded logos ensure branding consistency.

## Example Outputs
- [Statement 1: Classic Chase Layout](https://github.com/ch4444rlie/SyntheticBank/blob/master/synthetic_statements/bank_statement_BROWN-JONES_chase_chase_mail_style.pdf)
- [Statement 2: Classic PNC Layout](https://github.com/ch4444rlie/SyntheticBank/blob/master/synthetic_statements/bank_statement_BROWN-JONES_pnc_pnc_main.pdf)
- [Statement 3: Classic Wells Fargo Layout](https://github.com/ch4444rlie/SyntheticBank/blob/master/synthetic_statements/bank_statement_BROWN-JONES_wellsfargo_wells_fargo_classic.pdf)
- Additional statements (4–10) in `synthetic_statements/` with unique layouts.

*Note*: These are synthetic and not real financial data.

## Demo and Full Capabilities
### Try the Demo
A public demo is available on Streamlit Cloud: [**Synthetic Bank Statement Demo**](https://syntheticbank-xutpjbpmddrzxd8tg2hgsw.streamlit.app/)
- Generate HTML statements with 3–12 transactions and select from 10 templates.
- Download HTML or save as PDF via browser.
- Simplified for non-technical users, excluding LLM data generation.

### Full Capabilities
Run locally for:
- Dynamic transaction descriptions via Mistral (Ollama).
- Direct PDF generation with wkhtmltopdf.
- Access to all 10 templates.
**Setup**:
1. Install Ollama and Mistral: [Ollama Guide](https://ollama.ai/download), `ollama pull mistral:7b-instruct-v0.3-q4_0`.
2. Install wkhtmltopdf: [Downloads](https://wkhtmltopdf.org/downloads.html).
3. Install dependencies: `pip install -r requirements.txt`.

## Requirements
- **Demo**: No local setup required.
- **Full Version**:
  - Python 3.13+
  - Libraries: `faker`, `pandas`, `ollama`, `jinja2`, `pdfkit`, `pydantic`
  - External: wkhtmltopdf
  - See [requirements.txt](https://github.com/ch4444rlie/SyntheticBank/blob/master/requirements.txt).

## Getting Started
1. **Prerequisites**:
   - Install Python 3.13+.
   - For full version: Install wkhtmltopdf, dependencies, and place logo/templates in `sample_logos/` and `templates/`.
2. **Running**:
   - Use `final_chase_generator.ipynb` for full generation.
   - Run Streamlit app: `streamlit run app/main.py`.
