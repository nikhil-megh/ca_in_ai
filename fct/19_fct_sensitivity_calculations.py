import os
import numpy as np
import pandas as pd
from pathlib import Path

# ======================== CONFIGURATION ========================
FIGARO_DIR = "/Users/nikhil/Documents/Thesis/Figaro/IOT_v2"
GO_FILE = "/Users/nikhil/Documents/Thesis/Figaro/FIGARO_GrossOutput_2010_2021.xlsx"
BASE_SENSITIVITY_DIR = "/Users/nikhil/Documents/Thesis/FCT/Sensitivity"

FACTOR_FILES = {
    "labour": "/Users/nikhil/Documents/Thesis/Labour/EMP_figaro2025.xlsx",
    "capital": "/Users/nikhil/Documents/Thesis/Capital/CAPITAL_figaro2025.xlsx",
    "pct_all_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/AI_PATENTS_15_DEPRECIATION.xlsx",
    "pct_all_non_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/1_All_Applications/NON_AI_PATENTS_15_DEPRECIATION.xlsx",
    "pct_national_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/AI_PATENTS_15_DEPRECIATION.xlsx",
    "pct_national_non_ai_patents": "/Users/nikhil/Documents/Thesis/Patents/PCT_Applications/2_National_Phase/NON_AI_PATENTS_15_DEPRECIATION.xlsx",
}

COUNTRIES = [
    "AR", "AT", "AU", "BE", "BG", "BR", "CA", "CH", "CN", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FIGW1", "FR",
    "GB", "GR", "HR", "HU", "ID", "IE", "IN", "IT", "JP", "KR", "LT", "LU", "LV", "MT", "MX", "NL", "NO", "PL",
    "PT", "RO", "RU", "SA", "SE", "SI", "SK", "TR", "US", "ZA"
]

INDUSTRY_CODES = [
    "A01", "A02", "A03", "B", "C10T12", "C13T15", "C16", "C17", "C18", "C19",
    "C20", "C21", "C22", "C23", "C24", "C25", "C26", "C27", "C28", "C29",
    "C30", "C31_32", "C33", "D35", "E36", "E37T39", "F", "G45", "G46", "G47",
    "H49", "H50", "H51", "H52", "H53", "I", "J58", "J59_60", "J61", "J62_63",
    "K64", "K65", "K66", "L", "M69_70", "M71", "M72", "M73", "M74_75", "N77",
    "N78", "N79", "N80T82", "O84", "P85", "Q86", "Q87_88", "R90T92", "R93",
    "S94", "S95", "S96", "T", "U"
]

YEARS = list(range(2010, 2022))
N_COUNTRIES = 46
N_INDUSTRIES = 64
N_FINAL_DEMAND = 5


# ======================== HELPER FUNCTIONS ========================
def create_directory_structure(omitted_industry):
    """Creates the full directory structure for a given omitted industry."""
    industry_dir = Path(BASE_SENSITIVITY_DIR) / omitted_industry

    subdirs = [
        industry_dir / "Matrices" / "Factor_Vectors",
        industry_dir / "Matrices" / "Leontief_Inverse_Matrix",
        industry_dir / "Matrices" / "Net_Trade_Vectors",
        industry_dir / "Factor_Endowments",
        industry_dir / "Measured_FCT"
    ]

    for subdir in subdirs:
        subdir.mkdir(parents=True, exist_ok=True)

    return industry_dir


def get_industry_mask(omitted_industry_code):
    """Returns boolean mask for sectors to KEEP (excluding omitted industry)."""
    omitted_idx = INDUSTRY_CODES.index(omitted_industry_code)

    # Create sector labels for all 2944 sectors
    all_sectors = [f"{COUNTRIES[i // N_INDUSTRIES]}_{INDUSTRY_CODES[i % N_INDUSTRIES]}"
                   for i in range(N_COUNTRIES * N_INDUSTRIES)]

    # Keep sectors where industry index != omitted_idx
    keep_mask = [(i % N_INDUSTRIES) != omitted_idx for i in range(len(all_sectors))]

    return keep_mask, all_sectors


# ======================== STEP 1: LOAD FIGARO DATA ========================
def load_figaro_data():
    """Loads all FIGARO matrices (2010–2021) as numeric NumPy arrays."""
    W = []
    years = list(range(2010, 2022))
    for year in years:
        file_path = os.path.join(FIGARO_DIR, f"matrix_eu-ic-io_ind-by-ind_25ed_{year}_v2.csv")
        df = pd.read_csv(file_path, header=None)

        # Convert to numeric and drop all-empty rows/cols
        df_numeric = df.apply(pd.to_numeric, errors='coerce')
        df_numeric = df_numeric.dropna(how='all', axis=0).dropna(how='all', axis=1)

        W.append(df_numeric.to_numpy())
        print(f"Loaded FIGARO {year} matrix with shape {df_numeric.shape}")
    return W, years


