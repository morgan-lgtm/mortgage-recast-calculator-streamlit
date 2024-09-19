import streamlit as st
import math
import pandas as pd
import plotly.graph_objects as go

# Set the title of the app
st.title("🏡 Mortgage Recast Calculator")

# Sidebar for user inputs
st.sidebar.header("Input Parameters")

# Input fields with updated default values
original_loan_amount = st.sidebar.number_input(
    "Original Loan Amount ($)",
    min_value=0.0,
    value=720000.0,
    step=1000.0
)

remaining_amount = st.sidebar.number_input(
    "Remaining Loan Amount ($)",
    min_value=0.0,
    value=529000.0,
    step=1000.0
)

annual_interest_rate = st.sidebar.number_input(
    "Annual Interest Rate (%)",
    min_value=0.0,
    max_value=100.0,
    value=7.125,
    step=0.001
)

years_remaining = st.sidebar.number_input(
    "Years Remaining",
    min_value=0,
    value=29,
    step=1
)

current_payment = st.sidebar.number_input(
    "Current Monthly Payment ($)",
    min_value=0.0,
    value=4800.0,
    step=50.0
)

lump_sum_payment = st.sidebar.number_input(
    "Lump-Sum Payment Towards Principal ($)",
    min_value=0.0,
    value=1000.0,
    step=100.0
)

recast_fee = st.sidebar.number_input(
    "Recast Fee ($)",
    min_value=0.0,
    value=250.0,
    step=50.0
)

# Function to calculate monthly payment
def calculate_monthly_payment(principal, annual_rate, years):
    monthly_rate = annual_rate / 100 / 12
    number_of_payments = years * 12
    if monthly_rate == 0:
        return principal / number_of_payments
    payment = (monthly_rate * principal) / (1 - math.pow(1 + monthly_rate, -number_of_payments))
    return payment

# Updated function to generate amortization schedule
def generate_amortization_schedule(principal, annual_rate, years, monthly_payment):
    schedule = []
    remaining_principal = principal
    monthly_rate = annual_rate / 100 / 12
    total_payments = years * 12
    
    for payment_number in range(1, total_payments + 1):
        interest_payment = remaining_principal * monthly_rate
        principal_payment = min(monthly_payment - interest_payment, remaining_principal)
        remaining_principal = max(remaining_principal - principal_payment, 0)
        
        schedule.append({
            "Payment Number": payment_number,
            "Payment": monthly_payment,
            "Principal": principal_payment,
            "Interest": interest_payment,
            "Remaining Principal": remaining_principal
        })
        
        if remaining_principal == 0:
            break
    
    return pd.DataFrame(schedule)

# Calculate new remaining principal after lump-sum payment
new_remaining_principal = remaining_amount - lump_sum_payment

# Ensure the new principal is not negative
if new_remaining_principal < 0:
    st.error("❌ **Error:** Lump-sum payment exceeds the remaining loan amount.")
