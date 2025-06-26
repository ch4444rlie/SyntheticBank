
def get_important_account_info(account_type, current_date):
    """Generate Important Account Information based on account type."""
    if account_type == "Personal":
        return """
        <p>Between May 1, 2025, and September 30, 2025, Citibank will discontinue mini statement printing at ATMs. Use Online Banking or visit a branch for account details.</p><br>
        <p>Effective June 22, 2025, the fee for Citibank Express Funds on checks over $100 will rise from 2.00% to 2.50%. Checks $25-$100 remain at $2.00.</p><br>
        <p>Contact us at 1-800-374-9700 (Mon-Fri 8 AM-8 PM ET) for errors or questions, within 60 days per Regulation E.</p><br>
        <p>From June 16, 2025, first-day availability for deposits increases to $400 (up from $125). Holds on deposits over $5,000 may extend to 7 days. See citibank.com/terms.</p><br>
        <p>Enhance your account with Citibank Mobile’s new budgeting tools and alerts. Log in at citibank.com/mobile to activate.</p><br>
        <p>Starting July 1, 2025, the Citibank Basic Checking monthly fee rises to $12 unless you maintain a $500 balance or $500 direct deposit. Visit citibank.com/checking.</p><br>
        <p>Enable biometric login for mobile banking by July 1, 2025, at citibank.com/security for added security.</p><br>
        <p>For updates or fraud reporting, call 1-800-374-9700 or visit a branch.</p>
        """
    elif account_type == "Business":
        return """
        <p>Effective June 22, 2025, the monthly fee for Citibank Business Checking will increase to $25 unless you maintain a $5,000 balance or $5,000 in ACH transactions. See citibank.com/business.</p><br>
        <p>Citibank Business Analytics now offers payroll integration and cash flow tools. Contact 1-800-374-9700 to enroll.</p><br>
        <p>Domestic wire fees will rise to $30 from $25 starting June 30, 2025. International wires remain $45 online or $55 at branches. Details at citibank.com/business-fees.</p><br>
        <p>Transactions over $10,000 may be reported to the IRS. Contact 1-800-374-9700 for inquiries.</p><br>
        <p>Launch the Business Rewards Program on August 1, 2025, for accounts with $5,000 monthly card use. Enroll by July 31, 2025, at citibank.com/business-rewards.</p><br>
        <p>Same-day ACH settlement begins July 15, 2025. Call 1-800-374-9700 for eligibility.</p><br>
        <p>Activate expense tracking for Citibank Business Checking starting July 1, 2025, at citibank.com/business-tools.</p><br>
        <p>For support, visit a branch or call 1-800-374-9700 (Mon-Fri 8 AM-6 PM ET).</p>
        """
    return ""

def generate_populated_html_and_pdf(df, account_holder, bank_key, template_dir, output_dir, template_file):
    """Generate populated HTML and PDF from a DataFrame and template."""
    from jinja2 import Environment, FileSystemLoader  # Assuming Jinja2 is used
    import os

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_file)

    # Prepare summary data (example structure, adjust based on your implementation)
    summary = {
        "beginning_balance": df["balance"].iloc[0] if not df.empty else "0.00",
        "deposits_count": len(df[df["type"] == "deposit"]),
        "deposits_total": f"${df[df['type'] == 'deposit']['amount'].sum():.2f}",
        "withdrawals_count": len(df[df["type"] == "withdrawal"]),
        "withdrawals_total": f"${abs(df[df['type'] == 'withdrawal']['amount'].sum()):.2f}",
        "transactions_count": len(df),
        "ending_balance": f"${df['balance'].iloc[-1] if not df.empty else '0.00'}"
    }

    # Prepare transactions (example structure, adjust as needed)
    transactions = df.to_dict("records")

    # Get current date for dynamic content
    from datetime import datetime
    current_date = datetime.now().strftime("%B %d, %Y")

    # Get important account info based on account type (from session state or passed parameter)
    account_type = st.session_state.get("selected_account_type", "Personal")  # Default to Personal if not set
    important_account_info = get_important_account_info(account_type, current_date)

    # Render template with all variables
    html_content = template.render(
        logo_path=os.path.join(template_dir, "logos", f"{bank_key}_logo.png"),
        account_holder=account_holder,
        account_number=df["account_number"].iloc[0] if not df.empty else fake.random_number(digits=8),
        statement_period=f"{fake.date_between(start_date='-1y', end_date='today').strftime('%B %d, %Y')} - {current_date}",
        statement_date=current_date,
        summary=summary,
        transactions=transactions,
        opening_balance=summary["beginning_balance"],
        opening_balance_debit="0.00",  # Adjust based on your data
        opening_balance_credit="0.00",  # Adjust based on your data
        total=summary["ending_balance"],
        total_debit=summary["withdrawals_total"],
        total_credit=summary["deposits_total"],
        client_number=fake.random_number(digits=6),
        date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=80).strftime("%Y-%m-%d"),
        customer_account_number=df["account_number"].iloc[0] if not df.empty else fake.random_number(digits=8),
        customer_iban=f"GB{fake.random_number(digits=2)} {fake.random_upper_letters(length=4)} {fake.random_number(digits=6)} {fake.random_number(digits=8)}",
        customer_bank_name="Citibank UK Limited",
        important_account_info=important_account_info,
        footnotes="",  # Placeholder, populate if needed
        disclosures="",  # Placeholder, populate if needed
        terms=""  # Placeholder, populate if needed
    )

    # Save HTML and generate PDF (assuming existing logic)
    html_file = os.path.join(output_dir, f"{account_holder.replace(' ', '_')}_{bank_key}_statement.html")
    pdf_file = os.path.join(output_dir, f"{account_holder.replace(' ', '_')}_{bank_key}_statement.pdf")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    # Assuming you have a PDF generation function (e.g., using wkhtmltopdf)
    # generate_pdf(html_file, pdf_file)  # Implement this based on your setup
    return [(html_file, pdf_file)]