# ======================== STEP 2: NET TRADE VECTORS ========================
def compute_net_trade_vector_excluded(W, years, omitted_industry, industry_dir):
    """Computes net trade vectors excluding the omitted industry."""
    keep_mask, all_sectors = get_industry_mask(omitted_industry)
    n_reduced = sum(keep_mask)  # Should be 46 * 63 = 2898

    for idx, year in enumerate(years):
        M = W[idx].copy()
        M = M[:-6, :]  # Drop value added rows

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

        total_use = inter_country + fd_country

        # Zero out intra-country flows
        for i in range(N_COUNTRIES):
            row_start = i * N_INDUSTRIES
            row_end = (i + 1) * N_INDUSTRIES
            total_use[row_start:row_end, i] = 0

        # Add export column
        export_col = total_use.sum(axis=1, keepdims=True)

        # Multiply by -1
        total_use_neg = -1 * total_use

        # Replace diagonal with exports
        for i in range(N_COUNTRIES):
            row_start = i * N_INDUSTRIES
            row_end = (i + 1) * N_INDUSTRIES
            total_use_neg[row_start:row_end, i] = export_col[row_start:row_end, 0]

        # ✅ NOW EXCLUDE THE OMITTED INDUSTRY
        total_use_neg_reduced = total_use_neg[keep_mask, :]

        # Create row names (excluding omitted industry)
        row_names_reduced = [all_sectors[i] for i in range(len(all_sectors)) if keep_mask[i]]

        df_out = pd.DataFrame(total_use_neg_reduced, columns=COUNTRIES, index=row_names_reduced)

        out_path = industry_dir / "Matrices" / "Net_Trade_Vectors" / f"net_trade_vector_{year}.csv"
        df_out.to_csv(out_path)
        print(f"  Saved net trade vector for {year} (excluding {omitted_industry})")


# ======================== STEP 3: FACTOR VECTORS ========================
def compute_factor_vectors_excluded(years, omitted_industry, industry_dir):
    """Generates factor vectors excluding the omitted industry."""
    keep_mask, all_sectors = get_industry_mask(omitted_industry)

    # Load all factor data
    data = {}
    for factor_name, filepath in FACTOR_FILES.items():
        df = pd.read_excel(filepath, sheet_name="Final")
        if df.columns[0] != "factor_key":
            df.rename(columns={df.columns[0]: "factor_key"}, inplace=True)
        df.set_index("factor_key", inplace=True)
        df.columns = df.columns.map(str)
        data[factor_name] = df

    for year in years:
        year_str = str(year)
        rows = []

        for factor_name, df in data.items():
            if year_str not in df.columns:
                raise ValueError(f"Year {year_str} missing in factor: {factor_name}")

            series = df[year_str]

            # ✅ EXCLUDE omitted industry
            series_reduced = series[keep_mask]
            series_reduced.name = factor_name
            rows.append(series_reduced)

        out_df = pd.DataFrame(rows)

        outfile = industry_dir / "Matrices" / "Factor_Vectors" / f"factors_{year}.csv"
        out_df.to_csv(outfile, float_format="%.3f")
        print(f"  Saved factor vector for {year} (excluding {omitted_industry})")


# ======================== STEP 4: LEONTIEF INVERSE ========================
def load_IIO_matrix(year):
    """Loads the full IIO matrix for a given year."""
    file_path = os.path.join(FIGARO_DIR, f"matrix_eu-ic-io_ind-by-ind_25ed_{year}_v2.csv")
    df = pd.read_csv(file_path, header=None)

    N_SECTORS = N_COUNTRIES * N_INDUSTRIES  # 2944

    row_labels = df.iloc[1:N_SECTORS + 1, 0].values
    col_labels = df.iloc[0, 1:N_SECTORS + 1].values
    iio_numeric = df.iloc[1:N_SECTORS + 1, 1:N_SECTORS + 1].apply(pd.to_numeric, errors='coerce')

    iio_numeric.index = row_labels
    iio_numeric.columns = col_labels

    return iio_numeric


def load_GO_vector(year, go_df):
    """Loads gross output vector for a given year."""
    return go_df[str(year)].values


def compute_leontief_excluded(years, omitted_industry, industry_dir, go_df):
    """Computes Leontief inverse excluding the omitted industry."""
    keep_mask, all_sectors = get_industry_mask(omitted_industry)

    for year in years:
        print(f"  Processing Leontief for {year} (excluding {omitted_industry})...")

        # Load full IIO matrix
        IIO = load_IIO_matrix(year)
        GO = load_GO_vector(year, go_df)

        # ✅ EXCLUDE omitted industry from IIO (rows and columns)
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
        L_df.to_csv(industry_dir / "Matrices" / "Leontief_Inverse_Matrix" / f"leontief_matrix_{year}.csv")
        print(f"    ✅ Saved Leontief matrix for {year}")


