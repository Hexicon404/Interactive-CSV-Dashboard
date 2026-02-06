# Interactive CSV Dashboard

A Streamlit-based tool for exploring CSV datasets without writing code. Designed for analysts and non-technical users who need to quickly understand their data, apply basic filters, and generate common visualisations.

## Intended Use Case

This dashboard is suited for situations where you need to:
- Quickly inspect a new dataset before deeper analysis
- Share data exploration capabilities with colleagues who don't use Python
- Generate simple charts for internal reports or presentations

It is not intended for production data pipelines, large-scale datasets, or advanced statistical analysis.

## Features

- **Data upload**: Load any CSV file via the sidebar
- **Structure overview**: View row/column counts, column types, and memory usage
- **Missing value check**: Identify columns with incomplete data
- **Automatic type conversion**: Attempts to convert text columns that look like numbers or dates
- **Interactive filtering**: Filter by categorical values or numeric ranges
- **Visualisations**:
  - Distribution histogram for numeric columns
  - Bar chart for categorical breakdowns
  - Scatter plot for two-variable relationships
- **Download options**: Export filtered data or summary statistics as CSV

## How to Run Locally

1. Clone this repository:
   ```bash
   git clone https://github.com/Hexicon404/Interactive-CSV-Dashboard
   cd Interactive-CSV-Dashboard
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   streamlit run app.py
   ```

5. Open your browser to `http://localhost:8501`

## Project Structure

```
Interactive-CSV-Dashboard/
├── app.py              # Main application (all logic in one file)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Limitations

- **File size**: Large files (>100MB) may cause slow performance or timeouts
- **File format**: Only CSV files are supported; Excel files (.xlsx) are not handled
- **Data types**: Automatic type conversion uses simple heuristics and may not catch all cases
- **Visualisations**: Limited to three chart types; no custom styling options
- **No persistence**: Data is not saved between sessions; refreshing the page clears all state
- **Single user**: Not designed for concurrent multi-user access

## Possible Extensions

If developing this further, reasonable additions might include:

- Excel file support (.xlsx, .xls)
- More robust date parsing with format specification
- Additional chart types (box plots, time series)
- Option to drop or fill missing values before download
- Caching for larger files
- Export charts as images

## Technical Notes

- Built with Streamlit 1.28+
- Uses Plotly for interactive charts
- Tested with Python 3.9 and 3.11

## Licence

MIT
