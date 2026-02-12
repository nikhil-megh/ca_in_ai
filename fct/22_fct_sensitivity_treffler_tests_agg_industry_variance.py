import os
from pathlib import Path
import pandas as pd
import numpy as np

# ======================== CONFIGURATION ========================

BASE_DIR = "/Users/nikhil/Documents/Thesis/FCT/Sensitivity_HOV"
TESTS_DIR = os.path.join(BASE_DIR, "Consumption_Similarity_Tests")
VARIANCE_OUTPUT_DIR = os.path.join(BASE_DIR, "Industry_Variance_Rankings")

FACTOR_FILES = {
    "labour": "/Users/nikhil/Documents/Thesis/Labour/EMP_figaro2025.xlsx",
    "capital": "/Users/nikhil/Documents/Thesis/Capital/CAPITAL_figaro2025.xlsx",
    "pct_all_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/AI_PATENTS_15_DEPRECIATION.xlsx",
    "pct_all_non_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/NON_AI_PATENTS_15_DEPRECIATION.xlsx",
    "pct_national_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/AI_PATENTS_15_DEPRECIATION.xlsx",
    "pct_national_non_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/NON_AI_PATENTS_15_DEPRECIATION.xlsx",
}

YEARS = list(range(2010, 2022))


def ensure_dirs():
    """Create output directory if it doesn't exist."""
    Path(VARIANCE_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def get_consolidated_excel_path(factor_name: str) -> str:
    """Get path to the consolidated consumption similarity file for a factor."""
    factor_tests_dir = os.path.join(TESTS_DIR, factor_name)
    return os.path.join(factor_tests_dir, "consumption_similarity_ALL_YEARS.xlsx")


def analyze_industry_variance(factor_name: str) -> pd.DataFrame:
    """
    Read Table3_Variance sheet and calculate mean variance across years for each industry.

    Returns a DataFrame with industries ranked by variance (highest to lowest).
    """
    # Read the consolidated file
    input_path = get_consolidated_excel_path(factor_name)

    if not os.path.exists(input_path):
        print(f"⚠️  Warning: File not found for {factor_name}: {input_path}")
        return None

    # Read Table3_Variance sheet
    table3 = pd.read_excel(input_path, sheet_name="Table3_Variance")

    # Group by industry and calculate statistics
    industry_stats = table3.groupby(['Code', 'Industry']).agg({
        'σ_g²': ['mean', 'std', 'min', 'max', 'count'],
        'Prop_i=j': 'mean',
        'N_obs': 'mean',
        'N_diag': 'mean'
    }).reset_index()

    # Flatten column names
    industry_stats.columns = [
        'Code',
        'Industry',
        'Mean_Variance',
        'Std_Variance',
        'Min_Variance',
        'Max_Variance',
        'N_Years',
        'Mean_Prop_Diagonal',
        'Mean_N_Obs',
        'Mean_N_Diag'
    ]

    # Sort by mean variance (descending)
    industry_stats = industry_stats.sort_values('Mean_Variance', ascending=False).reset_index(drop=True)

    # Add rank column
    industry_stats.insert(0, 'Rank', range(1, len(industry_stats) + 1))

    # Round for readability
    industry_stats['Mean_Variance'] = industry_stats['Mean_Variance'].round(6)
    industry_stats['Std_Variance'] = industry_stats['Std_Variance'].round(6)
    industry_stats['Min_Variance'] = industry_stats['Min_Variance'].round(6)
    industry_stats['Max_Variance'] = industry_stats['Max_Variance'].round(6)
    industry_stats['Mean_Prop_Diagonal'] = industry_stats['Mean_Prop_Diagonal'].round(4)
    industry_stats['Mean_N_Obs'] = industry_stats['Mean_N_Obs'].round(0).astype(int)
    industry_stats['Mean_N_Diag'] = industry_stats['Mean_N_Diag'].round(0).astype(int)

    return industry_stats


def create_detailed_variance_sheet(factor_name: str) -> pd.DataFrame:
    """
    Create a detailed sheet with variance by year for each industry.
    Pivoted so industries are rows and years are columns.
    """
    input_path = get_consolidated_excel_path(factor_name)

    if not os.path.exists(input_path):
        return None

    table3 = pd.read_excel(input_path, sheet_name="Table3_Variance")

    # Pivot to get year-by-year variance
    variance_by_year = table3.pivot_table(
        index=['Code', 'Industry'],
        columns='year',
        values='σ_g²'
    ).reset_index()

    # Calculate mean across years
    year_cols = [col for col in variance_by_year.columns if isinstance(col, int)]
    variance_by_year['Mean_Variance'] = variance_by_year[year_cols].mean(axis=1)

    # Sort by mean variance
    variance_by_year = variance_by_year.sort_values('Mean_Variance', ascending=False).reset_index(drop=True)

    # Add rank
    variance_by_year.insert(0, 'Rank', range(1, len(variance_by_year) + 1))

    # Round values
    for col in year_cols + ['Mean_Variance']:
        variance_by_year[col] = variance_by_year[col].round(6)

    return variance_by_year


def save_industry_variance_analysis(factor_name: str):
    """
    Save industry variance analysis for a given factor to Excel.
    Creates multiple sheets with different views of the data.
    """
    output_path = os.path.join(VARIANCE_OUTPUT_DIR, f"industry_variance_{factor_name}.xlsx")

    # Get the summary statistics
    summary = analyze_industry_variance(factor_name)

    if summary is None:
        print(f"❌ Skipping {factor_name} - no data found")
        return

    # Get the year-by-year detail
    detail = create_detailed_variance_sheet(factor_name)

    # Write to Excel with multiple sheets
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Sheet 1: Summary statistics
        summary.to_excel(writer, sheet_name='Summary', index=False)

        # Sheet 2: Variance by year (pivoted)
        if detail is not None:
            detail.to_excel(writer, sheet_name='Variance_by_Year', index=False)

        # Sheet 3: Top 20 industries
        summary.head(20).to_excel(writer, sheet_name='Top_20', index=False)

        # Sheet 4: Bottom 20 industries
        summary.tail(20).to_excel(writer, sheet_name='Bottom_20', index=False)

    print(f"✅ Saved: {output_path}")
    print(f"   Top 3 industries by variance:")
    for idx, row in summary.head(3).iterrows():
        print(f"      {row['Rank']}. {row['Industry']} ({row['Code']}): {row['Mean_Variance']:.6f}")


def create_comparative_summary():
    """
    Create a single Excel file comparing variance rankings across all factors.
    """
    output_path = os.path.join(VARIANCE_OUTPUT_DIR, "industry_variance_COMPARISON.xlsx")

    all_summaries = {}

    for factor_name in FACTOR_FILES.keys():
        summary = analyze_industry_variance(factor_name)
        if summary is not None:
            all_summaries[factor_name] = summary[['Rank', 'Code', 'Industry', 'Mean_Variance']]

    if not all_summaries:
        print("❌ No data available for comparison")
        return

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Create a sheet for each factor
        for factor_name, summary in all_summaries.items():
            sheet_name = factor_name[:31]  # Excel sheet name limit
            summary.to_excel(writer, sheet_name=sheet_name, index=False)

        # Create a comparison sheet with ranks across factors
        if len(all_summaries) > 1:
            # Get all industry codes
            all_codes = set()
            for summary in all_summaries.values():
                all_codes.update(summary['Code'].values)

            comparison_data = []
            for code in sorted(all_codes):
                row = {'Code': code}
                industry_name = None

                for factor_name, summary in all_summaries.items():
                    industry_row = summary[summary['Code'] == code]
                    if not industry_row.empty:
                        if industry_name is None:
                            industry_name = industry_row.iloc[0]['Industry']
                        row[f'{factor_name}_Rank'] = industry_row.iloc[0]['Rank']
                        row[f'{factor_name}_Variance'] = industry_row.iloc[0]['Mean_Variance']

                row['Industry'] = industry_name
                comparison_data.append(row)

            comparison_df = pd.DataFrame(comparison_data)
            # Reorder columns: Code, Industry, then factors
            cols = ['Code', 'Industry'] + [col for col in comparison_df.columns if col not in ['Code', 'Industry']]
            comparison_df = comparison_df[cols]
            comparison_df.to_excel(writer, sheet_name='Comparison', index=False)

    print(f"✅ Saved comparison: {output_path}")


def main():
    """Main execution function."""
    ensure_dirs()

    print(f"\n{'=' * 70}")
    print("INDUSTRY VARIANCE RANKING ANALYSIS")
    print(f"{'=' * 70}\n")

    # Process each factor
    for factor_name in FACTOR_FILES.keys():
        print(f"\nProcessing: {factor_name}")
        print("-" * 70)
        save_industry_variance_analysis(factor_name)

    # Create comparative summary
    print(f"\n{'=' * 70}")
    print("Creating Comparative Summary")
    print(f"{'=' * 70}")
    create_comparative_summary()

    print(f"\n{'=' * 70}")
    print("✅ ANALYSIS COMPLETE")
    print(f"{'=' * 70}")
    print(f"Output directory: {VARIANCE_OUTPUT_DIR}")


if __name__ == "__main__":
    main()