# ======================== STEP 5: FACTOR ENDOWMENTS ========================
def compute_factor_endowments_excluded(years, omitted_industry, industry_dir):
    """Aggregates factor vectors to country level, excluding omitted industry."""
    for year in years:
        E = pd.read_csv(
            industry_dir / "Matrices" / "Factor_Vectors" / f"factors_{year}.csv",
            index_col=0
        )

        # Extract country code from sector columns
        country_map = E.columns.str.split("_").str[0]

        # Group by country and sum
        E_country = E.groupby(country_map, axis=1).sum()
        E_country = E_country[COUNTRIES]

        outfile = industry_dir / "Factor_Endowments" / f"factor_endowments_{year}.csv"
        E_country.to_csv(outfile)
        print(f"  Saved factor endowments for {year} (excluding {omitted_industry})")


# ======================== STEP 6: MEASURED FCT ========================
def compute_measured_fct_excluded(years, omitted_industry, industry_dir, go_df):
    """Computes measured FCT using excluded-industry matrices."""
    for year in years:
        print(f"  Computing FCT for {year} (excluding {omitted_industry})...")

        # Load factor matrix
        E = pd.read_csv(
            industry_dir / "Matrices" / "Factor_Vectors" / f"factors_{year}.csv",
            index_col=0
        )

        # Load Leontief inverse
        L = pd.read_csv(
            industry_dir / "Matrices" / "Leontief_Inverse_Matrix" / f"leontief_matrix_{year}.csv",
            index_col=0
        )

        # Load net trade vector
        T = pd.read_csv(
            industry_dir / "Matrices" / "Net_Trade_Vectors" / f"net_trade_vector_{year}.csv",
            index_col=0
        )

        # Get GO for this year
        year_col = str(year)
        if year_col not in go_df.columns:
            raise KeyError(f"Year {year} missing in GO dataset!")

        GO = go_df[year_col]

        # ✅ EXCLUDE omitted industry from GO
        keep_mask, _ = get_industry_mask(omitted_industry)
        GO_reduced = GO[keep_mask]
        GO_series = GO_reduced.replace(0, np.nan)

        # Normalize E by GO
        E_norm = E.div(GO_series)
        E_norm = E_norm.fillna(0)

        # Compute f = E · L · T
        f = E_norm.values @ L.values @ T.values
        f_df = pd.DataFrame(f, index=E.index, columns=T.columns)

        outfile = industry_dir / "Measured_FCT" / f"measured_fct_{year}.csv"
        f_df.to_csv(outfile)
        print(f"    ✅ Saved measured FCT for {year}")


# ======================== MAIN EXECUTION ========================
if __name__ == "__main__":
    print("🚀 Starting sensitivity analysis for all industries...\n")

    # Load FIGARO data once
    print("Loading FIGARO data...")
    W, years = load_figaro_data()

    # Load Gross Output once
    print("Loading Gross Output data...")
    go_df = pd.read_excel(GO_FILE, index_col=0)
    go_df.columns = go_df.columns.map(str)

    # Process each industry
    for omitted_industry in INDUSTRY_CODES:
        print(f"\n{'=' * 60}")
        print(f"PROCESSING OMITTED INDUSTRY: {omitted_industry}")
        print(f"{'=' * 60}")

        # Create directory structure
        industry_dir = create_directory_structure(omitted_industry)
        print(f"✅ Created directory structure at {industry_dir}")

        # Step 1: Net Trade Vectors
        print("  → Computing net trade vectors...")
        compute_net_trade_vector_excluded(W, years, omitted_industry, industry_dir)

        # Step 2: Factor Vectors
        print("  → Computing factor vectors...")
        compute_factor_vectors_excluded(years, omitted_industry, industry_dir)

        # Step 3: Leontief Inverse
        print("  → Computing Leontief inverse matrices...")
        compute_leontief_excluded(years, omitted_industry, industry_dir, go_df)

        # Step 4: Factor Endowments
        print("  → Computing factor endowments...")
        compute_factor_endowments_excluded(years, omitted_industry, industry_dir)

        # Step 5: Measured FCT
        print("  → Computing measured FCT...")
        compute_measured_fct_excluded(years, omitted_industry, industry_dir, go_df)

        print(f"✅ COMPLETED: {omitted_industry}\n")

    print("\n" + "=" * 60)
    print("🎉 SENSITIVITY ANALYSIS COMPLETE FOR ALL INDUSTRIES!")
    print("=" * 60)