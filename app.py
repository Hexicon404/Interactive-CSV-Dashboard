"""
CSV Insights Dashboard
A simple interactive tool for exploring CSV datasets.

Built for non-technical users who need to quickly understand 
their data without writing code.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="CSV Insights Dashboard",
    page_icon="📊",
    layout="wide"
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_csv(uploaded_file):
    """
    Attempt to load a CSV file with sensible defaults.
    Returns the dataframe or None if loading fails.
    """
    try:
        df = pd.read_csv(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Could not read file: {e}")
        return None


def get_column_types(df):
    """
    Categorise columns into numeric vs categorical for filtering purposes.
    We use a simple heuristic: if pandas says it's numeric, treat it as numeric.
    """
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=['number']).columns.tolist()
    return numeric_cols, categorical_cols


def calculate_missing_values(df):
    """
    Return a summary of missing values per column.
    Only includes columns that actually have missing data.
    """
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(1)
    
    summary = pd.DataFrame({
        'Missing Count': missing,
        'Missing %': missing_pct
    })
    
    # Only show columns with missing values
    summary = summary[summary['Missing Count'] > 0]
    return summary.sort_values('Missing Count', ascending=False)


def attempt_type_conversion(df):
    """
    Try to convert object columns that look like dates or numbers.
    This is intentionally conservative - we only convert when confident.
    Returns the converted dataframe and a list of changes made.
    """
    df_converted = df.copy()
    changes = []
    
    for col in df_converted.select_dtypes(include=['object']).columns:
        # Skip columns with too many missing values
        if df_converted[col].isnull().sum() / len(df_converted) > 0.5:
            continue
            
        # Try numeric conversion first
        try:
            numeric_converted = pd.to_numeric(df_converted[col], errors='coerce')
            # Only accept if most values converted successfully
            if numeric_converted.notna().sum() / df_converted[col].notna().sum() > 0.9:
                df_converted[col] = numeric_converted
                changes.append(f"'{col}' → numeric")
                continue
        except:
            pass
        
        # Try datetime conversion
        try:
            datetime_converted = pd.to_datetime(df_converted[col], errors='coerce')
            if datetime_converted.notna().sum() / df_converted[col].notna().sum() > 0.9:
                df_converted[col] = datetime_converted
                changes.append(f"'{col}' → datetime")
        except:
            pass
    
    return df_converted, changes


def convert_df_to_csv(df):
    """Convert dataframe to CSV bytes for download."""
    return df.to_csv(index=False).encode('utf-8')


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    st.title("📊 CSV Insights Dashboard")
    st.markdown("Upload a CSV file to explore its structure, filter data, and create visualisations.")
    
    # -------------------------------------------------------------------------
    # SIDEBAR: File Upload
    # -------------------------------------------------------------------------
    
    with st.sidebar:
        st.header("Data Upload")
        uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
        
        # NEW: Demo Mode Toggle
        use_sample = st.checkbox("Use sample data for demo")
    
    # LOGIC: Handle Sample Data vs Upload
    if use_sample:
        uploaded_file = "sample_data.csv" # Tells the app to look for this file
        try:
            df_raw = pd.read_csv(uploaded_file)
            st.sidebar.success("✅ Demo Data Loaded")
        except FileNotFoundError:
            st.error("⚠️ Error: sample_data.csv not found in folder.")
            return
            
    elif uploaded_file is not None:
        # Load the user's uploaded file
        df_raw = load_csv(uploaded_file)
        
    else:
        # If nothing is selected, show instructions and stop
        st.info("👈 Upload a CSV file or check 'Use sample data' to start.")
        st.markdown("---")
        # (Keep your existing explanation text here...)
        return
    
    # -------------------------------------------------------------------------
    # LOAD DATA
    # -------------------------------------------------------------------------
    
    df_raw = load_csv(uploaded_file)
    
    if df_raw is None:
        return
    
    # Store in session state so we don't reload on every interaction
    # ---------------------------------------------------------------------
    # FIX: Determine the filename safely (Handle String vs. File Object)
    # ---------------------------------------------------------------------
    if isinstance(uploaded_file, str):
        current_filename = uploaded_file  # It's just the string "sample_data.csv"
    else:
        current_filename = uploaded_file.name  # It's a real file object

    # Check if we need to reload data (Using the safe 'current_filename')
    if 'df' not in st.session_state or st.session_state.get('filename') != current_filename:
        with st.spinner('Loading data...'):
            if isinstance(uploaded_file, str):
                # Load the local sample file
                try:
                    df = pd.read_csv(uploaded_file)
                except FileNotFoundError:
                    st.error(f"❌ Error: {uploaded_file} not found. Make sure it is in the folder.")
                    st.stop()
            else:
                # Load the user uploaded file
                df = load_csv(uploaded_file)

            if df is not None:
                st.session_state['df'] = df
                st.session_state['filename'] = current_filename
            else:
                st.stop()
    
    # Get the dataframe from session state
    df = st.session_state['df']
    
    # -------------------------------------------------------------------------
    # SECTION 1: Dataset Overview
    # -------------------------------------------------------------------------
    
    st.header("1. Dataset Overview")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", f"{len(df):,}")
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        st.metric("Memory", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")
    
    # Show type conversions if any were made
    if st.session_state.conversion_changes:
        with st.expander("Type conversions applied"):
            st.write("The following columns were automatically converted:")
            for change in st.session_state.conversion_changes:
                st.write(f"  • {change}")
    
    # Column information
    with st.expander("Column types", expanded=True):
        col_info = pd.DataFrame({
            'Column': df.columns,
            'Type': df.dtypes.astype(str).values,
            'Non-Null Count': df.notna().sum().values,
            'Sample Value': [df[col].dropna().iloc[0] if df[col].notna().any() else 'N/A' for col in df.columns]
        })
        st.dataframe(col_info, use_container_width=True, hide_index=True)
    
    # Preview
    with st.expander("Data preview (first 10 rows)"):
        st.dataframe(df.head(10), use_container_width=True)
    
    # -------------------------------------------------------------------------
    # SECTION 2: Missing Values
    # -------------------------------------------------------------------------
    
    st.header("2. Data Quality Check")
    
    missing_summary = calculate_missing_values(df)
    
    if len(missing_summary) == 0:
        st.success("No missing values found in this dataset.")
    else:
        st.warning(f"Found missing values in {len(missing_summary)} column(s).")
        st.dataframe(missing_summary, use_container_width=True)
    
    # -------------------------------------------------------------------------
    # SECTION 3: Interactive Filtering
    # -------------------------------------------------------------------------
    
    st.header("3. Filter & Explore")
    
    numeric_cols, categorical_cols = get_column_types(df)
    
    # Start with full dataset
    df_filtered = df.copy()
    
    # Categorical filters
    if categorical_cols:
        st.subheader("Filter by Category")
        
        # Let user pick which categorical column to filter
        filter_cat_col = st.selectbox(
            "Select a categorical column to filter",
            options=['None'] + categorical_cols,
            key='cat_filter_col'
        )
        
        if filter_cat_col != 'None':
            unique_values = df[filter_cat_col].dropna().unique().tolist()
            
            # Only show multiselect if there aren't too many unique values
            if len(unique_values) <= 50:
                selected_values = st.multiselect(
                    f"Select values from '{filter_cat_col}'",
                    options=unique_values,
                    default=unique_values,
                    key='cat_filter_values'
                )
                if selected_values:
                    df_filtered = df_filtered[df_filtered[filter_cat_col].isin(selected_values)]
            else:
                st.info(f"'{filter_cat_col}' has {len(unique_values)} unique values. Try the numeric range filter or search in the data preview instead.")
    
    # Numeric range filter
    if numeric_cols:
        st.subheader("Filter by Numeric Range")
        
        filter_num_col = st.selectbox(
            "Select a numeric column to filter",
            options=['None'] + numeric_cols,
            key='num_filter_col'
        )
        
        if filter_num_col != 'None':
            col_min = float(df[filter_num_col].min())
            col_max = float(df[filter_num_col].max())
            
            # Handle edge case where min equals max
            if col_min == col_max:
                st.info(f"All values in '{filter_num_col}' are {col_min}")
            else:
                range_values = st.slider(
                    f"Select range for '{filter_num_col}'",
                    min_value=col_min,
                    max_value=col_max,
                    value=(col_min, col_max),
                    key='num_filter_range'
                )
                df_filtered = df_filtered[
                    (df_filtered[filter_num_col] >= range_values[0]) & 
                    (df_filtered[filter_num_col] <= range_values[1])
                ]
    
    # Show filtered data summary
    st.markdown(f"**Filtered dataset:** {len(df_filtered):,} rows ({len(df_filtered)/len(df)*100:.1f}% of original)")
    
    with st.expander("View filtered data"):
        st.dataframe(df_filtered.head(100), use_container_width=True)
        if len(df_filtered) > 100:
            st.caption("Showing first 100 rows")
    
    # -------------------------------------------------------------------------
    # SECTION 4: Visualisations
    # -------------------------------------------------------------------------
    
    st.header("4. Visualisations")
    
    # We use the filtered data for all plots
    df_plot = df_filtered
    
    # Recalculate column types for filtered data (in case filtering removed all of one type)
    numeric_cols_plot, categorical_cols_plot = get_column_types(df_plot)
    
    viz_tab1, viz_tab2, viz_tab3 = st.tabs(["Distribution", "Category Breakdown", "Relationship"])
    
    # --- Distribution Plot ---
    with viz_tab1:
        st.subheader("Distribution of a Numeric Column")
        
        if not numeric_cols_plot:
            st.info("No numeric columns available for distribution plot.")
        else:
            dist_col = st.selectbox(
                "Select column",
                options=numeric_cols_plot,
                key='dist_col'
            )
            
            fig = px.histogram(
                df_plot,
                x=dist_col,
                title=f"Distribution of {dist_col}",
                labels={dist_col: dist_col},
                template='plotly_white'
            )
            fig.update_layout(
                showlegend=False,
                title_x=0,
                margin=dict(t=50, l=50, r=30, b=50)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Basic stats below the chart
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Mean", f"{df_plot[dist_col].mean():.2f}")
            with col2:
                st.metric("Median", f"{df_plot[dist_col].median():.2f}")
            with col3:
                st.metric("Std Dev", f"{df_plot[dist_col].std():.2f}")
            with col4:
                st.metric("Range", f"{df_plot[dist_col].max() - df_plot[dist_col].min():.2f}")
    
    # --- Category Breakdown ---
    with viz_tab2:
        st.subheader("Breakdown by Category")
        
        if not categorical_cols_plot:
            st.info("No categorical columns available for breakdown.")
        else:
            cat_col = st.selectbox(
                "Select categorical column",
                options=categorical_cols_plot,
                key='cat_col'
            )
            
            # Count values
            value_counts = df_plot[cat_col].value_counts().reset_index()
            value_counts.columns = [cat_col, 'Count']
            
            # Limit to top 20 for readability
            if len(value_counts) > 20:
                value_counts = value_counts.head(20)
                st.caption("Showing top 20 categories")
            
            fig = px.bar(
                value_counts,
                x=cat_col,
                y='Count',
                title=f"Count by {cat_col}",
                template='plotly_white'
            )
            fig.update_layout(
                title_x=0,
                margin=dict(t=50, l=50, r=30, b=50),
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # --- Relationship Plot ---
    with viz_tab3:
        st.subheader("Relationship Between Two Variables")
        
        if len(numeric_cols_plot) < 2:
            st.info("Need at least two numeric columns to show relationships.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                x_col = st.selectbox(
                    "X-axis",
                    options=numeric_cols_plot,
                    key='scatter_x'
                )
            with col2:
                # Default to second numeric column for y
                y_default = numeric_cols_plot[1] if numeric_cols_plot[1] != x_col else numeric_cols_plot[0]
                y_col = st.selectbox(
                    "Y-axis",
                    options=numeric_cols_plot,
                    index=numeric_cols_plot.index(y_default),
                    key='scatter_y'
                )
            
            # Optional color by category
            color_col = None
            if categorical_cols_plot:
                color_option = st.selectbox(
                    "Colour by (optional)",
                    options=['None'] + categorical_cols_plot,
                    key='scatter_color'
                )
                if color_option != 'None':
                    # Only use color if not too many categories
                    if df_plot[color_option].nunique() <= 10:
                        color_col = color_option
                    else:
                        st.caption(f"'{color_option}' has too many unique values for colouring. Showing without colour.")
            
            # Sample if dataset is large (scatter plots get slow with many points)
            if len(df_plot) > 5000:
                df_scatter = df_plot.sample(n=5000, random_state=42)
                st.caption("Showing random sample of 5,000 points for performance")
            else:
                df_scatter = df_plot
            
            fig = px.scatter(
                df_scatter,
                x=x_col,
                y=y_col,
                color=color_col,
                title=f"{y_col} vs {x_col}",
                template='plotly_white',
                opacity=0.6
            )
            fig.update_layout(
                title_x=0,
                margin=dict(t=50, l=50, r=30, b=50)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # -------------------------------------------------------------------------
    # SECTION 5: Download Options
    # -------------------------------------------------------------------------
    
    st.header("5. Download")
    
    download_option = st.radio(
        "What would you like to download?",
        options=["Filtered dataset", "Summary statistics"],
        horizontal=True
    )
    
    if download_option == "Filtered dataset":
        csv_data = convert_df_to_csv(df_filtered)
        st.download_button(
            label="Download filtered data as CSV",
            data=csv_data,
            file_name="filtered_data.csv",
            mime="text/csv"
        )
        st.caption(f"This will download {len(df_filtered):,} rows and {len(df_filtered.columns)} columns.")
    
    else:
        # Generate summary statistics
        summary = df_filtered.describe(include='all').T
        summary = summary.round(2)
        csv_summary = convert_df_to_csv(summary.reset_index().rename(columns={'index': 'Column'}))
        
        st.download_button(
            label="Download summary statistics as CSV",
            data=csv_summary,
            file_name="summary_statistics.csv",
            mime="text/csv"
        )
        
        with st.expander("Preview summary"):
            st.dataframe(summary, use_container_width=True)


# =============================================================================
# RUN APPLICATION
# =============================================================================

if __name__ == "__main__":
    main()
