"""
Consolidated FCT Analysis Script - Factor-Specific with Non-Tradable Exclusions
================================================================================
This script processes each factor separately, excluding specified non-tradable industries
for each factor, calculating matrices, FCT measures, and running statistical tests.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr, binomtest
import statsmodels.api as sm
from pathlib import Path


# =============================================================================
# CONFIGURATION
# =============================================================================

# Static mapping: factor -> list of non-tradable industry codes to exclude
FACTOR_NON_TRADABLE_MAP = {
    "labour": ["A01", "F", "C10T12", "O84", "P85"],
    "capital": ["L", "O84", "F"],
    "pct_all_ai_patents": ["C26", "Q86", "O84", "J59_60", "F"],
    "pct_all_non_ai_patents": ["F", "C26", "C21", "Q86", "J59_60"],
    "pct_national_ai_patents": ["C26", "Q86", "O84", "J59_60", "F"],
    "pct_national_non_ai_patents": ["F", "C26", "C21", "Q86", "J59_60"],
}

# Data source paths (UPDATE THESE TO YOUR ACTUAL PATHS)
FIGARO_DIR = "/Users/nikhil/Documents/Thesis/Figaro/IOT_v2"
GO_FILE = "/Users/nikhil/Documents/Thesis/Figaro/FIGARO_GrossOutput_2010_2021.xlsx"

FACTOR_FILES = {
    "labour": "/Users/nikhil/Documents/Thesis/Labour/EMP_figaro2025.xlsx",
    "capital": "/Users/nikhil/Documents/Thesis/Capital/CAPITAL_figaro2025.xlsx",
    "pct_all_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/AI_PATENTS_15_DEPRECIATION.xlsx",
    "pct_all_non_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/NON_AI_PATENTS_15_DEPRECIATION.xlsx",
    "pct_national_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/AI_PATENTS_15_DEPRECIATION.xlsx",
    "pct_national_non_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/NON_AI_PATENTS_15_DEPRECIATION.xlsx",
}

# Constants
COUNTRIES = [
    "AR", "AT", "AU", "BE", "BG", "BR", "CA", "CH", "CN", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FIGW1", "FR",
    "GB", "GR", "HR", "HU", "ID", "IE", "IN", "IT", "JP", "KR", "LT", "LU", "LV", "MT", "MX", "NL", "NO", "PL",
    "PT", "RO", "RU", "SA", "SE", "SI", "SK", "TR", "US", "ZA"
]

ALL_INDUSTRY_CODES = [
    "A01", "A02", "A03", "B", "C10T12", "C13T15", "C16", "C17", "C18", "C19",
    "C20", "C21", "C22", "C23", "C24", "C25", "C26", "C27", "C28", "C29",
    "C30", "C31_32", "C33", "D35", "E36", "E37T39", "F", "G45", "G46", "G47",
    "H49", "H50", "H51", "H52", "H53", "I", "J58", "J59_60", "J61", "J62_63",
    "K64", "K65", "K66", "L", "M69_70", "M71", "M72", "M73", "M74_75", "N77",
    "N78", "N79", "N80T82", "O84", "P85", "Q86", "Q87_88", "R90T92", "R93",
    "S94", "S95", "S96", "T", "U"
]

N_COUNTRIES = 46
N_INDUSTRIES = 64
N_FINAL_DEMAND = 5
YEARS = list(range(2010, 2022))


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_industry_mask(excluded_industries):
    """
    Returns boolean mask for sectors to KEEP (excluding specified industries).

    Args:
        excluded_industries: List of industry codes to exclude

    Returns:
        keep_mask: Boolean array where True means keep the sector
        all_sectors: List of all sector labels (country_industry format)
    """
    # Get indices of industries to exclude
    excluded_indices = [ALL_INDUSTRY_CODES.index(code) for code in excluded_industries]

    # Create sector labels for all 2944 sectors (46 countries × 64 industries)
    all_sectors = [f"{COUNTRIES[i // N_INDUSTRIES]}_{ALL_INDUSTRY_CODES[i % N_INDUSTRIES]}"
                   for i in range(N_COUNTRIES * N_INDUSTRIES)]

    # Keep sectors where industry index is NOT in excluded_indices
    keep_mask = np.array([(i % N_INDUSTRIES) not in excluded_indices
                          for i in range(len(all_sectors))])

    return keep_mask, all_sectors


# =============================================================================
# DATA LOADING FUNCTIONS
# =============================================================================

def load_IIO_matrix(year):
    """Load Inter-Industry Output matrix for a given year."""
    file_path = os.path.join(FIGARO_DIR, f"matrix_eu-ic-io_ind-by-ind_25ed_{year}_v2.csv")
    df = pd.read_csv(file_path, header=None, low_memory=False)

    # Row labels are in column 0 (skip header row)
    row_labels = df.iloc[1:N_COUNTRIES*N_INDUSTRIES+1, 0].values

    # Column labels are in row 0, starting from col 1
    col_labels = df.iloc[0, 1:N_COUNTRIES*N_INDUSTRIES+1].values

    # Extract numeric block (skip row 0 label row + col 0)
    iio_numeric = df.iloc[1:N_COUNTRIES*N_INDUSTRIES+1,
                          1:N_COUNTRIES*N_INDUSTRIES+1].apply(pd.to_numeric, errors='coerce')

    # Reassign proper names
    iio_numeric.index = row_labels
    iio_numeric.columns = col_labels

    return iio_numeric


def load_GO_vector(year, go_df):
    """Load Gross Output vector for a given year."""
    return go_df[str(year)].values


# =============================================================================
# MATRIX COMPUTATION FUNCTIONS
# =============================================================================

def compute_net_trade_vectors(factor, excluded_industries, output_dir):
    """Compute net trade vectors excluding specified industries."""
    print(f"\n  → Computing Net Trade Vectors (excluding {len(excluded_industries)} industries)...")

    net_trade_dir = os.path.join(output_dir, "Net_Trade_Vectors")
    os.makedirs(net_trade_dir, exist_ok=True)

    # Get mask for industries to keep
    keep_mask, all_sectors = get_industry_mask(excluded_industries)
    n_reduced = sum(keep_mask)

    print(f"    Reduced sector count: {n_reduced} (from {N_COUNTRIES * N_INDUSTRIES})")

    for year in YEARS:
        # Load FIGARO data
        file_path = os.path.join(FIGARO_DIR, f"matrix_eu-ic-io_ind-by-ind_25ed_{year}_v2.csv")
        df = pd.read_csv(file_path, header=None, low_memory=False)
        df_numeric = df.apply(pd.to_numeric, errors='coerce')
        df_numeric = df_numeric.dropna(how='all', axis=0).dropna(how='all', axis=1)
        M = df_numeric.to_numpy()

        # Drop last 6 rows (value added)
        M = M[:-6, :]

        # Split into intermediate and final demand
        inter_start, inter_end = 0, N_COUNTRIES * N_INDUSTRIES
        fd_start, fd_end = inter_end, inter_end + N_COUNTRIES * N_FINAL_DEMAND

        inter_matrix = M[:, inter_start:inter_end]
        fd_matrix = M[:, fd_start:fd_end]

        # Aggregate at country level
        inter_country = np.hstack([
            inter_matrix[:, i * N_INDUSTRIES:(i + 1) * N_INDUSTRIES].sum(axis=1, keepdims=True)
            for i in range(N_COUNTRIES)
        ])

        fd_country = np.hstack([
            fd_matrix[:, i * N_FINAL_DEMAND:(i + 1) * N_FINAL_DEMAND].sum(axis=1, keepdims=True)
            for i in range(N_COUNTRIES)
        ])

        # Total use
        total_use = inter_country + fd_country

        # Zero out intra-country flows
        for i in range(N_COUNTRIES):
            row_start = i * N_INDUSTRIES
            row_end = (i + 1) * N_INDUSTRIES
            total_use[row_start:row_end, i] = 0

        # Export column
        export_col = total_use.sum(axis=1, keepdims=True)

        # Multiply by -1 and replace diagonal
        total_use_neg = -1 * total_use
        for i in range(N_COUNTRIES):
            row_start = i * N_INDUSTRIES
            row_end = (i + 1) * N_INDUSTRIES
            total_use_neg[row_start:row_end, i] = export_col[row_start:row_end, 0]

        # ✅ EXCLUDE non-tradable industries using mask
        total_use_neg_reduced = total_use_neg[keep_mask, :]

        # Create row names (excluding non-tradable industries)
        row_names_reduced = [all_sectors[i] for i in range(len(all_sectors)) if keep_mask[i]]

        df_out = pd.DataFrame(total_use_neg_reduced, columns=COUNTRIES, index=row_names_reduced)
        out_path = os.path.join(net_trade_dir, f"net_trade_vector_{year}.csv")
        df_out.to_csv(out_path)

    print(f"    ✓ Saved {len(YEARS)} net trade vector files")


def compute_leontief_inverse(factor, excluded_industries, output_dir, go_df):
    """Compute Leontief inverse matrices excluding specified industries."""
    print(f"\n  → Computing Leontief Inverse Matrices (excluding {len(excluded_industries)} industries)...")

    leontief_dir = os.path.join(output_dir, "Leontief_Inverse_Matrix")
    os.makedirs(leontief_dir, exist_ok=True)

    # Get mask for industries to keep
    keep_mask, all_sectors = get_industry_mask(excluded_industries)

    for year in YEARS:
        # Load full IIO matrix
        IIO = load_IIO_matrix(year)
        GO = load_GO_vector(year, go_df)

        # ✅ EXCLUDE non-tradable industries from IIO (rows and columns) using mask
        IIO_reduced = IIO.iloc[keep_mask, keep_mask]
        GO_reduced = GO[keep_mask]

        # Compute technical coefficients matrix A
        eps_vec = np.full_like(GO_reduced, 1e-8)
        GOnz = GO_reduced + eps_vec
        A = IIO_reduced.values @ np.linalg.inv(np.diag(GOnz))
        A_df = pd.DataFrame(A, index=IIO_reduced.index, columns=IIO_reduced.index)

        # Compute Leontief inverse L = (I - A)^(-1)
        I = np.identity(A.shape[0])
        L = np.linalg.inv(I - A)
        L_df = pd.DataFrame(L, index=A_df.index, columns=A_df.columns)

        # Save
        out_path = os.path.join(leontief_dir, f"leontief_inverse_{year}.csv")
        L_df.to_csv(out_path)

    print(f"    ✓ Saved {len(YEARS)} Leontief inverse matrices")


def compute_factor_vectors(factor, excluded_industries, output_dir):
    """Compute factor vectors excluding specified industries."""
    print(f"\n  → Computing Factor Vectors for {factor} (excluding {len(excluded_industries)} industries)...")

    factor_dir = os.path.join(output_dir, "Factor_Vectors")
    os.makedirs(factor_dir, exist_ok=True)

    # Get mask for industries to keep
    keep_mask, all_sectors = get_industry_mask(excluded_industries)

    # Load factor data
    df = pd.read_excel(FACTOR_FILES[factor], sheet_name="Final")
    if df.columns[0] != "factor_key":
        df.rename(columns={df.columns[0]: "factor_key"}, inplace=True)
    df.set_index("factor_key", inplace=True)
    df.columns = df.columns.map(str)

    for year in YEARS:
        year_str = str(year)

        if year_str not in df.columns:
            raise ValueError(f"Year {year_str} missing in factor: {factor}")

        series = df[year_str]

        # ✅ EXCLUDE non-tradable industries using mask
        series_reduced = series[keep_mask]
        series_reduced.name = factor

        out_df = pd.DataFrame([series_reduced])

        outfile = os.path.join(factor_dir, f"factors_{year}.csv")
        out_df.to_csv(outfile, float_format="%.3f")

    print(f"    ✓ Saved {len(YEARS)} factor vector files")


# =============================================================================
# FCT COMPUTATION FUNCTIONS
# =============================================================================

def compute_measured_fct(factor, excluded_industries, matrices_dir, output_dir):
    """Compute measured FCT for a factor."""
    print(f"\n  → Computing Measured FCT...")

    measured_dir = os.path.join(output_dir, "Measured_FCT")
    os.makedirs(measured_dir, exist_ok=True)

    net_trade_dir = os.path.join(matrices_dir, "Net_Trade_Vectors")
    factor_dir = os.path.join(matrices_dir, "Factor_Vectors")

    for year in YEARS:
        # Load net trade vector
        nt_path = os.path.join(net_trade_dir, f"net_trade_vector_{year}.csv")
        df_nt = pd.read_csv(nt_path, index_col=0)

        # Load factor vector
        fv_path = os.path.join(factor_dir, f"factors_{year}.csv")
        df_fv = pd.read_csv(fv_path, index_col=0)

        # Ensure alignment
        common_idx = df_nt.index.intersection(df_fv.columns)
        df_nt = df_nt.loc[common_idx]
        df_fv = df_fv.loc[:, common_idx]

        # Compute F * T
        F = df_fv.values  # 1 x n
        T = df_nt.values  # n x m

        result = F @ T  # 1 x m

        out_df = pd.DataFrame(result, index=[factor], columns=df_nt.columns)
        out_path = os.path.join(measured_dir, f"measured_fct_{year}.csv")
        out_df.to_csv(out_path)

    print(f"    ✓ Saved {len(YEARS)} measured FCT files")


def compute_predicted_fct(factor, excluded_industries, matrices_dir, output_dir):
    """Compute predicted FCT for a factor."""
    print(f"\n  → Computing Predicted FCT...")

    predicted_dir = os.path.join(output_dir, "Predicted_FCT")
    os.makedirs(predicted_dir, exist_ok=True)

    leontief_dir = os.path.join(matrices_dir, "Leontief_Inverse_Matrix")
    net_trade_dir = os.path.join(matrices_dir, "Net_Trade_Vectors")
    factor_dir = os.path.join(matrices_dir, "Factor_Vectors")

    for year in YEARS:
        # Load matrices
        L_path = os.path.join(leontief_dir, f"leontief_inverse_{year}.csv")
        df_L = pd.read_csv(L_path, index_col=0)

        nt_path = os.path.join(net_trade_dir, f"net_trade_vector_{year}.csv")
        df_nt = pd.read_csv(nt_path, index_col=0)

        fv_path = os.path.join(factor_dir, f"factors_{year}.csv")
        df_fv = pd.read_csv(fv_path, index_col=0)

        # Ensure alignment
        common_idx = df_L.index.intersection(df_L.columns).intersection(df_nt.index).intersection(df_fv.columns)
        df_L = df_L.loc[common_idx, common_idx]
        df_nt = df_nt.loc[common_idx]
        df_fv = df_fv.loc[:, common_idx]

        # Compute F * L * T
        F = df_fv.values  # 1 x n
        L = df_L.values   # n x n
        T = df_nt.values  # n x m

        result = F @ L @ T  # 1 x m

        out_df = pd.DataFrame(result, index=[factor], columns=df_nt.columns)
        out_path = os.path.join(predicted_dir, f"predicted_fct_{year}.csv")
        out_df.to_csv(out_path)

    print(f"    ✓ Saved {len(YEARS)} predicted FCT files")


def create_fct_excel(factor, excluded_industries, fct_dir, output_path):
    """Create Excel file with weighted measured and predicted FCT."""
    print(f"\n  → Creating FCT Excel file: {output_path}...")

    measured_dir = os.path.join(fct_dir, "Measured_FCT")
    predicted_dir = os.path.join(fct_dir, "Predicted_FCT")

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for year in YEARS:
            # Load data
            meas_path = os.path.join(measured_dir, f"measured_fct_{year}.csv")
            pred_path = os.path.join(predicted_dir, f"predicted_fct_{year}.csv")

            df_meas = pd.read_csv(meas_path, index_col=0).T
            df_pred = pd.read_csv(pred_path, index_col=0).T

            # Combine
            df_combined = pd.DataFrame({
                'Country': df_meas.index,
                'Measured_FCT': df_meas.iloc[:, 0].values,
                'Predicted_FCT': df_pred.iloc[:, 0].values
            })

            # Compute sign
            df_combined['Sign'] = np.sign(df_combined['Measured_FCT']) == np.sign(df_combined['Predicted_FCT'])

            # Compute weights
            abs_meas = df_combined['Measured_FCT'].abs()
            abs_pred = df_combined['Predicted_FCT'].abs()
            df_combined['Weight'] = (abs_meas + abs_pred) / 2

            # Weighted values
            df_combined['Weighted_Measured_FCT'] = df_combined['Measured_FCT'] * df_combined['Weight']
            df_combined['Weighted_Predicted_FCT'] = df_combined['Predicted_FCT'] * df_combined['Weight']

            # Errors
            df_combined['Error'] = df_combined['Measured_FCT'] - df_combined['Predicted_FCT']
            df_combined['Weighted_Error'] = df_combined['Weighted_Measured_FCT'] - df_combined['Weighted_Predicted_FCT']

            # Add total row
            total_row = pd.DataFrame([{
                'Country': 'Total',
                'Measured_FCT': df_combined['Measured_FCT'].sum(),
                'Predicted_FCT': df_combined['Predicted_FCT'].sum(),
                'Sign': '',
                'Weight': df_combined['Weight'].sum(),
                'Weighted_Measured_FCT': df_combined['Weighted_Measured_FCT'].sum(),
                'Weighted_Predicted_FCT': df_combined['Weighted_Predicted_FCT'].sum(),
                'Error': df_combined['Error'].sum(),
                'Weighted_Error': df_combined['Weighted_Error'].sum()
            }])

            df_final = pd.concat([df_combined, total_row], ignore_index=True)
            df_final.to_excel(writer, sheet_name=str(year), index=False)

    print(f"    ✓ Created Excel file with {len(YEARS)} sheets")


# =============================================================================
# STATISTICAL TESTS
# =============================================================================

def run_fct_tests(factor, excluded_industries, excel_path, output_dir):
    """Run FCT tests for a single factor."""
    print(f"\n  → Running FCT Tests...")

    measured_all, predicted_all = [], []

    for year in YEARS:
        try:
            df = pd.read_excel(excel_path, sheet_name=str(year))
            df = df[df.iloc[:, 0] != "Total"]
            df = df.dropna(subset=["Weighted_Measured_FCT", "Weighted_Predicted_FCT"])

            measured_all.extend(df["Weighted_Measured_FCT"].astype(float).tolist())
            predicted_all.extend(df["Weighted_Predicted_FCT"].astype(float).tolist())
        except Exception as e:
            print(f"    ⚠️ Error reading {factor}-{year}: {e}")

    measured_all = np.array(measured_all)
    predicted_all = np.array(predicted_all)
    n_obs = len(measured_all)

    # Correlation tests
    corr, corr_p = pearsonr(measured_all, predicted_all)
    rank_corr, rank_p = spearmanr(measured_all, predicted_all)

    # Missing trade ratio
    var_meas = np.var(measured_all, ddof=1)
    var_pred = np.var(predicted_all, ddof=1)
    missing_trade_ratio = var_meas / var_pred if var_pred != 0 else np.nan

    # Sign test
    same_sign = np.sign(measured_all) == np.sign(predicted_all)
    n = np.sum(measured_all != 0)
    k = np.sum(same_sign)
    result = binomtest(k, n, p=0.5, alternative='greater')
    same_sign_ratio = k / n
    sign_pvalue = result.pvalue

    # Regression
    X = sm.add_constant(predicted_all)
    model = sm.OLS(measured_all, X).fit()
    slope = model.params[1]
    t_stat = model.tvalues[1]
    r2 = model.rsquared

    # Save results
    results = {
        "Factor": factor,
        "Observations": n_obs,
        "Correlation": corr,
        "Corr_pval": corr_p,
        "Rank_Corr": rank_corr,
        "Rank_pval": rank_p,
        "Missing_Trade_Ratio": missing_trade_ratio,
        "Sign_Same_Ratio": same_sign_ratio,
        "Sign_Same_pval": sign_pvalue,
        "Slope": slope,
        "Slope_tstat": t_stat,
        "R2": r2
    }

    results_df = pd.DataFrame([results])
    results_path = os.path.join(output_dir, "fct_tests.xlsx")
    results_df.to_excel(results_path, index=False)

    # Create scatter plot
    plt.figure(figsize=(8, 6))
    plt.scatter(predicted_all, measured_all, marker='x', color='black', alpha=0.6, label=factor)

    # Regression line
    min_val = min(predicted_all.min(), measured_all.min())
    max_val = max(predicted_all.max(), measured_all.max())
    x_line = np.linspace(min_val, max_val, 100)
    plt.plot(x_line, model.params[0] + slope * x_line, 'k-', label='Linear correlation')

    # 45-degree line
    plt.plot(x_line, x_line, color='lightgrey', linestyle='--', label='Equality line')

    plt.xlabel("Predicted FCT")
    plt.ylabel("Measured FCT")
    plt.title(f"FCT: Measured vs. Predicted - {factor}")
    plt.legend()
    plt.grid(True, linestyle=':')
    plt.tight_layout()

    plot_path = os.path.join(output_dir, f"fct_scatter_{factor}.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()

    print(f"    ✓ Tests completed and saved")
    print(f"      Correlation: {corr:.4f} (p={corr_p:.4f})")
    print(f"      Slope: {slope:.4f} (R²={r2:.4f})")
    print(f"      Sign match: {same_sign_ratio:.2%} (p={sign_pvalue:.4f})")


# =============================================================================
# MAIN PROCESSING FUNCTION
# =============================================================================

def process_factor(factor, base_dir, go_df):
    """Process a single factor through the entire pipeline."""
    print(f"\n{'='*80}")
    print(f"PROCESSING FACTOR: {factor}")
    print(f"{'='*80}")

    # Get excluded industries for this factor
    excluded_industries = FACTOR_NON_TRADABLE_MAP.get(factor, [])
    print(f"Excluding {len(excluded_industries)} industries: {excluded_industries}")

    # Create factor subdirectory
    factor_dir = os.path.join(base_dir, factor)
    os.makedirs(factor_dir, exist_ok=True)

    # Create matrices subdirectory
    matrices_dir = os.path.join(factor_dir, "Matrices")
    os.makedirs(matrices_dir, exist_ok=True)

    # Step 1: Compute matrices
    compute_factor_vectors(factor, excluded_industries, matrices_dir)
    compute_leontief_inverse(factor, excluded_industries, matrices_dir, go_df)
    compute_net_trade_vectors(factor, excluded_industries, matrices_dir)

    # Step 2: Compute FCT
    fct_dir = factor_dir
    compute_measured_fct(factor, excluded_industries, matrices_dir, fct_dir)
    compute_predicted_fct(factor, excluded_industries, matrices_dir, fct_dir)

    # Step 3: Create Excel file
    excel_path = os.path.join(factor_dir, f"fct_{factor}.xlsx")
    create_fct_excel(factor, excluded_industries, fct_dir, excel_path)

    # Step 4: Run tests
    run_fct_tests(factor, excluded_industries, excel_path, factor_dir)

    print(f"\n✅ COMPLETED: {factor}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main(base_directory):
    """Main function to process all factors."""
    print("\n" + "="*80)
    print("FCT ANALYSIS BY FACTOR - WITH NON-TRADABLE EXCLUSIONS")
    print("="*80)

    # Create base directory
    os.makedirs(base_directory, exist_ok=True)

    # Load gross output data once (shared across all factors)
    print("\nLoading Gross Output data...")
    go_df = pd.read_excel(GO_FILE, index_col=0)
    go_df.columns = go_df.columns.map(str)
    print(f"✓ Loaded GO data: {go_df.shape}")

    # Process each factor
    for factor in FACTOR_NON_TRADABLE_MAP.keys():
        try:
            process_factor(factor, base_directory, go_df)
        except Exception as e:
            print(f"\n❌ ERROR processing {factor}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("🎯 ALL FACTORS PROCESSED SUCCESSFULLY!")
    print("="*80)


if __name__ == "__main__":
    # UPDATE THIS PATH TO YOUR DESIRED BASE DIRECTORY
    BASE_DIRECTORY = "/Users/nikhil/Documents/Thesis/FCT/Sensitivity_HOV/Non_Tradable_Tests"

    main(BASE_DIRECTORY)