else:
    # Calculate new monthly payment
    new_monthly_payment = calculate_monthly_payment(
        new_remaining_principal,
        annual_interest_rate,
        years_remaining
    )

    # Calculate monthly savings
    monthly_savings = current_payment - new_monthly_payment

    # Calculate total payments before and after recast
    total_payment_before = current_payment * years_remaining * 12
    total_payment_after = new_monthly_payment * years_remaining * 12 + lump_sum_payment + recast_fee

    # Calculate interest savings
    interest_savings = total_payment_before - total_payment_after

    # Display the results
    st.header("🏦 Recast Results")

    st.subheader("New Loan Details")
    col1, col2, col3 = st.columns(3)
    col1.metric("New Monthly Payment", f"${new_monthly_payment:,.2f}")
    col2.metric("New Remaining Principal", f"${new_remaining_principal:,.2f}")
    col3.metric("Monthly Payment Reduction", f"${monthly_savings:,.2f}", delta=f"-{monthly_savings:,.2f}")

    st.subheader("Financial Summary")
    col4, col5 = st.columns(2)
    col4.metric("Total Payments Before Recast", f"${total_payment_before:,.2f}")
    col5.metric("Total Payments After Recast", f"${total_payment_after:,.2f}")

    st.subheader("Savings")
    col6, col7 = st.columns(2)
    col6.metric("Interest Savings", f"${interest_savings:,.2f}")
    col7.metric("Recast Fee", f"${recast_fee:,.2f}")

    st.info(
        "🔍 **Note:** A lump-sum payment reduces your principal, potentially saving you interest over the life of the loan. "
        "The recast fee is a one-time cost associated with recalculating your mortgage terms."
    )

    st.markdown("---")

    st.header("📊 Amortization Schedule Comparison")

    # Generate amortization schedules
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

    # Create a Plotly figure
    fig = go.Figure()

    # Original Remaining Principal
    fig.add_trace(
        go.Scatter(
            x=original_schedule["Payment Number"],
            y=original_schedule["Remaining Principal"],
            mode='lines',
            name='Original Remaining Principal',
            line=dict(color='blue')
        )
    )

    # Recast Remaining Principal
    fig.add_trace(
        go.Scatter(
            x=recast_schedule["Payment Number"],
            y=recast_schedule["Remaining Principal"],
            mode='lines',
            name='Recast Remaining Principal',
            line=dict(color='green')
        )
    )

    # Add titles and labels
    fig.update_layout(
        title="🔄 Remaining Principal Over Time",
        xaxis_title="Payment Number",
        yaxis_title="Remaining Principal ($)",
        hovermode="x unified",
        template="plotly_dark",
        xaxis=dict(range=[0, years_remaining * 12])  # Set x-axis range to match loan term
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📈 Detailed Amortization Schedules")

    # Expandable sections for detailed schedules
    with st.expander("🔍 Original Amortization Schedule"):
        st.dataframe(original_schedule.style.format({
            "Payment": "${:,.2f}",
            "Principal": "${:,.2f}",
            "Interest": "${:,.2f}",
            "Remaining Principal": "${:,.2f}"
        }))

    with st.expander("🔍 Recast Amortization Schedule"):
        st.dataframe(recast_schedule.style.format({
            "Payment": "${:,.2f}",
            "Principal": "${:,.2f}",
            "Interest": "${:,.2f}",
            "Remaining Principal": "${:,.2f}"
        }))

    st.markdown("---")

    st.header("📊 Interest vs. Principal Payments")

    # Create a stacked bar chart for original schedule
    fig2 = go.Figure()

    fig2.add_trace(
        go.Bar(
            x=original_schedule["Payment Number"],
            y=original_schedule["Interest"],
            name='Interest (Original)',
            marker_color='indianred'
        )
    )

    fig2.add_trace(
        go.Bar(
            x=original_schedule["Payment Number"],
            y=original_schedule["Principal"],
            name='Principal (Original)',
            marker_color='lightsalmon'
        )
    )

    fig2.add_trace(
        go.Bar(
            x=recast_schedule["Payment Number"],
            y=recast_schedule["Interest"],
            name='Interest (Recast)',
            marker_color='darkseagreen'
        )
    )

    fig2.add_trace(
        go.Bar(
            x=recast_schedule["Payment Number"],
            y=recast_schedule["Principal"],
            name='Principal (Recast)',
            marker_color='mediumseagreen'
        )
    )

    # Update layout for stacked bars
    fig2.update_layout(
        barmode='stack',
        title="💰 Interest vs. Principal Payments Over Time",
        xaxis_title="Payment Number",
        yaxis_title="Amount ($)",
        hovermode="x unified",
        template="plotly_dark",
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)'
        )
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    st.markdown("### 📝 Summary")
    st.markdown(
        "- **Original Schedule**: Displays how your loan would amortize without any recast.\n"
        "- **Recast Schedule**: Shows the amortization after applying the lump-sum payment and recast fee.\n"
        "- **Interest vs. Principal**: Illustrates the distribution of each payment between interest and principal.\n"
        "- **Remaining Principal Over Time**: Compares how quickly the principal is paid down in both scenarios.\n"
        f"- **Monthly Payment Reduction**: Your monthly payment is reduced by ${monthly_savings:,.2f} after the recast."
    )