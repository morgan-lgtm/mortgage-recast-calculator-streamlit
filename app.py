import streamlit as st
import math
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
import base64
import io

# Set page config
st.set_page_config(page_title="Mortgage Recast Calculator", layout="wide")

# Custom CSS for better styling
st.markdown("""
    <style>
    .stAlert {
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .tooltip {
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted black;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state for comparison
if 'scenarios' not in st.session_state:
    st.session_state.scenarios = []

def validate_inputs(remaining_amount, current_payment, lump_sum_payment, years_remaining, annual_interest_rate):
    """Validate user inputs and return list of warnings"""
    warnings = []
    
    if lump_sum_payment >= remaining_amount:
        warnings.append("⚠️ Lump sum payment equals or exceeds remaining loan amount!")
        
    min_payment = calculate_monthly_payment(remaining_amount, annual_interest_rate, years_remaining)
    if current_payment < min_payment:
        warnings.append(f"⚠️ Current payment ({current_payment:.2f}) is less than minimum required payment ({min_payment:.2f})!")
        
    if years_remaining == 0:
        warnings.append("⚠️ Years remaining cannot be zero!")
        
    return warnings

def calculate_monthly_payment(principal, annual_rate, years):
    """Calculate monthly mortgage payment"""
    if years == 0:
        return 0
    monthly_rate = annual_rate / 100 / 12
    number_of_payments = years * 12
    if monthly_rate == 0:
        return principal / number_of_payments
    payment = (monthly_rate * principal) / (1 - math.pow(1 + monthly_rate, -number_of_payments))
    return payment

def calculate_total_interest(schedule):
    """Calculate total interest paid over the life of the loan"""
    return schedule["Interest"].sum()

def generate_amortization_schedule(principal, annual_rate, years, monthly_payment):
    """Generate detailed amortization schedule"""
    schedule = []
    remaining_principal = principal
    monthly_rate = annual_rate / 100 / 12
    total_payments = years * 12

    for payment_number in range(1, total_payments + 1):
        interest_payment = remaining_principal * monthly_rate
        principal_payment = monthly_payment - interest_payment
        
        if principal_payment > remaining_principal:
            principal_payment = remaining_principal
            monthly_payment = interest_payment + principal_payment
            
        remaining_principal = remaining_principal - principal_payment

        schedule.append({
            "Payment Number": payment_number,
            "Payment Date": (datetime.now().replace(day=1) + pd.DateOffset(months=payment_number-1)).strftime('%Y-%m-%d'),
            "Payment": monthly_payment,
            "Principal": principal_payment,
            "Interest": interest_payment,
            "Remaining Principal": remaining_principal,
            "Cumulative Interest": sum(row["Interest"] for row in schedule) + interest_payment
        })

        if remaining_principal <= 0:
            break

    return pd.DataFrame(schedule)

def export_to_csv(original_schedule, recast_schedule):
    """Export schedules to CSV"""
    buffer = io.BytesIO()
    
    # Create a writer to write to bytes buffer
    writer = pd.ExcelWriter(buffer, engine='xlsxwriter')
    
    # Write each dataframe to a different worksheet
    original_schedule.to_excel(writer, sheet_name='Original Schedule', index=False)
    recast_schedule.to_excel(writer, sheet_name='Recast Schedule', index=False)
    
    writer.close()
    
    return buffer

# Sidebar inputs with tooltips
st.sidebar.header("📝 Loan Details")

col1, col2 = st.sidebar.columns(2)
with col1:
    original_loan_amount = st.number_input(
        "Original Loan Amount ($)",
        min_value=0.0,
        value=720000.0,
        step=1000.0,
        help="The initial amount borrowed"
    )

with col2:
    remaining_amount = st.number_input(
        "Current Balance ($)",
        min_value=0.0,
        value=529000.0,
        step=1000.0,
        help="The current outstanding balance on your loan"
    )

col3, col4 = st.sidebar.columns(2)
with col3:
    annual_interest_rate = st.number_input(
        "Interest Rate (%)",
        min_value=0.0,
        max_value=100.0,
        value=7.125,
        step=0.125,
        help="Annual interest rate as a percentage"
    )

with col4:
    years_remaining = st.number_input(
        "Years Remaining",
        min_value=0,
        value=29,
        step=1,
        help="Number of years left on your mortgage"
    )

col5, col6 = st.sidebar.columns(2)
with col5:
    current_payment = st.number_input(
        "Current Payment ($)",
        min_value=0.0,
        value=4800.0,
        step=50.0,
        help="Your current monthly payment amount"
    )

with col6:
    lump_sum_payment = st.number_input(
        "Lump Sum Payment ($)",
        min_value=0.0,
        value=100000.0,
        step=1000.0,
        help="Amount you plan to pay towards principal"
    )

recast_fee = st.sidebar.number_input(
    "Recast Fee ($)",
    min_value=0.0,
    value=250.0,
    step=50.0,
    help="One-time fee charged by your lender for recasting"
)

# Main content
st.title("🏡 Mortgage Recast Calculator")
st.markdown("""
This calculator helps you evaluate the impact of making a lump sum payment and recasting your mortgage. 
A recast recalculates your monthly payments based on the new principal balance while keeping the original term and interest rate.
""")

# Validate inputs
warnings = validate_inputs(remaining_amount, current_payment, lump_sum_payment, 
                         years_remaining, annual_interest_rate)
for warning in warnings:
    st.warning(warning)

# Calculate new remaining principal
new_remaining_principal = remaining_amount - lump_sum_payment

if new_remaining_principal <= 0:
    st.error("❌ Lump sum payment exceeds the remaining loan amount!")
else:
    # Calculate new monthly payment
    new_monthly_payment = calculate_monthly_payment(
        new_remaining_principal,
        annual_interest_rate,
        years_remaining
    )
    
    # Generate schedules
    original_schedule = generate_amortization_schedule(
        remaining_amount,
        annual_interest_rate,
        years_remaining,
        current_payment
    )
    
    recast_schedule = generate_amortization_schedule(
        new_remaining_principal,
        annual_interest_rate,
        years_remaining,
        new_monthly_payment
    )
    
    # Calculate metrics
    monthly_savings = current_payment - new_monthly_payment
    total_payment_before = current_payment * years_remaining * 12
    total_payment_after = (new_monthly_payment * years_remaining * 12) + lump_sum_payment + recast_fee
    interest_savings = total_payment_before - total_payment_after
    original_total_interest = calculate_total_interest(original_schedule)
    recast_total_interest = calculate_total_interest(recast_schedule)
    interest_savings_actual = original_total_interest - recast_total_interest
    
    # Display results in an organized layout
    st.header("💰 Recast Analysis")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "New Monthly Payment",
            f"${new_monthly_payment:.2f}",
            f"-${monthly_savings:.2f}",
            help="Your new monthly payment after recast"
        )
    with col2:
        st.metric(
            "Total Interest Saved",
            f"${interest_savings_actual:.2f}",
            help="Total interest savings over the life of the loan"
        )
    with col3:
        years_to_recoup = recast_fee / monthly_savings if monthly_savings > 0 else float('inf')
        st.metric(
            "Months to Recoup Recast Fee",
            f"{years_to_recoup:.1f}",
            help="Number of months it will take for monthly savings to exceed recast fee"
        )

    # Detailed metrics in expandable section
    with st.expander("📊 Detailed Metrics"):
        col4, col5, col6 = st.columns(3)
        with col4:
            st.metric("Original Total Interest", f"${original_total_interest:.2f}")
            st.metric("New Total Interest", f"${recast_total_interest:.2f}")
        with col5:
            st.metric("Total Payments (Original)", f"${total_payment_before:.2f}")
            st.metric("Total Payments (After Recast)", f"${total_payment_after:.2f}")
        with col6:
            st.metric("Break-even Point", f"{(lump_sum_payment/monthly_savings):.1f} months")
            st.metric("Interest Rate", f"{annual_interest_rate}%")

    # Visualization section
    st.header("📈 Visual Analysis")
    
    # Create comparison plot
    fig = go.Figure()
    
    # Original vs Recast Principal Balance
    fig.add_trace(go.Scatter(
        x=original_schedule["Payment Date"],
        y=original_schedule["Remaining Principal"],
        name="Original Balance",
        line=dict(color="#1f77b4", width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=recast_schedule["Payment Date"],
        y=recast_schedule["Remaining Principal"],
        name="Recast Balance",
        line=dict(color="#2ca02c", width=2)
    ))
    
    fig.update_layout(
        title="Principal Balance Comparison",
        xaxis_title="Date",
        yaxis_title="Principal Balance ($)",
        hovermode="x unified",
        template="plotly_white"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Interest comparison plot
    fig2 = go.Figure()
    
    fig2.add_trace(go.Scatter(
        x=original_schedule["Payment Date"],
        y=original_schedule["Cumulative Interest"],
        name="Original Cumulative Interest",
        line=dict(color="#ff7f0e", width=2)
    ))
    
    fig2.add_trace(go.Scatter(
        x=recast_schedule["Payment Date"],
        y=recast_schedule["Cumulative Interest"],
        name="Recast Cumulative Interest",
        line=dict(color="#d62728", width=2)
    ))
    
    fig2.update_layout(
        title="Cumulative Interest Comparison",
        xaxis_title="Date",
        yaxis_title="Cumulative Interest ($)",
        hovermode="x unified",
        template="plotly_white"
    )
    
    st.plotly_chart(fig2, use_container_width=True)

    # Export functionality
    st.header("📑 Export Data")
    
    excel_buffer = export_to_csv(original_schedule, recast_schedule)
    
    st.download_button(
        label="Download Detailed Schedules (Excel)",
        data=excel_buffer.getvalue(),
        file_name=f"mortgage_recast_analysis_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.ms-excel"
    )

    # Additional information
    st.header("ℹ️ Additional Information")
    st.markdown("""
    ### Key Takeaways:
    * Your monthly payment will decrease by **${:.2f}**
    * You'll save **${:.2f}** in total interest over the life of the loan
    * It will take **{:.1f}** months to recoup the recast fee
    
    ### Important Notes:
    * This analysis assumes a fixed interest rate
    * The recast fee is typically a one-time cost
    * Additional principal payments can be made after recasting
    * Contact your lender for specific recast requirements and fees
    """.format(monthly_savings, interest_savings_actual, years_to_recoup))

    # Save scenario for comparison if requested
    if st.button("Save This Scenario for Comparison"):
        scenario = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "lump_sum": lump_sum_payment,
            "new_payment": new_monthly_payment,
            "total_savings": interest_savings_actual,
            "months_to_recoup": years_to_recoup
        }
        st.session_state.scenarios.append(scenario)
        st.success("Scenario saved!")

    # Display saved scenarios
    if st.session_state.scenarios:
        st.header("📊 Saved Scenarios")
        scenarios_df = pd.DataFrame(st.session_state.scenarios)
        st.dataframe(scenarios_df.style.format({
            "lump_sum": "${:,.2f}",
            "new_payment": "${:,.2f}",
            "total_savings": "${:,.2f}",
            "months_to_recoup": "{:,.1f}"
        }))