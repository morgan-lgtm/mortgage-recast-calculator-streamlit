# 🏡 Mortgage Recast Calculator

A simple and interactive Streamlit app to explore mortgage recast scenarios. Adjust your mortgage details to see how lump-sum payments and recast fees can impact your monthly payments and overall interest.

https://mortgage-recast-calculator-app-eenunvt4qblpjecz8bqrt3.streamlit.app

## Features

- **Input Parameters**: Original loan amount, remaining balance, interest rate, years remaining, current payment, lump-sum payment, and recast fee.
- **Financial Summary**: Displays new monthly payment, remaining principal, total payments before and after recast, and interest savings.
- **Interactive Visualizations**:
  - Remaining Principal Over Time
  - Interest vs. Principal Payments
- **Detailed Amortization Schedules**: Expandable sections to view payment breakdowns.

## Getting Started

### Prerequisites

- Python 3.7+
- Streamlit
- Plotly
- Pandas

### Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/mortgage-recast-calculator.git
    cd mortgage-recast-calculator
    ```

2. **Install dependencies:**

    ```bash
    pip install streamlit plotly pandas
    ```

### Running the App

```bash
streamlit run mortgage_recast_app.py
